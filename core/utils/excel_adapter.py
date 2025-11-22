"""
Excel 어댑터 모듈 - Pandas DataFrame을 OpenPyXL Workbook처럼 감싸는 어댑터 클래스
Calamine 엔진을 사용한 고속 로딩을 위해 pandas로 읽은 데이터를 기존 openpyxl 로직과 호환되도록 변환
"""

import pandas as pd
from typing import Optional, Iterator, Tuple


class MockCell:
    """OpenPyXL Cell 객체를 모방하는 클래스"""
    
    def __init__(self, value, row: int, col: int):
        self.value = value
        self.row = row
        self.column = col


class MockSheet:
    """OpenPyXL Worksheet 객체를 모방하는 클래스"""
    
    def __init__(self, name: str, df: pd.DataFrame):
        self.title = name
        self.df = df
        self.max_row = len(df) if not df.empty else 0
        self.max_column = len(df.columns) if not df.empty else 0
    
    def cell(self, row: int, column: int) -> MockCell:
        """
        OpenPyXL의 cell() 메서드를 모방
        - openpyxl은 1-based index, pandas는 0-based index
        """
        try:
            # 1-based → 0-based 변환
            val = self.df.iloc[row - 1, column - 1]
            # NaN 값을 None으로 변환
            if pd.isna(val):
                val = None
            return MockCell(val, row, column)
        except (IndexError, KeyError):
            return MockCell(None, row, column)
    
    def iter_rows(self, min_row: int = 1, max_row: Optional[int] = None, 
                  min_col: int = 1, max_col: Optional[int] = None,
                  values_only: bool = False) -> Iterator:
        """
        OpenPyXL의 iter_rows() 메서드를 모방
        - pandas DataFrame을 행 단위로 반복
        """
        if self.df.empty:
            return iter([])
        
        # 기본값 설정
        if max_row is None:
            max_row = self.max_row
        if max_col is None:
            max_col = self.max_column
        
        # 범위 조정 (1-based → 0-based)
        start_row = max(1, min_row) - 1
        end_row = min(self.max_row, max_row)
        start_col = max(1, min_col) - 1
        end_col = min(self.max_column, max_col)
        
        # 범위 검증
        if start_row >= end_row or start_col >= end_col:
            return iter([])
        
        # DataFrame 슬라이싱 (0-based)
        sliced_df = self.df.iloc[start_row:end_row, start_col:end_col]
        
        # 행 단위로 반복
        for idx, row_data in sliced_df.iterrows():
            row_num = idx + 1 + start_row  # 실제 행 번호 (1-based)
            if values_only:
                yield tuple(row_data.values)
            else:
                # MockCell 객체 리스트 반환
                cells = []
                for col_idx, val in enumerate(row_data):
                    col_num = start_col + col_idx + 1  # 실제 열 번호 (1-based)
                    if pd.isna(val):
                        val = None
                    cells.append(MockCell(val, row_num, col_num))
                yield cells


class MockWorkbook:
    """OpenPyXL Workbook 객체를 모방하는 클래스"""
    
    def __init__(self, pandas_dict: dict):
        """
        Args:
            pandas_dict: {sheet_name: DataFrame} 형태의 딕셔너리
        """
        self.sheet_names = list(pandas_dict.keys())
        self.sheets = {name: MockSheet(name, df) for name, df in pandas_dict.items()}
    
    @property
    def sheetnames(self) -> list:
        """시트 이름 리스트 반환"""
        return self.sheet_names
    
    def __getitem__(self, key: str) -> MockSheet:
        """시트 이름으로 시트 접근"""
        return self.sheets[key]
    
    def close(self):
        """리소스 정리 (아무것도 하지 않음)"""
        pass


