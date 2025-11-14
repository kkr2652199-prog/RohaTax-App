"""
변환 관련 헬퍼 함수 모듈
공통으로 사용되는 유틸리티 함수들
"""

import os
import tempfile
import logging
from datetime import datetime
from core.file_parser import FileParser

logger = logging.getLogger(__name__)


def normalize_issue_date(s: str) -> str:
    """
    전자세금일자 문자열을 ISO 형식(YYYY-MM-DD)으로 정규화하는 함수
    
    지원 형식:
    - "251001" (6자리 숫자)
    - "25년10월01일" (한글 포함)
    - "2025-10-01" (ISO 형식)
    
    Args:
        s: 정규화할 날짜 문자열
        
    Returns:
        str: ISO 형식 날짜 문자열 (YYYY-MM-DD), 실패 시 빈 문자열
    """
    try:
        # 251001 형태
        if len(s) == 6 and s.isdigit():
            yy = int(s[0:2])
            mm = int(s[2:4])
            dd = int(s[4:6])
            yyyy = 2000 + yy
            return f"{yyyy:04d}-{mm:02d}-{dd:02d}"
        # 25년10월01일 형태
        if '년' in s and '월' in s and '일' in s:
            yy = int(s.split('년')[0][-2:])
            rest = s.split('년')[1]
            mm = int(rest.split('월')[0])
            dd = int(rest.split('월')[1].split('일')[0])
            yyyy = 2000 + yy
            return f"{yyyy:04d}-{mm:02d}-{dd:02d}"
        # ISO 날짜 시도
        return datetime.fromisoformat(s).date().isoformat()
    except Exception:
        return ''

