"""
데이터베이스 체계적 관리 모듈
- 변환 통계 저장
- 에러 로깅
- 성능 모니터링
"""
import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import json

class DatabaseManager:
    """데이터베이스 관리자"""
    
    def __init__(self, db_path: str = "conversion_stats.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.init_database()
    
    def init_database(self):
        """데이터베이스 테이블 초기화"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 변환 기록 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversion_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                filename TEXT,
                file_size INTEGER,
                recipient_count INTEGER,
                success BOOLEAN,
                error_message TEXT,
                execution_time REAL,
                user_id INTEGER
            )
        ''')
        
        # 에러 기록 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS error_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                filename TEXT,
                error_type TEXT,
                error_message TEXT,
                stack_trace TEXT,
                severity TEXT,
                resolved BOOLEAN DEFAULT FALSE,
                user_id INTEGER
            )
        ''')
        
        # 성능 메트릭 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                conversion_duration REAL,
                memory_usage REAL,
                cpu_usage REAL,
                file_count INTEGER,
                success_rate REAL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def log_conversion(self, conversion_data: Dict[str, Any]):
        """변환 결과 로깅"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO conversion_logs 
            (timestamp, filename, file_size, recipient_count, success, error_message, execution_time, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            conversion_data.get('filename'),
            conversion_data.get('file_size'),
            conversion_data.get('recipient_count'),
            conversion_data.get('success', True),
            conversion_data.get('error_message'),
            conversion_data.get('execution_time'),
            conversion_data.get('user_id')
        ))
        
        conn.commit()
        conn.close()
    
    def log_error(self, error_data: Dict[str, Any]):
        """에러 로깅"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO error_logs 
            (timestamp, filename, error_type, error_message, stack_trace, severity, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            error_data.get('filename'),
            error_data.get('error_type'),
            error_data.get('error_message'),
            error_data.get('stack_trace'),
            error_data.get('severity', 'ERROR'),
            error_data.get('user_id')
        ))
        
        conn.commit()
        conn.close()
    
    def get_conversion_stats(self, days: int = 30) -> Dict[str, Any]:

        """변환 통계 조회"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_conversions,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_conversions,
                AVG(recipient_count) as avg_recipients,
                AVG(execution_time) as avg_execution_time,
                COUNT(DISTINCT filename) as unique_files
            FROM conversion_logs 
            WHERE timestamp >= datetime('now', '-{} days')
        '''.format(days))


        stats = dict(cursor.fetchone())
        conn.close()
        
        # 성공률 계산
        if stats['total_conversions'] > 0:
            stats['success_rate'] = stats['successful_conversions'] / stats['total_conversions']
        else:
            stats['success_rate'] = 0.0
        
        return stats


    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """최근 에러들 조회"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM error_logs 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        errors = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return errors
    
    def get_file_conversion_history(self, filename: str) -> List[Dict[str, Any]]:
        """특정 파일의 변환 기록 조회"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM conversion_logs 
            WHERE filename LIKE ? 
            ORDER BY timestamp DESC
        ''', (f'%{filename}%',))
        
        history = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return history
    
    def cleanup_old_logs(self, days_to_keep: int = 90):
        """오래된 로그 정리"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM conversion_logs 
            WHERE timestamp < datetime('now', '-{} days')
        '''.format(days_to_keep))
        
        cursor.execute('''
            DELETE FROM error_logs 
            WHERE timestamp < datetime('now', '-{} days')
        '''.format(days_to_keep))
        
        deleted_rows = cursor.rowcount
        conn.commit()
        conn.close()
        
        self.logger.info(f"🧹 오래된 로그 {deleted_rows}개 정리 완료 ({days_to_keep}일 이전)")
        return deleted_rows

# 전역 데이터베이스 관리자 인스턴스
db_manager = DatabaseManager()









