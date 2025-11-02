"""
파일 파싱 부품 - 배달대행사 정산서 파일 파싱
핵심기술 절대지침에 따라 파일을 파싱하고 구조화된 데이터 반환
"""

import pandas as pd
import openpyxl
from typing import Dict, List, Any, Optional, Callable
import logging
from pathlib import Path
import concurrent.futures  # Python 3.14 Free-Threaded Python 활용
import threading  # Python 3.14에서 GIL 제거로 성능 향상
import time  # 병렬 처리 시간 측정용
from .parallel_processor import ParallelFileProcessor, ProcessingMode, process_files_parallel
from .file_parser_utils.data_processor import DataProcessor
from .file_parser_utils.header_analyzer import HeaderAnalyzer
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
        self.file_upload_validator = FileUploadValidator(self.supported_formats, max_size_mb=100, logger=self.logger)
        
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
        """
        헤더 행 자동 감지
        지능앱 기술: 제목/부제목 행을 건너뛰고 실제 헤더 행 찾기
        
        Returns:
            int: 헤더 행 번호 (1부터 시작)
        """
        max_row = sheet.max_row
        max_col = sheet.max_column
        
        # 🎯 제목/부제목 행 감지 및 건너뛰기
        title_rows = self._detect_title_rows(sheet, max_col)
        self.logger.info(f"🔍 제목/부제목 행 감지: {title_rows}")
        
        # 상위 1000행에서 헤더 후보 검색 (제목 행 제외)
        header_candidates = []
        
        for row in range(1, min(1001, max_row + 1)):
            # 제목/부제목 행은 건너뛰기
            if row in title_rows:
                continue
                
            # 해당 행의 데이터 밀도 계산
            data_density = self._calculate_data_density(sheet, row, max_col)
            header_candidates.append((row, data_density))
        
        if not header_candidates:
            # 헤더 후보가 없으면 기본값 사용
            self.logger.warning("헤더 후보가 없습니다. 기본 헤더 행 사용")
            return 1
        
        # 데이터 밀도가 가장 높은 행을 헤더로 선택 (결정적 정렬)
        header_candidates.sort(key=lambda x: (x[1], x[0]), reverse=True)  # 밀도, 행번호 순
        best_header_row = header_candidates[0][0]
        
        self.logger.info(f"헤더 후보 분석: {header_candidates[:5]}...")  # 처음 5개만 로그
        self.logger.info(f"선택된 헤더 행: {best_header_row}")
        
        return best_header_row
    
    def _detect_title_rows(self, sheet, max_col: int) -> List[int]:
        """
        제목/부제목 행 감지
        지능앱 기술: 제목/부제목 행을 감지하여 헤더 검색에서 제외
        
        Args:
            sheet: Excel 시트 객체
            max_col: 최대 컬럼 수
            
        Returns:
            List[int]: 제목/부제목 행 번호 리스트
        """
        title_rows = []
        
        # 상위 20행에서 제목/부제목 패턴 감지
        for row in range(1, min(21, sheet.max_row + 1)):
            # 해당 행의 텍스트 패턴 분석
            text_pattern = self._analyze_text_pattern(sheet, row, max_col)
            
            # 제목/부제목 패턴 감지
            if self._is_title_pattern(text_pattern):
                title_rows.append(row)
                self.logger.debug(f"제목/부제목 행 감지: {row}행 - {text_pattern}")
        
        return title_rows
    
    def _analyze_text_pattern(self, sheet, row: int, max_col: int) -> Dict[str, Any]:
        """
        텍스트 패턴 분석
        지능앱 기술: 행의 텍스트 패턴을 분석하여 제목/부제목 여부 판단
        
        Args:
            sheet: Excel 시트 객체
            row: 행 번호
            max_col: 최대 컬럼 수
            
        Returns:
            Dict[str, Any]: 텍스트 패턴 정보
        """
        text_count = 0
        number_count = 0
        empty_count = 0
        long_text_count = 0  # 긴 텍스트 개수
        
        # 최대 컬럼 수를 50개로 제한 (성능 최적화)
        max_col = min(max_col, 50)
        
        for col in range(1, max_col + 1):
            cell_value = sheet.cell(row=row, column=col).value
            
            if cell_value is None or str(cell_value).strip() == '':
                empty_count += 1
            elif isinstance(cell_value, (int, float)):
                number_count += 1
            else:
                text_count += 1
                # 긴 텍스트 (제목/부제목 가능성)
                if len(str(cell_value).strip()) > 10:
                    long_text_count += 1
        
        return {
            'text_count': text_count,
            'number_count': number_count,
            'empty_count': empty_count,
            'long_text_count': long_text_count,
            'total_cells': max_col
        }
    
    def _is_title_pattern(self, pattern: Dict[str, Any]) -> bool:
        """
        제목/부제목 패턴 판단
        지능앱 기술: 텍스트 패턴을 분석하여 제목/부제목 여부 판단
        
        Args:
            pattern: 텍스트 패턴 정보
            
        Returns:
            bool: 제목/부제목 패턴 여부
        """
        # 제목/부제목 패턴 조건
        conditions = [
            # 조건 1: 텍스트가 많고 숫자가 적음
            pattern['text_count'] > pattern['number_count'] * 2,
            
            # 조건 2: 긴 텍스트가 있음 (제목/부제목 가능성)
            pattern['long_text_count'] > 0,
            
            # 조건 3: 전체 셀 대비 텍스트 비율이 높음
            pattern['text_count'] / pattern['total_cells'] > 0.3,
            
            # 조건 4: 빈 셀이 많음 (제목/부제목은 보통 일부 셀만 사용)
            pattern['empty_count'] / pattern['total_cells'] > 0.5
        ]
        
        # 3개 이상 조건 만족 시 제목/부제목으로 판단
        return sum(conditions) >= 3
    
    def _calculate_data_density(self, sheet, row: int, max_col: int) -> float:
        """
        특정 행의 데이터 밀도 계산
        지능앱 기술: 데이터 밀도 기반 헤더 감지
        
        Args:
            sheet: Excel 시트 객체
            row: 행 번호
            max_col: 최대 컬럼 수
            
        Returns:
            float: 데이터 밀도 점수
        """
        text_count = 0
        number_count = 0
        empty_count = 0
        
        # 최대 컬럼 수를 50개로 제한 (성능 최적화)
        max_col = min(max_col, 50)
        
        for col in range(1, max_col + 1):
            cell_value = sheet.cell(row=row, column=col).value
            
            if cell_value is None or str(cell_value).strip() == "":
                empty_count += 1
            elif isinstance(cell_value, (int, float)):
                number_count += 1
            else:
                text_count += 1
        
        # 헤더는 보통 텍스트가 많고, 데이터는 숫자가 많음
        # 텍스트 비율이 높을수록 헤더일 가능성이 높음
        total_cells = max_col
        if total_cells == 0:
            return 0.0
        
        text_ratio = text_count / total_cells
        number_ratio = number_count / total_cells
        empty_ratio = empty_count / total_cells
        
        # 헤더 점수 계산 (텍스트 비율이 높을수록 높은 점수)
        header_score = text_ratio * 2 + number_ratio * 0.5 + empty_ratio * 0.1
        
        return header_score
    
    def _detect_csv_header_row(self, df: pd.DataFrame) -> int:
        """
        CSV 파일의 헤더 행 감지 (지능앱 기술 강화)
        5개 핵심 필드 매칭으로 정밀한 헤더 감지
        
        Args:
            df: pandas DataFrame
            
        Returns:
            int: 헤더 행 번호 (0부터 시작)
        """
        if len(df) == 0:
            return 0
        
        # 지능앱 기술: 필수 5개 컬럼 키워드 (클래스 속성 사용)
        
        # 지능앱 기술: 상위 10행에서 헤더 후보 검색
        header_candidates = []
        scan_rows = min(10, len(df))
        
        for row_idx in range(scan_rows):
            # 해당 행의 데이터 밀도 계산
            data_density = self._calculate_csv_data_density(df, row_idx)
            
            # 지능앱 기술: 5가지 필수 컬럼 매칭 확인
            matched_fields = self._count_csv_matched_fields(df, row_idx, self.required_keywords)
            
            # 지능앱 기술: 헤더 점수 계산
            field_match_score = (matched_fields / 5) * 0.8
            density_score = data_density * 0.2
            header_score = field_match_score + density_score
            
            if matched_fields >= 3:  # 최소 3개 필드 매칭
                header_candidates.append({
                    'row': row_idx,
                    'data_density': data_density,
                    'matched_fields': matched_fields,
                    'header_score': header_score
                })
                self.logger.debug(f"지능앱 CSV 헤더 후보: 행 {row_idx}, 점수 {header_score:.3f}, 매칭 {matched_fields}개")
        
        if not header_candidates:
            # 매칭된 헤더가 없으면 데이터 밀도로 선택 (결정적 정렬)
            density_scores = [(row, self._calculate_csv_data_density(df, row)) for row in range(scan_rows)]
            density_scores.sort(key=lambda x: (x[1], -x[0]), reverse=True)  # 밀도 높은 순, 행번호 낮은 순
            best_header_row = density_scores[0][0]
            self.logger.warning(f"지능앱 CSV 헤더 감지: 매칭된 헤더가 없어 데이터 밀도로 선택 - 행 {best_header_row}")
        else:
            # 지능앱 기술: 최적 헤더 선택 (결정적 정렬)
            header_candidates.sort(key=lambda x: (x['matched_fields'], x['header_score'], x['row']), reverse=True)
            best_header = header_candidates[0]
            best_header_row = best_header['row']
            self.logger.info(f"지능앱 CSV 헤더 감지: 최적 헤더 선택 - 행 {best_header_row} (점수: {best_header['header_score']:.3f}, 매칭: {best_header['matched_fields']}개)")
        
        return best_header_row
    
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
        """
        CSV 특정 행에서 필수 컬럼 매칭 개수 계산 (지능앱 기술)
        
        Args:
            df: pandas DataFrame
            row_idx: 행 인덱스
            required_keywords: 필수 컬럼 키워드 딕셔너리
            
        Returns:
            int: 매칭된 필드 개수
        """
        if row_idx >= len(df):
            return 0
            
        matched_fields = set()
        row_data = df.iloc[row_idx]
        
        # 각 셀의 값을 확인하여 키워드 매칭
        for col_idx, cell_value in enumerate(row_data):
            if pd.isna(cell_value):
                continue
                
            cell_text = str(cell_value).lower().strip()
            
            # 지능앱 기술: 각 필드 타입별 정밀 키워드 매칭
            for field_type, keywords in required_keywords.items():
                if field_type in matched_fields:
                    continue
                    
                for keyword in keywords:
                    keyword_lower = keyword.lower()
                    if keyword_lower in cell_text:
                        matched_fields.add(field_type)
                        self.logger.debug(f"지능앱 CSV 헤더 감지: {field_type} 매칭 '{keyword}' → '{cell_text}' (행 {row_idx}, 컬럼 {col_idx})")
                        break
        
        matched_count = len(matched_fields)
        self.logger.debug(f"지능앱 CSV 헤더 감지: 행 {row_idx}에서 {matched_count}개 필드 매칭 ({matched_fields})")
        
        return matched_count
    
    def _inspect_all_sheets(self, workbook) -> Optional[Dict[str, Any]]:
        """
        지능앱 핵심 기술: 모든 시트를 검열하여 최적의 시트 선택
        배달대행사 정산서의 5가지 필수 컬럼을 기준으로 시트 평가
        
        Args:
            workbook: openpyxl Workbook 객체
            
        Returns:
            Dict: 최적의 시트 정보 또는 None
        """
        sheet_results = []
        best_result = None
        best_score = -1

        # Load delivery scoring config (기본값 사용)
        weights = {
            'business_number': 30,
            'representative': 10,
            'address': 30,
            'email': 20,
            'store_name': 10,
        }
        thresholds = {'pass': 80, 'candidate': 70}
        override_all5 = True
        
        # 필수 5개 컬럼 키워드 (지능앱 기술 - 강화된 키워드)
        required_keywords = {
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
                '상호', '상호명', '가맹점명', '매장명', '업체명', '가게명', '점포명', '매장', '점포', '업체', '가게',
                '공급받는자 상호', '공급받는자 상호명', '공급받는자 회사명', '공급받는자 업체명', '공급받는자 가게명',
                '공급받는자명', '공급받는자매장', '공급받는자 매장', '공급받는자점포', '공급받는자 점포',
                '구매자명', '구매자 상호', '구매자 상호명', '구매자 업체명', '구매자 회사명', '구매자 가게명',
                '수취인명', '수취인 상호', '수취인 상호명', '수취인 업체명', '수취인 회사명', '수취인 가게명',
                '수령인명', '수령인 상호', '수령인 상호명', '수령인 업체명', '수령인 회사명', '수령인 가게명',
                '받는이명', '받는이 상호', '받는이 상호명', '받는이 업체명', '받는이 회사명', '받는이 가게명',
                '수신자명', '수신자 상호', '수신자 상호명', '수신자 업체명', '수신자 회사명', '수신자 가게명',
                '고객명', '고객 상호', '고객 상호명', '고객 업체명', '고객 회사명', '고객 가게명',
                '거래처명', '거래처 상호', '거래처 상호명', '거래처 업체명', '거래처 회사명', '거래처 가게명',
                '클라이언트명', '클라이언트 상호', '클라이언트 상호명', '클라이언트 업체명', '클라이언트 회사명',
                '파트너사명', '파트너 상호', '파트너 상호명', '파트너 업체명', '파트너 회사명',
                '매입자명', '매입자 상호', '매입자 상호명', '매입자 업체명', '매입자 회사명', '매입자 가게명',
                '회사', '상점', '사업장', '사업소', '업소명', '브랜드명', '브랜드', '체인명', '체인', 
                '프랜차이즈명', '프랜차이즈', '가맹점브랜드', '가맹점 브랜드'
            ],
            'representative': [
                '대표자명', '대표자', '성명', '사업주', '대표명', '대표이사', '사장명', '대표담당자', '담당자', '등록자명',
                '신청인명', '신청인', '계약자명', '계약자', '수신자명', '수신자', '담당자명', '책임자명', '책임자',
                '법인대표', '법인 대표', '회사대표', '회사 대표', '업체대표', '업체 대표',
                '공급받는자대표', '공급받는자 대표', '공급받는자대표자', '공급받는자 대표자', '공급받는자성명', '공급받는자 성명',
                '구매자 대표', '구매자 대표자', '수취인 대표', '수취인 대표자', '고객 대표', '고객 대표자',
                '거래처 대표', '거래처 대표자', '매입자 대표', '매입자 대표자', '법인 대표', '법인 대표자',
                '업체 대표', '업체 대표자', '가맹점 대표', '가맹점 대표자', '매장 대표', '매장 대표자',
                '점포 대표', '점포 대표자', '업소 대표', '업소 대표자', '사업장 대표', '사업장 대표자'
            ],
            'address': [
                '사업장주소', '주소', '소재지', '사업장소재지', '도로명주소', '지번주소', '사업장', '주소지', '위치',
                '사업소주소', '사업소 소재지', '본사주소', '지점주소', '영업소주소', '지사주소', '분점주소',
                '공급받는자주소', '공급받는자 주소', '공급받는자소재지', '공급받는자 소재지', '공급받는자사업장주소', '공급받는자 사업장주소',
                '구매자 주소', '구매자 소재지', '수취인 주소', '수취인 소재지', '고객 주소', '고객 소재지',
                '거래처 주소', '거래처 소재지', '매입자 주소', '매입자 소재지', '법인 주소', '법인 소재지',
                '업체 주소', '업체 소재지', '가맹점 주소', '가맹점 소재지', '매장 주소', '매장 소재지',
                '점포 주소', '점포 소재지', '업소 주소', '업소 소재지', '사업장 주소', '사업장 소재지'
            ],
            'email': [
                '이메일', 'e-mail', 'email', '메일', '연락처', '사업자이메일', '사업자 이메일', '사업자메일', '사업자 메일',
                '전자우편', '대표메일', '연락처메일', 'contact', '이메일주소', '메일주소', '전자메일',
                '공급받는자이메일', '공급받는자 이메일', '공급받는자메일', '공급받는자 메일', '공급받는자 전자우편', '공급받는자 전자메일',
                '구매자 이메일', '구매자메일', '구매자 이메일주소', '구매자 메일주소', '수취인 이메일', '수취인이메일', '수취인 메일', '수취인메일', '수취인 전자우편', '수취인 전자메일',
                '받는이 이메일', '받는이이메일', '받는이 메일', '받는이메일', '받는이 전자우편', '받는이 전자메일',
                '수신자 이메일', '수신자이메일', '수신자 메일', '수신자메일', '수신자 전자우편', '수신자 전자메일',
                '고객 이메일', '고객이메일', '고객 메일', '고객메일', '고객 전자우편', '고객 전자메일',
                '거래처 이메일', '거래처이메일', '거래처 메일', '거래처메일', '거래처 전자우편', '거래처 전자메일',
                '클라이언트 이메일', '클라이언트이메일', '클라이언트 메일', '클라이언트메일', '클라이언트 전자우편', '클라이언트 전자메일',
                '파트너 이메일', '파트너이메일', '파트너 메일', '파트너메일', '파트너 전자우편', '파트너 전자메일',
                '협력사 이메일', '협력사이메일', '협력사 메일', '협력사메일', '협력사 전자우편', '협력사 전자메일',
                '매입자 이메일', '매입자이메일', '매입자 메일', '매입자메일', '매입자 전자우편', '매입자 전자메일',
                '구매처 이메일', '구매처이메일', '구매처 메일', '구매처메일', '구매처 전자우편', '구매처 전자메일',
                '납품처 이메일', '납품처이메일', '납품처 메일', '납품처메일', '납품처 전자우편', '납품처 전자메일',
                '배송지 이메일', '배송지이메일', '배송지 메일', '배송지메일', '배송지 전자우편', '배송지 전자메일',
                '도착지 이메일', '도착지이메일', '도착지 메일', '도착지메일', '도착지 전자우편', '도착지 전자메일',
                '배달지 이메일', '배달지이메일', '배달지 메일', '배달지메일', '배달지 전자우편', '배달지 전자메일',
                '수령지 이메일', '수령지이메일', '수령지 메일', '수령지메일', '수령지 전자우편', '수령지 전자메일',
                '연락처', '연락처이메일', '연락처 메일', '연락처메일', '연락처 전자우편', '연락처 전자메일',
                '대표이메일', '대표메일', '대표 전자우편', '대표 전자메일', '대표 이메일주소', '대표 메일주소',
                '담당자이메일', '담당자 메일', '담당자메일', '담당자 전자우편', '담당자 전자메일',
                '책임자이메일', '책임자 메일', '책임자메일', '책임자 전자우편', '책임자 전자메일'
            ]
        }
        
        # 🚨 금지어 시스템 (전기 연결 시스템 강화)
        forbidden_keywords_map = {
            'business_number': [
                '상호', '상호명', '가맹점명', '매장명', '업체명', '가게명', '점포명', '매장', '점포', '업체', '가게',
                '대표자명', '대표자', '성명', '사업주', '대표명', '대표이사', '사장명', '대표담당자', '담당자', '등록자명',
                '사업장주소', '주소', '소재지', '사업장소재지', '도로명주소', '지번주소', '사업장', '주소지', '위치',
                '이메일', 'e-mail', 'email', '메일', '연락처', '사업자이메일', '사업자 이메일',
                '전화번호', '전화', '폰', '휴대폰', '핸드폰', '사업자전화', '사업자 전화', '팩스번호', '팩스',
                '업태', '종목', '사업종목', '업종', '사업분야', '업무분야',
                '계좌번호', '계좌', '은행', '카드', '결제', '승인', '사업자계좌', '사업자 계좌', '사업자은행', '사업자 은행',
                '세금계산서', '발행일자', '발행일', '공급가액', '부가세', '합계금액', '비고', '메모', '비고사항',
                '코드', 'ID', '아이디', '순번', '일련번호', '고유번호', '식별번호'
            ],
            'store_name': [
                '사업자등록번호', '사업자번호', '등록번호', '사업자등록', '사업자', '등록',
                '대표자명', '대표자', '성명', '사업주', '대표명', '대표이사', '사장명', '대표담당자', '담당자', '등록자명',
                '사업장주소', '주소', '소재지', '사업장소재지', '도로명주소', '지번주소', '사업장', '주소지', '위치',
                '이메일', 'e-mail', 'email', '메일', '연락처', '사업자이메일', '사업자 이메일',
                '전화번호', '전화', '폰', '휴대폰', '핸드폰', '사업자전화', '사업자 전화', '팩스번호', '팩스',
                '업태', '종목', '사업종목', '업종', '사업분야', '업무분야',
                '계좌번호', '계좌', '은행', '카드', '결제', '승인', '사업자계좌', '사업자 계좌', '사업자은행', '사업자 은행',
                '세금계산서', '발행일자', '발행일', '공급가액', '부가세', '합계금액', '비고', '메모', '비고사항',
                '코드', 'ID', '아이디', '순번', '일련번호', '고유번호', '식별번호'
            ],
            'representative': [
                '사업자등록번호', '사업자번호', '등록번호', '사업자등록', '사업자', '등록',
                '상호', '상호명', '가맹점명', '매장명', '업체명', '가게명', '점포명', '매장', '점포', '업체', '가게',
                '사업장주소', '주소', '소재지', '사업장소재지', '도로명주소', '지번주소', '사업장', '주소지', '위치',
                '이메일', 'e-mail', 'email', '메일', '연락처', '사업자이메일', '사업자 이메일',
                '전화번호', '전화', '폰', '휴대폰', '핸드폰', '사업자전화', '사업자 전화', '팩스번호', '팩스',
                '업태', '종목', '사업종목', '업종', '사업분야', '업무분야',
                '계좌번호', '계좌', '은행', '카드', '결제', '승인', '사업자계좌', '사업자 계좌', '사업자은행', '사업자 은행',
                '세금계산서', '발행일자', '발행일', '공급가액', '부가세', '합계금액', '비고', '메모', '비고사항',
                '코드', 'ID', '아이디', '순번', '일련번호', '고유번호', '식별번호'
            ],
            'address': [
                '사업자등록번호', '사업자번호', '등록번호', '사업자등록', '사업자', '등록',
                '상호', '상호명', '가맹점명', '매장명', '업체명', '가게명', '점포명', '매장', '점포', '업체', '가게',
                '대표자명', '대표자', '성명', '사업주', '대표명', '대표이사', '사장명', '대표담당자', '담당자', '등록자명',
                '이메일', 'e-mail', 'email', '메일', '연락처', '사업자이메일', '사업자 이메일',
                '전화번호', '전화', '폰', '휴대폰', '핸드폰', '사업자전화', '사업자 전화', '팩스번호', '팩스',
                '업태', '종목', '사업종목', '업종', '사업분야', '업무분야',
                '계좌번호', '계좌', '은행', '카드', '결제', '승인', '사업자계좌', '사업자 계좌', '사업자은행', '사업자 은행',
                '세금계산서', '발행일자', '발행일', '공급가액', '부가세', '합계금액', '비고', '메모', '비고사항',
                '코드', 'ID', '아이디', '순번', '일련번호', '고유번호', '식별번호'
            ],
            'email': [
                '사업자등록번호', '사업자번호', '등록번호', '사업자등록', '사업자', '등록',
                '상호', '상호명', '가맹점명', '매장명', '업체명', '가게명', '점포명', '매장', '점포', '업체', '가게',
                '대표자명', '대표자', '성명', '사업주', '대표명', '대표이사', '사장명', '대표담당자', '담당자', '등록자명',
                '사업장주소', '주소', '소재지', '사업장소재지', '도로명주소', '지번주소', '사업장', '주소지', '위치',
                '전화번호', '전화', '폰', '휴대폰', '핸드폰', '사업자전화', '사업자 전화', '팩스번호', '팩스',
                '업태', '종목', '사업종목', '업종', '사업분야', '업무분야',
                '계좌번호', '계좌', '은행', '카드', '결제', '승인', '사업자계좌', '사업자 계좌', '사업자은행', '사업자 은행',
                '세금계산서', '발행일자', '발행일', '공급가액', '부가세', '합계금액', '비고', '메모', '비고사항',
                '코드', 'ID', '아이디', '순번', '일련번호', '고유번호', '식별번호'
            ]
        }
        
        self.logger.info(f"시트 검열 시작: 총 {len(workbook.sheetnames)}개 시트 (강화된 키워드 시스템 적용)")
        
        # 🚀 시트 우선순위 시스템: 1순위 시트 우선 검색
        priority_sheet = self._find_priority_sheet(workbook, self.required_keywords)
        if priority_sheet:
            self.logger.info(f"1순위 시트 발견! '{priority_sheet['sheet_name']}' (아빠 금액: {priority_sheet['max_dad_amount']:,.0f}원) - 즉시 선택")
            self.logger.info(f"2순위 프로세스 완전 중단 - 1순위 시트가 존재하므로 추가 검열 불필요")
            return priority_sheet
        
        # 1순위 시트가 없으면 기존 방식으로 진행 (순서 보장)
        self.logger.info("1순위 시트 없음 - 기존 방식으로 시트 검열 진행")
        
        sheet_names = sorted(workbook.sheetnames)  # 알파벳 순서로 정렬하여 결정적 순서 보장
        self.logger.info(f"🔍 시트 검열 순서: {sheet_names}")
        
        for sheet_name in sheet_names:
            try:
                sheet = workbook[sheet_name]
                
                # 🎯 총배달 금액 우선 선점: 각 시트의 총배달 금액 분석
                total_delivery_amount = self._find_max_delivery_amount(sheet)
                
                sheet_result = self._evaluate_sheet(sheet, sheet_name, self.required_keywords, forbidden_keywords_map)
                
                if sheet_result:
                    # Compute field presence for scoring
                    headers_lower = [str(h).lower() for h in sheet_result['headers']]
                    def any_in(keys: List[str]) -> bool:
                        for key in keys:
                            if any(key in h for h in headers_lower):
                                return True
                        return False

                    # Heuristic header sets for 5 core fields (확장된 키워드)
                    has_bn = any_in(['사업자', '등록번호', '공급받는자사업자', '공급받는자 사업자'])
                    has_rep = any_in(['대표자', '대표', '성명', '이름', '공급받는자대표', '공급받는자 대표', '대표담당자', '담당자', '등록자명'])
                    has_addr = any_in(['주소', '소재지', '사업장', '공급받는자주소', '공급받는자 주소'])
                    has_email = any_in(['이메일', 'email', '메일', '공급받는자이메일', '공급받는자 이메일'])
                    has_store = any_in(['가맹점', '상호', '상호명', '매장', '점포', '업체', '가게', '공급받는자상호', '공급받는자 상호', '매장명', '점포명'])

                    found5 = sum([has_bn, has_rep, has_addr, has_email, has_store])

                    # Scoring by weights
                    sheet_score_pts = (
                        (weights.get('business_number', 30) if has_bn else 0) +
                        (weights.get('representative', 10) if has_rep else 0) +
                        (weights.get('address', 30) if has_addr else 0) +
                        (weights.get('email', 20) if has_email else 0) +
                        (weights.get('store_name', 10) if has_store else 0)
                    )

                    # Attach scoring info
                    sheet_result['core_fields_found'] = found5
                    sheet_result['scoring_points'] = sheet_score_pts
                    
                    # 🎯 총배달 금액 우선 선점: 보너스 점수 추가
                    sheet_result['delivery_amount'] = total_delivery_amount
                    if total_delivery_amount > 0:
                        delivery_bonus = min(total_delivery_amount / 1000000, 50)  # 최대 50점 보너스
                        sheet_result['delivery_bonus'] = delivery_bonus
                        sheet_result['score'] += delivery_bonus
                        self.logger.info(f"시트 '{sheet_name}' 총배달 금액: {total_delivery_amount:,.0f}원 (보너스: +{delivery_bonus:.1f}점)")
                    else:
                        sheet_result['delivery_bonus'] = 0
                        self.logger.info(f"시트 '{sheet_name}' 총배달 금액: 없음 (보너스: +0점)")

                    # Log scoring details
                    self.logger.info(
                        f"시트 '{sheet_name}' 평가: 헤더매칭 {found5}/5, 점수 {sheet_result['score']:.2f}, 가중치점 {sheet_score_pts}"
                    )

                    sheet_results.append(sheet_result)
                    
                    # 최고 점수 시트 선택
                    if sheet_result['score'] > best_score:
                        best_score = sheet_result['score']
                        best_result = sheet_result
                        
            except Exception as e:
                self.logger.warning(f"시트 '{sheet_name}' 검열 실패: {str(e)}")
                continue
        
        # 🎯 총배달 금액 우선 선점: 최종 시트 선택
        if sheet_results:
            # 1순위: 총배달 금액이 가장 높은 시트 우선 선점
            delivery_sheets = [r for r in sheet_results if r.get('delivery_amount', 0) > 0]
            if delivery_sheets:
                # 총배달 금액이 가장 높은 시트 선택 (결정적 정렬)
                delivery_sheets.sort(key=lambda r: (r.get('delivery_amount', 0), r.get('sheet_name', '')), reverse=True)
                best_result = delivery_sheets[0]
                self.logger.info(f"🎯 총배달 금액 우선 선점: '{best_result['sheet_name']}' (총배달 금액: {best_result.get('delivery_amount',0):,.0f}원)")
            else:
                # 총배달 금액이 없는 경우 기존 로직 사용
                # 5/5 override
                if override_all5:
                    all5 = [r for r in sheet_results if r.get('core_fields_found', 0) >= 5]
                    if all5:
                        # If multiple: choose highest scoring_points, then total_rows desc, then lowest header_row, then sheet_name (결정적 정렬)
                        all5.sort(key=lambda r: (r.get('scoring_points', 0), r.get('total_rows', 0), -r.get('header_row', 0), r.get('sheet_name', '')), reverse=True)
                        best_result = all5[0]
                        self.logger.info(f"5/5 매칭 우선 선택: '{best_result['sheet_name']}' (가중치점 {best_result.get('scoring_points',0)})")
                    else:
                        # Use thresholds on scoring_points
                        passing = [r for r in sheet_results if r.get('scoring_points', 0) >= thresholds.get('pass', 80)]
                        if passing:
                            passing.sort(key=lambda r: (r.get('scoring_points', 0), r.get('total_rows', 0), -r.get('header_row', 0), r.get('sheet_name', '')), reverse=True)
                            best_result = passing[0]
                        else:
                            candidates = [r for r in sheet_results if r.get('scoring_points', 0) >= thresholds.get('candidate', 70)]
                            if candidates:
                                candidates.sort(key=lambda r: (r.get('scoring_points', 0), r.get('total_rows', 0), -r.get('header_row', 0), r.get('sheet_name', '')), reverse=True)
                                best_result = candidates[0]
                            else:
                                # fallback to highest original score (결정적 정렬)
                                sheet_results.sort(key=lambda r: (r.get('score', 0), r.get('sheet_name', '')), reverse=True)
                                best_result = sheet_results[0]
                else:
                    # fallback to highest original score (결정적 정렬)
                    sheet_results.sort(key=lambda r: (r.get('score', 0), r.get('sheet_name', '')), reverse=True)
                    best_result = sheet_results[0]

        if best_result:
            self.logger.info(f"최적 시트 선택: '{best_result['sheet_name']}' (원점수: {best_result.get('score',0):.2f}, 가중치점: {best_result.get('scoring_points',0)})")
        else:
            self.logger.warning("적합한 시트를 찾지 못했습니다.")
            
        return best_result
    
    def _find_priority_sheet(self, workbook, required_keywords: Dict) -> Optional[Dict[str, Any]]:
        """
        🚀 1순위 시트 Fast-Path 로직 (절대지침 준수)
        
        절대지침에 따라 1순위 시트를 찾아 즉시 반환하여 성능을 최적화합니다.
        
        Args:
            workbook: openpyxl Workbook 객체
            required_keywords: 필수 컬럼 키워드 딕셔너리
            
        Returns:
            Dict: 1순위 시트 정보 또는 None
        """
        self.logger.info("🚀 1순위 시트 Fast-Path 검색 시작")
        
        # 금지어 시스템 초기화
        forbidden_keywords_map = {
            'business_number': [
                '상호', '상호명', '가맹점명', '매장명', '업체명', '가게명', '점포명', '매장', '점포', '업체', '가게',
                '대표자명', '대표자', '성명', '사업주', '대표명', '대표이사', '사장명', '대표담당자', '담당자', '등록자명',
                '사업장주소', '주소', '소재지', '사업장소재지', '도로명주소', '지번주소', '사업장', '주소지', '위치',
                '이메일', 'e-mail', 'email', '메일', '연락처', '사업자이메일', '사업자 이메일',
                '전화번호', '전화', '폰', '휴대폰', '핸드폰', '사업자전화', '사업자 전화', '팩스번호', '팩스',
                '업태', '종목', '사업종목', '업종', '사업분야', '업무분야',
                '계좌번호', '계좌', '은행', '카드', '결제', '승인', '사업자계좌', '사업자 계좌', '사업자은행', '사업자 은행',
                '세금계산서', '발행일자', '발행일', '공급가액', '부가세', '합계금액', '비고', '메모', '비고사항',
                '코드', 'ID', '아이디', '순번', '일련번호', '고유번호', '식별번호'
            ],
            'store_name': [
                '사업자등록번호', '사업자번호', '등록번호', '사업자등록', '사업자', '등록',
                '대표자명', '대표자', '성명', '사업주', '대표명', '대표이사', '사장명', '대표담당자', '담당자', '등록자명',
                '사업장주소', '주소', '소재지', '사업장소재지', '도로명주소', '지번주소', '사업장', '주소지', '위치',
                '이메일', 'e-mail', 'email', '메일', '연락처', '사업자이메일', '사업자 이메일',
                '전화번호', '전화', '폰', '휴대폰', '핸드폰', '사업자전화', '사업자 전화', '팩스번호', '팩스',
                '업태', '종목', '사업종목', '업종', '사업분야', '업무분야',
                '계좌번호', '계좌', '은행', '카드', '결제', '승인', '사업자계좌', '사업자 계좌', '사업자은행', '사업자 은행',
                '세금계산서', '발행일자', '발행일', '공급가액', '부가세', '합계금액', '비고', '메모', '비고사항',
                '코드', 'ID', '아이디', '순번', '일련번호', '고유번호', '식별번호'
            ],
            'representative': [
                '사업자등록번호', '사업자번호', '등록번호', '사업자등록', '사업자', '등록',
                '상호', '상호명', '가맹점명', '매장명', '업체명', '가게명', '점포명', '매장', '점포', '업체', '가게',
                '사업장주소', '주소', '소재지', '사업장소재지', '도로명주소', '지번주소', '사업장', '주소지', '위치',
                '이메일', 'e-mail', 'email', '메일', '연락처', '사업자이메일', '사업자 이메일',
                '전화번호', '전화', '폰', '휴대폰', '핸드폰', '사업자전화', '사업자 전화', '팩스번호', '팩스',
                '업태', '종목', '사업종목', '업종', '사업분야', '업무분야',
                '계좌번호', '계좌', '은행', '카드', '결제', '승인', '사업자계좌', '사업자 계좌', '사업자은행', '사업자 은행',
                '세금계산서', '발행일자', '발행일', '공급가액', '부가세', '합계금액', '비고', '메모', '비고사항',
                '코드', 'ID', '아이디', '순번', '일련번호', '고유번호', '식별번호'
            ],
            'address': [
                '사업자등록번호', '사업자번호', '등록번호', '사업자등록', '사업자', '등록',
                '상호', '상호명', '가맹점명', '매장명', '업체명', '가게명', '점포명', '매장', '점포', '업체', '가게',
                '대표자명', '대표자', '성명', '사업주', '대표명', '대표이사', '사장명', '대표담당자', '담당자', '등록자명',
                '이메일', 'e-mail', 'email', '메일', '연락처', '사업자이메일', '사업자 이메일',
                '전화번호', '전화', '폰', '휴대폰', '핸드폰', '사업자전화', '사업자 전화', '팩스번호', '팩스',
                '업태', '종목', '사업종목', '업종', '사업분야', '업무분야',
                '계좌번호', '계좌', '은행', '카드', '결제', '승인', '사업자계좌', '사업자 계좌', '사업자은행', '사업자 은행',
                '세금계산서', '발행일자', '발행일', '공급가액', '부가세', '합계금액', '비고', '메모', '비고사항',
                '코드', 'ID', '아이디', '순번', '일련번호', '고유번호', '식별번호'
            ],
            'email': [
                '사업자등록번호', '사업자번호', '등록번호', '사업자등록', '사업자', '등록',
                '상호', '상호명', '가맹점명', '매장명', '업체명', '가게명', '점포명', '매장', '점포', '업체', '가게',
                '대표자명', '대표자', '성명', '사업주', '대표명', '대표이사', '사장명', '대표담당자', '담당자', '등록자명',
                '사업장주소', '주소', '소재지', '사업장소재지', '도로명주소', '지번주소', '사업장', '주소지', '위치',
                '전화번호', '전화', '폰', '휴대폰', '핸드폰', '사업자전화', '사업자 전화', '팩스번호', '팩스',
                '업태', '종목', '사업종목', '업종', '사업분야', '업무분야',
                '계좌번호', '계좌', '은행', '카드', '결제', '승인', '사업자계좌', '사업자 계좌', '사업자은행', '사업자 은행',
                '세금계산서', '발행일자', '발행일', '공급가액', '부가세', '합계금액', '비고', '메모', '비고사항',
                '코드', 'ID', '아이디', '순번', '일련번호', '고유번호', '식별번호'
            ]
        }
        
        best_sheet = None
        max_dad_amount = 0
        
        # 모든 시트를 순회하며 1순위 시트 찾기 (순서 보장)
        sheet_names = sorted(workbook.sheetnames)  # 알파벳 순서로 정렬하여 결정적 순서 보장
        self.logger.info(f"🔍 시트 검색 순서: {sheet_names}")
        
        for sheet_name in sheet_names:
            try:
                sheet = workbook[sheet_name]
                self.logger.debug(f"🔍 1순위 시트 검색: '{sheet_name}' 검토 중...")
                
                # 시트 평가
                sheet_result = self._evaluate_sheet(sheet, sheet_name, self.required_keywords, forbidden_keywords_map)
                
                if not sheet_result:
                    self.logger.debug(f"❌ '{sheet_name}': 시트 평가 실패")
                    continue
            
                # 1순위 시트 조건 확인
                matched_fields = sheet_result.get('matched_fields', 0)
                families = sheet_result.get('families', [])
                
                # 🎯 1순위 시트 판별 기준 (절대지침)
                # 1. 5형제 가족 존재: 사업자번호, 대표자명, 주소, 이메일, 가맹점명 모두 존재
                # 2. 데이터 품질: 유효한 숫자 데이터 존재
                # 3. 업종별 특화 조건: 아빠값과 엄마값이 같은 행에 존재
                
                if matched_fields >= 5 and families:
                    # 아빠값과 엄마값이 같은 행에 있는 최대값 찾기
                    max_dad_with_mom = self._get_max_dad_with_mom_same_row(sheet_result)
                    
                    # 동일한 max_dad_amount일 때는 시트 이름 순서로 결정 (결정적 선택)
                    if max_dad_with_mom > max_dad_amount or (max_dad_with_mom == max_dad_amount and (best_sheet is None or sheet_name < best_sheet['sheet_name'])):
                        max_dad_amount = max_dad_with_mom
                        best_sheet = sheet_result
                        best_sheet['max_dad_amount'] = max_dad_amount
                        best_sheet['priority'] = '1순위'
                        
                        self.logger.info(f"🎯 1순위 시트 후보 발견: '{sheet_name}' (아빠값: {max_dad_amount:,.0f}원)")
            
            except Exception as e:
                self.logger.warning(f"시트 '{sheet_name}' 1순위 검색 중 오류: {str(e)}")
                continue
            
        if best_sheet:
            self.logger.info(f"🏆 1순위 시트 최종 선택: '{best_sheet['sheet_name']}' (아빠값: {max_dad_amount:,.0f}원)")
            return best_sheet
        else:
            self.logger.info("❌ 1순위 시트를 찾지 못했습니다.")
            return None
    
    def _get_max_dad_with_mom_same_row(self, sheet_result: Dict[str, Any]) -> float:
        """
        아빠값과 엄마값이 같은 행에 있는 최대 아빠값 찾기
        
        Args:
            sheet_result: 시트 평가 결과
            
        Returns:
            float: 최대 아빠값 (엄마값과 같은 행에 있는 경우만)
        """
        try:
            families = sheet_result.get('families', [])
            if not families:
                return 0.0
            
            max_dad_amount = 0.0
            
            for family in families:
                dad_amount = self._to_number(family.get('공급가액', 0))
                mom_amount = self._to_number(family.get('부가세', 0))
                
                # 아빠값과 엄마값이 모두 존재하고 0보다 큰 경우만 고려
                if dad_amount > 0 and mom_amount > 0:
                    if dad_amount > max_dad_amount:
                        max_dad_amount = dad_amount
                        
            self.logger.debug(f"🔍 같은 행 아빠값 최대값: {max_dad_amount:,.0f}원")
            return max_dad_amount
        except Exception as e:
            self.logger.warning(f"같은 행 아빠값 최대값 계산 중 오류: {str(e)}")
            return 0.0
    
    def _find_max_delivery_amount(self, sheet) -> float:
        """총배달 금액 컬럼에서 최대값 찾기 (총배달 금액 우선 선점)"""
        max_amount = 0
        
        # 총배달 금액 관련 키워드
        delivery_keywords = ['총배달', '배달금액', '총금액', '합계', '총합', '배달요금', '총배달요금', '총배달금액']
        
        try:
            for row in sheet.iter_rows():
                for cell in row:
                    if cell.value is None:
                        continue
                    
                    cell_value = str(cell.value).lower().strip()
                    
                    # 헤더에서 총배달 금액 컬럼 찾기
                    if any(keyword in cell_value for keyword in delivery_keywords):
                        col_idx = cell.column
                        
                        # 해당 컬럼의 모든 숫자 값 중 최대값 찾기
                        for data_row in sheet.iter_rows(min_row=cell.row+1, min_col=col_idx, max_col=col_idx):
                            for data_cell in data_row:
                                if data_cell.value is None:
                                    continue
                
                                if isinstance(data_cell.value, (int, float)) and data_cell.value > max_amount:
                                    max_amount = data_cell.value
                        
                        break
        except Exception as e:
            self.logger.warning(f"총배달 금액 분석 중 오류: {str(e)}")
        
        return max_amount
    
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
            actual_max_row, actual_max_col = self._find_actual_data_range(sheet)
            
            # 데이터 행에서 가족 정보 추출 (실제 데이터 범위 내에서)
            raw_families = []
            # 전체 실제 데이터 범위를 사용 (지침: 마지막 행까지 검열)
            max_rows = actual_max_row
            
            for row_num in range(header_row + 1, max_rows + 1):
                family_data = self._extract_family_from_row(sheet, row_num, column_mapping, actual_max_col)
                if family_data and self._is_valid_family(family_data):
                    raw_families.append(family_data)
            
            # 가족 통합 로직 적용
            families = self._merge_family_data(raw_families)
                    
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
        representative_keywords = ['대표자', '대표자명', '대표', '성명', '이름', '등록자', '등록자명']
        for col_num in range(1, sheet.max_column + 1):
            cell_value = str(sheet.cell(header_row, col_num).value).strip().lower()
            if any(keyword in cell_value for keyword in representative_keywords):
                column_mapping['representative'] = col_num
                break
        
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
    
    def _extract_family_from_row(self, sheet, row_num: int, column_mapping: Dict, actual_max_col: int) -> Optional[Dict]:
        """행에서 가족 정보 추출 (5형제 정보 포함)"""
        try:
            family_data = {}
            
            # 아빠 금액 추출
            if 'dad_amount' in column_mapping:
                dad_cell = sheet.cell(row_num, column_mapping['dad_amount'])
                dad_value = dad_cell.value
                dad_number = self._to_number(dad_value)
                if dad_number is not None and dad_number > 0:
                    family_data['dad_amount'] = dad_number
            
            # 엄마 금액 추출
            if 'mom_amount' in column_mapping:
                mom_cell = sheet.cell(row_num, column_mapping['mom_amount'])
                mom_value = mom_cell.value
                mom_number = self._to_number(mom_value)
                if mom_number is not None and mom_number > 0:
                    family_data['mom_amount'] = mom_number
            
            # 5형제 정보 추출 (컬럼 매핑 기반)
            # 1. 사업자번호 추출
            if 'business_number' in column_mapping:
                business_cell = sheet.cell(row_num, column_mapping['business_number'])
                business_value = str(business_cell.value).strip()
                if business_value and business_value != 'None' and self._is_business_number(business_value):
                    family_data['business_number'] = business_value
            
            # 2. 상호명 추출
            if 'store_name' in column_mapping:
                store_cell = sheet.cell(row_num, column_mapping['store_name'])
                store_value = str(store_cell.value).strip()
                if store_value and store_value != 'None' and len(store_value) > 1:
                    family_data['store_name'] = store_value
            
            # 3. 대표자명 추출
            if 'representative' in column_mapping:
                rep_cell = sheet.cell(row_num, column_mapping['representative'])
                rep_value = str(rep_cell.value).strip()
                if rep_value and rep_value != 'None' and self._is_representative_name(rep_value):
                    family_data['representative'] = rep_value
            
            # 4. 주소 추출
            if 'address' in column_mapping:
                addr_cell = sheet.cell(row_num, column_mapping['address'])
                addr_value = str(addr_cell.value).strip()
                if addr_value and addr_value != 'None' and self._is_address(addr_value):
                    family_data['address'] = addr_value
            
            # 5. 이메일 추출
            if 'email' in column_mapping:
                email_cell = sheet.cell(row_num, column_mapping['email'])
                email_value = str(email_cell.value).strip()
                if email_value and email_value != 'None' and '@' in email_value and '.' in email_value:
                    family_data['email'] = email_value
            
            return family_data if family_data else None
            
        except Exception as e:
            return None
    
    def _is_business_number(self, value: str) -> bool:
        """사업자번호 패턴 확인"""
        # 숫자 10자리 또는 하이픈 포함
        import re
        pattern = r'^\d{3}-?\d{2}-?\d{5}$|^\d{10}$'
        return bool(re.match(pattern, value))
    
    def _is_representative_name(self, value: str) -> bool:
        """대표자명 패턴 확인 (한글 이름)"""
        import re
        # 한글 2-4자 이름 패턴
        pattern = r'^[가-힣]{2,4}$'
        return bool(re.match(pattern, value)) and not value.isdigit()
    
    def _is_address(self, value: str) -> bool:
        """주소 패턴 확인"""
        address_keywords = ['시', '구', '동', '로', '길', '번지', '아파트', '빌딩']
        return any(keyword in value for keyword in address_keywords) and len(value) > 5
    
    def _is_store_name(self, value: str) -> bool:
        """가맹점명 패턴 확인"""
        store_keywords = ['점', '식당', '카페', '마트', '상점', '센터', '플라자']
        return any(keyword in value for keyword in store_keywords) and len(value) > 2
    
    def _is_valid_family(self, family_data: Dict) -> bool:
        """유효한 가족 정보인지 검증"""
        # 아빠 금액이 있어야 유효한 가족
        return family_data.get('dad_amount', 0) > 0
    
    def _merge_family_data(self, families: List[Dict]) -> List[Dict]:
        """
        가족 통합 로직: 중복 가족 정보를 하나로 통합
        
        Args:
            families: 가족 정보 리스트
            
        Returns:
            List[Dict]: 통합된 가족 정보 리스트
        """
        if not families:
            return []
        
        self.logger.info(f"가족 통합 시작: {len(families)}개 가족 정보")
        
        # 가족별로 그룹화 (사업자번호, 대표자명 기준)
        family_groups = {}
        
        for family in families:
            # 가족 식별 키 생성 (사업자번호만 사용 - 핵심 수정!)
            business_number = family.get('business_number', '')
            family_key = business_number.strip()
            
            if not family_key:
                # 사업자번호가 없으면 대표자명으로 구분
                representative = family.get('representative', '')
                family_key = f"rep_{representative}".strip()
            
            if not family_key or family_key == 'rep_':
                # 식별 정보가 없으면 아빠 금액으로만 구분
                family_key = f"amount_{family.get('dad_amount', 0)}"
            
            if family_key not in family_groups:
                family_groups[family_key] = []
            
            family_groups[family_key].append(family)
        
        # 각 그룹을 통합
        merged_families = []
        
        for family_key, group in family_groups.items():
            if len(group) == 1:
                # 단일 가족은 그대로 유지
                merged_families.append(group[0])
                self.logger.info(f"단일 가족 유지: {family_key}")
            else:
                # 중복 가족 통합
                merged_family = self._integrate_family_group(group)
                merged_families.append(merged_family)
                self.logger.info(f"가족 통합 완료: {family_key} ({len(group)}개 → 1개)")
        
        self.logger.info(f"가족 통합 완료: {len(families)}개 → {len(merged_families)}개")
        return merged_families
    
    def _integrate_family_group(self, family_group: List[Dict]) -> Dict:
        """
        가족 그룹을 하나로 통합
        
        Args:
            family_group: 같은 가족의 여러 정보
            
        Returns:
            Dict: 통합된 가족 정보
        """
        integrated = {
            'dad_amount': 0,
            'mom_amount': 0,
            'business_number': '',
            'representative': '',
            'address': '',
            'email': '',
            'store_name': '',
            'integration_count': len(family_group)
        }
        
        # 각 필드에서 가장 좋은 값 선택 또는 합산
        for family in family_group:
            # 아빠 금액 합산
            dad_amount = family.get('dad_amount', 0)
            if isinstance(dad_amount, (int, float)):
                integrated['dad_amount'] += dad_amount
            
            # 엄마 금액 합산
            mom_amount = family.get('mom_amount', 0)
            if isinstance(mom_amount, (int, float)):
                integrated['mom_amount'] += mom_amount
            
            # 텍스트 필드는 가장 긴 값 선택 (더 완전한 정보)
            for field in ['business_number', 'representative', 'address', 'email', 'store_name']:
                current_value = family.get(field, '')
                if isinstance(current_value, str) and len(current_value) > len(integrated[field]):
                    integrated[field] = current_value
        
        # 통합 정보 로깅
        self.logger.info(f"  통합 결과: 아빠 {integrated['dad_amount']:,.0f}원, 엄마 {integrated['mom_amount']:,.0f}원")
        
        return integrated
    
    def _evaluate_sheet(self, sheet, sheet_name: str, required_keywords: Dict, forbidden_keywords_map: Dict = None) -> Optional[Dict[str, Any]]:
        """
        개별 시트 평가 - 지능앱 기술 적용
        5가지 필수 컬럼 매칭과 데이터 품질을 종합적으로 평가
        
        Args:
            sheet: openpyxl Worksheet 객체
            sheet_name: 시트 이름
            required_keywords: 필수 컬럼 키워드 딕셔너리
            
        Returns:
            Dict: 시트 평가 결과 또는 None
        """
        try:
            # 실제 데이터 범위 감지: 각 시트의 실제 마지막 행/열 찾기
            actual_max_row, actual_max_col = self._find_actual_data_range(sheet)
            
            # 지침 반영: 행은 실제 마지막 행까지 사용, 열은 안전 상한 유지(50)
            max_row = actual_max_row
            max_col = min(actual_max_col, 50)
            
            if max_row < 2 or max_col < 5:
                return None
            
            # 지능앱 기술: 헤더 행 후보 검색 (상단 30행까지 확장)
            header_candidates = []
            
            # 지능앱 기술: 스캔 범위 확장 (복잡한 파일 대응)
            scan_rows = min(1000, max_row)  # 최대 1000행까지 스캔 (장문 제목/설명 대응)
            
            for row in range(1, scan_rows + 1):
                # 해당 행의 데이터 밀도 계산
                data_density = self._calculate_data_density(sheet, row, max_col)
                
                # 지능앱 기술: 5가지 필수 컬럼 정밀 매칭 + 전기 연결 시스템
                matched_fields = self._count_matched_fields(sheet, row, max_col, required_keywords, forbidden_keywords_map)
                
                # 지능앱 기술: 헤더 점수 계산 (매칭 필드 비중 증가)
                field_match_score = (matched_fields / 5) * 0.8  # 80% 가중치
                density_score = data_density * 0.2  # 20% 가중치
                header_score = field_match_score + density_score
                
                # 지능앱 기술: 최소 3개 필드 매칭 + 추가 검증
                if matched_fields >= 3:
                    # 추가 검증: 빈 행 제외
                    non_empty_cells = 0
                    for col in range(1, max_col + 1):
                        cell_value = sheet.cell(row=row, column=col).value
                        if cell_value is not None and str(cell_value).strip():
                            non_empty_cells += 1
                    
                    # 최소 5개 이상의 비어있지 않은 셀이 있어야 헤더로 인정
                    if non_empty_cells >= 5:
                        header_candidates.append({
                            'row': row,
                            'data_density': data_density,
                            'matched_fields': matched_fields,
                            'header_score': header_score,
                            'non_empty_cells': non_empty_cells
                        })
                        self.logger.debug(f"지능앱 헤더 후보: 행 {row}, 점수 {header_score:.3f}, 매칭 {matched_fields}개, 비어있지 않은 셀 {non_empty_cells}개")
            
            if not header_candidates:
                self.logger.warning(f"지능앱 헤더 감지: 시트 '{sheet_name}'에서 적합한 헤더를 찾지 못했습니다.")
                return None
            
            # 지능앱 기술: 최적 헤더 행 선택 (다중 기준, 결정적 정렬)
            # 1순위: 매칭된 필드 수가 가장 많은 것
            # 2순위: 헤더 점수가 가장 높은 것
            # 3순위: 가장 아래쪽 행 (나중에 나온 헤더 우선)
            # 4순위: 행 번호 (동일 조건일 때 결정적 선택)
            
            header_candidates.sort(key=lambda x: (
                x['matched_fields'],  # 매칭된 필드 수 (최우선)
                x['header_score'],    # 헤더 점수
                -x['row'],           # 행 번호 (낮은 번호가 우선, 음수로 변환하여 높은 값이 우선되도록)
                x['row']             # 행 번호 (동일 조건일 때 결정적 선택)
            ), reverse=True)
            
            best_header = header_candidates[0]
            
            header_row = best_header['row']
            self.logger.info(f"지능앱 헤더 감지: 시트 '{sheet_name}'에서 최적 헤더 선택 - 행 {header_row} (점수: {best_header['header_score']:.3f}, 매칭: {best_header['matched_fields']}개)")
            
            # 데이터 추출
            headers = []
            data = []
            
            # 헤더 추출
            for col in range(1, max_col + 1):
                cell_value = sheet.cell(row=header_row, column=col).value
                headers.append(str(cell_value) if cell_value is not None else f"Column_{col}")
            
            # 데이터 추출 (헤더 행 + 1부터)
            data_start_row = header_row + 1
            for row in range(data_start_row, max_row + 1):
                row_data = []
                for col in range(1, max_col + 1):
                    cell_value = sheet.cell(row=row, column=col).value
                    row_data.append(cell_value)
                data.append(row_data)
            
            # 데이터 품질 평가
            data_quality_score = self._evaluate_data_quality(data, headers)
            
            # 최종 점수 계산
            final_score = best_header['header_score'] * 0.7 + data_quality_score * 0.3
            
            # 가족 데이터 생성 및 반환 (핵심 수정!)
            families = self._find_families_in_sheet(sheet, self.required_keywords)
            
            return {
                'sheet_name': sheet_name,
                'header_row': header_row,
                'data_start_row': data_start_row,
                'headers': headers,
                'data': data,
                'score': final_score,
                'matched_fields': best_header['matched_fields'],
                'data_quality': data_quality_score,
                'total_rows': len(data),
                'actual_max_row': actual_max_row,
                'actual_max_col': actual_max_col,
                'families': families  # 가족 데이터 추가
            }
            
        except Exception as e:
            self.logger.error(f"시트 '{sheet_name}' 평가 오류: {str(e)}")
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
        
        Args:
            data: 데이터 행 리스트
            headers: 헤더 리스트
            
        Returns:
            float: 데이터 품질 점수 (0.0 ~ 1.0)
        """
        if not data or not headers:
            return 0.0
        
        total_cells = len(data) * len(headers)
        if total_cells == 0:
            return 0.0
        
        # 빈 셀 개수 계산
        empty_cells = 0
        for row in data:
            for cell in row:
                if cell is None or str(cell).strip() == "":
                    empty_cells += 1
        
        # 데이터 완성도 점수
        completeness_score = 1.0 - (empty_cells / total_cells)
        
        # 데이터 일관성 점수 (행별 데이터 분포)
        consistency_score = 0.0
        if len(data) > 1:
            row_lengths = [len([cell for cell in row if cell is not None and str(cell).strip()]) for row in data]
            if row_lengths:
                avg_length = sum(row_lengths) / len(row_lengths)
                variance = sum((length - avg_length) ** 2 for length in row_lengths) / len(row_lengths)
                consistency_score = max(0.0, 1.0 - (variance / (avg_length + 1)))
        
        # 최종 품질 점수
        quality_score = completeness_score * 0.7 + consistency_score * 0.3
        
        return min(1.0, max(0.0, quality_score))

    def _inspect_all_sheets_fast(self, workbook: openpyxl.Workbook) -> Optional[Dict]:
        """최적화된 시트 검열 - 속도 우선"""
        try:
            sheet_results = []
            self.logger.info(f"시트 검열 시작: 총 {len(workbook.sheetnames)}개 시트")
            
            # 먼저 헤더만 빠르게 스캔하여 후보 시트 선택
            header_candidates = []
            for sheet_name in workbook.sheetnames:
                if sheet_name.startswith('_xl') or sheet_name == 'Sheet1':  # 시스템 시트 스킵
                    continue
                    
                sheet = workbook[sheet_name]
                
                # 첫 5행만 스캔하여 헤더 후보 찾기
                header_candidate = self._quick_header_scan(sheet, max_rows=5)
                if header_candidate:
                    header_candidates.append({
                        'sheet_name': sheet_name,
                        'sheet': sheet,
                        'header_info': header_candidate
                    })
            
            # 헤더가 좋은 시트 우선으로 상세 평가
            from .industry_config_loader import industry_config_loader
            config = industry_config_loader.get_config('delivery')
            
            for candidate in sorted(header_candidates, 
                                 key=lambda x: x['header_info']['match_count'], 
                                 reverse=True)[:3]:  # 상위 3개만 평가
                result = self._evaluate_sheet_fast(candidate['sheet'], 
                                                 candidate['sheet_name'],
                                                 candidate['header_info'], 
                                                 config)
                if result:
                    sheet_results.append(result)
            
            # 최고 점수 결과 반환 (결정적 정렬)
            if sheet_results:
                sheet_results.sort(key=lambda x: (x['weighted_score'], x.get('sheet_name', '')), reverse=True)
                best_result = sheet_results[0]
                self.logger.info(f"최적 시트 선택: '{best_result['sheet_name']}' (원점수: {best_result['original_score']:.2f}, 가중치점: {best_result['weighted_score']})")
                return best_result
            
            # 기존 방식으로 폴백
            return self._inspect_all_sheets(workbook)
            
        except Exception as e:
            self.logger.error(f"빠른 시트 검열 오류: {str(e)}")
            return self._inspect_all_sheets(workbook)
    
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
            # 속도 최적화: 필요한 데이터만 읽기 (공식 계산된 값 우선)
            workbook = openpyxl.load_workbook(file_path, data_only=True)
            
            # 지능형 시트 검열 (지능앱 핵심 기술)
            best_sheet_result = self._inspect_all_sheets(workbook)
            
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
            header_row = self._detect_csv_header_row(df)
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
        """
        데이터 섹션 자동 감지 - 이미 파싱된 DataFrame 사용
        배달대행사 정산서의 특성을 고려한 섹션 분석
        """
        sections = {
            'header_section': None,      # 헤더 정보
            'data_section': None,       # 실제 데이터 (전체)
            'summary_section': None,    # 요약 정보
            'total_rows': len(df)
        }
        
        try:
            # 이미 FileParser에서 헤더 행을 감지하고 데이터를 추출했으므로
            # 전체 DataFrame이 실제 데이터임
            sections['data_section'] = df.to_dict('records')
            
            # 요약 섹션 감지 (하위 3행)
            if len(df) > 3:
                summary_candidates = df.tail(3)
                sections['summary_section'] = summary_candidates.to_dict('records')
            
            self.logger.info(f"데이터 섹션 분석 완료: 총 {len(df)}행")
            
            return sections
            
        except Exception as e:
            self.logger.error(f"데이터 섹션 분석 오류: {str(e)}")
            return sections
    
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
        """
        파싱된 데이터 미리보기
        
        Args:
            parsed_data: parse_file() 결과
            max_rows: 미리보기 행 수
            
        Returns:
            Dict: 미리보기 데이터
        """
        if parsed_data['parsing_status'] != 'success':
            return {'error': '파싱 실패'}
        
        try:
            df = parsed_data['raw_data']
            preview = df.head(max_rows)
            
            return {
                'headers': list(df.columns),
                'preview_data': preview.to_dict('records'),
                'total_rows': len(df),
                'file_type': parsed_data['file_type']
            }
            
        except Exception as e:
            self.logger.error(f"데이터 미리보기 오류: {str(e)}")
            return {'error': f'미리보기 생성 오류: {str(e)}'}
    
    def extract_text_content(self, parsed_data: Dict[str, Any]) -> str:
        """
        파싱된 데이터에서 텍스트 내용 추출
        키워드 매칭을 위한 텍스트 추출
        """
        if parsed_data['parsing_status'] != 'success':
            return ""
        
        try:
            df = parsed_data['raw_data']
            text_content = []
            
            # 모든 셀의 텍스트 추출
            for _, row in df.iterrows():
                for value in row.values:
                    if pd.notna(value) and str(value).strip():
                        text_content.append(str(value).strip())
            
            return " ".join(text_content)
            
        except Exception as e:
            self.logger.error(f"텍스트 추출 오류: {str(e)}")
            return ""

    def _merge_families_by_business_number(self, families: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        🎯 사업자번호 기반 가족 통합 서브지침
        
        Args:
            families: 추출된 가족 데이터 리스트
            
        Returns:
            List[Dict]: 통합된 가족 데이터 리스트
        """
        if not families:
            return []
        
        merged_families = {}
        
        # [AGG-START] 고정 태그
        self.logger.info(f"[AGG-START] 가족 통합 시작: 총 {len(families)}건")
        
        def _to_number(value):
            try:
                if value is None:
                    return 0.0
                if isinstance(value, (int, float)):
                    return float(value)
                s = str(value).strip().replace(',', '')
                return float(s) if s not in ['', 'None', 'nan'] else 0.0
            except Exception:
                return 0.0

        # 합계/소계/총계/집계 키워드 (요약행 제외)
        summary_keywords = ("합계", "소계", "총계", "집계")

        # 블록 개념이 상위 단계에서 처리되지 않은 경우에도 추적 가능하도록 기본 블록 로그
        self.logger.info("[AGG-BLOCK] default-block 시작")

        for family in families:
            # 사업자번호 정규화: 숫자만 10자리로 맞춤 (공백/하이픈/지수표기 제거)
            raw_biz = family.get('사업자등록번호', '')
            try:
                import re
                digits = re.sub(r'[^0-9]', '', str(raw_biz))
                if len(digits) > 10:
                    # 뒤쪽 10자리 우선 (앞쪽에 0이 포함되거나 서식 흔적 방지)
                    digits = digits[-10:]
                business_number = digits
            except Exception:
                business_number = str(raw_biz).strip()
            self.logger.info(f"처리 중인 가족: 사업자번호={business_number}, 상호={family.get('상호', '')}, 공급가액={family.get('공급가액', 0)}, 부가세={family.get('부가세', 0)}")

            # 요약/합계 행 제외 로직
            try:
                text_fields = [
                    str(family.get('상호', '')),
                    str(family.get('store_name', '')),
                    str(family.get('비고', '')),
                    str(family.get('메모', '')),
                ]
                if any(any(k in t for k in summary_keywords) for t in text_fields if t and t != 'None'):
                    self.logger.info(f"[SKIP-SUMROW] 요약/합계 행 제외: 사업자번호={business_number}, 상호={family.get('상호', '')}")
                    continue
            except Exception:
                pass
            
            if not business_number:
                # 사업자번호가 없으면 그대로 추가
                merged_families[f"no_business_number_{len(merged_families)}"] = family.copy()
                continue
            
            # 부가세 0은 집계 제외 (합산은 사후 템플릿 레이어에서만 사용)
            new_supply = self._to_number(family.get('공급가액', 0))
            new_vat = self._to_number(family.get('부가세', 0))
            if new_vat <= 0:
                self.logger.info(f"[SKIP-VAT0] 부가세 0 행 제외: 사업자번호={business_number}, 공급가액={new_supply}, 부가세={new_vat}")
                continue

            if business_number in merged_families:
                # 기존 가족과 통합
                existing = merged_families[business_number]
                
                # 금액 합산 (아빠 + 엄마) - 문자열/콤마 포함값 정규화 후 합산
                old_supply = self._to_number(existing.get('공급가액', 0))
                old_vat = self._to_number(existing.get('부가세', 0))
                
                existing['공급가액'] = old_supply + new_supply
                existing['부가세'] = old_vat + new_vat
                existing['요금합계'] = existing['공급가액'] + existing['부가세']
                
                self.logger.info(f"[AGG-SUM] {business_number} 기존({old_supply}+{old_vat}) + 새({new_supply}+{new_vat}) = 합계({existing['공급가액']}+{existing['부가세']})")
                
                # 텍스트 필드는 가장 완전한 것 선택
                if len(family.get('상호', '')) > len(existing.get('상호', '')):
                    existing['상호'] = family.get('상호', '')
                if len(family.get('대표자명', '')) > len(existing.get('대표자명', '')):
                    existing['대표자명'] = family.get('대표자명', '')
                if len(family.get('사업장주소', '')) > len(existing.get('사업장주소', '')):
                    existing['사업장주소'] = family.get('사업장주소', '')
                if len(family.get('사업자이메일', '')) > len(existing.get('사업자이메일', '')):
                    existing['사업자이메일'] = family.get('사업자이메일', '')
                
                self.logger.info(f"가족 통합: {business_number} - 상호: {existing['상호']}, 금액: {existing['요금합계']}")
            else:
                # 새로운 가족 추가
                # 최초 입력도 숫자 정규화 적용
                nf = family.copy()
                nf['공급가액'] = self._to_number(nf.get('공급가액', 0))
                nf['부가세'] = self._to_number(nf.get('부가세', 0))
                nf['요금합계'] = nf['공급가액'] + nf['부가세']
                merged_families[business_number] = nf
        
        result = list(merged_families.values())
        
        # 아빠 값 계산 서브지침 적용
        result = self._apply_dad_fallback_logic(result)
        
        # 최종 합계 로그 (사업자번호별)
        try:
            for r in result:
                biz = r.get('사업자등록번호', '')
                self.logger.info(f"통합 결과: {biz} 공급가액={r.get('공급가액', 0)}, 부가세={r.get('부가세', 0)}, 요금합계={r.get('요금합계', 0)}")
        except Exception:
            pass

        # [AGG-END] 고정 태그
        self.logger.info(f"[AGG-END] 사업자번호 기반 가족 통합 완료: {len(families)} → {len(result)}건")
        
        return result
    
    def _apply_dad_fallback_logic(self, families: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        아빠 값 찾기 힘들 때 엄마 값을 기준으로 아빠 값을 계산하는 서브지침
        
        대한민국 부가세법에 따른 절대 규칙:
        - 부가세는 공급가액의 10%
        - 엄마(부가세)가 100이면 → 아빠(공급가액)는 1000
        - 엄마(부가세)가 0이면 → 아빠(공급가액)도 0 (그 시트는 우리가 찾는 시트가 아님)
        
        분산된 가족 통합 예외 지침:
        - 아빠가 술이 취해서 엄마가 도와준다: 엄마 값이 진실, 아빠 값을 보정
        
        Args:
            families: 가족 데이터 리스트
            
        Returns:
            List[Dict]: 아빠 값이 보정된 가족 데이터 리스트
        """
        for family in families:
            supply_amount = family.get('공급가액', 0)
            vat_amount = family.get('부가세', 0)
            
            # 중요: 엄마 값이 0이면 아빠 값도 0으로 설정 (그 시트는 우리가 찾는 시트가 아님)
            if vat_amount == 0:
                # 엄마 값이 0이면 아빠 값도 0으로 설정
                family['공급가액'] = 0
                family['요금합계'] = 0
                
                self.logger.info(f"엄마 값이 0이므로 아빠 값도 0으로 설정 (해당 시트는 우리가 찾는 시트가 아님)")
            
            # 아빠 값이 0이거나 없을 때 엄마 값을 기준으로 계산
            elif supply_amount == 0 and vat_amount > 0:
                # 엄마 값 × 10 = 아빠 값 (부가세법 10% 규칙)
                calculated_supply = vat_amount * 10
                family['공급가액'] = calculated_supply
                family['요금합계'] = calculated_supply + vat_amount
                
                self.logger.info(f"아빠 값 계산: 엄마 {vat_amount:,.0f}원 → 아빠 {calculated_supply:,.0f}원 (부가세법 10% 규칙)")
            
            # 분산된 가족 통합 예외 지침: 아빠가 술이 취해서 엄마가 도와준다
            elif supply_amount > 0 and vat_amount > 0:
                # 세법 10% 규칙 검증
                expected_vat = supply_amount * 0.1
                if abs(vat_amount - expected_vat) > 1:  # 1원 오차 허용
                    # 엄마 값이 진실이므로 아빠 값을 보정
                    corrected_supply = vat_amount * 10
                    family['공급가액'] = corrected_supply
                    family['요금합계'] = corrected_supply + vat_amount
                    
                    self.logger.info(f"아빠가 술이 취해서 엄마가 도와준다: 엄마 {vat_amount:,.0f}원 → 아빠 {corrected_supply:,.0f}원 (세법 10% 규칙 보정)")
        
        return families

# 테스트용 함수
def test_file_parser():
    """FileParser 테스트"""
    parser = FileParser()
    
    # 테스트 데이터 생성
    test_data = {
        '가맹점명': ['신전떡볶이', '맘스터치', '피자헛'],
        '사업자번호': ['123-45-67890', '234-56-78901', '345-67-89012'],
        '대표자명': ['홍길동', '김철수', '이영희'],
        '주소': ['서울시 강남구', '부산시 해운대구', '대구시 수성구'],
        '이메일': ['hong@shinjeon.com', 'kim@moms.com', 'lee@pizza.com'],
        '배달요금': [50000, 75000, 60000],
        '부가세': [5000, 7500, 6000]
    }
    
    df = pd.DataFrame(test_data)
    print("테스트 데이터:")
    print(df)
    
    # 파싱 결과 시뮬레이션
    parsed_result = {
        'file_type': 'excel',
        'raw_data': df,
        'headers': list(df.columns),
        'data_sections': parser._analyze_data_sections(df),
        'total_rows': len(df),
        'parsing_status': 'success'
    }
    
    print("\n파싱 결과:")
    print(f"파일 타입: {parsed_result['file_type']}")
    print(f"총 행 수: {parsed_result['total_rows']}")
    print(f"헤더: {parsed_result['headers']}")
    
    # 텍스트 추출 테스트
    text_content = parser.extract_text_content(parsed_result)
    print(f"\n추출된 텍스트: {text_content[:100]}...")

    def parse_multiple_files_parallel(self, file_paths: List[Path], max_workers: int = 4) -> List[Dict[str, Any]]:
        """
        Python 3.14 Free-Threaded Python을 활용한 병렬 파일 처리
        GIL 제거로 인한 성능 향상을 활용하여 여러 파일을 동시에 처리
        """
        results = []
        
        # Python 3.14의 향상된 ThreadPoolExecutor 성능 활용
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 각 파일에 대해 파싱 작업을 병렬로 실행
            future_to_file = {
                executor.submit(self.parse_file, file_path): file_path 
                for file_path in file_paths
            }
            
            # 결과 수집
            for future in concurrent.futures.as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    result = future.result()
                    result['file_path'] = str(file_path)  # 파일 경로 추가
                    results.append(result)
                    self.logger.info(f"병렬 처리 완료: {file_path}")
                except Exception as e:
                    error_result = self._create_error_response(f"병렬 처리 중 오류: {e}")
                    error_result['file_path'] = str(file_path)
                    results.append(error_result)
                    self.logger.error(f"병렬 처리 실패: {file_path} - {e}")
        
        return results
    
    def batch_validate_files(self, file_paths: List[Path]) -> Dict[str, Any]:
        """
        Python 3.14 Free-Threaded Python을 활용한 배치 파일 검증
        여러 파일의 유효성을 동시에 검사
        """
        validation_results = {
            'valid_files': [],
            'invalid_files': [],
            'total_files': len(file_paths),
            'processing_time': 0
        }
        
        start_time = time.time()
        
        # 병렬로 파일 유효성 검사
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_to_file = {
                executor.submit(self.file_upload_validator.validate, file_path): file_path
                for file_path in file_paths
            }
            
            for future in concurrent.futures.as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    validation_result = future.result()
                    if validation_result.is_valid:
                        validation_results['valid_files'].append(str(file_path))
                    else:
                        validation_results['invalid_files'].append(str(file_path))
                        if validation_result.message:
                            self.logger.warning("파일 검증 실패(%s): %s", file_path, validation_result.message)
                except Exception as e:
                    validation_results['invalid_files'].append(str(file_path))
                    self.logger.error(f"파일 검증 실패: {file_path} - {e}")
        
        validation_results['processing_time'] = time.time() - start_time
        return validation_results
    
    def parse_multiple_files_optimized(self, file_paths: List[Path], max_workers: int = 4) -> List[Dict[str, Any]]:
        """
        Python 3.14 Free-Threaded Python을 활용한 최적화된 병렬 파일 처리
        새로운 ParallelFileProcessor를 사용하여 고성능 처리
        """
        if not file_paths:
            return []
        
        self.logger.info(f"최적화된 병렬 파일 처리 시작: {len(file_paths)}개 파일")
        
        # ParallelFileProcessor 사용
        processor = ParallelFileProcessor(
            max_workers=max_workers,
            processing_mode=ProcessingMode.HYBRID,
            chunk_size=50
        )
        
        # 파일 경로를 문자열로 변환
        file_path_strs = [str(path) for path in file_paths]
        
        # 병렬 처리 실행
        results = processor.process_files_parallel(
            file_path_strs,
            self._parse_single_file_optimized
        )
        
        # 결과 변환
        parsed_results = []
        for result in results:
            if result.success:
                parsed_results.append(result.data)
            else:
                error_result = self._create_error_response(f"파일 처리 실패: {result.error}")
                error_result['file_path'] = result.file_path
                parsed_results.append(error_result)
        
        # 성능 리포트 로깅
        performance_report = processor.get_performance_report()
        self.logger.info(f"최적화된 병렬 처리 완료: {performance_report['successful_files']}/{performance_report['total_files']} 성공 "
                        f"({performance_report['total_time']:.2f}초, {performance_report['throughput']:.2f} 파일/초)")
        
        return parsed_results
    
    def _parse_single_file_optimized(self, file_path: str) -> Dict[str, Any]:
        """
        단일 파일 파싱 (최적화된 병렬 처리용)
        """
        try:
            path_obj = Path(file_path)
            return self.parse_file(path_obj)
        except Exception as e:
            self.logger.error(f"최적화된 파일 파싱 실패: {file_path} - {e}")
            raise
    
    def process_files_with_progress(self, file_paths: List[Path], 
                                   progress_callback: Optional[Callable] = None) -> List[Dict[str, Any]]:
        """
        진행률 콜백을 포함한 파일 처리
        """
        if not file_paths:
            return []
        
        self.logger.info(f"진행률 추적 파일 처리 시작: {len(file_paths)}개 파일")
        
        results = []
        total_files = len(file_paths)
        
        # 병렬 처리 실행
        processor = ParallelFileProcessor(
            max_workers=4,
            processing_mode=ProcessingMode.THREAD,
            chunk_size=10
        )
        
        file_path_strs = [str(path) for path in file_paths]
        
        # 진행률 추적을 위한 콜백 함수
        def progress_tracker(result):
            results.append(result)
            if progress_callback:
                progress = len(results) / total_files * 100
                progress_callback(progress, len(results), total_files)
        
        # 병렬 처리 실행
        parallel_results = processor.process_files_parallel(
            file_path_strs,
            self._parse_single_file_optimized
        )
        
        # 결과 변환
        parsed_results = []
        for result in parallel_results:
            if result.success:
                parsed_results.append(result.data)
            else:
                error_result = self._create_error_response(f"파일 처리 실패: {result.error}")
                error_result['file_path'] = result.file_path
                parsed_results.append(error_result)
        
        # 최종 진행률 콜백
        if progress_callback:
            progress_callback(100.0, total_files, total_files)
        
        return parsed_results
    
    def _validate_single_file(self, file_path: Path) -> bool:
        """
        단일 파일 유효성 검사 (병렬 처리용)
        """
        try:
            if not file_path.exists():
                return False
            
            if file_path.suffix.lower() not in self.supported_formats:
                return False
            
            # 파일 크기 검사 (100MB 제한)
            if file_path.stat().st_size > 100 * 1024 * 1024:
                return False
            
            return True
        except Exception:
            return False


if __name__ == "__main__":
    test_file_parser()








