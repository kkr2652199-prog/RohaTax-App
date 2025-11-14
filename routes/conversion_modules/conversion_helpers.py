"""
변환 관련 헬퍼 함수 모듈
공통으로 사용되는 유틸리티 함수들
"""

import os
import tempfile
import logging
import json
from datetime import datetime
from flask import request
from core.file_parser import FileParser
from core.responses import error

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


def validate_and_extract_params(request):
    """
    변환 요청의 파라미터를 추출하고 유효성을 검사하는 함수
    
    Args:
        request: Flask request 객체
        
    Returns:
        tuple: (success: bool, result: dict or error_response)
               - success=True: result는 추출된 파라미터 딕셔너리
               - success=False: result는 에러 응답 객체
    """
    # CSRF 토큰 검증
    csrf_token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
    if not csrf_token:
        return False, error('보안 토큰이 없습니다. 다시 시도해주세요.', status=403)
    
    # Form Data에서 파라미터 추출
    template_id = (request.form.get('template_id') or 'hometax_official').strip()
    issue_date_raw = (request.form.get('issue_date') or '').strip()
    file_name = (request.form.get('file_name') or '').strip()
    industry_type = (request.form.get('industry_type') or 'delivery').strip()
    guidelines_json = request.form.get('guidelines', '{}')
    
    # 업종별 지침 파싱
    try:
        guidelines = json.loads(guidelines_json)
        logger.info(f"활성화된 지침: {guidelines.get('name', 'Unknown')}")
    except:
        guidelines = {}
    
    # 파일 업로드 확인
    if 'file' not in request.files:
        return False, error('배달대행사 정산서 파일을 업로드해주세요', status=400)
    
    uploaded_file = request.files['file']
    if uploaded_file.filename == '':
        return False, error('파일이 선택되지 않았습니다', status=400)
    
    # 필수 파라미터 검증
    if not issue_date_raw:
        return False, error('전자세금일자를 선택하세요', status=400)
    if not file_name:
        return False, error('파일명을 입력하세요', status=400)
    
    # issue_date 정규화: "25년10월01일" 또는 "251001" 또는 ISO 모두 수용 → ISO(YYYY-MM-DD)
    issue_date = normalize_issue_date(issue_date_raw)
    if not issue_date:
        return False, error('전자세금일자 형식이 올바르지 않습니다', status=400)
    
    # 성공 시 추출된 파라미터 반환
    return True, {
        'template_id': template_id,
        'issue_date': issue_date,
        'issue_date_raw': issue_date_raw,
        'file_name': file_name,
        'industry_type': industry_type,
        'guidelines': guidelines,
        'uploaded_file': uploaded_file
    }

