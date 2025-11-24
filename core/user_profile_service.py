"""
사용자 프로필 서비스
사용자 관련 데이터 처리 및 계산 로직을 담당
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from core.db import get_conn_optimized as get_conn


class UserProfileService:
    """사용자 프로필 서비스 클래스"""
    
    def __init__(self):
        self.logger = None
    
    def get_user_profile_data(self, user_id: int) -> Dict[str, Any]:
        """
        사용자 프로필 데이터 조회 및 계산
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            Dict: 사용자 프로필 데이터
        """
        try:
            with get_conn() as conn:
                conn.row_factory = sqlite3.Row
                
                # 기본 사용자 정보 조회
                user = conn.execute("""
                    SELECT id, username, email, company_name, business_number, 
                           representative_name, phone, address, business_type, business_category, 
                           plan_type, monthly_limit, used_count, is_active, created_at, 
                           COALESCE(token_balance, 0) AS token_balance, 
                           COALESCE(tokens_used, 0) AS tokens_used, 
                           COALESCE(approval_status, 'pending') AS approval_status,
                           subscription_end_date
                    FROM users 
                    WHERE id = ? AND COALESCE(is_deleted, 0) = 0
                """, (user_id,)).fetchone()
                
                if not user:
                    return {}
                
                # 최근 24시간 변환 건수 계산
                recent_conversion_count = self._calculate_recent_conversions(user_id, conn)
                
                # 사용자 데이터를 딕셔너리로 변환
                user_data = dict(user)
                
                # 최근 24시간 변환 건수로 업데이트
                user_data['used_count'] = recent_conversion_count
                
                return user_data
                
        except Exception as e:
            print(f"사용자 프로필 데이터 조회 오류: {str(e)}")
            return {}
    
    def _calculate_recent_conversions(self, user_id: int, conn) -> int:
        """
        최근 24시간 동안의 변환 건수 계산
        
        Args:
            user_id: 사용자 ID
            conn: 데이터베이스 연결
            
        Returns:
            int: 최근 24시간 변환 건수
        """
        try:
            # 24시간 전 시간 계산
            twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
            
            # 최근 24시간 동안의 변환 건수 조회
            result = conn.execute("""
                SELECT COUNT(*) as count
                FROM conversion_logs 
                WHERE user_id = ? 
                AND created_at >= ?
                AND status = 'success'
            """, (user_id, twenty_four_hours_ago.isoformat())).fetchone()
            
            return result['count'] if result else 0
            
        except Exception as e:
            print(f"최근 변환 건수 계산 오류: {str(e)}")
            return 0
    
    def get_all_users_with_recent_usage(self) -> list:
        """
        모든 사용자의 최근 사용량을 포함한 데이터 조회
        
        Returns:
            list: 사용자 목록
        """
        try:
            with get_conn() as conn:
                conn.row_factory = sqlite3.Row
                
                # 모든 활성 사용자 조회
                users = conn.execute("""
                    SELECT id, username, email, company_name, business_number, 
                           representative_name, phone, address, business_type, business_category, 
                           plan_type, monthly_limit, used_count, is_active, created_at, 
                           COALESCE(token_balance, 0) AS token_balance, 
                           COALESCE(tokens_used, 0) AS tokens_used, 
                           COALESCE(approval_status, 'pending') AS approval_status,
                           subscription_end_date
                    FROM users 
                    WHERE COALESCE(is_deleted, 0) = 0
                    ORDER BY created_at ASC
                """).fetchall()
                
                # 각 사용자별로 최근 24시간 변환 건수 계산 및 Gold 결제일 조회
                users_with_recent_usage = []
                for user in users:
                    user_data = dict(user)
                    user_data['used_count'] = self._calculate_recent_conversions(user['id'], conn)
                    
                    # 가장 최근 Gold 상품 결제일 조회 (token_amount = -1)
                    gold_payment = conn.execute(
                        """
                        SELECT created_at
                        FROM payment_history
                        WHERE user_id = ? AND token_amount = -1 AND status = 'completed'
                        ORDER BY created_at DESC
                        LIMIT 1
                        """,
                        (user['id'],)
                    ).fetchone()
                    
                    if gold_payment:
                        user_data['gold_payment_start_date'] = gold_payment['created_at']
                    else:
                        user_data['gold_payment_start_date'] = None
                    
                    users_with_recent_usage.append(user_data)
                
                return users_with_recent_usage
                
        except Exception as e:
            print(f"사용자 목록 조회 오류: {str(e)}")
            return []
    
    def update_user_usage_count(self, user_id: int) -> bool:
        """
        사용자의 사용량 카운트를 최근 24시간 변환 건수로 업데이트
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            bool: 업데이트 성공 여부
        """
        try:
            with get_conn() as conn:
                # 최근 24시간 변환 건수 계산
                recent_count = self._calculate_recent_conversions(user_id, conn)
                
                # 사용자 테이블의 used_count 업데이트
                conn.execute("""
                    UPDATE users 
                    SET used_count = ?, updated_at = datetime('now')
                    WHERE id = ?
                """, (recent_count, user_id))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"사용량 카운트 업데이트 오류: {str(e)}")
            return False


# 전역 인스턴스
user_profile_service = UserProfileService()


