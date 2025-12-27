#!/usr/bin/env python3
"""
서버 배포 자동화 스크립트
로컬에서 개발한 애플리케이션을 인터넷 서버에 배포할 때 필요한 모든 설정을 자동으로 수행합니다.
"""

import sqlite3
import os
import sys
from pathlib import Path

# core.db 모듈의 마이그레이션 함수 사용
try:
    from core.db import _apply_migrations as apply_core_migrations
    USE_CORE_MIGRATIONS = True
except ImportError:
    USE_CORE_MIGRATIONS = False

# 프로젝트 루트 경로
project_root = Path(__file__).parent.parent
DB_PATH = project_root / 'database' / 'app.db'
SCHEMA_PATH = project_root / 'database' / 'schema.sql'
MIGRATIONS_DIR = project_root / 'database' / 'migrations'


def ensure_database_directory():
    """데이터베이스 디렉토리 생성"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    print(f"✅ 데이터베이스 디렉토리 확인: {DB_PATH.parent}")


def create_orders_table(conn):
    """orders 테이블 생성 (누락 시)"""
    cursor = conn.cursor()
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                merchant_uid TEXT UNIQUE NOT NULL,
                order_uid TEXT UNIQUE,
                status TEXT DEFAULT 'pending',
                amount INTEGER DEFAULT 0,
                token_amount INTEGER DEFAULT 0,
                supply_price INTEGER DEFAULT 0,
                vat INTEGER DEFAULT 0,
                quantity INTEGER DEFAULT 1,
                payment_method TEXT,
                product_name TEXT,
                tax_evidence_requested INTEGER DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(product_id) REFERENCES products(id)
            )
        ''')
        
        # 인덱스 생성
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_merchant_uid ON orders(merchant_uid)')
        
        conn.commit()
        print("✅ orders 테이블 생성 완료")
        return True
    except Exception as e:
        print(f"⚠️ orders 테이블 생성 중 오류: {e}")
        return False


def apply_migrations(conn):
    """마이그레이션 파일 자동 적용"""
    if not MIGRATIONS_DIR.exists():
        print(f"⚠️ 마이그레이션 디렉토리 없음: {MIGRATIONS_DIR}")
        return
    
    migration_files = sorted([f for f in MIGRATIONS_DIR.glob('*.sql')])
    if not migration_files:
        print("⚠️ 마이그레이션 파일 없음")
        return
    
    cursor = conn.cursor()
    applied_count = 0
    skipped_count = 0
    
    for migration_file in migration_files:
        try:
            with open(migration_file, 'r', encoding='utf-8') as f:
                sql = f.read()
            
            cursor.executescript(sql)
            conn.commit()
            applied_count += 1
            print(f"✅ 마이그레이션 적용: {migration_file.name}")
        except sqlite3.Error as e:
            # 이미 적용된 마이그레이션은 무시
            error_msg = str(e).lower()
            if 'already exists' in error_msg or 'duplicate' in error_msg:
                skipped_count += 1
                print(f"⏭️  이미 적용됨: {migration_file.name}")
            else:
                print(f"⚠️ 마이그레이션 오류 ({migration_file.name}): {e}")
        except Exception as e:
            print(f"⚠️ 마이그레이션 오류 ({migration_file.name}): {e}")
    
    if applied_count > 0:
        print(f"✅ 총 {applied_count}개 마이그레이션 적용 완료")
    if skipped_count > 0:
        print(f"⏭️  {skipped_count}개 마이그레이션은 이미 적용됨")


def check_required_tables(conn):
    """필수 테이블 존재 확인"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = {row[0] for row in cursor.fetchall()}
    
    required_tables = {
        'users', 'products', 'orders', 'activity_logs', 
        'payment_history', 'token_history', 'settings'
    }
    
    missing_tables = required_tables - existing_tables
    
    if missing_tables:
        print(f"⚠️ 누락된 테이블: {', '.join(missing_tables)}")
        return False
    else:
        print("✅ 모든 필수 테이블 존재 확인")
        return True


def seed_initial_data(conn):
    """초기 데이터 삽입 (없는 경우만)"""
    cursor = conn.cursor()
    
    # products 테이블 확인
    cursor.execute('SELECT COUNT(*) FROM products')
    product_count = cursor.fetchone()[0]
    
    if product_count == 0:
        print("📦 초기 상품 데이터 삽입 중...")
        products = [
            ('Welcome Event', 'New user benefit', 0, 50, 0, 'event', 1),
            ('Welcome Period Event', 'New user benefit', 0, 0, 3, 'event_period', 1),
            ('Standard', 'Flexible plan', 300, 1, 0, 'package', 1),
            ('Premium', '100 package', 15000, 100, 0, 'package', 1),
            ('Gold', 'Specialist plan', 100000, 999999, 30, 'subscription', 1),
        ]
        
        for p in products:
            name, desc, price, token, duration, ptype, active = p
            cursor.execute('SELECT id FROM products WHERE name = ?', (name,))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO products (name, description, price, token_amount, duration_days, type, is_active, vat_included, created_at, updated_at) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, 0, datetime('now', 'localtime'), datetime('now', 'localtime'))
                """, (name, desc, price, token, duration, ptype, active))
        
        conn.commit()
        print("✅ 초기 상품 데이터 삽입 완료")
    else:
        print(f"✅ 상품 데이터 이미 존재 ({product_count}개)")


def main():
    """메인 배포 프로세스"""
    print("=" * 60)
    print("🚀 서버 배포 자동화 시작")
    print("=" * 60)
    
    # 1. 데이터베이스 디렉토리 확인
    ensure_database_directory()
    
    # 2. 데이터베이스 연결
    if not DB_PATH.exists():
        print(f"📁 데이터베이스 파일 없음. 초기화 중...")
        from core.db import init_db
        init_db()
        print("✅ 데이터베이스 초기화 완료")
    
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    
    try:
        # 3. 마이그레이션 적용
        print("\n📋 마이그레이션 적용 중...")
        if USE_CORE_MIGRATIONS:
            # core.db의 마이그레이션 함수 사용 (더 안정적)
            apply_core_migrations(conn)
            print("✅ core.db 마이그레이션 적용 완료")
        else:
            # 직접 마이그레이션 적용
            apply_migrations(conn)
        
        # 4. orders 테이블 생성 (누락 시)
        print("\n📦 필수 테이블 확인 중...")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orders'")
        if not cursor.fetchone():
            create_orders_table(conn)
        else:
            print("✅ orders 테이블 이미 존재")
        
        # 5. 필수 테이블 확인
        check_required_tables(conn)
        
        # 6. 초기 데이터 삽입
        print("\n🌱 초기 데이터 확인 중...")
        seed_initial_data(conn)
        
        print("\n" + "=" * 60)
        print("✅ 서버 배포 자동화 완료!")
        print("=" * 60)
        print("\n다음 단계:")
        print("1. 서버 재시작: pkill -f 'python3 app.py' && ...")
        print("2. 브라우저에서 https://rohatax.com 접속 테스트")
        
    except Exception as e:
        print(f"\n❌ 배포 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        conn.close()


if __name__ == '__main__':
    main()

