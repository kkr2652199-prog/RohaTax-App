"""
User Repository
SQL 쿼리 및 DB 접근 담당 (보안 쿼리 적용)
API Turbocharger 리팩토링 - Phase 1
"""
from typing import List, Dict, Any, Optional
import sqlite3
import logging

logger = logging.getLogger(__name__)

class UserRepository:
    """사용자 데이터 접근 계층"""
    
    # 정렬 필드 화이트리스트 (보안)
    # SQL Injection 방지를 위해 화이트리스트만 허용
    SORT_FIELD_MAP = {
        'date': 'th.created_at',
        'log_type': 'th.change_type',
        'filename': 'COALESCE(json_extract(th.meta, \'$.file_name\'), json_extract(th.meta, \'$.file\'))',
        'customer_name': 'COALESCE(json_extract(th.meta, \'$.customer_name\'), \'\')',
        'amount': 'th.amount',
        'plan_type': 'u.plan_type'
    }
    
    def __init__(self, logger_instance: Optional[logging.Logger] = None):
        """Repository 초기화"""
        self.logger = logger_instance or logger
    
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
    
    def get_total_count(
        self,
        conn: sqlite3.Connection,
        user_id: int
    ) -> int:
        """
        총 개수 조회
        
        Args:
            conn: 데이터베이스 연결
            user_id: 사용자 ID
        
        Returns:
            int: 총 개수
        """
        try:
            row = conn.execute(
                """
                SELECT COUNT(*) as cnt
                FROM token_history
                WHERE user_id = ? AND COALESCE(json_extract(meta, '$.deleted'), 0) = 0
                """,
                (user_id,)
            ).fetchone()
            
            count = row['cnt'] if row else 0
            self.logger.debug(f"총 개수 조회 완료: user_id={user_id}, count={count}")
            return count
        except Exception as e:
            self.logger.error(f"총 개수 조회 오류: {str(e)}")
            raise
    
    def get_user_info(
        self,
        conn: sqlite3.Connection,
        user_id: int
    ) -> Optional[sqlite3.Row]:
        """
        사용자 정보 조회
        
        Args:
            conn: 데이터베이스 연결
            user_id: 사용자 ID
        
        Returns:
            Optional[sqlite3.Row]: 사용자 정보 (없으면 None)
        """
        try:
            row = conn.execute(
                """
                SELECT 
                    id, username, created_at, plan_type, is_admin
                FROM users 
                WHERE id = ? AND COALESCE(is_deleted, 0) = 0
                """,
                (user_id,)
            ).fetchone()
            
            if row:
                self.logger.debug(f"사용자 정보 조회 완료: user_id={user_id}, username={row['username']}")
            else:
                self.logger.warning(f"사용자 정보 없음: user_id={user_id}")
            
            return row
        except Exception as e:
            self.logger.error(f"사용자 정보 조회 오류: {str(e)}")
            raise
    
    def get_token_summary(
        self,
        conn: sqlite3.Connection,
        user_id: int
    ) -> Optional[sqlite3.Row]:
        """
        토큰 요약 조회 (activity_logs 기반)
        
        Args:
            conn: 데이터베이스 연결
            user_id: 사용자 ID
        
        Returns:
            Optional[sqlite3.Row]: 토큰 요약 정보 (없으면 기본값 0, 0 반환)
        """
        try:
            # activity_logs에 데이터가 없어도 항상 값을 반환하도록 수정
            # 서브쿼리를 사용하여 항상 결과가 나오도록 함
            row = conn.execute(
                """
                WITH last_reset AS (
                    SELECT MAX(timestamp) as reset_time
                    FROM activity_logs
                    WHERE user_id = ? AND activity_type = 'TOKEN_RESET_BY_ADMIN'
                      AND COALESCE(is_deleted, 0) = 0
                ),
                token_calc AS (
                    SELECT
                        COALESCE(SUM(CASE WHEN al.token_change > 0 AND al.activity_type != 'TOKEN_RESET_BY_ADMIN' THEN al.token_change ELSE 0 END), 0) as total_charged,
                        COALESCE(SUM(CASE WHEN al.token_change < 0 AND al.activity_type != 'TOKEN_RESET_BY_ADMIN' THEN ABS(al.token_change) ELSE 0 END), 0) as total_used
                    FROM activity_logs al
                    CROSS JOIN last_reset lr
                    WHERE al.user_id = ?
                      AND (lr.reset_time IS NULL OR al.timestamp >= lr.reset_time)
                      AND COALESCE(al.is_deleted, 0) = 0
                )
                SELECT 
                    COALESCE((SELECT total_charged FROM token_calc), 0) as total_charged,
                    COALESCE((SELECT total_used FROM token_calc), 0) as total_used
                """,
                (user_id, user_id)
            ).fetchone()
            
            # row가 None인 경우 기본값 반환 (안전장치)
            if not row:
                self.logger.warning(f"토큰 요약 정보 없음 (기본값 반환): user_id={user_id}")
                # 기본값을 가진 Row 객체 생성
                row = conn.execute(
                    "SELECT 0 as total_charged, 0 as total_used"
                ).fetchone()
            
            if row:
                self.logger.debug(f"토큰 요약 조회 완료: user_id={user_id}, total_charged={row['total_charged']}, total_used={row['total_used']}")
            
            return row
        except Exception as e:
            self.logger.error(f"토큰 요약 조회 오류: {str(e)}")
            # 오류 발생 시에도 기본값 반환
            try:
                return conn.execute("SELECT 0 as total_charged, 0 as total_used").fetchone()
            except:
                raise
    
    def get_token_status_data(
        self,
        conn: sqlite3.Connection,
        user_id: int
    ) -> Dict[str, Any]:
        """
        토큰 상태 데이터 조회 (통합)
        
        Args:
            conn: 데이터베이스 연결
            user_id: 사용자 ID
        
        Returns:
            Dict[str, Any]: 토큰 상태 데이터
        """
        try:
            # 사용자 정보
            user = self.get_user_info(conn, user_id)
            if not user:
                return {}
            
            # 토큰 요약
            summary = self.get_token_summary(conn, user_id)
            if not summary:
                return {}
            
            # 최근 사용 내역
            recent_usage = conn.execute(
                """
                SELECT action, meta, created_at 
                FROM usage_logs 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT 5
                """,
                (user_id,)
            ).fetchall()
            
            # 변환 통계
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
            
            return {
                'user': user,
                'summary': summary,
                'recent_usage': recent_usage,
                'conversion_stats': conversion_stats
            }
        except Exception as e:
            self.logger.error(f"토큰 상태 데이터 조회 오류: {str(e)}")
            raise
    
    def get_usage_history_data(
        self,
        conn: sqlite3.Connection,
        user_id: int
    ) -> Dict[str, Any]:
        """
        사용 내역 데이터 조회
        
        Args:
            conn: 데이터베이스 연결
            user_id: 사용자 ID
        
        Returns:
            Dict[str, Any]: 사용 내역 데이터
        """
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
            self.logger.error(f"사용 내역 데이터 조회 오류: {str(e)}")
            raise
    
    def get_activity_logs(
        self,
        conn: sqlite3.Connection,
        user_id: int
    ) -> List[sqlite3.Row]:
        """
        활동 로그 조회 (가장 최근 리셋 이후)
        
        Args:
            conn: 데이터베이스 연결
            user_id: 사용자 ID
        
        Returns:
            List[sqlite3.Row]: 활동 로그 리스트
        """
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
            
            self.logger.debug(f"활동 로그 조회 완료: user_id={user_id}, count={len(logs)}")
            return logs
        except Exception as e:
            self.logger.error(f"활동 로그 조회 오류: {str(e)}")
            raise
    
    def delete_token_history_items(
        self,
        conn: sqlite3.Connection,
        user_id: int,
        item_ids: List[int]
    ) -> int:
        """
        토큰 히스토리 항목 삭제 (소프트 삭제)
        
        Args:
            conn: 데이터베이스 연결
            user_id: 사용자 ID
            item_ids: 삭제할 항목 ID 리스트
        
        Returns:
            int: 삭제된 항목 수
        """
        import json
        
        deleted_count = 0
        
        try:
            for item_id in item_ids:
                # 항목 존재 확인 및 소유권 검증
                row = conn.execute(
                    "SELECT id, meta FROM token_history WHERE id = ? AND user_id = ?",
                    (item_id, user_id)
                ).fetchone()
                
                if not row:
                    self.logger.warning(f"항목 없음 또는 소유권 없음: item_id={item_id}, user_id={user_id}")
                    continue
                
                # 메타데이터 업데이트 (소프트 삭제)
                try:
                    meta = json.loads(row['meta']) if row['meta'] else {}
                except Exception:
                    meta = {}
                
                meta['deleted'] = 1
                
                # 업데이트 (파라미터 바인딩)
                conn.execute(
                    "UPDATE token_history SET meta = ? WHERE id = ? AND user_id = ?",
                    (json.dumps(meta, ensure_ascii=False), item_id, user_id)
                )
                deleted_count += 1
            
            conn.commit()
            self.logger.info(f"토큰 히스토리 항목 삭제 완료: user_id={user_id}, deleted_count={deleted_count}")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"토큰 히스토리 항목 삭제 오류: {str(e)}")
            conn.rollback()
            raise
    
    def refresh_user_tokens(
        self,
        conn: sqlite3.Connection,
        user_id: int,
        token_amount: int,
        admin_id: int
    ) -> Dict[str, Any]:
        """
        사용자 토큰 새로고침 (관리자용)
        
        Args:
            conn: 데이터베이스 연결
            user_id: 사용자 ID
            token_amount: 추가할 토큰 양
            admin_id: 관리자 ID
        
        Returns:
            Dict[str, Any]: 사용자 정보 및 토큰 정보
        """
        import json
        from datetime import datetime
        
        try:
            # 사용자 존재 확인
            user = conn.execute(
                "SELECT username FROM users WHERE id = ? AND COALESCE(is_deleted, 0) = 0",
                (user_id,)
            ).fetchone()
            
            if not user:
                raise ValueError(f"사용자를 찾을 수 없습니다: user_id={user_id}")
            
            # 토큰 추가 (파라미터 바인딩)
            conn.execute(
                "UPDATE users SET token_balance = COALESCE(token_balance, 0) + ? WHERE id = ?",
                (token_amount, user_id)
            )
            
            # 사용 로그 기록 (파라미터 바인딩)
            conn.execute(
                "INSERT INTO usage_logs (user_id, action, meta) VALUES (?, ?, ?)",
                (user_id, 'token_refresh', json.dumps({
                    'amount': token_amount,
                    'admin_id': admin_id,
                    'timestamp': datetime.now().isoformat()
                }))
            )
            
            conn.commit()
            
            result = {
                'user_id': user_id,
                'username': user['username'],
                'token_amount': token_amount,
                'admin_id': admin_id,
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"토큰 새로고침 완료: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"토큰 새로고침 오류: {str(e)}")
            conn.rollback()
            raise

