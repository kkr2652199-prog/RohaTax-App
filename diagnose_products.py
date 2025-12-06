"""
상품 관리 시스템 진단 스크립트
"""
import sqlite3
from pathlib import Path
import sys

DB_PATH = Path(__file__).parent / 'database' / 'app.db'

def check_table_exists():
    """products 테이블 존재 여부 확인"""
    print("=" * 60)
    print("1️⃣  products 테이블 존재 여부 확인")
    print("=" * 60)
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='products'"
            )
            result = cursor.fetchone()
            
            if result:
                print("✅ products 테이블이 존재합니다")
                return True
            else:
                print("❌ products 테이블이 존재하지 않습니다")
                return False
    except Exception as e:
        print(f"❌ 오류: {e}")
        return False

def check_table_schema():
    """products 테이블 스키마 확인"""
    print("\n" + "=" * 60)
    print("2️⃣  products 테이블 스키마 확인")
    print("=" * 60)
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute("PRAGMA table_info(products)")
            columns = cursor.fetchall()
            
            if not columns:
                print("❌ 테이블 스키마를 가져올 수 없습니다")
                return False
            
            print(f"✅ 총 {len(columns)}개 컬럼:")
            expected_columns = {
                'id', 'name', 'description', 'price', 'token_amount',
                'type', 'vat_included', 'duration_days', 'token_validity_days',
                'one_time_limit', 'is_active', 'created_at', 'updated_at'
            }
            
            actual_columns = set()
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                actual_columns.add(col_name)
                print(f"   • {col_name:20s} ({col_type})")
            
            # 누락된 컬럼 확인
            missing = expected_columns - actual_columns
            if missing:
                print(f"\n⚠️  누락된 컬럼: {', '.join(missing)}")
                return False
            else:
                print("\n✅ 모든 필수 컬럼이 존재합니다")
                return True
                
    except Exception as e:
        print(f"❌ 오류: {e}")
        return False

def check_products_data():
    """products 테이블 데이터 확인"""
    print("\n" + "=" * 60)
    print("3️⃣  products 테이블 데이터 확인")
    print("=" * 60)
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT id, name, type, price, token_amount, is_active FROM products ORDER BY id"
            )
            products = cursor.fetchall()
            
            if not products:
                print("⚠️  상품 데이터가 없습니다 (빈 테이블)")
                print("\n💡 해결 방법:")
                print("   서버를 시작하면 자동으로 기본 상품 5개가 생성됩니다")
                print("   또는 관리자 페이지에서 '/admin/api/products' 호출 시 자동 생성")
                return False
            
            print(f"✅ 총 {len(products)}개 상품:")
            for p in products:
                status = "활성" if p['is_active'] else "비활성"
                print(f"   • ID {p['id']:2d} | {p['name']:25s} | {p['type']:15s} | {p['price']:8,}원 | {status}")
            
            return True
            
    except Exception as e:
        print(f"❌ 오류: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_api_routes():
    """API 라우트 파일 존재 확인"""
    print("\n" + "=" * 60)
    print("4️⃣  API 라우트 파일 확인")
    print("=" * 60)
    
    api_file = Path(__file__).parent / 'routes' / 'admin' / 'product_api.py'
    if api_file.exists():
        print(f"✅ {api_file.name} 존재")
        
        # 주요 엔드포인트 확인
        with open(api_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        endpoints = [
            ('/admin/api/products', 'GET', '상품 목록 조회'),
            ('/admin/api/products/<int:product_id>', 'PATCH', '상품 수정'),
            ('/admin/api/products/<int:product_id>', 'DELETE', '상품 삭제'),
        ]
        
        print("\n📡 API 엔드포인트:")
        for path, method, desc in endpoints:
            if f"@admin_bp.route('{path}'" in content and f"methods=['{method}']" in content:
                print(f"   ✅ {method:6s} {path:45s} - {desc}")
            else:
                print(f"   ❌ {method:6s} {path:45s} - {desc} (누락)")
        
        return True
    else:
        print(f"❌ {api_file} 파일이 없습니다")
        return False

def check_js_files():
    """프론트엔드 JS 파일 확인"""
    print("\n" + "=" * 60)
    print("5️⃣  프론트엔드 JS 파일 확인")
    print("=" * 60)
    
    js_file = Path(__file__).parent / 'static' / 'js' / 'admin' / 'product.js'
    if js_file.exists():
        print(f"✅ {js_file.name} 존재")
        
        with open(js_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 주요 함수 확인
        functions = [
            'loadProducts',
            'updateProduct',
            'handleStandardSubmit',
            'handlePremiumSubmit',
            'handleGoldSubmit',
        ]
        
        print("\n🔧 주요 함수:")
        for func in functions:
            if f"function {func}" in content or f"async function {func}" in content:
                print(f"   ✅ {func}()")
            else:
                print(f"   ❌ {func}() (누락)")
        
        return True
    else:
        print(f"❌ {js_file} 파일이 없습니다")
        return False

def main():
    print("\n🔍 상품 관리 시스템 진단 시작...\n")
    
    if not DB_PATH.exists():
        print(f"❌ 데이터베이스 파일이 없습니다: {DB_PATH}")
        sys.exit(1)
    
    results = {
        'table_exists': check_table_exists(),
        'schema_ok': False,
        'data_ok': False,
        'api_ok': check_api_routes(),
        'js_ok': check_js_files(),
    }
    
    if results['table_exists']:
        results['schema_ok'] = check_table_schema()
        results['data_ok'] = check_products_data()
    
    # 최종 진단 결과
    print("\n" + "=" * 60)
    print("📋 최종 진단 결과")
    print("=" * 60)
    
    all_ok = all(results.values())
    
    if all_ok:
        print("✅ 모든 시스템이 정상입니다!")
    else:
        print("❌ 다음 문제가 발견되었습니다:\n")
        
        if not results['table_exists']:
            print("   🔴 products 테이블이 없습니다")
            print("      → python create_products_table.py 실행")
        
        if results['table_exists'] and not results['schema_ok']:
            print("   🔴 테이블 스키마에 문제가 있습니다")
            print("      → 테이블을 삭제하고 재생성 필요")
        
        if results['table_exists'] and results['schema_ok'] and not results['data_ok']:
            print("   🟡 상품 데이터가 없습니다 (경고)")
            print("      → 서버 시작 시 자동으로 생성됩니다")
        
        if not results['api_ok']:
            print("   🔴 API 라우트 파일에 문제가 있습니다")
        
        if not results['js_ok']:
            print("   🔴 프론트엔드 JS 파일에 문제가 있습니다")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()









