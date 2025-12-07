"""
토큰 관리 유틸리티
만료된 토큰 자동 회수 시스템 (Token Reaper)
"""
import sqlite3
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import json

from core.db import get_conn_optimized as get_conn

logger = logging.getLogger(__name__)


class TokenManager:
    """토큰 관리 클래스"""
    
    def __init__(self):
        """TokenManager 초기화"""
        self.logger = logger
    
    def check_and_deduct_expired_tokens(self, user_id: int) -> Dict[str, Any]:
        """
        만료된 토큰을 찾아서 자동으로 차감하는 메서드 (The Reaper)
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            Dict: 처리 결과
            {
                'processed': bool,  # 처리 여부
                'deducted_amount': int,  # 차감된 토큰 수
                'expired_count': int  # 만료된 기록 수
            }
        """
        try:
            with get_conn() as conn:
                conn.row_factory = sqlite3.Row
                
                # 트랜잭션 시작
                conn.execute("BEGIN TRANSACTION")
                
                try:
                    # 1. 만료된 토큰 기록 찾기
                    # expires_at < NOW 이고 is_expired_processed = 0인 항목
                    # ⚠️ 중요: 무료 토큰(source_type='FREE')만 만료 처리
                    # 유료 토큰(source_type='PAID')은 만료일이 지나도 절대 회수하지 않음
                    expired_records = conn.execute(
                        """
                        SELECT id, amount, expires_at, created_at, source_type
                        FROM token_history
                        WHERE user_id = ?
                          AND expires_at IS NOT NULL
                          AND expires_at < datetime('now', 'localtime')
                          AND COALESCE(is_expired_processed, 0) = 0
                          AND change_type = 'grant'
                          AND COALESCE(source_type, 'PAID') = 'FREE'  -- 무료 토큰만 만료 처리
                        ORDER BY created_at ASC
                        """,
                        (user_id,)
                    ).fetchall()
                    
                    if not expired_records:
                        # 만료된 토큰이 없으면 처리 없음
                        conn.commit()
                        return {
                            'processed': False,
                            'deducted_amount': 0,
                            'expired_count': 0
                        }
                    
                    # 2. 현재 유저의 token_balance 조회
                    user_row = conn.execute(
                        """
                        SELECT COALESCE(token_balance, 0) AS token_balance, username
                        FROM users
                        WHERE id = ?
                        """,
                        (user_id,)
                    ).fetchone()
                    
                    if not user_row:
                        logger.warning(f"사용자를 찾을 수 없습니다: ID {user_id}")
                        conn.rollback()
                        return {
                            'processed': False,
                            'deducted_amount': 0,
                            'expired_count': 0
                        }
                    
                    current_balance = user_row['token_balance'] or 0
                    username = user_row['username']
                    
                    # 3. 차감 계산 및 집행
                    total_deducted = 0
                    processed_count = 0
                    
                    for record in expired_records:
                        original_amount = record['amount']
                        expires_at = record['expires_at']
                        record_id = record['id']
                        
                        # 차감량 계산: min(원래_지급량, 현재_잔액)
                        deduct_amount = min(original_amount, current_balance)
                        
                        if deduct_amount > 0:
                            # 토큰 차감
                            new_balance = current_balance - deduct_amount
                            conn.execute(
                                """
                                UPDATE users
                                SET token_balance = ?, updated_at = datetime('now', 'localtime')
                                WHERE id = ?
                                """,
                                (new_balance, user_id)
                            )
                            
                            # token_history에 차감 기록
                            expire_meta = json.dumps({
                                'reason': 'token_expired',
                                'original_grant_id': record_id,
                                'original_amount': original_amount,
                                'expires_at': expires_at,
                                'deducted_amount': deduct_amount
                            }, ensure_ascii=False)
                            
                            conn.execute(
                                """
                                INSERT INTO token_history
                                (user_id, changed_by, amount, change_type, meta, created_at)
                                VALUES (?, ?, ?, 'expire', ?, datetime('now', 'localtime'))
                                """,
                                (
                                    user_id,
                                    user_id,  # 시스템이 자동 처리
                                    -deduct_amount,  # 음수로 기록
                                    expire_meta
                                )
                            )
                            
                            total_deducted += deduct_amount
                            current_balance = new_balance  # 다음 루프를 위해 업데이트
                            
                            logger.info(
                                f"만료 토큰 차감: 사용자 ID {user_id} ({username}), "
                                f"원래 지급량 {original_amount}, 차감량 {deduct_amount}, "
                                f"만료일 {expires_at}, 새 잔액 {new_balance}"
                            )
                        
                        # 원본 기록의 is_expired_processed를 1로 업데이트 (중복 처리 방지)
                        conn.execute(
                            """
                            UPDATE token_history
                            SET is_expired_processed = 1
                            WHERE id = ?
                            """,
                            (record_id,)
                        )
                        
                        processed_count += 1
                    
                    # activity_logs에 토큰 만료 기록 추가
                    if total_deducted > 0:
                        from core.activity_service import record_activity
                        cursor = conn.cursor()
                        
                        # 만료 전 잔액 (차감 전)
                        balance_before = current_balance + total_deducted
                        # 만료 후 잔액 (차감 후)
                        balance_after = current_balance
                        
                        # 사용자 plan_type 조회
                        user_plan = conn.execute(
                            "SELECT plan_type FROM users WHERE id = ?",
                            (user_id,)
                        ).fetchone()
                        plan_type = user_plan['plan_type'] if user_plan else 'free'
                        
                        activity_data = {
                            'user_id': user_id,
                            'performed_by_id': user_id,  # 시스템 자동 처리
                            'performed_by_type': 'system',
                            'activity_type': 'TOKEN_EXPIRED',
                            'details': {
                                'type': 'free_token_expiration',  # 무료 토큰 만료 명시
                                'reason': '무료 토큰 만료로 인한 자동 회수',
                                'expired_count': processed_count,
                                'total_deducted': total_deducted,
                                'note': '유료로 구매한 토큰은 만료일이 지나도 유지됩니다'
                            },
                            'token_change': -total_deducted,
                            'potential_cost': 0,
                            'token_balance_before': balance_before,
                            'token_balance_after': balance_after,
                            'user_plan_snapshot': {
                                'plan_type': plan_type,
                                'username': username
                            }
                        }
                        
                        try:
                            record_activity(cursor, activity_data)
                        except Exception as e:
                            logger.error(f"activity_logs 기록 중 오류: {str(e)}")
                            # activity_logs 기록 실패해도 토큰 차감은 계속 진행
                    
                    conn.commit()
                    
                    if total_deducted > 0:
                        logger.info(
                            f"토큰 만료 처리 완료: 사용자 ID {user_id} ({username}), "
                            f"처리된 기록 {processed_count}건, 총 차감량 {total_deducted}"
                        )
                    
                    return {
                        'processed': True,
                        'deducted_amount': total_deducted,
                        'expired_count': processed_count
                    }
                    
                except Exception as e:
                    conn.rollback()
                    logger.error(f"만료 토큰 처리 중 오류 발생 (user_id: {user_id}): {str(e)}")
                    raise
                    
        except Exception as e:
            logger.error(f"만료 토큰 확인 중 오류 발생 (user_id: {user_id}): {str(e)}")
            return {
                'processed': False,
                'deducted_amount': 0,
                'expired_count': 0
            }

