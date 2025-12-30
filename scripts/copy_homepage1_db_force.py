#!/usr/bin/env python3
"""homepage1 데이터베이스를 본진에 강제로 복사"""

import os
import sys
import shutil
import sqlite3
import time

# Windows 인코딩 설정
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
homepage1_db = os.path.join(project_root, 'homepage1', 'database', 'app.db')
main_db = os.path.join(project_root, 'database', 'app.db')
backup_dir = os.path.join(project_root, 'database', 'backups')

print("=" * 60)
print("homepage1 데이터베이스를 본진에 복사")
print("=" * 60)

# homepage1 데이터베이스 확인
if not os.path.exists(homepage1_db):
    print(f"\n[ERROR] homepage1 데이터베이스가 없습니다: {homepage1_db}")
    sys.exit(1)

# homepage1 데이터베이스 확인
print(f"\n[1단계] homepage1 데이터베이스 확인...")
conn = sqlite3.connect(homepage1_db)
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM products")
products = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM product_packages")
packages = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM subscription_plans")
plans = cursor.fetchone()[0]
conn.close()

print(f"  Products: {products}개")
print(f"  Product Packages: {packages}개")
print(f"  Subscription Plans: {plans}개")

if products == 0 and packages == 0:
    print(f"\n[ERROR] homepage1에도 상품 정보가 없습니다!")
    sys.exit(1)

# 백업 디렉토리 생성
os.makedirs(backup_dir, exist_ok=True)

# 본진 데이터베이스 백업
if os.path.exists(main_db):
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(backup_dir, f'app_backup_{timestamp}.db')
    try:
        shutil.copy2(main_db, backup_path)
        print(f"\n[2단계] 본진 데이터베이스 백업 완료: {os.path.basename(backup_path)}")
    except Exception as e:
        print(f"\n[WARNING] 백업 실패: {e}")

# homepage1 데이터베이스를 임시 파일로 복사
temp_db = main_db + '.new'
print(f"\n[3단계] homepage1 데이터베이스 복사 중...")
shutil.copy2(homepage1_db, temp_db)
print(f"  [OK] 복사 완료: {os.path.basename(temp_db)}")

# 기존 파일 삭제 시도
print(f"\n[4단계] 기존 데이터베이스 파일 교체 중...")
max_retries = 10
for i in range(max_retries):
    try:
        # WAL 체크포인트
        if os.path.exists(main_db):
            try:
                temp_conn = sqlite3.connect(main_db, timeout=1.0)
                temp_conn.execute('PRAGMA wal_checkpoint(FULL)')
                temp_conn.close()
            except Exception:
                pass
        
        time.sleep(1)
        
        # 기존 파일 삭제
        if os.path.exists(main_db):
            os.remove(main_db)
        
        # WAL, SHM 파일 삭제
        for ext in ['-wal', '-shm']:
            wal_path = main_db + ext
            if os.path.exists(wal_path):
                try:
                    os.remove(wal_path)
                except Exception:
                    pass
        
        # 새 파일로 교체
        os.rename(temp_db, main_db)
        print(f"  [OK] 데이터베이스 교체 완료!")
        break
        
    except PermissionError:
        if i < max_retries - 1:
            print(f"  [INFO] 파일이 사용 중입니다. 대기 중... ({i+1}/{max_retries})")
        else:
            print(f"  [ERROR] 파일 교체 실패 (Flask 서버가 사용 중)")
            print(f"  [INFO] Flask 서버를 재시작한 후 수동으로 교체하세요:")
            print(f"    {temp_db} → {main_db}")
            sys.exit(1)

# 복원 확인
print(f"\n[5단계] 복원된 데이터베이스 확인...")
conn = sqlite3.connect(main_db)
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM products")
restored_products = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM product_packages")
restored_packages = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM subscription_plans")
restored_plans = cursor.fetchone()[0]
conn.close()

print(f"  Products: {restored_products}개")
print(f"  Product Packages: {restored_packages}개")
print(f"  Subscription Plans: {restored_plans}개")

if restored_products == products and restored_packages == packages:
    print(f"\n[OK] 데이터베이스 복원 완료!")
    print(f"  상품 정보가 정상적으로 복원되었습니다.")
else:
    print(f"\n[WARNING] 데이터가 일치하지 않습니다.")
    print(f"  예상: Products {products}, Packages {packages}")
    print(f"  실제: Products {restored_products}, Packages {restored_packages}")

print("\n" + "=" * 60)


