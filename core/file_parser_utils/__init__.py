"""
파일 파서 유틸리티 모듈
독립적인 유틸리티 함수들을 모듈화
"""

import re
from typing import Dict, Any


def to_number(value) -> float:
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


def is_business_number(value: str) -> bool:
    """사업자번호 패턴 확인"""
    # 숫자 10자리 또는 하이픈 포함
    pattern = r'^\d{3}-?\d{2}-?\d{5}$|^\d{10}$'
    return bool(re.match(pattern, value))


def is_representative_name(value: str) -> bool:
    """대표자명 패턴 확인 (한글 이름)"""
    # 한글 2-4자 이름 패턴
    pattern = r'^[가-힣]{2,4}$'
    return bool(re.match(pattern, value)) and not value.isdigit()


def is_address(value: str) -> bool:
    """주소 패턴 확인"""
    address_keywords = ['시', '구', '동', '로', '길', '번지', '아파트', '빌딩']
    return any(keyword in value for keyword in address_keywords) and len(value) > 5


def is_store_name(value: str) -> bool:
    """가맹점명 패턴 확인"""
    store_keywords = ['점', '식당', '카페', '마트', '상점', '센터', '플라자']
    return any(keyword in value for keyword in store_keywords) and len(value) > 2


def is_valid_family(family_data: Dict) -> bool:
    """유효한 가족 정보인지 검증"""
    # 아빠 금액이 있어야 유효한 가족
    return family_data.get('dad_amount', 0) > 0


def normalize_business_number(business_number: str) -> str:
    """사업자번호 정규화 (10자리 숫자로 통일)"""
    if not business_number:
        return ""
    
    # 하이픈 제거하고 숫자만 추출
    cleaned = re.sub(r'[^\d]', '', str(business_number))
    
    # 10자리인지 확인
    if len(cleaned) == 10:
        return cleaned
    
    return business_number.strip()


def validate_email(email: str) -> bool:
    """이메일 형식 검증"""
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def clean_text(text: str) -> str:
    """텍스트 정리 (공백, 특수문자 제거)"""
    if not text:
        return ""
    
    # 공백 정리 및 특수문자 제거
    cleaned = re.sub(r'\s+', ' ', str(text).strip())
    return cleaned


