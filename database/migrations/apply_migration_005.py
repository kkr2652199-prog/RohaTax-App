"""
마이그레이션 005 적용 스크립트
token_history 테이블에 source_type 컬럼 추가
"""
import sqlite3
import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.db import get_conn


def add_column_if_not_exists(conn: sqlite3.Connection, table_name: str, column_name: str, column_def: str) -> bool:
    """
    테이블에 컬럼이 없으면 추가하는 안전한 함수
    
    Args:
        conn: 데이터베이스 연결
        table_name: 테이블명
        column_name: 컬럼명
        column_def: 컬럼 정의 (예: "TEXT DEFAULT 'PAID'")
    
    Returns:
        bool: 컬럼이 추가되었으면 True, 이미 존재하면 False
    """
    try:
        # 테이블 구조 확인
        cursor = conn.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]
        
        if column_name in columns:
            print(f"[INFO] 컬럼 '{column_name}'이 이미 존재합니다.")
            return False
        
        # 컬럼 추가
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}")
        print(f"[SUCCESS] 컬럼 '{column_name}'이 추가되었습니다.")
        return True
        
    except Exception as e:
        print(f"[ERROR] 컬럼 추가 중 오류 발생: {str(e)}")
        raise


def apply_migration_005():
    """마이그레이션 005 적용"""
    try:
        with get_conn() as conn:
            print("=" * 60)
            print("마이그레이션 005: token_history에 source_type 컬럼 추가")
            print("=" * 60)
            
            # 1. source_type 컬럼 추가
            add_column_if_not_exists(
                conn, 
                'token_history', 
                'source_type', 
                "TEXT DEFAULT 'PAID'"
            )
            
            # 2. 인덱스 추가
            try:
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_token_history_source_type 
                    ON token_history(source_type)
                """)
                print("[SUCCESS] 인덱스 'idx_token_history_source_type' 생성 완료")
            except Exception as e:
                print(f"[WARNING] 인덱스 생성 중 오류 (이미 존재할 수 있음): {str(e)}")
            
            try:
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_token_history_source_expires 
                    ON token_history(source_type, expires_at) 
                    WHERE expires_at IS NOT NULL
                """)
                print("[SUCCESS] 인덱스 'idx_token_history_source_expires' 생성 완료")
            except Exception as e:
                print(f"[WARNING] 인덱스 생성 중 오류 (이미 존재할 수 있음): {str(e)}")
            
            conn.commit()
            print("\n[SUCCESS] 마이그레이션 005 적용 완료!")
            print("=" * 60)
            
    except Exception as e:
        print(f"\n[ERROR] 마이그레이션 적용 실패: {str(e)}")
        raise


if __name__ == '__main__':
    apply_migration_005()

