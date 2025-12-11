"""
서울 범죄비율 히트맵 관련 라우터
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from typing import Optional
from pathlib import Path
import sys

# 공통 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from app.heatmap.service import SeoulCrimeHeatmapService

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

router = APIRouter(tags=["heatmap"])

# 서비스 인스턴스 생성 (싱글톤 패턴)
_service_instance: Optional[SeoulCrimeHeatmapService] = None


def get_service() -> SeoulCrimeHeatmapService:
    """SeoulCrimeHeatmapService 싱글톤 인스턴스 반환"""
    global _service_instance
    if _service_instance is None:
        _service_instance = SeoulCrimeHeatmapService()
    return _service_instance


@router.get("/")
async def heatmap_root():
    """서울 범죄비율 히트맵 서비스 루트"""
    return create_response(
        data={"service": "mlservice", "module": "seoul_crime_heatmap", "status": "running"},
        message="Seoul Crime Heatmap Service is running"
    )


@router.get("/heatmap", response_class=HTMLResponse)
async def get_crime_heatmap():
    """
    서울 범죄비율 히트맵 생성 및 반환
    
    - 범죄 데이터를 정규화하여 히트맵으로 시각화
    - 자치구별 범죄 유형별 정규화된 비율 표시
    - HTML 형식으로 반환
    """
    try:
        service = get_service()
        logger.info("서울 범죄비율 히트맵 생성 요청")
        
        # 히트맵 HTML 생성
        html_content = service.generate_heatmap_html()
        
        logger.info("서울 범죄비율 히트맵 생성 완료")
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"히트맵 생성 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"히트맵 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/data")
async def get_heatmap_data():
    """
    정규화된 범죄비율 데이터 조회
    
    - 자치구별 범죄 유형별 정규화된 비율 데이터를 JSON 형식으로 반환
    """
    try:
        service = get_service()
        logger.info("히트맵 데이터 조회 요청")
        
        # 히트맵 데이터 가져오기
        heatmap_data = service.get_heatmap_data()
        
        # DataFrame을 딕셔너리로 변환
        data_dict = heatmap_data.to_dict(orient="index")
        
        logger.info(f"히트맵 데이터 조회 완료: {len(data_dict)}개 자치구")
        return create_response(
            data={
                "districts": data_dict,
                "total_count": len(data_dict),
                "columns": list(heatmap_data.columns)
            },
            message="히트맵 데이터 조회 완료"
        )
        
    except Exception as e:
        logger.error(f"데이터 조회 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"데이터 조회 중 오류가 발생했습니다: {str(e)}"
        )

