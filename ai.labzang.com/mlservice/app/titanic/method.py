from app.titanic.datasets import DataSets
import pandas as pd
import numpy as np
from icecream import ic
import os

class TitanicMethod(object):

    def __init__(self):
        # 데이터셋 객체 생성
        self.datasets = DataSets()


    def new_model(self, fname: str) -> pd.DataFrame:
        # train.csv 파일을 읽어와서 데이터프레임 작성

        return pd.read_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), fname))

    def create_train(self, df: pd.DataFrame, label: str) -> pd.DataFrame:
        # Survived 값을 제거한 데이터프레임 작성
        if label in df.columns:
            return df.drop(columns=[label])
        return df
  

    def create_label(self, df: pd.DataFrame, label: str) -> pd.DataFrame:
        # Survived 값만 가지는 답안지 데이터프레임 작성
        return df[[label]]

    def drop_features(self, df: pd.DataFrame, *features:str) -> pd.DataFrame:
        # 피쳐를 삭제하는 메소드
        return df.drop(columns=[x for x in features])

    def check_null(self, df: pd.DataFrame) -> int:
        # 널을 체크하는 메소드
        ic('데이터 결측지 확인')
        return int(df.isnull().sum().sum())

    #nominal , ordinal, interval, ratio

    def pclass_ordinal(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Pclass: 객실 등급 (1, 2, 3)
        - 서열형 척도(ordinal)로 처리합니다.
        - 1등석 > 2등석 > 3등석이므로, 생존률 관점에서 1이 가장 좋고 3이 가장 안 좋습니다.
        """
        # Pclass는 이미 서열형이므로 그대로 사용하되, 명시적으로 정수형으로 변환
        df = df.copy()
        df['Pclass'] = df['Pclass'].astype(int)
        return df

    def title_nominal(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Title: 명칭 (Mr, Mrs, Miss, Master, Dr, etc.)
        - Name 컬럼에서 추출한 타이틀입니다.
        - nominal 척도입니다.
        """
        df = df.copy()
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
        
        # Title을 숫자로 매핑 (0, 1, 2, 3, 4, 5, 6, 7, 8...)
        title_mapping = {
            'Mr': 0,
            'Miss': 1,
            'Mrs': 2,
            'Master': 3,
            'Rare': 4
        }
        
        # 매핑에 없는 타이틀은 5부터 순차적으로 할당
        unique_titles = df['Title'].unique()
        current_num = 5
        for title in unique_titles:
            if title not in title_mapping:
                title_mapping[title] = current_num
                current_num += 1
        
        df['Title'] = df['Title'].map(title_mapping)
        df['Title'] = df['Title'].astype(int)
        
        return df

    def gender_nominal(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Sex: 성별 (male, female)
        - nominal 척도입니다.
        """
        df = df.copy()
        # One-hot encoding
        sex_dummies = pd.get_dummies(df['Sex'], prefix='Sex')
        # True/False를 1/0으로 변환
        sex_dummies = sex_dummies.astype(int)
        df = pd.concat([df, sex_dummies], axis=1)

        #원본 sex 컬럼을 "gender"로 변경하고 male=0, female=1로 변환
        df.rename(columns={'Sex': 'gender'}, inplace=True)
        df['gender'] = df['gender'].map({'male': 0, 'female': 1})
        df['gender'] = df['gender'].astype(int)
        return df

    def age_ratio(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Age: 나이
        - 원래는 ratio 척도지만, 여기서는 나이를 구간으로 나눈 ordinal 피처를 만들고자 합니다.
        - bins: [-1, 0, 5, 12, 18, 24, 35, 60, np.inf]
          의미: 미상/유아(0), 유아(0-5), 어린이(5-12), 청소년(12-18), 청년(18-24), 
                성인(24-35), 중년(35-60), 노년(60+)
        """
        df = df.copy()
        bins = [-1, 0, 5, 12, 18, 24, 35, 60, np.inf]
        labels = ['Unknown', 'Baby', 'Child', 'Teenager', 'Young_Adult', 'Adult', 'Middle_Age', 'Senior']
        
        # 결측치를 중앙값으로 채우기
        if df['Age'].isnull().any():
            df['Age'].fillna(df['Age'].median(), inplace=True)
        
        # Age를 정수형으로 변환
        df['Age'] = df['Age'].astype(int)
        
        # 나이를 구간화하여 새로운 컬럼 생성 (숫자로 변환)
        df['Age_band'] = pd.cut(df['Age'], bins=bins, labels=False, include_lowest=True)
        df['Age_band'] = df['Age_band'].astype(int)
        
        # 범주형을 숫자로 변환 (ordinal)
        df['Age_ordinal'] = pd.cut(df['Age'], bins=bins, labels=False, include_lowest=True)
        df['Age_ordinal'] = df['Age_ordinal'].astype(int)
        
        return df

    def sibSp_ratio(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        SibSp: 형제/배우자 수
        - ratio 척도입니다.
        """
        df = df.copy()
        # 결측치 처리 (0으로 채우기 - 가족이 없다는 의미)
        if 'SibSp' in df.columns:
            df['SibSp'].fillna(0, inplace=True)
            df['SibSp'] = df['SibSp'].astype(int)
        return df

    def parch_ratio(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Parch: 부모/자녀 수
        - ratio 척도입니다.
        """
        df = df.copy()
        # 결측치 처리 (0으로 채우기 - 가족이 없다는 의미)
        if 'Parch' in df.columns:
            df['Parch'].fillna(0, inplace=True)
            df['Parch'] = df['Parch'].astype(int)
        return df

    def ticket_nominal(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ticket: 티켓 번호
        - nominal 척도입니다.
        - 티켓 번호의 접두사나 패턴을 추출하여 사용할 수 있습니다.
        """
        df = df.copy()
        if 'Ticket' in df.columns:
            # 티켓 번호의 접두사 추출 (예: "PC 17599" -> "PC")
            df['Ticket_prefix'] = df['Ticket'].str.extract(r'^([A-Za-z]+)', expand=False)
            df['Ticket_prefix'].fillna('Numeric', inplace=True)
            
            # Ticket_prefix를 숫자로 매핑
            unique_prefixes = df['Ticket_prefix'].unique()
            prefix_mapping = {prefix: idx for idx, prefix in enumerate(unique_prefixes)}
            df['Ticket_prefix'] = df['Ticket_prefix'].map(prefix_mapping)
            df['Ticket_prefix'] = df['Ticket_prefix'].astype(int)
        return df

    def fare_ordinal(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Fare: 요금
        - 연속형 ratio 척도이지만, 여기서는 구간화하여 서열형으로 사용하려고 합니다.
        """
        df = df.copy()
        # 결측치를 중앙값으로 채우기
        if df['Fare'].isnull().any():
            df['Fare'].fillna(df['Fare'].median(), inplace=True)
        
        # Fare를 사분위수로 구간화하여 ordinal 피처 생성 (숫자로 변환)
        df['Fare_band'] = pd.qcut(df['Fare'], q=4, labels=False, duplicates='drop')
        df['Fare_band'] = df['Fare_band'].astype(int)
        
        # 숫자형으로 변환
        df['Fare'] = pd.qcut(df['Fare'], q=4, labels=False, duplicates='drop')
        df['Fare'] = df['Fare'].astype(int)
        
        return df

    def cabin_nominal(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Cabin: 객실 번호
        - nominal 척도입니다.
        - Cabin의 첫 글자(갑판)를 추출하여 사용합니다.
        """
        df = df.copy()
        if 'Cabin' in df.columns:
            # Cabin의 첫 글자 추출 (갑판 정보)
            df['Cabin_deck'] = df['Cabin'].str[0]
            df['Cabin_deck'].fillna('Unknown', inplace=True)
            
            # One-hot encoding
            cabin_dummies = pd.get_dummies(df['Cabin_deck'], prefix='Cabin')
            # True/False를 1/0으로 변환
            cabin_dummies = cabin_dummies.astype(int)
            df = pd.concat([df, cabin_dummies], axis=1)
            # 원본 Cabin_deck 문자열 컬럼 삭제
            df.drop(columns=['Cabin_deck'], inplace=True)
        
        return df
        
    def embarked_nominal(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Embarked: 탑승 항구 (C, Q, S)
        - 본질적으로는 nominal(명목) 척도입니다.
        """
        df = df.copy()
        # 결측치를 가장 많이 등장하는 값(mode)으로 채우기
        if df['Embarked'].isnull().any():
            df['Embarked'].fillna(df['Embarked'].mode()[0], inplace=True)
        
        # One-hot encoding
        embarked_dummies = pd.get_dummies(df['Embarked'], prefix='Embarked')
        # True/False를 1/0으로 변환
        embarked_dummies = embarked_dummies.astype(int)
        df = pd.concat([df, embarked_dummies], axis=1)
        # 원본 Embarked 문자열 컬럼 삭제
        df.drop(columns=['Embarked'], inplace=True)
        
        return df