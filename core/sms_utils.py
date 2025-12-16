"""
가상 SMS 인증 유틸리티
실제 SMS 발송 대신 서버 로그에 인증번호를 출력하는 시뮬레이션 방식
"""
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple
import sqlite3

logger = logging.getLogger(__name__)


def generate_verification_code() -> str:
    """
    6자리 랜덤 숫자 인증번호 생성
    
    Returns:
        str: 6자리 숫자 문자열 (예: "123456")
    """
    return ''.join([str(secrets.randbelow(10)) for _ in range(6)])


def generate_code_expiry(minutes: int = 5) -> str:
    """
    인증번호 만료 시간 생성 (기본 5분)
    
    Args:
        minutes: 만료 시간 (분)
        
    Returns:
        str: ISO 형식의 만료 시간 문자열
    """
    expiry = datetime.now() + timedelta(minutes=minutes)
    return expiry.isoformat()


def is_code_expired(expires_at: str) -> bool:
    """
    인증번호가 만료되었는지 확인
    
    Args:
        expires_at: 만료 시간 (ISO 형식)
        
    Returns:
        bool: 만료 여부
    """
    try:
        expiry = datetime.fromisoformat(expires_at)
        return datetime.now() > expiry
    except Exception as e:
        logger.error(f"인증번호 만료 확인 중 오류 발생: {e}")
        return True


def send_verification_code(phone: str) -> Tuple[bool, Optional[str]]:
    """
    가상 SMS 인증번호 발송 (서버 로그 출력)
    
    Args:
        phone: 휴대폰 번호 (예: "010-1234-5678")
        
    Returns:
        Tuple[bool, Optional[str]]: (성공 여부, 인증번호)
    """
    from core.db import get_conn_optimized as get_conn
    
    try:
        # 휴대폰 번호 정규화 (하이픈과 공백 모두 제거)
        normalized_phone = phone.replace('-', '').replace(' ', '').strip()
        
        # 인증번호 생성
        code = generate_verification_code()
        expires_at = generate_code_expiry(minutes=5)
        
        logger.info(f"가상 SMS 인증번호 발송 - 원본 번호: {phone}, 정규화된 번호: {normalized_phone}")
        
        with get_conn() as conn:
            # 기존 미인증 코드 무효화 (같은 번호의 이전 코드들)
            conn.execute(
                """
                UPDATE sms_verification_codes 
                SET is_verified = -1 
                WHERE phone_number = ? AND is_verified = 0 AND expires_at > datetime('now')
                """,
                (normalized_phone,)
            )
            
            # 새 인증번호 저장
            conn.execute(
                """
                INSERT INTO sms_verification_codes (phone_number, code, expires_at) 
                VALUES (?, ?, ?)
                """,
                (normalized_phone, code, expires_at)
            )
            conn.commit()
        
        # 가상 SMS: 서버 로그에 출력 (버퍼링 없이 즉시 출력)
        print(f"\n{'=' * 60}", flush=True)
        print(f"[가상 SMS] {phone} 님의 인증번호: {code}", flush=True)
        print(f"[가상 SMS] 인증번호는 5분간 유효합니다.", flush=True)
        print(f"{'=' * 60}\n", flush=True)
        logger.info(f"가상 SMS 인증번호 발송 - 전화번호: {phone}, 인증번호: {code}")
        
        return True, code
        
    except Exception as e:
        import traceback
        logger.error(f"가상 SMS 인증번호 발송 중 오류 발생: {e}")
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        return False, None


def verify_code(phone: str, input_code: str) -> Tuple[bool, Optional[str]]:
    """
    인증번호 검증
    
    Args:
        phone: 휴대폰 번호
        input_code: 사용자가 입력한 인증번호
        
    Returns:
        Tuple[bool, Optional[str]]: (검증 성공 여부, 에러 메시지)
    """
    from core.db import get_conn_optimized as get_conn
    
    try:
        # 휴대폰 번호 정규화 (하이픈과 공백 모두 제거)
        clean_phone = phone.replace('-', '').replace(' ', '').strip()
        
        logger.info(f"SMS 인증번호 검증 시도 - 입력된 번호: {phone} (정제후: {clean_phone}), 입력된 코드: {input_code}")
        
        with get_conn() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT id, code, expires_at, is_verified 
                FROM sms_verification_codes 
                WHERE phone_number = ? AND is_verified = 0
                ORDER BY created_at DESC 
                LIMIT 1
                """,
                (clean_phone,)
            ).fetchone()
            
            if not row:
                print(f"[검증 실패] 입력된 번호: {phone} (정제후: {clean_phone}), 입력된 코드: {input_code}")
                print(f"[검증 실패] DB에서 인증번호를 찾을 수 없습니다.")
                logger.warning(f"SMS 인증번호 검증 실패 - 인증번호를 찾을 수 없음: {phone} (정제후: {clean_phone})")
                return False, "인증번호를 찾을 수 없습니다. 다시 요청해주세요."
            
            # 이미 사용된 코드인지 확인
            if row['is_verified'] != 0:
                print(f"[검증 실패] 입력된 번호: {phone} (정제후: {clean_phone}), 입력된 코드: {input_code}")
                print(f"[검증 실패] 이미 사용된 인증번호입니다.")
                logger.warning(f"SMS 인증번호 검증 실패 - 이미 사용된 코드: {phone}")
                return False, "이미 사용된 인증번호입니다."
            
            # 만료 확인
            if is_code_expired(row['expires_at']):
                print(f"[검증 실패] 입력된 번호: {phone} (정제후: {clean_phone}), 입력된 코드: {input_code}")
                print(f"[검증 실패] 인증번호가 만료되었습니다. (만료시간: {row['expires_at']})")
                logger.warning(f"SMS 인증번호 검증 실패 - 만료됨: {phone}")
                return False, "인증번호가 만료되었습니다. 다시 요청해주세요."
            
            # 인증번호 일치 확인
            stored_code = row['code']
            if stored_code != input_code:
                print(f"[검증 실패] 입력된 번호: {phone} (정제후: {clean_phone}), 입력된 코드: {input_code}")
                print(f"[검증 실패] 저장된 코드: {stored_code}, 입력된 코드: {input_code} (일치하지 않음)")
                logger.warning(f"SMS 인증번호 검증 실패 - 코드 불일치: {phone}, 저장된 코드: {stored_code}, 입력된 코드: {input_code}")
                return False, "인증번호가 일치하지 않습니다."
            
            # 인증 성공: is_verified를 1로 업데이트
            conn.execute(
                """
                UPDATE sms_verification_codes 
                SET is_verified = 1, verified_at = datetime('now') 
                WHERE id = ?
                """,
                (row['id'],)
            )
            conn.commit()
            
            print(f"[검증 성공] 입력된 번호: {phone} (정제후: {clean_phone}), 입력된 코드: {input_code}")
            logger.info(f"SMS 인증번호 검증 성공 - 전화번호: {phone} (정제후: {clean_phone})")
            return True, None
            
    except Exception as e:
        import traceback
        print(f"[검증 실패] 입력된 번호: {phone}, 입력된 코드: {input_code}")
        print(f"[검증 실패] 예외 발생: {e}")
        logger.error(f"SMS 인증번호 검증 중 오류 발생: {e}")
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        return False, f"인증번호 검증 중 오류가 발생했습니다: {str(e)}"


def get_user_by_phone(phone: str) -> Optional[dict]:
    """
    휴대폰 번호로 사용자 정보 조회
    
    Args:
        phone: 휴대폰 번호
        
    Returns:
        Optional[dict]: 사용자 정보 (없으면 None)
    """
    from core.db import get_conn_optimized as get_conn
    
    try:
        # 휴대폰 번호 정규화 (하이픈과 공백 모두 제거)
        normalized_phone = phone.replace('-', '').replace(' ', '').strip()
        
        with get_conn() as conn:
            conn.row_factory = sqlite3.Row
            user = conn.execute(
                """
                SELECT id, username, email, phone 
                FROM users 
                WHERE REPLACE(REPLACE(phone, '-', ''), ' ', '') = ? AND is_deleted = 0
                """,
                (normalized_phone,)
            ).fetchone()
            
            if user:
                return dict(user)
            return None
            
    except Exception as e:
        import traceback
        logger.error(f"휴대폰 번호로 사용자 조회 중 오류 발생: {e}")
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        return None

