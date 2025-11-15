"""
검증 모듈

공급받는자 정보 검증 및 신뢰도 계산 기능을 제공합니다.
"""

import pandas as pd
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class Validator:
    """검증 모듈"""
    
    def __init__(self):
        self.logger = logger

    def calculate_confidence(self, extracted_data: Dict[str, str]) -> float:
        """추출된 데이터의 신뢰도 점수 계산 (0.0 ~ 1.0)"""
        scores = []
        
        # 각 필드별 점수
        if extracted_data['business_number']:
            scores.append(0.3)  # 사업자등록번호는 중요하므로 높은 가중치
        if extracted_data['store_name']:
            scores.append(0.25)
        if extracted_data['representative']:
            scores.append(0.2)
        if extracted_data['address']:
            scores.append(0.15)
        if extracted_data['email']:
            scores.append(0.1)
        
        return sum(scores) if scores else 0.0

    def validate_family_completeness(self, recipient: Dict[str, Any]) -> bool:
        """5형제 가족 검증 시스템: 모든 필수 필드가 완전한지 확인"""
        required_fields = ['사업자등록번호', '상호', '대표명', '사업장주소', '사업자이메일']
        
        missing_fields = []
        for field in required_fields:
            value = recipient.get(field, '')
            if not value or value in ['None', '', 'nan']:
                missing_fields.append(field)
        
        if missing_fields:
            self.logger.warning(f"👨‍👩‍👧‍👦 가족 불완전: {len(missing_fields)}명 부재 - {missing_fields}")
            return False
        
        self.logger.info("👨‍👩‍👧‍👦 가족 완전: 5형제 모두 존재")
        return True

    def validate_vat_ratio(self, recipient: Dict[str, Any]) -> bool:
        """부가세 비율 검증: 공급가액 × 0.1 = 부가세 (5% 허용 오차)"""
        try:
            supply_amount = recipient.get('공급가액', 0)
            vat_amount = recipient.get('부가세', 0)
            
            if not supply_amount or not vat_amount:
                return False
            
            expected_vat = supply_amount * 0.1
            tolerance = expected_vat * 0.05  # 5% 허용 오차
            
            is_valid = abs(vat_amount - expected_vat) <= tolerance
            
            if not is_valid:
                self.logger.warning(f"💰 부가세 비율 오류: 예상={expected_vat:.0f}, 실제={vat_amount}, 오차={abs(vat_amount - expected_vat):.0f}")
            
            return is_valid
            
        except Exception as e:
            self.logger.error(f"부가세 비율 검증 오류: {str(e)}")
            return False

    def validate_recipient(self, recipient: Dict[str, Any], guideline: Dict[str, Any]) -> bool:
        """추출된 공급받는자 정보 검증 (5형제 가족 검증 시스템 적용)"""
        
        # 1. 5형제 가족 검증 (절대 지침)
        if not self.validate_family_completeness(recipient):
            self.logger.warning("❌ 가족 불완전으로 데이터 제외")
            return False
        
        # 2. 부가세 비율 검증 (절대 지침)
        if not self.validate_vat_ratio(recipient):
            self.logger.warning("❌ 부가세 비율 오류로 데이터 제외")
            return False
        
        # 3. 기존 업종별 검증 (업종별 지침)
        min_valid_fields = guideline.get('min_valid_fields', 3)
        valid_fields = sum(1 for value in recipient.values() 
                          if isinstance(value, str) and value.strip())
        
        confidence_threshold = guideline.get('confidence_threshold', 0.3)
        
        is_valid = valid_fields >= min_valid_fields and recipient.get('confidence', 0) >= confidence_threshold
        
        if not is_valid:
            self.logger.debug(f"업종별 검증 실패: 필드수={valid_fields}/{min_valid_fields}, 신뢰도={recipient.get('confidence', 0):.2f}/{confidence_threshold}")
        
        return is_valid

    def validate_recipients(self, recipients: List[Dict[str, Any]], stats: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """공급받는자 목록 검증 및 필터링"""
        if not recipients:
            return []
        
        # stats에서 guideline 추출 시도, 없으면 기본값 사용
        guideline = stats.get('guideline', {}) if stats else {}
        if not guideline:
            # 기본 guideline 설정
            guideline = {
                'min_valid_fields': 3,
                'confidence_threshold': 0.3
            }
        
        validated_list = []
        for recipient in recipients:
            if self.validate_recipient(recipient, guideline):
                validated_list.append(recipient)
        
        self.logger.info(f"검증 완료: {len(validated_list)}/{len(recipients)}건 통과")
        return validated_list

    def remove_duplicates(self, recipients: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """사업자등록번호 기준 중복 제거"""
        seen_numbers = set()
        unique_recipients = []
        
        for recipient in recipients:
            business_number = recipient.get('사업자등록번호', '')
            if business_number and business_number not in seen_numbers:
                seen_numbers.add(business_number)
                unique_recipients.append(recipient)
            elif not business_number:
                # 사업자등록번호가 없는 경우도 포함 (신뢰도 높은 것만)
                if recipient.get('confidence', 0) >= 0.5:
                    unique_recipients.append(recipient)
        
        return unique_recipients

    def get_extraction_summary(self, recipients: List[Dict[str, Any]]) -> Dict[str, Any]:
        """추출 결과 요약"""
        if not recipients:
            return {
                'total_count': 0,
                'high_confidence': 0,
                'medium_confidence': 0,
                'low_confidence': 0,
                'extraction_rate': 0.0
            }
        
        high_confidence = sum(1 for r in recipients if r.get('confidence', 0) >= 0.7)
        medium_confidence = sum(1 for r in recipients if 0.4 <= r.get('confidence', 0) < 0.7)
        low_confidence = sum(1 for r in recipients if r.get('confidence', 0) < 0.4)
        
        return {
            'total_count': len(recipients),
            'high_confidence': high_confidence,
            'medium_confidence': medium_confidence,
            'low_confidence': low_confidence,
            'extraction_rate': len(recipients) / len(recipients) if recipients else 0.0
        }


