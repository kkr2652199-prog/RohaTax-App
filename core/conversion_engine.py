"""
통합 변환 엔진 - 모든 부품을 통합하여 전체 변환 프로세스 실행
핵심기술 절대지침과 공급받는자 지침을 반영하여 홈텍스 템플릿에 기입
"""

import os
import pandas as pd
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
from .engine_processor import (
    HometaxTemplateWriter,
    RecipientPipeline,
    RecipientPipelineError,
    RecipientPipelineResult,
    StatsCollector,
    create_error_response,
    create_success_response,
    get_conversion_status,
    ConversionContextManager,
    ContextValidationError,
)

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
        self.recipient_pipeline = RecipientPipeline(
            guideline_manager=self.guideline_manager,
            extractor_factory=RecipientExtractor,
            logger=self.logger,
        )
        self.context_manager = ConversionContextManager(logger=self.logger)
        
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
        """
        conversion_log: List[str] = []
        stats_collector = StatsCollector()
        conversion_log.append("변환 프로세스 시작")

        sanitized_user_info = user_info

        try:
            context = self.context_manager.prepare(
                uploaded_file_path=uploaded_file_path,
                supplier_info=supplier_info,
                template_id=template_id,
                industry_type=industry_type,
                issue_date=issue_date,
                file_name=file_name,
                user_info=user_info,
                conversion_log=conversion_log,
            )

            supplier_info = context.supplier_info
            template_id = context.template_id
            issue_date = context.issue_date
            file_name = context.file_name
            sanitized_user_info = context.user_info
            industry = context.industry

            self.logger.info("[CONVERSION] 변환 프로세스 시작")
            self.logger.info(f"[CONVERSION] 파일 경로: {uploaded_file_path}")
            self.logger.info(
                f"[CONVERSION] 사용자 ID: {sanitized_user_info.get('user_id') if sanitized_user_info else 'None'}"
            )
            self.logger.info(f"[CONVERSION] 업종 타입: {industry}")

            self.logger.info("명확한 데이터 전달 구조 적용 시작")
            
            conversion_log.append("1단계: 파일 파싱 시작")
            self.logger.info("[CONVERSION] 1단계: 파일 파싱 시작")
            parsed_data = self.file_parser.parse_file(uploaded_file_path)
            
            if parsed_data['parsing_status'] != 'success':
                self.logger.error(
                    "[CONVERSION] 파일 파싱 실패: %s",
                    parsed_data.get('error_message', '알 수 없는 오류'),
                )
                return create_error_response(
                    f"파일 파싱 실패: {parsed_data.get('error_message', '알 수 없는 오류')}",
                    conversion_log,
                )
            
            conversion_log.append(f"파일 파싱 완료: {parsed_data['total_rows']}행")
            self.logger.info(f"[CONVERSION] 파일 파싱 완료: {parsed_data['total_rows']}행")
            
            conversion_log.append("2단계: 업종별 절대지침 적용 시작")
            self.logger.info("[CONVERSION] 2단계: 업종별 절대지침 적용 시작")
            try:
                pipeline_result: RecipientPipelineResult = self.recipient_pipeline.run(
                    parsed_data=parsed_data,
                    industry_type=industry,
                )
            except RecipientPipelineError as exc:
                self.logger.error("[CONVERSION] 수신자 파이프라인 오류: %s", exc)
                return create_error_response(str(exc), conversion_log)

            recipients = pipeline_result.recipients
            conversion_log.extend(pipeline_result.log_entries)
            stats_collector.merge(pipeline_result.detailed_stats)
            extraction_summary = pipeline_result.extraction_summary
            
            conversion_log.append(f"업종별 절대지침 적용 완료: {len(recipients)}건")
            
            conversion_log.append("3단계: 공급받는자 통합지침 적용 시작")
            self.logger.info("👥 [CONVERSION] 3단계: 공급받는자 통합지침 적용 시작")
            self.logger.info(
                f"📊 [CONVERSION] 추출 대상 데이터: {len(parsed_data.get('data', []))}행"
            )

            result_files = self.template_writer.fill_templates_simple(
                recipients=recipients,
                supplier_info=supplier_info,
                template_id=template_id,
                issue_date=issue_date,
                file_name=file_name,
            )
            stats_collector.mark_files_generated(len(result_files))
            
            conversion_log.append(f"홈텍스 템플릿 기입 완료: {len(result_files)}개 파일")
            self.logger.info(
                f"✅ [CONVERSION] 홈텍스 템플릿 기입 완료: {len(result_files)}개 파일"
            )
            
            conversion_log.append("4단계: 결과 요약 시작")
            self.logger.info("📋 [CONVERSION] 4단계: 결과 요약 시작")
            
            conversion_log.append("변환 프로세스 완료")
            self.logger.info("🎉 [CONVERSION] 변환 프로세스 완료")
            
            final_stats = stats_collector.finalize(total_count=len(recipients))
            execution_time = final_stats.get('processing_time', 0)
            
            db_manager.log_conversion({
                'filename': os.path.basename(uploaded_file_path),
                'file_size': os.path.getsize(uploaded_file_path) if os.path.exists(uploaded_file_path) else 0,
                'recipient_count': len(recipients),
                'success': True,
                'execution_time': execution_time,
                'user_id': sanitized_user_info.get('user_id') if sanitized_user_info else None,
            })
            
            processing_time = final_stats.get('processing_time', 0)
            per_second = final_stats.get('per_second', 0)
            
            self.logger.info("📊 [CONVERSION] 상세 통계 계산 완료:")
            self.logger.info(f"   - 처리 시간: {processing_time:.2f}초")
            self.logger.info(f"   - 초당 처리 건수: {per_second:.2f}건/초")
            self.logger.info(f"   - 추출된 공급받는자: {len(recipients)}건")
            self.logger.info(f"   - 생성된 파일: {len(result_files)}개")
            
            return create_success_response(
                result_files=result_files,
                recipients=recipients,
                extraction_summary=extraction_summary,
                conversion_log=conversion_log,
                detailed_stats=final_stats,
            )

        except ContextValidationError as exc:
            return create_error_response(str(exc), conversion_log)
        except Exception as e:
            self.logger.error("❌ [CONVERSION] 변환 프로세스 오류: %s", e)
            conversion_log.append(f"❌ 변환 프로세스 오류: {str(e)}")
            
            import traceback

            db_manager.log_error({
                'filename': os.path.basename(uploaded_file_path) if uploaded_file_path else 'unknown',
                'error_type': 'ConversionEngineError',
                'error_message': str(e),
                'stack_trace': traceback.format_exc(),
                'severity': 'ERROR',
                'user_id': sanitized_user_info.get('user_id') if sanitized_user_info else None,
            })
            
            return create_error_response(
                f"변환 프로세스 중 오류 발생: {str(e)}",
                conversion_log,
            )

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
    status = get_conversion_status({'success': True, 'files': ['test.xlsx'], 'total_recipients': len(matched_data)})
    print(f"\n변환 상태: {status}")

if __name__ == "__main__":
    test_conversion_engine()









