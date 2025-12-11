# 서울 범죄지도 히트맵 구현 전략

## 📋 목차
1. [프로젝트 구조 및 파일 생성](#1-프로젝트-구조-및-파일-생성)
2. [데이터 처리 전략](#2-데이터-처리-전략)
3. [카카오 지도 API 통합](#3-카카오-지도-api-통합)
4. [히트맵 구현 전략](#4-히트맵-구현-전략)
5. [데이터 로딩 전략](#5-데이터-로딩-전략)
6. [UI/UX 고려사항](#6-uiux-고려사항)
7. [기술 스택](#7-기술-스택)
8. [구현 순서](#8-구현-순서)
9. [주의사항](#9-주의사항)

---

## 1. 프로젝트 구조 및 파일 생성

```
www.labzang.com/
├── app/
│   └── portfolio/
│       └── page.tsx          # 포트폴리오 페이지 (히트맵 표시)
├── components/
│   └── seoul-crime-map/
│       ├── CrimeHeatMap.tsx  # 메인 히트맵 컴포넌트
│       └── types.ts          # 타입 정의
├── lib/
│   └── crime-data.ts         # CSV 파싱 및 데이터 처리 유틸
└── public/
    └── data/
        └── crime.csv         # CSV 파일 복사 (또는 API로 제공)
```

---

## 2. 데이터 처리 전략

### 2.1 CSV 데이터 전처리

#### 자치구별 데이터 집계
- 같은 자치구의 여러 관서 데이터를 합산해야 함
- 예시:
  - **중구** = 중부서 + 남대문서 데이터 합산
  - **종로구** = 종로서 + 혜화서 데이터 합산
  - **성북구** = 성북서 + 종암서 데이터 합산
  - **강남구** = 강남서 + 수서서 데이터 합산
  - **서초구** = 서초서 + 방배서 데이터 합산
  - **은평구** = 서부서 + 은평서 데이터 합산

#### 범죄 발생 건수 합계 계산
각 자치구별로 다음 항목들을 합산:
- 살인 발생
- 강도 발생
- 강간 발생
- 절도 발생 (쉼표 제거 필요: "1,395" → 1395)
- 폭력 발생 (쉼표 제거 필요: "1,355" → 1355)

**계산 공식:**
```
총 범죄 발생 건수 = 살인 발생 + 강도 발생 + 강간 발생 + 절도 발생 + 폭력 발생
```

#### 평균 계산
전체 자치구의 평균 범죄 발생 건수 계산:
```
평균 = 전체 자치구 범죄 발생 건수 합계 / 자치구 개수 (25개)
```

### 2.2 자치구 좌표 매핑

서울 25개 자치구의 중심 좌표(위도, 경도) 매핑 테이블 생성:

```typescript
const seoulDistricts = {
  '종로구': { lat: 37.5735, lng: 126.9788 },
  '중구': { lat: 37.5640, lng: 126.9970 },
  '용산구': { lat: 37.5326, lng: 126.9905 },
  '성동구': { lat: 37.5633, lng: 127.0366 },
  // ... 나머지 자치구
}
```

- 카카오 지도 API의 좌표 변환 API 활용 가능
- 또는 공공데이터포털의 서울시 행정구역 좌표 데이터 활용

---

## 3. 카카오 지도 API 통합

### 3.1 필요한 API

- **카카오 지도 JavaScript API** (필수)
- **카카오 지도 좌표 변환 API** (선택, 주소 → 좌표 변환 시)

### 3.2 설치 및 설정

#### 방법 1: CDN 사용 (권장)
```html
<!-- app/layout.tsx 또는 portfolio/page.tsx -->
<script
  type="text/javascript"
  src={`//dapi.kakao.com/v2/maps/sdk.js?appkey=${process.env.NEXT_PUBLIC_KAKAO_MAP_API_KEY}&autoload=false`}
></script>
```

#### 방법 2: npm 패키지
```bash
npm install react-kakao-maps-sdk
# 또는
npm install @types/kakao.maps.d.ts
```

### 3.3 API 키 설정

`.env.local` 파일에 추가:
```env
NEXT_PUBLIC_KAKAO_MAP_API_KEY=your_kakao_map_api_key
```

**카카오 개발자 콘솔 설정:**
1. https://developers.kakao.com 접속
2. 애플리케이션 생성
3. 플랫폼 설정 (웹 도메인 등록)
4. JavaScript 키 발급
5. 카카오 로그인 활성화 (필요 시)

---

## 4. 히트맵 구현 전략

### 4.1 지도 초기화

```typescript
// 지도 중심 좌표: 서울시청
const center = new kakao.maps.LatLng(37.5665, 126.9780);

// 지도 레벨: 7-8 (서울 전체 보기)
const level = 7;

const map = new kakao.maps.Map(container, {
  center: center,
  level: level
});
```

### 4.2 히트맵 레이어 생성 방법

#### 방법 1: 커스텀 오버레이 + 원형 마커 (권장)
- 각 자치구 중심에 원형 마커 배치
- 범죄 건수에 따라 반경과 색상 조정
- 구현이 간단하고 성능이 좋음

```typescript
// 원형 마커 생성
const circle = new kakao.maps.Circle({
  center: districtCenter,
  radius: calculateRadius(crimeCount), // 범죄 건수에 따라 반경 계산
  strokeWeight: 2,
  strokeColor: '#FFFFFF',
  strokeOpacity: 0.8,
  fillColor: calculateColor(crimeCount), // 범죄 건수에 따라 색상 계산
  fillOpacity: 0.7
});
```

#### 방법 2: 폴리곤 오버레이
- 자치구 경계 좌표로 폴리곤 생성
- 범죄 건수에 따라 색상 적용
- 더 정확한 시각화이지만 경계 좌표 데이터 필요

```typescript
// 폴리곤 생성
const polygon = new kakao.maps.Polygon({
  path: districtBoundary, // 자치구 경계 좌표 배열
  strokeWeight: 2,
  strokeColor: '#FFFFFF',
  strokeOpacity: 0.8,
  fillColor: calculateColor(crimeCount),
  fillOpacity: 0.7
});
```

#### 방법 3: 히트맵 라이브러리
- `heatmap.js` 또는 유사 라이브러리 활용
- 점 데이터 기반 히트맵 생성

### 4.3 색상 스케일링

#### 색상 그라데이션 정의
```typescript
const colorScale = {
  min: '#E8E0FF',  // 연한 보라색 (최소값)
  mid: '#9C7FD8',  // 중간 보라색
  max: '#4A148C'   // 진한 보라색 (최대값)
};
```

#### 정규화 함수
```typescript
function normalizeValue(value: number, min: number, max: number): number {
  return (value - min) / (max - min);
}

function calculateColor(crimeCount: number, min: number, max: number): string {
  const normalized = normalizeValue(crimeCount, min, max);
  
  // RGB 보간 계산
  // 또는 미리 정의된 색상 팔레트에서 선택
  return interpolateColor(colorScale.min, colorScale.max, normalized);
}
```

### 4.4 데이터 표시

#### 텍스트 오버레이
각 자치구 위에 범죄 건수 텍스트 표시:

```typescript
// 커스텀 오버레이로 텍스트 표시
const customOverlay = new kakao.maps.CustomOverlay({
  position: districtCenter,
  content: `<div class="crime-count-label">${crimeCount}건</div>`,
  yAnchor: 0.5
});
```

#### 평균값 표시
좌측 상단에 평균값 표시:

```tsx
<div className="absolute top-4 left-4 bg-black/70 text-white p-4 rounded-lg">
  <div className="text-sm">평균</div>
  <div className="text-2xl font-bold">{average.toFixed(1)}건</div>
</div>
```

---

## 5. 데이터 로딩 전략

### 5.1 CSV 파일 제공 방법

#### 옵션 1: Public 폴더에 배치 (정적 파일)
```
public/data/crime.csv
```

```typescript
// 클라이언트에서 fetch
const response = await fetch('/data/crime.csv');
const csvText = await response.text();
```

#### 옵션 2: API 엔드포인트 생성
```
app/api/crime-data/route.ts
```

```typescript
// API Route에서 CSV 파일 읽어서 JSON 반환
export async function GET() {
  const csvPath = path.join(process.cwd(), 'public', 'data', 'crime.csv');
  const csvData = fs.readFileSync(csvPath, 'utf-8');
  // 파싱 후 JSON 반환
  return Response.json(parsedData);
}
```

#### 옵션 3: mlservice에서 CSV 제공 API 활용
```
GET http://localhost:9010/api/seoul-crime/data
```

### 5.2 클라이언트 사이드 파싱

#### 라이브러리 설치
```bash
npm install papaparse
# 또는
npm install csv-parse
```

#### CSV 파싱 예시
```typescript
import Papa from 'papaparse';

async function loadCrimeData() {
  const response = await fetch('/data/crime.csv');
  const csvText = await response.text();
  
  return new Promise((resolve, reject) => {
    Papa.parse(csvText, {
      header: true,
      skipEmptyLines: true,
      complete: (results) => {
        resolve(results.data);
      },
      error: (error) => {
        reject(error);
      }
    });
  });
}
```

### 5.3 데이터 변환 및 집계

```typescript
interface CrimeRecord {
  관서명: string;
  '살인 발생': string;
  '강도 발생': string;
  '강간 발생': string;
  '절도 발생': string;
  '폭력 발생': string;
  자치구: string;
}

interface DistrictCrimeData {
  district: string;
  totalCrimes: number;
  coordinates: { lat: number; lng: number };
}

function aggregateByDistrict(records: CrimeRecord[]): DistrictCrimeData[] {
  const districtMap = new Map<string, number>();
  
  records.forEach(record => {
    const district = record.자치구;
    const crimes = 
      parseInt(record['살인 발생']) +
      parseInt(record['강도 발생']) +
      parseInt(record['강간 발생']) +
      parseInt(record['절도 발생'].replace(/,/g, '')) +
      parseInt(record['폭력 발생'].replace(/,/g, ''));
    
    districtMap.set(district, (districtMap.get(district) || 0) + crimes);
  });
  
  return Array.from(districtMap.entries()).map(([district, totalCrimes]) => ({
    district,
    totalCrimes,
    coordinates: seoulDistricts[district]
  }));
}
```

---

## 6. UI/UX 고려사항

### 6.1 레이아웃

#### 다크 테마
- 배경색: `#1a1a1a` 또는 `#0f0f0f` (이미지와 유사)
- 텍스트: 흰색 또는 밝은 회색

#### 지도 영역
- 전체 화면 또는 큰 영역 차지
- 최소 높이: `100vh` 또는 `800px`

#### 평균값 표시
- 좌측 상단 고정 위치
- 반투명 배경 (`bg-black/70`)
- 큰 폰트 사이즈로 강조

### 6.2 인터랙션

#### 호버 효과
```typescript
// 마커/폴리곤에 마우스 오버 시
- 자치구명 표시
- 상세 범죄 건수 표시
- 인포윈도우 또는 툴팁 표시
```

#### 클릭 이벤트
```typescript
// 자치구 클릭 시
- 상세 정보 모달 표시
- 범죄 유형별 상세 통계
- 그래프 또는 차트 표시
```

#### 범례 추가
```tsx
<div className="legend">
  <div className="legend-title">범죄 발생 건수</div>
  <div className="legend-gradient">
    <span>낮음</span>
    <div className="gradient-bar"></div>
    <span>높음</span>
  </div>
  <div className="legend-values">
    <span>{minCount}건</span>
    <span>{maxCount}건</span>
  </div>
</div>
```

### 6.3 반응형 디자인

#### 브레이크포인트
- 모바일: `< 768px`
- 태블릿: `768px - 1024px`
- 데스크톱: `> 1024px`

#### 모바일 최적화
- 터치 제스처 지원 (핀치 줌, 팬)
- 지도 레벨 자동 조정
- 텍스트 크기 조정

---

## 7. 기술 스택

### 필수
- **Next.js 16** (App Router)
- **React 19**
- **TypeScript**
- **카카오 지도 JavaScript API**
- **Tailwind CSS** (스타일링)

### 선택
- **papaparse** (CSV 파싱)
- **recharts** (차트, 범례용)
- **react-kakao-maps-sdk** (카카오 지도 React 래퍼)

### 설치 명령어
```bash
# CSV 파싱
npm install papaparse
npm install --save-dev @types/papaparse

# 카카오 지도 (선택)
npm install react-kakao-maps-sdk

# 차트 (선택)
npm install recharts
```

---

## 8. 구현 순서

### Phase 1: 기본 설정
1. ✅ `app/portfolio/page.tsx` 페이지 생성
2. ✅ 카카오 지도 API 키 설정 (`.env.local`)
3. ✅ 카카오 지도 스크립트 로드 설정
4. ✅ CSV 파일을 `public/data/crime.csv`로 복사

### Phase 2: 데이터 처리
5. ✅ CSV 파싱 유틸 함수 작성 (`lib/crime-data.ts`)
6. ✅ 자치구별 데이터 집계 로직 구현
7. ✅ 자치구 좌표 매핑 데이터 생성
8. ✅ 평균값 계산 로직 구현

### Phase 3: 지도 초기화
9. ✅ 카카오 지도 API 초기화
10. ✅ 지도 컨테이너 렌더링
11. ✅ 서울 전체가 보이도록 중심/레벨 설정

### Phase 4: 히트맵 구현
12. ✅ 색상 스케일링 로직 구현
13. ✅ 자치구별 원형 마커/폴리곤 생성
14. ✅ 범죄 건수에 따른 색상 적용
15. ✅ 텍스트 오버레이 (범죄 건수 표시)

### Phase 5: UI 개선
16. ✅ 평균값 표시 컴포넌트
17. ✅ 범례 컴포넌트
18. ✅ 다크 테마 스타일링

### Phase 6: 인터랙션
19. ✅ 호버 효과 (인포윈도우)
20. ✅ 클릭 이벤트 (상세 정보)
21. ✅ 반응형 디자인 적용

### Phase 7: 최적화
22. ✅ 성능 최적화 (메모이제이션)
23. ✅ 로딩 상태 처리
24. ✅ 에러 핸들링

---

## 9. 주의사항

### 9.1 API 키 보안
- ✅ 카카오 지도 API 키는 환경 변수로 관리
- ✅ `.env.local` 파일은 `.gitignore`에 추가
- ✅ `NEXT_PUBLIC_` 접두사 사용 (클라이언트에서 접근 가능)

### 9.2 데이터 처리
- ✅ CSV 파싱 시 숫자 형식 처리 (쉼표 제거: `"1,395"` → `1395`)
- ✅ 같은 자치구의 여러 관서 데이터 합산 필요
- ✅ 빈 값 또는 잘못된 데이터 처리

### 9.3 지도 API
- ✅ 카카오 지도 API 로딩 순서 보장 (스크립트 로드 후 초기화)
- ✅ `autoload: false` 옵션 사용 시 수동으로 로드 필요
- ✅ 지도 컨테이너 크기 명시적 설정

### 9.4 자치구 경계 좌표
- ✅ 폴리곤 사용 시 자치구 경계 좌표 데이터 필요
- ✅ 공공데이터포털 또는 카카오 로컬 API 활용
- ✅ GeoJSON 형식 데이터 활용 가능

### 9.5 성능 최적화
- ✅ 대량의 오버레이 생성 시 성능 고려
- ✅ 메모이제이션 활용 (React.memo, useMemo)
- ✅ 지도 이벤트 리스너 정리 (cleanup)

### 9.6 브라우저 호환성
- ✅ 모던 브라우저 지원 (Chrome, Firefox, Safari, Edge)
- ✅ 모바일 브라우저 테스트
- ✅ 터치 이벤트 처리

---

## 10. 참고 자료

### 카카오 지도 API
- [카카오 지도 JavaScript API 문서](https://apis.map.kakao.com/web/documentation/)
- [카카오 지도 예제](https://apis.map.kakao.com/web/sample/)

### 데이터 소스
- [공공데이터포털](https://www.data.go.kr/)
- [서울 열린데이터 광장](https://data.seoul.go.kr/)

### 라이브러리
- [PapaParse 문서](https://www.papaparse.com/)
- [React Kakao Maps SDK](https://www.npmjs.com/package/react-kakao-maps-sdk)

---

## 11. 예상 결과물

### 화면 구성
```
┌─────────────────────────────────────────┐
│ [평균: 691.5건]                         │
│                                         │
│     ┌─────────────────────┐            │
│     │                     │            │
│     │   서울 지도 히트맵   │            │
│     │   (보라색 그라데이션) │            │
│     │                     │            │
│     │  각 구별 범죄 건수   │            │
│     │  표시 (예: 1,494건)  │            │
│     │                     │            │
│     └─────────────────────┘            │
│                                         │
│  [범례: 낮음 ──────── 높음]            │
└─────────────────────────────────────────┘
```

### 주요 기능
- ✅ 서울 25개 자치구 범죄 발생 건수 시각화
- ✅ 범죄 건수에 따른 색상 그라데이션
- ✅ 각 구별 범죄 건수 텍스트 표시
- ✅ 전체 평균값 표시
- ✅ 호버/클릭 인터랙션
- ✅ 반응형 디자인

---

**작성일**: 2025-12-11  
**버전**: 1.0.0

