"""
데이터 처리 연동 모듈
file_parser.py의 데이터 처리 기능을 확장
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class DataProcessor:
    """데이터 처리 연동 클래스"""
    
    def __init__(self):
        """데이터 프로세서 초기화"""
        self.logger = logger
        
    def process_excel_data(self, sheet_data: pd.DataFrame, headers: List[str]) -> Dict[str, Any]:
        """
        Excel 데이터 처리 및 정제
        
        Args:
            sheet_data: 시트 데이터
            headers: 헤더 정보
            
        Returns:
            Dict: 처리된 데이터
        """
        try:
            processed_data = {
                'raw_data': sheet_data,
                'cleaned_data': self._clean_data(sheet_data),
                'validated_data': self._validate_data(sheet_data),
                'summary': self._generate_summary(sheet_data)
            }
            
            return processed_data
            
        except Exception as e:
            self.logger.error(f"데이터 처리 오류: {str(e)}")
            return {'error': str(e)}
    
    def _clean_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """데이터 정제"""
        try:
            # 빈 행 제거
            cleaned = data.dropna(how='all')
            
            # 중복 행 제거
            cleaned = cleaned.drop_duplicates()
            
            # 공백 정리
            for col in cleaned.columns:
                if cleaned[col].dtype == 'object':
                    cleaned[col] = cleaned[col].astype(str).str.strip()
            
            return cleaned
            
        except Exception as e:
            self.logger.error(f"데이터 정제 오류: {str(e)}")
            return data
    
    def _validate_data(self, data: pd.DataFrame) -> Dict[str, Any]:
        """데이터 검증"""
        try:
            validation_result = {
                'total_rows': len(data),
                'valid_rows': 0,
                'invalid_rows': 0,
                'validation_errors': []
            }
            
            # 각 행 검증
            for idx, row in data.iterrows():
                if self._is_valid_row(row):
                    validation_result['valid_rows'] += 1
                else:
                    validation_result['invalid_rows'] += 1
                    validation_result['validation_errors'].append({
                        'row': idx,
                        'errors': self._get_row_errors(row)
                    })
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"데이터 검증 오류: {str(e)}")
            return {'error': str(e)}
    
    def _is_valid_row(self, row: pd.Series) -> bool:
        """행 유효성 검사"""
        try:
            # 필수 필드 확인
            required_fields = ['사업자등록번호', '상호명', '대표자명']
            
            for field in required_fields:
                if field in row.index and pd.isna(row[field]):
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _get_row_errors(self, row: pd.Series) -> List[str]:
        """행 오류 정보 수집"""
        errors = []
        
        try:
            # 사업자등록번호 검증
            if '사업자등록번호' in row.index:
                business_number = str(row['사업자등록번호'])
                if not self._is_valid_business_number(business_number):
                    errors.append('유효하지 않은 사업자등록번호')
            
            # 대표자명 검증
            if '대표자명' in row.index:
                representative = str(row['대표자명'])
                if not self._is_valid_representative(representative):
                    errors.append('유효하지 않은 대표자명')
            
        except Exception as e:
            errors.append(f'검증 오류: {str(e)}')
        
        return errors
    
    def _is_valid_business_number(self, business_number: str) -> bool:
        """사업자등록번호 유효성 검사"""
        import re
        pattern = r'^\d{3}-?\d{2}-?\d{5}$|^\d{10}$'
        return bool(re.match(pattern, business_number))
    
    def _is_valid_representative(self, representative: str) -> bool:
        """대표자명 유효성 검사"""
        import re
        pattern = r'^[가-힣]{2,4}$'
        return bool(re.match(pattern, representative)) and not representative.isdigit()
    
    def _generate_summary(self, data: pd.DataFrame) -> Dict[str, Any]:
        """데이터 요약 정보 생성"""
        try:
            summary = {
                'total_rows': len(data),
                'total_columns': len(data.columns),
                'column_names': list(data.columns),
                'data_types': data.dtypes.to_dict(),
                'null_counts': data.isnull().sum().to_dict(),
                'unique_counts': data.nunique().to_dict()
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"요약 생성 오류: {str(e)}")
            return {'error': str(e)}


