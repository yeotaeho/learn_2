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
    metrics,
    naive_bayes,
    svm
)
from app.titanic.method import TitanicMethod
from datasets import Dataset
from icecream import ic
from app.titanic.datasets import DataSets



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
        self.this = None
        self.train_label = None
        self.models = {}
        self.model_scores = {}

    def preprocess(self):
        ic("전처리 시작")
        the_method = TitanicMethod()

        # train.csv와 test.csv를 동시에 읽기
        df_train = the_method.read_csv('train.csv')
        df_test = the_method.read_csv('test.csv')

        
        # Survived 컬럼 제거
        this_train = the_method.create_train(df_train , 'Survived')
        this_test = the_method.create_train(df_test, 'Survived')
        # 라벨 추출 (create_label 메서드 사용)
        train_label_df = the_method.create_label(df_train, 'Survived')
        train_label = train_label_df['Survived'] if 'Survived' in train_label_df.columns else None
        print(f'1. Train 의 type \n {type(this_train)} ')
        print(f'2. Train 의 column \n {this_train.columns} ')
        print(f'3. Train 의 상위 5개 행\n {this_train.head(5)} ')
        train_null, test_null = the_method.check_null(this_train, this_test)
        print(f'4. Train 의 null 의 갯수\n {train_null}개')
        ic("Train 전처리 완료")

        ic("Test 전처리 시작")
        print(f'5. Test 의 type \n {type(this_test)} ')
        print(f'6. Test 의 column \n {this_test.columns} ')
        print(f'7. Test 의 상위 5개 행\n {this_test.head(5)} ')
        print(f'8. Test 의 null 의 갯수\n {test_null}개')

        # DataSets 객체 생성 및 train, test 설정
        this = DataSets(train=this_train, test=this_test)

        # 삭제할 피처 목록 (Sex, Sex_female은 gender_nominal 실행 후 삭제)
        drop_features = ['SibSp', 'Parch', 'Cabin', 'Ticket', 'Sex', 'Sex_female']
        
        # 전처리 메서드 실행 (원본 컬럼이 필요한 메서드들을 먼저 실행)
        this = the_method.pclass_ordinal(this)
        this = the_method.fare_ordinal(this)
        this = the_method.embarked_nominal(this)
        this = the_method.cabin_nominal(this)
        this = the_method.ticket_nominal(this)
        this = the_method.gender_nominal(this)
        
        # 초기 피처 삭제 (Sex, Sex_female 제외)
        this = the_method.drop_features(this,*[f for f in drop_features if f not in ['Sex', 'Sex_female']])
        # gender_nominal 실행 후 Sex, Sex_female 삭제
        this = the_method.drop_features(this, *[f for f in drop_features if f in ['Sex', 'Sex_female']])
        this = the_method.age_ratio(this)
        this = the_method.sibSp_ratio(this)
        this = the_method.parch_ratio(this)
        this = the_method.title_nominal(this)
        this = the_method.drop_features(this, 'Name')
        
        # 최종 컬럼만 선택: PassengerId, Pclass, Embarked, Fare, gender, Title, Age_band
        this = the_method.select_final_features(this)
        
        print(f'3. Train 의 상위 5개 행\n {this.train.head(5)} ')
        print(f'1. Train 의 type \n {type(this.train)} ')
        print(f'2. Train 의 column \n {this.train.columns} ')

        print(f'5. Test 의 type \n {type(this.test)} ')
        print(f'6. Test 의 column \n {this.test.columns} ')
        print(f'7. Test 의 상위 5개 행\n {this.test.head(5)} ')
        train_null_final, test_null_final = the_method.check_null(this.train, this.test)
        print(f'8. Test 의 null 의 갯수\n {test_null_final}개')
        ic("Test 전처리 완료")
        
        # 전처리된 데이터와 라벨 저장
        self.this = this
        self.train_label = train_label

    def modeling(self):
        ic("모델링 시작")
        if self.this is None or self.this.train is None:
            raise ValueError("전처리가 먼저 실행되어야 합니다. preprocess()를 먼저 호출하세요.")
        
        # 로지스틱 회귀
        self.models['logistic_regression'] = linear_model.LogisticRegression(random_state=42, max_iter=1000)
        
        # NB (나이브 베이즈)
        self.models['naive_bayes'] = naive_bayes.GaussianNB()
        
        # 랜덤 포레스트
        self.models['random_forest'] = ensemble.RandomForestClassifier(n_estimators=100, random_state=42)
        
        # LightGBM
        try:
            import lightgbm as lgb
            self.models['lightgbm'] = lgb.LGBMClassifier(random_state=42, verbose=-1)
        except ImportError:
            ic("LightGBM이 설치되지 않았습니다. pip install lightgbm을 실행하세요.")
            self.models['lightgbm'] = None
        
        # SVM
        self.models['svm'] = svm.SVC(random_state=42, probability=True)
        
        ic("모델링 완료")

    def learning(self):
        ic("학습 시작")
        if self.this is None or self.this.train is None or self.train_label is None:
            raise ValueError("전처리가 먼저 실행되어야 합니다. preprocess()를 먼저 호출하세요.")
        
        if not self.models:
            raise ValueError("모델링이 먼저 실행되어야 합니다. modeling()을 먼저 호출하세요.")
        
        X_train = self.this.train.drop(columns=['PassengerId'], errors='ignore')
        
        # 로지스틱 회귀
        self.models['logistic_regression'].fit(X_train, self.train_label)
        
        # NB (나이브 베이즈)
        self.models['naive_bayes'].fit(X_train, self.train_label)
        
        # 랜덤 포레스트
        self.models['random_forest'].fit(X_train, self.train_label)
        
        # LightGBM
        if self.models['lightgbm'] is not None:
            self.models['lightgbm'].fit(X_train, self.train_label)
        
        # SVM
        self.models['svm'].fit(X_train, self.train_label)
        
        ic("학습 완료")

    def evaluate(self):
        ic("평가 시작")
        if self.this is None or self.this.train is None or self.train_label is None:
            raise ValueError("전처리가 먼저 실행되어야 합니다. preprocess()를 먼저 호출하세요.")
        
        if not self.models:
            raise ValueError("모델링과 학습이 먼저 실행되어야 합니다. modeling()과 learning()을 먼저 호출하세요.")
        
        X_train = self.this.train.drop(columns=['PassengerId'], errors='ignore')
        
        # 교차 검증을 사용하여 평가
        cv = model_selection.StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        
        # 로지스틱 회귀
        lr_scores = model_selection.cross_val_score(self.models['logistic_regression'], X_train, self.train_label, cv=cv, scoring='accuracy')
        lr_accuracy = lr_scores.mean()
        self.model_scores['logistic_regression'] = lr_accuracy
        print(f'로지스틱 회귀 활용한 검증 정확도 {lr_accuracy:.4f}')
        
        # 나이브베이즈
        nb_scores = model_selection.cross_val_score(self.models['naive_bayes'], X_train, self.train_label, cv=cv, scoring='accuracy')
        nb_accuracy = nb_scores.mean()
        self.model_scores['naive_bayes'] = nb_accuracy
        print(f'나이브베이즈 활용한 검증 정확도 {nb_accuracy:.4f}')
        
        # 랜덤포레스트
        rf_scores = model_selection.cross_val_score(self.models['random_forest'], X_train, self.train_label, cv=cv, scoring='accuracy')
        rf_accuracy = rf_scores.mean()
        self.model_scores['random_forest'] = rf_accuracy
        print(f'랜덤포레스트 활용한 검증 정확도 {rf_accuracy:.4f}')
        
        # LightGBM
        if self.models['lightgbm'] is not None:
            lgb_scores = model_selection.cross_val_score(self.models['lightgbm'], X_train, self.train_label, cv=cv, scoring='accuracy')
            lgb_accuracy = lgb_scores.mean()
            self.model_scores['lightgbm'] = lgb_accuracy
            print(f'LightGBM 활용한 검증 정확도 {lgb_accuracy:.4f}')
        else:
            self.model_scores['lightgbm'] = None
            print(f'LightGBM 활용한 검증 정확도 None (모델 미설치)')
        
        # SVM
        svm_scores = model_selection.cross_val_score(self.models['svm'], X_train, self.train_label, cv=cv, scoring='accuracy')
        svm_accuracy = svm_scores.mean()
        self.model_scores['svm'] = svm_accuracy
        print(f'SVM 활용한 검증 정확도 {svm_accuracy:.4f}')
        
        ic("평가 완료")
        return self.model_scores

    def submit(self):
        ic("제출 시작")
        if self.this is None or self.this.test is None:
            raise ValueError("전처리가 먼저 실행되어야 합니다. preprocess()를 먼저 호출하세요.")
        
        if not self.models:
            raise ValueError("모델링과 학습이 먼저 실행되어야 합니다. modeling()과 learning()을 먼저 호출하세요.")
        
        # 테스트 데이터 준비
        X_test = self.this.test.drop(columns=['PassengerId'], errors='ignore')
        
        # download 디렉토리 생성
        current_dir = os.path.dirname(os.path.abspath(__file__))
        download_dir = os.path.join(current_dir, 'download')
        os.makedirs(download_dir, exist_ok=True)
        
        # 타임스탬프 생성
        timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
        
        # 모든 모델에 대해 제출 파일 생성
        results = []
        best_model_name = None
        best_score = 0
        
        for model_name, model in self.models.items():
            if model is None:
                continue
            
            ic(f"{model_name} 모델 예측 시작...")
            
            # 예측 수행
            predictions = model.predict(X_test)
            
            # 제출용 DataFrame 생성
            submission_df = pd.DataFrame({
                'PassengerId': self.this.test['PassengerId'],
                'Survived': predictions.astype(int)
            })
            
            # CSV 파일 저장
            filename = f'submission_{model_name}_{timestamp}.csv'
            filepath = os.path.join(download_dir, filename)
            submission_df.to_csv(filepath, index=False)
            
            # 모델 정확도 가져오기
            model_accuracy = self.model_scores.get(model_name, None)
            
            # 최고 성능 모델 추적
            if model_accuracy is not None and model_accuracy > best_score:
                best_score = model_accuracy
                best_model_name = model_name
            
            ic(f"{model_name} 제출 파일 저장 완료: {filepath}")
            accuracy_str = f"{model_accuracy:.4f}" if model_accuracy is not None else "N/A"
            ic(f"  - 정확도: {accuracy_str}")
            ic(f"  - 생존 예측: {predictions.sum()}명")
            ic(f"  - 사망 예측: {len(predictions) - predictions.sum()}명")
            
            results.append({
                'model_name': model_name,
                'accuracy': model_accuracy,
                'filepath': filepath,
                'filename': filename,
                'download_url': f"/titanic/download/{filename}",
                'predictions_count': len(predictions),
                'survived_count': int(predictions.sum()),
                'deceased_count': int(len(predictions) - predictions.sum())
            })
        
        ic(f"최고 성능 모델: {best_model_name} (정확도: {best_score:.4f})")
        ic("제출 완료")
        
        return {
            'best_model': best_model_name,
            'best_accuracy': best_score,
            'all_models': results
        }