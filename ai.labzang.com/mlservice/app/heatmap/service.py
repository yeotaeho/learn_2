"""
서울 범죄비율 히트맵 서비스
범죄 데이터를 정규화하여 히트맵으로 시각화
"""
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # 백엔드 설정 (GUI 없이 사용)
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64

# 공통 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

try:
    from common.utils import setup_logging
    logger = setup_logging("seoul_crime_heatmap_service")
except ImportError:
    import logging
    logger = logging.getLogger("seoul_crime_heatmap_service")

# CSV 파일 경로
CRIME_CSV_PATH = Path(__file__).parent.parent / "seoul_crime" / "save" / "crime.csv"

# 한글 폰트 설정 (matplotlib)
import platform
def setup_korean_font():
    """플랫폼에 맞는 한글 폰트 설정"""
    system = platform.system()
    
    # 사용 가능한 한글 폰트 목록 (우선순위 순)
    korean_fonts = []
    
    if system == 'Windows':
        korean_fonts = ['Malgun Gothic', 'NanumGothic', 'Gulim', 'Batang']
    elif system == 'Darwin':  # macOS
        korean_fonts = ['AppleGothic', 'NanumGothic', 'Arial Unicode MS']
    else:  # Linux
        korean_fonts = ['NanumGothic', 'NanumBarunGothic', 'DejaVu Sans']
    
    # matplotlib에서 사용 가능한 폰트 목록 가져오기
    import matplotlib.font_manager as fm
    available_fonts = [f.name for f in fm.fontManager.ttflist]
    
    # 사용 가능한 한글 폰트 찾기
    for font in korean_fonts:
        if font in available_fonts:
            plt.rcParams['font.family'] = font
            logger.info(f"한글 폰트 설정 완료: {font}")
            break
    else:
        # 한글 폰트를 찾지 못한 경우 경고
        logger.warning("한글 폰트를 찾을 수 없습니다. 기본 폰트를 사용합니다.")
        plt.rcParams['font.family'] = 'DejaVu Sans'
    
    plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지

# 한글 폰트 설정 실행
setup_korean_font()


class SeoulCrimeHeatmapService:
    """서울 범죄비율 히트맵 생성 서비스"""
    
    def __init__(self):
        """서비스 초기화"""
        self.crime_data: Optional[pd.DataFrame] = None
        self.heatmap_data: Optional[pd.DataFrame] = None
        logger.info("SeoulCrimeHeatmapService 초기화 완료")
    
    def load_crime_data(self) -> pd.DataFrame:
        """
        범죄 데이터 CSV 파일 로드
        
        Returns:
            pd.DataFrame: 범죄 데이터
        """
        if self.crime_data is None:
            try:
                logger.info(f"범죄 데이터 로드 중: {CRIME_CSV_PATH}")
                self.crime_data = pd.read_csv(CRIME_CSV_PATH, encoding='utf-8')
                logger.info(f"범죄 데이터 로드 완료: {len(self.crime_data)}개 관서")
            except Exception as e:
                logger.error(f"범죄 데이터 로드 실패: {e}")
                raise
        return self.crime_data
    
    def parse_number(self, value: Any) -> int:
        """
        숫자 문자열에서 쉼표 제거하고 숫자로 변환
        
        Args:
            value: 숫자 문자열 (예: "1,395") 또는 숫자
            
        Returns:
            int: 변환된 숫자
        """
        if pd.isna(value) or value == '':
            return 0
        if isinstance(value, (int, float)):
            return int(value)
        return int(str(value).replace(',', ''))
    
    def aggregate_by_district(self) -> pd.DataFrame:
        """
        자치구별 범죄 데이터 집계
        
        Returns:
            pd.DataFrame: 자치구별 범죄 발생 건수 (범죄 유형별)
        """
        crime_df = self.load_crime_data()
        
        # 범죄 유형별 컬럼명 매핑
        crime_types = {
            '살인': '살인 발생',
            '강도': '강도 발생',
            '강간': '강간 발생',
            '절도': '절도 발생',
            '폭력': '폭력 발생'
        }
        
        # 자치구별로 범죄 발생 건수 집계
        district_crimes = {}
        
        for _, row in crime_df.iterrows():
            district = row['자치구']
            if pd.isna(district):
                continue
            
            if district not in district_crimes:
                district_crimes[district] = {
                    '살인': 0,
                    '강도': 0,
                    '강간': 0,
                    '절도': 0,
                    '폭력': 0
                }
            
            # 각 범죄 유형별로 합산
            for crime_type, column_name in crime_types.items():
                district_crimes[district][crime_type] += self.parse_number(row[column_name])
        
        # DataFrame으로 변환
        data_list = []
        for district, crimes in district_crimes.items():
            row = {'자치구': district}
            row.update(crimes)
            # 전체 범죄 건수 계산
            row['범죄'] = sum(crimes.values())
            data_list.append(row)
        
        result_df = pd.DataFrame(data_list)
        logger.info(f"자치구별 범죄 데이터 집계 완료: {len(result_df)}개 자치구")
        return result_df
    
    def normalize_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        범죄 데이터 정규화 (0-1 스케일)
        
        Args:
            df: 자치구별 범죄 데이터
            
        Returns:
            pd.DataFrame: 정규화된 데이터
        """
        # 정규화할 컬럼 (범죄 유형)
        crime_columns = ['살인', '강도', '강간', '절도', '폭력', '범죄']
        
        # 정규화된 데이터 복사
        normalized_df = df.copy()
        
        # 각 범죄 유형별로 정규화
        for col in crime_columns:
            if col in normalized_df.columns:
                col_data = normalized_df[col]
                min_val = col_data.min()
                max_val = col_data.max()
                
                if max_val > min_val:
                    normalized_df[col] = (col_data - min_val) / (max_val - min_val)
                else:
                    normalized_df[col] = 0.0
        
        logger.info("데이터 정규화 완료")
        return normalized_df
    
    def prepare_heatmap_data(self) -> pd.DataFrame:
        """
        히트맵용 데이터 준비 (정규화 및 정렬)
        
        Returns:
            pd.DataFrame: 히트맵용 데이터 (자치구별 정규화된 범죄 비율)
        """
        if self.heatmap_data is not None:
            return self.heatmap_data
        
        # 자치구별 집계
        district_data = self.aggregate_by_district()
        
        # 정규화
        normalized_data = self.normalize_data(district_data)
        
        # "범죄" 컬럼으로 내림차순 정렬
        normalized_data = normalized_data.sort_values('범죄', ascending=False)
        
        # 인덱스를 자치구로 설정
        normalized_data = normalized_data.set_index('자치구')
        
        # 컬럼 순서: 강간, 강도, 살인, 절도, 폭력, 범죄
        column_order = ['강간', '강도', '살인', '절도', '폭력', '범죄']
        normalized_data = normalized_data[column_order]
        
        self.heatmap_data = normalized_data
        logger.info(f"히트맵 데이터 준비 완료: {normalized_data.shape}")
        return self.heatmap_data
    
    def generate_heatmap_html(self) -> str:
        """
        히트맵을 생성하고 HTML로 변환
        
        Returns:
            str: 히트맵이 포함된 HTML 문자열
        """
        # 히트맵 데이터 준비
        heatmap_df = self.prepare_heatmap_data()
        
        # 한글 폰트 재설정 (이미 전역으로 설정되어 있지만 확실히 하기 위해)
        setup_korean_font()
        
        # 그림 크기 설정
        fig, ax = plt.subplots(figsize=(10, 14))
        
        # 히트맵 생성 (보라색-핑크 그라데이션)
        sns.heatmap(
            heatmap_df,
            annot=True,
            fmt='.6f',
            cmap='RdPu',  # Red-Purple 색상 팔레트 (보라색-핑크)
            vmin=0.0,
            vmax=1.0,
            cbar_kws={'label': '정규화된 범죄 비율'},
            linewidths=0.5,
            linecolor='white',
            ax=ax,
            annot_kws={'size': 8}
        )
        
        # 제목 설정
        ax.set_title('범죄비율 (정규화된 발생 건수로 정렬)', fontsize=16, fontweight='bold', pad=20)
        
        # 축 레이블 설정
        ax.set_xlabel('범죄 유형', fontsize=12)
        ax.set_ylabel('자치구', fontsize=12)
        
        # x축 레이블 회전
        plt.xticks(rotation=0)
        plt.yticks(rotation=0)
        
        # 레이아웃 조정
        plt.tight_layout()
        
        # 이미지를 base64로 인코딩
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        plt.close(fig)
        
        # HTML 생성
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>서울 범죄비율 히트맵</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                h1 {{
                    text-align: center;
                    color: #333;
                    margin-bottom: 20px;
                }}
                .heatmap-image {{
                    width: 100%;
                    height: auto;
                    display: block;
                    margin: 0 auto;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>범죄비율 (정규화된 발생 건수로 정렬)</h1>
                <img src="data:image/png;base64,{image_base64}" alt="서울 범죄비율 히트맵" class="heatmap-image" />
            </div>
        </body>
        </html>
        """
        
        logger.info("히트맵 HTML 생성 완료")
        return html_content
    
    def get_heatmap_data(self) -> pd.DataFrame:
        """
        히트맵 데이터 반환 (정규화된 값)
        
        Returns:
            pd.DataFrame: 정규화된 범죄 비율 데이터
        """
        return self.prepare_heatmap_data()
    
    def reset(self) -> None:
        """서비스 상태 초기화"""
        self.crime_data = None
        self.heatmap_data = None
        logger.info("서비스 상태 초기화 완료")

