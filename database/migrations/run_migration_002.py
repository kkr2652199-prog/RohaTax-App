"""
결제 관리 시스템 마이그레이션 실행 스크립트
002_create_payment_history.sql 실행
"""

import sqlite3
import os

# 프로젝트 루트 경로
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, 'database', 'app.db')
MIGRATION_FILE = os.path.join(os.path.dirname(__file__), '002_create_payment_history.sql')

def run_migration():
    """마이그레이션 실행"""
    try:
        # 데이터베이스 연결
        conn = sqlite3.connect(DB_PATH)
        
        # 마이그레이션 파일 읽기 및 실행
        with open(MIGRATION_FILE, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        conn.executescript(migration_sql)
        conn.commit()
        conn.close()
        
        print(f"[SUCCESS] 마이그레이션 실행 완료: {MIGRATION_FILE}")
        return True
        
    except Exception as e:
        print(f"[ERROR] 마이그레이션 실행 실패: {str(e)}")
        return False

if __name__ == '__main__':
    run_migration()

