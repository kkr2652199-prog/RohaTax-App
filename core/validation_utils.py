"""
회원가입 검증 유틸리티 모듈
기존 routes/home.py의 검증 로직을 보강하는 연장 모듈
"""

import re
import logging
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)

class RegistrationValidator:
    """회원가입 검증 클래스"""
    
    def __init__(self):
        self.logger = logger
    
    def validate_business_number_checksum(self, business_number: str) -> Tuple[bool, str]:
        """
        사업자등록번호 체크섬 검증
        
        Args:
            business_number: 10자리 사업자등록번호
            
        Returns:
            Tuple[bool, str]: (유효성, 오류메시지)
        """
        try:
            # 숫자만 추출
            digits = re.sub(r'\D', '', business_number)
            
            if len(digits) != 10:
                return False, "사업자등록번호는 10자리 숫자여야 합니다"
            
            if not digits.isdigit():
                return False, "사업자등록번호는 숫자만 입력 가능합니다"
            
            # 체크섬 계산
            weights = [1, 3, 7, 1, 3, 7, 1, 3, 5]
            checksum = 0
            
            for i in range(9):
                checksum += int(digits[i]) * weights[i]
            
            # 9번째 자리 처리
            checksum += int(digits[8]) * 5 // 10
            remainder = checksum % 10
            
            # 체크섬 검증
            if remainder == 0:
                expected_check = 0
            else:
                expected_check = 10 - remainder
            
            actual_check = int(digits[9])
            
            if actual_check == expected_check:
                return True, "유효한 사업자등록번호입니다"
            else:
                return False, f"유효하지 않은 사업자등록번호입니다 (체크섬 오류)"
                
        except Exception as e:
            self.logger.error(f"사업자등록번호 검증 오류: {str(e)}")
            return False, "사업자등록번호 검증 중 오류가 발생했습니다"
    
    def validate_password_strength(self, password: str) -> Tuple[bool, str, List[str]]:
        """
        비밀번호 강도 검증
        
        Args:
            password: 검증할 비밀번호
            
        Returns:
            Tuple[bool, str, List[str]]: (유효성, 메시지, 오류목록)
        """
        errors = []
        
        if len(password) < 8:
            errors.append("8자리 이상")
        
        if not re.search(r'[A-Z]', password):
            errors.append("대문자 포함")
        
        if not re.search(r'[a-z]', password):
            errors.append("소문자 포함")
        
        if not re.search(r'\d', password):
            errors.append("숫자 포함")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("특수문자 포함")
        
        if errors:
            return False, f"비밀번호 요구사항: {', '.join(errors)}", errors
        else:
            return True, "안전한 비밀번호입니다", []
    
    def validate_email_format(self, email: str) -> Tuple[bool, str]:
        """
        이메일 형식 검증
        
        Args:
            email: 검증할 이메일
            
        Returns:
            Tuple[bool, str]: (유효성, 오류메시지)
        """
        if not email:
            return False, "이메일을 입력해주세요"
        
        # 기본 이메일 형식 검증
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, email):
            return False, "올바른 이메일 형식이 아닙니다"
        
        # 추가 검증: 도메인 길이, 연속 점 등
        if '..' in email:
            return False, "이메일에 연속된 점(.)이 있습니다"
        
        if len(email) > 254:
            return False, "이메일이 너무 깁니다 (254자 이하)"
        
        return True, "유효한 이메일입니다"
    
    def validate_phone_format(self, phone: str) -> Tuple[bool, str]:
        """
        전화번호 형식 검증 및 정규화
        
        Args:
            phone: 검증할 전화번호
            
        Returns:
            Tuple[bool, str]: (유효성, 정규화된번호 또는 오류메시지)
        """
        if not phone:
            return False, "전화번호를 입력해주세요"
        
        # 숫자만 추출
        digits = re.sub(r'\D', '', phone)
        
        # 휴대폰 번호 패턴 검증
        mobile_patterns = [
            r'^010\d{8}$',  # 010-0000-0000
            r'^01[1-9]\d{7,8}$',  # 011, 016, 017, 018, 019
        ]
        
        is_valid = any(re.match(pattern, digits) for pattern in mobile_patterns)
        
        if not is_valid:
            return False, "올바른 휴대폰 번호 형식이 아닙니다 (예: 010-1234-5678)"
        
        # 정규화 (010-0000-0000 형식)
        if digits.startswith('010'):
            normalized = f"010-{digits[3:7]}-{digits[7:]}"
        else:
            normalized = f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
        
        return True, normalized
    
    def validate_company_info(self, company_name: str, business_type: str, business_category: str) -> Tuple[bool, str]:
        """
        회사 정보 검증
        
        Args:
            company_name: 회사명
            business_type: 업태
            business_category: 종목
            
        Returns:
            Tuple[bool, str]: (유효성, 오류메시지)
        """
        if not company_name or len(company_name.strip()) < 2:
            return False, "회사명은 2자 이상 입력해주세요"
        
        if not business_type or len(business_type.strip()) < 2:
            return False, "업태는 2자 이상 입력해주세요"
        
        if not business_category or len(business_category.strip()) < 3:
            return False, "종목은 3자 이상 입력해주세요"
        
        # 특수문자 검증
        if not re.match(r'^[가-힣a-zA-Z0-9\s&().,-]+$', company_name):
            return False, "회사명에 사용할 수 없는 문자가 포함되어 있습니다"
        
        if not re.match(r'^[가-힣a-zA-Z0-9\s]+$', business_type):
            return False, "업태에 사용할 수 없는 문자가 포함되어 있습니다"
        
        if not re.match(r'^[가-힣a-zA-Z0-9\s]+$', business_category):
            return False, "종목에 사용할 수 없는 문자가 포함되어 있습니다"
        
        return True, "유효한 회사 정보입니다"
    
    def validate_username_format(self, username: str) -> Tuple[bool, str]:
        """
        사용자명 형식 검증
        
        Args:
            username: 검증할 사용자명
            
        Returns:
            Tuple[bool, str]: (유효성, 오류메시지)
        """
        if not username:
            return False, "사용자명을 입력해주세요"
        
        if len(username) < 3:
            return False, "사용자명은 3자 이상이어야 합니다"
        
        if len(username) > 20:
            return False, "사용자명은 20자 이하여야 합니다"
        
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False, "사용자명은 영문, 숫자, 언더스코어만 사용 가능합니다"
        
        if username.startswith('_') or username.endswith('_'):
            return False, "사용자명은 언더스코어로 시작하거나 끝날 수 없습니다"
        
        return True, "유효한 사용자명입니다"
    
    def validate_representative_name(self, name: str) -> Tuple[bool, str]:
        """
        대표자명 검증
        
        Args:
            name: 검증할 대표자명
            
        Returns:
            Tuple[bool, str]: (유효성, 오류메시지)
        """
        if not name or len(name.strip()) < 2:
            return False, "대표자명은 2자 이상 입력해주세요"
        
        if len(name.strip()) > 20:
            return False, "대표자명은 20자 이하여야 합니다"
        
        if not re.match(r'^[가-힣a-zA-Z\s]+$', name.strip()):
            return False, "대표자명은 한글, 영문만 입력 가능합니다"
        
        return True, "유효한 대표자명입니다"
    
    def comprehensive_validation(self, form_data: Dict[str, str]) -> Tuple[bool, List[str]]:
        """
        종합 검증
        
        Args:
            form_data: 폼 데이터 딕셔너리
            
        Returns:
            Tuple[bool, List[str]]: (전체 유효성, 오류 메시지 목록)
        """
        errors = []
        
        # 사용자명 검증
        username_valid, username_msg = self.validate_username_format(form_data.get('username', ''))
        if not username_valid:
            errors.append(f"사용자명: {username_msg}")
        
        # 비밀번호 검증
        password_valid, password_msg, _ = self.validate_password_strength(form_data.get('password', ''))
        if not password_valid:
            errors.append(f"비밀번호: {password_msg}")
        
        # 사업자등록번호 검증
        business_valid, business_msg = self.validate_business_number_checksum(form_data.get('business_number', ''))
        if not business_valid:
            errors.append(f"사업자등록번호: {business_msg}")
        
        # 이메일 검증
        email_valid, email_msg = self.validate_email_format(form_data.get('email', ''))
        if not email_valid:
            errors.append(f"이메일: {email_msg}")
        
        # 전화번호 검증
        phone_valid, phone_msg = self.validate_phone_format(form_data.get('phone', ''))
        if not phone_valid:
            errors.append(f"전화번호: {phone_msg}")
        
        # 대표자명 검증
        rep_valid, rep_msg = self.validate_representative_name(form_data.get('representative_name', ''))
        if not rep_valid:
            errors.append(f"대표자명: {rep_msg}")
        
        # 회사 정보 검증
        company_valid, company_msg = self.validate_company_info(
            form_data.get('company_name', ''),
            form_data.get('business_type', ''),
            form_data.get('business_category', '')
        )
        if not company_valid:
            errors.append(f"회사정보: {company_msg}")
        
        return len(errors) == 0, errors



# ===== 단순 유효성 헬퍼 (CRUD/API 등에서 재사용) =====
def validate_business_number(business_number: str) -> bool:
    """사업자등록번호(10자리, 체크섬) 간단 검증 함수."""
    validator = RegistrationValidator()
    ok, _msg = validator.validate_business_number_checksum(business_number or '')
    return ok


def validate_email(email: str) -> bool:
    """이메일 형식 간단 검증 함수."""
    validator = RegistrationValidator()
    ok, _msg = validator.validate_email_format(email or '')
    return ok


def validate_phone(phone: str) -> bool:
    """전화번호 형식 간단 검증 함수."""
    validator = RegistrationValidator()
    ok, _normalized_or_msg = validator.validate_phone_format(phone or '')
    return ok
