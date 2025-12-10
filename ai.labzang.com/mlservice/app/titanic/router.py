"""
Titanic 관련 라우터
"""
from fastapi import APIRouter, Query
from fastapi.responses import FileResponse
from typing import Optional
import os
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

@router.get(
    "/evaluate",
    summary="모델 평가",
    description="전처리된 데이터로 여러 머신러닝 모델을 학습하고 평가합니다."
)
async def evaluate_model():
    """
    모델 평가 실행
    - 전처리, 모델링, 학습, 평가를 순차적으로 실행
    - 로지스틱 회귀, 나이브베이즈, 랜덤포레스트, LightGBM, SVM 모델 평가
    - 모델 평가 결과 반환
    """
    service = TitanicService()
    
    # 전처리
    service.preprocess()
    
    # 모델링
    service.modeling()
    
    # 학습
    service.learning()
    
    # 평가
    scores = service.evaluate()
    
    return {
        "status": "success",
        "message": "모델 평가가 완료되었습니다.",
        "data": {
            "model_scores": {
                "logistic_regression": scores.get('logistic_regression'),
                "naive_bayes": scores.get('naive_bayes'),
                "random_forest": scores.get('random_forest'),
                "lightgbm": scores.get('lightgbm'),
                "svm": scores.get('svm')
            }
        }
    }

@router.get(
    "/submit",
    summary="캐글 제출 파일 생성",
    description="최고 성능 모델을 사용하여 테스트 데이터에 대한 예측을 수행하고 캐글 제출용 CSV 파일을 생성합니다."
)
async def submit_model():
    """
    캐글 제출 파일 생성
    - 전처리, 모델링, 학습, 평가를 순차적으로 실행
    - 최고 성능 모델을 선택하여 테스트 데이터 예측
    - 캐글 제출 형식의 CSV 파일 생성 및 저장
    """
    service = TitanicService()
    
    # 전처리
    service.preprocess()
    
    # 모델링
    service.modeling()
    
    # 학습
    service.learning()
    
    # 평가
    service.evaluate()
    
    # 제출 파일 생성
    result = service.submit()
    
    return {
        "status": "success",
        "message": "캐글 제출 파일이 생성되었습니다.",
        "data": {
            "best_model": result['best_model'],
            "best_accuracy": result['best_accuracy'],
            "all_models": result['all_models']
        }
    }

@router.get(
    "/download/{filename}",
    summary="제출 파일 다운로드",
    description="생성된 캐글 제출 CSV 파일을 다운로드합니다."
)
async def download_submission(filename: str):
    """
    제출 파일 다운로드
    - 생성된 제출 CSV 파일을 다운로드합니다.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    download_dir = os.path.join(current_dir, 'download')
    filepath = os.path.join(download_dir, filename)
    
    if not os.path.exists(filepath):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"파일을 찾을 수 없습니다: {filename}")
    
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type='text/csv'
    )