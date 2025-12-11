"""
미국 실업률 관련 라우터
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
from typing import Optional
from pathlib import Path
import sys

# 공통 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from app.us_unemployment.service import USUnemploymentService

try:
    from common.utils import create_response, create_error_response
except ImportError:
    # common.utils가 없는 경우 기본 함수 사용
    def create_response(data=None, message="Success"):
        return {"status": "success", "message": message, "data": data}
    
    def create_error_response(message="Error", status_code=500):
        return {"status": "error", "message": message, "status_code": status_code}

import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["usa"])

# 서비스 인스턴스 생성 (싱글톤 패턴)
_service_instance: Optional[USUnemploymentService] = None


def get_service() -> USUnemploymentService:
    """USUnemploymentService 싱글톤 인스턴스 반환"""
    global _service_instance
    if _service_instance is None:
        _service_instance = USUnemploymentService()
    return _service_instance


@router.get("/")
async def usa_root():
    """미국 실업률 서비스 루트"""
    return create_response(
        data={"service": "mlservice", "module": "us_unemployment", "status": "running"},
        message="US Unemployment Service is running"
    )


@router.get("/map", response_class=HTMLResponse)
async def get_unemployment_map(
    fill_color: str = Query("YlGn", description="색상 팔레트 (예: YlGn, YlOrRd, Blues)"),
    fill_opacity: float = Query(0.7, ge=0.0, le=1.0, description="채우기 투명도 (0.0 ~ 1.0)"),
    line_opacity: float = Query(0.2, ge=0.0, le=1.0, description="경계선 투명도 (0.0 ~ 1.0)"),
    legend_name: str = Query("Unemployment Rate (%)", description="범례 이름")
):
    """
    미국 실업률 지도 생성 및 반환
    
    - Folium을 사용한 인터랙티브 지도 생성
    - 주별 실업률을 Choropleth로 시각화
    - HTML 형식으로 반환
    """
    try:
        service = get_service()
        logger.info("미국 실업률 지도 생성 요청")
        
        # 지도 생성
        map_obj = service.generate_map(
            fill_color=fill_color,
            fill_opacity=fill_opacity,
            line_opacity=line_opacity,
            legend_name=legend_name
        )
        
        # HTML로 변환
        map_html = map_obj._repr_html_() if hasattr(map_obj, '_repr_html_') else str(map_obj)
        
        logger.info("미국 실업률 지도 생성 완료")
        return HTMLResponse(content=map_html)
        
    except Exception as e:
        logger.error(f"지도 생성 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"지도 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/data")
async def get_unemployment_data():
    """
    미국 실업률 데이터 조회
    
    - 주별 실업률 데이터를 JSON 형식으로 반환
    """
    try:
        service = get_service()
        logger.info("미국 실업률 데이터 조회 요청")
        
        # 데이터 로드
        state_data = service.load_state_data()
        
        # DataFrame을 딕셔너리로 변환
        data_dict = state_data.to_dict(orient="records")
        
        logger.info(f"미국 실업률 데이터 조회 완료: {len(data_dict)}개 주")
        return create_response(
            data={
                "states": data_dict,
                "total_count": len(data_dict)
            },
            message="미국 실업률 데이터 조회 완료"
        )
        
    except Exception as e:
        logger.error(f"데이터 조회 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"데이터 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/geo")
async def get_state_geo_data():
    """
    주(State) 지리 데이터 조회
    
    - GeoJSON 형식의 주 지리 데이터 반환
    """
    try:
        service = get_service()
        logger.info("주 지리 데이터 조회 요청")
        
        # 지리 데이터 로드
        state_geo = service.load_state_geo_data()
        
        logger.info("주 지리 데이터 조회 완료")
        return create_response(
            data=state_geo,
            message="주 지리 데이터 조회 완료"
        )
        
    except Exception as e:
        logger.error(f"지리 데이터 조회 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"지리 데이터 조회 중 오류가 발생했습니다: {str(e)}"
        )

