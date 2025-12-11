'use client';

import dynamic from 'next/dynamic';

// 동적 import로 클라이언트 사이드에서만 로드
const DynamicCrimeHeatMap = dynamic(
  () => import('@/components/seoul-crime-map/CrimeHeatMap'),
  { 
    ssr: false,
    loading: () => (
      <div className="flex items-center justify-center h-screen bg-gray-900 text-white">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
          <p>지도를 불러오는 중...</p>
        </div>
      </div>
    )
  }
);

export default function PortfolioPage() {
  const apiKey = process.env.NEXT_PUBLIC_KAKAO_MAP_API_KEY || '';

  // 디버깅: API 키 확인
  if (typeof window !== 'undefined') {
    console.log('포트폴리오 페이지 - API 키:', apiKey ? `${apiKey.substring(0, 10)}...` : '없음');
  }

  if (!apiKey) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-900 text-white">
        <div className="text-center">
          <p className="text-red-400 mb-2">환경 변수 오류</p>
          <p className="text-sm">
            NEXT_PUBLIC_KAKAO_MAP_API_KEY가 설정되지 않았습니다.
            <br />
            .env.local 파일에 카카오 지도 API 키를 추가해주세요.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900">
      <div className="h-screen w-full">
        <DynamicCrimeHeatMap apiKey={apiKey} />
      </div>
    </div>
  );
}

