"""
recipient_extractor 유틸리티 모듈
"""

# 데이터 검증 함수들
from .data_validator import (
    is_valid_business_number,
    is_valid_store_name,
    is_valid_representative_name,
    is_valid_address,
    is_valid_email,
    is_valid_amount,
)

# 기존 utils.py의 모든 함수들을 re-export (legacy_utils.py로 이동)
from .legacy_utils import (
    get_synonyms,
    find_header_row,
    extract_total_amount_simple,
    extract_amount,
    extract_business_number_simple,
    extract_store_name_simple,
    extract_representative_simple,
    extract_address_simple,
    extract_email_simple,
)

__all__ = [
    # 데이터 검증 함수들
    'is_valid_business_number',
    'is_valid_store_name',
    'is_valid_representative_name',
    'is_valid_address',
    'is_valid_email',
    'is_valid_amount',
    # 기존 utils.py 함수들
    'get_synonyms',
    'find_header_row',
    'extract_total_amount_simple',
    'extract_amount',
    'extract_business_number_simple',
    'extract_store_name_simple',
    'extract_representative_simple',
    'extract_address_simple',
    'extract_email_simple',
]

