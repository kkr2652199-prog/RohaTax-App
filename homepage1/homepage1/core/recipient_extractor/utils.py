"""
유틸리티 모듈

공통으로 사용되는 유틸리티 함수들을 제공합니다.
"""

from typing import List, Any, Optional
import pandas as pd

from .normalizers import (
    normalize_address,
    normalize_amount,
    normalize_email,
    normalize_whitespace,
)

def get_synonyms(column_name: str) -> List[str]:
    """컬럼명 동의어 반환 - 다양한 파일 형식 지원"""
    synonyms = {
        '가맹점명': [
            # 기본 동의어
            '가맹점', '가맹점명', '상호', '상호명', '매장명', '점포명', '업체명', '가게명', '법인명', '사업장명',
            # 공급받는자 관련
            '공급받는자 상호', '공급받는자 상호명', '공급받는자 회사명', '공급받는자 업체명', '공급받는자 가게명',
            # 거래처 관련
            '거래처명', '거래처 상호', '거래처명', '수취인명', '수취인 상호',
            # 일반적인 업체명
            '업체', '회사', '상점', '매장', '점포', '가게', '사업장', '사업소'
        ],
        '대표자명': [
            # 기본 동의어
            '대표자', '대표자명', '대표', '성명', '이름', '사업자명', '사업주', '사장', '사업주명', '사장님',
            # 공급받는자 관련
            '공급받는자 대표자', '공급받는자 대표자명',
            # 담당자 관련
            '대표담당자', '대표 담당자', '담당자', '담당자명', '등록자명', '등록자',
            # 일반적인 이름
            '성함', '이름', '성명', '주민명', '실명'
        ],
        '주소': [
            # 기본 동의어
            '주소', '사업장주소', '소재지', '사업장소재지', '도로명주소', '지번주소',
            # 공급받는자 관련
            '공급받는자 사업장주소', '공급받는자 주소', '공급받는자 소재지',
            # 일반적인 주소
            '사업장', '주소지', '소재지', '위치', '주소'
        ],
        '사업자번호': [
            # 기본 동의어
            '사업자등록번호', '등록번호', '사업자번호', '법인등록번호', '고유번호',
            # 공급받는자 관련
            '공급받는자 사업자등록번호', '공급받는자 사업자번호', '공급받는자 등록번호',
            # 거래처 관련
            '수취인 사업자번호', '거래처 사업자번호', '거래처 등록번호',
            # 일반적인 번호
            '사업자', '등록', '번호'
        ],
        '이메일': [
            # 기본 동의어
            '이메일', 'email', 'e-mail', '메일', '전자우편', '대표메일', '연락처메일', 'contact',
            # 공급받는자 관련
            '공급받는자 이메일', '공급받는자 메일', '공급받는자 전자우편',
            # 일반적인 이메일
            '이메일주소', '메일주소', '전자메일', '이메일', '메일'
        ]
    }
    return synonyms.get(column_name, [])

def find_header_row(df: pd.DataFrame) -> Optional[int]:
    """헤더 행 찾기 (데이터 밀도 기반)"""
    for row_idx in range(min(10, len(df))):  # 처음 10행만 검사
        row_data = df.iloc[row_idx].astype(str).tolist()
        text_ratio = sum(1 for cell in row_data if cell and cell != 'nan' and not cell.replace('.', '').isdigit()) / len(row_data)
        if text_ratio > 0.5:  # 텍스트 비율이 50% 이상이면 헤더로 판단
            return row_idx
    return None

def extract_total_amount_simple(
    row: pd.Series, column_names: List[str], default_total: int
) -> int:
    """총금액(합계) 단순 추출: 첨부 파일의 총금액 열이 있으면 사용, 없으면 기본값(공급가액+부가세)."""
    try:
        total_keywords = ['총금액', '합계금액', '총액', '합계', '요금합계']
        for col_idx, col_name in enumerate(column_names):
            name = str(col_name)
            if any(k in name for k in total_keywords):
                val = normalize_amount(row.iloc[col_idx])
                if val > 0:
                    return val
    except Exception:
        pass
    return int(default_total or 0)

def extract_amount(value) -> int:
    """금액 추출 (정수만 반환하여 과학표기법 방지)"""
    return normalize_amount(value)

def extract_business_number_simple(row: pd.Series, column_names: List[str]) -> str:
    """사업자번호 추출 (단순)"""
    for col_idx, col_name in enumerate(column_names):
        if '사업자' in col_name or '등록번호' in col_name:
            value = str(row.iloc[col_idx]).strip()
            if value and value != 'nan':
                # 간단한 사업자번호 추출 로직
                import re
                # 숫자만 추출
                numbers = re.findall(r'\d+', value)
                if numbers:
                    biz_num = ''.join(numbers)
                    # 10자리 사업자번호만 유효
                    if len(biz_num) == 10:
                        return biz_num
    return ""

def extract_store_name_simple(row: pd.Series, column_names: List[str]) -> str:
    """상호명 추출 (단순) - 숫자 형태는 상호명이 아닌 것으로 간주"""
    import logging
    logger = logging.getLogger(__name__)
    
    # 디버깅: 체크 중인 컬럼명들 출력
    logger.info(f"🔍 상호명 추출시도: 찾은 컬럼명들 {column_names}")
    
    for col_idx, col_name in enumerate(column_names):
        # 더 많은 키워드 패턴 추가 (홈텍스 템플릿 고려)
        store_keywords = ['가맹점', '가맹점명', '상호', '상호명', '매장', '점포', '업체', '가게', '공급받는자 상호', '공급받는자 상호명']
        
        # 디버깅: 매칭 테스트
        if any(keyword in col_name for keyword in store_keywords):
            logger.info(f"✅ 상호명 키워드 매칭: '{col_name}' -> 키워드: {[k for k in store_keywords if k in col_name]}")
            value = normalize_whitespace(row.iloc[col_idx])
            if value and value != 'nan':
                # 🚨 숫자만으로 구성된 값은 상호명이 아님
                if value.isdigit():
                    logger.info(f"⚠️ 숫자형 값 제외: '{value}'")
                    continue

                # 🚨 특별 패턴 검증: 숫자로 시작하거나 끝나는 패턴
                import re
                if re.match(r'^\d+$', value) or len(value) <= 1:
                    logger.info(f"⚠️ 패턴 불일치 제외: '{value}'")
                    continue

                # 🚨 "인천연수옥련2지사" 같은 단순 텍스트 제외
                if '인천연수옥련2지사' in value or '인천연수옥련2' in value:
                    logger.info(f"⚠️ 특수패턴 제외: '{value}'")
                    continue

                # ✅ 유효한 상호명으로 간주
                normalized = normalize_whitespace(value)
                logger.info(
                    f"✅ 상호명 추출 성공: '{normalized}' (컬럼: '{col_name}')"
                )
                return normalized
    logger.warning(f"❌ 상호명을 찾을 수 없습니다. 컬럼: {len(column_names)}개 확인됨")
    return ""

def extract_representative_simple(row: pd.Series, column_names: List[str]) -> str:
    """대표자명 추출 (단순)"""
    import logging

    logger = logging.getLogger(__name__)

    logger.info(f"🔍 대표자명 추출시도: 찾은 컬럼명들 {column_names}")

    # 다단계 우선순위 시스템: 필요 시 각 그룹에 키워드를 자유롭게 추가 가능
    priority_groups = [
        # 1순위: 가장 명확한 키워드 (완전 일치 수준)
        [
            '대표자명', '대표자 성명', '대표이사', '대표자 이름',
            '대표자(한글)', '대표자(영문)', '대표자_한글', '대표자_영문',
            '대표자 국문', '대표자 영문', '대표자명(국문)', '대표자명(영문)',
            '공급받는자성함', '공급받는자이름', '공급받는자 대표명', '공급받는자대표',
            '사장님성함', '사장님이름', '업체대표님', '업체성함', '업체대표이름'
        ],
        # 2순위: 사람 이름일 확률이 높은 일반 표현
        [
            '대표', '성명', '이름', '대표님', '사장', '사장님', '사장명',
            '사업주', '사업주명', '대표자(대표)', '대표자(국문)', '대표자(영문)',
            '대표자명 대표', '대표자명 국문', '대표자명 영문', '대표자명(대표)',
            'CEO', 'ceo', 'owner', '대표성명', '대표명'
        ],
        # 3순위: 담당자/점장 등 역할 기반 표현
        [
            '담당자', '담당자명', '담당자 성명', '담당자 이름', '담당부서',
            '점장', '점장명', '매니저', '관리자', '관리책임자', '지배인',
            'Contact Person', 'contact person', 'contact_person', 'contact',
            '대표2', '부대표', '관리 담당자', '현장 관리자', '업주'
        ],
        # 4순위: 작성자/등록자 등 가장 낮은 확률의 표현
        [
            '등록자', '등록자명', '작성자', '작성자명', '입력자', '기재자',
            '수정자', '변경자', '오너', '오너명'
        ],
    ]

    def _find_value_by_keywords(keywords: List[str]) -> Optional[str]:
        import re

        invalid_markers = {
            '', 'nan', 'none', 'null', '-', '없음', '미상', 'n/a', 'na', '해당없음', '해당 없음'
        }

        matched_columns = []
        for col_idx, col_name in enumerate(column_names):
            col_name_str = str(col_name).replace('\n', ' ').strip()
            matched = [keyword for keyword in keywords if keyword.lower() in col_name_str.lower()]
            if matched:
                value = normalize_whitespace(row.iloc[col_idx])
                if not value or value.lower() in invalid_markers:
                    continue

                # 대괄호로 둘러싸인 플레이스홀더([상점직접], [푸드테크] 등) 제외
                if re.match(r'^\[[^\]]+\]$', value):
                    logger.debug("⚠️ 대표자명 플레이스홀더 제외: %s", value)
                    continue

                # 최소 2글자 이상, 한글/영문 포함 여부 확인
                if len(value) < 2 or not re.search(r'[가-힣a-zA-Z]', value):
                    logger.debug("⚠️ 대표자명 유효성 미달: %s", value)
                    continue

                matched_columns.append((col_name_str, normalize_whitespace(value), matched))
        if matched_columns:
            # 가장 먼저 나온 컬럼을 사용 (엑셀 좌→우 우선)
            col_name, value, matched = matched_columns[0]
            logger.info(
                "✅ 대표자명 키워드 매칭: '%s' -> 키워드: %s (값: '%s')",
                col_name,
                matched,
                value,
            )
            return value
        return None

    # 우선순위를 순차적으로 적용하며 대표자명 탐색
    for order, keywords in enumerate(priority_groups, start=1):
        logger.debug("대표자명 추출 %d순위 검사: %s", order, keywords)
        extracted = _find_value_by_keywords(keywords)
        if extracted:
            logger.info("🎯 대표자명 %d순위에서 확정: %s", order, extracted)
            return extracted

    logger.warning(f"❌ 대표자명을 찾을 수 없습니다. 컬럼: {len(column_names)}개 확인됨")
    return ""

def extract_address_simple(row: pd.Series, column_names: List[str]) -> str:
    """주소 추출 (단순)"""
    for col_idx, col_name in enumerate(column_names):
        # 개행문자 제거하여 정확한 비교
        clean_col_name = str(col_name).replace('\n', ' ').strip()
        address_keywords = ['공급받는자 사업장주소', '사업장주소', '공급받는자 주소', '주소', '소재지', '사업장', '주소지']
        
        if any(keyword in clean_col_name for keyword in address_keywords):
            value = normalize_address(row.iloc[col_idx])
            if value:
                return value
    return ""

def extract_email_simple(row: pd.Series, column_names: List[str]) -> str:
    """이메일 추출 (단순) + 자동 수정"""
    for col_idx, col_name in enumerate(column_names):
        if any(keyword in col_name for keyword in ['이메일', 'email', '메일']):
            value = normalize_whitespace(row.iloc[col_idx])
            if value and value.lower() != 'nan':
                # 간단한 이메일 검증
                import re
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if re.match(email_pattern, value):
                    return normalize_email(value)
    return ""
