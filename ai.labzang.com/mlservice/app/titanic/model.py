"""
Titanic 데이터 모델 클래스
각 속성에 대한 getter와 setter를 포함합니다.
"""

class TitanicModel:
    """타이타닉 데이터 모델"""

    def __init__(self):
        self.schema = Schema()
        self.datasets = DataSets()