"""
파일 파싱 부품 - 배달대행사 정산서 파일 파싱
핵심기술 절대지침에 따라 파일을 파싱하고 구조화된 데이터 반환
"""

import pandas as pd
import openpyxl
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
from .file_parser_utils.validation_pipeline import ValidationPipeline

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
        self.validation_pipeline = ValidationPipeline(
            upload_validator=self.file_upload_validator,
            logger=self.logger,
        )
        
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

            pre_validation = self.validation_pipeline.run(file_path)
            if not pre_validation.is_valid:
                error_message = pre_validation.message or "파일 검증에 실패했습니다."
                return self._create_error_response(error_message)

            if pre_validation.file_type == 'csv':
                return self._parse_csv(file_path)

            if pre_validation.file_type == 'excel':
                return self._parse_excel(file_path)

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
    
    def _find_families_in_sheet(self, sheet, required_keywords: Dict) -> List[Dict]:
        """
        시트에서 5형제 가족 찾기
        
        [최적화] 여기서는 통합(Merge)을 수행하지 않고 원본 데이터만 반환한다.
        통합은 상위 호출자(_parse_excel)가 1순위 여부에 따라 선택적으로 수행한다.
        
        Args:
            sheet: openpyxl Worksheet 객체
            required_keywords: 필수 컬럼 키워드 딕셔너리
            
        Returns:
            List[Dict]: 찾은 가족 정보 리스트 (통합되지 않은 원본 데이터)
        """
        families = []
        
        try:
            header_row = self.header_locator.detect_header_row(sheet)
            column_mapping = self.header_locator.map_columns(sheet, header_row, self.required_keywords)
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
            
            # [최적화] 여기서는 통합하지 않고 원본 데이터만 반환
            # 통합은 상위 호출자(_parse_excel)가 1순위 여부에 따라 선택적으로 수행
            families = raw_families
                    
        except Exception as e:
            self.logger.warning(f"가족 검색 중 오류: {str(e)}")
            
        return families
    
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
        """HeaderLocator에 위임된 실제 데이터 범위 감지."""
        return self.header_locator.get_actual_data_range(sheet)
    
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
    
    def _parse_excel(self, file_path: Path) -> Dict[str, Any]:
        """Excel 파일 파싱 - 지능앱 시트 검열 알고리즘 적용"""
        try:
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
            priority = best_sheet_result.get('priority')
            families = best_sheet_result.get('families', [])
            
            # [최적화] 1순위 시트(월 정산서)는 이미 통합된 데이터이므로 가족 통합 생략
            # 2순위 이하 시트(일간 내역서)는 흩어진 데이터를 합쳐야 하므로 통합 필요
            if priority != '1순위' and families:
                self.logger.info(
                    f"2순위 이하 시트 감지 - 가족 통합 수행: {len(families)}개 정보"
                )
                families = self.industry_rules.merge_family_data(families)
                self.logger.info(f"가족 통합 완료: {len(families)}개")
            elif priority == '1순위':
                self.logger.info(
                    f"1순위 시트(월 정산서) '{best_sheet_name}' - 가족 통합 생략 (이미 통합된 데이터)"
                )
            
            # 중요: 1순위 시트 데이터로 완전히 교체
            if priority == '1순위':
                self.logger.info(f"1순위 시트 '{best_sheet_name}' 데이터로 완전 교체")
                all_sheets = self.reporting_utils.build_priority_sheet_entry(
                    sheet_name=best_sheet_name,
                    headers=best_headers,
                    data=best_data,
                    header_row=best_header_row,
                    data_start_row=best_data_start_row,
                    priority=priority,
                    families=families,
                )
            
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
            data_sections = self.reporting_utils.analyze_data_sections(df)
            
            # 1순위 시트가 이미 선택된 경우 다른 시트 정보 수집하지 않음
            if priority == '1순위':
                self.logger.info(f"1순위 시트 '{best_sheet_name}' 선택됨 - 다른 시트 정보 수집 생략")
                # 1순위 시트만 사용하므로 all_sheets는 이미 위에서 설정됨
            else:
                all_sheets = self.reporting_utils.collect_sheet_overview(workbook)
                sheet_entry = all_sheets.setdefault(best_sheet_name, {'sheet_name': best_sheet_name})
                if families:
                    sheet_entry['families'] = families
                if priority:
                    sheet_entry['priority'] = priority
            
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
                'all_sheets': all_sheets,
                'families': families,
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
            header_row = self.header_locator.detect_csv_header_row(df, self.required_keywords)
            self.logger.info(f"CSV 헤더 행 감지: {header_row}행")
            
            # 헤더 행부터 데이터 추출
            if header_row > 0:
                df = df.iloc[header_row:]
                df.columns = df.iloc[0]  # 첫 행을 헤더로 설정
                df = df.drop(df.index[0])  # 첫 행 제거
                df = df.reset_index(drop=True)  # 인덱스 재설정
            
            # 데이터 섹션 분석
            data_sections = self.reporting_utils.analyze_data_sections(df)
            
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

