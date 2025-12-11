"""이벤트 상품 확인 및 추가 스크립트"""
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'database', 'app.db')

def check_event_products():
    """이벤트 상품 확인"""
    if not os.path.exists(DB_PATH):
        print("❌ 데이터베이스 파일이 없습니다:", DB_PATH)
        return False
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 이벤트 상품 조회
        cursor.execute("""
            SELECT id, name, price, type, token_amount, is_active 
            FROM products 
            WHERE price = 0 OR type = 'event'
        """)
        results = cursor.fetchall()
        
        print("=" * 60)
        print("1️⃣  데이터베이스 검증 결과")
        print("=" * 60)
        print(f"이벤트 상품 개수: {len(results)}")
        
        if results:
            print("\n✅ 발견된 이벤트 상품:")
            for r in results:
                print(f"  - ID: {r[0]}, 이름: {r[1]}, 가격: {r[2]}, 타입: {r[3]}, 토큰: {r[4]}, 활성: {r[5]}")
            conn.close()
            return True
        else:
            print("\n❌ 이벤트 상품이 없습니다. 테스트 상품을 추가합니다...")
            conn.close()
            return False
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False

def add_test_event_product():
    """테스트 이벤트 상품 추가"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # products 테이블 존재 확인
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='products'
        """)
        if not cursor.fetchone():
            print("❌ products 테이블이 없습니다. 테이블을 생성합니다...")
            cursor.execute("""
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
                )
            """)
            conn.commit()
        
        # 테스트 이벤트 상품 추가
        cursor.execute("""
            INSERT INTO products (name, description, price, token_amount, type, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "신규 가입 혜택(무료)",
            "신규 회원 가입 시 60개의 무료 토큰이 즉시 지급됩니다",
            0,
            60,
            "event",
            1,
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        product_id = cursor.lastrowid
        print(f"✅ 테스트 이벤트 상품 추가 완료 (ID: {product_id})")
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 상품 추가 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    has_products = check_event_products()
    
    if not has_products:
        add_test_event_product()
        print("\n" + "=" * 60)
        print("재확인 중...")
        print("=" * 60)
        check_event_products()







