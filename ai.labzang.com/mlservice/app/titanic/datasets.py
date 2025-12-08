from typing import Optional
from dataclasses import dataclass
import pandas as pd

@dataclass

class DataSets:
    """데이터셋 관리를 위한 클래스"""
    
    def __init__(self):
        """초기화"""
        self._fname: str = ''  # file name
        self._dname: str = ''  # data path
        self._sname: str = ''  # save path
        self._train: Optional[pd.DataFrame] = None
        self._test: Optional[pd.DataFrame] = None
        self._id: str = ''
        self._label: str = ''
    
    @property
    def fname(self) -> str:
        """파일명 getter"""
        return self._fname
    
    @fname.setter
    def fname(self, fname: str):
        """파일명 setter"""
        self._fname = fname
    
    @property
    def dname(self) -> str:
        """데이터 경로 getter"""
        return self._dname
    
    @dname.setter
    def dname(self, dname: str):
        """데이터 경로 setter"""
        self._dname = dname
    
    @property
    def sname(self) -> str:
        """저장 경로 getter"""
        return self._sname
    
    @sname.setter
    def sname(self, sname: str):
        """저장 경로 setter"""
        self._sname = sname
    
    @property
    def train(self) -> Optional[pd.DataFrame]:
        """훈련 데이터 getter"""
        return self._train
    
    @train.setter
    def train(self, train: Optional[pd.DataFrame]):
        """훈련 데이터 setter"""
        self._train = train
    
    @property
    def test(self) -> Optional[pd.DataFrame]:
        """테스트 데이터 getter"""
        return self._test
    
    @test.setter
    def test(self, test: Optional[pd.DataFrame]):
        """테스트 데이터 setter"""
        self._test = test
    
    @property
    def id(self) -> str:
        """ID getter"""
        return self._id
    
    @id.setter
    def id(self, id: str):
        """ID setter"""
        self._id = id
    
    @property
    def label(self) -> str:
        """라벨 getter"""
        return self._label
    
    @label.setter
    def label(self, label: str):
        """라벨 setter"""
        self._label = label
