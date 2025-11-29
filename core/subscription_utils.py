"""
구독 관리 유틸리티
VIP/VIP-Plus/GoldVIP 요금제 및 유저 구독 관리
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
import sqlite3
import json

from core.db import get_conn_optimized as get_conn

logger = logging.getLogger(__name__)


UNLIMITED_PLAN_TYPES = {'gold', 'gold-vip'}
TOKEN_DEDUCTION_PLAN_TYPES = {'vip', 'vip-plus', 'premium', 'premium-vip'}

PLAN_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    'free': {'display_name': '무료', 'is_unlimited': False},
    'vip': {'display_name': 'VIP', 'is_unlimited': False},
    'vip-plus': {'display_name': 'VIP Plus', 'is_unlimited': False},
    'premium': {'display_name': 'Premium', 'is_unlimited': False},
    'premium-vip': {'display_name': 'Premium VIP', 'is_unlimited': False},
    'gold': {'display_name': 'Gold', 'is_unlimited': True},
    'gold-vip': {'display_name': 'Gold VIP', 'is_unlimited': True},
}

TOKEN_PLAN_SUFFIX = ' (토큰차감)'
UNLIMITED_PLAN_SUFFIX = ' (무제한사용)'


def _normalize_plan_type(plan_type: Optional[str]) -> str:
    return (plan_type or 'free').strip().lower()


def _get_plan_definition(plan_type: Optional[str]) -> Dict[str, Any]:
    normalized = _normalize_plan_type(plan_type)
    definition = PLAN_DEFINITIONS.get(normalized)
    if definition:
        return definition
    fallback_name = (plan_type or 'FREE').upper()
    return {'display_name': fallback_name, 'is_unlimited': False}


def get_plan_display_label(plan_type: Optional[str]) -> str:
    normalized = _normalize_plan_type(plan_type)
    definition = _get_plan_definition(plan_type)
    base_label = definition['display_name']
    if normalized in UNLIMITED_PLAN_TYPES:
        return f"{base_label}{UNLIMITED_PLAN_SUFFIX}"
    if normalized in TOKEN_DEDUCTION_PLAN_TYPES:
        return f"{base_label}{TOKEN_PLAN_SUFFIX}"
    if normalized == 'free':
        return base_label
    return f"{base_label}{TOKEN_PLAN_SUFFIX}"


def _build_subscription_payload(plan_type: Optional[str], is_active: int | bool, token_balance: Optional[int] = None, tokens_used: Optional[int] = None) -> Dict[str, Any]:
    normalized = _normalize_plan_type(plan_type)
    definition = _get_plan_definition(plan_type)
    total_granted = token_balance if token_balance is not None else 0
    used_tokens = tokens_used if tokens_used is not None else 0

    if definition['is_unlimited']:
        remaining_tokens = -1
    else:
        remaining_tokens = max(0, (total_granted or 0) - (used_tokens or 0))

    payload = {
        'plan_type': plan_type or 'free',
        'display_name': definition['display_name'],
        'display_label': get_plan_display_label(plan_type),
        'is_unlimited': 1 if definition['is_unlimited'] else 0,
        'remaining_tokens': remaining_tokens,
        'status': 'active' if is_active else 'inactive',
        'total_granted': total_granted or 0,
        'tokens_used': used_tokens or 0,
    }
    return payload


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
    with get_conn() as conn:
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
        token_balance = row['token_balance'] if 'token_balance' in row.keys() else None
        tokens_used = row['tokens_used'] if 'tokens_used' in row.keys() else None

        subscription = _build_subscription_payload(plan_type, is_active, token_balance, tokens_used)

        logger.info(
            "사용자 플랜 조회 - ID: %s, 플랜: %s, 무제한: %s",
            user_id,
            plan_type,
            bool(subscription['is_unlimited'])
        )
        return subscription


def check_and_revoke_expired_subscription(user_id: int) -> bool:
    """
    사용자의 Gold 구독 만료일을 확인하고, 만료된 경우 등급을 강등하는 함수
    
    Args:
        user_id: 사용자 ID
        
    Returns:
        bool: 만료되어 강등되었으면 True, 아니면 False
    """
    try:
        with get_conn() as conn:
            conn.row_factory = sqlite3.Row
            user_row = conn.execute(
                """
                SELECT id, plan_type, subscription_end_date, free_trial_expired_at
                FROM users
                WHERE id = ? AND is_deleted = 0
                """,
                (user_id,)
            ).fetchone()
            
            if not user_row:
                return False
            
            plan_type = user_row['plan_type'] or 'free'
            subscription_end_date = user_row['subscription_end_date']
            free_trial_expired_at = user_row['free_trial_expired_at']
            
            # Gold 등급이 아니면 체크 불필요
            if plan_type not in ['gold', 'gold-vip']:
                return False
            
            now = datetime.now()
            
            # helper: 문자열/Datetime → datetime 변환
            def _parse_dt(value: Any) -> Optional[datetime]:
                if not value:
                    return None
                if isinstance(value, datetime):
                    return value
                if isinstance(value, str):
                    try:
                        # 기본 포맷 (초 단위)
                        return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        try:
                            # 밀리초(마이크로초) 포함 포맷 지원
                            return datetime.strptime(value, '%Y-%m-%d %H:%M:%S.%f')
                        except ValueError:
                            return None
                return None
            
            sub_end = _parse_dt(subscription_end_date)
            trial_end = _parse_dt(free_trial_expired_at)
            
            # 둘 중 하나라도 미래(유효)이면 → 권한 유지
            if (sub_end and now <= sub_end) or (trial_end and now <= trial_end):
                return False
            
            # 둘 다 없거나, 둘 다 과거(만료)라면 → 등급 free로 강등
            conn.execute(
                """
                UPDATE users
                SET plan_type = 'free', subscription_end_date = NULL, updated_at = datetime('now', 'localtime')
                WHERE id = ?
                """,
                (user_id,)
            )
            conn.commit()
            
            from core.activity_service import record_activity
            record_activity(
                user_id=user_id,
                activity_type='GRADE_CHANGE',
                details=(
                    "Gold 구독/체험 기간 만료로 등급이 'free'로 하락되었습니다. "
                    f"(subscription_end_date: {subscription_end_date}, free_trial_expired_at: {free_trial_expired_at})"
                ),
                token_change=0,
                ip_address='System'
            )
            
            logger.info(
                "사용자 ID %s의 Gold 권한이 만료되어 등급이 'free'로 강등되었습니다. "
                "(subscription_end_date: %s, free_trial_expired_at: %s)",
                user_id, subscription_end_date, free_trial_expired_at
            )
            return True
            
    except Exception as e:
        logger.error(f"구독 만료 확인 중 오류: {str(e)}")
        return False


def is_unlimited_user(user_id: int) -> bool:
    """
    사용자가 무제한 토큰 사용 가능한지 확인
    (만료일 체크 포함)
    
    Args:
        user_id: 사용자 ID
        
    Returns:
        bool: 무제한 사용 가능 여부 (Gold VIP만 True, 만료되지 않은 경우만)
    """
    try:
        # 먼저 만료 확인 및 강등 처리
        check_and_revoke_expired_subscription(user_id)
        
        subscription = get_user_subscription(user_id)
        print(f"[DEBUG | GHOST_HUNT] User ID: {user_id}, Subscription Data from get_user_subscription: {subscription}")

        if not subscription:
            return False
        
        # Gold VIP이고 만료되지 않은 경우만 True
        plan_type = subscription.get('plan_type', 'free')
        if plan_type not in ['gold', 'gold-vip']:
            return False
        
        # subscription_end_date 확인 (추가 안전장치)
        with get_conn() as conn:
            conn.row_factory = sqlite3.Row
            user_row = conn.execute(
                """
                SELECT subscription_end_date
                FROM users
                WHERE id = ? AND is_deleted = 0
                """,
                (user_id,)
            ).fetchone()
            
            if user_row and user_row['subscription_end_date']:
                try:
                    end_date_str = user_row['subscription_end_date']
                    if isinstance(end_date_str, str):
                        end_date = datetime.strptime(end_date_str, '%Y-%m-%d %H:%M:%S')
                    else:
                        end_date = end_date_str
                    
                    # 만료일이 지났으면 False
                    if datetime.now() > end_date:
                        return False
                except Exception:
                    # 파싱 오류 시 안전하게 False 반환
                    return False
        
        return bool(subscription.get('is_unlimited'))
        
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


