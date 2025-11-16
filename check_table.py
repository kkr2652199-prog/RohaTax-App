"""테이블 구조 확인 스크립트"""
import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / "database" / "app.db"
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# 테이블 존재 확인
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='activity_logs'")
if cursor.fetchone():
    print("[확인] activity_logs 테이블이 존재합니다.")
    
    # 테이블 구조 확인
    cursor.execute("PRAGMA table_info(activity_logs)")
    cols = cursor.fetchall()
    print(f"\n[컬럼] 총 {len(cols)}개 컬럼:")
    for col in cols:
        print(f"  - {col[1]:<25} {col[2]:<15} {'NOT NULL' if col[3] else 'NULL':<10}")
    
    # 인덱스 확인
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='activity_logs'")
    idxs = cursor.fetchall()
    print(f"\n[인덱스] 총 {len(idxs)}개 인덱스:")
    for idx in idxs:
        print(f"  - {idx[0]}")
else:
    print("[오류] activity_logs 테이블이 존재하지 않습니다.")

conn.close()

