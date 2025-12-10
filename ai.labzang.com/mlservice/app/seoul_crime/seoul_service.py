from poplib import POP3
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from app.seoul_crime.seoul_method import SeoulMethod
from app.seoul_crime.seoul_data import SeoulData
from app.seoul_crime.kakao_map_singleton import KakaoMapSingleton

try:
    from common.utils import setup_logging
    logger = setup_logging("seoul_service")
except ImportError:
    import logging
    logger = logging.getLogger("seoul_service")
class SeoulService:
    
    def __init__(self):
        self.data = SeoulData()
        self.method = SeoulMethod()
        self.crime_rate_columns = ['살인검거율', '강도검거율', '강간검거율', '절도검거율', '폭력검거율']
        self.crime_columns = ['살인', '강도', '강간', '절도', '폭력']

    def preprocess(self):
        data_dir = Path(self.data.dname)
        cctv_path = data_dir / "cctv.csv"
        crime_path = data_dir / "crime.csv"
        pop_path = data_dir / "pop.xls"
        
        # 데이터 로드
        cctv = self.method.csv_to_df(str(cctv_path))
        cctv = cctv.drop(['2013년도 이전', '2014년', '2015년', '2016년'], axis=1)
        crime = self.method.csv_to_df(str(crime_path))
        pop = self.method.xlsx_to_df(str(pop_path))
        # pop 컬럼 편집 
        # axis = 1 방향으로 자치구와 좌로부터 4번째 컬럼만 남기고 모두 삭제 
        # axis = 0 방향으로 위로부터 2, 3, 4 번째 행을 제거
        
        # 컬럼 편집: 자치구(인덱스 1)와 좌로부터 4번째 컬럼(인덱스 3)만 남기기
        columns_to_keep = [pop.columns[1], pop.columns[3]]  # 자치구와 좌로부터 4번째 컬럼
        pop = pop[columns_to_keep]
        
        # 행 편집: 위로부터 2, 3, 4 번째 행 제거 (인덱스 1, 2, 3)
        pop = pop.drop(pop.index[1:4])  # 인덱스 1, 2, 3 제거
        
        logger.info(f"  cctv 탑  : {cctv.head(1).to_string()}")
        logger.info(f"  crime 탑  : {crime.head(1).to_string()}")
        logger.info(f"  pop 탑  : {pop.head(1).to_string()}")
        
        # cctv와 pop 머지 전략
        # - cctv의 "기관명"과 pop의 "자치구"를 키로 사용
        # - 중복된 feature가 없도록 처리
        # - "기관명"과 "자치구"는 같은 값이지만 컬럼명이 다르므로 left_on, right_on 사용
        
        # 머지 전에 컬럼명 확인 및 중복 컬럼 체크
        logger.info(f"cctv 컬럼: {cctv.columns.tolist()}")
        logger.info(f"pop 컬럼: {pop.columns.tolist()}")
        
        # 중복되는 컬럼 확인 (키 컬럼 제외)
        cctv_cols = set(cctv.columns) - {'기관명'}
        pop_cols = set(pop.columns) - {'자치구'}
        duplicate_cols = cctv_cols & pop_cols
        
        if duplicate_cols:
            logger.warning(f"중복되는 컬럼이 발견되었습니다: {duplicate_cols}")
            logger.info("머지 시 suffixes를 사용하여 중복 컬럼을 구분합니다.")
        
        # cctv의 "기관명"과 pop의 "자치구"를 키로 머지
        cctv_pop = self.method.df_merge(
            left=cctv,
            right=pop,
            left_on='기관명',
            right_on='자치구',
            how='inner'
        )
        
        # 머지 후 "자치구" 컬럼 제거 (기관명과 동일한 값이므로)

        cctv_pop = cctv_pop.drop(columns=['기관명'])
        
        logger.info(f"머지 완료: cctv_pop shape = {cctv_pop.shape}")
        logger.info(f"cctv_pop 컬럼: {cctv_pop.columns.tolist()}")
        logger.info(f"cctv_pop 탑 :\n{cctv_pop.head(1).to_string()}")

        # 관서명에 따른 경찰서 주소 찾기
        logger.info("경찰서 관서명으로 주소 검색 시작...")
        
        station_names = [] # 경찰서 관서명 리스트
        for name in crime['관서명']:
            station_names.append('서울' + str(name[:-1]) + '경찰서')
        logger.info(f"경찰서 관서명 리스트: {station_names}")
        
        station_addrs = []
        station_lats = []
        station_lngs = []
        
        # 싱글턴 패턴 테스트
        kakao1 = KakaoMapSingleton()
        kakao2 = KakaoMapSingleton()
        if kakao1 is kakao2:
            logger.info("KakaoMapSingleton: 동일한 객체입니다 (싱글턴 패턴 정상 작동)")
        else:
            logger.warning("KakaoMapSingleton: 다른 객체입니다 (싱글턴 패턴 오류)")
        
        kakao = KakaoMapSingleton() # 카카오맵 객체 생성
        logger.info(f"총 {len(station_names)}개 경찰서 주소 검색 중...")
        
        for idx, name in enumerate(station_names, 1):
            try:
                tmp = kakao.geocode(name, language='ko')
                if tmp and len(tmp) > 0:
                    formatted_addr = tmp[0].get("formatted_address", "")
                    logger.info(f"[{idx}/{len(station_names)}] {name}의 검색 결과: {formatted_addr}")
                    station_addrs.append(formatted_addr)
                    tmp_loc = tmp[0].get("geometry", {})
                    location = tmp_loc.get('location', {})
                    station_lats.append(location.get('lat', 0.0))
                    station_lngs.append(location.get('lng', 0.0))
                else:
                    logger.warning(f"[{idx}/{len(station_names)}] {name}의 검색 결과가 없습니다.")
                    station_addrs.append("")
                    station_lats.append(0.0)
                    station_lngs.append(0.0)
            except Exception as e:
                logger.error(f"[{idx}/{len(station_names)}] {name} 검색 중 오류 발생: {str(e)}")
                station_addrs.append("")
                station_lats.append(0.0)
                station_lngs.append(0.0)
        
        logger.info(f"주소 검색 완료. 검색된 주소 리스트: {station_addrs}")
        
        # 주소에서 자치구 추출
        gu_names = []
        for idx, addr in enumerate(station_addrs):
            try:
                if addr:
                    tmp = addr.split()
                    tmp_gu_list = [gu for gu in tmp if gu[-1] == '구']
                    if tmp_gu_list:
                        gu_names.append(tmp_gu_list[0])
                    else:
                        logger.warning(f"주소에서 자치구를 찾을 수 없습니다: {addr}")
                        gu_names.append("")
                else:
                    logger.warning(f"빈 주소입니다. 자치구를 추출할 수 없습니다.")
                    gu_names.append("")
            except Exception as e:
                logger.error(f"자치구 추출 중 오류 발생 (주소: {addr}): {str(e)}")
                gu_names.append("")
        
        logger.info(f"추출된 자치구 리스트: {gu_names}")
        
        # crime 데이터프레임에 자치구 컬럼 추가
        if len(gu_names) == len(crime):
            crime['자치구'] = gu_names
            logger.info("crime 데이터프레임에 '자치구' 컬럼이 추가되었습니다.")
        else:
            logger.warning(f"자치구 리스트 길이({len(gu_names)})와 crime 데이터 길이({len(crime)})가 일치하지 않습니다.")
            # 길이가 다르더라도 가능한 만큼만 추가
            crime['자치구'] = gu_names[:len(crime)] if len(gu_names) > len(crime) else gu_names + [''] * (len(crime) - len(gu_names))

        logger.info("카카오맵 실행 완료")

        # crime 를 save 폴더에 csv 파일로 저장 (컬럼 순서 정렬)
        save_path = Path(self.data.sname)
        save_path.mkdir(parents=True, exist_ok=True)
        desired_cols = [
            '관서명', '살인 발생', '살인 검거',
            '강도 발생', '강도 검거',
            '강간 발생', '강간 검거',
            '절도 발생', '절도 검거',
            '폭력 발생', '폭력 검거',
            '자치구',
        ]
        ordered_cols = [c for c in desired_cols if c in crime.columns]
        rest_cols = [c for c in crime.columns if c not in ordered_cols]
        crime_sorted = crime[ordered_cols + rest_cols]
        out_file = save_path / "crime.csv"
        crime_sorted.to_csv(out_file, index=False)
        logger.info(f"crime 데이터프레임을 {out_file} 에 저장했습니다.")






        
        return {
            "status": "success",
            "cctv_rows": len(cctv),
            "cctv_columns": cctv.columns.tolist(),
            "crime_rows": len(crime),
            "crime_columns": crime.columns.tolist(),
            "pop_rows": len(pop),
            "pop_columns": pop.columns.tolist(),
            "cctv_pop_rows": len(cctv_pop),
            "cctv_pop_columns": cctv_pop.columns.tolist(),
            "cctv_preview": cctv.head(3).to_dict(orient='records'),
            "crime_preview": crime.head(3).to_dict(orient='records'),
            "pop_preview": pop.head(3).to_dict(orient='records'),
            "cctv_pop_preview": cctv_pop.head(3).to_dict(orient='records'),
            "message": "데이터 전처리 및 머지가 완료되었습니다"
        }
        