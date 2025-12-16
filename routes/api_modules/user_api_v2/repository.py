"""
User API v2 - Repository Layer
DB 쿼리 전담 (SQL Injection 방지 필수)
"""
import sqlite3
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class UserRepository:
    """사용자 데이터 접근 계층"""
    
    # 정렬 필드 화이트리스트 (보안)
    SORT_FIELD_MAP = {
        'date': 'th.created_at',
        'created_at': 'th.created_at',
        'datetime': 'th.created_at',
        'log_type': 'th.change_type',
        'change_type': 'th.change_type',
        'filename': "COALESCE(json_extract(th.meta, '$.file_name'), json_extract(th.meta, '$.file'))",
        'file': "COALESCE(json_extract(th.meta, '$.file_name'), json_extract(th.meta, '$.file'))",
        'file_name': "COALESCE(json_extract(th.meta, '$.file_name'), json_extract(th.meta, '$.file'))",
        'customer_name': "COALESCE(json_extract(th.meta, '$.customer_name'), '')",
        'customer': "COALESCE(json_extract(th.meta, '$.customer_name'), '')",
        'amount': 'th.amount',
        'change_amount': 'th.amount',
        'plan_type': 'u.plan_type'
    }
    
    def __init__(self):
        """Repository 초기화"""
        self.logger = logger
    
    def get_user_plan_type(self, conn: sqlite3.Connection, user_id: int) -> Optional[str]:
        """사용자 plan_type 조회"""
        try:
            user_row = conn.execute(
                "SELECT plan_type FROM users WHERE id = ?",
                (user_id,)
            ).fetchone()
            return (user_row['plan_type'] or '').upper() if user_row else ''
        except Exception as e:
            self.logger.error(f"사용자 plan_type 조회 오류: {str(e)}")
            return ''
    
    def get_total_count(self, conn: sqlite3.Connection, user_id: int) -> int:
        """토큰 히스토리 총 개수 조회"""
        try:
            total_row = conn.execute(
                """
                SELECT COUNT(*) as cnt
                FROM token_history
                WHERE user_id = ? AND COALESCE(json_extract(meta, '$.deleted'), 0) = 0
                """,
                (user_id,)
            ).fetchone()
            return total_row['cnt'] if total_row else 0
        except Exception as e:
            self.logger.error(f"총 개수 조회 오류: {str(e)}")
            return 0
    
    def get_myhome_data(
        self,
        conn: sqlite3.Connection,
        user_id: int,
        limit: int,
        offset: int,
        sort: str,
        order: str
    ) -> List[sqlite3.Row]:
        """
        마이홈 데이터 조회 (보안 쿼리)
        
        Args:
            conn: 데이터베이스 연결
            user_id: 사용자 ID
            limit: 페이지 크기
            offset: 오프셋
            sort: 정렬 필드 (화이트리스트 검증됨)
            order: 정렬 순서 (asc/desc)
        
        Returns:
            List[sqlite3.Row]: 조회된 데이터 리스트
        """
        # 화이트리스트 검증 (보안)
        if sort not in self.SORT_FIELD_MAP:
            self.logger.warning(f"잘못된 정렬 필드: {sort}, 기본값 'date' 사용")
            sort = 'date'
        
        if order not in ('asc', 'desc'):
            self.logger.warning(f"잘못된 정렬 순서: {order}, 기본값 'desc' 사용")
            order = 'desc'
        
        # 안전한 정렬 필드 추출 (화이트리스트에서만 선택)
        sort_field = self.SORT_FIELD_MAP[sort]
        
        # 파라미터화된 쿼리 (ORDER BY는 화이트리스트로 안전하게 처리)
        # LIMIT, OFFSET은 파라미터 바인딩으로 안전하게 처리
        query = f"""
            SELECT 
                th.id, 
                th.change_type, 
                th.amount, 
                th.meta, 
                th.created_at, 
                u.plan_type,
                COALESCE(SUM(th.amount) OVER (
                    PARTITION BY th.user_id 
                    ORDER BY th.created_at, th.id 
                    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                ), 0) as balance_after
            FROM token_history th
            LEFT JOIN users u ON u.id = th.user_id
            WHERE th.user_id = ? 
              AND COALESCE(json_extract(th.meta, '$.deleted'), 0) = 0
            ORDER BY {sort_field} {order}, th.id {order}
            LIMIT ? OFFSET ?
        """
        
        try:
            # 파라미터 바인딩 (안전)
            result = conn.execute(query, (user_id, limit, offset)).fetchall()
            self.logger.debug(f"마이홈 데이터 조회 완료: user_id={user_id}, limit={limit}, offset={offset}, sort={sort}, order={order}, count={len(result)}")
            return result
        except Exception as e:
            self.logger.error(f"마이홈 데이터 조회 오류: {str(e)}")
            raise
    
    def delete_token_history_items(
        self,
        conn: sqlite3.Connection,
        user_id: int,
        item_ids: List[int]
    ) -> int:
        """토큰 히스토리 항목 삭제 (소프트 삭제)"""
        deleted_count = 0
        
        for th_id in item_ids:
            try:
                # 항목 존재 확인 및 소유권 검증
                row = conn.execute(
                    "SELECT id, meta FROM token_history WHERE id = ? AND user_id = ?",
                    (th_id, user_id)
                ).fetchone()
                
                if not row:
                    continue
                
                # meta JSON 파싱 및 deleted 플래그 설정
                try:
                    m = json.loads(row['meta']) if row['meta'] else {}
                except Exception:
                    m = {}
                
                m['deleted'] = 1
                
                # 소프트 삭제 업데이트
                conn.execute(
                    "UPDATE token_history SET meta = ? WHERE id = ? AND user_id = ?",
                    (json.dumps(m, ensure_ascii=False), th_id, user_id)
                )
                deleted_count += 1
                
            except Exception as e:
                self.logger.error(f"항목 삭제 오류 (id={th_id}): {str(e)}")
                continue
        
        return deleted_count
    
    def get_user_info(self, conn: sqlite3.Connection, user_id: int) -> Optional[sqlite3.Row]:
        """사용자 기본 정보 조회"""
        try:
            user = conn.execute(
                """
                SELECT 
                    id, username, created_at, plan_type, is_admin, tokens_used
                FROM users 
                WHERE id = ? AND COALESCE(is_deleted, 0) = 0
                """,
                (user_id,)
            ).fetchone()
            return user
        except Exception as e:
            self.logger.error(f"사용자 정보 조회 오류: {str(e)}")
            return None
    
    def get_token_summary(self, conn: sqlite3.Connection, user_id: int) -> Optional[sqlite3.Row]:
        """토큰 요약 조회 (activity_logs 기반)"""
        try:
            summary = conn.execute(
                """
                WITH last_reset AS (
                    SELECT MAX(timestamp) as reset_time
                    FROM activity_logs
                    WHERE user_id = ? AND activity_type = 'TOKEN_RESET_BY_ADMIN'
                      AND COALESCE(is_deleted, 0) = 0
                )
                SELECT
                    COALESCE(SUM(CASE WHEN al.token_change > 0 AND al.activity_type != 'TOKEN_RESET_BY_ADMIN' THEN al.token_change ELSE 0 END), 0) as total_charged,
                    COALESCE(SUM(CASE WHEN al.token_change < 0 AND al.activity_type != 'TOKEN_RESET_BY_ADMIN' THEN ABS(al.token_change) ELSE 0 END), 0) as total_used
                FROM activity_logs al, last_reset lr
                WHERE al.user_id = ?
                  AND (lr.reset_time IS NULL OR al.timestamp >= lr.reset_time)
                  AND COALESCE(al.is_deleted, 0) = 0
                """,
                (user_id, user_id)
            ).fetchone()
            return summary
        except Exception as e:
            self.logger.error(f"토큰 요약 조회 오류: {str(e)}")
            return None
    
    def get_activity_logs(self, conn: sqlite3.Connection, user_id: int) -> List[sqlite3.Row]:
        """활동 로그 조회 (activity_logs 기반)"""
        try:
            logs = conn.execute(
                """
                WITH last_reset AS (
                    SELECT MAX(timestamp) as reset_time
                    FROM activity_logs
                    WHERE user_id = ? AND activity_type = 'TOKEN_RESET_BY_ADMIN'
                      AND COALESCE(is_deleted, 0) = 0
                )
                SELECT
                    al.id,
                    al.timestamp,
                    al.user_plan_snapshot,
                    al.activity_type,
                    al.details,
                    al.token_change,
                    al.token_balance_before,
                    al.token_balance_after
                FROM activity_logs al, last_reset lr
                WHERE al.user_id = ?
                  AND (lr.reset_time IS NULL OR al.timestamp >= lr.reset_time)
                  AND COALESCE(al.is_deleted, 0) = 0
                ORDER BY al.timestamp ASC
                """,
                (user_id, user_id)
            ).fetchall()
            return logs
        except Exception as e:
            self.logger.error(f"활동 로그 조회 오류: {str(e)}")
            return []
    
    def get_usage_history_stats(self, conn: sqlite3.Connection, user_id: int) -> Dict[str, Any]:
        """사용 내역 통계 조회"""
        try:
            # 기간별 사용 통계
            period_stats = conn.execute(
                """
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as daily_conversions,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as daily_success,
                    AVG(conversion_time) as avg_time,
                    SUM(file_size) as daily_file_size
                FROM conversion_logs 
                WHERE user_id = ? AND created_at >= date('now', '-30 days')
                GROUP BY DATE(created_at)
                ORDER BY date DESC
                """,
                (user_id,)
            ).fetchall()
            
            # 월별 토큰 사용량
            monthly_usage = conn.execute(
                """
                SELECT 
                    strftime('%Y-%m', created_at) as month,
                    COUNT(*) as conversions,
                    SUM(CASE WHEN meta LIKE '%token%' THEN 1 ELSE 0 END) as token_usage
                FROM usage_logs 
                WHERE user_id = ? AND created_at >= date('now', '-12 months')
                GROUP BY strftime('%Y-%m', created_at)
                ORDER BY month DESC
                """,
                (user_id,)
            ).fetchall()
            
            return {
                'period_stats': period_stats,
                'monthly_usage': monthly_usage
            }
        except Exception as e:
            self.logger.error(f"사용 내역 통계 조회 오류: {str(e)}")
            return {'period_stats': [], 'monthly_usage': []}
    
    def get_recent_usage(self, conn: sqlite3.Connection, user_id: int, limit: int = 5) -> List[sqlite3.Row]:
        """최근 사용 내역 조회"""
        try:
            recent_usage = conn.execute(
                """
                SELECT action, meta, created_at 
                FROM usage_logs 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
                """,
                (user_id, limit)
            ).fetchall()
            return recent_usage
        except Exception as e:
            self.logger.error(f"최근 사용 내역 조회 오류: {str(e)}")
            return []
    
    def get_conversion_stats(self, conn: sqlite3.Connection, user_id: int) -> Optional[sqlite3.Row]:
        """변환 통계 조회"""
        try:
            conversion_stats = conn.execute(
                """
                SELECT 
                    COUNT(*) as total_conversions,
                    AVG(conversion_time) as avg_conversion_time,
                    SUM(file_size) as total_file_size,
                    COUNT(CASE WHEN status = 'success' THEN 1 END) as successful_conversions
                FROM conversion_logs 
                WHERE user_id = ?
                """,
                (user_id,)
            ).fetchone()
            return conversion_stats
        except Exception as e:
            self.logger.error(f"변환 통계 조회 오류: {str(e)}")
            return None
    
    def refresh_user_tokens(
        self,
        conn: sqlite3.Connection,
        user_id: int,
        token_amount: int,
        admin_id: int
    ) -> Optional[sqlite3.Row]:
        """사용자 토큰 새로고침 (관리자용)"""
        try:
            # 사용자 존재 확인
            user = conn.execute(
                "SELECT username FROM users WHERE id = ? AND COALESCE(is_deleted, 0) = 0",
                (user_id,)
            ).fetchone()
            
            if not user:
                return None
            
            # 토큰 추가
            conn.execute(
                "UPDATE users SET token_balance = COALESCE(token_balance, 0) + ? WHERE id = ?",
                (token_amount, user_id)
            )
            
            return user
        except Exception as e:
            self.logger.error(f"토큰 새로고침 오류: {str(e)}")
            return None

