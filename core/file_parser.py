"""
파일 파싱 부품 - 배달대행사 정산서 파일 파싱
핵심기술 절대지침에 따라 파일을 파싱하고 구조화된 데이터 반환
"""

import pandas as pd
import openpyxl
import zipfile
from typing import Dict, List, Any, Optional, Callable
import logging
from pathlib import Path
from .file_parser_utils.data_processor import DataProcessor
from .file_parser_utils.header_analyzer import HeaderAnalyzer
from .file_parser_utils.header_locator import HeaderLocator
from .file_parser_utils.industry_rules import IndustryRules
from .file_parser_utils.parallel_runner import ParallelRunner
from .file_parser_utils.reporting import ReportingUtils
from .file_parser_utils.validators import FileUploadValidator

logger = logging.getLogger(__name__)

class FileParser:
    """배달대행사 정산서 파일 파싱 부품"""
    
    def __init__(self):
        """파일 파서 초기화"""
        self.supported_formats = ['.xlsx', '.xls', '.csv']
        self.logger = logger
        
        # 연동 모듈 초기화
        self.data_processor = DataProcessor()
        self.header_analyzer = HeaderAnalyzer()
        self.header_locator = HeaderLocator(logger=self.logger)
        self.file_upload_validator = FileUploadValidator(self.supported_formats, max_size_mb=100, logger=self.logger)
        self.industry_rules = IndustryRules(logger=self.logger, number_parser=self._to_number)
        self.reporting_utils = ReportingUtils(logger=self.logger)
        self.parallel_runner = ParallelRunner(self, logger=self.logger)
        
        # 필수 5개 컬럼 키워드 (지능앱 기술 - 강화된 키워드)
        self.required_keywords = {
            'business_number': [
                '사업자등록번호', '사업자번호', '등록번호', '사업자등록', '사업자', '등록',
                '공급받는자사업자', '공급받는자 사업자', '공급받는자 등록번호', '공급받는자 사업자등록번호', '공급받는자 사업자번호', '공급받는자번호',
                '구매자 등록번호', '구매자 사업자등록번호', '구매자 사업자번호', '수취인 등록번호', '수취인 사업자등록번호', '수취인 사업자번호',
                '고객 사업자등록번호', '고객 사업자번호', '거래처 등록번호', '거래처 사업자등록번호', '거래처 사업자번호',
                '매입자 등록번호', '매입자 사업자등록번호', '매입자 사업자번호',
                '법인등록번호', '법인 사업자등록번호', '법인 사업자번호',
                '업체 사업자등록번호', '업체 사업자번호', '가맹점 사업자등록번호', '가맹점 사업자번호',
                '매장 사업자등록번호', '매장 사업자번호', '점포 사업자등록번호', '점포 사업자번호', '업소 사업자등록번호', '업소 사업자번호'
            ],
            'store_name': [
                '상호명', '상호', '업체명', '사업장명', '가맹점명', '매장명', '점포명', '업소명', '가게명',
                '공급받는자상호', '공급받는자 상호', '공급받는자 상호명', '공급받는자 업체명', '공급받는자 사업장명',
                '구매자 상호', '구매자 상호명', '구매자 업체명', '구매자 사업장명',
                '수취인 상호', '수취인 상호명', '수취인 업체명', '수취인 사업장명',
                '고객 상호', '고객 상호명', '고객 업체명', '고객 사업장명',
                '거래처 상호', '거래처 상호명', '거래처 업체명', '거래처 사업장명',
                '매입자 상호', '매입자 상호명', '매입자 업체명', '매입자 사업장명',
                '법인 상호', '법인 상호명', '법인 업체명', '법인 사업장명',
                '가맹점 상호', '가맹점 상호명', '가맹점 업체명', '가맹점 사업장명',
                '매장 상호', '매장 상호명', '매장 업체명', '매장 사업장명',
                '점포 상호', '점포 상호명', '점포 업체명', '점포 사업장명', '업소 상호', '업소 상호명', '업소 업체명', '업소 사업장명'
            ],
            'representative': [
                '대표자', '대표자명', '성명', '이름', '사업주', '대표명', '대표이사', '사장명', '대표담당자', '담당자', '등록자명',
                '공급받는자대표자', '공급받는자 대표자', '공급받는자 대표자명', '공급받는자 성명', '공급받는자 이름',
                '구매자 대표자', '구매자 대표자명', '구매자 성명', '구매자 이름',
                '수취인 대표자', '수취인 대표자명', '수취인 성명', '수취인 이름',
                '고객 대표자', '고객 대표자명', '고객 성명', '고객 이름',
                '거래처 대표자', '거래처 대표자명', '거래처 성명', '거래처 이름',
                '매입자 대표자', '매입자 대표자명', '매입자 성명', '매입자 이름',
                '법인 대표자', '법인 대표자명', '법인 성명', '법인 이름',
                '가맹점 대표자', '가맹점 대표자명', '가맹점 성명', '가맹점 이름',
                '매장 대표자', '매장 대표자명', '매장 성명', '매장 이름',
                '점포 대표자', '점포 대표자명', '점포 성명', '점포 이름', '업소 대표자', '업소 대표자명', '업소 성명', '업소 이름'
            ],
            'address': [
                '주소', '사업장주소', '업체주소', '소재지', '사업장소재지', '도로명주소', '지번주소', '사업장', '주소지', '위치',
                '공급받는자주소', '공급받는자 주소', '공급받는자 사업장주소', '공급받는자 업체주소', '공급받는자 소재지',
                '구매자 주소', '구매자 사업장주소', '구매자 업체주소', '구매자 소재지',
                '수취인 주소', '수취인 사업장주소', '수취인 업체주소', '수취인 소재지',
                '고객 주소', '고객 사업장주소', '고객 업체주소', '고객 소재지',
                '거래처 주소', '거래처 사업장주소', '거래처 업체주소', '거래처 소재지',
                '매입자 주소', '매입자 사업장주소', '매입자 업체주소', '매입자 소재지',
                '법인 주소', '법인 사업장주소', '법인 업체주소', '법인 소재지',
                '가맹점 주소', '가맹점 사업장주소', '가맹점 업체주소', '가맹점 소재지',
                '매장 주소', '매장 사업장주소', '매장 업체주소', '매장 소재지',
                '점포 주소', '점포 사업장주소', '점포 업체주소', '점포 소재지', '업소 주소', '업소 사업장주소', '업소 업체주소', '업소 소재지'
            ],
            'email': [
                '이메일', '메일', 'email', 'mail', 'e-mail', '전자우편', '전자메일',
                '공급받는자이메일', '공급받는자 이메일', '공급받는자 메일', '공급받는자 email', '공급받는자 mail',
                '구매자 이메일', '구매자 메일', '구매자 email', '구매자 mail',
                '수취인 이메일', '수취인 메일', '수취인 email', '수취인 mail',
                '고객 이메일', '고객 메일', '고객 email', '고객 mail',
                '거래처 이메일', '거래처 메일', '거래처 email', '거래처 mail',
                '매입자 이메일', '매입자 메일', '매입자 email', '매입자 mail',
                '법인 이메일', '법인 메일', '법인 email', '법인 mail',
                '가맹점 이메일', '가맹점 메일', '가맹점 email', '가맹점 mail',
                '매장 이메일', '매장 메일', '매장 email', '매장 mail',
                '점포 이메일', '점포 메일', '점포 email', '점포 mail', '업소 이메일', '업소 메일', '업소 email', '업소 mail'
            ]
        }
        
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        파일 파싱 및 데이터 구조화
        
        Args:
            file_path: 업로드된 파일 경로
            
        Returns:
            Dict: 구조화된 데이터
            {
                'file_type': str,
                'raw_data': DataFrame,
                'headers': List[str],
                'data_sections': Dict,
                'total_rows': int,
                'parsing_status': str
            }
        """
        try:
            file_path = Path(file_path)
            
            # 파일 업로드 기본 검증
            validation_result = self.file_upload_validator.validate(file_path)
            if not validation_result.is_valid:
                error_message = validation_result.message or "지원하지 않는 파일 형식입니다."
                return self._create_error_response(error_message)
            
            # 파일 파싱
            if file_path.suffix.lower() == '.csv':
                return self._parse_csv(file_path)
            elif file_path.suffix.lower() in ['.xlsx', '.xls']:
                return self._parse_excel(file_path)
            else:
                return self._create_error_response("파일 형식을 확인할 수 없습니다.")
                
        except FileNotFoundError as e:
            # Python 3.14의 향상된 에러 메시지 활용
            self.logger.error(f"파일을 찾을 수 없습니다: {file_path} - {e}")
            return self._create_error_response(f"파일을 찾을 수 없습니다. 파일 경로를 확인해주세요. (오류: {e})")
        except PermissionError as e:
            # Python 3.14의 향상된 에러 메시지 활용
            self.logger.error(f"파일 접근 권한 오류: {file_path} - {e}")
            return self._create_error_response(f"파일 접근 권한이 없습니다. 파일이 다른 프로그램에서 사용 중인지 확인해주세요. (오류: {e})")
        except openpyxl.utils.exceptions.InvalidFileException as e:
            # Python 3.14의 향상된 에러 메시지 활용
            self.logger.error(f"잘못된 Excel 파일 형식: {file_path} - {e}")
            return self._create_error_response(f"Excel 파일이 손상되었거나 지원하지 않는 형식입니다. (오류: {e})")
        except ValueError as e:
            # Python 3.14의 향상된 에러 메시지 활용
            self.logger.error(f"데이터 값 오류: {file_path} - {e}")
            return self._create_error_response(f"파일 내 데이터 형식이 올바르지 않습니다. (오류: {e})")
        except Exception as e:
            # Python 3.14의 향상된 에러 메시지와 Template Strings 활용
            self.logger.error(f"파일 파싱 중 예상치 못한 오류 발생: {file_path} - {e}", exc_info=True)
            return self._create_error_response(f"파일 처리 중 오류가 발생했습니다. 관리자에게 문의해주세요. (오류 코드: {hash(str(e)) % 10000}, 상세: {e})")
    
    def _detect_header_row(self, sheet) -> int:
        """레거시 호환을 위한 헤더 감지 래퍼."""
        return self.header_locator.detect_header_row(sheet)
    
    def _detect_csv_header_row(self, df: pd.DataFrame) -> int:
        """레거시 호환을 위한 CSV 헤더 감지 래퍼."""
        return self.header_locator.detect_csv_header_row(df, self.required_keywords)
    
    def _calculate_csv_data_density(self, df: pd.DataFrame, row_idx: int) -> float:
        """
        CSV 특정 행의 데이터 밀도 계산
        지능앱 기술: 데이터 밀도 기반 헤더 감지
        
        Args:
            df: pandas DataFrame
            row_idx: 행 인덱스
            
        Returns:
            float: 데이터 밀도 점수
        """
        if row_idx >= len(df):
            return 0.0
        
        row_data = df.iloc[row_idx]
        text_count = 0
        number_count = 0
        empty_count = 0
        
        for value in row_data:
            if pd.isna(value) or str(value).strip() == "":
                empty_count += 1
            elif isinstance(value, (int, float)):
                number_count += 1
            else:
                text_count += 1
        
        # 헤더는 보통 텍스트가 많고, 데이터는 숫자가 많음
        total_cells = len(row_data)
        if total_cells == 0:
            return 0.0
        
        text_ratio = text_count / total_cells
        number_ratio = number_count / total_cells
        empty_ratio = empty_count / total_cells
        
        # 헤더 점수 계산 (텍스트 비율이 높을수록 높은 점수)
        header_score = text_ratio * 2 + number_ratio * 0.5 + empty_ratio * 0.1
        
        return header_score
    
    def _count_csv_matched_fields(self, df: pd.DataFrame, row_idx: int, required_keywords: Dict) -> int:
        """HeaderLocator 기반 CSV 필드 매칭 래퍼."""
        if hasattr(self.header_locator, "_count_csv_matched_fields"):
            return self.header_locator._count_csv_matched_fields(df, row_idx, required_keywords)
        return 0
    
    def _inspect_all_sheets(self, workbook) -> Optional[Dict[str, Any]]:
        """HeaderLocator를 통한 시트 검열 래퍼."""
        return self.header_locator.inspect_all_sheets(
            workbook,
            self.required_keywords,
            family_extractor=self._find_families_in_sheet,
            number_parser=self._to_number,
        )
    
    def _find_priority_sheet(self, workbook, required_keywords: Dict) -> Optional[Dict[str, Any]]:
        """HeaderLocator가 우선순위 시트를 처리하므로 더 이상 직접 구현이 필요 없다."""
        return None
    
    def _get_max_dad_with_mom_same_row(self, sheet_result: Dict[str, Any]) -> float:
        """HeaderLocator 모듈로 이전된 기능."""
        return 0.0
    
    def _find_max_delivery_amount(self, sheet) -> float:
        """HeaderLocator 모듈에 위임된 기능."""
        return 0.0
    
    def _find_families_in_sheet(self, sheet, required_keywords: Dict) -> List[Dict]:
        """
        시트에서 5형제 가족 찾기
        
        Args:
            sheet: openpyxl Worksheet 객체
            required_keywords: 필수 컬럼 키워드 딕셔너리
            
        Returns:
            List[Dict]: 찾은 가족 정보 리스트
        """
        families = []
        
        try:
            # 헤더 행 찾기
            header_row = self._find_header_row(sheet)
            if header_row is None:
                return families
            
            # 컬럼 매핑
            column_mapping = self._map_columns(sheet, header_row, self.required_keywords)
            
            # 실제 데이터 범위 감지: 각 시트의 실제 마지막 행/열 찾기
            actual_max_row, actual_max_col = self.header_locator.get_actual_data_range(sheet)
            
            # 데이터 행에서 가족 정보 추출 (실제 데이터 범위 내에서)
            raw_families = []
            # 전체 실제 데이터 범위를 사용 (지침: 마지막 행까지 검열)
            max_rows = actual_max_row
            
            for row_num in range(header_row + 1, max_rows + 1):
                family_data = self.industry_rules.extract_family_from_row(
                    sheet,
                    row_num,
                    column_mapping,
                    actual_max_col,
                )
                if family_data:
                    raw_families.append(family_data)
            
            # 가족 통합 로직 적용
            families = self.industry_rules.merge_family_data(raw_families)
                    
        except Exception as e:
            self.logger.warning(f"가족 검색 중 오류: {str(e)}")
            
        return families
    
    def _get_max_dad_amount(self, families: List[Dict]) -> float:
        """
        가족들 중에서 아빠(총금액) 최대값 찾기
        
        Args:
            families: 가족 정보 리스트
            
        Returns:
            float: 최대 아빠 금액
        """
        max_amount = 0
        
        for family in families:
            dad_amount = family.get('dad_amount', 0)
            if isinstance(dad_amount, (int, float)) and dad_amount > max_amount:
                max_amount = dad_amount
                
        return max_amount
    
    
    def _to_number(self, value):
        """값을 숫자로 변환하는 유틸리티 함수"""
        try:
            if value is None:
                return 0.0
            if isinstance(value, (int, float)):
                return float(value)
            s = str(value).strip().replace(',', '')
            return float(s) if s not in ['', 'None', 'nan'] else 0.0
        except Exception:
            return 0.0

    def _find_actual_data_range(self, sheet) -> tuple[int, int]:
        """
        실제 데이터 범위 감지: 각 시트의 실제 마지막 행/열 찾기
        
        Args:
            sheet: openpyxl Worksheet 객체
            
        Returns:
            tuple: (실제_최대_행, 실제_최대_열)
        """
        actual_max_row = 1
        actual_max_col = 1
        
        try:
            # 모든 셀을 순회하여 실제 데이터가 있는 범위 찾기
            for row in sheet.iter_rows():
                for cell in row:
                    if cell.value is not None and str(cell.value).strip():
                        # 실제 데이터가 있는 셀 발견
                        if cell.row > actual_max_row:
                            actual_max_row = cell.row
                        if cell.column > actual_max_col:
                            actual_max_col = cell.column
            
            # 최소값 보장 (헤더가 있을 수 있으므로)
            actual_max_row = max(actual_max_row, 2)
            actual_max_col = max(actual_max_col, 5)
            
            self.logger.info(f"실제 데이터 범위 감지: 행 {actual_max_row}, 열 {actual_max_col}")
            
        except Exception as e:
            self.logger.warning(f"실제 데이터 범위 감지 중 오류: {str(e)}")
            # 오류 시 기본값 사용
            actual_max_row = min(sheet.max_row, 1000)
            actual_max_col = min(sheet.max_column, 50)
        
        return actual_max_row, actual_max_col
        """
        가족들 중에서 아빠(총금액) 최대값 찾기
        
        Args:
            families: 가족 정보 리스트
            
        Returns:
            float: 최대 아빠 금액
        """
        max_amount = 0
        
        for family in families:
            dad_amount = family.get('dad_amount', 0)
            if isinstance(dad_amount, (int, float)) and dad_amount > max_amount:
                max_amount = dad_amount
                
        return max_amount
    
    def _find_header_row(self, sheet) -> Optional[int]:
        """유연한 헤더 감지 시스템 (동적 컬럼 수 + 5형제 키워드 기반)"""
        # 5형제 키워드 정의
        header_keywords = ['사업자번호', '사업자등록번호', '상호명', '상호', '업체명', '가맹점명', 
                          '대표자', '대표자명', '주소', '사업장주소', '이메일', 'email']
        
        best_header_row = None
        best_score = 0
        
        for row_num in range(1, min(15, sheet.max_row + 1)):
            row_values = [str(cell.value).strip() for cell in sheet[row_num] if cell.value]
            
            # 최소 5개 컬럼이 있어야 헤더로 인정 (5형제 최소 요구사항)
            if len(row_values) >= 5:
                # 5형제 키워드 카운트
                header_count = 0
                for cell_value in row_values:
                    if any(keyword in cell_value for keyword in header_keywords):
                        header_count += 1
                
                # 5형제 키워드가 2개 이상 포함된 행을 헤더로 인정
                if header_count >= 2:
                    # 컬럼 수와 키워드 수를 종합한 점수 계산
                    score = header_count * 10 + len(row_values)
                    
                    if score > best_score:
                        best_score = score
                        best_header_row = row_num
        
        return best_header_row
    
    def _calculate_header_data_quality(self, sheet, header_row: int) -> float:
        """헤더 행의 데이터 품질 점수 계산"""
        try:
            # 헤더 다음 3행의 데이터 품질 확인
            quality_score = 0
            
            for check_row in range(header_row + 1, min(header_row + 4, sheet.max_row + 1)):
                row_values = [str(cell.value).strip() for cell in sheet[check_row] if cell.value]
                
                # 숫자 데이터 비율 계산
                number_count = 0
                for cell_value in row_values:
                    if self._to_number(cell_value) is not None:
                        number_count += 1
                
                if len(row_values) > 0:
                    number_ratio = number_count / len(row_values)
                    quality_score += number_ratio
            
            return quality_score
        except Exception:
            return 0
    
    def _map_columns(self, sheet, header_row: int, required_keywords: Dict) -> Dict[str, int]:
        """컬럼 매핑 (부가세 앞칸 규칙 적용)"""
        column_mapping = {}
        
        # 먼저 엄마(부가세) 컬럼 찾기
        mom_keywords = ['부가세', '세액', 'VAT', '세금', '부가세액']
        for col_num in range(1, sheet.max_column + 1):
            cell_value = str(sheet.cell(header_row, col_num).value).strip().lower()
            
            if any(keyword in cell_value for keyword in mom_keywords):
                column_mapping['mom_amount'] = col_num
                
                # 부가세 앞칸 규칙 적용: 부가세 앞칸이 총합계인지 확인
                dad_col = self._validate_dad_column_before_mom(sheet, col_num, header_row)
                if dad_col is not None:
                    column_mapping['dad_amount'] = dad_col
                    self.logger.info(f"부가세 앞칸 규칙 적용: 부가세 컬럼 {col_num} 앞칸 {dad_col}이 총합계로 확인됨")
                break
        
        # 기존 방식으로 아빠(총금액) 컬럼 찾기 (부가세 앞칸 규칙이 적용되지 않은 경우)
        if 'dad_amount' not in column_mapping:
            dad_keywords = ['총', '합계', '금액', '요금', '배달', '총금액', '총합', '배달요금', '총배달요금', '총배달금액']
            for col_num in range(1, sheet.max_column + 1):
                cell_value = str(sheet.cell(header_row, col_num).value).strip().lower()
                
                if any(keyword in cell_value for keyword in dad_keywords):
                    column_mapping['dad_amount'] = col_num
                    break
        
        # 5형제 컬럼 매핑 추가
        # 1. 사업자번호 컬럼 찾기 (정확한 매칭만)
        business_keywords = ['사업자번호', '사업자등록번호']
        for col_num in range(1, sheet.max_column + 1):
            cell_value = str(sheet.cell(header_row, col_num).value).strip().lower()
            if any(keyword in cell_value for keyword in business_keywords):
                column_mapping['business_number'] = col_num
                break
        
        # 2. 상호명 컬럼 찾기 (정확한 매칭만)
        store_keywords = ['상호명', '상호', '업체명', '업체', '매장명', '매장', '점포', '가게', '사업소', '가맹점명']
        for col_num in range(1, sheet.max_column + 1):
            cell_value = str(sheet.cell(header_row, col_num).value).strip().lower()
            if any(keyword in cell_value for keyword in store_keywords):
                column_mapping['store_name'] = col_num
                break
        
        # 3. 대표자명 컬럼 찾기
        def _score_representative_header(header: str) -> int:
            header_lower = header.lower()

            if not header_lower or header_lower in {'', 'none', 'nan'}:
                return -100

            score = 0

            # 명확한 대표자/사장 키워드에 높은 가중치 부여
            if '대표자' in header_lower:
                score += 90
            elif '대표' in header_lower:
                score += 70

            if any(keyword in header_lower for keyword in ['사장', '원장', '점주', '대표원장']):
                score += 60

            if any(keyword in header_lower for keyword in ['성명', '성함', '이름']):
                score += 40

            if any(keyword in header_lower for keyword in ['공급받는자', '수취인', '구매자', '거래처', '고객', '매입자', '업체', '가맹점', '매장', '점포', '업소']):
                score += 10

            # 담당자/등록자 계열은 낮은 가중치 부여
            if any(keyword in header_lower for keyword in ['담당', '매니저', '관리자', '점장']):
                score -= 30

            if any(keyword in header_lower for keyword in ['등록자', '작성자', '입력자']):
                score -= 50

            # 대표번호(전화번호) 등 혼동되는 컬럼은 강하게 패널티
            if '대표번호' in header_lower:
                score -= 80

            if '번호' in header_lower and not any(keyword in header_lower for keyword in ['성명', '성함', '이름']):
                score -= 60

            return score

        representative_fallback_keywords = ['등록자', '등록자명', '작성자', '입력자', '담당자', '담당']
        best_rep_col: Optional[int] = None
        best_rep_header: Optional[str] = None
        best_rep_score = -999
        fallback_rep_col: Optional[int] = None
        fallback_rep_header: Optional[str] = None

        for col_num in range(1, sheet.max_column + 1):
            raw_header_value = sheet.cell(header_row, col_num).value
            if raw_header_value is None:
                continue

            header_value = str(raw_header_value).strip()
            header_lower = header_value.lower()

            score = _score_representative_header(header_value)

            if score > best_rep_score:
                best_rep_score = score
                best_rep_col = col_num
                best_rep_header = header_value

            if fallback_rep_col is None and any(keyword in header_lower for keyword in representative_fallback_keywords):
                fallback_rep_col = col_num
                fallback_rep_header = header_value

        if best_rep_col is not None and best_rep_score >= 40:
            column_mapping['representative'] = best_rep_col
            self.logger.info(
                "대표자 컬럼 매핑: '%s' (점수 %s) -> 열 %s",
                best_rep_header,
                best_rep_score,
                best_rep_col,
            )
        elif best_rep_col is not None and best_rep_score > 0:
            column_mapping['representative'] = best_rep_col
            self.logger.info(
                "대표자 컬럼 매핑(완전 일치 없음, 점수 %s): '%s' -> 열 %s",
                best_rep_score,
                best_rep_header,
                best_rep_col,
            )
        elif fallback_rep_col is not None:
            column_mapping['representative'] = fallback_rep_col
            self.logger.info(
                "대표자 컬럼 미발견, 등록자 계열 fallback 사용: '%s' -> 열 %s",
                fallback_rep_header,
                fallback_rep_col,
            )
        
        # 4. 주소 컬럼 찾기
        address_keywords = ['주소', '사업장주소', '소재지', '사업장', '주소지']
        for col_num in range(1, sheet.max_column + 1):
            cell_value = str(sheet.cell(header_row, col_num).value).strip().lower()
            if any(keyword in cell_value for keyword in address_keywords):
                column_mapping['address'] = col_num
                break
        
        # 5. 이메일 컬럼 찾기
        email_keywords = ['이메일', 'email', '메일', '사업자이메일']
        for col_num in range(1, sheet.max_column + 1):
            cell_value = str(sheet.cell(header_row, col_num).value).strip().lower()
            if any(keyword in cell_value for keyword in email_keywords):
                column_mapping['email'] = col_num
                break
        
        # 매핑 결과 로깅
        self.logger.info(f"컬럼 매핑 결과: {column_mapping}")
        
        return column_mapping
    
    def _validate_dad_column_before_mom(self, sheet, mom_col: int, header_row: int) -> Optional[int]:
        """부가세 앞칸이 총합계인지 확인 (10:1 비율 검증)"""
        try:
            if mom_col <= 1:
                return None
            
            # 부가세 앞칸 확인
            dad_col = mom_col - 1
            
            # 10:1 비율 확인 (부가세 10% 규칙)
            valid_rows = 0
            total_rows = 0
            
            for row_num in range(header_row + 1, min(header_row + 20, sheet.max_row + 1)):
                try:
                    dad_cell = sheet.cell(row_num, dad_col)
                    mom_cell = sheet.cell(row_num, mom_col)
                    
                    dad_value = dad_cell.value
                    mom_value = mom_cell.value
                    
                    # 숫자 데이터인지 확인
                    if not isinstance(dad_value, (int, float)) or not isinstance(mom_value, (int, float)):
                        continue
                    
                    if dad_value <= 0 or mom_value <= 0:
                        continue
                    
                    total_rows += 1
                    
                    # 10:1 비율 확인 (9.5:1 ~ 10.5:1 범위 허용)
                    ratio = dad_value / mom_value
                    if 9.5 <= ratio <= 10.5:
                        valid_rows += 1
                        
                except (ValueError, TypeError):
                    continue
            
            # 70% 이상의 행이 10:1 비율을 만족하면 유효한 총합계 컬럼으로 인정
            if total_rows > 0 and (valid_rows / total_rows) >= 0.7:
                self.logger.info(f"부가세 앞칸 규칙 검증 성공: 컬럼 {dad_col}이 총합계로 확인됨 (유효 비율: {valid_rows}/{total_rows})")
                return dad_col
            
            return None
            
        except Exception as e:
            self.logger.error(f"부가세 앞칸 규칙 검증 오류: {str(e)}")
            return None
    
    def _extract_family_from_row(
        self,
        sheet,
        row_num: int,
        column_mapping: Dict,
        actual_max_col: int,
    ) -> Optional[Dict]:
        """산업 규칙 모듈에 위임된 가족 추출 래퍼."""

        return self.industry_rules.extract_family_from_row(
            sheet,
            row_num,
            column_mapping,
            actual_max_col,
        )
    
    def _merge_family_data(self, families: List[Dict]) -> List[Dict]:
        """산업 규칙 모듈에 위임된 가족 통합 래퍼."""

        return self.industry_rules.merge_family_data(families)
    
    def _evaluate_sheet(
        self,
        sheet,
        sheet_name: str,
        required_keywords: Dict,
        forbidden_keywords_map: Dict = None,
    ) -> Optional[Dict[str, Any]]:
        """HeaderLocator 모듈 사용으로 더 이상 직접 사용하지 않는다."""
        return None
    
    def _count_matched_fields(self, sheet, row: int, max_col: int, required_keywords: Dict, forbidden_keywords_map: Dict = None) -> int:
        """
        특정 행에서 필수 컬럼 매칭 개수 계산 (지능앱 기술 강화 + 전기 연결 시스템)
        5개 핵심 필드 정밀 매칭으로 헤더 검증 + 금지어 시스템으로 정확도 향상
        
        Args:
            sheet: openpyxl Worksheet 객체
            row: 행 번호
            max_col: 최대 컬럼 수
            required_keywords: 필수 컬럼 키워드 딕셔너리
            forbidden_keywords_map: 금지어 맵 (전기 연결 시스템)
            
        Returns:
            int: 매칭된 필드 개수
        """
        matched_fields = set()  # 중복 매칭 방지
        
        # 최대 컬럼 수를 50개로 제한 (성능 최적화)
        max_col = min(max_col, 50)
        
        # 각 컬럼의 값을 확인하여 키워드 매칭
        for col in range(1, max_col + 1):
            cell_value = sheet.cell(row=row, column=col).value
            if cell_value is None:
                continue
                
            cell_text = str(cell_value).lower().strip()
            
            # 지능앱 기술: 각 필드 타입별 정밀 키워드 매칭 + 금지어 시스템
            for field_type, keywords in required_keywords.items():
                if field_type in matched_fields:
                    continue  # 이미 매칭된 필드는 건너뛰기
                
                # 전기 연결 시스템: 금지어 체크
                if forbidden_keywords_map and field_type in forbidden_keywords_map:
                    forbidden_keywords = forbidden_keywords_map[field_type]
                    is_forbidden = any(forbidden_keyword.lower() in cell_text for forbidden_keyword in forbidden_keywords)
                    if is_forbidden:
                        self.logger.debug(f"금지어 감지: {field_type} 필드에서 금지어 발견 '{cell_text}' (행 {row}, 컬럼 {col})")
                        continue  # 금지어가 포함된 컬럼은 해당 필드에서 제외
                    
                for keyword in keywords:
                    keyword_lower = keyword.lower()
                    
                    # 정확한 매칭 (부분 문자열 포함)
                    if keyword_lower in cell_text:
                        matched_fields.add(field_type)
                        self.logger.debug(f"지능앱 헤더 감지: {field_type} 매칭 '{keyword}' → '{cell_text}' (행 {row}, 컬럼 {col})")
                        break
        
        matched_count = len(matched_fields)
        self.logger.debug(f"지능앱 헤더 감지: 행 {row}에서 {matched_count}개 필드 매칭 ({matched_fields})")
        
        return matched_count
    
    def _evaluate_data_quality(self, data: List[List], headers: List[str]) -> float:
        """
        데이터 품질 평가
        지능앱 기술: 데이터 완성도와 일관성 평가
        """
        if not data or not headers:
            return 0.0
        
        total_cells = len(data) * len(headers)
        if total_cells == 0:
            return 0.0
        
        empty_cells = 0
        for row in data:
            for cell in row:
                if cell is None or str(cell).strip() == "":
                    empty_cells += 1
        
        completeness_score = 1.0 - (empty_cells / total_cells)
        
        consistency_score = 0.0
        if len(data) > 1:
            row_lengths = [
                len([cell for cell in row if cell is not None and str(cell).strip()])
                for row in data
            ]
            if row_lengths:
                avg_length = sum(row_lengths) / len(row_lengths)
                variance = sum((length - avg_length) ** 2 for length in row_lengths) / len(row_lengths)
                consistency_score = max(0.0, 1.0 - (variance / (avg_length + 1)))
        
        quality_score = completeness_score * 0.7 + consistency_score * 0.3
        
        return min(1.0, max(0.0, quality_score))

    def _inspect_all_sheets_fast(self, workbook: openpyxl.Workbook) -> Optional[Dict]:
        """빠른 검열 요청 시에도 HeaderLocator 결과를 재사용한다."""
        try:
            return self._inspect_all_sheets(workbook)
        except Exception as exc:
            self.logger.error("빠른 시트 검열 중 오류: %s", exc)
            return None
    
    def _quick_header_scan(self, sheet, max_rows: int = 5) -> Optional[Dict]:
        """헤더 빠른 스캔 - 처음 몇 행만 체크"""
        # 5가지 필수 헤더에 대한 풍부한 동의어 세트 (정규화 비교)
        def _norm(s: str) -> str:
            return str(s).replace('\n', '').replace(' ', '').replace('\t', '').strip().lower()

        required_synonyms = {
            '사업자번호': [_norm(x) for x in ['사업자번호','사업자등록번호','등록번호','사업자','공급받는자사업자번호','공급받는자 사업자번호']],
            '가맹점명': [_norm(x) for x in ['가맹점명','가맹점','상호','상호명','매장명','점포명','공급받는자상호','공급받는자 상호']],
            '대표자명': [_norm(x) for x in ['대표자명','대표자','대표','성명','이름','공급받는자대표자','공급받는자 대표자']],
            '주소':   [_norm(x) for x in ['주소','사업장주소','업체주소','소재지','공급받는자주소','공급받는자 주소']],
            '이메일': [_norm(x) for x in ['이메일','메일','email','mail','공급받는자이메일','공급받는자 이메일']]
        }
        try:
            # 스캔 범위 설정
            max_rows = min(max_rows, sheet.max_row)
            for row in range(1, max_rows + 1):
                headers = []
                for col in range(1, sheet.max_column + 1):
                    cell_value = sheet.cell(row=row, column=col).value
                    if cell_value is not None:
                        headers.append(str(cell_value).strip())
                
                # 필수 헤더 매칭 체크
                matched_headers = []
                norm_headers = [_norm(h) for h in headers]
                for nh in norm_headers:
                    # 각 필수 항목의 동의어가 하나라도 포함되면 매칭으로 인정
                    for key, syns in required_synonyms.items():
                        if any(s in nh for s in syns):
                            matched_headers.append(nh)
                            break
                
                if len(matched_headers) >= 2:
                    return {
                        'row': row,
                        'headers': headers,
                        'matched_headers': matched_headers,
                        'match_count': len(matched_headers)
                    }
        except Exception as e:
            self.logger.error(f"헤더 빠른 스캔 오류: {str(e)}")
            return None
        return None

    def _evaluate_sheet_fast(self, sheet, 
                           sheet_name: str, header_info: Dict, 
                           config: Dict) -> Optional[Dict]:
        """빠른 시트 평가"""
        try:
            # 헤더 정보 기반 계산
            original_score = header_info['match_count'] / 5.0  # 5개 필수 헤더 기준
            
            # 가중치 계산 (간단화)
            if header_info['match_count'] == 5:
                weighted_score = 100  # 완벽 매칭 우선
            else:
                weighted_score = int(original_score * 90)  # 기타는 점수 기반
            
            return {
                'sheet_name': sheet_name,
                'original_score': original_score,
                'weighted_score': weighted_score,
                'header_row': header_info['row'],
                'data_start_row': header_info['row'] + 1,
                'headers': header_info['headers'],
                'data': self._extract_sheet_data_optimized(sheet, header_info['row'] + 1, 
                                                         header_info['headers'])
            }
            
        except Exception as e:
            self.logger.error(f"빠른 시트 평가 오류: {str(e)}")
            return None
    
    def _extract_sheet_data_optimized(self, sheet, 
                                    start_row: int, headers: List[str]) -> List[List]:
        """최적화된 데이터 추출 - 필요한 컬럼만"""
        data = []
        
        # 필수 컬럼 인덱스만 추출
        essential_columns = []
        for i, header in enumerate(headers):
            if any(keyword in header for keyword in ['사업자번호', '가맹점명', '대표자', '주소', '이메일', '세', '금액']):
                essential_columns.append(i)
        
        # 지침 반영: 실제 마지막 행까지 처리
        max_rows = sheet.max_row
        
        for row_idx in range(start_row, max_rows):
            row_data = [None] * len(headers)
            has_data = False
            
            for col_idx in essential_columns:
                cell_value = sheet.cell(row=row_idx, column=col_idx + 1).value
                if cell_value:
                    row_data[col_idx] = cell_value
                    has_data = True
            
            if has_data:
                data.append(row_data)
        
        return data
    
    def _parse_excel(self, file_path: Path) -> Dict[str, Any]:
        """Excel 파일 파싱 - 지능앱 시트 검열 알고리즘 적용"""
        try:
            if file_path.suffix.lower() == '.xlsx' and not zipfile.is_zipfile(file_path):
                self.logger.error(
                    "손상된 Excel 형식 감지: %s", file_path
                )
                return self._create_error_response(
                    "업로드하신 Excel 파일이 손상되었거나 지원하지 않는 형식입니다. 엑셀에서 '다른 이름으로 저장' 후 다시 시도해주세요."
                )
            workbook = openpyxl.load_workbook(file_path, data_only=True)
            best_sheet_result = self.header_locator.inspect_all_sheets(
                workbook,
                self.required_keywords,
                family_extractor=self._find_families_in_sheet,
                number_parser=self._to_number,
            )
            
            if not best_sheet_result:
                return self._create_error_response("적합한 시트를 찾을 수 없습니다.")
            
            # 추가 안전성 검증: best_sheet_result가 None인 경우 처리
            if best_sheet_result is None:
                self.logger.error("best_sheet_result가 None입니다.")
                return self._create_error_response("시트 검열 결과를 찾을 수 없습니다.")
            
            # 추가 안전성 검증: best_sheet_result가 딕셔너리가 아닌 경우 처리
            if not isinstance(best_sheet_result, dict):
                self.logger.error(f"best_sheet_result가 딕셔너리가 아닙니다: {type(best_sheet_result)}")
                return self._create_error_response("시트 검사 결과가 올바르지 않습니다.")
            
            # 최적의 시트 정보 추출 (안전한 접근)
            best_sheet_name = best_sheet_result.get('sheet_name', 'Unknown')
            best_header_row = best_sheet_result.get('header_row', 1)
            best_data_start_row = best_sheet_result.get('data_start_row', 2)
            best_headers = best_sheet_result.get('headers', [])
            best_data = best_sheet_result.get('data', [])
            
            # 중요: 1순위 시트 데이터로 완전히 교체
            if 'priority' in best_sheet_result and best_sheet_result['priority'] == '1순위':
                self.logger.info(f"1순위 시트 '{best_sheet_name}' 데이터로 완전 교체")
                # 모든 시트 정보 초기화하고 1순위 시트만 사용
                all_sheets = {
                    best_sheet_name: {
                        'headers': best_headers,
                        'data': best_data,
                        'header_row': best_header_row,
                        'data_start_row': best_data_start_row,
                        'priority': '1순위',
                        'families': best_sheet_result.get('families', [])
                    }
                }
            
            # 안전성 검증: 필수 정보가 없으면 오류 반환
            if not best_headers or not best_data:
                self.logger.error(f"시트 정보 불완전: headers={len(best_headers)}, data={len(best_data)}")
                return self._create_error_response("시트에서 헤더 또는 데이터를 찾을 수 없습니다.")
            
            self.logger.info(f"최적 시트 선택: {best_sheet_name} (헤더: {best_header_row}행)")
            
            # DataFrame 생성
            df = pd.DataFrame(best_data, columns=best_headers)
            
            # 연동 모듈을 통한 헤더 분석
            header_analysis = self.header_analyzer.analyze_headers(best_headers)
            self.logger.info(f"헤더 분석 완료: {header_analysis.get('analysis_summary', {})}")
            
            # 연동 모듈을 통한 데이터 처리
            processed_data = self.data_processor.process_excel_data(df, best_headers)
            self.logger.info(f"데이터 처리 완료: {processed_data.get('summary', {})}")
            
            # header_row 변수 정의 (best_header_row 사용)
            header_row = best_header_row
            
            # data_start_row 변수 정의 (best_data_start_row 사용)
            data_start_row = best_data_start_row
            
            # headers 변수 정의 (best_headers 사용)
            headers = best_headers
            
            # 데이터 섹션 분석
            data_sections = self._analyze_data_sections(df)
            
            # 1순위 시트가 이미 선택된 경우 다른 시트 정보 수집하지 않음
            if 'priority' in best_sheet_result and best_sheet_result['priority'] == '1순위':
                self.logger.info(f"1순위 시트 '{best_sheet_name}' 선택됨 - 다른 시트 정보 수집 생략")
                # 1순위 시트만 사용하므로 all_sheets는 이미 위에서 설정됨
            else:
                # 모든 시트 정보 수집 (2순위 시트 선택을 위해)
                all_sheets = {}
                for sheet_name in workbook.sheetnames:
                    try:
                        sheet = workbook[sheet_name]
                        # 각 시트의 기본 정보 수집
                        sheet_info = {
                            'sheet_name': sheet_name,
                            'max_row': sheet.max_row,
                            'max_column': sheet.max_column,
                            'headers': [],
                            'data': []
                        }
                        
                        # 헤더 정보 수집 (상위 10행에서)
                        for row in range(1, min(11, sheet.max_row + 1)):
                            row_headers = []
                            for col in range(1, min(51, sheet.max_column + 1)):  # 최대 50컬럼
                                cell_value = sheet.cell(row=row, column=col).value
                                if cell_value is not None:
                                    row_headers.append(str(cell_value).strip())
                                else:
                                    row_headers.append("")
                            sheet_info['headers'].append(row_headers)
                        
                        # 데이터 샘플 수집 (상위 100행, 최대 50컬럼)
                        for row in range(1, min(101, sheet.max_row + 1)):
                            row_data = []
                            for col in range(1, min(51, sheet.max_column + 1)):
                                cell_value = sheet.cell(row=row, column=col).value
                                row_data.append(cell_value)
                            sheet_info['data'].append(row_data)
                        
                        all_sheets[sheet_name] = sheet_info
                        
                    except Exception as e:
                        self.logger.warning(f"시트 '{sheet_name}' 정보 수집 실패: {str(e)}")
                        continue
            
            self.logger.info(f"모든 시트 정보 수집 완료: {len(all_sheets)}개 시트")
            
            return {
                'file_type': 'excel',
                'raw_data': df,
                'headers': best_headers,
                'data_sections': data_sections,
                'total_rows': len(df),
                'parsing_status': 'success',
                'file_path': str(file_path),
                'selected_sheet': best_sheet_name,
                'sheet_inspection_result': best_sheet_result,
                'all_sheets': all_sheets,  # 모든 시트 정보 추가
                'families': best_sheet_result.get('families', [])  # 가족 데이터 추가
            }
            
        except zipfile.BadZipFile as e:
            self.logger.error(f"손상된 Excel 압축 구조: {file_path} - {str(e)}")
            return self._create_error_response(
                "Excel 파일 구조를 읽을 수 없습니다. 원본 파일을 열어 '다른 이름으로 저장' 한 뒤 다시 업로드해주세요."
            )
        except openpyxl.utils.exceptions.InvalidFileException as e:
            self.logger.error(f"Excel 파일 형식 오류: {file_path} - {str(e)}")
            return self._create_error_response("Excel 파일이 손상되었거나 지원하지 않는 형식입니다.")
        except PermissionError as e:
            self.logger.error(f"Excel 파일 접근 권한 오류: {file_path} - {str(e)}")
            return self._create_error_response("Excel 파일이 다른 프로그램에서 사용 중입니다. 파일을 닫고 다시 시도해주세요.")
        except ValueError as e:
            self.logger.error(f"Excel 데이터 값 오류: {file_path} - {str(e)}")
            return self._create_error_response("Excel 파일 내 데이터 형식이 올바르지 않습니다.")
        except Exception as e:
            self.logger.error(f"Excel 파싱 중 예상치 못한 오류 발생: {file_path} - {str(e)}", exc_info=True)
            return self._create_error_response(f"Excel 파일 처리 중 오류가 발생했습니다. 관리자에게 문의해주세요. (오류 코드: {hash(str(e)) % 10000})")
    
    def _parse_csv(self, file_path: Path) -> Dict[str, Any]:
        """CSV 파일 파싱 - 헤더 제목 밑 빈 칸부터 데이터 추출"""
        try:
            # CSV 파일 읽기 (인코딩 자동 감지)
            encodings = ['utf-8', 'cp949', 'euc-kr', 'utf-8-sig']
            df = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is None:
                return self._create_error_response("CSV 파일 인코딩을 확인할 수 없습니다.")
            
            # 헤더 행 자동 감지 (CSV는 보통 첫 행이 헤더)
            # 하지만 빈 행이 있을 수 있으므로 검증
            header_row = self.header_locator.detect_csv_header_row(df, self.required_keywords)
            self.logger.info(f"CSV 헤더 행 감지: {header_row}행")
            
            # 헤더 행부터 데이터 추출
            if header_row > 0:
                df = df.iloc[header_row:]
                df.columns = df.iloc[0]  # 첫 행을 헤더로 설정
                df = df.drop(df.index[0])  # 첫 행 제거
                df = df.reset_index(drop=True)  # 인덱스 재설정
            
            # 데이터 섹션 분석
            data_sections = self._analyze_data_sections(df)
            
            return {
                'file_type': 'csv',
                'raw_data': df,
                'headers': list(df.columns),
                'data_sections': data_sections,
                'total_rows': len(df),
                'parsing_status': 'success',
                'file_path': str(file_path)
            }
            
        except UnicodeDecodeError as e:
            self.logger.error(f"CSV 파일 인코딩 오류: {file_path} - {str(e)}")
            return self._create_error_response("CSV 파일의 인코딩을 인식할 수 없습니다. UTF-8 또는 CP949 형식으로 저장해주세요.")
        except PermissionError as e:
            self.logger.error(f"CSV 파일 접근 권한 오류: {file_path} - {str(e)}")
            return self._create_error_response("CSV 파일이 다른 프로그램에서 사용 중입니다. 파일을 닫고 다시 시도해주세요.")
        except ValueError as e:
            self.logger.error(f"CSV 데이터 값 오류: {file_path} - {str(e)}")
            return self._create_error_response("CSV 파일 내 데이터 형식이 올바르지 않습니다.")
        except Exception as e:
            self.logger.error(f"CSV 파싱 중 예상치 못한 오류 발생: {file_path} - {str(e)}", exc_info=True)
            return self._create_error_response(f"CSV 파일 처리 중 오류가 발생했습니다. 관리자에게 문의해주세요. (오류 코드: {hash(str(e)) % 10000})")
    
    def _analyze_data_sections(self, df: pd.DataFrame) -> Dict[str, Any]:
        """데이터 섹션 분석을 리포팅 유틸로 위임."""

        return self.reporting_utils.analyze_data_sections(df)
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """오류 응답 생성"""
        return {
            'file_type': 'unknown',
            'raw_data': None,
            'headers': [],
            'data_sections': {},
            'total_rows': 0,
            'parsing_status': 'error',
            'error_message': error_message
        }
    
    def get_data_preview(self, parsed_data: Dict[str, Any], max_rows: int = 10) -> Dict[str, Any]:
        """리포팅 유틸리티를 통한 미리보기 데이터 생성."""

        return self.reporting_utils.build_preview(parsed_data, max_rows)
    
    def extract_text_content(self, parsed_data: Dict[str, Any]) -> str:
        """리포팅 유틸리티에 텍스트 추출을 위임."""

        return self.reporting_utils.extract_text_content(parsed_data)

    # ------------------------------------------------------------------
    # 병렬/배치 처리 래퍼
    # ------------------------------------------------------------------
    def parse_multiple_files_parallel(
        self,
        file_paths: List[Path],
        max_workers: int = 4,
    ) -> List[Dict[str, Any]]:
        """ThreadPoolExecutor 기반 병렬 파싱."""

        return self.parallel_runner.parse_multiple_files_parallel(file_paths, max_workers)

    def batch_validate_files(
        self,
        file_paths: List[Path],
        max_workers: int = 4,
    ) -> Dict[str, Any]:
        """파일 업로드 유효성 배치 검증."""

        return self.parallel_runner.batch_validate_files(file_paths, max_workers)

    def parse_multiple_files_optimized(
        self,
        file_paths: List[Path],
        max_workers: int = 4,
    ) -> List[Dict[str, Any]]:
        """ParallelFileProcessor 기반 고성능 병렬 파싱."""

        return self.parallel_runner.parse_multiple_files_optimized(file_paths, max_workers)

    def process_files_with_progress(
        self,
        file_paths: List[Path],
        progress_callback: Optional[Callable[[float, int, int], None]] = None,
    ) -> List[Dict[str, Any]]:
        """진행률 콜백을 포함한 파일 처리."""

        return self.parallel_runner.process_files_with_progress(file_paths, progress_callback)

    def validate_single_file(self, file_path: Path) -> bool:
        """단일 파일 유효성 검증."""

        return self.parallel_runner.validate_single_file(file_path)

    def _merge_families_by_business_number(
        self,
        families: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """산업 규칙 모듈에 위임된 사업자번호 통합."""

        return self.industry_rules.merge_families_by_business_number(families)
    
    def _apply_dad_fallback_logic(self, families: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """산업 규칙 모듈에 위임된 금액 보정."""

        return self.industry_rules.apply_dad_fallback_logic(families)

