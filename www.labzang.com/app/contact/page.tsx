'use client';

import { useState } from 'react';

export default function ContactPage() {
  const [usaLoading, setUsaLoading] = useState(true);
  const [usaError, setUsaError] = useState<string | null>(null);
  const [krLoading, setKrLoading] = useState(true);
  const [krError, setKrError] = useState<string | null>(null);
  const [heatmapLoading, setHeatmapLoading] = useState(true);
  const [heatmapError, setHeatmapError] = useState<string | null>(null);

  const usaMapUrl = 'http://localhost:8080/api/ml/usa/map';
  const krMapUrl = 'http://localhost:8080/api/ml/kr/map';
  const heatmapUrl = 'http://localhost:8080/api/ml/kr/heatmap';

  const handleUsaIframeLoad = () => {
    setUsaLoading(false);
  };

  const handleUsaIframeError = () => {
    setUsaLoading(false);
    setUsaError('미국 실업률 지도를 불러올 수 없습니다.');
  };

  const handleKrIframeLoad = () => {
    setKrLoading(false);
  };

  const handleKrIframeError = () => {
    setKrLoading(false);
    setKrError('서울 범죄지도를 불러올 수 없습니다.');
  };

  const handleHeatmapIframeLoad = () => {
    setHeatmapLoading(false);
  };

  const handleHeatmapIframeError = () => {
    setHeatmapLoading(false);
    setHeatmapError('서울 범죄비율 히트맵을 불러올 수 없습니다.');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">데이터 시각화</h1>
        
        {/* 미국 실업률 지도 섹션 */}
        <div className="mb-12">
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">미국 실업률 지도</h2>
          
          {/* 로딩 상태 */}
          {usaLoading && (
            <div className="flex items-center justify-center bg-white rounded-lg shadow-lg" style={{ minHeight: '600px' }}>
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <p className="text-gray-600">지도를 불러오는 중...</p>
              </div>
            </div>
          )}

          {/* 에러 상태 */}
          {usaError && (
            <div className="flex items-center justify-center bg-white rounded-lg shadow-lg" style={{ minHeight: '600px' }}>
              <div className="text-center">
                <p className="text-red-600 mb-2">오류 발생</p>
                <p className="text-gray-600">{usaError}</p>
              </div>
            </div>
          )}

          {/* 지도 표시 영역 (iframe 사용) */}
          <div className="bg-white rounded-lg shadow-lg overflow-hidden">
            <iframe
              src={usaMapUrl}
              className="w-full border-0"
              style={{ minHeight: '600px', display: usaLoading || usaError ? 'none' : 'block' }}
              onLoad={handleUsaIframeLoad}
              onError={handleUsaIframeError}
              title="미국 실업률 지도"
              allowFullScreen
            />
          </div>
        </div>

        {/* 서울 범죄지도 섹션 */}
        <div className="mb-12">
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">서울 범죄지도</h2>
          
          {/* 로딩 상태 */}
          {krLoading && (
            <div className="flex items-center justify-center bg-white rounded-lg shadow-lg" style={{ minHeight: '600px' }}>
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
                <p className="text-gray-600">지도를 불러오는 중...</p>
              </div>
            </div>
          )}

          {/* 에러 상태 */}
          {krError && (
            <div className="flex items-center justify-center bg-white rounded-lg shadow-lg" style={{ minHeight: '600px' }}>
              <div className="text-center">
                <p className="text-red-600 mb-2">오류 발생</p>
                <p className="text-gray-600">{krError}</p>
              </div>
            </div>
          )}

          {/* 지도 표시 영역 (iframe 사용) */}
          <div className="bg-white rounded-lg shadow-lg overflow-hidden">
            <iframe
              src={krMapUrl}
              className="w-full border-0"
              style={{ minHeight: '600px', display: krLoading || krError ? 'none' : 'block' }}
              onLoad={handleKrIframeLoad}
              onError={handleKrIframeError}
              title="서울 범죄지도"
              allowFullScreen
            />
          </div>
        </div>

        {/* 서울 범죄비율 히트맵 섹션 */}
        <div>
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">서울 범죄비율 히트맵</h2>
          
          {/* 로딩 상태 */}
          {heatmapLoading && (
            <div className="flex items-center justify-center bg-white rounded-lg shadow-lg" style={{ minHeight: '600px' }}>
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pink-600 mx-auto mb-4"></div>
                <p className="text-gray-600">히트맵을 불러오는 중...</p>
              </div>
            </div>
          )}

          {/* 에러 상태 */}
          {heatmapError && (
            <div className="flex items-center justify-center bg-white rounded-lg shadow-lg" style={{ minHeight: '600px' }}>
              <div className="text-center">
                <p className="text-red-600 mb-2">오류 발생</p>
                <p className="text-gray-600">{heatmapError}</p>
              </div>
            </div>
          )}

          {/* 히트맵 표시 영역 (iframe 사용) */}
          <div className="bg-white rounded-lg shadow-lg overflow-hidden">
            <iframe
              src={heatmapUrl}
              className="w-full border-0"
              style={{ minHeight: '800px', display: heatmapLoading || heatmapError ? 'none' : 'block' }}
              onLoad={handleHeatmapIframeLoad}
              onError={handleHeatmapIframeError}
              title="서울 범죄비율 히트맵"
              allowFullScreen
            />
          </div>
        </div>
      </div>
    </div>
  );
}

