"""
결제 관리 서비스 레이어
Jet Engine 기반 Service Layer 패턴 적용
비즈니스 로직과 데이터베이스 접근 분리
"""

from __future__ import annotations

import sqlite3
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from core.db import get_conn_optimized as get_conn
from .schemas import PaymentCreate, PaymentResponse, PaymentStatus

logger = logging.getLogger(__name__)


class PaymentService:
    """결제 관리 서비스 클래스"""
    
    def __init__(self):
        """PaymentService 초기화"""
        self.logger = logger
    
    def create_payment(self, payment_data: PaymentCreate) -> PaymentResponse:
        """
        결제 생성
        
        Args:
            payment_data: 결제 생성 데이터
            
        Returns:
            PaymentResponse: 생성된 결제 정보
            
        Raises:
            ValueError: 주문 ID 중복 또는 유효하지 않은 데이터
        """
        try:
            with get_conn() as conn:
                conn.row_factory = sqlite3.Row
                
                # 주문 ID 중복 확인
                existing = conn.execute(
                    "SELECT id FROM payment_history WHERE order_id = ?",
                    (payment_data.order_id,)
                ).fetchone()
                
                if existing:
                    raise ValueError(f"이미 존재하는 주문 ID입니다: {payment_data.order_id}")
                
                # 결제 생성
                cursor = conn.execute(
                    """
                    INSERT INTO payment_history 
                    (user_id, order_id, amount, token_amount, status, pg_provider, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, datetime('now', 'localtime'), datetime('now', 'localtime'))
                    """,
                    (
                        payment_data.user_id,
                        payment_data.order_id,
                        payment_data.amount,
                        payment_data.token_amount,
                        payment_data.status.value,
                        payment_data.pg_provider,
                    )
                )
                
                conn.commit()
                payment_id = cursor.lastrowid
                
                # 생성된 결제 정보 조회
                return self.get_payment_by_id(payment_id)
                
        except sqlite3.IntegrityError as e:
            self.logger.error(f"결제 생성 중 DB 제약 조건 위반: {str(e)}")
            raise ValueError(f"결제 생성 실패: 주문 ID가 이미 존재합니다")
        except Exception as e:
            self.logger.error(f"결제 생성 중 오류: {str(e)}")
            raise
    
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
            
            return PaymentResponse(
                id=row['id'],
                user_id=row['user_id'],
                order_id=row['order_id'],
                amount=row['amount'],
                token_amount=row['token_amount'],
                status=PaymentStatus(row['status']),
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
            
            return PaymentResponse(
                id=row['id'],
                user_id=row['user_id'],
                order_id=row['order_id'],
                amount=row['amount'],
                token_amount=row['token_amount'],
                status=PaymentStatus(row['status']),
                pg_provider=row['pg_provider'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
    
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
                params.append(status.value)
            
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
                    status=PaymentStatus(row['status']),
                    pg_provider=row['pg_provider'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                ).dict()  # JSON 직렬화를 위해 dict로 변환
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
            cursor = conn.execute(
                """
                UPDATE payment_history
                SET status = ?, updated_at = datetime('now', 'localtime')
                WHERE id = ?
                """,
                (status.value, payment_id)
            )
            
            if cursor.rowcount == 0:
                raise ValueError(f"결제를 찾을 수 없습니다: ID {payment_id}")
            
            conn.commit()
            
            return self.get_payment_by_id(payment_id)
    
    def get_all_payments(
        self,
        page: int = 1,
        per_page: int = 20,
        status: Optional[PaymentStatus] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        전체 결제 목록 조회 (관리자용)
        
        Args:
            page: 페이지 번호 (1부터 시작)
            per_page: 페이지당 항목 수
            status: 결제 상태 필터 (선택사항)
            user_id: 사용자 ID 필터 (선택사항)
            
        Returns:
            Dict: 결제 목록, 페이징 정보, KPI 통계
        """
        with get_conn() as conn:
            conn.row_factory = sqlite3.Row
            
            # WHERE 조건 구성
            where_conditions = []
            params = []
            
            if status:
                where_conditions.append("status = ?")
                params.append(status.value)
            
            if user_id:
                where_conditions.append("user_id = ?")
                params.append(user_id)
            
            where_clause = ""
            if where_conditions:
                where_clause = "WHERE " + " AND ".join(where_conditions)
            
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
            
            payments = []
            for row in rows:
                try:
                    payment_obj = PaymentResponse(
                        id=row['id'],
                        user_id=row['user_id'],
                        order_id=row['order_id'],
                        amount=row['amount'],
                        token_amount=row['token_amount'],
                        status=PaymentStatus(row['status']),
                        pg_provider=row['pg_provider'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at']
                    )
                    # Pydantic v1/v2 호환성: .dict() 또는 .model_dump() 사용
                    if hasattr(payment_obj, 'model_dump'):
                        payments.append(payment_obj.model_dump())
                    else:
                        payments.append(payment_obj.dict())
                except Exception as e:
                    self.logger.error(f"결제 데이터 변환 오류: {str(e)}, row: {dict(row)}")
                    continue
            
            # KPI 통계 계산 (필터와 무관하게 전체 데이터 기준)
            today = datetime.now().strftime('%Y-%m-%d')
            month_start = datetime.now().replace(day=1).strftime('%Y-%m-%d')
            
            # 오늘 매출 (completed 상태만)
            today_revenue_row = conn.execute(
                """
                SELECT COALESCE(SUM(amount), 0) as revenue
                FROM payment_history
                WHERE strftime('%Y-%m-%d', created_at) = strftime('%Y-%m-%d', 'now', 'localtime')
                AND status = 'completed'
                """
            ).fetchone()
            today_revenue = today_revenue_row['revenue'] if today_revenue_row else 0
            
            # 이번 달 매출 (completed 상태만)
            month_revenue_row = conn.execute(
                """
                SELECT COALESCE(SUM(amount), 0) as revenue
                FROM payment_history
                WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now', 'localtime')
                AND status = 'completed'
                """
            ).fetchone()
            month_revenue = month_revenue_row['revenue'] if month_revenue_row else 0
            
            # 오늘 결제 건수
            today_count_row = conn.execute(
                """
                SELECT COUNT(*) as count
                FROM payment_history
                WHERE strftime('%Y-%m-%d', created_at) = strftime('%Y-%m-%d', 'now', 'localtime')
                """
            ).fetchone()
            today_count = today_count_row['count'] if today_count_row else 0
            
            # 환불 요청 (cancelled 상태)
            refund_count_row = conn.execute(
                """
                SELECT COUNT(*) as count
                FROM payment_history
                WHERE status = 'cancelled'
                """
            ).fetchone()
            refund_count = refund_count_row['count'] if refund_count_row else 0
            
            # 최근 7일간 매출 추이 (completed 상태만)
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
            
            # 최근 5건 결제 (최신순)
            latest_payments_rows = conn.execute(
                """
                SELECT id, user_id, order_id, amount, token_amount, status, pg_provider, created_at, updated_at
                FROM payment_history
                ORDER BY created_at DESC
                LIMIT 5
                """
            ).fetchall()
            
            latest_payments = []
            for row in latest_payments_rows:
                try:
                    payment_obj = PaymentResponse(
                        id=row['id'],
                        user_id=row['user_id'],
                        order_id=row['order_id'],
                        amount=row['amount'],
                        token_amount=row['token_amount'],
                        status=PaymentStatus(row['status']),
                        pg_provider=row['pg_provider'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at']
                    )
                    # Pydantic v1/v2 호환성: .dict() 또는 .model_dump() 사용
                    if hasattr(payment_obj, 'model_dump'):
                        latest_payments.append(payment_obj.model_dump())
                    else:
                        latest_payments.append(payment_obj.dict())
                except Exception as e:
                    self.logger.error(f"최신 결제 데이터 변환 오류: {str(e)}, row: {dict(row)}")
                    continue
            
            # 일별 매출 추이 데이터 구성 (최근 7일, 없는 날은 0으로)
            daily_revenue_trend = []
            for i in range(6, -1, -1):
                date = datetime.now()
                date = date.replace(day=date.day - i)
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
                    'today_revenue': today_revenue,
                    'month_revenue': month_revenue,
                    'today_payment_count': today_count,
                    'refund_requests': refund_count
                },
                'daily_revenue_trend': daily_revenue_trend,
                'latest_payments': latest_payments  # 이미 dict로 변환됨
            }

