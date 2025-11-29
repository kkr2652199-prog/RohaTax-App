"""서비스 레이어: 관리자 사용자 관리 로직."""

from __future__ import annotations

import os
import shutil
import sqlite3
import logging
from typing import Dict, List
from datetime import datetime

from core.db import get_conn_optimized as get_conn
from core.user_profile_service import user_profile_service
from core.activity_service import record_activity


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
ROUTES_DIR = os.path.join(PROJECT_ROOT, 'routes')
BASE_USERS_DIR = os.path.join(ROUTES_DIR, 'user_data')


class UserServiceError(Exception):
    """일반 사용자 서비스 예외."""


def get_user_by_id(user_id: int) -> Dict:
    """
    특정 사용자 정보를 조회합니다.
    
    Args:
        user_id: 사용자 ID
        
    Returns:
        Dict: 사용자 정보
        
    Raises:
        UserServiceError: 사용자를 찾을 수 없을 때
    """
    user_data = user_profile_service.get_user_profile_data(user_id)
    if not user_data:
        raise UserServiceError(f"사용자를 찾을 수 없습니다: ID {user_id}")
    
    # subscription_end_date, free_trial_expired_at 및 가장 최근 Gold 결제일 포함 확인
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT subscription_end_date, free_trial_expired_at FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()
        
        if row:
            user_data['subscription_end_date'] = row['subscription_end_date']
            user_data['free_trial_expired_at'] = row['free_trial_expired_at']
        
        # 가장 최근 Gold 상품 결제일 조회 (상품 ID 기준: 3 = 유료 Gold)
        gold_payment = conn.execute(
            """
            SELECT created_at
            FROM payment_history
            WHERE user_id = ? AND product_id = 3 AND status = 'completed'
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (user_id,)
        ).fetchone()
        
        if gold_payment:
            user_data['gold_payment_start_date'] = gold_payment['created_at']
        else:
            user_data['gold_payment_start_date'] = None

        # 가장 최근 무료 기간제(체험) 결제일 조회 (상품 ID 기준: 5 = 기간 이벤트)
        trial_payment = conn.execute(
            """
            SELECT created_at
            FROM payment_history
            WHERE user_id = ? AND product_id = 5 AND status = 'completed'
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (user_id,)
        ).fetchone()

        if trial_payment:
            user_data['trial_start_date'] = trial_payment['created_at']
        else:
            user_data['trial_start_date'] = None

        # 가장 최근 무료 토큰 이벤트 정보 조회 (상품 ID = 4, expires_at이 있는 grant 기록)
        # payment_history에서 product_id = 4인 결제를 찾고,
        # 해당 결제 시점의 token_history에서 expires_at이 있는 grant 기록 찾기
        token_event = conn.execute(
            """
            SELECT th.created_at, th.expires_at
            FROM token_history th
            JOIN payment_history ph ON ph.user_id = th.user_id 
                AND ABS(JULIANDAY(ph.created_at) - JULIANDAY(th.created_at)) < 0.01
            WHERE th.user_id = ?
              AND th.change_type = 'grant'
              AND th.expires_at IS NOT NULL
              AND ph.product_id = 4
            ORDER BY th.created_at DESC
            LIMIT 1
            """,
            (user_id,)
        ).fetchone()

        if token_event:
            user_data['token_event_start_date'] = token_event['created_at']
            user_data['token_event_expires_at'] = token_event['expires_at']
        else:
            user_data['token_event_start_date'] = None
            user_data['token_event_expires_at'] = None
    
    return user_data


def fetch_general_users() -> List[Dict]:
    users = user_profile_service.get_all_users_with_recent_usage()
    return [user for user in users if not user.get('is_admin', False)]


def fetch_admin_users() -> List[Dict]:
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, username, email, company_name, business_number, representative_name,
                   phone, address, plan_type, monthly_limit, used_count, is_active,
                   created_at, COALESCE(token_balance, 0) AS token_balance,
                   COALESCE(tokens_used, 0) AS tokens_used,
                   COALESCE(approval_status, 'pending') AS approval_status
            FROM users
            WHERE COALESCE(is_deleted, 0) = 0 AND is_admin = 1
            ORDER BY created_at ASC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def fetch_dashboard_stats() -> Dict:
    with get_conn() as conn:
        total_issued_tokens = conn.execute(
            "SELECT COALESCE(SUM(token_balance), 0) AS total_issued FROM users WHERE COALESCE(is_deleted, 0) = 0"
        ).fetchone()["total_issued"]

        active_users_count = conn.execute(
            """
            SELECT COUNT(*) AS active_count
            FROM users
            WHERE COALESCE(is_deleted, 0) = 0 AND is_active = 1 AND COALESCE(is_admin, 0) = 0
            """
        ).fetchone()["active_count"]

    return {
        "total_issued_tokens": total_issued_tokens,
        "active_users_count": active_users_count,
        "system_error_rate": 0.1,
        "system_uptime": 99.9,
    }


def update_user_email(user_id: int, email: str) -> None:
    with get_conn() as conn:
        cursor = conn.execute("UPDATE users SET email = ? WHERE id = ?", (email, user_id))
        if cursor.rowcount == 0:
            raise UserServiceError("user not found")
        conn.commit()


def fetch_user_conversions(user_id: int) -> List[Dict]:
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        user = conn.execute(
            "SELECT id FROM users WHERE id = ? AND is_deleted = 0",
            (user_id,),
        ).fetchone()
        if not user:
            raise UserServiceError("user not found")

        conversions = conn.execute(
            """
            SELECT id, original_filename, created_at, status, tokens_used, file_size
            FROM conversion_logs
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 20
            """,
            (user_id,),
        ).fetchall()

    return [dict(conv) for conv in conversions]


def approve_user(user_id: int) -> None:
    _execute_user_update(
        "UPDATE users SET approval_status = 'approved', is_active = 1 WHERE id = ?",
        (user_id,),
    )


def reject_user(user_id: int) -> None:
    _execute_user_update(
        "UPDATE users SET approval_status = 'rejected' WHERE id = ?",
        (user_id,),
    )


def soft_delete_user(user_id: int, admin_user_id: int) -> None:
    """사용자를 소프트 삭제하고 이 활동을 기록합니다."""
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 사용자 정보 조회 (기록에 필요)
        user_row = conn.execute(
            "SELECT username, COALESCE(token_balance, 0) AS token_balance, plan_type FROM users WHERE id = ? AND COALESCE(is_deleted, 0) = 0",
            (user_id,)
        ).fetchone()
        
        if not user_row:
            raise UserServiceError(f'User not found: {user_id}')
        
        token_balance = user_row['token_balance'] or 0
        plan_type = user_row['plan_type'] or 'free'
        
        # 소프트 삭제 실행
        cursor.execute(
            "UPDATE users SET is_deleted = 1, deleted_at = datetime('now') WHERE id = ?",
            (user_id,)
        )
        
        # --- [수정] 새로운 'activity_logs'에 기록 ---
        activity_data = {
            'user_id': user_id,
            'performed_by_id': admin_user_id,
            'performed_by_type': 'ADMIN',
            'activity_type': 'USER_SOFT_DELETE_BY_ADMIN',
            'details': {
                'reason': '관리자에 의한 계정 비활성화',
                'username': user_row['username']
            },
            'token_change': 0,  # 삭제는 토큰 변화 없음
            'potential_cost': 0,
            'token_balance_before': token_balance,
            'token_balance_after': token_balance,  # 변화 없으므로 동일
            'user_plan_snapshot': plan_type
        }
        
        record_activity(cursor, activity_data)
        
        # 트랜잭션 커밋
        conn.commit()


def restore_user(user_id: int, admin_user_id: int) -> None:
    """소프트 삭제된 사용자를 복구하고 이 활동을 기록합니다."""
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 삭제된 사용자도 조회 가능하도록 조건 완화
        user_row = conn.execute(
            "SELECT username, COALESCE(token_balance, 0) AS token_balance, plan_type FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()
        
        if not user_row:
            raise UserServiceError(f'User not found: {user_id}')
        
        token_balance = user_row['token_balance'] or 0
        plan_type = user_row['plan_type'] or 'free'
        
        # 복구 실행
        cursor.execute(
            "UPDATE users SET is_deleted = 0, deleted_at = NULL, is_active = 1, approval_status = 'approved' WHERE id = ?",
            (user_id,)
        )
        
        # --- [수정] 새로운 'activity_logs'에 기록 ---
        activity_data = {
            'user_id': user_id,
            'performed_by_id': admin_user_id,
            'performed_by_type': 'ADMIN',
            'activity_type': 'USER_RESTORE_BY_ADMIN',
            'details': {
                'reason': '관리자에 의한 계정 복구',
                'username': user_row['username']
            },
            'token_change': 0,  # 복구는 토큰 변화 없음
            'potential_cost': 0,
            'token_balance_before': token_balance,
            'token_balance_after': token_balance,  # 변화 없으므로 동일
            'user_plan_snapshot': plan_type
        }
        
        record_activity(cursor, activity_data)
        
        # 트랜잭션 커밋
        conn.commit()


def update_user_subscription(user_id: int, subscription_end_date: str, admin_user_id: int) -> Dict:
    """
    사용자의 Gold 구독 종료일을 수정합니다.
    
    Args:
        user_id: 사용자 ID
        subscription_end_date: 새로운 종료일 (YYYY-MM-DD HH:MM:SS 형식)
        admin_user_id: 관리자 ID
        
    Returns:
        Dict: {
            'message': 성공 메시지,
            'grade_changed': 등급 변경 여부 (bool),
            'old_plan_type': 이전 등급,
            'new_plan_type': 새 등급
        }
        
    Raises:
        UserServiceError: 사용자를 찾을 수 없거나 오류 발생 시
    """
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 사용자 존재 확인 및 현재 정보 조회
        user_row = conn.execute(
            """
            SELECT id, username, plan_type, subscription_end_date
            FROM users
            WHERE id = ? AND COALESCE(is_deleted, 0) = 0
            """,
            (user_id,)
        ).fetchone()
        
        if not user_row:
            raise UserServiceError(f"사용자를 찾을 수 없습니다: ID {user_id}")
        
        username = user_row['username']
        current_plan_type = user_row['plan_type'] or 'free'
        old_end_date = user_row['subscription_end_date']
        
        # Gold 등급이 아니면 경고
        if current_plan_type not in ['gold', 'gold-vip']:
            raise UserServiceError(f"Gold 등급 사용자만 구독 기간을 수정할 수 있습니다. 현재 등급: {current_plan_type}")
        
        # subscription_end_date 업데이트
        cursor.execute(
            """
            UPDATE users
            SET subscription_end_date = ?, updated_at = datetime('now', 'localtime')
            WHERE id = ?
            """,
            (subscription_end_date, user_id)
        )
        
        if cursor.rowcount == 0:
            raise UserServiceError("구독 종료일 업데이트에 실패했습니다.")
        
        # 만료 체크 로직 즉시 실행
        from core.subscription_utils import check_and_revoke_expired_subscription
        
        # 만료일 파싱
        try:
            end_date_obj = datetime.strptime(subscription_end_date, '%Y-%m-%d %H:%M:%S')
            today = datetime.now()
            
            # 만료되었는지 확인
            if end_date_obj < today:
                # 만료된 경우 강등 처리
                check_and_revoke_expired_subscription(user_id)
                # 강등 후 최신 등급 조회
                updated_user = conn.execute(
                    "SELECT plan_type FROM users WHERE id = ?",
                    (user_id,)
                ).fetchone()
                new_plan_type = updated_user['plan_type'] if updated_user else current_plan_type
                grade_changed = new_plan_type != current_plan_type
            else:
                # 만료되지 않은 경우 등급 유지 또는 복구
                if current_plan_type != 'gold-vip':
                    # 만료되지 않았는데 등급이 gold-vip가 아니면 복구
                    cursor.execute(
                        "UPDATE users SET plan_type = 'gold-vip', updated_at = datetime('now', 'localtime') WHERE id = ?",
                        (user_id,)
                    )
                    new_plan_type = 'gold-vip'
                    grade_changed = True
                else:
                    new_plan_type = current_plan_type
                    grade_changed = False
        except Exception as e:
            # 날짜 파싱 실패 시 로그만 남기고 계속 진행
            logging.getLogger(__name__).warning(f"구독 종료일 파싱 실패: {str(e)}")
            new_plan_type = current_plan_type
            grade_changed = False
        
        # activity_logs에 기록
        activity_data = {
            'user_id': user_id,
            'performed_by_id': admin_user_id,
            'performed_by_type': 'ADMIN',
            'activity_type': 'GRADE_CHANGE' if grade_changed else 'SUBSCRIPTION_UPDATE',
            'details': {
                'reason': f'관리자 수동 기간 변경: {old_end_date or "미설정"} → {subscription_end_date} (관리자 수동)' + 
                         (f' / 등급 변경: {current_plan_type} → {new_plan_type}' if grade_changed else ''),
                'old_subscription_end_date': old_end_date,
                'new_subscription_end_date': subscription_end_date
            },
            'token_change': 0,
            'potential_cost': 0,
            'token_balance_before': None,
            'token_balance_after': None,
            'user_plan_snapshot': new_plan_type
        }
        
        record_activity(cursor, activity_data)
        
        # 트랜잭션 커밋
        conn.commit()
        
        message = f"사용자 {username}의 Gold 구독 종료일이 {subscription_end_date}로 변경되었습니다."
        if grade_changed:
            message += f" 등급이 {current_plan_type}에서 {new_plan_type}로 변경되었습니다."
        
        # 강등 여부를 포함한 Dict 반환
        return {
            'message': message,
            'grade_changed': grade_changed,
            'old_plan_type': current_plan_type,
            'new_plan_type': new_plan_type
        }


def purge_user(user_id: int, admin_user_id: int) -> str:
    """사용자를 영구 삭제하고 이 활동을 기록합니다."""
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 삭제 전 사용자 정보 조회 (기록에 필요)
        user_row = conn.execute(
            "SELECT username, COALESCE(token_balance, 0) AS token_balance, plan_type FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()
        
        if not user_row:
            # 이미 없는 사용자일 수 있으므로 오류 대신 경고만 반환
            return f"경고: 영구 삭제하려는 사용자 ID {user_id}를 찾을 수 없습니다."
        
        username = user_row['username']
        token_balance = user_row['token_balance'] or 0
        plan_type = user_row['plan_type'] or 'free'
        
        # --- [수정] 새로운 'activity_logs'에 기록 (사용자가 삭제되기 전에) ---
        activity_data = {
            'user_id': user_id,
            'performed_by_id': admin_user_id,
            'performed_by_type': 'ADMIN',
            'activity_type': 'USER_PURGE_BY_ADMIN',
            'details': {
                'reason': '관리자에 의한 계정 영구 삭제',
                'purged_username': username
            },
            'token_change': 0,  # 삭제는 토큰 변화 없음
            'potential_cost': 0,
            'token_balance_before': token_balance,
            'token_balance_after': None,  # 삭제 후에는 잔액이 없음
            'user_plan_snapshot': plan_type
        }
        
        record_activity(cursor, activity_data)
        
        # Foreign Key 제약 조건을 일시적으로 비활성화 (안전장치)
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        # 관련 데이터 삭제 (순서 중요: Foreign Key 의존성 순서대로)
        try:
            # 1. payment_history (결제 기록)
            cursor.execute("DELETE FROM payment_history WHERE user_id = ?", (user_id,))
            
            # 2. token_history (토큰 기록)
            cursor.execute("DELETE FROM token_history WHERE user_id = ?", (user_id,))
            
            # 3. activity_logs (활동 로그 - 해당 사용자 관련 로그만 삭제)
            # 주의: activity_logs는 ON DELETE SET NULL이지만, 해당 사용자의 로그는 삭제
            cursor.execute("DELETE FROM activity_logs WHERE user_id = ?", (user_id,))
            
            # 4. email_verification_attempts (이메일 인증 시도 기록)
            # 테이블이 존재하는 경우에만 삭제
            try:
                cursor.execute("DELETE FROM email_verification_attempts WHERE user_id = ?", (user_id,))
            except Exception:
                pass  # 테이블이 없을 수 있음
            
            # 5. password_reset_tokens (비밀번호 재설정 토큰)
            cursor.execute("DELETE FROM password_reset_tokens WHERE user_id = ?", (user_id,))
            
            # 6. user_subscriptions (구독 정보)
            cursor.execute("DELETE FROM user_subscriptions WHERE user_id = ?", (user_id,))
            
            # 7. gold_customers (Gold 고객 정보)
            cursor.execute("DELETE FROM gold_customers WHERE user_id = ?", (user_id,))
            
            # 8. validation_logs (검증 로그)
            cursor.execute("DELETE FROM validation_logs WHERE user_id = ?", (user_id,))
            
            # 9. usage_logs (사용 로그)
            cursor.execute("DELETE FROM usage_logs WHERE user_id = ?", (user_id,))
            
            # 10. conversion_logs (변환 로그)
            cursor.execute("DELETE FROM conversion_logs WHERE user_id = ?", (user_id,))
            
        except Exception as e:
            # Foreign Key 제약 조건 다시 활성화
            cursor.execute("PRAGMA foreign_keys = ON")
            raise Exception(f"관련 데이터 삭제 중 오류 발생: {str(e)}")
        
        # Foreign Key 제약 조건 다시 활성화
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # 실제 사용자 삭제 실행
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()

    # 파일 시스템 정리
    message = "User and related files purged"
    user_dir = os.path.join(BASE_USERS_DIR, str(user_id))
    try:
        if os.path.isdir(user_dir):
            shutil.rmtree(user_dir)
    except Exception as exc:  # pragma: no cover - 파일 시스템 상태 의존
        message = f"User deleted (file cleanup issues: {exc})"

    return message


def purge_all_users(keep_username: str, admin_user_id: int) -> str:
    """지정한 관리자 계정을 제외하고 모든 사용자를 삭제합니다. (로깅은 복잡하므로 일단 제외)"""
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        keeper = conn.execute(
            "SELECT id FROM users WHERE username = ? AND COALESCE(is_deleted,0)=0",
            (keep_username,),
        ).fetchone()
        if not keeper:
            raise UserServiceError("keeper not found")

        keep_id = keeper["id"]
        rows = conn.execute("SELECT id FROM users WHERE id != ?", (keep_id,)).fetchall()
        target_ids = [row["id"] for row in rows]

        for target_id in target_ids:
            try:
                conn.execute("DELETE FROM token_history WHERE user_id = ?", (target_id,))
                conn.execute("DELETE FROM usage_logs WHERE user_id = ?", (target_id,))
                conn.execute("DELETE FROM conversion_logs WHERE user_id = ?", (target_id,))
            except Exception:
                pass

        conn.execute("DELETE FROM users WHERE id != ?", (keep_id,))
        conn.commit()

    try:
        if os.path.isdir(BASE_USERS_DIR):
            for name in os.listdir(BASE_USERS_DIR):
                if name.isdigit() and int(name) != keep_id:
                    shutil.rmtree(os.path.join(BASE_USERS_DIR, name), ignore_errors=True)
    except Exception:  # pragma: no cover - 파일 시스템 상태 의존
        pass

    return "All users and files purged except keeper"


def approve_user_from_payload(user_id: int) -> None:
    approve_user(user_id)


def delete_user_from_payload(user_id: int, admin_user_id: int) -> None:
    """API 레이어에서 호출하는 소프트 삭제 래퍼 함수."""
    soft_delete_user(user_id, admin_user_id)


VALID_PLAN_TYPES = ['free', 'vip', 'premium-vip', 'gold-vip', 'unlimited']


def change_user_plan(user_id: int, plan_type: str, admin_user_id: int) -> str:
    """사용자의 플랜 유형을 변경하고, 이 활동을 activity_logs에 기록합니다."""
    
    if plan_type not in VALID_PLAN_TYPES:
        raise UserServiceError(
            '유효하지 않은 플랜 유형입니다. 가능한 값: ' + ', '.join(VALID_PLAN_TYPES)
        )

    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 관리자 권한 확인
        admin_user = cursor.execute(
            "SELECT username FROM users WHERE id = ? AND is_admin = 1",
            (admin_user_id,),
        ).fetchone()
        if not admin_user:
            raise UserServiceError('Administrator privileges required')

        # 사용자 정보 조회 (기록에 필요)
        target_user = cursor.execute(
            "SELECT username, plan_type, COALESCE(token_balance, 0) AS token_balance FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if not target_user:
            raise UserServiceError('User not found')

        previous_plan = target_user['plan_type']
        token_balance = target_user['token_balance']

        # 사용자 플랜 업데이트
        cursor.execute("UPDATE users SET plan_type = ? WHERE id = ?", (plan_type, user_id))

        # --- [수정] 새로운 'activity_logs'에 기록 ---
        # 낡은 token_history 기록 로직은 제거하고, 새로운 '기록관'을 사용합니다.
        
        activity_data = {
            'user_id': user_id,
            'performed_by_id': admin_user_id,
            'performed_by_type': 'ADMIN',
            'activity_type': 'GRADE_CHANGE_BY_ADMIN',
            'details': {
                'from_plan': previous_plan,
                'to_plan': plan_type,
                'reason': '관리자에 의한 변경 (관리자 수동)'
            },
            'token_change': 0,  # 등급 변경 자체는 토큰 변화 없음
            'potential_cost': 0,
            'token_balance_before': token_balance,
            'token_balance_after': token_balance,  # 변화 없으므로 동일
            'user_plan_snapshot': plan_type
        }
        
        # 범용 기록 함수 호출
        record_activity(cursor, activity_data)

        # 트랜잭션 커밋
        conn.commit()

    return f'사용자 플랜이 {plan_type}으로 변경되었습니다 (이전: {previous_plan})'


def _execute_user_update(query: str, params: tuple) -> None:
    with get_conn() as conn:
        cursor = conn.execute(query, params)
        if cursor.rowcount == 0:
            raise UserServiceError("user not found")
        conn.commit()
