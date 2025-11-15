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

# 컬럼 매핑 및 점수 계산 함수들
from .column_scorer import (
    remap_headers_for_second_priority,
    find_best_column_match,
    calculate_column_score,
    calculate_business_number_score,
    calculate_email_score,
    calculate_general_field_score,
    validate_total_column_before_vat,
    get_synonyms as get_column_synonyms,  # column_scorer의 get_synonyms
)

# 공급받는자 정보 추출 함수들
from .extractor import (
    extract_recipients_from_second_priority,
)

# 기존 utils.py의 모든 함수들을 re-export (legacy_utils.py로 이동)
from .legacy_utils import (
    get_synonyms,  # legacy_utils의 get_synonyms (다른 용도)
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
    # 컬럼 매핑 및 점수 계산 함수들
    'remap_headers_for_second_priority',
    'find_best_column_match',
    'calculate_column_score',
    'calculate_business_number_score',
    'calculate_email_score',
    'calculate_general_field_score',
    'validate_total_column_before_vat',
    'get_column_synonyms',
    # 공급받는자 정보 추출 함수들
    'extract_recipients_from_second_priority',
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

