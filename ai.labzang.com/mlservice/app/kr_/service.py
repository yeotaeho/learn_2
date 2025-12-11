"""
서울 범죄지도 서비스
Folium과 지오코딩을 사용한 서울 범죄 데이터 시각화 서비스
"""
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
import pandas as pd
import folium
import json

# 공통 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

try:
    from common.utils import setup_logging
    logger = setup_logging("seoul_crime_map_service")
except ImportError:
    import logging
    logger = logging.getLogger("seoul_crime_map_service")

# CSV 파일 경로
CRIME_CSV_PATH = Path(__file__).parent.parent / "seoul_crime" / "save" / "crime.csv"
GEOJSON_PATH = Path(__file__).parent.parent / "seoul_crime" / "data" / "kr-state.json"

# 서울 중심 좌표
SEOUL_CENTER = [37.5665, 126.9780]  # 서울시청
DEFAULT_ZOOM_START = 11


class SeoulCrimeMapService:
    """서울 범죄지도 생성 서비스"""
    
    def __init__(self):
        """서비스 초기화"""
        self.crime_data: Optional[pd.DataFrame] = None
        self.geo_data: Optional[Dict[str, Any]] = None
        self.district_crime_data: Optional[pd.DataFrame] = None
        self.map: Optional[folium.Map] = None
        logger.info("SeoulCrimeMapService 초기화 완료")
    
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
    
    def load_geo_data(self) -> Dict[str, Any]:
        """
        서울 자치구 GeoJSON 데이터 로드
        
        Returns:
            Dict[str, Any]: GeoJSON 데이터
        """
        if self.geo_data is None:
            try:
                logger.info(f"GeoJSON 데이터 로드 중: {GEOJSON_PATH}")
                with open(GEOJSON_PATH, 'r', encoding='utf-8') as f:
                    self.geo_data = json.load(f)
                logger.info(f"GeoJSON 데이터 로드 완료: {len(self.geo_data.get('features', []))}개 자치구")
            except Exception as e:
                logger.error(f"GeoJSON 데이터 로드 실패: {e}")
                raise
        return self.geo_data
    
    def parse_number(self, value: str) -> int:
        """
        숫자 문자열에서 쉼표 제거하고 숫자로 변환
        
        Args:
            value: 숫자 문자열 (예: "1,395")
            
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
        자치구별 범죄 데이터 집계 (발생 건수 및 검거 건수)
        
        Returns:
            pd.DataFrame: 자치구별 범죄 발생 건수 및 검거 건수
        """
        if self.district_crime_data is not None:
            return self.district_crime_data
        
        crime_df = self.load_crime_data()
        
        # 자치구별로 범죄 발생 건수 및 검거 건수 합산
        district_crimes = {}
        
        for _, row in crime_df.iterrows():
            district = row['자치구']
            if pd.isna(district):
                continue
            
            # 범죄 발생 건수 합산
            total_crimes = (
                self.parse_number(row['살인 발생']) +
                self.parse_number(row['강도 발생']) +
                self.parse_number(row['강간 발생']) +
                self.parse_number(row['절도 발생']) +
                self.parse_number(row['폭력 발생'])
            )
            
            # 검거 건수 합산
            total_arrests = (
                self.parse_number(row['살인 검거']) +
                self.parse_number(row['강도 검거']) +
                self.parse_number(row['강간 검거']) +
                self.parse_number(row['절도 검거']) +
                self.parse_number(row['폭력 검거'])
            )
            
            if district not in district_crimes:
                district_crimes[district] = {'범죄건수': 0, '검거건수': 0}
            district_crimes[district]['범죄건수'] += total_crimes
            district_crimes[district]['검거건수'] += total_arrests
        
        # DataFrame으로 변환
        data_list = []
        for district, data in district_crimes.items():
            crime_count = data['범죄건수']
            arrest_count = data['검거건수']
            # 검거율 계산 (발생 건수가 0이면 0%)
            arrest_rate = (arrest_count / crime_count * 100) if crime_count > 0 else 0.0
            data_list.append({
                '자치구': district,
                '범죄건수': crime_count,
                '검거건수': arrest_count,
                '검거율': arrest_rate
            })
        
        self.district_crime_data = pd.DataFrame(data_list)
        
        logger.info(f"자치구별 범죄 데이터 집계 완료: {len(self.district_crime_data)}개 자치구")
        return self.district_crime_data
    
    def calculate_average(self) -> float:
        """
        평균 범죄 발생 건수 계산
        
        Returns:
            float: 평균 범죄 발생 건수
        """
        district_data = self.aggregate_by_district()
        if len(district_data) == 0:
            return 0.0
        return district_data['범죄건수'].mean()
    
    def get_district_center(self, district_name: str) -> Optional[List[float]]:
        """
        자치구의 중심 좌표 계산 (GeoJSON에서)
        
        Args:
            district_name: 자치구명
            
        Returns:
            Optional[List[float]]: [위도, 경도] 또는 None
        """
        geo_data = self.load_geo_data()
        
        for feature in geo_data.get('features', []):
            if feature.get('id') == district_name:
                geometry = feature.get('geometry', {})
                if geometry.get('type') == 'Polygon':
                    coordinates = geometry.get('coordinates', [])
                    if coordinates and len(coordinates) > 0:
                        # 폴리곤의 모든 좌표에서 중심 계산
                        all_coords = coordinates[0]  # 외곽 좌표
                        lngs = [coord[0] for coord in all_coords]
                        lats = [coord[1] for coord in all_coords]
                        center_lng = sum(lngs) / len(lngs)
                        center_lat = sum(lats) / len(lats)
                        return [center_lat, center_lng]
        return None
    
    def create_map(self, location: Optional[List[float]] = None, zoom_start: Optional[int] = None) -> folium.Map:
        """
        Folium 지도 생성
        
        Args:
            location: 지도 중심 좌표 [위도, 경도]
            zoom_start: 초기 줌 레벨
            
        Returns:
            folium.Map: 생성된 지도 객체
        """
        if location is None:
            location = SEOUL_CENTER
        if zoom_start is None:
            zoom_start = DEFAULT_ZOOM_START
        
        logger.info(f"지도 생성 중: location={location}, zoom_start={zoom_start}")
        
        # 라이트 테마 지도 생성 (OpenStreetMap 스타일)
        self.map = folium.Map(
            location=location,
            zoom_start=zoom_start,
            tiles='OpenStreetMap'
        )
        
        logger.info("지도 생성 완료")
        return self.map
    
    def calculate_color(self, crime_count: float, min_count: float, max_count: float) -> str:
        """
        범죄 건수에 따른 보라색 그라데이션 색상 계산
        
        Args:
            crime_count: 범죄 건수
            min_count: 최소 범죄 건수
            max_count: 최대 범죄 건수
            
        Returns:
            str: RGB 색상 문자열
        """
        if max_count == min_count:
            return 'rgb(232, 224, 255)'  # #E8E0FF
        
        normalized = (crime_count - min_count) / (max_count - min_count)
        
        # 보라색 그라데이션: #E8E0FF (연한) -> #9C7FD8 (중간) -> #4A148C (진한)
        colors = [
            {'r': 232, 'g': 224, 'b': 255},  # #E8E0FF
            {'r': 156, 'g': 127, 'b': 216},  # #9C7FD8
            {'r': 74, 'g': 20, 'b': 140}     # #4A148C
        ]
        
        if normalized < 0.5:
            color1, color2 = colors[0], colors[1]
            factor = normalized * 2
        else:
            color1, color2 = colors[1], colors[2]
            factor = (normalized - 0.5) * 2
        
        r = int(color1['r'] + (color2['r'] - color1['r']) * factor)
        g = int(color1['g'] + (color2['g'] - color1['g']) * factor)
        b = int(color1['b'] + (color2['b'] - color1['b']) * factor)
        
        return f'rgb({r}, {g}, {b})'
    
    def add_choropleth_layer(self) -> None:
        """Choropleth 레이어 추가 (자치구별 범죄 건수 - 히트맵 스타일)"""
        if self.map is None:
            raise ValueError("지도가 생성되지 않았습니다. create_map()을 먼저 호출하세요.")
        
        geo_data = self.load_geo_data()
        district_data = self.aggregate_by_district()
        
        # 범죄 건수 범위 계산
        min_count = district_data['범죄건수'].min()
        max_count = district_data['범죄건수'].max()
        
        # GeoJSON의 각 feature에 범죄 건수, 검거 건수 및 색상 추가
        for feature in geo_data['features']:
            district_name = feature.get('id')
            if district_name:
                district_row = district_data[district_data['자치구'] == district_name]
                if not district_row.empty:
                    crime_count = district_row.iloc[0]['범죄건수']
                    arrest_count = district_row.iloc[0]['검거건수']
                    arrest_rate = district_row.iloc[0]['검거율']
                    feature['properties']['범죄건수'] = float(crime_count)
                    feature['properties']['검거건수'] = float(arrest_count)
                    feature['properties']['검거율'] = float(arrest_rate)
                    # 색상 계산 및 추가 (히트맵 스타일: 연한 보라색 -> 진한 빨강/핑크)
                    color = self.calculate_heatmap_color(crime_count, min_count, max_count)
                    feature['properties']['fillColor'] = color
                else:
                    feature['properties']['범죄건수'] = 0.0
                    feature['properties']['검거건수'] = 0.0
                    feature['properties']['검거율'] = 0.0
                    feature['properties']['fillColor'] = 'rgb(232, 224, 255)'  # 기본 색상
        
        # GeoJson 레이어로 커스텀 색상 적용
        folium.GeoJson(
            geo_data,
            style_function=lambda feature: {
                'fillColor': feature['properties'].get('fillColor', 'rgb(232, 224, 255)'),
                'color': '#000000',  # 검은색 경계선
                'weight': 2,
                'fillOpacity': 0.6,
            },
            tooltip=folium.GeoJsonTooltip(
                fields=['name', '범죄건수', '검거건수', '검거율'],
                aliases=['자치구:', '범죄 발생:', '검거:', '검거율:'],
                localize=True
            )
        ).add_to(self.map)
        
        logger.info("Choropleth 레이어 추가 완료")
    
    def calculate_heatmap_color(self, value: float, min_val: float, max_val: float) -> str:
        """
        히트맵 스타일 색상 계산 (연한 보라색 -> 진한 빨강/핑크)
        
        Args:
            value: 값
            min_val: 최소값
            max_val: 최대값
            
        Returns:
            str: RGB 색상 문자열
        """
        if max_val == min_val:
            return 'rgb(232, 224, 255)'  # 연한 보라색
        
        normalized = (value - min_val) / (max_val - min_val)
        
        # 히트맵 색상: 연한 보라색 -> 보라색 -> 핑크 -> 빨강
        # #E8E0FF (연한 보라) -> #9C7FD8 (보라) -> #FF6B9D (핑크) -> #FF1744 (빨강)
        colors = [
            {'r': 232, 'g': 224, 'b': 255},  # #E8E0FF
            {'r': 156, 'g': 127, 'b': 216},  # #9C7FD8
            {'r': 255, 'g': 107, 'b': 157},  # #FF6B9D
            {'r': 255, 'g': 23, 'b': 68}     # #FF1744
        ]
        
        if normalized < 0.33:
            color1, color2 = colors[0], colors[1]
            factor = normalized / 0.33
        elif normalized < 0.66:
            color1, color2 = colors[1], colors[2]
            factor = (normalized - 0.33) / 0.33
        else:
            color1, color2 = colors[2], colors[3]
            factor = (normalized - 0.66) / 0.34
        
        r = int(color1['r'] + (color2['r'] - color1['r']) * factor)
        g = int(color1['g'] + (color2['g'] - color1['g']) * factor)
        b = int(color1['b'] + (color2['b'] - color1['b']) * factor)
        
        return f'rgb({r}, {g}, {b})'
    
    def add_arrest_circle_markers(self) -> None:
        """검거 건수를 원형 마커로 표시 (히트맵 스타일)"""
        if self.map is None:
            raise ValueError("지도가 생성되지 않았습니다. create_map()을 먼저 호출하세요.")
        
        district_data = self.aggregate_by_district()
        
        # 검거 건수 범위 계산
        min_arrest = district_data['검거건수'].min()
        max_arrest = district_data['검거건수'].max()
        
        for _, row in district_data.iterrows():
            district_name = row['자치구']
            arrest_count = row['검거건수']
            arrest_rate = row['검거율']
            
            # 자치구 중심 좌표 가져오기
            center = self.get_district_center(district_name)
            if center:
                # 검거 건수에 따라 원형 마커 크기 계산 (최소 800m, 최대 2500m)
                if max_arrest > min_arrest:
                    normalized = (arrest_count - min_arrest) / (max_arrest - min_arrest)
                    radius = 800 + (normalized * 1700)  # 800m ~ 2500m
                else:
                    radius = 1200
                
                # 파란색 원형 마커 추가 (Circle 사용 - 미터 단위)
                folium.Circle(
                    location=center,
                    radius=radius,  # 미터 단위
                    popup=folium.Popup(
                        f"""
                        <div style="font-family: Arial, sans-serif;">
                            <h4 style="margin: 5px 0; color: #333;">{district_name}</h4>
                            <p style="margin: 3px 0;"><strong>검거:</strong> {arrest_count:.0f}건</p>
                            <p style="margin: 3px 0;"><strong>검거율:</strong> {arrest_rate:.1f}%</p>
                        </div>
                        """,
                        max_width=200
                    ),
                    tooltip=f"{district_name}: 검거 {arrest_count:.0f}건 ({arrest_rate:.1f}%)",
                    color='#0066FF',  # 파란색 테두리
                    weight=2,
                    fillColor='#0066FF',  # 파란색 채우기
                    fillOpacity=0.3,  # 투명도 조정
                ).add_to(self.map)
        
        logger.info("검거 원형 마커 추가 완료")
    
    def add_district_labels(self) -> None:
        """각 자치구에 범죄 건수 및 검거 건수 텍스트 라벨 추가"""
        if self.map is None:
            raise ValueError("지도가 생성되지 않았습니다. create_map()을 먼저 호출하세요.")
        
        district_data = self.aggregate_by_district()
        
        for _, row in district_data.iterrows():
            district_name = row['자치구']
            crime_count = row['범죄건수']
            arrest_count = row['검거건수']
            arrest_rate = row['검거율']
            
            # 자치구 중심 좌표 가져오기
            center = self.get_district_center(district_name)
            if center:
                # 텍스트 라벨 추가 (범죄 건수와 검거 건수 표시)
                folium.Marker(
                    location=center,
                    icon=folium.DivIcon(
                        html=f"""
                        <div style="
                            background: rgba(255, 255, 255, 0.9);
                            color: #333;
                            padding: 6px 10px;
                            border-radius: 4px;
                            font-size: 11px;
                            font-weight: bold;
                            white-space: nowrap;
                            pointer-events: none;
                            text-align: center;
                            line-height: 1.4;
                            border: 1px solid #ccc;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                        ">
                            <div style="font-size: 13px; margin-bottom: 2px; color: #000;">{district_name}</div>
                            <div style="color: #FF6B6B;">발생: {crime_count:.0f}건</div>
                            <div style="color: #0066FF;">검거: {arrest_count:.0f}건</div>
                            <div style="color: #4CAF50; font-size: 10px;">검거율: {arrest_rate:.1f}%</div>
                        </div>
                        """,
                        icon_size=(120, 80),
                        icon_anchor=(60, 40)
                    )
                ).add_to(self.map)
        
        logger.info("자치구 라벨 추가 완료")
    
    def add_average_indicator(self) -> None:
        """평균값 표시 추가 (좌측 상단) - 발생 건수 및 검거 건수"""
        if self.map is None:
            raise ValueError("지도가 생성되지 않았습니다. create_map()을 먼저 호출하세요.")
        
        district_data = self.aggregate_by_district()
        avg_crime = district_data['범죄건수'].mean()
        avg_arrest = district_data['검거건수'].mean()
        avg_arrest_rate = district_data['검거율'].mean()
        
        # 평균값 표시 HTML
        average_html = f"""
        <div style="
            position: fixed;
            top: 10px;
            left: 10px;
            background: rgba(0, 0, 0, 0.7);
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            z-index: 1000;
            font-family: Arial, sans-serif;
            box-shadow: 0 2px 10px rgba(0,0,0,0.5);
        ">
            <div style="font-size: 16px; color: #CCCCCC; margin-bottom: 10px; font-weight: bold;">평균</div>
            <div style="margin-bottom: 8px;">
                <div style="font-size: 12px; color: #FF6B6B; margin-bottom: 3px;">발생</div>
                <div style="font-size: 20px; font-weight: bold; color: #FFD700;">{avg_crime:.1f}건</div>
            </div>
            <div style="margin-bottom: 8px;">
                <div style="font-size: 12px; color: #4ECDC4; margin-bottom: 3px;">검거</div>
                <div style="font-size: 20px; font-weight: bold; color: #4ECDC4;">{avg_arrest:.1f}건</div>
            </div>
            <div>
                <div style="font-size: 12px; color: #95E1D3; margin-bottom: 3px;">검거율</div>
                <div style="font-size: 18px; font-weight: bold; color: #95E1D3;">{avg_arrest_rate:.1f}%</div>
            </div>
        </div>
        """
        
        self.map.get_root().html.add_child(folium.Element(average_html))
        logger.info(f"평균값 표시 추가 완료: 발생 {avg_crime:.1f}건, 검거 {avg_arrest:.1f}건, 검거율 {avg_arrest_rate:.1f}%")
    
    def generate_map(
        self,
        location: Optional[List[float]] = None,
        zoom_start: Optional[int] = None
    ) -> folium.Map:
        """
        완전한 서울 범죄지도 생성 (모든 단계 포함)
        
        Args:
            location: 지도 중심 좌표 [위도, 경도]
            zoom_start: 초기 줌 레벨
            
        Returns:
            folium.Map: 생성된 지도 객체
        """
        logger.info("서울 범죄지도 생성 시작")
        
        # 지도 생성
        self.create_map(location=location, zoom_start=zoom_start)
        
        # Choropleth 레이어 추가 (범죄 발생 건수 히트맵)
        self.add_choropleth_layer()
        
        # 검거 건수 원형 마커 추가 (히트맵 스타일)
        self.add_arrest_circle_markers()
        
        # 자치구 라벨 추가
        self.add_district_labels()
        
        # 평균값 표시 추가
        self.add_average_indicator()
        
        logger.info("서울 범죄지도 생성 완료")
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
        self.crime_data = None
        self.geo_data = None
        self.district_crime_data = None
        self.map = None
        logger.info("서비스 상태 초기화 완료")

