"""데이터 정규화 유틸리티 모듈.

공급받는자 파이프라인 전반에서 반복적으로 사용되는 정규화 로직을
하나의 모듈로 모아 재사용성과 테스트 용이성을 높입니다.
"""

from __future__ import annotations

import re
from typing import Optional, Union


INVALID_TEXT_TOKENS = {"", "none", "null", "nan", "미상", "없음", "해당없음", "-"}


def normalize_colname(col: Union[str, int, float, None]) -> str:
    """컬럼명을 비교 용도로 정규화합니다.

    개행/공백/탭을 제거하고 소문자로 변환하여 키 매칭 시 일관성을 보장합니다.
    """

    if col is None:
        return ""
    return (
        str(col)
        .replace("\n", "")
        .replace("\t", "")
        .replace(" ", "")
        .strip()
        .lower()
    )


def normalize_whitespace(text: Optional[str]) -> str:
    """공백을 단일 공백으로 축소하고 앞뒤 공백을 제거합니다."""

    if text is None:
        return ""
    normalized = re.sub(r"\s+", " ", str(text)).strip()
    return normalized


def normalize_address(address: Optional[str]) -> str:
    """주소 문자열을 표준 형태로 정리합니다."""

    normalized = normalize_whitespace(address)
    lowered = normalized.lower()
    if lowered in INVALID_TEXT_TOKENS:
        return ""
    return normalized
def normalize_amount(value: Union[str, int, float, None]) -> int:
    """금액 값을 정규화하여 정수로 반환합니다."""

    if value is None:
        return 0

    value_str = str(value).strip()
    if not value_str or value_str.lower() in INVALID_TEXT_TOKENS:
        return 0

    value_str = value_str.replace(",", "").replace("원", "").replace(" ", "")

    # 과학표기법 처리
    if "e" in value_str.lower():
        try:
            return int(round(float(value_str)))
        except (ValueError, TypeError):
            return 0

    numbers = re.findall(r"\d+\.?\d*", value_str)
    if not numbers:
        return 0

    candidate = numbers[0]
    try:
        if "." in candidate:
            return int(float(candidate))
        return int(candidate)
    except (ValueError, TypeError):
        return 0


def normalize_email(email: Optional[str]) -> str:
    """이메일 문자열의 공백을 정리하고 소문자로 변환합니다."""

    normalized = normalize_whitespace(email)
    return normalized.lower()


