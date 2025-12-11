import Papa from 'papaparse';

export interface CrimeRecord {
  관서명: string;
  '살인 발생': string;
  '강도 발생': string;
  '강간 발생': string;
  '절도 발생': string;
  '폭력 발생': string;
  자치구: string;
}

export interface DistrictCrimeData {
  district: string;
  totalCrimes: number;
  coordinates: { lat: number; lng: number };
}

// 서울 25개 자치구 중심 좌표
export const seoulDistricts: Record<string, { lat: number; lng: number }> = {
  '종로구': { lat: 37.5735, lng: 126.9788 },
  '중구': { lat: 37.5640, lng: 126.9970 },
  '용산구': { lat: 37.5326, lng: 126.9905 },
  '성동구': { lat: 37.5633, lng: 127.0366 },
  '광진구': { lat: 37.5384, lng: 127.0822 },
  '동대문구': { lat: 37.5744, lng: 127.0396 },
  '중랑구': { lat: 37.6063, lng: 127.0926 },
  '성북구': { lat: 37.5894, lng: 127.0167 },
  '강북구': { lat: 37.6398, lng: 127.0256 },
  '도봉구': { lat: 37.6688, lng: 127.0471 },
  '노원구': { lat: 37.6542, lng: 127.0568 },
  '은평구': { lat: 37.6027, lng: 126.9291 },
  '서대문구': { lat: 37.5791, lng: 126.9368 },
  '마포구': { lat: 37.5663, lng: 126.9019 },
  '양천구': { lat: 37.5170, lng: 126.8664 },
  '강서구': { lat: 37.5509, lng: 126.8495 },
  '구로구': { lat: 37.4954, lng: 126.8874 },
  '금천구': { lat: 37.4519, lng: 126.9020 },
  '영등포구': { lat: 37.5264, lng: 126.8962 },
  '동작구': { lat: 37.5124, lng: 126.9393 },
  '관악구': { lat: 37.4784, lng: 126.9516 },
  '서초구': { lat: 37.4837, lng: 127.0324 },
  '강남구': { lat: 37.5172, lng: 127.0473 },
  '송파구': { lat: 37.5145, lng: 127.1058 },
  '강동구': { lat: 37.5301, lng: 127.1238 },
};

// 숫자 문자열에서 쉼표 제거하고 숫자로 변환
function parseNumber(value: string): number {
  if (!value) return 0;
  return parseInt(value.replace(/,/g, ''), 10) || 0;
}

// CSV 데이터를 파싱하여 자치구별로 집계
export async function loadCrimeData(): Promise<CrimeRecord[]> {
  const response = await fetch('/data/crime.csv');
  const csvText = await response.text();
  
  return new Promise((resolve, reject) => {
    Papa.parse<CrimeRecord>(csvText, {
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

// 자치구별 범죄 데이터 집계
export function aggregateByDistrict(records: CrimeRecord[]): DistrictCrimeData[] {
  const districtMap = new Map<string, number>();
  
  records.forEach(record => {
    if (!record.자치구) return;
    
    const district = record.자치구;
    const crimes = 
      parseNumber(record['살인 발생']) +
      parseNumber(record['강도 발생']) +
      parseNumber(record['강간 발생']) +
      parseNumber(record['절도 발생']) +
      parseNumber(record['폭력 발생']);
    
    districtMap.set(district, (districtMap.get(district) || 0) + crimes);
  });
  
  return Array.from(districtMap.entries())
    .map(([district, totalCrimes]) => ({
      district,
      totalCrimes,
      coordinates: seoulDistricts[district] || { lat: 0, lng: 0 }
    }))
    .filter(item => item.coordinates.lat !== 0 && item.coordinates.lng !== 0)
    .sort((a, b) => b.totalCrimes - a.totalCrimes);
}

// 평균 범죄 발생 건수 계산
export function calculateAverage(districtData: DistrictCrimeData[]): number {
  if (districtData.length === 0) return 0;
  const sum = districtData.reduce((acc, item) => acc + item.totalCrimes, 0);
  return sum / districtData.length;
}

// 색상 계산 (보라색 그라데이션)
export function calculateColor(crimeCount: number, min: number, max: number): string {
  if (max === min) return '#E8E0FF';
  
  const normalized = (crimeCount - min) / (max - min);
  
  // 보라색 그라데이션: #E8E0FF (연한) -> #9C7FD8 (중간) -> #4A148C (진한)
  const colors = [
    { r: 232, g: 224, b: 255 }, // #E8E0FF
    { r: 156, g: 127, b: 216 }, // #9C7FD8
    { r: 74, g: 20, b: 140 }    // #4A148C
  ];
  
  let color1, color2, factor;
  
  if (normalized < 0.5) {
    color1 = colors[0];
    color2 = colors[1];
    factor = normalized * 2;
  } else {
    color1 = colors[1];
    color2 = colors[2];
    factor = (normalized - 0.5) * 2;
  }
  
  const r = Math.round(color1.r + (color2.r - color1.r) * factor);
  const g = Math.round(color1.g + (color2.g - color1.g) * factor);
  const b = Math.round(color1.b + (color2.b - color1.b) * factor);
  
  return `rgb(${r}, ${g}, ${b})`;
}

