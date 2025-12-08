"""
Titanic Service - FastAPI 애플리케이션
"""
import csv
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pathlib import Path
from typing import List, Dict

# 라우터 import
from app.titanic.router import router as titanic_router

# FastAPI 앱 생성
app = FastAPI(
    title="Titanic Service API",
    description="타이타닉 데이터 서비스 API",
    version="1.0.0"
)

# 라우터 등록
app.include_router(titanic_router)


def get_top_10_passengers() -> List[Dict]:
    """train.csv 파일에서 상위 10명의 승객 정보를 반환"""
    
    # 현재 파일의 디렉토리 경로
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, 'train.csv')
    
    # CSV 파일 읽기
    try:
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            passengers = list(reader)
            
            # 상위 10명만 선택
            top_10 = passengers[:10]
            
            # 데이터 포맷팅
            formatted_passengers = []
            for idx, passenger in enumerate(top_10, 1):
                formatted_passenger = {
                    '순번': idx,
                    '승객ID': passenger.get('PassengerId', 'N/A'),
                    '생존': '생존' if passenger.get('Survived') == '1' else '사망',
                    '등급': passenger.get('Pclass', 'N/A'),
                    '이름': passenger.get('Name', 'N/A'),
                    '성별': '남성' if passenger.get('Sex') == 'male' else '여성',
                    '나이': passenger.get('Age', 'N/A'),
                    '요금': passenger.get('Fare', 'N/A')
                }
                formatted_passengers.append(formatted_passenger)
            
            return formatted_passengers
            
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"CSV 파일을 찾을 수 없습니다: {csv_path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"오류 발생: {str(e)}")


@app.get(
    "/dashboard/google",
    response_class=HTMLResponse,
    tags=["dashboard"],
    summary="타이타닉 승객 대시보드 (HTML)",
    description="타이타닉 데이터셋의 상위 10명 승객 정보를 HTML 테이블 형식으로 반환합니다."
)
async def dashboard_google():
    """
    타이타닉 승객 정보를 HTML 형식으로 보여주는 대시보드
    
    - train.csv 파일에서 상위 10명의 승객 정보를 조회
    - 생존 여부, 등급, 이름, 성별, 나이, 요금 등의 정보를 포함
    - HTML 테이블 형식으로 반환
    """
    try:
        passengers = get_top_10_passengers()
        
        # HTML 테이블 생성
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>타이타닉 승객 정보 - 상위 10명</title>
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                h1 {
                    color: #333;
                    text-align: center;
                    margin-bottom: 30px;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                }
                th, td {
                    padding: 12px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }
                th {
                    background-color: #4CAF50;
                    color: white;
                    font-weight: bold;
                }
                tr:hover {
                    background-color: #f5f5f5;
                }
                .status-alive {
                    color: #4CAF50;
                    font-weight: bold;
                }
                .status-dead {
                    color: #f44336;
                    font-weight: bold;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚢 타이타닉 승객 정보 - 상위 10명</h1>
                <table>
                    <thead>
                        <tr>
                            <th>순번</th>
                            <th>승객ID</th>
                            <th>생존</th>
                            <th>등급</th>
                            <th>이름</th>
                            <th>성별</th>
                            <th>나이</th>
                            <th>요금</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        for passenger in passengers:
            status_class = 'status-alive' if passenger['생존'] == '생존' else 'status-dead'
            html_content += f"""
                        <tr>
                            <td>{passenger['순번']}</td>
                            <td>{passenger['승객ID']}</td>
                            <td class="{status_class}">{passenger['생존']}</td>
                            <td>{passenger['등급']}</td>
                            <td>{passenger['이름']}</td>
                            <td>{passenger['성별']}</td>
                            <td>{passenger['나이']}</td>
                            <td>{passenger['요금']}</td>
                        </tr>
            """
        
        html_content += """
                    </tbody>
                </table>
            </div>
        </body>
        </html>
        """
        
        return html_content
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"오류 발생: {str(e)}")


@app.get(
    "/dashboard/google/json",
    tags=["dashboard"],
    summary="타이타닉 승객 대시보드 (JSON)",
    description="타이타닉 데이터셋의 상위 10명 승객 정보를 JSON 형식으로 반환합니다."
)
async def dashboard_google_json():
    """
    상위 10명의 승객 정보를 JSON 형식으로 반환
    
    - train.csv 파일에서 상위 10명의 승객 정보를 조회
    - JSON 형식으로 구조화된 데이터 반환
    - 총 승객 수와 함께 반환
    """
    return {
        "status": "success",
        "message": "상위 10명의 승객 정보",
        "data": {
            "passengers": get_top_10_passengers(),
            "total_count": len(get_top_10_passengers())
        }
    }


@app.get(
    "/",
    tags=["root"],
    summary="서비스 루트",
    description="Titanic Service의 루트 엔드포인트입니다. 서비스 상태와 사용 가능한 엔드포인트 목록을 반환합니다."
)
async def root():
    """
    서비스 루트 엔드포인트
    
    - 서비스 이름과 상태 정보 반환
    - 사용 가능한 엔드포인트 목록 제공
    """
    return {
        "service": "titanicservice",
        "status": "running",
        "endpoints": {
            "dashboard": "/dashboard/google",
            "dashboard_json": "/dashboard/google/json"
        }
    }
