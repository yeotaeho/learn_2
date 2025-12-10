from app.titanic.datasets import DataSets
import pandas as pd
import numpy as np
from icecream import ic
import os
from typing import Tuple

class TitanicMethod(object):

    def __init__(self):
        # 데이터셋 객체 생성
        self.datasets = DataSets()


    def read_csv(self, fname: str) -> pd.DataFrame:
        # CSV 파일을 읽어와서 데이터프레임 작성
        current_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(current_dir, fname)
        return pd.read_csv(csv_path)

    def create_train(self, df: pd.DataFrame, label: str) -> pd.DataFrame:
        # Survived 값을 제거한 데이터프레임 작성
        df = df.copy()
        if label in df.columns:
            df = df.drop(columns=[label])
        return df
  

    def create_label(self, df: pd.DataFrame, label: str) -> pd.DataFrame:
        # Survived 값만 가지는 답안지 데이터프레임 작성
        return df[[label]]

    def drop_features(self, this: DataSets, *features: str) -> DataSets:
        # 피쳐를 삭제하는 메소드
        dataframes = [i for i in [this.train, this.test] if i is not None]
        [i.drop(j, axis=1, inplace=True) for j in features for i in dataframes]

        # for i in [this.train, this.test]:
        #     if i is not None:
        #         for j in features:
        #             i.drop(j, axis=1, inplace=True)
 
        return this

    def select_final_features(self, this: DataSets) -> DataSets:
        # 최종 컬럼만 선택하는 메소드: PassengerId, Pclass, Embarked, Fare, gender, Title, Age_band
        if this.train is not None:
            # 불필요한 컬럼 삭제
            cols_to_drop = []
            if 'Fare_band' in this.train.columns:
                cols_to_drop.append('Fare_band')
            # Cabin 관련 컬럼 삭제
            cabin_cols = [col for col in this.train.columns if col.startswith('Cabin_')]
            cols_to_drop.extend(cabin_cols)
            # Ticket_prefix 삭제
            if 'Ticket_prefix' in this.train.columns:
                cols_to_drop.append('Ticket_prefix')
            # Embarked_* 컬럼 삭제 (Embarked 하나만 사용)
            embarked_cols = [col for col in this.train.columns if col.startswith('Embarked_')]
            cols_to_drop.extend(embarked_cols)
            if cols_to_drop:
                this.train.drop(columns=cols_to_drop, inplace=True)
            
            # 최종 컬럼 리스트
            final_cols = ['PassengerId', 'Pclass', 'Embarked', 'Fare', 'gender', 'Title', 'Age_band']
            # 존재하는 컬럼만 선택
            available_cols = [col for col in final_cols if col in this.train.columns]
            this.train = this.train[available_cols]
        
        if this.test is not None:
            # 불필요한 컬럼 삭제
            cols_to_drop = []
            if 'Fare_band' in this.test.columns:
                cols_to_drop.append('Fare_band')
            # Cabin 관련 컬럼 삭제
            cabin_cols = [col for col in this.test.columns if col.startswith('Cabin_')]
            cols_to_drop.extend(cabin_cols)
            # Ticket_prefix 삭제
            if 'Ticket_prefix' in this.test.columns:
                cols_to_drop.append('Ticket_prefix')
            # Embarked_* 컬럼 삭제 (Embarked 하나만 사용)
            embarked_cols = [col for col in this.test.columns if col.startswith('Embarked_')]
            cols_to_drop.extend(embarked_cols)
            if cols_to_drop:
                this.test.drop(columns=cols_to_drop, inplace=True)
            
            # train과 동일한 컬럼 구조 유지
            if this.train is not None:
                final_cols = list(this.train.columns)
            else:
                final_cols = ['PassengerId', 'Pclass', 'Embarked', 'Fare', 'gender', 'Title', 'Age_band']
            # 존재하는 컬럼만 선택
            available_cols = [col for col in final_cols if col in this.test.columns]
            this.test = this.test[available_cols]
        
        return this

    def check_null(self, df: pd.DataFrame, test_df: pd.DataFrame) -> Tuple[int, int]:
        # 널을 체크하는 메소드
        ic('데이터 결측지 확인')
        return int(df.isnull().sum().sum()), int(test_df.isnull().sum().sum())

    #nominal , ordinal, interval, ratio

    def pclass_ordinal(self, this: DataSets) -> DataSets:
        """
        Pclass: 객실 등급 (1, 2, 3)
        - 서열형 척도(ordinal)로 처리합니다.
        - 1등석 > 2등석 > 3등석이므로, 생존률 관점에서 1이 가장 좋고 3이 가장 안 좋습니다.
        """
        # Pclass는 이미 서열형이므로 그대로 사용하되, 명시적으로 정수형으로 변환
        if this.train is not None:
            this.train['Pclass'] = this.train['Pclass'].astype(int)
        if this.test is not None:
            this.test['Pclass'] = this.test['Pclass'].astype(int)
        return this

    def title_nominal(self, this: DataSets) -> DataSets:
        """
        Title: 명칭 (Mr, Mrs, Miss, Master, Dr, etc.)
        - Name 컬럼에서 추출한 타이틀입니다.
        - nominal 척도입니다.
        """
        df = this.train
        test_df = this.test
        
        if df is not None:
            # Name에서 타이틀 추출 (예: "Braund, Mr. Owen Harris" -> "Mr")
            df['Title'] = df['Name'].str.extract(r',\s*([^\.]+)\.', expand=False)
            
            # 희소한 타이틀을 "Rare"로 묶기
            rare_titles = ['Lady', 'Countess', 'Capt', 'Col', 'Don', 'Dr', 'Major', 'Rev', 'Sir', 'Jonkheer', 'Dona']
            df['Title'] = df['Title'].replace(rare_titles, 'Rare')
            
            # 일반적인 타이틀 정리
            df['Title'] = df['Title'].replace(['Mlle', 'Ms'], 'Miss')
            df['Title'] = df['Title'].replace('Mme', 'Mrs')
            
            # 결측치 처리 (가장 빈도가 높은 값으로)
            if df['Title'].isnull().any():
                df['Title'].fillna(df['Title'].mode()[0], inplace=True)
        
        if test_df is not None:
            test_df['Title'] = test_df['Name'].str.extract(r',\s*([^\.]+)\.', expand=False)
            rare_titles = ['Lady', 'Countess', 'Capt', 'Col', 'Don', 'Dr', 'Major', 'Rev', 'Sir', 'Jonkheer', 'Dona']
            test_df['Title'] = test_df['Title'].replace(rare_titles, 'Rare')
            test_df['Title'] = test_df['Title'].replace(['Mlle', 'Ms'], 'Miss')
            test_df['Title'] = test_df['Title'].replace('Mme', 'Mrs')
            if test_df['Title'].isnull().any() and df is not None:
                test_df['Title'].fillna(df['Title'].mode()[0], inplace=True)
        
        # Title을 숫자로 매핑 (train과 test의 모든 타이틀을 고려)
        if df is not None and test_df is not None:
            all_titles = set(df['Title'].unique()) | set(test_df['Title'].unique())
        elif df is not None:
            all_titles = set(df['Title'].unique())
        elif test_df is not None:
            all_titles = set(test_df['Title'].unique())
        else:
            return this
            
        title_mapping = {
            'Mr': 0,
            'Miss': 1,
            'Mrs': 2,
            'Master': 3,
            'Rare': 4
        }
        
        # 매핑에 없는 타이틀은 5부터 순차적으로 할당
        current_num = 5
        for title in all_titles:
            if title not in title_mapping:
                title_mapping[title] = current_num
                current_num += 1
        
        if df is not None:
            df['Title'] = df['Title'].map(title_mapping)
            df['Title'] = df['Title'].astype(int)
        if test_df is not None:
            test_df['Title'] = test_df['Title'].map(title_mapping)
            test_df['Title'] = test_df['Title'].astype(int)
        
        return this

    def gender_nominal(self, this: DataSets) -> DataSets:
        """
        Sex: 성별 (male, female)
        - nominal 척도입니다.
        """
        df = this.train
        test_df = this.test
        
        if df is not None:
            # One-hot encoding
            sex_dummies = pd.get_dummies(df['Sex'], prefix='Sex')
            sex_dummies = sex_dummies.astype(int)
            df = pd.concat([df, sex_dummies], axis=1)
            this.train = df
            
            # Sex_male 컬럼을 gender로 변경
            if 'Sex_male' in df.columns:
                df.rename(columns={'Sex_male': 'gender'}, inplace=True)
        
        if test_df is not None:
            # test_df도 동일한 컬럼 구조를 가지도록 처리
            test_sex_dummies = pd.get_dummies(test_df['Sex'], prefix='Sex')
            if df is not None and 'Sex_male' in df.columns:
                # train에 있는 모든 컬럼이 test에도 있도록 보장
                for col in sex_dummies.columns:
                    if col not in test_sex_dummies.columns:
                        test_sex_dummies[col] = 0
                test_sex_dummies = test_sex_dummies[sex_dummies.columns]  # 순서 맞추기
            test_sex_dummies = test_sex_dummies.astype(int)
            test_df = pd.concat([test_df, test_sex_dummies], axis=1)
            this.test = test_df
            
            if 'Sex_male' in test_df.columns:
                test_df.rename(columns={'Sex_male': 'gender'}, inplace=True)
        
        return this

    def age_ratio(self, this: DataSets) -> DataSets:
        """
        Age: 나이
        - 원래는 ratio 척도지만, 여기서는 나이를 구간으로 나눈 ordinal 피처를 만들고자 합니다.
        - bins: [-1, 0, 5, 12, 18, 24, 35, 60, np.inf]
          의미: 미상/유아(0), 유아(0-5), 어린이(5-12), 청소년(12-18), 청년(18-24), 
                성인(24-35), 중년(35-60), 노년(60+)
        """
        df = this.train
        test_df = this.test
        bins = [-1, 0, 5, 12, 18, 24, 35, 60, np.inf]
        
        if df is not None:
            # 결측치를 train의 중앙값으로 채우기
            age_median = df['Age'].median()
            if df['Age'].isnull().any():
                df['Age'].fillna(age_median, inplace=True)
            df['Age'] = df['Age'].astype(int)
            df['Age_band'] = pd.cut(df['Age'], bins=bins, labels=False, include_lowest=True)
            df['Age_band'] = df['Age_band'].astype(int)
            df.drop(columns=['Age', 'Age_ordinal'], inplace=True, errors='ignore')
            this.train = df
        
        if test_df is not None:
            if df is not None:
                age_median = df['Age'].median() if 'Age' in df.columns else test_df['Age'].median()
            else:
                age_median = test_df['Age'].median()
            if test_df['Age'].isnull().any():
                test_df['Age'].fillna(age_median, inplace=True)
            test_df['Age'] = test_df['Age'].astype(int)
            test_df['Age_band'] = pd.cut(test_df['Age'], bins=bins, labels=False, include_lowest=True)
            test_df['Age_band'] = test_df['Age_band'].astype(int)
            test_df.drop(columns=['Age', 'Age_ordinal'], inplace=True, errors='ignore')
            this.test = test_df
        
        return this

    def sibSp_ratio(self, this: DataSets) -> DataSets:
        """
        SibSp: 형제/배우자 수
        - ratio 척도입니다.
        """
        df = this.train
        test_df = this.test
        # 결측치 처리 (0으로 채우기 - 가족이 없다는 의미)
        if df is not None and 'SibSp' in df.columns:
            df['SibSp'].fillna(0, inplace=True)
            df['SibSp'] = df['SibSp'].astype(int)
            this.train = df
        if test_df is not None and 'SibSp' in test_df.columns:
            test_df['SibSp'].fillna(0, inplace=True)
            test_df['SibSp'] = test_df['SibSp'].astype(int)
            this.test = test_df
        return this

    def parch_ratio(self, this: DataSets) -> DataSets:
        """
        Parch: 부모/자녀 수
        - ratio 척도입니다.
        """
        df = this.train
        test_df = this.test
        # 결측치 처리 (0으로 채우기 - 가족이 없다는 의미)
        if df is not None and 'Parch' in df.columns:
            df['Parch'].fillna(0, inplace=True)
            df['Parch'] = df['Parch'].astype(int)
            this.train = df
        if test_df is not None and 'Parch' in test_df.columns:
            test_df['Parch'].fillna(0, inplace=True)
            test_df['Parch'] = test_df['Parch'].astype(int)
            this.test = test_df
        return this

    def ticket_nominal(self, this: DataSets) -> DataSets:
        """
        Ticket: 티켓 번호
        - nominal 척도입니다.
        - 티켓 번호의 접두사나 패턴을 추출하여 사용할 수 있습니다.
        """
        df = this.train
        test_df = this.test
        
        if df is not None and 'Ticket' in df.columns:
            # 티켓 번호의 접두사 추출 (예: "PC 17599" -> "PC")
            df['Ticket_prefix'] = df['Ticket'].str.extract(r'^([A-Za-z]+)', expand=False)
            df['Ticket_prefix'].fillna('Numeric', inplace=True)
            this.train = df
        
        if test_df is not None and 'Ticket' in test_df.columns:
            test_df['Ticket_prefix'] = test_df['Ticket'].str.extract(r'^([A-Za-z]+)', expand=False)
            test_df['Ticket_prefix'].fillna('Numeric', inplace=True)
            this.test = test_df
        
        # Ticket_prefix를 숫자로 매핑 (train과 test의 모든 prefix 고려)
        # Ticket_prefix 컬럼이 생성되었는지 확인
        has_train_prefix = df is not None and 'Ticket_prefix' in df.columns
        has_test_prefix = test_df is not None and 'Ticket_prefix' in test_df.columns
        
        if has_train_prefix and has_test_prefix:
            all_prefixes = set(df['Ticket_prefix'].unique()) | set(test_df['Ticket_prefix'].unique())
        elif has_train_prefix:
            all_prefixes = set(df['Ticket_prefix'].unique())
        elif has_test_prefix:
            all_prefixes = set(test_df['Ticket_prefix'].unique())
        else:
            return this
            
        prefix_mapping = {prefix: idx for idx, prefix in enumerate(sorted(all_prefixes))}
        
        if has_train_prefix:
            df['Ticket_prefix'] = df['Ticket_prefix'].map(prefix_mapping)
            df['Ticket_prefix'] = df['Ticket_prefix'].astype(int)
            this.train = df
        if has_test_prefix:
            test_df['Ticket_prefix'] = test_df['Ticket_prefix'].map(prefix_mapping)
            test_df['Ticket_prefix'] = test_df['Ticket_prefix'].astype(int)
            this.test = test_df
        
        return this

    def fare_ordinal(self, this: DataSets) -> DataSets:
        """
        Fare: 요금
        - 연속형 ratio 척도이지만, 여기서는 구간화하여 서열형으로 사용하려고 합니다.
        """
        df = this.train
        test_df = this.test
        
        if df is not None:
            # 결측치를 train의 중앙값으로 채우기
            fare_median = df['Fare'].median()
            if df['Fare'].isnull().any():
                df['Fare'].fillna(fare_median, inplace=True)
            
            # Fare를 사분위수로 구간화
            train_fare_quantiles = df['Fare'].quantile([0, 0.25, 0.5, 0.75, 1.0])
            df['Fare_band'] = pd.cut(df['Fare'], bins=train_fare_quantiles, labels=False, include_lowest=True, duplicates='drop')
            df['Fare_band'] = df['Fare_band'].astype(int)
            df['Fare'] = pd.cut(df['Fare'], bins=train_fare_quantiles, labels=False, include_lowest=True, duplicates='drop')
            df['Fare'] = df['Fare'].astype(int)
            this.train = df
        else:
            train_fare_quantiles = None
        
        if test_df is not None:
            if df is not None:
                fare_median = df['Fare'].median() if 'Fare' in df.columns else test_df['Fare'].median()
            else:
                fare_median = test_df['Fare'].median()
                train_fare_quantiles = test_df['Fare'].quantile([0, 0.25, 0.5, 0.75, 1.0])
            
            if test_df['Fare'].isnull().any():
                test_df['Fare'].fillna(fare_median, inplace=True)
            
            if train_fare_quantiles is not None:
                test_df['Fare_band'] = pd.cut(test_df['Fare'], bins=train_fare_quantiles, labels=False, include_lowest=True, duplicates='drop')
                test_df['Fare_band'] = test_df['Fare_band'].astype(int)
                test_df['Fare'] = pd.cut(test_df['Fare'], bins=train_fare_quantiles, labels=False, include_lowest=True, duplicates='drop')
                test_df['Fare'] = test_df['Fare'].astype(int)
            this.test = test_df
        
        return this

    def cabin_nominal(self, this: DataSets) -> DataSets:
        """
        Cabin: 객실 번호
        - nominal 척도입니다.
        - Cabin의 첫 글자(갑판)를 추출하여 사용합니다.
        """
        df = this.train
        test_df = this.test
        
        if df is not None and 'Cabin' in df.columns:
            # Cabin의 첫 글자 추출 (갑판 정보)
            df['Cabin_deck'] = df['Cabin'].str[0]
            df['Cabin_deck'].fillna('Unknown', inplace=True)
            
            # One-hot encoding
            cabin_dummies = pd.get_dummies(df['Cabin_deck'], prefix='Cabin')
            cabin_dummies = cabin_dummies.astype(int)
            df = pd.concat([df, cabin_dummies], axis=1)
            df.drop(columns=['Cabin_deck'], inplace=True)
            this.train = df
        
        if test_df is not None and 'Cabin' in test_df.columns:
            test_df['Cabin_deck'] = test_df['Cabin'].str[0]
            test_df['Cabin_deck'].fillna('Unknown', inplace=True)
            
            # test_df도 동일한 컬럼 구조를 가지도록 처리
            test_cabin_dummies = pd.get_dummies(test_df['Cabin_deck'], prefix='Cabin')
            if df is not None and 'Cabin_deck' in df.columns:
                # train에 있는 모든 컬럼이 test에도 있도록 보장
                for col in cabin_dummies.columns:
                    if col not in test_cabin_dummies.columns:
                        test_cabin_dummies[col] = 0
                test_cabin_dummies = test_cabin_dummies[cabin_dummies.columns]  # 순서 맞추기
            test_cabin_dummies = test_cabin_dummies.astype(int)
            test_df = pd.concat([test_df, test_cabin_dummies], axis=1)
            test_df.drop(columns=['Cabin_deck'], inplace=True)
            this.test = test_df
        
        return this
        
    def embarked_nominal(self, this: DataSets) -> DataSets:
        """
        Embarked: 탑승 항구 (C, Q, S)
        - 본질적으로는 nominal(명목) 척도입니다.
        - 숫자로 매핑: C=0, Q=1, S=2
        """
        df = this.train
        test_df = this.test
        
        # Embarked를 숫자로 매핑
        embarked_mapping = {'C': 0, 'Q': 1, 'S': 2}
        
        if df is not None:
            # 결측치를 train의 가장 많이 등장하는 값(mode)으로 채우기
            embarked_mode = df['Embarked'].mode()[0] if not df['Embarked'].mode().empty else 'S'
            if df['Embarked'].isnull().any():
                df['Embarked'].fillna(embarked_mode, inplace=True)
            
            # 숫자로 매핑
            df['Embarked'] = df['Embarked'].map(embarked_mapping)
            df['Embarked'] = df['Embarked'].astype(int)
            this.train = df
        else:
            embarked_mode = 'S'
        
        if test_df is not None:
            if test_df['Embarked'].isnull().any():
                test_df['Embarked'].fillna(embarked_mode, inplace=True)
            
            # 숫자로 매핑
            test_df['Embarked'] = test_df['Embarked'].map(embarked_mapping)
            test_df['Embarked'] = test_df['Embarked'].astype(int)
            this.test = test_df
        
        return this