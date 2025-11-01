"""
이메일 인증 관리자 모듈
이메일 인증 토큰 생성, 검증, 발송을 담당하는 핵심 모듈
"""

import secrets
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from core.db import get_conn
import sqlite3

logger = logging.getLogger(__name__)

class EmailVerificationManager:
    """이메일 인증 관리자 클래스"""
    
    def __init__(self):
        self.logger = logger
        self.token_length = 32
        self.charset = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    
    def _get_setting(self, key: str, default: str = None) -> str:
        """설정값 조회"""
        try:
            with get_conn() as conn:
                conn.row_factory = sqlite3.Row
                setting = conn.execute(
                    "SELECT value FROM settings WHERE key = ?", (key,)
                ).fetchone()
                return setting['value'] if setting else default
        except Exception as e:
            self.logger.error(f"설정 조회 오류 ({key}): {str(e)}")
            return default
    
    def is_verification_enabled(self) -> bool:
        """이메일 인증이 활성화되어 있는지 확인"""
        return self._get_setting('email_verification_enabled', '0') == '1'
    
    def get_expiry_hours(self) -> int:
        """토큰 만료 시간 조회 (시간)"""
        return int(self._get_setting('email_verification_expiry_hours', '24'))
    
    def get_max_attempts(self) -> int:
        """최대 시도 횟수 조회"""
        return int(self._get_setting('email_verification_max_attempts', '3'))
    
    def get_lockout_hours(self) -> int:
        """잠금 시간 조회 (시간)"""
        return int(self._get_setting('email_verification_lockout_hours', '24'))
    
    def generate_secure_token(self) -> str:
        """
        32자리 보안 토큰 생성
        
        보안 특징:
        - 암호학적으로 안전한 랜덤 생성 (secrets 모듈 사용)
        - 32자리 = 62^32 ≈ 2^192 가지 조합 (충분한 엔트로피)
        - 예측 불가능한 패턴
        """
        return ''.join(secrets.choice(self.charset) for _ in range(self.token_length))
    
    def generate_verification_token(self, user_id: int, email: str) -> Tuple[str, str]:
        """
        사용자별 고유 인증 토큰 생성
        
        Args:
            user_id: 사용자 ID
            email: 사용자 이메일
            
        Returns:
            Tuple[str, str]: (토큰, 해시값)
        """
        try:
            # 기본 토큰 생성
            base_token = self.generate_secure_token()
            
            # 사용자별 고유 해시 생성
            user_data = f"{user_id}:{email}:{datetime.now().isoformat()}"
            user_hash = hashlib.sha256(user_data.encode()).hexdigest()[:8]
            
            # 최종 토큰: 기본토큰 + 사용자해시
            final_token = f"{base_token}{user_hash}"
            
            self.logger.info(f"인증 토큰 생성 완료 - 사용자 ID: {user_id}, 토큰 길이: {len(final_token)}")
            
            return final_token, user_hash
            
        except Exception as e:
            self.logger.error(f"토큰 생성 오류 - 사용자 ID: {user_id}, 오류: {str(e)}")
            raise
    
    def save_verification_token(self, user_id: int, email: str, token: str) -> bool:
        """
        인증 토큰을 데이터베이스에 저장
        
        Args:
            user_id: 사용자 ID
            email: 사용자 이메일
            token: 인증 토큰
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            expiry_hours = self.get_expiry_hours()
            expires_at = datetime.now() + timedelta(hours=expiry_hours)
            
            with get_conn() as conn:
                conn.execute(
                    """
                    UPDATE users SET 
                        email_verification_token = ?,
                        email_verification_expires = ?,
                        email_verified = 0
                    WHERE id = ?
                    """,
                    (token, expires_at.isoformat(), user_id)
                )
                conn.commit()
            
            self.logger.info(f"인증 토큰 저장 완료 - 사용자 ID: {user_id}, 만료: {expires_at}")
            return True
            
        except Exception as e:
            self.logger.error(f"토큰 저장 오류 - 사용자 ID: {user_id}, 오류: {str(e)}")
            return False
    
    def verify_token(self, token: str) -> Tuple[bool, str, Optional[int]]:
        """
        인증 토큰 검증
        
        Args:
            token: 검증할 토큰
            
        Returns:
            Tuple[bool, str, Optional[int]]: (유효성, 메시지, 사용자ID)
        """
        try:
            with get_conn() as conn:
                conn.row_factory = sqlite3.Row
                
                # 토큰으로 사용자 조회
                user = conn.execute(
                    """
                    SELECT id, email, email_verification_expires, email_verified
                    FROM users 
                    WHERE email_verification_token = ? AND is_deleted = 0
                    """,
                    (token,)
                ).fetchone()
                
                if not user:
                    self.logger.warning(f"유효하지 않은 토큰으로 인증 시도: {token[:8]}...")
                    return False, "유효하지 않은 인증 토큰입니다", None
                
                # 이미 인증된 사용자 확인
                if user['email_verified']:
                    self.logger.info(f"이미 인증된 사용자 - 사용자 ID: {user['id']}")
                    return False, "이미 인증이 완료된 계정입니다", user['id']
                
                # 토큰 만료 확인
                if user['email_verification_expires']:
                    expires_at = datetime.fromisoformat(user['email_verification_expires'])
                    if datetime.now() > expires_at:
                        self.logger.warning(f"만료된 토큰으로 인증 시도 - 사용자 ID: {user['id']}")
                        return False, "인증 토큰이 만료되었습니다", user['id']
                
                # 인증 성공 처리
                conn.execute(
                    """
                    UPDATE users SET 
                        email_verified = 1,
                        email_verification_token = NULL,
                        email_verification_expires = NULL
                    WHERE id = ?
                    """,
                    (user['id'],)
                )
                
                # 인증 로그 기록
                conn.execute(
                    """
                    INSERT INTO email_verification_logs (user_id, email, token, action)
                    VALUES (?, ?, ?, ?)
                    """,
                    (user['id'], user['email'], token, 'verified')
                )
                
                conn.commit()
                
                self.logger.info(f"이메일 인증 성공 - 사용자 ID: {user['id']}, 이메일: {user['email']}")
                return True, "이메일 인증이 완료되었습니다", user['id']
                
        except Exception as e:
            self.logger.error(f"토큰 검증 오류: {str(e)}")
            return False, "인증 처리 중 오류가 발생했습니다", None
    
    def check_attempt_limit(self, user_id: int, email: str) -> Tuple[bool, str]:
        """
        인증 시도 제한 확인
        
        Args:
            user_id: 사용자 ID
            email: 사용자 이메일
            
        Returns:
            Tuple[bool, str]: (시도 가능 여부, 메시지)
        """
        try:
            max_attempts = self.get_max_attempts()
            lockout_hours = self.get_lockout_hours()
            
            with get_conn() as conn:
                conn.row_factory = sqlite3.Row
                
                # 최근 시도 기록 조회
                attempt = conn.execute(
                    """
                    SELECT attempt_count, last_attempt, locked_until
                    FROM email_verification_attempts
                    WHERE user_id = ? AND email = ?
                    ORDER BY last_attempt DESC
                    LIMIT 1
                    """,
                    (user_id, email)
                ).fetchone()
                
                if not attempt:
                    return True, "시도 가능"
                
                # 잠금 상태 확인
                if attempt['locked_until']:
                    locked_until = datetime.fromisoformat(attempt['locked_until'])
                    if datetime.now() < locked_until:
                        remaining_time = locked_until - datetime.now()
                        hours = int(remaining_time.total_seconds() // 3600)
                        minutes = int((remaining_time.total_seconds() % 3600) // 60)
                        return False, f"인증 시도가 제한되었습니다. {hours}시간 {minutes}분 후 다시 시도해주세요."
                
                # 시도 횟수 확인
                if attempt['attempt_count'] >= max_attempts:
                    # 잠금 설정
                    locked_until = datetime.now() + timedelta(hours=lockout_hours)
                    conn.execute(
                        """
                        UPDATE email_verification_attempts 
                        SET locked_until = ?
                        WHERE user_id = ? AND email = ?
                        """,
                        (locked_until.isoformat(), user_id, email)
                    )
                    conn.commit()
                    
                    return False, f"최대 시도 횟수({max_attempts}회)를 초과했습니다. {lockout_hours}시간 후 다시 시도해주세요."
                
                return True, "시도 가능"
                
        except Exception as e:
            self.logger.error(f"시도 제한 확인 오류: {str(e)}")
            return True, "시도 가능"  # 오류 시 허용
    
    def record_attempt(self, user_id: int, email: str, success: bool) -> None:
        """
        인증 시도 기록
        
        Args:
            user_id: 사용자 ID
            email: 사용자 이메일
            success: 성공 여부
        """
        try:
            with get_conn() as conn:
                conn.row_factory = sqlite3.Row
                
                # 기존 시도 기록 조회
                existing = conn.execute(
                    """
                    SELECT attempt_count FROM email_verification_attempts
                    WHERE user_id = ? AND email = ?
                    ORDER BY last_attempt DESC
                    LIMIT 1
                    """,
                    (user_id, email)
                ).fetchone()
                
                if existing:
                    # 기존 기록 업데이트
                    new_count = existing['attempt_count'] + 1 if not success else 0
                    conn.execute(
                        """
                        UPDATE email_verification_attempts 
                        SET attempt_count = ?, last_attempt = ?
                        WHERE user_id = ? AND email = ?
                        """,
                        (new_count, datetime.now().isoformat(), user_id, email)
                    )
                else:
                    # 새 기록 생성
                    conn.execute(
                        """
                        INSERT INTO email_verification_attempts (user_id, email, attempt_count, last_attempt)
                        VALUES (?, ?, ?, ?)
                        """,
                        (user_id, email, 1 if not success else 0, datetime.now().isoformat())
                    )
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"시도 기록 오류: {str(e)}")
    
    def send_verification_email(self, user_id: int, email: str, token: str) -> bool:
        """
        인증 이메일 발송 (현재는 로그만 기록)
        
        Args:
            user_id: 사용자 ID
            email: 사용자 이메일
            token: 인증 토큰
            
        Returns:
            bool: 발송 성공 여부
        """
        try:
            # 현재는 실제 이메일 발송 대신 로그만 기록
            # 향후 SMTP 서비스 연동 시 실제 발송 구현
            
            verification_url = f"http://localhost:3000/verify-email/{token}"
            
            self.logger.info(f"인증 이메일 발송 시뮬레이션:")
            self.logger.info(f"  수신자: {email}")
            self.logger.info(f"  인증 URL: {verification_url}")
            self.logger.info(f"  토큰: {token[:8]}...")
            
            # 발송 로그 기록
            with get_conn() as conn:
                conn.execute(
                    """
                    INSERT INTO email_verification_logs (user_id, email, token, action)
                    VALUES (?, ?, ?, ?)
                    """,
                    (user_id, email, token, 'sent')
                )
                conn.commit()
            
            return True
            
        except Exception as e:
            self.logger.error(f"이메일 발송 오류: {str(e)}")
            return False
    
    def resend_verification_email(self, user_id: int, email: str) -> Tuple[bool, str]:
        """
        인증 이메일 재발송
        
        Args:
            user_id: 사용자 ID
            email: 사용자 이메일
            
        Returns:
            Tuple[bool, str]: (성공 여부, 메시지)
        """
        try:
            # 시도 제한 확인
            can_attempt, limit_message = self.check_attempt_limit(user_id, email)
            if not can_attempt:
                return False, limit_message
            
            # 새 토큰 생성
            token, _ = self.generate_verification_token(user_id, email)
            
            # 토큰 저장
            if not self.save_verification_token(user_id, email, token):
                return False, "토큰 저장에 실패했습니다"
            
            # 이메일 발송
            if not self.send_verification_email(user_id, email, token):
                return False, "이메일 발송에 실패했습니다"
            
            # 시도 기록
            self.record_attempt(user_id, email, True)
            
            return True, "인증 이메일이 재발송되었습니다"
            
        except Exception as e:
            self.logger.error(f"이메일 재발송 오류: {str(e)}")
            return False, "이메일 재발송 중 오류가 발생했습니다"
    
    def get_verification_stats(self) -> Dict[str, any]:
        """
        이메일 인증 통계 조회
        
        Returns:
            Dict: 인증 통계 정보
        """
        try:
            with get_conn() as conn:
                conn.row_factory = sqlite3.Row
                
                # 전체 사용자 수
                total_users = conn.execute("SELECT COUNT(*) as count FROM users WHERE is_deleted = 0").fetchone()['count']
                
                # 인증된 사용자 수
                verified_users = conn.execute("SELECT COUNT(*) as count FROM users WHERE email_verified = 1 AND is_deleted = 0").fetchone()['count']
                
                # 인증 대기 사용자 수
                pending_users = conn.execute("SELECT COUNT(*) as count FROM users WHERE email_verified = 0 AND email_verification_token IS NOT NULL AND is_deleted = 0").fetchone()['count']
                
                # 최근 24시간 인증 시도 수
                recent_attempts = conn.execute(
                    """
                    SELECT COUNT(*) as count FROM email_verification_logs 
                    WHERE created_at >= datetime('now', '-24 hours')
                    """
                ).fetchone()['count']
                
                return {
                    'total_users': total_users,
                    'verified_users': verified_users,
                    'pending_users': pending_users,
                    'verification_rate': (verified_users / total_users * 100) if total_users > 0 else 0,
                    'recent_attempts': recent_attempts,
                    'is_enabled': self.is_verification_enabled()
                }
                
        except Exception as e:
            self.logger.error(f"통계 조회 오류: {str(e)}")
            return {}


