"""
Titanic 관련 라우터
"""
from fastapi import APIRouter, Query
from typing import Optional
from app.titanic.service import get_top_10_passengers, get_passengers_by_survival_probability, TitanicService

router = APIRouter(prefix="/titanic", tags=["titanic"])


@router.get(
    "/",
    summary="타이타닉 승객 10명 조회",
    description="타이타닉 데이터셋의 상위 10명 승객 정보를 반환합니다."
)
async def titanic_root():
    """
    타이타닉 승객 상위 10명 정보 조회
    
    - train.csv 파일에서 상위 10명의 승객 정보를 조회
    - 승객ID, 생존여부, 등급, 이름, 성별, 나이, 요금 등의 정보를 포함
    """
    passengers = get_top_10_passengers()
    
    return {
        "status": "success",
        "message": "타이타닉 승객 상위 10명 정보",
        "data": {
            "passengers": passengers,
            "total_count": len(passengers)
        }
    }


@router.get(
    "/survival-analysis",
    summary="생존 가능성 분석",
    description="생존 가능성이 높은 승객과 낮은 승객을 분석하여 반환합니다."
)
async def survival_analysis(
    limit: Optional[int] = Query(
        default=10,
        ge=1,
        le=50,
        description="각 그룹(높은/낮은)에서 반환할 승객 수 (1-50)"
    )
):
    """
    생존 가능성 분석 엔드포인트
    
    - 생존 가능성 점수를 기반으로 승객들을 분류
    - 성별, 등급, 나이, 요금 등을 고려하여 점수 계산
    - 생존 가능성이 높은 승객과 낮은 승객을 각각 반환
    
    Parameters:
    - limit: 각 그룹에서 반환할 승객 수 (기본값: 10)
    """
    result = get_passengers_by_survival_probability(limit=limit)
    
    return {
        "status": "success",
        "message": f"생존 가능성 분석 결과 (상위/하위 {limit}명)",
        "data": {
            "high_survival_passengers": {
                "description": "생존 가능성이 높은 승객들",
                "passengers": result['high_survival'],
                "count": len(result['high_survival'])
            },
            "low_survival_passengers": {
                "description": "생존 가능성이 낮은 승객들",
                "passengers": result['low_survival'],
                "count": len(result['low_survival'])
            }
        }
    }


@router.get(
    "/preprocess",
    summary="데이터 전처리",
    description="타이타닉 데이터셋의 전처리를 수행합니다."
)
async def preprocess():
    """
    데이터 전처리 엔드포인트
    
    - train.csv와 test.csv 파일을 읽어와서 전처리 수행
    - Survived 컬럼 제거 및 null 값 확인
    - Train과 Test 데이터의 타입, 컬럼, 상위 행, null 개수 정보 출력
    """
    service = TitanicService()
    service.preprocess()
    
    return {
        "status": "success",
        "message": "데이터 전처리가 완료되었습니다. 콘솔을 확인하세요."
    }