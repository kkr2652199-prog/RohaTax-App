"""
마이그레이션 003 실행 스크립트
상품(패키지) 관리 테이블 생성
"""
import sqlite3
import os
import sys

# 프로젝트 루트 경로 설정
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, 'database', 'app.db')
MIGRATION_FILE = os.path.join(PROJECT_ROOT, 'database', 'migrations', '003_create_product_packages.sql')

def run_migration():
    """마이그레이션 실행"""
    conn = None
    try:
        if not os.path.exists(DB_PATH):
            print(f"[ERROR] 데이터베이스 파일을 찾을 수 없습니다: {DB_PATH}")
            return False
        
        if not os.path.exists(MIGRATION_FILE):
            print(f"[ERROR] 마이그레이션 파일을 찾을 수 없습니다: {MIGRATION_FILE}")
            return False
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        with open(MIGRATION_FILE, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        cursor.executescript(sql_script)
        conn.commit()
        
        print(f"[SUCCESS] 마이그레이션 실행 완료: 003_create_product_packages.sql")
        
        # 테이블 생성 확인
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='product_packages'")
        if cursor.fetchone():
            print("[SUCCESS] product_packages 테이블 생성 확인됨")
        else:
            print("[WARNING] product_packages 테이블이 생성되지 않았습니다")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 마이그레이션 실행 실패: {str(e)}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)

