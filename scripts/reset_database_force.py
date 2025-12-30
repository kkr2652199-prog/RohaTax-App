#!/usr/bin/env python3
"""
데이터베이스 강제 초기화 스크립트
테이블을 삭제하고 재생성합니다 (파일 삭제 없이).
"""

import os
import sys
import sqlite3
from datetime import datetime

# Windows 인코딩 설정
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from core.db import DB_PATH, SCHEMA_PATH, init_db

def reset_database_force():
    """데이터베이스 강제 초기화 (테이블 삭제 후 재생성)"""
    
    print("=" * 60)
    print("데이터베이스 강제 초기화 스크립트")
    print("=" * 60)
    
    db_path = DB_PATH
    
    if not os.path.exists(db_path):
        print(f"\n[INFO] 데이터베이스 파일이 없습니다. 새로 생성합니다.")
        init_db()
        print(f"[OK] 데이터베이스 초기화 완료")
        return True
    
    print(f"\n[1단계] 기존 데이터베이스 연결 중...")
    print(f"  데이터베이스 경로: {db_path}")
    
    try:
        # 데이터베이스 연결
        conn = sqlite3.connect(db_path, timeout=10.0)
        cursor = conn.cursor()
        
        print(f"[OK] 데이터베이스 연결 성공")
        
        # 모든 테이블 목록 가져오기
        print(f"\n[2단계] 기존 테이블 목록 조회 중...")
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        if tables:
            print(f"  발견된 테이블: {', '.join(tables)}")
        else:
            print(f"  테이블이 없습니다.")
        
        # 외래 키 제약 조건 비활성화
        print(f"\n[3단계] 외래 키 제약 조건 비활성화...")
        cursor.execute("PRAGMA foreign_keys = OFF")
        print(f"[OK] 외래 키 제약 조건 비활성화 완료")
        
        # 모든 테이블 삭제
        print(f"\n[4단계] 기존 테이블 삭제 중...")
        for table in tables:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
                print(f"  [OK] 테이블 삭제: {table}")
            except Exception as e:
                print(f"  [WARNING] 테이블 삭제 실패 ({table}): {e}")
        
        # 인덱스 삭제
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND name NOT LIKE 'sqlite_%'
        """)
        indexes = [row[0] for row in cursor.fetchall()]
        
        if indexes:
            print(f"\n[5단계] 기존 인덱스 삭제 중...")
            for index in indexes:
                try:
                    cursor.execute(f"DROP INDEX IF EXISTS {index}")
                    print(f"  [OK] 인덱스 삭제: {index}")
                except Exception as e:
                    print(f"  [WARNING] 인덱스 삭제 실패 ({index}): {e}")
        
        # 변경사항 커밋
        conn.commit()
        print(f"\n[OK] 기존 테이블 및 인덱스 삭제 완료")
        
        # 연결 종료
        conn.close()
        
        # 새 스키마로 초기화
        print(f"\n[6단계] 새 스키마로 데이터베이스 초기화 중...")
        init_db()
        print(f"[OK] 데이터베이스 초기화 완료")
        
        print("\n" + "=" * 60)
        print("[OK] 데이터베이스 초기화가 완료되었습니다!")
        print("=" * 60)
        
        return True
        
    except sqlite3.OperationalError as e:
        if "database is locked" in str(e).lower():
            print(f"\n[ERROR] 데이터베이스가 잠겨 있습니다.")
            print(f"  다른 프로세스(Flask 앱 등)가 데이터베이스를 사용 중입니다.")
            print(f"  모든 Python 프로세스를 종료한 후 다시 시도하세요.")
        else:
            print(f"\n[ERROR] 데이터베이스 작업 실패: {e}")
        return False
    except Exception as e:
        print(f"\n[ERROR] 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = reset_database_force()
    sys.exit(0 if success else 1)


