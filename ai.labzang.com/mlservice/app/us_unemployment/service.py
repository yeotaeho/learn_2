"""
미국 실업률 데이터 서비스
Folium을 사용한 지도 시각화 서비스
"""
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import requests
import pandas as pd
import folium

# 공통 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# 로깅 설정
try:
    from common.utils import setup_logging
    logger = setup_logging("us_unemployment_service")
except ImportError:
    import logging
    logger = logging.getLogger("us_unemployment_service")


class USUnemploymentService:
    """미국 실업률 데이터 처리 및 지도 시각화 서비스"""
    
    # 데이터 소스 URL
    STATE_GEO_URL = "https://raw.githubusercontent.com/python-visualization/folium-example-data/main/us_states.json"
    STATE_DATA_URL = "https://raw.githubusercontent.com/python-visualization/folium-example-data/main/us_unemployment_oct_2012.csv"
    
    # 지도 기본 설정
    DEFAULT_LOCATION = [48, -102]  # 미국 중심 좌표
    DEFAULT_ZOOM_START = 3
    
    def __init__(self):
        """서비스 초기화"""
        self.state_geo: Optional[Dict[str, Any]] = None
        self.state_data: Optional[pd.DataFrame] = None
        self.map: Optional[folium.Map] = None
        logger.info("USUnemploymentService 초기화 완료")
    
    def load_state_geo_data(self) -> Dict[str, Any]:
        """
        주(State) 지리 데이터 로드
        
        Returns:
            Dict[str, Any]: 주 지리 데이터 (GeoJSON 형식)
        """
        if self.state_geo is None:
            try:
                logger.info(f"주 지리 데이터 로드 중: {self.STATE_GEO_URL}")
                response = requests.get(self.STATE_GEO_URL)
                response.raise_for_status()
                self.state_geo = response.json()
                logger.info("주 지리 데이터 로드 완료")
            except Exception as e:
                logger.error(f"주 지리 데이터 로드 실패: {e}")
                raise
        return self.state_geo
    
    def load_state_data(self) -> pd.DataFrame:
        """
        주별 실업률 데이터 로드
        
        Returns:
            pd.DataFrame: 주별 실업률 데이터
        """
        if self.state_data is None:
            try:
                logger.info(f"실업률 데이터 로드 중: {self.STATE_DATA_URL}")
                self.state_data = pd.read_csv(self.STATE_DATA_URL)
                logger.info(f"실업률 데이터 로드 완료: {len(self.state_data)}개 주")
            except Exception as e:
                logger.error(f"실업률 데이터 로드 실패: {e}")
                raise
        return self.state_data
    
    def create_map(self, location: Optional[list] = None, zoom_start: Optional[int] = None) -> folium.Map:
        """
        Folium 지도 생성
        
        Args:
            location: 지도 중심 좌표 [위도, 경도]. 기본값: [48, -102]
            zoom_start: 초기 줌 레벨. 기본값: 3
            
        Returns:
            folium.Map: 생성된 지도 객체
        """
        if location is None:
            location = self.DEFAULT_LOCATION
        if zoom_start is None:
            zoom_start = self.DEFAULT_ZOOM_START
        
        logger.info(f"지도 생성 중: location={location}, zoom_start={zoom_start}")
        self.map = folium.Map(location=location, zoom_start=zoom_start)
        logger.info("지도 생성 완료")
        return self.map
    
    def add_choropleth_layer(
        self,
        fill_color: str = "YlGn",
        fill_opacity: float = 0.7,
        line_opacity: float = 0.2,
        legend_name: str = "Unemployment Rate (%)"
    ) -> None:
        """
        실업률 Choropleth 레이어 추가
        
        Args:
            fill_color: 색상 팔레트 (기본값: "YlGn")
            fill_opacity: 채우기 투명도 (0.0 ~ 1.0)
            line_opacity: 경계선 투명도 (0.0 ~ 1.0)
            legend_name: 범례 이름
        """
        if self.map is None:
            raise ValueError("지도가 생성되지 않았습니다. create_map()을 먼저 호출하세요.")
        
        # 데이터 로드
        state_geo = self.load_state_geo_data()
        state_data = self.load_state_data()
        
        try:
            logger.info("Choropleth 레이어 추가 중")
            folium.Choropleth(
                geo_data=state_geo,
                name="choropleth",
                data=state_data,
                columns=["State", "Unemployment"],
                key_on="feature.id",
                fill_color=fill_color,
                fill_opacity=fill_opacity,
                line_opacity=line_opacity,
                legend_name=legend_name,
            ).add_to(self.map)
            logger.info("Choropleth 레이어 추가 완료")
        except Exception as e:
            logger.error(f"Choropleth 레이어 추가 실패: {e}")
            raise
    
    def add_layer_control(self) -> None:
        """레이어 컨트롤 추가"""
        if self.map is None:
            raise ValueError("지도가 생성되지 않았습니다. create_map()을 먼저 호출하세요.")
        
        logger.info("레이어 컨트롤 추가 중")
        folium.LayerControl().add_to(self.map)
        logger.info("레이어 컨트롤 추가 완료")
    
    def generate_map(
        self,
        location: Optional[list] = None,
        zoom_start: Optional[int] = None,
        fill_color: str = "YlGn",
        fill_opacity: float = 0.7,
        line_opacity: float = 0.2,
        legend_name: str = "Unemployment Rate (%)"
    ) -> folium.Map:
        """
        완전한 실업률 지도 생성 (모든 단계 포함)
        
        Args:
            location: 지도 중심 좌표 [위도, 경도]
            zoom_start: 초기 줌 레벨
            fill_color: 색상 팔레트
            fill_opacity: 채우기 투명도
            line_opacity: 경계선 투명도
            legend_name: 범례 이름
            
        Returns:
            folium.Map: 생성된 지도 객체
        """
        logger.info("실업률 지도 생성 시작")
        
        # 지도 생성
        self.create_map(location=location, zoom_start=zoom_start)
        
        # Choropleth 레이어 추가
        self.add_choropleth_layer(
            fill_color=fill_color,
            fill_opacity=fill_opacity,
            line_opacity=line_opacity,
            legend_name=legend_name
        )
        
        # 레이어 컨트롤 추가
        self.add_layer_control()
        
        logger.info("실업률 지도 생성 완료")
        return self.map
    
    def get_map(self) -> Optional[folium.Map]:
        """
        현재 지도 객체 반환
        
        Returns:
            Optional[folium.Map]: 지도 객체 (없으면 None)
        """
        return self.map
    
    def reset(self) -> None:
        """서비스 상태 초기화"""
        self.state_geo = None
        self.state_data = None
        self.map = None
        logger.info("서비스 상태 초기화 완료")