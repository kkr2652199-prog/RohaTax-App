"""
products 테이블 생성 스크립트
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'database' / 'app.db'

# products 테이블 생성 SQL
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    price INTEGER NOT NULL DEFAULT 0,
    token_amount INTEGER NOT NULL DEFAULT 0,
    type TEXT NOT NULL DEFAULT 'basic',
    vat_included INTEGER NOT NULL DEFAULT 0,
    duration_days INTEGER,
    token_validity_days INTEGER,
    one_time_limit INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_products_type ON products(type);
CREATE INDEX IF NOT EXISTS idx_products_is_active ON products(is_active);
CREATE INDEX IF NOT EXISTS idx_products_price ON products(price);
"""

def main():
    print(f"📂 DB 경로: {DB_PATH}")
    
    if not DB_PATH.exists():
        print(f"❌ 데이터베이스 파일이 존재하지 않습니다: {DB_PATH}")
        return
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            # 테이블 생성
            conn.executescript(CREATE_TABLE_SQL)
            
            # 확인
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='products'"
            )
            result = cursor.fetchone()
            
            if result:
                print("✅ products 테이블 생성 완료")
                
                # 컬럼 확인
                cursor = conn.execute("PRAGMA table_info(products)")
                columns = cursor.fetchall()
                print(f"📋 테이블 컬럼 ({len(columns)}개):")
                for col in columns:
                    print(f"   - {col[1]} ({col[2]})")
            else:
                print("❌ 테이블 생성 실패")
                
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

