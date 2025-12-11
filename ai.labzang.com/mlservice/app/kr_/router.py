"""
서울 범죄지도 관련 라우터
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
from typing import Optional
from pathlib import Path
import sys

# 공통 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from app.kr_.service import SeoulCrimeMapService

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

router = APIRouter(tags=["kr"])

# 서비스 인스턴스 생성 (싱글톤 패턴)
_service_instance: Optional[SeoulCrimeMapService] = None


def get_service() -> SeoulCrimeMapService:
    """SeoulCrimeMapService 싱글톤 인스턴스 반환"""
    global _service_instance
    if _service_instance is None:
        _service_instance = SeoulCrimeMapService()
    return _service_instance


@router.get("/")
async def kr_root():
    """서울 범죄지도 서비스 루트"""
    return create_response(
        data={"service": "mlservice", "module": "seoul_crime_map", "status": "running"},
        message="Seoul Crime Map Service is running"
    )


@router.get("/map", response_class=HTMLResponse)
async def get_crime_map(
    zoom_start: int = Query(11, ge=1, le=18, description="초기 줌 레벨 (1-18)")
):
    """
    서울 범죄지도 생성 및 반환
    
    - Folium을 사용한 인터랙티브 지도 생성
    - 자치구별 범죄 발생 건수를 보라색 그라데이션으로 시각화
    - HTML 형식으로 반환
    """
    try:
        service = get_service()
        logger.info("서울 범죄지도 생성 요청")
        
        # 지도 생성
        map_obj = service.generate_map(zoom_start=zoom_start)
        
        # HTML로 변환
        map_html = map_obj._repr_html_() if hasattr(map_obj, '_repr_html_') else str(map_obj)
        
        logger.info("서울 범죄지도 생성 완료")
        return HTMLResponse(content=map_html)
        
    except Exception as e:
        logger.error(f"지도 생성 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"지도 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/data")
async def get_crime_data():
    """
    서울 자치구별 범죄 데이터 조회
    
    - 자치구별 범죄 발생 건수 데이터를 JSON 형식으로 반환
    """
    try:
        service = get_service()
        logger.info("서울 범죄 데이터 조회 요청")
        
        # 데이터 집계
        district_data = service.aggregate_by_district()
        average = service.calculate_average()
        
        # DataFrame을 딕셔너리로 변환
        data_dict = district_data.to_dict(orient="records")
        
        logger.info(f"서울 범죄 데이터 조회 완료: {len(data_dict)}개 자치구")
        return create_response(
            data={
                "districts": data_dict,
                "total_count": len(data_dict),
                "average": float(average)
            },
            message="서울 범죄 데이터 조회 완료"
        )
        
    except Exception as e:
        logger.error(f"데이터 조회 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"데이터 조회 중 오류가 발생했습니다: {str(e)}"
        )

