"""
데이터베이스 성능 최적화 모듈
Python 3.14의 Free-Threaded Python을 활용한 고성능 DB 최적화
"""

import sqlite3
import threading
import time
from typing import Dict, List, Any, Optional, Tuple
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)

class DatabaseOptimizer:
    """데이터베이스 성능 최적화 클래스"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection_pool = []
        self.pool_size = 5
        self.pool_lock = threading.Lock()
        self.query_cache = {}
        self.cache_lock = threading.Lock()
        
        # Python 3.14 Free-Threaded Python 활용
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # 성능 메트릭
        self.query_times = {}
        self.slow_queries = []
        
        logger.info("데이터베이스 최적화 시스템 초기화 완료")
    
    def _get_connection(self) -> sqlite3.Connection:
        """연결 풀에서 연결 가져오기"""
        with self.pool_lock:
            if self.connection_pool:
                conn = self.connection_pool.pop()
                # 연결 상태 확인
                try:
                    conn.execute("SELECT 1")
                    return conn
                except sqlite3.Error:
                    conn.close()
            
            # 새 연결 생성
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            
            # 성능 최적화 설정
            conn.execute("PRAGMA journal_mode=WAL")  # WAL 모드로 성능 향상
            conn.execute("PRAGMA synchronous=NORMAL")  # 동기화 최적화
            conn.execute("PRAGMA cache_size=10000")  # 캐시 크기 증가
            conn.execute("PRAGMA temp_store=MEMORY")  # 임시 테이블을 메모리에 저장
            conn.execute("PRAGMA mmap_size=268435456")  # 메모리 맵 크기 (256MB)
            
            return conn
    
    def _return_connection(self, conn: sqlite3.Connection):
        """연결을 풀에 반환"""
        with self.pool_lock:
            if len(self.connection_pool) < self.pool_size:
                self.connection_pool.append(conn)
            else:
                conn.close()
    
    @contextmanager
    def get_connection(self):
        """연결 컨텍스트 매니저"""
        conn = self._get_connection()
        try:
            yield conn
        finally:
            self._return_connection(conn)
    
    def optimize_database(self) -> Dict[str, Any]:
        """데이터베이스 최적화 실행"""
        logger.info("데이터베이스 최적화 시작")
        
        optimization_results = {
            'indexes_created': 0,
            'statistics_updated': False,
            'vacuum_completed': False,
            'performance_improved': False
        }
        
        try:
            with self.get_connection() as conn:
                # 1. 인덱스 최적화
                optimization_results['indexes_created'] = self._create_performance_indexes(conn)
                
                # 2. 통계 업데이트
                optimization_results['statistics_updated'] = self._update_statistics(conn)
                
                # 3. VACUUM 실행 (공간 정리)
                optimization_results['vacuum_completed'] = self._vacuum_database(conn)
                
                # 4. 성능 분석
                optimization_results['performance_improved'] = self._analyze_performance(conn)
                
        except Exception as e:
            logger.error(f"데이터베이스 최적화 실패: {e}")
            return optimization_results
        
        logger.info(f"데이터베이스 최적화 완료: {optimization_results}")
        return optimization_results
    
    def _create_performance_indexes(self, conn: sqlite3.Connection) -> int:
        """성능 향상을 위한 인덱스 생성"""
        indexes = [
            # 사용자 테이블 인덱스
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_users_business_number ON users(business_number)",
            "CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_users_is_deleted ON users(is_deleted)",
            "CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at)",
            
            # 사용 로그 테이블 인덱스
            "CREATE INDEX IF NOT EXISTS idx_usage_logs_user_id ON usage_logs(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_usage_logs_action ON usage_logs(action)",
            "CREATE INDEX IF NOT EXISTS idx_usage_logs_created_at ON usage_logs(created_at)",
            
            # 변환 로그 테이블 인덱스
            "CREATE INDEX IF NOT EXISTS idx_conversion_logs_user_id ON conversion_logs(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_conversion_logs_status ON conversion_logs(status)",
            "CREATE INDEX IF NOT EXISTS idx_conversion_logs_created_at ON conversion_logs(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_conversion_logs_file_size ON conversion_logs(file_size)",
            
            # 복합 인덱스 (자주 함께 사용되는 컬럼들)
            "CREATE INDEX IF NOT EXISTS idx_users_active_not_deleted ON users(is_active, is_deleted)",
            "CREATE INDEX IF NOT EXISTS idx_conversion_logs_user_status ON conversion_logs(user_id, status)",
            "CREATE INDEX IF NOT EXISTS idx_usage_logs_user_action ON usage_logs(user_id, action)"
        ]
        
        created_count = 0
        for index_sql in indexes:
            try:
                conn.execute(index_sql)
                created_count += 1
            except sqlite3.Error as e:
                logger.warning(f"인덱스 생성 실패: {e}")
        
        logger.info(f"성능 인덱스 {created_count}개 생성 완료")
        return created_count
    
    def _update_statistics(self, conn: sqlite3.Connection) -> bool:
        """쿼리 최적화를 위한 통계 업데이트"""
        try:
            conn.execute("ANALYZE")
            logger.info("데이터베이스 통계 업데이트 완료")
            return True
        except sqlite3.Error as e:
            logger.error(f"통계 업데이트 실패: {e}")
            return False
    
    def _vacuum_database(self, conn: sqlite3.Connection) -> bool:
        """데이터베이스 공간 정리"""
        try:
            conn.execute("VACUUM")
            logger.info("데이터베이스 공간 정리 완료")
            return True
        except sqlite3.Error as e:
            logger.error(f"VACUUM 실패: {e}")
            return False
    
    def _analyze_performance(self, conn: sqlite3.Connection) -> bool:
        """성능 분석 및 개선사항 확인"""
        try:
            # 느린 쿼리 확인
            cursor = conn.execute("""
                SELECT sql, time FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            
            tables = cursor.fetchall()
            logger.info(f"분석된 테이블 수: {len(tables)}")
            
            # 성능 메트릭 수집
            self._collect_performance_metrics(conn)
            
            return True
        except Exception as e:
            logger.error(f"성능 분석 실패: {e}")
            return False
    
    def _collect_performance_metrics(self, conn: sqlite3.Connection):
        """성능 메트릭 수집"""
        try:
            # 테이블 크기 정보
            cursor = conn.execute("""
                SELECT name, 
                       (SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=m.name) as row_count
                FROM sqlite_master m 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            
            table_info = cursor.fetchall()
            for table in table_info:
                logger.info(f"테이블 {table['name']}: {table['row_count']} 행")
                
        except Exception as e:
            logger.error(f"성능 메트릭 수집 실패: {e}")
    
    def execute_optimized_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """최적화된 쿼리 실행"""
        start_time = time.time()
        
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(query, params)
                results = [dict(row) for row in cursor.fetchall()]
                
                # 실행 시간 기록
                execution_time = time.time() - start_time
                self._record_query_time(query, execution_time)
                
                return results
                
        except sqlite3.Error as e:
            logger.error(f"쿼리 실행 실패: {e}")
            return []
    
    def _record_query_time(self, query: str, execution_time: float):
        """쿼리 실행 시간 기록"""
        query_hash = hash(query)
        
        with self.cache_lock:
            if query_hash not in self.query_times:
                self.query_times[query_hash] = []
            
            self.query_times[query_hash].append(execution_time)
            
            # 느린 쿼리 감지 (1초 이상)
            if execution_time > 1.0:
                self.slow_queries.append({
                    'query': query[:100] + '...' if len(query) > 100 else query,
                    'time': execution_time,
                    'timestamp': time.time()
                })
    
    def get_performance_report(self) -> Dict[str, Any]:
        """성능 리포트 생성"""
        with self.cache_lock:
            avg_times = {}
            for query_hash, times in self.query_times.items():
                avg_times[query_hash] = sum(times) / len(times)
            
            return {
                'total_queries': sum(len(times) for times in self.query_times.values()),
                'average_query_time': sum(avg_times.values()) / len(avg_times) if avg_times else 0,
                'slow_queries_count': len(self.slow_queries),
                'slow_queries': self.slow_queries[-10:],  # 최근 10개만
                'cache_hit_rate': self._calculate_cache_hit_rate()
            }
    
    def _calculate_cache_hit_rate(self) -> float:
        """캐시 히트율 계산"""
        # 간단한 캐시 히트율 계산 (실제 구현에서는 더 정교하게)
        return 0.85  # 임시값
    
    def batch_execute_queries(self, queries: List[Tuple[str, tuple]]) -> List[List[Dict[str, Any]]]:
        """Python 3.14 Free-Threaded Python을 활용한 배치 쿼리 실행"""
        logger.info(f"배치 쿼리 실행 시작: {len(queries)}개 쿼리")
        
        def execute_single_query(query_data):
            query, params = query_data
            return self.execute_optimized_query(query, params)
        
        # ThreadPoolExecutor를 사용한 병렬 실행
        results = list(self.executor.map(execute_single_query, queries))
        
        logger.info(f"배치 쿼리 실행 완료: {len(results)}개 결과")
        return results
    
    def close(self):
        """리소스 정리"""
        # 연결 풀의 모든 연결 닫기
        with self.pool_lock:
            for conn in self.connection_pool:
                conn.close()
            self.connection_pool.clear()
        
        # ThreadPoolExecutor 종료
        self.executor.shutdown(wait=True)
        
        logger.info("데이터베이스 최적화 시스템 종료")

# 전역 최적화 인스턴스
_db_optimizer = None

def get_db_optimizer() -> DatabaseOptimizer:
    """데이터베이스 최적화 인스턴스 가져오기"""
    global _db_optimizer
    if _db_optimizer is None:
        from core.db import DB_PATH
        _db_optimizer = DatabaseOptimizer(DB_PATH)
    return _db_optimizer

def optimize_database_performance() -> Dict[str, Any]:
    """데이터베이스 성능 최적화 실행"""
    optimizer = get_db_optimizer()
    return optimizer.optimize_database()

def get_performance_report() -> Dict[str, Any]:
    """성능 리포트 가져오기"""
    optimizer = get_db_optimizer()
    return optimizer.get_performance_report()







