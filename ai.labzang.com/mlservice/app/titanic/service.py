"""
Titanic 서비스 모듈
"""
import os
import csv
from typing import List, Dict
from fastapi import HTTPException
import pandas as pd
import numpy as np
from sklearn import (
    model_selection,
    preprocessing,
    ensemble,
    linear_model,
    metrics
)
from app.titanic.method import TitanicMethod
from datasets import Dataset
from icecream import ic



def get_top_10_passengers():
    """상위 10명 승객 정보 조회 (임시 함수)"""
    return []


def get_passengers_by_survival_probability(limit: int = 10):
    """생존 가능성 분석 (임시 함수)"""
    return {
        'high_survival': [],
        'low_survival': []
    }


class TitanicService:
    """타이타닉 데이터 처리 및 머신러닝 서비스"""

    def __init__(self):
        pass

    def preprocess(self):
        ic("전처리 시작")
        the_method = TitanicMethod()
        df_train = the_method.new_model('train.csv')
        df_test = the_method.new_model('test.csv')
        this_train = the_method.create_train(df_train, 'Survived')
        this_test = the_method.create_train(df_test, 'Survived')
        print(f'1. Train 의 type \n {type(this_train)} ')
        print(f'2. Train 의 column \n {this_train.columns} ')
        print(f'3. Train 의 상위 5개 행\n {this_train.head(5)} ')
        print(f'4. Train 의 null 의 갯수\n {the_method.check_null(this_train)}개')
        drop_features = ['SibSp', 'Parch', 'Cabin', 'Ticket']
        this_train = the_method.drop_features(this_train, *drop_features)
        this_train = the_method.pclass_ordinal(this_train)
        this_train = the_method.fare_ordinal(this_train)
        this_train = the_method.embarked_nominal(this_train)
        this_train = the_method.cabin_nominal(this_train)
        this_train = the_method.ticket_nominal(this_train)
        this_train = the_method.gender_nominal(this_train)
        this_train = the_method.age_ratio(this_train)
        this_train = the_method.sibSp_ratio(this_train)
        this_train = the_method.parch_ratio(this_train)
        this_train = the_method.title_nominal(this_train)
        this_train = the_method.drop_features(this_train, 'Name')
        print(f'3. Train 의 상위 5개 행\n {this_train.head(5)} ')
        print(f'1. Train 의 type \n {type(this_train)} ')
        print(f'2. Train 의 column \n {this_train.columns} ')
        ic("전처리 완료")

    def modeling(self):
        ic("모델링 시작")
        ic("모델링 완료")

    def learning(self):
        ic("학습 시작")
        ic("학습 완료")

    def evaluate(self):
        ic("평가 시작")
        ic("평가 완료")

    def submit(self):
        ic("제출 시작")
        ic("제출 완료")