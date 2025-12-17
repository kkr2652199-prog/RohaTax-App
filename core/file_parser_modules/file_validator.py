"""
파일 검증 모듈 - 연동 모듈 방식
file_parser.py의 파일 검증 기능을 분리하여 연동
"""

import pandas as pd
import openpyxl
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class FileValidator:
    """파일 검증 클래스 - 연동 모듈"""
    
    def __init__(self):
        """파일 검증기 초기화"""
        self.supported_formats = ['.xlsx', '.xls', '.csv']
        self.logger = logger
    
    def validate_file_format(self, file_path: str) -> bool:
        """파일 형식 검증"""
        try:
            file_ext = Path(file_path).suffix.lower()
            if file_ext not in self.supported_formats:
                self.logger.error(f"지원하지 않는 파일 형식: {file_ext}")
                return False
            return True
        except Exception as e:
            self.logger.error(f"파일 형식 검증 실패: {e}")
            return False
    
    def validate_file_exists(self, file_path: str) -> bool:
        """파일 존재 여부 검증"""
        try:
            if not Path(file_path).exists():
                self.logger.error(f"파일이 존재하지 않음: {file_path}")
                return False
            return True
        except Exception as e:
            self.logger.error(f"파일 존재 검증 실패: {e}")
            return False
    
    def validate_file_size(self, file_path: str, max_size_mb: int = 50) -> bool:
        """파일 크기 검증"""
        try:
            file_size = Path(file_path).stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            
            if file_size_mb > max_size_mb:
                self.logger.error(f"파일 크기가 너무 큼: {file_size_mb:.2f}MB (최대: {max_size_mb}MB)")
                return False
            return True
        except Exception as e:
            self.logger.error(f"파일 크기 검증 실패: {e}")
            return False
    
    def validate_excel_file(self, file_path: str) -> Tuple[bool, Optional[List[str]]]:
        """Excel 파일 검증"""
        try:
            workbook = openpyxl.load_workbook(file_path, read_only=True)
            sheet_names = workbook.sheetnames
            
            if not sheet_names:
                self.logger.error("Excel 파일에 시트가 없음")
                return False, None
            
            workbook.close()
            return True, sheet_names
        except Exception as e:
            self.logger.error(f"Excel 파일 검증 실패: {e}")
            return False, None
    
    def validate_csv_file(self, file_path: str) -> bool:
        """CSV 파일 검증"""
        try:
            # CSV 파일 읽기 시도
            df = pd.read_csv(file_path, encoding='utf-8', nrows=1)
            if df.empty:
                self.logger.error("CSV 파일이 비어있음")
                return False
            return True
        except UnicodeDecodeError:
            try:
                # UTF-8 실패 시 CP949 시도
                df = pd.read_csv(file_path, encoding='cp949', nrows=1)
                if df.empty:
                    self.logger.error("CSV 파일이 비어있음")
                    return False
                return True
            except Exception as e:
                self.logger.error(f"CSV 파일 검증 실패: {e}")
                return False
        except Exception as e:
            self.logger.error(f"CSV 파일 검증 실패: {e}")
            return False
    
    def validate_dataframe_structure(self, df: pd.DataFrame) -> bool:
        """DataFrame 구조 검증"""
        try:
            if df.empty:
                self.logger.error("DataFrame이 비어있음")
                return False
            
            if len(df.columns) < 3:
                self.logger.error(f"컬럼 수가 부족함: {len(df.columns)}개 (최소 3개 필요)")
                return False
            
            if len(df) < 1:
                self.logger.error("데이터 행이 없음")
                return False
            
            return True
        except Exception as e:
            self.logger.error(f"DataFrame 구조 검증 실패: {e}")
            return False
    
    def validate_required_columns(self, df: pd.DataFrame, required_columns: List[str]) -> Tuple[bool, List[str]]:
        """필수 컬럼 검증"""
        try:
            missing_columns = []
            for col in required_columns:
                if col not in df.columns:
                    missing_columns.append(col)
            
            if missing_columns:
                self.logger.warning(f"필수 컬럼 누락: {missing_columns}")
                return False, missing_columns
            
            return True, []
        except Exception as e:
            self.logger.error(f"필수 컬럼 검증 실패: {e}")
            return False, []
    
    def validate_data_types(self, df: pd.DataFrame) -> bool:
        """데이터 타입 검증"""
        try:
            # 숫자형 데이터가 있는지 확인
            numeric_columns = df.select_dtypes(include=['number']).columns
            if len(numeric_columns) == 0:
                self.logger.warning("숫자형 데이터가 없음")
            
            # 문자열 데이터가 있는지 확인
            string_columns = df.select_dtypes(include=['object']).columns
            if len(string_columns) == 0:
                self.logger.warning("문자열 데이터가 없음")
            
            return True
        except Exception as e:
            self.logger.error(f"데이터 타입 검증 실패: {e}")
            return False
    
    def validate_file_comprehensive(self, file_path: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """종합 파일 검증"""
        try:
            # 기본 검증
            if not self.validate_file_exists(file_path):
                return False, None
            
            if not self.validate_file_format(file_path):
                return False, None
            
            if not self.validate_file_size(file_path):
                return False, None
            
            # 파일 형식별 검증
            file_ext = Path(file_path).suffix.lower()
            validation_info = {
                'file_path': file_path,
                'file_format': file_ext,
                'file_size_mb': Path(file_path).stat().st_size / (1024 * 1024)
            }
            
            if file_ext in ['.xlsx', '.xls']:
                is_valid, sheet_names = self.validate_excel_file(file_path)
                if not is_valid:
                    return False, None
                validation_info['sheet_names'] = sheet_names
                
            elif file_ext == '.csv':
                if not self.validate_csv_file(file_path):
                    return False, None
            
            return True, validation_info
            
        except Exception as e:
            self.logger.error(f"종합 파일 검증 실패: {e}")
            return False, None






