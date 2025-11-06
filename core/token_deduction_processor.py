"""
토큰 차감 로직 연동 모듈
routes/conversion.py의 토큰 차감 기능을 연동 모듈로 분리
"""

import logging
import sqlite3
from typing import Dict, Any, Optional

from core.db import get_conn_optimized as get_conn
from core.subscription_utils import get_plan_display_label
import os
import json

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
            
            total_recipients = conversion_result.get('total_recipients')

            if total_recipients in (None, 0):
                detailed_stats = conversion_result.get('detailed_stats') or {}
                for key in ('total_recipients', 'recipient_count', 'recipients_count'):
                    if detailed_stats.get(key) not in (None, 0):
                        total_recipients = detailed_stats.get(key)
                        break

            if total_recipients in (None, 0):
                recipients = conversion_result.get('recipients')
                if isinstance(recipients, (list, tuple, set)):
                    total_recipients = len(recipients)

            total_recipients = int(total_recipients or 0)

            self.logger.info(f"계산된 템플릿 건수: {total_recipients}")

            return total_recipients
            
        except Exception as e:
            self.logger.error(f"템플릿 건수 계산 중 오류 발생: {str(e)}")
            return 0
    
    def get_initial_tokens_used(self, user_id: int) -> int:
        """변환 전 토큰 사용량 조회"""
        try:
            with get_conn() as conn:
                user = conn.execute(
                    "SELECT COALESCE(tokens_used, 0) as tokens_used FROM users WHERE id = ?",
                    (user_id,)
                ).fetchone()
                if not user:
                    self.logger.error(f"사용자 ID {user_id}를 찾을 수 없음")
                    return 0
                return user['tokens_used'] or 0
        except Exception as e:
            self.logger.error(f"초기 토큰 사용량 조회 중 오류: {str(e)}")
            return 0
    
    def deduct_tokens(
        self,
        user_id: int,
        usage_amount: int,
        is_unlimited: bool,
        filename: str | None = None,
        customer_name: str | None = None,
        recipient_count: int = 0,
    ) -> Dict[str, Any]:
        """
        토큰 차감 실행
        
        Args:
            user_id: 사용자 ID
            usage_amount: 실제 차감할 토큰 수(무제한은 0)
            is_unlimited: 무제한 사용자 여부
            filename: 변환에 사용된 파일명
            customer_name: 고객명(선택)
            
        Returns:
            Dict[str, Any]: 처리 결과 (성공 여부, 잔여 토큰 등)
        """
        try:
            with get_conn() as conn:
                conn.row_factory = sqlite3.Row
                user = conn.execute(
                    "SELECT plan_type, token_balance, COALESCE(tokens_used,0) as tokens_used FROM users WHERE id = ?",
                    (user_id,)
                ).fetchone()
                if not user:
                    self.logger.error(f"사용자 ID {user_id} 조회 실패")
                    return {'success': False, 'error': 'USER_NOT_FOUND'}

                plan_type = user['plan_type'] or 'free'
                plan_display = get_plan_display_label(plan_type)
                token_balance = user['token_balance'] or 0
                current_used = user['tokens_used'] or 0
                available_before = token_balance - current_used

                actual_usage = 0 if is_unlimited else int(max(0, usage_amount))

                if not is_unlimited and actual_usage > available_before:
                    self.logger.warning(
                        "사용 가능한 토큰 부족: user=%s, 요청=%s, 가용=%s",
                        user_id,
                        actual_usage,
                        available_before,
                    )

                new_used = current_used + actual_usage
                available_after = token_balance - new_used if not is_unlimited else available_before

                if not is_unlimited and actual_usage > 0:
                    try:
                        conn.execute(
                            "UPDATE users SET tokens_used = ?, updated_at = datetime('now') WHERE id = ?",
                            (new_used, user_id)
                        )
                    except sqlite3.OperationalError:
                        conn.execute(
                            "UPDATE users SET tokens_used = ? WHERE id = ?",
                            (new_used, user_id)
                        )

                meta = {
                    'filename': os.path.basename(filename) if filename else '',
                    'customer_name': customer_name or '',
                    'recipient_count': int(recipient_count or 0),
                    'plan_type': plan_type,
                    'plan_display': plan_display,
                    'is_unlimited': bool(is_unlimited),
                    'balance_after': available_after,
                    'tokens_used_after': new_used,
                }

                change_amount = -actual_usage if actual_usage > 0 else 0
                conn.execute(
                    """
                    INSERT INTO token_history (user_id, changed_by, amount, change_type, meta, created_at)
                    VALUES (?, ?, ?, 'use', ?, datetime('now'))
                    """,
                    (
                        user_id,
                        user_id,
                        change_amount,
                        json.dumps(meta, ensure_ascii=False),
                    ),
                )

                conn.commit()

                self.logger.info(
                    "토큰 처리 완료 | user=%s, plan=%s, unlimited=%s, 사용=%s, 누적사용=%s, 잔여=%s",
                    user_id,
                    plan_type,
                    is_unlimited,
                    actual_usage,
                    new_used,
                    available_after,
                )
                return {
                    'success': True,
                    'is_unlimited': bool(is_unlimited),
                    'tokens_used_after': new_used,
                    'available_tokens_after': available_after,
                    'total_granted': token_balance,
                    'plan_type': plan_type,
                    'plan_display': plan_display,
                    'change_amount': change_amount,
                    'actual_usage': actual_usage,
                }
                
        except Exception as e:
            self.logger.error(f"토큰 차감 중 오류 발생: {str(e)}")
            return {'success': False, 'error': str(e)}
    
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
            
            # 파일명 추출
            filename = None
            try:
                files = conversion_result.get('files') or []
                if files and isinstance(files, list):
                    filename = os.path.basename(files[0])
            except Exception:
                filename = None

            customer_name = conversion_result.get('customer_name') or None

            target_usage = 0 if is_unlimited else int(max(0, actual_recipient_count))

            deduction_result = self.deduct_tokens(
                user_id=user_id,
                usage_amount=target_usage,
                is_unlimited=is_unlimited,
                filename=filename,
                customer_name=customer_name,
                recipient_count=actual_recipient_count,
            )

            if not deduction_result.get('success'):
                return {
                    'success': False,
                    'deducted': False,
                    'message': f"토큰 처리 실패: {deduction_result.get('error', 'UNKNOWN_ERROR')}",
                    'recipient_count': actual_recipient_count
                }

            message = (
                f"무제한(GOLD) 사용자: 차감 없음, 활동 기록 완료 (템플릿 {actual_recipient_count}개)"
                if is_unlimited
                else f"실제 템플릿 {actual_recipient_count}개 생성, 토큰 {deduction_result.get('actual_usage', 0)}개 차감 및 기록 완료"
            )

            return {
                'success': True,
                'deducted': not is_unlimited and deduction_result.get('actual_usage', 0) > 0,
                'message': message,
                'recipient_count': actual_recipient_count,
                'tokens_deducted': deduction_result.get('actual_usage', 0),
                'tokens_used_after': deduction_result.get('tokens_used_after'),
                'available_tokens_after': deduction_result.get('available_tokens_after'),
                'total_granted': deduction_result.get('total_granted'),
                'plan_type': deduction_result.get('plan_type'),
                'plan_display': deduction_result.get('plan_display'),
            }
                
        except Exception as e:
            self.logger.error(f"토큰 차감 프로세스 중 오류 발생: {str(e)}")
            return {
                'success': False,
                'deducted': False,
                'message': f"오류 발생: {str(e)}",
                'recipient_count': 0
            }

