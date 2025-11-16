"""
공용 유틸리티 함수 모음
프로젝트 전반에서 사용되는 공통 함수들을 모아둔 모듈
"""


def row_value(row, key, default=None):
    """sqlite3.Row 안전 접근 헬퍼.
    
    Row는 dict.get을 지원하지 않으므로 키 인덱싱 후 None/누락을 기본값으로 대체한다.
    
    Args:
        row: sqlite3.Row 객체
        key: 접근할 키 이름
        default: 키가 없거나 값이 None일 때 반환할 기본값
    
    Returns:
        row[key]의 값, 또는 키가 없거나 None인 경우 default 값
    """
    try:
        value = row[key]
    except Exception:
        return default
    return default if value is None else value




