# 서울 범죄지도 히트맵 설정 가이드

## 📋 필수 설정

### 1. 카카오 지도 API 키 발급

1. [카카오 개발자 콘솔](https://developers.kakao.com/) 접속
2. 애플리케이션 생성
3. 플랫폼 설정 → Web 플랫폼 등록
   - 사이트 도메인: `http://localhost:3000` (개발용)
4. 앱 키 → JavaScript 키 복사

### 2. 환경 변수 설정

프로젝트 루트에 `.env.local` 파일을 생성하고 다음 내용을 추가하세요:

```env
NEXT_PUBLIC_KAKAO_MAP_API_KEY=your_kakao_map_api_key_here
```

**주의**: `NEXT_PUBLIC_` 접두사가 필수입니다. 이 접두사가 있어야 클라이언트 사이드에서 환경 변수에 접근할 수 있습니다.

### 3. 개발 서버 실행

```bash
cd www.labzang.com
npm run dev
```

브라우저에서 `http://localhost:3000/portfolio` 접속

## 📁 생성된 파일 구조

```
www.labzang.com/
├── app/
│   └── portfolio/
│       └── page.tsx                    # 포트폴리오 페이지
├── components/
│   └── seoul-crime-map/
│       └── CrimeHeatMap.tsx            # 히트맵 컴포넌트
├── lib/
│   └── crime-data.ts                   # 데이터 처리 유틸
├── public/
│   └── data/
│       └── crime.csv                   # 범죄 데이터 CSV
├── types/
│   └── kakao.d.ts                      # 카카오 지도 타입 정의
└── .env.local                          # 환경 변수 (직접 생성 필요)
```

## 🎨 기능

- ✅ 서울 25개 자치구 범죄 발생 건수 시각화
- ✅ 범죄 건수에 따른 보라색 그라데이션 히트맵
- ✅ 각 구별 범죄 건수 텍스트 표시
- ✅ 전체 평균값 표시
- ✅ 반응형 디자인

## 🔧 문제 해결

### 카카오 지도가 표시되지 않는 경우

1. `.env.local` 파일이 프로젝트 루트에 있는지 확인
2. 환경 변수 이름이 `NEXT_PUBLIC_KAKAO_MAP_API_KEY`인지 확인
3. 개발 서버를 재시작 (`Ctrl+C` 후 `npm run dev`)
4. 브라우저 콘솔에서 오류 메시지 확인

### 데이터가 표시되지 않는 경우

1. `public/data/crime.csv` 파일이 존재하는지 확인
2. 브라우저 개발자 도구 → Network 탭에서 CSV 파일 로드 확인
3. 콘솔에서 오류 메시지 확인

## 📝 참고

- 카카오 지도 API는 무료 사용량 제한이 있습니다 (일일 300,000건)
- 개발 환경에서는 `localhost:3000` 도메인으로 사용 가능
- 프로덕션 배포 시 카카오 개발자 콘솔에 실제 도메인 등록 필요

