"""
통합 변환 엔진 - 모든 부품을 통합하여 전체 변환 프로세스 실행
핵심기술 절대지침과 공급받는자 지침을 반영하여 홈텍스 템플릿에 기입
"""

import os
import pandas as pd
import time
from typing import Dict, List, Any, Optional
import logging

# 부품들 import
from .file_parser import FileParser
from .recipient_extractor.main_extractor import RecipientExtractor
from .database_manager import db_manager
from .amount_extractor import AmountExtractor
from .template_manager import TemplateManager
from .conversion_core import ConversionCore
from .guideline_manager import GuidelineManager
from .absolute_guideline_loader import get_absolute_guideline_loader
from .engine_processor import HometaxTemplateWriter

logger = logging.getLogger(__name__)

class ConversionEngine:
    """통합 변환 엔진"""
    
    def __init__(self):
        """변환 엔진 초기화"""
        self.logger = logger
        
        # 부품들 초기화
        self.file_parser = FileParser()
        self.recipient_extractor = RecipientExtractor()
        self.amount_extractor = AmountExtractor()
        self.template_manager = TemplateManager()
        self.conversion_core = ConversionCore()
        self.guideline_manager = GuidelineManager()
        self.template_writer = HometaxTemplateWriter(
            template_manager=self.template_manager,
            conversion_core=self.conversion_core,
            logger=self.logger,
        )
        
        # 지능앱 핵심 기술: 절대지침 시스템 초기화
        self.absolute_guideline_loader = get_absolute_guideline_loader()
        
        # 홈텍스 템플릿 컬럼 매핑 (공급받는자 핵심기술 절대지침)
        self.hometax_columns = {
            'K': '사업자등록번호',    # 공급받는자 등록번호
            'M': '상호명',           # 공급받는자 상호
            'N': '대표자명',         # 공급받는자 성명
            'O': '사업장주소',       # 공급받는자 사업장주소
            'R': '이메일',           # 공급받는자 이메일
            'T': '공급가액',         # 공급가액 (1차)
            'U': '부가세',           # 부가세 (1차)
            'AB': '공급가액',        # 공급가액 (2차 - 중복)
            'AC': '부가세'           # 부가세 (2차 - 중복)
        }
    
    def convert_file(self, uploaded_file_path: str, 
                    supplier_info: Dict[str, str], 
                    template_id: str = "hometax_bulk",
                    industry_type: str = "delivery",
                    guidelines: Dict = None,
                    issue_date: str = None,
                    file_name: str = None,
                    user_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        전체 변환 프로세스 실행
        
        Args:
            uploaded_file_path: 업로드된 파일 경로
            supplier_info: 공급자 정보 (유저 정보)
            template_id: 템플릿 ID
            
        Returns:
            Dict: 변환 결과
            {
                'success': bool,
                'files': List[str],  # 생성된 파일 경로들
                'total_recipients': int,
                'extraction_summary': Dict,
                'amount_summary': Dict,
                'conversion_log': List[str]
            }
        """
        conversion_log = []
        
        # 📊 상세 통계 수집을 위한 변수 초기화
        start_time = time.time()
        detailed_stats = {
            'total_count': 0,
            'success_rate': 0,
            'rows_processed': 0,
            'files_generated': 0,
            'vat_included_count': 0,
            'vat_zero_count': 0,
            'total_supply_amount': 0,
            'total_tax_amount': 0,
            'email_auto_fixed_count': 0,
            'business_number_auto_fixed_count': 0,
            'perfect_info_count': 0,
            'processing_time': 0,
            'per_second': 0
        }
        
        try:
            conversion_log.append("변환 프로세스 시작")
            
            # ===== 단순화된 변환 프로세스 =====
            self.logger.info("[CONVERSION] 변환 프로세스 시작")
            self.logger.info(f"[CONVERSION] 파일 경로: {uploaded_file_path}")
            self.logger.info(f"[CONVERSION] 사용자 ID: {user_info.get('user_id') if user_info else 'None'}")
            self.logger.info(f"[CONVERSION] 업종 타입: {industry_type or 'delivery'}")
            
            # 기본 사용자 정보 검증만 수행
            if user_info:
                conversion_log.append("기본 사용자 정보 검증")
                if not user_info.get('business_number') or not user_info.get('company_name'):
                    return self._create_error_response("필수 사용자 정보가 누락되었습니다", conversion_log)
                conversion_log.append("기본 사용자 정보 검증 완료")
            
            # ===== 명확한 데이터 전달 구조 =====
            self.logger.info("명확한 데이터 전달 구조 적용 시작")
            
            # 1단계: 파일 파싱
            conversion_log.append("1단계: 파일 파싱 시작")
            self.logger.info("[CONVERSION] 1단계: 파일 파싱 시작")
            parsed_data = self.file_parser.parse_file(uploaded_file_path)
            
            if parsed_data['parsing_status'] != 'success':
                self.logger.error(f"[CONVERSION] 파일 파싱 실패: {parsed_data.get('error_message', '알 수 없는 오류')}")
                return self._create_error_response(
                    f"파일 파싱 실패: {parsed_data.get('error_message', '알 수 없는 오류')}",
                    conversion_log
                )
            
            conversion_log.append(f"파일 파싱 완료: {parsed_data['total_rows']}행")
            self.logger.info(f"[CONVERSION] 파일 파싱 완료: {parsed_data['total_rows']}행")
            
            # 2단계: 업종별 절대지침 적용 (5가지 컬럼 찾기, 6번 7번 컬럼 추출)
            conversion_log.append("2단계: 업종별 절대지침 적용 시작")
            self.logger.info("[CONVERSION] 2단계: 업종별 절대지침 적용 시작")
            selected = self.guideline_manager.select_guideline(industry_type or 'delivery')
            if not self.guideline_manager.is_guideline_ready():
                self.logger.warning(f"[CONVERSION] 지침 미구현 상태로 진행: {selected.get('name') if selected else 'Unknown'} (industry={industry_type})")
            
            # 안전성 검증: selected가 None인 경우 처리
            if selected is None:
                self.logger.error("업종별 지침을 찾을 수 없습니다.")
                return self._create_error_response("업종별 지침을 찾을 수 없습니다.", conversion_log)
            
            # 안전성 검증: selected가 딕셔너리가 아닌 경우 처리
            if not isinstance(selected, dict):
                self.logger.error(f"업종별 지침이 딕셔너리가 아닙니다: {type(selected)}")
                return self._create_error_response("업종별 지침 형식이 올바르지 않습니다.", conversion_log)
            
            # 핵심 수정: 매번 새로운 RecipientExtractor 인스턴스 생성 (상태 초기화)
            recipient_extractor = RecipientExtractor()
            recipient_extractor.set_industry_guideline(industry_type or 'delivery', selected)
            recipients = recipient_extractor.extract_recipients_simple(parsed_data, industry_type or 'delivery')
            
            if not recipients:
                return self._create_error_response(
                    "공급받는자 정보를 추출할 수 없습니다.",
                    conversion_log
                )
            
            # 📊 통계 수집 (recipients에서 _stats 추출)
            if recipients and '_stats' in recipients[0]:
                stats = recipients[0]['_stats']
                detailed_stats.update({
                    'total_count': len(recipients),
                    'success_rate': 100,  # 성공적으로 추출된 경우
                    'rows_processed': stats.get('rows_processed', 0),
                    'vat_included_count': stats.get('vat_included_count', 0),
                    'vat_zero_count': stats.get('vat_zero_count', 0),
                    'total_supply_amount': stats.get('total_supply_amount', 0),
                    'total_tax_amount': stats.get('total_tax_amount', 0),
                    'email_auto_fixed_count': stats.get('email_auto_fixed_count', 0),
                    'business_number_auto_fixed_count': stats.get('business_number_auto_fixed_count', 0),
                    'perfect_info_count': stats.get('perfect_info_count', 0),
                    # 샘플 예시 전달 (있을 때만)
                    'email_auto_fixed_sample_from': stats.get('email_auto_fixed_sample_from'),
                    'email_auto_fixed_sample_to': stats.get('email_auto_fixed_sample_to'),
                    'business_auto_fixed_sample_from': stats.get('business_auto_fixed_sample_from'),
                    'business_auto_fixed_sample_to': stats.get('business_auto_fixed_sample_to')
                })
            
            conversion_log.append(f"업종별 절대지침 적용 완료: {len(recipients)}건")
            
            # 3단계: 공급받는자 통합지침 적용 (템플릿 기입 전용)
            conversion_log.append("3단계: 공급받는자 통합지침 적용 시작")
            self.logger.info("👥 [CONVERSION] 3단계: 공급받는자 통합지침 적용 시작")
            self.logger.info(f"📊 [CONVERSION] 추출 대상 데이터: {len(parsed_data.get('data', []))}행")
            
            # 추출된 데이터를 공급받는자 통합지침에 전달하여 템플릿 기입
            result_files = self.template_writer.fill_templates_simple(
                recipients=recipients,
                supplier_info=supplier_info,
                template_id=template_id,
                issue_date=issue_date,
                file_name=file_name,
            )
            
            conversion_log.append(f"홈텍스 템플릿 기입 완료: {len(result_files)}개 파일")
            self.logger.info(f"✅ [CONVERSION] 홈텍스 템플릿 기입 완료: {len(result_files)}개 파일")
            
            # 4단계: 결과 요약
            conversion_log.append("4단계: 결과 요약 시작")
            self.logger.info("📋 [CONVERSION] 4단계: 결과 요약 시작")
            extraction_summary = recipient_extractor.get_extraction_summary(recipients)
            
            conversion_log.append("변환 프로세스 완료")
            self.logger.info("🎉 [CONVERSION] 변환 프로세스 완료")
            
            # 📊 최종 통계 완성
            end_time = time.time()
            execution_time = round(end_time - start_time, 2)
            
            # 데이터베이스에 변환 결과 로깅
            db_manager.log_conversion({
                'filename': os.path.basename(uploaded_file_path),
                'file_size': os.path.getsize(uploaded_file_path) if os.path.exists(uploaded_file_path) else 0,
                'recipient_count': len(recipients),
                'success': True,
                'execution_time': execution_time,  # 실행 시간 기록
                'user_id': user_info.get('user_id') if user_info else None
            })
            detailed_stats['processing_time'] = round(end_time - start_time, 2)
            detailed_stats['files_generated'] = len(result_files)
            if detailed_stats['processing_time'] > 0:
                detailed_stats['per_second'] = round(detailed_stats['total_count'] / detailed_stats['processing_time'], 1)
            
            # 📊 상세 통계 계산
            processing_time = time.time() - start_time
            per_second = len(recipients) / processing_time if processing_time > 0 else 0
            
            self.logger.info(f"📊 [CONVERSION] 상세 통계 계산 완료:")
            self.logger.info(f"   - 처리 시간: {processing_time:.2f}초")
            self.logger.info(f"   - 초당 처리 건수: {per_second:.2f}건/초")
            self.logger.info(f"   - 추출된 공급받는자: {len(recipients)}건")
            self.logger.info(f"   - 생성된 파일: {len(result_files)}개")
            
            return {
                'success': True,
                'files': result_files,
                'total_recipients': len(recipients),
                'extraction_summary': extraction_summary,
                'conversion_log': conversion_log,
                'recipients_preview': recipients[:5],  # 처음 5건 미리보기
                'detailed_stats': detailed_stats  # 📊 상세 통계 추가
            }
            
        except Exception as e:
            self.logger.error(f"❌ [CONVERSION] 변환 프로세스 오류: {str(e)}")
            conversion_log.append(f"❌ 변환 프로세스 오류: {str(e)}")
            
            # 에러를 데이터베이스에 로깅
            import traceback
            db_manager.log_error({
                'filename': os.path.basename(uploaded_file_path) if uploaded_file_path else 'unknown',
                'error_type': 'ConversionEngineError',
                'error_message': str(e),
                'stack_trace': traceback.format_exc(),
                'severity': 'ERROR',
                'user_id': user_info.get('user_id') if user_info else None
            })
            
            return self._create_error_response(
                f"변환 프로세스 중 오류 발생: {str(e)}",
                conversion_log
            )
    
    def _filter_valid_data(self, matched_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """업종별 지침에 따른 유효한 데이터 필터링"""
        valid_data = []
        
        # 현재 적용된 업종별 지침 가져오기
        current_guideline = self.recipient_extractor.get_current_guideline()
        min_valid_fields = current_guideline.get('min_valid_fields', 3)
        confidence_threshold = current_guideline.get('confidence_threshold', 0.3)
        
        for data in matched_data:
            # 업종별 필수 항목 확인
            required_fields = ['사업자등록번호', '상호', '대표명', '사업장주소', '사업자이메일']
            
            valid_fields = sum(1 for field in required_fields 
                              if data.get(field, '').strip())
            
            # 업종별 최소 필드 수 확인
            if valid_fields >= min_valid_fields:
                # 신뢰도 확인 (있는 경우)
                if 'confidence' in data:
                    if data['confidence'] >= confidence_threshold:
                        valid_data.append(data)
                else:
                    # 신뢰도가 없으면 그대로 통과
                    valid_data.append(data)
        
        self.logger.info(f"유효 데이터 필터링: {len(matched_data)}건 → {len(valid_data)}건 (업종: {current_guideline.get('industry', 'unknown')}, 최소필드: {min_valid_fields}, 신뢰도: {confidence_threshold})")
        return valid_data
    
    def _fill_hometax_template_simple(self, recipients: List[Dict[str, Any]], 
                                     supplier_info: Dict[str, str], 
                                     template_id: str,
                                     issue_date: str = None,
                                     file_name: str = None) -> List[str]:
        """이전 내부 메서드 호환성을 위해 템플릿 작성기 호출을 위임."""

        return self.template_writer.fill_templates_simple(
            recipients=recipients,
                    supplier_info=supplier_info, 
                    template_id=template_id,
                    issue_date=issue_date,
            file_name=file_name,
        )
    
    def _fill_hometax_template(self, valid_data: List[Dict[str, Any]], 
                              supplier_info: Dict[str, str], 
                              template_id: str,
                              issue_date: str = None,
                              file_name: str = None) -> List[str]:
         """이전 내부 메서드 호환성을 위해 템플릿 작성기 호출을 위임."""
 
         return self.template_writer.fill_templates(
             valid_data,
                    supplier_info=supplier_info, 
                    template_id=template_id,
                    issue_date=issue_date,
             file_name=file_name,
         )
 
     # 나머지 세부 구현은 HometaxTemplateWriter에 위임된다.

    def convert_to_hometax_template(
        self,
        parsed_data: Dict[str, Any],
        recipients: List[Dict[str, Any]],
        template_id: str = "hometax_official",
        supplier_info: Optional[Dict[str, Any]] = None,
        issue_date: Optional[str] = None,
        file_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """레거시 테스트 스크립트 호환을 위한 간편 변환 헬퍼."""

        normalized_supplier = self._normalize_supplier_info(
            supplier_info or parsed_data.get("supplier_info") or {}
        )

        try:
            result_files = self.template_writer.fill_templates_simple(
                recipients=recipients,
                supplier_info=normalized_supplier,
                template_id=template_id,
                issue_date=issue_date,
                file_name=file_name,
            )

            return {
                "success": True,
                "files": result_files,
                "total_recipients": len(recipients),
                "conversion_log": [f"Generated {len(result_files)} files."],
            }

        except Exception as exc:  # pragma: no cover - 레거시 경로 보호
            self.logger.error("convert_to_hometax_template 실패: %s", exc)
            return {
                "success": False,
                "error_message": str(exc),
                "files": [],
                "total_recipients": 0,
                "conversion_log": [f"Error: {exc}"],
            }

    def _normalize_supplier_info(self, raw_supplier_info: Dict[str, Any]) -> Dict[str, str]:
        """템플릿 작성기에 전달하기 위해 공급자 정보를 정규화."""

        return {
            "supplier_name": raw_supplier_info.get("supplier_name", ""),
            "supplier_representative": raw_supplier_info.get("supplier_representative", ""),
            "supplier_business_number": raw_supplier_info.get("supplier_business_number", ""),
            "supplier_address": raw_supplier_info.get("supplier_address", ""),
            "supplier_email": raw_supplier_info.get("supplier_email", ""),
            "supplier_business_type": raw_supplier_info.get("supplier_business_type", ""),
            "supplier_business_category": raw_supplier_info.get("supplier_business_category", ""),
        }
    
    def _create_error_response(self, error_message: str, conversion_log: List[str]) -> Dict[str, Any]:
        """오류 응답 생성"""
        return {
            'success': False,
            'error_message': error_message,
            'files': [],
            'total_recipients': 0,
            'extraction_summary': {},
            'amount_summary': {},
            'conversion_log': conversion_log
        }
    
    def get_conversion_status(self, conversion_result: Dict[str, Any]) -> Dict[str, Any]:
        """변환 결과 상태 요약"""
        if not conversion_result['success']:
            return {
                'status': 'failed',
                'message': conversion_result.get('error_message', '변환 실패'),
                'files_count': 0,
                'recipients_count': 0
            }
        
        return {
            'status': 'success',
            'message': '변환 완료',
            'files_count': len(conversion_result.get('files', [])),
            'recipients_count': conversion_result.get('total_recipients', 0),
            'extraction_rate': conversion_result.get('extraction_summary', {}).get('extraction_rate', 0),
            'total_amount': conversion_result.get('amount_summary', {}).get('total_amount', 0)
        }

# 테스트용 함수
def test_conversion_engine():
    """ConversionEngine 테스트"""
    engine = ConversionEngine()
    
    # 테스트 데이터
    test_data = {
        '가맹점명': ['신전떡볶이', '맘스터치', '피자헛'],
        '사업자번호': ['123-45-67890', '234-56-78901', '345-67-89012'],
        '대표자명': ['홍길동', '김철수', '이영희'],
        '주소': ['서울시 강남구 테헤란로 123', '부산시 해운대구 센텀로 456', '대구시 수성구 동대구로 789'],
        '이메일': ['hong@shinjeon.com', 'kim@moms.com', 'lee@pizza.com'],
        '요금합계': ['50,000원', '75,000원', '60,000원'],
        '부가세': ['5,000원', '7,500원', '6,000원']
    }
    
    df = pd.DataFrame(test_data)
    
    # 공급자 정보
    supplier_info = {
        'supplier_name': '테스트공급자',
        'supplier_representative': '테스트대표',
        'supplier_business_number': '999-99-99999',
        'supplier_address': '서울시 테스트구 테스트로 123',
        'supplier_email': 'test@supplier.com'
    }
    
    # 파싱 결과 시뮬레이션
    parsed_data = {
        'parsing_status': 'success',
        'raw_data': df
    }
    
    # 공급받는자 정보 추출
    recipients = engine.recipient_extractor.extract_recipients(parsed_data)
    amounts = engine.amount_extractor.extract_amounts(parsed_data)
    matched_data = engine.amount_extractor.match_amounts_with_recipients(recipients, amounts)
    
    print("매칭된 데이터:")
    for i, data in enumerate(matched_data, 1):
        print(f"{i}. {data}")
    
    # 변환 상태 확인
    status = engine.get_conversion_status({'success': True, 'files': ['test.xlsx'], 'total_recipients': len(matched_data)})
    print(f"\n변환 상태: {status}")

if __name__ == "__main__":
    test_conversion_engine()









