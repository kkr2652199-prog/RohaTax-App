"""점수 계산 유틸리티 전담 모듈."""

from __future__ import annotations


def score_representative_header(header: str) -> int:
    """대표자 헤더 점수를 계산한다."""
    header_lower = header.strip().lower()

    if not header_lower or header_lower in {'', 'none', 'nan'}:
        return -100

    score = 0

    if '대표자' in header_lower:
        score += 90
    elif '대표' in header_lower:
        score += 70

    if any(keyword in header_lower for keyword in ['사장', '원장', '점주', '대표원장']):
        score += 60

    if any(keyword in header_lower for keyword in ['성명', '성함', '이름']):
        score += 40

    if any(keyword in header_lower for keyword in ['공급받는자', '수취인', '구매자', '거래처', '고객', '매입자', '업체', '가맹점', '매장', '점포', '업소']):
        score += 10

    if any(keyword in header_lower for keyword in ['담당', '매니저', '관리자', '점장']):
        score -= 30

    if any(keyword in header_lower for keyword in ['등록자', '작성자', '입력자']):
        score -= 50

    if '대표번호' in header_lower:
        score -= 80

    if '번호' in header_lower and not any(keyword in header_lower for keyword in ['성명', '성함', '이름']):
        score -= 60

    return score

