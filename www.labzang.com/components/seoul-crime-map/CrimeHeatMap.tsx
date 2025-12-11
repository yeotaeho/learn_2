'use client';

import { useEffect, useRef, useState } from 'react';
import { 
  aggregateByDistrict, 
  calculateAverage, 
  calculateColor,
  loadCrimeData,
  type DistrictCrimeData 
} from '@/lib/crime-data';

declare global {
  interface Window {
    kakao: {
      maps: {
        LatLng: new (lat: number, lng: number) => any;
        Map: new (container: HTMLElement, options: any) => any;
        Circle: new (options: any) => any;
        CustomOverlay: new (options: any) => any;
        load: (callback: () => void) => void;
      };
    };
  }
}

interface CrimeHeatMapProps {
  apiKey: string;
}

export default function CrimeHeatMap({ apiKey }: CrimeHeatMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapRef = useRef<any>(null);
  const [districtData, setDistrictData] = useState<DistrictCrimeData[]>([]);
  const [average, setAverage] = useState<number>(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const circlesRef = useRef<any[]>([]);
  const overlaysRef = useRef<any[]>([]);

  useEffect(() => {
    // API 키 확인
    if (!apiKey) {
      setError('카카오 지도 API 키가 제공되지 않았습니다.');
      setLoading(false);
      return;
    }

    console.log('카카오 지도 API 키:', apiKey ? `${apiKey.substring(0, 10)}...` : '없음');
    
    // 지도 초기화 함수 (지도 컨테이너가 준비될 때까지 대기)
    const initMapWhenReady = () => {
      // 지도 컨테이너가 준비될 때까지 대기
      const checkContainer = () => {
        if (mapContainer.current) {
          console.log('지도 컨테이너 확인됨');
          initializeMap();
          loadData();
        } else {
          console.log('지도 컨테이너 대기 중...');
          // 다음 프레임에서 다시 확인
          requestAnimationFrame(checkContainer);
        }
      };
      checkContainer();
    };
    
    // 이미 스크립트가 로드되어 있는지 확인
    if (window.kakao && window.kakao.maps) {
      console.log('카카오 지도 API가 이미 로드되어 있습니다.');
      window.kakao.maps.load(() => {
        console.log('카카오 지도 API 초기화 완료');
        // 약간의 지연 후 지도 초기화 (DOM 렌더링 대기)
        setTimeout(initMapWhenReady, 100);
      });
      return;
    }

    // 카카오 지도 API 스크립트 로드
    const script = document.createElement('script');
    script.src = `//dapi.kakao.com/v2/maps/sdk.js?appkey=${apiKey}&autoload=false`;
    script.async = true;
    
    script.onload = () => {
      console.log('카카오 지도 API 스크립트 로드 완료');
      if (!window.kakao || !window.kakao.maps) {
        setError('카카오 지도 API 객체를 찾을 수 없습니다.');
        setLoading(false);
        return;
      }
      window.kakao.maps.load(() => {
        console.log('카카오 지도 API 초기화 완료');
        // 약간의 지연 후 지도 초기화 (DOM 렌더링 대기)
        setTimeout(initMapWhenReady, 100);
      });
    };
    
    script.onerror = (err) => {
      console.error('카카오 지도 API 스크립트 로드 실패:', err);
      setError('카카오 지도 API를 로드할 수 없습니다. API 키와 도메인 설정을 확인해주세요.');
      setLoading(false);
    };
    
    document.head.appendChild(script);
    
    return () => {
      // 정리
      circlesRef.current.forEach(circle => circle.setMap(null));
      overlaysRef.current.forEach(overlay => overlay.setMap(null));
    };
  }, [apiKey]);

  const initializeMap = () => {
    if (!mapContainer.current) {
      console.error('지도 컨테이너를 찾을 수 없습니다.');
      setError('지도 컨테이너를 찾을 수 없습니다.');
      return;
    }

    if (!window.kakao || !window.kakao.maps) {
      console.error('카카오 지도 API가 로드되지 않았습니다.');
      setError('카카오 지도 API가 로드되지 않았습니다.');
      return;
    }
    
    try {
      const center = new window.kakao.maps.LatLng(37.5665, 126.9780); // 서울시청
      const options = {
        center: center,
        level: 7, // 서울 전체 보기
      };
      
      mapRef.current = new window.kakao.maps.Map(mapContainer.current, options);
      console.log('지도 초기화 완료:', mapRef.current);
    } catch (err) {
      console.error('지도 초기화 실패:', err);
      setError(`지도 초기화 실패: ${err instanceof Error ? err.message : '알 수 없는 오류'}`);
    }
  };

  const loadData = async () => {
    try {
      setLoading(true);
      const records = await loadCrimeData();
      const aggregated = aggregateByDistrict(records);
      const avg = calculateAverage(aggregated);
      
      setDistrictData(aggregated);
      setAverage(avg);
      
      if (mapRef.current) {
        renderHeatMap(aggregated);
      }
    } catch (err) {
      setError('데이터를 불러올 수 없습니다.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const renderHeatMap = (data: DistrictCrimeData[]) => {
    if (!mapRef.current || data.length === 0) return;
    
    // 기존 오버레이 제거
    circlesRef.current.forEach(circle => circle.setMap(null));
    overlaysRef.current.forEach(overlay => overlay.setMap(null));
    circlesRef.current = [];
    overlaysRef.current = [];
    
    const min = Math.min(...data.map(d => d.totalCrimes));
    const max = Math.max(...data.map(d => d.totalCrimes));
    
    data.forEach(district => {
      const position = new window.kakao.maps.LatLng(
        district.coordinates.lat,
        district.coordinates.lng
      );
      
      // 원형 마커 생성 (히트맵 효과)
      const circle = new window.kakao.maps.Circle({
        center: position,
        radius: 3000, // 3km 반경
        strokeWeight: 2,
        strokeColor: '#FFFFFF',
        strokeOpacity: 0.8,
        fillColor: calculateColor(district.totalCrimes, min, max),
        fillOpacity: 0.6,
      });
      
      circle.setMap(mapRef.current);
      circlesRef.current.push(circle);
      
      // 범죄 건수 텍스트 오버레이
      const overlay = new window.kakao.maps.CustomOverlay({
        position: position,
        content: `
          <div style="
            background: rgba(0, 0, 0, 0.7);
            color: #FFD700;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
            white-space: nowrap;
            pointer-events: none;
          ">
            ${district.district}<br/>
            ${district.totalCrimes.toFixed(1)}건
          </div>
        `,
        yAnchor: 0.5,
      });
      
      overlay.setMap(mapRef.current);
      overlaysRef.current.push(overlay);
    });
  };

  if (error) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-900 text-white">
        <div className="text-center">
          <p className="text-red-400 mb-2">오류 발생</p>
          <p className="text-sm">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative w-full h-full bg-gray-900">
      {/* 평균값 표시 */}
      {average > 0 && (
        <div className="absolute top-4 left-4 z-10 bg-black/70 text-white p-4 rounded-lg shadow-lg">
          <div className="text-sm text-gray-300 mb-1">평균</div>
          <div className="text-2xl font-bold text-yellow-400">{average.toFixed(1)}건</div>
        </div>
      )}
      
      {/* 로딩 상태 */}
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-900/80 z-20">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
            <p className="text-white">데이터를 불러오는 중...</p>
          </div>
        </div>
      )}
      
      {/* 지도 컨테이너 - 항상 렌더링 (로딩 중에도) */}
      <div 
        ref={mapContainer} 
        className="w-full h-full" 
        style={{ minHeight: '100%', minWidth: '100%', position: 'relative' }}
      />
    </div>
  );
}

