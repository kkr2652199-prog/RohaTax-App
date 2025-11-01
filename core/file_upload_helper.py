"""
파일 업로드 및 템플릿 카운트 계산 연동 모듈
core/file_parser.py의 템플릿 카운트 계산 기능을 연동
"""

import os
import tempfile
import logging
from typing import Dict, Any
from core.file_parser import FileParser

logger = logging.getLogger(__name__)

def save_uploaded_file(uploaded_file) -> str:
    """
    업로드된 파일을 임시 디렉토리에 저장
    
    Args:
        uploaded_file: Flask uploaded file
        
    Returns:
        str: 저장된 파일 경로
    """
    try:
        # 임시 디렉토리 생성
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, uploaded_file.filename)
        
        # 파일 저장
        uploaded_file.seek(0)
        uploaded_file.save(temp_file_path)
        
        logger.info(f"파일 저장 완료: {temp_file_path}")
        return temp_file_path
        
    except Exception as e:
        logger.error(f"파일 저장 실패: {str(e)}")
        raise

def cleanup_temp_file(file_path: str):
    """
    임시 파일 및 디렉토리 정리
    
    Args:
        file_path: 정리할 파일 경로
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.debug(f"임시 파일 삭제: {file_path}")
        
        # 디렉토리도 삭제 시도
        temp_dir = os.path.dirname(file_path)
        if os.path.exists(temp_dir) and not os.listdir(temp_dir):
            os.rmdir(temp_dir)
            logger.debug(f"임시 디렉토리 삭제: {temp_dir}")
    except Exception as e:
        logger.warning(f"임시 파일 정리 실패: {str(e)}")

def calculate_template_count(file_path: str, industry_type: str = 'delivery') -> int:
    """
    파일에서 템플릿 건수(공급받는자 수) 계산
    
    핵심: 검열 건수(72)가 아닌 실제 템플릿에 기입된 건수(53)만 카운트
    
    Args:
        file_path: 파일 경로
        industry_type: 업종 타입 (기본값: 'delivery', 현재는 사용 안함)
        
    Returns:
        int: 실제 템플릿 기입 건수 (검열/필터링/가족 통합 후)
    """
    try:
        logger.info(f"템플릿 건수 계산 시작: 파일={os.path.basename(file_path)}, 업종={industry_type}")
        
        # 파일 파싱
        from core.file_parser import FileParser
        from core.recipient_extractor import RecipientExtractor
        
        file_parser = FileParser()
        parsed_data = file_parser.parse_file(file_path)
        
        if not parsed_data or parsed_data.get('parsing_status') != 'success':
            logger.warning("파일 파싱 실패 또는 데이터 없음")
            return 0
        
        # 실제 템플릿에 기입될 건수 계산
        # recipients는 검열/필터링 후 최종적으로 템플릿에 기입되는 데이터
        recipient_extractor = RecipientExtractor()
        recipients = recipient_extractor.extract_recipients(parsed_data)
        
        # 실제 템플릿 기입 건수 = 검열/필터링 후 남은 데이터 건수
        actual_template_count = len(recipients)
        
        logger.info(f"검열 전 건수: {parsed_data.get('total_rows', 0)}건")
        logger.info(f"실제 템플릿 기입 건수: {actual_template_count}건")
        
        return actual_template_count
        
    except Exception as e:
        logger.error(f"템플릿 건수 계산 중 오류 발생: {str(e)}")
        return 0
