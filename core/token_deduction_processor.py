"""
토큰 차감 로직 연동 모듈
routes/conversion.py의 토큰 차감 기능을 연동 모듈로 분리
"""

import logging
import sqlite3
from typing import Dict, Any, Optional

from core.db import get_conn_optimized

logger = logging.getLogger(__name__)


class TokenDeductionProcessor:
    """토큰 차감 처리 연동 클래스"""
    
    def __init__(self):
        """토큰 차감 프로세서 초기화"""
        self.logger = logger
        self.module_name = "TokenDeductionProcessor"
        self.version = "1.0.0"
        
    def calculate_template_count(self, conversion_result: Dict[str, Any]) -> int:
        """
        변환 결과에서 템플릿 건수 계산
        
        Args:
            conversion_result: 변환 결과 딕셔너리
            
        Returns:
            int: 템플릿 건수 (공급받는자 수)
        """
        try:
            self.logger.info(f"변환 결과 타입: {type(conversion_result)}")
            
            if not isinstance(conversion_result, dict):
                self.logger.warning("변환 결과가 딕셔너리가 아닙니다")
                return 0
            
            self.logger.info(f"변환 결과 키: {list(conversion_result.keys())}")
            
            # total_recipients 키로 템플릿 건수 확인
            total_recipients = conversion_result.get('total_recipients', 0)
            
            self.logger.info(f"계산된 템플릿 건수: {total_recipients}")
            
            return total_recipients
            
        except Exception as e:
            self.logger.error(f"템플릿 건수 계산 중 오류 발생: {str(e)}")
            return 0
    
    def get_initial_tokens_used(self, user_id: int) -> int:
        """
        변환 전 토큰 사용량 조회
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            int: 변환 전 토큰 사용량
        """
        try:
            with get_conn_optimized() as conn:
                # row_factory는 이미 get_conn_optimized()에서 설정됨
                user = conn.execute(
                    "SELECT COALESCE(tokens_used, 0) as tokens_used FROM users WHERE id = ?",
                    (user_id,)
                ).fetchone()
                
                if not user:
                    self.logger.error(f"사용자 ID {user_id}를 찾을 수 없음")
                    return 0
                
                initial_tokens_used = user['tokens_used'] or 0
                self.logger.info(f"초기 토큰 사용량: {initial_tokens_used}")
                
                return initial_tokens_used
                
        except Exception as e:
            self.logger.error(f"초기 토큰 사용량 조회 중 오류: {str(e)}")
            return 0
    
    def deduct_tokens(self, user_id: int, initial_tokens_used: int, actual_recipient_count: int) -> bool:
        """
        토큰 차감 실행
        
        Args:
            user_id: 사용자 ID
            initial_tokens_used: 변환 전 토큰 사용량
            actual_recipient_count: 실제 생성된 템플릿 수
            
        Returns:
            bool: 차감 성공 여부
        """
        try:
            # 최종 토큰 사용량 계산
            final_tokens_used = initial_tokens_used + actual_recipient_count
            
            with get_conn_optimized() as conn:
                conn.execute(
                    "UPDATE users SET tokens_used = ? WHERE id = ?",
                    (final_tokens_used, user_id)
                )
                # commit은 get_conn_optimized()가 자동 처리
                
                self.logger.info(f"토큰 차감 완료: 템플릿 {actual_recipient_count}개, 총 사용량 {final_tokens_used}개")
                return True
                
        except Exception as e:
            self.logger.error(f"토큰 차감 중 오류 발생: {str(e)}")
            return False
    
    def process_token_deduction(self, user_id: int, is_unlimited: bool, conversion_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        토큰 차감 프로세스 통합 실행
        
        Args:
            user_id: 사용자 ID
            is_unlimited: 무제한 사용자 여부
            conversion_result: 변환 결과
            
        Returns:
            Dict: 처리 결과 (차감 여부, 메시지 등)
        """
        try:
            # 1. 템플릿 건수 계산
            actual_recipient_count = self.calculate_template_count(conversion_result)
            
            # 2. 무제한 사용자는 차감 없음
            if is_unlimited:
                return {
                    'success': True,
                    'deducted': False,
                    'message': f"무제한 VIP 사용자: 토큰 차감 없음 (템플릿 {actual_recipient_count}개 생성)",
                    'recipient_count': actual_recipient_count
                }
            
            # 3. 초기 토큰 사용량 조회
            initial_tokens_used = self.get_initial_tokens_used(user_id)
            
            # 4. 토큰 차감 실행
            success = self.deduct_tokens(user_id, initial_tokens_used, actual_recipient_count)
            
            if success:
                return {
                    'success': True,
                    'deducted': True,
                    'message': f"실제 템플릿 {actual_recipient_count}개 생성, 토큰 {actual_recipient_count}개 정확히 차감",
                    'recipient_count': actual_recipient_count,
                    'tokens_deducted': actual_recipient_count
                }
            else:
                return {
                    'success': False,
                    'deducted': False,
                    'message': f"토큰 차감 실패",
                    'recipient_count': actual_recipient_count
                }
                
        except Exception as e:
            self.logger.error(f"토큰 차감 프로세스 중 오류 발생: {str(e)}")
            return {
                'success': False,
                'deducted': False,
                'message': f"오류 발생: {str(e)}",
                'recipient_count': 0
            }

