"""
파일 업로드 및 템플릿 카운트 계산 연동 모듈
core/file_parser.py의 템플릿 카운트 계산 기능을 연동
"""

import os
import tempfile
import logging
import math
from typing import Dict, Any
from core.file_parser import FileParser

logger = logging.getLogger(__name__)

def save_uploaded_file(uploaded_file) -> str:
    """
    업로드된 파일을 임시 디렉토리에 저장
    
    Args:
        uploaded_file: Flask uploaded file
        
    Returns:
        str: 저장된 파일 경로
    """
    try:
        # 임시 디렉토리 생성
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, uploaded_file.filename)
        
        # 파일 저장
        uploaded_file.seek(0)
        uploaded_file.save(temp_file_path)
        
        logger.info(f"파일 저장 완료: {temp_file_path}")
        return temp_file_path
        
    except Exception as e:
        logger.error(f"파일 저장 실패: {str(e)}")
        raise

def cleanup_temp_file(file_path: str):
    """
    임시 파일 및 디렉토리 정리
    
    Args:
        file_path: 정리할 파일 경로
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.debug(f"임시 파일 삭제: {file_path}")
        
        # 디렉토리도 삭제 시도
        temp_dir = os.path.dirname(file_path)
        if os.path.exists(temp_dir) and not os.listdir(temp_dir):
            os.rmdir(temp_dir)
            logger.debug(f"임시 디렉토리 삭제: {temp_dir}")
    except Exception as e:
        logger.warning(f"임시 파일 정리 실패: {str(e)}")

def calculate_count_and_parse(file_path: str, industry_type: str = 'delivery') -> tuple[int, Dict[str, Any]]:
    """
    파일에서 템플릿 건수(공급받는자 수) 계산 및 파싱 데이터 반환
    
    핵심: 검열 건수(72)가 아닌 실제 템플릿에 기입된 건수(53)만 카운트
    대혁명 1단계: 단일 파싱 구현 - 파싱 결과를 재사용하기 위해 튜플로 반환
    
    Args:
        file_path: 파일 경로
        industry_type: 업종 타입 (기본값: 'delivery', 현재는 사용 안함)
        
    Returns:
        tuple[int, Dict[str, Any]]: (실제 템플릿 기입 건수, 파싱된 데이터)
        - 건수: 검열/필터링/가족 통합 후 최종적으로 템플릿에 기입되는 데이터 건수
        - 파싱된 데이터: 재사용을 위한 완전한 파싱 결과
    """
    try:
        logger.info(f"템플릿 건수 계산 및 파싱 시작: 파일={os.path.basename(file_path)}, 업종={industry_type}")
        
        # 파일 파싱 (단 한 번만 실행)
        from core.file_parser import FileParser
        from core.recipient_extractor import RecipientExtractor
        
        file_parser = FileParser()
        parsed_data = file_parser.parse_file(file_path)
        
        if not parsed_data or parsed_data.get('parsing_status') != 'success':
            logger.warning("파일 파싱 실패 또는 데이터 없음")
            return (0, parsed_data if parsed_data else {})
        
        # [The Architect Fix] 토큰 계산 시 강제 통합 수행
        from core.file_parser_utils.industry_rules import IndustryRules
        
        rules = IndustryRules()
        raw_families = parsed_data.get('families', [])
        
        if raw_families:
            # 통합된 건수 계산
            merged_families = rules.merge_family_data(raw_families)
            # ✅ 핵심 수정: 엄마값(부가세) 0인 경우 제외 (템플릿에 기입되지 않음)
            # merged_families는 딕셔너리 리스트이며, 각 딕셔너리에는 'mom_amount' 또는 '부가세' 필드가 있음
            # 필터링 전 상세 분석
            mom_zero_count = 0
            mom_non_zero_count = 0
            for f in merged_families:
                mom_amount = f.get('mom_amount', 0)
                부가세 = f.get('부가세', 0)
                # 숫자 변환 (문자열일 수 있음)
                try:
                    mom_amount = float(mom_amount) if mom_amount else 0
                except (ValueError, TypeError):
                    mom_amount = 0
                try:
                    부가세 = float(부가세) if 부가세 else 0
                except (ValueError, TypeError):
                    부가세 = 0
                
                if mom_amount == 0 and 부가세 == 0:
                    mom_zero_count += 1
                else:
                    mom_non_zero_count += 1
            
            logger.info(f"가족 통합 후 건수: {len(merged_families)}건")
            logger.info(f"   - 엄마값 0인 항목: {mom_zero_count}건")
            logger.info(f"   - 엄마값 0이 아닌 항목: {mom_non_zero_count}건")
            
            # ✅ 안정화: 엄마값 0인 경우 제외 (변환 전 계산값 정확도 향상)
            valid_families = []
            for idx, f in enumerate(merged_families):
                # ✅ 핵심: merged_families는 merge_family_data 결과
                # - single_df: 원본 families의 모든 필드 유지 (mom_amount 또는 부가세 포함 가능)
                # - merged_multi: mom_amount만 합산 (부가세 필드 없음)
                # 따라서 mom_amount 필드를 우선 확인하고, 없으면 부가세 필드 확인
                mom_amount_raw = f.get('mom_amount')
                부가세_raw = f.get('부가세')
                vat_amount_raw = f.get('vat_amount')
                
                # 숫자 변환 (문자열, None, NaN 등 모든 경우 처리)
                mom_amount = 0
                부가세 = 0
                
                # mom_amount 우선 확인 (merged_multi는 mom_amount만 있음)
                if mom_amount_raw is not None:
                    try:
                        if isinstance(mom_amount_raw, float) and math.isnan(mom_amount_raw):
                            mom_amount = 0
                        else:
                            mom_amount = float(mom_amount_raw) if mom_amount_raw else 0
                    except (ValueError, TypeError, AttributeError):
                        mom_amount = 0
                
                # 부가세 필드 확인 (single_df는 원본 필드 유지)
                if 부가세_raw is not None:
                    try:
                        if isinstance(부가세_raw, float) and math.isnan(부가세_raw):
                            부가세 = 0
                        else:
                            부가세 = float(부가세_raw) if 부가세_raw else 0
                    except (ValueError, TypeError, AttributeError):
                        부가세 = 0
                
                # vat_amount 필드 확인 (fallback)
                if vat_amount_raw is not None and mom_amount == 0 and 부가세 == 0:
                    try:
                        if isinstance(vat_amount_raw, float) and math.isnan(vat_amount_raw):
                            pass
                        else:
                            vat_amount = float(vat_amount_raw) if vat_amount_raw else 0
                            if vat_amount != 0:
                                mom_amount = vat_amount  # vat_amount를 mom_amount로 사용
                    except (ValueError, TypeError, AttributeError):
                        pass
                
                # 최종 엄마값 결정 (mom_amount 우선, 없으면 부가세 사용)
                final_mom_value = mom_amount if mom_amount != 0 else 부가세
                
                # 디버깅: 처음 3개 항목의 상세 정보 로깅
                if idx < 3:
                    logger.info(f"   [안정화] 항목 {idx+1}: mom_amount={mom_amount}, 부가세={부가세}, 최종값={final_mom_value}, 필드={list(f.keys())[:5]}")
                
                # 엄마값이 0이 아닌 경우만 포함
                if final_mom_value != 0:
                    valid_families.append(f)
            
            template_count = len(valid_families)
            excluded_count = len(merged_families) - template_count
            logger.info(f"✅ [안정화] 변환 전 템플릿 개수 계산 완료: {template_count}건 (엄마값 0 제외: {excluded_count}건)")
            if excluded_count > 0:
                logger.info(f"   → 엄마값 0인 항목은 템플릿에 기입되지 않으므로 제외됨")
        else:
            # 데이터 없음 (0건)
            recipient_extractor = RecipientExtractor()
            recipients = recipient_extractor.extract_recipients(parsed_data)
            # ✅ 핵심 수정: 엄마값(부가세) 0인 경우 제외
            # recipients는 '부가세' 필드를 가지고 있음 (mom_amount 아님)
            mom_zero_count = 0
            mom_non_zero_count = 0
            for r in recipients:
                부가세 = r.get('부가세', 0)
                mom_amount = r.get('mom_amount', 0)
                # 숫자 변환
                try:
                    부가세 = float(부가세) if 부가세 else 0
                except (ValueError, TypeError):
                    부가세 = 0
                try:
                    mom_amount = float(mom_amount) if mom_amount else 0
                except (ValueError, TypeError):
                    mom_amount = 0
                
                if 부가세 == 0 and mom_amount == 0:
                    mom_zero_count += 1
                else:
                    mom_non_zero_count += 1
            
            logger.info(f"추출된 공급받는자: {len(recipients)}건")
            logger.info(f"   - 엄마값 0인 항목: {mom_zero_count}건")
            logger.info(f"   - 엄마값 0이 아닌 항목: {mom_non_zero_count}건")
            
            # ✅ 안정화: 엄마값 0인 경우 제외 (변환 전 계산값 정확도 향상)
            valid_recipients = []
            for r in recipients:
                부가세 = r.get('부가세', 0)
                mom_amount = r.get('mom_amount', 0)
                # 숫자 변환
                try:
                    부가세 = float(부가세) if 부가세 else 0
                except (ValueError, TypeError):
                    부가세 = 0
                try:
                    mom_amount = float(mom_amount) if mom_amount else 0
                except (ValueError, TypeError):
                    mom_amount = 0
                
                # 엄마값이 0이 아닌 경우만 포함
                if 부가세 != 0 or mom_amount != 0:
                    valid_recipients.append(r)
            
            template_count = len(valid_recipients)
            excluded_count = len(recipients) - template_count
            logger.info(f"✅ [안정화] 변환 전 템플릿 개수 계산 완료: {template_count}건 (엄마값 0 제외: {excluded_count}건)")
            if excluded_count > 0:
                logger.info(f"   → 엄마값 0인 항목은 템플릿에 기입되지 않으므로 제외됨")
        
        logger.info(f"검열 전 건수: {parsed_data.get('total_rows', 0)}건")
        logger.info(f"✅ [안정화] 실제 템플릿 기입 건수(토큰 차감, 엄마값 0 제외): {template_count}건")
        logger.info(f"파싱된 데이터 반환 (재사용 준비 완료)")
        
        return (template_count, parsed_data)
        
    except Exception as e:
        logger.error(f"템플릿 건수 계산 및 파싱 중 오류 발생: {str(e)}")
        return (0, {})
