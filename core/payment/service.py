"""
결제 관리 서비스 레이어
Jet Engine 기반 Service Layer 패턴 적용
비즈니스 로직과 데이터베이스 접근 분리
"""

from __future__ import annotations

import sqlite3
import logging
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

from core.db import get_conn_optimized as get_conn
from core.activity_service import record_activity
from .schemas import PaymentCreate, PaymentResponse, PaymentStatus

logger = logging.getLogger(__name__)


class PaymentService:
    """결제 관리 서비스 클래스"""
    
    def __init__(self):
        """PaymentService 초기화"""
        self.logger = logger
    
    def _safe_parse_payment_status(self, status_value: str, context: str = "") -> PaymentStatus:
        """
        PaymentStatus 안전 변환 헬퍼 함수
        
        Args:
            status_value: DB에서 가져온 status 값 (문자열)
            context: 로깅용 컨텍스트 정보 (예: "Payment ID: 123")
            
        Returns:
            PaymentStatus: 변환된 Enum 값 (실패 시 PENDING 반환)
        """
        try:
            return PaymentStatus(status_value)
        except ValueError:
            # DB 값이 Enum에 없으면 로깅 후 기본값(PENDING) 사용
            self.logger.warning(
                f"Unknown payment status in DB: '{status_value}' {context}. "
                f"Using default status: PENDING"
            )
            return PaymentStatus.PENDING
    
    def create_payment(
        self, 
        user_id: int, 
        product_id: int, 
        quantity: int = 1,
        admin_user_id: int = 1,
        status: PaymentStatus = PaymentStatus.COMPLETED,
        order_id: Optional[str] = None
    ) -> PaymentResponse:
        """
        결제 생성 (요금제 기반 수동 결제)
        
        Args:
            user_id: 사용자 ID
            product_id: 상품 ID
            quantity: 수량 (Standard일 경우만 사용, 기본값: 1)
            admin_user_id: 관리자 ID (토큰 지급 기록용)
            status: 결제 상태 (기본값: completed)
            
        Returns:
            PaymentResponse: 생성된 결제 정보
            
        Raises:
            ValueError: 유효하지 않은 데이터 또는 상품을 찾을 수 없음
        """
        try:
            with get_conn() as conn:
                conn.row_factory = sqlite3.Row
                
                # 트랜잭션 시작
                conn.execute("BEGIN TRANSACTION")
                
                # 변수 초기화 (스코프 문제 해결)
                user_row = None
                
                try:
                    # 1. 상품 정보 조회 (type, duration_days, token_validity_days 포함)
                    product_row = conn.execute(
                        """
                        SELECT id, name, price, token_amount, type, duration_days, token_validity_days, is_active
                        FROM products
                        WHERE id = ?
                        """,
                        (product_id,)
                    ).fetchone()
                    
                    if not product_row:
                        raise ValueError(f"상품을 찾을 수 없습니다: ID {product_id}")
                    
                    # sqlite3.Row를 dict로 변환 (안전한 접근을 위해)
                    product = dict(product_row)
                    
                    if not product['is_active']:
                        raise ValueError(f"판매 중지된 상품입니다: {product['name']}")
                    
                    product_name = product['name']
                    product_price = product['price']
                    product_token_amount = product['token_amount']
                    product_type = product.get('type') or 'basic'  # 기본값 'basic'
                    product_duration_days = product.get('duration_days')
                    product_token_validity_days = product.get('token_validity_days')
                    
                    # 2. 금액 및 토큰 계산 (수량 반영)
                    # event_period 타입은 금액 0원, 토큰 0개
                    if product_type == 'event_period':
                        total_amount = 0  # 기간제 이벤트는 무료
                        total_token_amount = 0  # 토큰 지급 없음
                    else:
                        # 모든 상품: 가격 × 수량
                        total_amount = product_price * quantity
                        
                        # 토큰 계산 (수량 반영, 단 무제한(-1)은 그대로 유지)
                        if product_token_amount == -1:  # Gold (무제한)
                            total_token_amount = -1  # 무제한은 수량과 무관하게 -1
                        else:
                            # Standard, Premium 등: 토큰 수량 × 주문 수량
                            total_token_amount = (product_token_amount or 0) * quantity
                    
                    # 3. 주문 ID 생성 또는 사용 (order_id가 제공되면 사용, 없으면 생성)
                    from datetime import datetime
                    if not order_id:
                        # order_id가 제공되지 않으면 자동 생성
                        now = datetime.now()
                        order_id = f"ORD-{now.strftime('%Y%m%d-%H%M%S')}-{user_id:04d}"
                        
                        # 주문 ID 중복 확인 (거의 없지만 안전장치)
                        existing = conn.execute(
                            "SELECT id FROM payment_history WHERE order_id = ?",
                            (order_id,)
                        ).fetchone()
                        
                        if existing:
                            # 중복 시 타임스탬프 추가
                            order_id = f"ORD-{now.strftime('%Y%m%d-%H%M%S')}-{user_id:04d}-{now.microsecond:06d}"
                    
                    # 3-1. 중복 결제 방지: 같은 사용자, 같은 상품, 같은 시간대(5초 이내) 중복 생성 방지
                    # (더블 클릭으로 인한 중복 요청 방지)
                    # payment_history 테이블에는 product_id가 없으므로, token_amount와 amount로 추론
                    # Gold(-1), Premium(>=100), Standard(1) 구분 가능
                    recent_payment = conn.execute(
                        """
                        SELECT id, order_id, created_at, token_amount, amount
                        FROM payment_history
                        WHERE user_id = ? AND token_amount = ? AND amount = ? AND status = 'completed'
                        AND datetime(created_at) > datetime('now', '-5 seconds', 'localtime')
                        ORDER BY created_at DESC
                        LIMIT 1
                        """,
                        (user_id, total_token_amount, total_amount)
                    ).fetchone()
                    
                    if recent_payment:
                        # 최근 5초 이내에 동일한 결제가 있으면 중복 요청으로 간주
                        self.logger.warning(
                            f"중복 결제 요청 감지: 사용자 ID {user_id}, 상품 ID {product_id}, "
                            f"최근 결제 ID {recent_payment['id']} (주문번호: {recent_payment['order_id']})"
                        )
                        raise ValueError(
                            f"최근 5초 이내에 동일한 결제가 생성되었습니다. "
                            f"주문번호: {recent_payment['order_id']}. "
                            f"중복 요청을 방지하기 위해 잠시 후 다시 시도해주세요."
                        )
                    
                    # 4. 사용자 현재 등급 조회 (이전 등급 저장용)
                    # status가 Enum이면 .value를, 문자열이면 그대로 사용하여 비교
                    status_str = status.value if isinstance(status, PaymentStatus) else str(status)
                    previous_plan_type = None
                    
                    if status_str == PaymentStatus.COMPLETED.value:
                        # 등급 업데이트가 발생할 수 있는 경우에만 이전 등급 저장
                        user_row_for_plan = conn.execute(
                            """
                            SELECT plan_type
                            FROM users
                            WHERE id = ?
                            """,
                            (user_id,)
                        ).fetchone()
                        
                        if user_row_for_plan:
                            previous_plan_type = user_row_for_plan['plan_type'] or 'free'
                    
                    # 5. 결제 기록 생성
                    # status가 Enum이면 .value를, 문자열이면 그대로 사용
                    status_value = status.value if isinstance(status, PaymentStatus) else str(status)
                    cursor = conn.execute(
                        """
                        INSERT INTO payment_history 
                        (user_id, order_id, amount, token_amount, status, pg_provider, previous_plan_type, product_id, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'), datetime('now', 'localtime'))
                        """,
                        (
                            user_id,
                            order_id,
                            total_amount,
                            total_token_amount,
                            status_value,
                            'manual',  # 수동 결제
                            previous_plan_type,  # 이전 등급 저장
                            product_id,
                        )
                    )
                    
                    payment_id = cursor.lastrowid
                    
                    # 변수 초기화 (activity_logs 기록용)
                    token_balance_before = None
                    token_balance_after = None
                    user_row = None
                    new_plan_type = None  # 등급 업데이트용 변수 초기화
                    
                    # 6. 토큰 지급 (status가 'completed'인 경우만)
                    # Gold 상품(-1)은 무제한이므로 토큰 지급 로직을 건너뛰지만, 등급 업데이트는 필요
                    if status_str == PaymentStatus.COMPLETED.value and total_token_amount > 0:
                        # 사용자 정보 조회
                        user_row = conn.execute(
                            """
                            SELECT username, COALESCE(token_balance, 0) AS token_balance, plan_type
                            FROM users
                            WHERE id = ?
                            """,
                            (user_id,)
                        ).fetchone()
                        
                        if not user_row:
                            raise ValueError(f"사용자를 찾을 수 없습니다: ID {user_id}")
                        
                        token_balance_before = user_row['token_balance'] or 0
                        token_balance_after = token_balance_before + total_token_amount
                        
                        # token_balance 업데이트
                        conn.execute(
                            """
                            UPDATE users
                            SET token_balance = ?
                            WHERE id = ?
                            """,
                            (token_balance_after, user_id)
                        )
                        
                        # token_history에 기록 (change_type: 'grant' 또는 'CHARGE')
                        import json
                        from datetime import timedelta
                        
                        # 토큰 유효기간 계산 (token_validity_days가 설정되어 있으면)
                        expires_at = None
                        if product_token_validity_days and product_token_validity_days > 0:
                            now = datetime.now()
                            expires_at = (now + timedelta(days=product_token_validity_days)).strftime('%Y-%m-%d %H:%M:%S')
                            self.logger.info(
                                f"토큰 유효기간 설정: 사용자 ID {user_id}, 상품 {product_name}, "
                                f"유효기간 {product_token_validity_days}일, 만료일 {expires_at}"
                            )
                        
                        meta = json.dumps({
                            'payment_id': payment_id,
                            'order_id': order_id,
                            'product_id': product_id,
                            'product_name': product_name,
                            'quantity': quantity if product_id == 1 else 1,
                            'token_validity_days': product_token_validity_days,
                            'tag': '(결제 연동)'
                        }, ensure_ascii=False)
                        
                        conn.execute(
                            """
                            INSERT INTO token_history 
                            (user_id, changed_by, amount, change_type, meta, expires_at, created_at)
                            VALUES (?, ?, ?, 'grant', ?, ?, datetime('now', 'localtime'))
                            """,
                            (
                                user_id,
                                admin_user_id,
                                total_token_amount,
                                meta,
                                expires_at
                            )
                        )
                    
                    # 7. 등급 업데이트 (status가 'completed'인 경우만)
                    if status_str == PaymentStatus.COMPLETED.value:
                        # user_row가 없으면 조회 (토큰 지급 조건이 맞지 않았을 경우, 예: Gold 무제한)
                        if user_row is None:
                            user_row = conn.execute(
                                """
                                SELECT username, COALESCE(token_balance, 0) AS token_balance, plan_type
                                FROM users
                                WHERE id = ?
                                """,
                                (user_id,)
                            ).fetchone()
                            
                            if not user_row:
                                raise ValueError(f"사용자를 찾을 수 없습니다: ID {user_id}")
                        
                        current_plan_type = user_row['plan_type'] or 'free'
                        
                        # 상품 ID 및 타입에 따른 등급 매핑
                        if product_id == 1:  # Standard
                            # Standard 구매 시: vip로 변경 (단, 이미 premium-vip나 gold-vip면 변경하지 않음)
                            if current_plan_type not in ['premium-vip', 'gold-vip']:
                                new_plan_type = 'vip'
                        elif product_id == 2:  # Premium
                            # Premium 구매 시: premium-vip로 변경 (단, 이미 gold-vip면 변경하지 않음)
                            if current_plan_type != 'gold-vip':
                                new_plan_type = 'premium-vip'
                        elif product_id == 3:  # Gold (유료 구독)
                            # Gold 구매 시: 항상 gold-vip로 변경 (최고 등급) + 구독 종료일 30일 연장
                            new_plan_type = 'gold-vip'

                            # Gold 구매 시 기간 연장 로직
                            # **결제일 기준으로 정확히 30일만 연장** (기존 만료일과 무관하게)
                            from datetime import datetime, timedelta

                            # 결제일을 기준으로 계산 (payment_history의 created_at 사용)
                            payment_created_at = None
                            payment_row = conn.execute(
                                """
                                SELECT created_at
                                FROM payment_history
                                WHERE id = ?
                                """,
                                (payment_id,)
                            ).fetchone()

                            if payment_row and payment_row['created_at']:
                                try:
                                    payment_created_at_str = payment_row['created_at']
                                    if isinstance(payment_created_at_str, str):
                                        payment_created_at = datetime.strptime(payment_created_at_str, '%Y-%m-%d %H:%M:%S')
                                    else:
                                        payment_created_at = payment_created_at_str
                                except Exception as e:
                                    self.logger.warning(f"결제일 파싱 오류: {str(e)}, 현재 시간 사용")

                            # 결제일을 찾지 못했으면 현재 시간 사용
                            if payment_created_at is None:
                                now_row = conn.execute("SELECT datetime('now', 'localtime') as now_time").fetchone()
                                now_str = now_row['now_time'] if now_row else None
                                if now_str:
                                    payment_created_at = datetime.strptime(now_str, '%Y-%m-%d %H:%M:%S')
                                else:
                                    payment_created_at = datetime.now()

                            # 결제일 기준으로 정확히 30일 연장
                            new_end_date = payment_created_at + timedelta(days=30)

                            # 기존 만료일 조회 (로깅용)
                            subscription_row = conn.execute(
                                """
                                SELECT subscription_end_date
                                FROM users
                                WHERE id = ?
                                """,
                                (user_id,)
                            ).fetchone()

                            current_end_date = subscription_row['subscription_end_date'] if subscription_row else None

                            if current_end_date:
                                try:
                                    if isinstance(current_end_date, str):
                                        current_end = datetime.strptime(current_end_date, '%Y-%m-%d %H:%M:%S')
                                    else:
                                        current_end = current_end_date

                                    self.logger.info(
                                        f"Gold 구독 기간 연장: 결제일 {payment_created_at.strftime('%Y-%m-%d %H:%M:%S')} "
                                        f"→ 새 만료일 {new_end_date.strftime('%Y-%m-%d %H:%M:%S')} (+30일) "
                                        f"[기존 만료일: {current_end.strftime('%Y-%m-%d %H:%M:%S')}]"
                                    )
                                except Exception:
                                    self.logger.info(
                                        f"Gold 구독 기간 연장: 결제일 {payment_created_at.strftime('%Y-%m-%d %H:%M:%S')} "
                                        f"→ 새 만료일 {new_end_date.strftime('%Y-%m-%d %H:%M:%S')} (+30일)"
                                    )
                            else:
                                self.logger.info(
                                    f"Gold 구독 신규 설정: 결제일 {payment_created_at.strftime('%Y-%m-%d %H:%M:%S')} "
                                    f"→ 만료일 {new_end_date.strftime('%Y-%m-%d %H:%M:%S')} (+30일)"
                                )

                            # subscription_end_date 업데이트 (등급 업데이트와 함께)
                            update_cursor = conn.execute(
                                """
                                UPDATE users
                                SET plan_type = ?, subscription_end_date = ?, updated_at = datetime('now', 'localtime')
                                WHERE id = ?
                                """,
                                (new_plan_type, new_end_date.strftime('%Y-%m-%d %H:%M:%S'), user_id)
                            )
                            rows_affected = update_cursor.rowcount
                            if rows_affected == 0:
                                self.logger.warning(
                                    f"등급 및 구독 기간 업데이트 실패: 사용자 ID {user_id}"
                                )
                            else:
                                self.logger.info(
                                    f"사용자 ID {user_id}의 등급이 '{current_plan_type}'에서 '{new_plan_type}'로 변경되었습니다 "
                                    f"(상품: {product_name}, product_id: {product_id}, 결제 ID: {payment_id}) "
                                    f"구독 만료일: {new_end_date.strftime('%Y-%m-%d %H:%M:%S')} (결제 연동)"
                                )

                            # Gold는 여기서 처리 완료 (아래 일반 등급 업데이트 분기 스킵)
                            new_plan_type = None
                        elif product_type == 'event_period':
                            # 무료 기간제 이벤트: 체험 기간 동안 Gold VIP 등급 부여
                            # (subscription_end_date는 건드리지 않고 free_trial_expired_at과 함께 사용)
                            new_plan_type = 'gold-vip'

                        # Gold(상품 ID 3)를 제외한 일반 등급 업데이트
                        if new_plan_type and new_plan_type != current_plan_type:
                            # Gold가 아닌 다른 상품의 등급 업데이트
                            update_cursor = conn.execute(
                                """
                                UPDATE users
                                SET plan_type = ?, updated_at = datetime('now', 'localtime')
                                WHERE id = ?
                                """,
                                (new_plan_type, user_id)
                            )
                            rows_affected = update_cursor.rowcount
                            if rows_affected == 0:
                                self.logger.warning(
                                    f"등급 업데이트 실패: 사용자 ID {user_id}의 등급을 '{current_plan_type}'에서 '{new_plan_type}'로 변경하려 했으나 업데이트된 행이 없습니다."
                                )
                            else:
                                self.logger.info(
                                    f"사용자 ID {user_id}의 등급이 '{current_plan_type}'에서 '{new_plan_type}'로 변경되었습니다 "
                                    f"(상품: {product_name}, product_id: {product_id}, 결제 ID: {payment_id}) (결제 연동)"
                                )
                        elif new_plan_type is None:
                            self.logger.warning(
                                f"등급 업데이트 스킵: 상품 ID {product_id} ({product_name})에 대한 등급 매핑이 없습니다."
                            )
                        elif new_plan_type == current_plan_type:
                            self.logger.info(
                                f"등급 업데이트 스킵: 사용자 ID {user_id}의 등급이 이미 '{current_plan_type}'입니다."
                            )
                    
                    # 7-1. 기간제 이벤트 처리 (event_period 타입)
                    if status_str == PaymentStatus.COMPLETED.value and product_type == 'event_period' and product_duration_days:
                        from datetime import timedelta
                        
                        # free_trial_expired_at 컬럼 확인 및 추가
                        columns_info = conn.execute("PRAGMA table_info(users)").fetchall()
                        columns = [row[1] for row in columns_info]
                        if 'free_trial_expired_at' not in columns:
                            conn.execute("ALTER TABLE users ADD COLUMN free_trial_expired_at TEXT")
                            self.logger.info(f"users 테이블에 free_trial_expired_at 컬럼 추가 완료")
                        
                        # 기간 연장 계산 (현재 시간 + duration_days)
                        now = datetime.now()
                        expiration = now + timedelta(days=max(1, product_duration_days))
                        expiration_iso = expiration.strftime('%Y-%m-%d %H:%M:%S')
                        
                        # 기존 만료일 조회 (로깅용)
                        trial_row = conn.execute(
                            """
                            SELECT free_trial_expired_at
                            FROM users
                            WHERE id = ?
                            """,
                            (user_id,)
                        ).fetchone()
                        
                        current_expiration = trial_row['free_trial_expired_at'] if trial_row else None
                        
                        # free_trial_expired_at 업데이트
                        conn.execute(
                            """
                            UPDATE users
                            SET free_trial_expired_at = ?, updated_at = datetime('now', 'localtime')
                            WHERE id = ?
                            """,
                            (expiration_iso, user_id)
                        )
                        
                        if current_expiration:
                            self.logger.info(
                                f"기간제 이벤트 기간 연장: 사용자 ID {user_id}, "
                                f"기존 만료일 {current_expiration} → 새 만료일 {expiration_iso} (+{product_duration_days}일)"
                            )
                        else:
                            self.logger.info(
                                f"기간제 이벤트 신규 설정: 사용자 ID {user_id}, "
                                f"만료일 {expiration_iso} (+{product_duration_days}일)"
                            )
                    
                    # 7. activity_logs에 기록 (결제 완료 시)
                    if status_str == PaymentStatus.COMPLETED.value:
                        # user_row가 없으면 조회
                        if user_row is None:
                            user_row = conn.execute(
                                """
                                SELECT username, COALESCE(token_balance, 0) AS token_balance, plan_type
                                FROM users
                                WHERE id = ?
                                """,
                                (user_id,)
                            ).fetchone()
                        
                        if user_row:
                            # token_balance_after가 없으면 현재 잔액 사용
                            if token_balance_after is None:
                                token_balance_after = user_row['token_balance'] or 0
                            
                            # token_balance_before가 없으면 계산
                            if token_balance_before is None:
                                if total_token_amount > 0:
                                    token_balance_before = token_balance_after - total_token_amount
                                else:
                                    token_balance_before = token_balance_after
                            
                            # 등급 업데이트가 실행된 경우 업데이트된 등급 사용, 아니면 현재 등급 사용
                            # 등급 업데이트가 실행되었다면 new_plan_type 사용, 아니면 DB에서 최신 등급 조회
                            if new_plan_type:
                                plan_type = new_plan_type
                            else:
                                # 등급 업데이트가 실행되지 않았거나, 이미 업데이트된 경우 최신 등급 조회
                                latest_user = conn.execute(
                                    "SELECT plan_type FROM users WHERE id = ?",
                                    (user_id,)
                                ).fetchone()
                                plan_type = latest_user['plan_type'] if latest_user else (user_row['plan_type'] or 'free')
                            
                            # activity_logs에 기록
                            activity_data = {
                                'user_id': user_id,
                                'performed_by_id': admin_user_id,  # 관리자가 결제를 생성했으므로
                                'performed_by_type': 'ADMIN',
                                'activity_type': 'TOKEN_CHARGE',  # 토큰 충전
                                'details': {
                                    'payment_id': payment_id,
                                    'order_id': order_id,
                                    'product_id': product_id,
                                    'product_name': product_name,
                                    'amount': total_amount,
                                    'token_amount': total_token_amount,
                                    'message': f"{product_name} 결제 완료 (주문번호: {order_id}) - (결제 자동)"
                                },
                                'token_change': total_token_amount if total_token_amount > 0 else 0,
                                'potential_cost': 0,
                                'token_balance_before': token_balance_before,
                                'token_balance_after': token_balance_after,
                                'user_plan_snapshot': plan_type
                            }
                            
                            # 디버깅용 로그
                            self.logger.info(
                                f"activity_logs 기록: 사용자 ID {user_id}, 상품: {product_name} (ID: {product_id}), "
                                f"등급 스냅샷: {plan_type}, new_plan_type: {new_plan_type} (결제 연동)"
                            )
                            
                            # record_activity 호출 (cursor는 conn.cursor()로 얻어야 함)
                            cursor = conn.cursor()
                            record_activity(cursor, activity_data)
                    
                    # 트랜잭션 커밋
                    conn.commit()
                    
                    # 생성된 결제 정보 조회
                    return self.get_payment_by_id(payment_id)
                    
                except Exception as e:
                    # 트랜잭션 롤백
                    conn.rollback()
                    raise e
                
        except sqlite3.IntegrityError as e:
            self.logger.error(f"결제 생성 중 DB 제약 조건 위반: {str(e)}")
            raise ValueError("결제 생성 실패: 데이터베이스 제약 조건 위반")
        except ValueError as e:
            # ValueError는 그대로 전달
            raise
        except Exception as e:
            self.logger.error(f"결제 생성 중 오류: {str(e)}")
            raise ValueError("결제 생성 중 오류가 발생했습니다: " + str(e))
    
    def get_payment_by_id(self, payment_id: int) -> PaymentResponse:
        """
        결제 ID로 결제 정보 조회
        
        Args:
            payment_id: 결제 ID
            
        Returns:
            PaymentResponse: 결제 정보
            
        Raises:
            ValueError: 결제를 찾을 수 없음
        """
        with get_conn() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT id, user_id, order_id, amount, token_amount, status, pg_provider, created_at, updated_at
                FROM payment_history
                WHERE id = ?
                """,
                (payment_id,)
            ).fetchone()
            
            if not row:
                raise ValueError(f"결제를 찾을 수 없습니다: ID {payment_id}")
            
            # PaymentStatus 안전 변환
            status_enum = self._safe_parse_payment_status(row['status'], f"(Payment ID: {payment_id})")
            
            return PaymentResponse(
                id=row['id'],
                user_id=row['user_id'],
                order_id=row['order_id'],
                amount=row['amount'],
                token_amount=row['token_amount'],
                status=status_enum,
                pg_provider=row['pg_provider'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
    
    def get_payment_by_order_id(self, order_id: str) -> Optional[PaymentResponse]:
        """
        주문 ID로 결제 정보 조회
        
        Args:
            order_id: 주문 ID
            
        Returns:
            Optional[PaymentResponse]: 결제 정보 또는 None
        """
        with get_conn() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT id, user_id, order_id, amount, token_amount, status, pg_provider, created_at, updated_at
                FROM payment_history
                WHERE order_id = ?
                """,
                (order_id,)
            ).fetchone()
            
            if not row:
                return None
            
            # PaymentStatus 안전 변환
            status_enum = self._safe_parse_payment_status(row['status'], f"(Order ID: {order_id})")
            
            return PaymentResponse(
                id=row['id'],
                user_id=row['user_id'],
                order_id=row['order_id'],
                amount=row['amount'],
                token_amount=row['token_amount'],
                status=status_enum,
                pg_provider=row['pg_provider'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
    
    def cancel_payment(self, payment_id: int, admin_user_id: int) -> PaymentResponse:
        """
        결제 취소 (토큰 회수 포함)
        
        Args:
            payment_id: 결제 ID
            admin_user_id: 관리자 ID (취소 처리자)
            
        Returns:
            PaymentResponse: 취소된 결제 정보
            
        Raises:
            ValueError: 결제를 찾을 수 없거나 취소할 수 없는 상태
        """
        with get_conn() as conn:
            conn.row_factory = sqlite3.Row
            
            # 트랜잭션 시작
            conn.execute("BEGIN TRANSACTION")
            
            try:
                # 1. 결제 정보 조회 (previous_plan_type 포함)
                payment_row = conn.execute(
                    """
                    SELECT id, user_id, order_id, amount, token_amount, status, previous_plan_type
                    FROM payment_history
                    WHERE id = ?
                    """,
                    (payment_id,)
                ).fetchone()
                
                if not payment_row:
                    raise ValueError(f"결제를 찾을 수 없습니다: ID {payment_id}")
                
                # 2. 상태 확인 (completed인 경우만 취소 가능)
                status_str = payment_row['status']
                if status_str != PaymentStatus.COMPLETED.value:
                    raise ValueError(f"취소할 수 없는 결제 상태입니다: {status_str}")
                
                # 3. 토큰 회수 (token_amount > 0인 경우만)
                token_amount = payment_row['token_amount'] or 0
                user_id = payment_row['user_id']
                previous_plan_type = payment_row['previous_plan_type']
                
                # 변수 초기화 (등급 복구 로직에서 사용)
                token_balance_before = None
                token_balance_after = None
                
                if token_amount > 0:
                    # 사용자 현재 토큰 잔액 조회
                    user_row = conn.execute(
                        """
                        SELECT COALESCE(token_balance, 0) AS token_balance
                        FROM users
                        WHERE id = ?
                        """,
                        (user_id,)
                    ).fetchone()
                    
                    if not user_row:
                        raise ValueError(f"사용자를 찾을 수 없습니다: ID {user_id}")
                    
                    token_balance_before = user_row['token_balance'] or 0
                    token_balance_after = max(0, token_balance_before - token_amount)  # 음수 방지
                    
                    # token_balance 업데이트
                    conn.execute(
                        """
                        UPDATE users
                        SET token_balance = ?, updated_at = datetime('now', 'localtime')
                        WHERE id = ?
                        """,
                        (token_balance_after, user_id)
                    )
                    
                    # 토큰 차감 후 최신 잔액 재조회 (통합 관제실 동기화를 위해)
                    updated_user_row = conn.execute(
                        """
                        SELECT COALESCE(token_balance, 0) AS token_balance
                        FROM users
                        WHERE id = ?
                        """,
                        (user_id,)
                    ).fetchone()
                    
                    if updated_user_row:
                        # 실제 DB에 저장된 최신 잔액 사용
                        token_balance_after = updated_user_row['token_balance'] or 0
                    
                    # token_history에 REFUND 기록
                    import json
                    meta = json.dumps({
                        'payment_id': payment_id,
                        'order_id': payment_row['order_id'],
                        'refund_amount': token_amount,
                        'tag': '(결제 취소/환불)'
                    }, ensure_ascii=False)
                    
                    conn.execute(
                        """
                        INSERT INTO token_history 
                        (user_id, changed_by, amount, change_type, meta, created_at)
                        VALUES (?, ?, ?, 'REFUND', ?, datetime('now', 'localtime'))
                        """,
                        (
                            user_id,
                            admin_user_id,
                            -token_amount,  # 음수로 기록 (회수)
                            meta
                        )
                    )
                    
                    self.logger.info(
                        f"결제 취소로 인한 토큰 회수: 사용자 ID {user_id}, "
                        f"회수량 {token_amount}토큰 (이전: {token_balance_before}, 이후: {token_balance_after}) (결제 취소/환불)"
                    )
                
                # 4. 등급 원상복구 (previous_plan_type이 있는 경우만)
                if previous_plan_type:
                    # 사용자 현재 등급 조회
                    user_row_for_grade = conn.execute(
                        """
                        SELECT plan_type
                        FROM users
                        WHERE id = ?
                        """,
                        (user_id,)
                    ).fetchone()
                    
                    if user_row_for_grade:
                        current_plan_type = user_row_for_grade['plan_type'] or 'free'
                        
                        # 이전 등급으로 복구 (현재 등급이 이전 등급과 다른 경우만)
                        if current_plan_type != previous_plan_type:
                            conn.execute(
                                """
                                UPDATE users
                                SET plan_type = ?, updated_at = datetime('now', 'localtime')
                                WHERE id = ?
                                """,
                                (previous_plan_type, user_id)
                            )
                            
                            self.logger.info(
                                f"결제 취소로 인한 등급 원상복구: 사용자 ID {user_id}, "
                                f"등급 '{current_plan_type}' -> '{previous_plan_type}' (결제 취소/환불)"
                            )
                            
                            # activity_logs에 등급 복구 기록
                            from core.activity_service import record_activity
                            activity_data = {
                                'user_id': user_id,
                                'performed_by_id': admin_user_id,
                                'performed_by_type': 'ADMIN',
                                'activity_type': 'GRADE_CHANGE_BY_ADMIN',
                                'details': {
                                    'from_plan': current_plan_type,
                                    'to_plan': previous_plan_type,
                                    'reason': f'결제 취소로 인한 등급 원상복구 (결제 ID: {payment_id}) (결제 취소/환불)'
                                },
                                'token_change': 0,
                                'potential_cost': 0,
                                'token_balance_before': token_balance_before if token_amount > 0 else None,
                                'token_balance_after': token_balance_after if token_amount > 0 else None,
                                'user_plan_snapshot': previous_plan_type
                            }
                            
                            cursor = conn.cursor()
                            record_activity(cursor, activity_data)
                
                # 5. 결제 상태를 cancelled로 변경
                conn.execute(
                    """
                    UPDATE payment_history
                    SET status = ?, updated_at = datetime('now', 'localtime')
                    WHERE id = ?
                    """,
                    (PaymentStatus.CANCELLED.value, payment_id)
                )
                
                # 5-1. orders 테이블도 동기화 (세무 리포트 정확성 보장)
                order_id = payment_row['order_id']
                if order_id:
                    orders_updated = conn.execute(
                        """
                        UPDATE orders
                        SET status = 'cancelled', updated_at = datetime('now', 'localtime')
                        WHERE merchant_uid = ?
                        """,
                        (order_id,)
                    )
                    
                    if orders_updated.rowcount > 0:
                        self.logger.info(
                            f"결제 취소로 인한 orders 테이블 동기화: 주문번호 {order_id} -> status='cancelled' (결제 취소/환불)"
                        )
                    else:
                        self.logger.warning(
                            f"결제 취소 시 orders 테이블 업데이트 실패: 주문번호 {order_id}를 찾을 수 없습니다 (결제 취소/환불)"
                        )
                
                # 6. activity_logs에 PAYMENT_CANCEL 기록 (통합 관제실 동기화)
                # 사용자 최신 정보 조회 (토큰 잔액, 등급)
                final_user_row = conn.execute(
                    """
                    SELECT COALESCE(token_balance, 0) AS token_balance, plan_type
                    FROM users
                    WHERE id = ?
                    """,
                    (user_id,)
                ).fetchone()
                
                if final_user_row:
                    # 최종 토큰 잔액 (토큰 회수 후 또는 원래 잔액)
                    final_token_balance = final_user_row['token_balance'] or 0
                    final_plan_type = final_user_row['plan_type'] or 'free'
                    
                    # 토큰 회수가 있었던 경우 token_balance_before/after 사용, 없었던 경우 현재 잔액 사용
                    if token_amount > 0:
                        log_token_balance_before = token_balance_before
                        log_token_balance_after = token_balance_after
                    else:
                        # 토큰 회수가 없었던 경우 (예: Gold 무제한)
                        log_token_balance_before = final_token_balance
                        log_token_balance_after = final_token_balance
                    
                    from core.activity_service import record_activity
                    activity_data = {
                        'user_id': user_id,
                        'performed_by_id': admin_user_id,
                        'performed_by_type': 'ADMIN',
                        'activity_type': 'PAYMENT_CANCEL',
                        'details': {
                            'payment_id': payment_id,
                            'order_id': payment_row['order_id'],
                            'refund_token_amount': token_amount if token_amount > 0 else 0,
                            'message': f"결제 취소 (주문번호: {payment_row['order_id']}) - (결제 취소/환불)"
                        },
                        'token_change': -token_amount if token_amount > 0 else 0,  # 음수로 기록 (회수)
                        'potential_cost': 0,
                        'token_balance_before': log_token_balance_before,
                        'token_balance_after': log_token_balance_after,  # 최신 잔액 사용
                        'user_plan_snapshot': final_plan_type
                    }
                    
                    cursor = conn.cursor()
                    record_activity(cursor, activity_data)
                    
                    self.logger.info(
                        f"결제 취소 activity_logs 기록: 사용자 ID {user_id}, "
                        f"토큰 잔액 {log_token_balance_before} -> {log_token_balance_after} (결제 취소/환불)"
                    )
                
                # 트랜잭션 커밋
                conn.commit()
                
                # 취소된 결제 정보 반환
                return self.get_payment_by_id(payment_id)
                
            except Exception as e:
                # 트랜잭션 롤백
                conn.rollback()
                raise e
    
    def delete_payment(self, payment_id: int) -> None:
        """
        결제 기록 삭제 (Hard Delete)
        
        Args:
            payment_id: 삭제할 결제 ID
            
        Raises:
            ValueError: 결제를 찾을 수 없거나 삭제할 수 없는 상태
        """
        with get_conn() as conn:
            conn.row_factory = sqlite3.Row
            
            # 결제 정보 조회
            payment_row = conn.execute(
                """
                SELECT id, status
                FROM payment_history
                WHERE id = ?
                """,
                (payment_id,)
            ).fetchone()
            
            if not payment_row:
                raise ValueError(f"결제를 찾을 수 없습니다: ID {payment_id}")
            
            # 삭제 가능한 상태인지 확인
            status_str = payment_row['status']
            if status_str not in [PaymentStatus.CANCELLED.value, PaymentStatus.FAILED.value]:
                raise ValueError(f"삭제할 수 없는 결제 상태입니다: {status_str} (취소/환불 또는 실패 상태만 삭제 가능)")
            
            # 결제 기록 삭제
            cursor = conn.execute(
                "DELETE FROM payment_history WHERE id = ?",
                (payment_id,)
            )
            
            if cursor.rowcount == 0:
                raise ValueError(f"결제 삭제에 실패했습니다: ID {payment_id}")
            
            conn.commit()
            self.logger.info(f"결제 기록 삭제 완료: ID {payment_id}")
    
    def get_payments_by_user_id(
        self, 
        user_id: int, 
        page: int = 1, 
        per_page: int = 20,
        status: Optional[PaymentStatus] = None
    ) -> Dict[str, Any]:
        """
        사용자별 결제 목록 조회
        
        Args:
            user_id: 사용자 ID
            page: 페이지 번호 (1부터 시작)
            per_page: 페이지당 항목 수
            status: 결제 상태 필터 (선택사항)
            
        Returns:
            Dict: 결제 목록 및 페이징 정보
            {
                'payments': List[PaymentResponse],
                'total': int,
                'page': int,
                'per_page': int
            }
        """
        with get_conn() as conn:
            conn.row_factory = sqlite3.Row
            
            # WHERE 조건 구성
            where_clause = "WHERE user_id = ?"
            params = [user_id]
            
            if status:
                where_clause += " AND status = ?"
                # status가 Enum이면 .value를, 문자열이면 그대로 사용
                status_value = status.value if isinstance(status, PaymentStatus) else str(status)
                params.append(status_value)
            
            # 전체 개수 조회
            total_row = conn.execute(
                f"SELECT COUNT(*) as total FROM payment_history {where_clause}",
                tuple(params)
            ).fetchone()
            total = total_row['total'] if total_row else 0
            
            # 페이징 계산
            offset = (page - 1) * per_page
            
            # 결제 목록 조회
            rows = conn.execute(
                f"""
                SELECT id, user_id, order_id, amount, token_amount, status, pg_provider, created_at, updated_at
                FROM payment_history
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                tuple(params + [per_page, offset])
            ).fetchall()
            
            payments = [
                PaymentResponse(
                    id=row['id'],
                    user_id=row['user_id'],
                    order_id=row['order_id'],
                    amount=row['amount'],
                    token_amount=row['token_amount'],
                    status=self._safe_parse_payment_status(row['status'], f"(Payment ID: {row['id']})"),
                    pg_provider=row['pg_provider'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                ).model_dump()  # JSON 직렬화를 위해 dict로 변환
                for row in rows
            ]
            
            return {
                'payments': payments,
                'total': total,
                'page': page,
                'per_page': per_page
            }
    
    def update_payment_status(
        self, 
        payment_id: int, 
        status: PaymentStatus
    ) -> PaymentResponse:
        """
        결제 상태 업데이트
        
        Args:
            payment_id: 결제 ID
            status: 새로운 결제 상태
            
        Returns:
            PaymentResponse: 업데이트된 결제 정보
            
        Raises:
            ValueError: 결제를 찾을 수 없음
        """
        with get_conn() as conn:
            # status가 Enum이면 .value를, 문자열이면 그대로 사용
            status_value = status.value if isinstance(status, PaymentStatus) else str(status)
            cursor = conn.execute(
                """
                UPDATE payment_history
                SET status = ?, updated_at = datetime('now', 'localtime')
                WHERE id = ?
                """,
                (status_value, payment_id)
            )
            
            if cursor.rowcount == 0:
                raise ValueError(f"결제를 찾을 수 없습니다: ID {payment_id}")
            
            conn.commit()
            
            return self.get_payment_by_id(payment_id)
    
    def get_all_payments(
        self,
        page: int = 1,
        per_page: int = 20,
        status: Optional[Union[PaymentStatus, str]] = None,
        user_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        전체 결제 목록 조회 (관리자용)
        
        Args:
            page: 페이지 번호 (1부터 시작)
            per_page: 페이지당 항목 수
            status: 결제 상태 필터 (선택사항)
            user_id: 사용자 ID 필터 (선택사항)
            start_date: 시작 날짜 (YYYY-MM-DD 형식, 선택사항)
            end_date: 종료 날짜 (YYYY-MM-DD 형식, 선택사항)
            
        Returns:
            Dict: 결제 목록, 페이징 정보, KPI 통계
        """
        # datetime 모듈 import (함수 내부에서 사용)
        from datetime import datetime, timedelta
        
        with get_conn() as conn:
            conn.row_factory = sqlite3.Row
            
            # WHERE 조건 구성 (JOIN 쿼리용과 COUNT 쿼리용 분리)
            where_conditions = []  # JOIN 쿼리용 (ph. 접두사 포함)
            count_where_conditions = []  # COUNT 쿼리용 (ph. 접두사 없음)
            params = []
            
            if status:
                # JOIN 쿼리용 (ph. 붙임)
                where_conditions.append("ph.status = ?")
                # COUNT 쿼리용 (ph. 뺌 - 중요!)
                count_where_conditions.append("status = ?")
                
                # status를 문자열로 변환 (Enum이면 .value, 문자열이면 그대로 사용)
                status_value = status.value if isinstance(status, PaymentStatus) else str(status)
                params.append(status_value)
            
            if user_id:
                where_conditions.append("ph.user_id = ?")
                count_where_conditions.append("user_id = ?")
                params.append(user_id)
            
            # 날짜 필터 추가 (빈 문자열 체크)
            if start_date and start_date.strip():
                where_conditions.append("DATE(ph.created_at) >= ?")
                count_where_conditions.append("DATE(created_at) >= ?")
                params.append(start_date.strip())
            
            if end_date and end_date.strip():
                where_conditions.append("DATE(ph.created_at) <= ?")
                count_where_conditions.append("DATE(created_at) <= ?")
                params.append(end_date.strip())
            
            # WHERE 절 구성 (JOIN 쿼리용 - ph. 접두사 포함)
            where_clause = ""
            if where_conditions:
                where_clause = "WHERE " + " AND ".join(where_conditions)
            
            # COUNT 쿼리용 WHERE 절 (ph. 접두사 없음)
            count_where_clause = ""
            if count_where_conditions:
                count_where_clause = "WHERE " + " AND ".join(count_where_conditions)
            
            # 디버그: 실제 실행되는 SQL 확인
            count_sql = f"SELECT COUNT(*) as total FROM payment_history {count_where_clause}"
            self.logger.debug(f"COUNT 쿼리 SQL: {count_sql}")
            self.logger.debug(f"COUNT 쿼리 파라미터: {params}")
            self.logger.debug(f"count_where_conditions: {count_where_conditions}")
            
            # 전체 개수 조회 (JOIN 없이, 테이블명 직접 사용)
            total_row = conn.execute(
                count_sql,
                tuple(params)
            ).fetchone()
            total = total_row['total'] if total_row else 0
            
            # 페이징 계산
            offset = (page - 1) * per_page
            
            # 결제 목록 조회 (유저 정보 및 주문 정보 JOIN)
            rows = conn.execute(
                f"""
                SELECT 
                    ph.id, 
                    ph.user_id, 
                    ph.order_id, 
                    ph.amount as ph_amount, 
                    ph.token_amount, 
                    ph.status, 
                    ph.pg_provider, 
                    ph.created_at, 
                    ph.updated_at,
                    u.username,
                    u.email,
                    COALESCE(o.amount, ph.amount, 0) as amount,
                    COALESCE(o.supply_price, 0) as supply_price,
                    COALESCE(o.vat, 0) as vat
                FROM payment_history ph
                LEFT JOIN users u ON ph.user_id = u.id
                LEFT JOIN orders o ON ph.order_id = o.merchant_uid
                {where_clause}
                ORDER BY ph.created_at DESC
                LIMIT ? OFFSET ?
                """,
                tuple(params + [per_page, offset])
            ).fetchall()
            
            payments = []
            for row in rows:
                try:
                    # sqlite3.Row를 dict로 변환하여 안전하게 접근
                    row_dict = dict(row)
                    
                    # orders 테이블의 amount를 우선 사용 (부가세 포함 총액)
                    # orders 테이블에 데이터가 없으면 payment_history의 amount 사용
                    final_amount = row_dict.get('amount') or row_dict.get('ph_amount') or 0
                    
                    payment_obj = PaymentResponse(
                        id=row_dict.get('id'),
                        user_id=row_dict.get('user_id'),
                        order_id=row_dict.get('order_id'),
                        amount=final_amount,
                        token_amount=row_dict.get('token_amount'),
                        status=self._safe_parse_payment_status(row_dict.get('status', 'pending'), f"(Payment ID: {row_dict.get('id')})"),
                        pg_provider=row_dict.get('pg_provider'),
                        created_at=row_dict.get('created_at'),
                        updated_at=row_dict.get('updated_at')
                    )
                    # Pydantic v1/v2 호환성: .model_dump() 사용
                    payment_dict = payment_obj.model_dump()
                    # 유저 정보 추가 (NULL 처리)
                    payment_dict['user_name'] = row_dict.get('username') or ''
                    payment_dict['user_email'] = row_dict.get('email') or ''
                    # 주문 정보 추가 (공급가/부가세)
                    payment_dict['supply_price'] = row_dict.get('supply_price') or 0
                    payment_dict['vat'] = row_dict.get('vat') or 0
                    payments.append(payment_dict)
                except Exception as e:
                    self.logger.error(f"결제 데이터 변환 오류: {str(e)}, row: {dict(row) if row else 'None'}")
                    continue
            
            # KPI 통계 계산 (기간 필터 적용)
            # 기간 필터 조건 구성 (KPI 통계용)
            kpi_where_conditions = []
            kpi_params = []
            
            # 빈 문자열 체크 및 None 변환
            if start_date and start_date.strip():
                kpi_where_conditions.append("DATE(created_at) >= ?")
                kpi_params.append(start_date.strip())
            
            if end_date and end_date.strip():
                kpi_where_conditions.append("DATE(created_at) <= ?")
                kpi_params.append(end_date.strip())
            
            kpi_where_clause = ""
            if kpi_where_conditions:
                kpi_where_clause = "WHERE " + " AND ".join(kpi_where_conditions)
            
            # 기간 내 매출 (completed 상태만)
            # WHERE 조건 동적 구성
            revenue_where_conditions = kpi_where_conditions.copy() if kpi_where_conditions else []
            revenue_where_conditions.append("status = 'completed'")
            revenue_where_clause = "WHERE " + " AND ".join(revenue_where_conditions) if revenue_where_conditions else ""
            
            period_revenue_row = conn.execute(
                f"""
                SELECT COALESCE(SUM(amount), 0) as revenue
                FROM payment_history
                {revenue_where_clause}
                """,
                tuple(kpi_params)
            ).fetchone()
            period_revenue = period_revenue_row['revenue'] if period_revenue_row else 0
            
            # 기간 내 결제 건수
            period_count_row = conn.execute(
                f"""
                SELECT COUNT(*) as count
                FROM payment_history
                {kpi_where_clause}
                """,
                tuple(kpi_params)
            ).fetchone()
            period_count = period_count_row['count'] if period_count_row else 0
            
            # 기간 내 환불 요청 (cancelled 상태)
            refund_where_conditions = kpi_where_conditions.copy() if kpi_where_conditions else []
            refund_where_conditions.append("status = 'cancelled'")
            refund_where_clause = "WHERE " + " AND ".join(refund_where_conditions) if refund_where_conditions else ""
            
            refund_count_row = conn.execute(
                f"""
                SELECT COUNT(*) as count
                FROM payment_history
                {refund_where_clause}
                """,
                tuple(kpi_params)
            ).fetchone()
            refund_count = refund_count_row['count'] if refund_count_row else 0
            
            # 상태별 건수 계산 (배지용)
            status_counts = {}
            for status_val in ['completed', 'pending', 'cancelled', 'failed']:
                status_where_conditions = kpi_where_conditions.copy() if kpi_where_conditions else []
                status_where_conditions.append("status = ?")
                status_where_clause = "WHERE " + " AND ".join(status_where_conditions) if status_where_conditions else ""
                
                status_count_row = conn.execute(
                    f"""
                    SELECT COUNT(*) as count
                    FROM payment_history
                    {status_where_clause}
                    """,
                    tuple(kpi_params + [status_val])
                ).fetchone()
                status_counts[status_val] = status_count_row['count'] if status_count_row else 0
            
            # 전체 건수 (기간 필터만 적용)
            all_count_row = conn.execute(
                f"""
                SELECT COUNT(*) as count
                FROM payment_history
                {kpi_where_clause}
                """,
                tuple(kpi_params)
            ).fetchone()
            status_counts['all'] = all_count_row['count'] if all_count_row else 0
            
            # 기간 내 매출 추이 (completed 상태만, 최대 30일)
            # 날짜 범위가 지정되지 않으면 최근 7일, 지정되면 해당 기간
            if start_date and end_date:
                # 지정된 기간 사용
                trend_where_conditions = kpi_where_conditions.copy() if kpi_where_conditions else []
                trend_where_conditions.append("status = 'completed'")
                trend_where_clause = "WHERE " + " AND ".join(trend_where_conditions) if trend_where_conditions else ""
                
                daily_revenue_rows = conn.execute(
                    f"""
                    SELECT 
                        strftime('%Y-%m-%d', created_at) as date,
                        COALESCE(SUM(amount), 0) as revenue
                    FROM payment_history
                    {trend_where_clause}
                    GROUP BY strftime('%Y-%m-%d', created_at)
                    ORDER BY date ASC
                    """,
                    tuple(kpi_params)
                ).fetchall()
            else:
                # 기본값: 최근 7일
                daily_revenue_rows = conn.execute(
                    """
                    SELECT 
                        strftime('%Y-%m-%d', created_at) as date,
                        COALESCE(SUM(amount), 0) as revenue
                    FROM payment_history
                    WHERE created_at >= datetime('now', '-7 days', 'localtime')
                    AND status = 'completed'
                    GROUP BY strftime('%Y-%m-%d', created_at)
                    ORDER BY date ASC
                    """
                ).fetchall()
            
            # 기간 내 최근 5건 결제 (최신순)
            # JOIN 없이 payment_history만 사용하므로 ph. 접두사 제거된 WHERE 절 사용
            latest_payments_where_clause = count_where_clause if count_where_clause else ""
            latest_payments_params = params.copy() if params else []
            
            latest_payments_rows = conn.execute(
                f"""
                SELECT id, user_id, order_id, amount, token_amount, status, pg_provider, created_at, updated_at
                FROM payment_history
                {latest_payments_where_clause}
                ORDER BY created_at DESC
                LIMIT 5
                """,
                tuple(latest_payments_params)
            ).fetchall()
            
            latest_payments = []
            for row in latest_payments_rows:
                try:
                    # sqlite3.Row를 dict로 변환하여 안전하게 접근
                    row_dict = dict(row)
                    
                    payment_obj = PaymentResponse(
                        id=row_dict.get('id'),
                        user_id=row_dict.get('user_id'),
                        order_id=row_dict.get('order_id'),
                        amount=row_dict.get('amount'),
                        token_amount=row_dict.get('token_amount'),
                        status=self._safe_parse_payment_status(row_dict.get('status', 'pending'), f"(Payment ID: {row_dict.get('id')})"),
                        pg_provider=row_dict.get('pg_provider'),
                        created_at=row_dict.get('created_at'),
                        updated_at=row_dict.get('updated_at')
                    )
                    # Pydantic v1/v2 호환성: .model_dump() 사용
                    latest_payments.append(payment_obj.model_dump())
                except Exception as e:
                    self.logger.error(f"최신 결제 데이터 변환 오류: {str(e)}, row: {dict(row) if row else 'None'}")
                    continue
            
            # 일별 매출 추이 데이터 구성
            daily_revenue_trend = []
            
            if start_date and end_date:
                # 지정된 기간의 모든 날짜 포함
                start = datetime.strptime(start_date, '%Y-%m-%d')
                end = datetime.strptime(end_date, '%Y-%m-%d')
                current = start
                
                while current <= end:
                    date_str = current.strftime('%Y-%m-%d')
                    # 해당 날짜의 매출 찾기
                    revenue = 0
                    for row in daily_revenue_rows:
                        if row['date'] == date_str:
                            revenue = row['revenue']
                            break
                    
                    daily_revenue_trend.append({
                        'date': date_str,
                        'revenue': revenue
                    })
                    current += timedelta(days=1)
            else:
                # 기본값: 최근 7일
                for i in range(6, -1, -1):
                    # timedelta를 사용하여 안전하게 날짜 계산
                    date = datetime.now() - timedelta(days=i)
                    date_str = date.strftime('%Y-%m-%d')
                    
                    # 해당 날짜의 매출 찾기
                    revenue = 0
                    for row in daily_revenue_rows:
                        if row['date'] == date_str:
                            revenue = row['revenue']
                            break
                    
                    daily_revenue_trend.append({
                        'date': date_str,
                        'revenue': revenue
                    })
            
            return {
                'payments': payments,
                'total': total,
                'page': page,
                'per_page': per_page,
                'kpi_stats': {
                    'period_revenue': period_revenue,  # 기간 내 매출
                    'period_payment_count': period_count,  # 기간 내 결제 건수
                    'refund_requests': refund_count
                },
                'status_counts': status_counts,  # 상태별 건수 (배지용)
                'daily_revenue_trend': daily_revenue_trend,
                'latest_payments': latest_payments  # 이미 dict로 변환됨
            }

