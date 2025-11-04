"""
구독 관리 유틸리티
VIP/VIP-Plus/GoldVIP 요금제 및 유저 구독 관리
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
import sqlite3
import json

from core.db import get_conn_optimized

logger = logging.getLogger(__name__)


def get_user_subscription(user_id: int) -> Optional[Dict[str, Any]]:
    """
    사용자의 현재 활성 구독 정보 조회 (users 테이블의 plan_type 기반)
    
    Args:
        user_id: 사용자 ID
        
    Returns:
        Optional[Dict]: 구독 정보 또는 None
        {
            'plan_type': 'gold-vip',
            'display_name': 'Gold VIP',
            'is_unlimited': 1,
            'remaining_tokens': -1,
            'status': 'active'
        }
    """
    with get_conn_optimized() as conn:
        # row_factory는 이미 get_conn_optimized()에서 설정됨
        row = conn.execute(
            """
            SELECT id, plan_type, token_balance, tokens_used, is_active
            FROM users
            WHERE id = ? AND is_deleted = 0
            """,
            (user_id,)
        ).fetchone()
        
        if not row:
            logger.warning(f"사용자 조회 실패 - ID: {user_id}")
            return None
        
        plan_type = row['plan_type'] or 'free'
        is_active = row['is_active'] if row['is_active'] is not None else 1
        
        # 플랜별 매핑
        plan_mapping = {
            'free': {'display_name': '무료', 'is_unlimited': 0, 'tokens': 50},
            'vip': {'display_name': 'VIP', 'is_unlimited': 0, 'tokens': 50},
            'premium-vip': {'display_name': 'Premium VIP', 'is_unlimited': 0, 'tokens': 300},
            'gold-vip': {'display_name': 'Gold VIP', 'is_unlimited': 1, 'tokens': -1}
        }
        
        plan_info = plan_mapping.get(plan_type, plan_mapping['free'])
        
        subscription = {
            'plan_type': plan_type,
            'display_name': plan_info['display_name'],
            'is_unlimited': plan_info['is_unlimited'],
            'remaining_tokens': plan_info['tokens'],
            'status': 'active' if is_active else 'inactive'
        }
        
        logger.info(f"사용자 플랜 조회 - ID: {user_id}, 플랜: {plan_type}, 무제한: {plan_info['is_unlimited']}")
        return subscription


def is_unlimited_user(user_id: int) -> bool:
    """
    사용자가 무제한 토큰 사용 가능한지 확인
    
    Args:
        user_id: 사용자 ID
        
    Returns:
        bool: 무제한 사용 가능 여부 (Gold VIP만 True)
    """
    try:
        subscription = get_user_subscription(user_id)
        
        if not subscription:
            return False
        
        # gold-vip만 무제한 사용 가능
        return subscription.get('plan_type') == 'gold-vip'
        
    except Exception as e:
        logger.error(f"무제한 사용자 확인 중 오류: {str(e)}")
        return False


def get_all_subscription_plans() -> List[Dict[str, Any]]:
    """
    모든 활성 구독 플랜 조회 (관리자용)
    
    Returns:
        List[Dict]: 구독 플랜 리스트
    """
    try:
        with get_conn() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT id, plan_name, display_name, price, token_amount, 
                       is_unlimited, expiry_days, features, is_active,
                       created_at, updated_at
                FROM subscription_plans
                WHERE is_active = 1
                ORDER BY price ASC
                """
            ).fetchall()
            
            plans = []
            for row in rows:
                plan_dict = dict(row)
                # features JSON 파싱 시도
                try:
                    if plan_dict['features']:
                        plan_dict['features'] = json.loads(plan_dict['features'])
                    else:
                        plan_dict['features'] = []
                except:
                    plan_dict['features'] = []
                
                plans.append(plan_dict)
            
            logger.info(f"구독 플랜 조회: {len(plans)}개")
            return plans
            
    except Exception as e:
        logger.error(f"구독 플랜 조회 중 오류: {str(e)}")
        return []


def purchase_subscription(user_id: int, plan_id: int) -> Dict[str, Any]:
    """
    구독 플랜 구매 (결제 완료 후 호출)
    
    Args:
        user_id: 사용자 ID
        plan_id: 구독 플랜 ID
        
    Returns:
        Dict: 구매 결과
        {
            'success': True/False,
            'subscription_id': int,
            'expires_at': '2025-11-26T00:00:00',
            'message': '구독이 시작되었습니다'
        }
    """
    try:
        with get_conn() as conn:
            conn.row_factory = sqlite3.Row
            
            # 구독 플랜 정보 조회
            plan = conn.execute(
                "SELECT * FROM subscription_plans WHERE id = ? AND is_active = 1",
                (plan_id,)
            ).fetchone()
            
            if not plan:
                return {
                    'success': False,
                    'message': '구독 플랜을 찾을 수 없습니다'
                }
            
            # 유저 정보 조회
            user = conn.execute(
                "SELECT plan_type FROM users WHERE id = ?",
                (user_id,)
            ).fetchone()
            
            if not user:
                return {
                    'success': False,
                    'message': '사용자를 찾을 수 없습니다'
                }
            
            # 만료 시간 계산
            expires_at = (datetime.now() + timedelta(days=plan['expiry_days'])).isoformat()
            
            # 기존 구독 비활성화
            conn.execute(
                "UPDATE user_subscriptions SET status = 'cancelled' WHERE user_id = ? AND status = 'active'",
                (user_id,)
            )
            
            # 새 구독 생성
            cursor = conn.execute(
                """
                INSERT INTO user_subscriptions 
                (user_id, plan_id, status, purchased_at, expires_at, remaining_tokens) 
                VALUES (?, ?, 'active', datetime('now'), ?, ?)
                """,
                (
                    user_id,
                    plan_id,
                    expires_at,
                    -1 if plan['is_unlimited'] else plan['token_amount']
                )
            )
            
            subscription_id = cursor.lastrowid
            conn.commit()
            
            # 유저 plan_type 업데이트
            conn.execute(
                "UPDATE users SET plan_type = ?, updated_at = datetime('now') WHERE id = ?",
                (plan['plan_name'], user_id)
            )
            conn.commit()
            
            logger.info(f"구독 구매 완료 - 사용자 ID: {user_id}, 플랜 ID: {plan_id}, 구독 ID: {subscription_id}")
            
            return {
                'success': True,
                'subscription_id': subscription_id,
                'expires_at': expires_at,
                'message': f"{plan['display_name']} 구독이 시작되었습니다"
            }
            
    except Exception as e:
        logger.error(f"구독 구매 중 오류: {str(e)}")
        return {
            'success': False,
            'message': f'구독 구매 중 오류 발생: {str(e)}'
        }


def update_plan_price_and_tokens(plan_id: int, new_price: int, new_token_amount: int) -> Dict[str, Any]:
    """
    구독 플랜의 가격 및 토큰 수량 수정 (관리자용)
    
    Args:
        plan_id: 구독 플랜 ID
        new_price: 새로운 가격
        new_token_amount: 새로운 토큰 수량
        
    Returns:
        Dict: 수정 결과
    """
    try:
        with get_conn() as conn:
            cursor = conn.execute(
                """
                UPDATE subscription_plans 
                SET price = ?, token_amount = ?, updated_at = datetime('now') 
                WHERE id = ?
                """,
                (new_price, new_token_amount, plan_id)
            )
            conn.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"구독 플랜 수정 완료 - 플랜 ID: {plan_id}, 가격: {new_price}, 토큰: {new_token_amount}")
                return {
                    'success': True,
                    'message': '구독 플랜이 업데이트되었습니다'
                }
            else:
                return {
                    'success': False,
                    'message': '구독 플랜을 찾을 수 없습니다'
                }
                
    except Exception as e:
        logger.error(f"구독 플랜 수정 중 오류: {str(e)}")
        return {
            'success': False,
            'message': f'구독 플랜 수정 중 오류 발생: {str(e)}'
        }


def check_subscription_expiry():
    """
    만료된 구독을 자동으로 비활성화 (크론 작업용)
    """
    try:
        with get_conn() as conn:
            cursor = conn.execute(
                """
                UPDATE user_subscriptions 
                SET status = 'expired', updated_at = datetime('now') 
                WHERE status = 'active' AND datetime('now') > expires_at
                """
            )
            conn.commit()
            
            expired_count = cursor.rowcount
            
            if expired_count > 0:
                logger.info(f"만료된 구독 {expired_count}개 비활성화 완료")
            
            return expired_count
            
    except Exception as e:
        logger.error(f"구독 만료 확인 중 오류: {str(e)}")
        return 0


