"""
상품 관리 시스템 완전 복구 스크립트
- products 테이블 생성
- 기본 상품 5개 자동 생성
"""
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / 'database' / 'app.db'

# 1. products 테이블 생성
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

# 2. 기본 상품 5개 데이터
DEFAULT_PRODUCTS = [
    {
        'name': 'Standard',
        'description': '기본 토큰 상품',
        'price': 500,
        'token_amount': 1,
        'type': 'basic',
        'vat_included': 0,
        'duration_days': None,
        'token_validity_days': None,
        'one_time_limit': 0,
        'is_active': 1,
    },
    {
        'name': 'Premium Package',
        'description': '할인 패키지',
        'price': 25000,
        'token_amount': 100,
        'type': 'package',
        'vat_included': 0,
        'duration_days': None,
        'token_validity_days': None,
        'one_time_limit': 0,
        'is_active': 1,
    },
    {
        'name': 'Gold Membership',
        'description': '무제한 이용권',
        'price': 70000,
        'token_amount': -1,
        'type': 'subscription',
        'vat_included': 0,
        'duration_days': None,
        'token_validity_days': None,
        'one_time_limit': 0,
        'is_active': 1,
    },
    {
        'name': 'Welcome Event',
        'description': '신규 가입자를 위한 무료 토큰 혜택',
        'price': 0,
        'token_amount': 50,
        'type': 'event',
        'vat_included': 1,
        'duration_days': None,
        'token_validity_days': 0,
        'one_time_limit': 1,
        'is_active': 0,
    },
    {
        'name': 'Welcome Period Event',
        'description': '신규 가입자를 위한 기간제 혜택',
        'price': 0,
        'token_amount': 0,
        'type': 'event_period',
        'vat_included': 1,
        'duration_days': 3,
        'token_validity_days': None,
        'one_time_limit': 1,
        'is_active': 0,
    },
]

def main():
    print("🔧 상품 관리 시스템 복구 시작...\n")
    
    if not DB_PATH.exists():
        print(f"❌ 데이터베이스 파일이 없습니다: {DB_PATH}")
        return
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            # Step 1: 테이블 생성
            print("1️⃣  products 테이블 생성 중...")
            conn.executescript(CREATE_TABLE_SQL)
            print("   ✅ 테이블 생성 완료\n")
            
            # Step 2: 기존 데이터 확인
            cursor = conn.execute("SELECT COUNT(*) FROM products")
            count = cursor.fetchone()[0]
            
            if count > 0:
                print(f"2️⃣  기존 상품 데이터 {count}개 발견")
                print("   ⚠️  기존 데이터를 유지합니다 (덮어쓰지 않음)\n")
            else:
                print("2️⃣  기본 상품 데이터 삽입 중...")
                
                for product in DEFAULT_PRODUCTS:
                    conn.execute("""
                        INSERT INTO products 
                        (name, description, price, token_amount, type, vat_included, 
                         duration_days, token_validity_days, one_time_limit, is_active)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        product['name'],
                        product['description'],
                        product['price'],
                        product['token_amount'],
                        product['type'],
                        product['vat_included'],
                        product['duration_days'],
                        product['token_validity_days'],
                        product['one_time_limit'],
                        product['is_active'],
                    ))
                
                conn.commit()
                print(f"   ✅ {len(DEFAULT_PRODUCTS)}개 기본 상품 생성 완료\n")
            
            # Step 3: 최종 확인
            print("3️⃣  최종 상품 목록:")
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT id, name, type, price, token_amount, is_active 
                FROM products 
                ORDER BY id
            """)
            products = cursor.fetchall()
            
            for p in products:
                status = "ON" if p['is_active'] else "OFF"
                print(f"   [{p['id']}] {p['name']:25s} | {p['type']:15s} | {p['price']:8,}원 | {p['token_amount']:4d}토큰 | [{status}]")
            
            print("\n" + "="*70)
            print("✅ 상품 관리 시스템 복구 완료!")
            print("="*70)
            print("\n💡 다음 단계:")
            print("   1. 서버를 재시작하세요")
            print("   2. 관리자 페이지 > 상품 관리 탭으로 이동")
            print("   3. '저장' 버튼이 정상 작동하는지 확인")
            
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()











