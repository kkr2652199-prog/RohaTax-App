#!/usr/bin/env python3
"""
백업 파일에서 데이터베이스 복원 스크립트
가장 오래된 백업(초기화 전)을 찾아서 복원합니다.
"""

import os
import sys
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path

# Windows 인코딩 설정
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backup_dir = os.path.join(project_root, 'database', 'backups')
main_db_path = os.path.join(project_root, 'database', 'app.db')

def check_database_products(db_path):
    """데이터베이스에 상품 정보가 있는지 확인"""
    try:
        conn = sqlite3.connect(db_path, timeout=5.0)
        cursor = conn.cursor()
        
        products = cursor.execute('SELECT COUNT(*) FROM products').fetchone()[0]
        packages = cursor.execute('SELECT COUNT(*) FROM product_packages').fetchone()[0]
        plans = cursor.execute('SELECT COUNT(*) FROM subscription_plans').fetchone()[0]
        
        conn.close()
        return products, packages, plans
    except Exception as e:
        return None, None, None

def restore_from_backup():
    """백업 파일에서 데이터베이스 복원"""
    
    print("=" * 60)
    print("백업 파일에서 데이터베이스 복원")
    print("=" * 60)
    
    if not os.path.exists(backup_dir):
        print(f"\n[ERROR] 백업 디렉토리가 없습니다: {backup_dir}")
        return False
    
    # 백업 파일 목록 가져오기
    backup_files = []
    for file in os.listdir(backup_dir):
        if file.endswith('.db') and not file.endswith('-wal') and not file.endswith('-shm'):
            file_path = os.path.join(backup_dir, file)
            mtime = os.path.getmtime(file_path)
            backup_files.append((file, file_path, mtime))
    
    if not backup_files:
        print(f"\n[ERROR] 백업 파일이 없습니다.")
        return False
    
    # 시간순으로 정렬 (오래된 것부터)
    backup_files.sort(key=lambda x: x[2])
    
    print(f"\n[1단계] 백업 파일 확인 중...")
    print(f"  발견된 백업 파일: {len(backup_files)}개\n")
    
    # 각 백업 파일 확인
    best_backup = None
    best_score = 0
    
    for file, file_path, mtime in backup_files:
        products, packages, plans = check_database_products(file_path)
        
        if products is not None:
            score = products + packages + plans
            date_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
            
            status = "✓" if score > 0 else "✗"
            print(f"  {status} {file}")
            print(f"     날짜: {date_str}")
            print(f"     Products: {products}, Packages: {packages}, Plans: {plans}")
            print(f"     점수: {score}")
            print()
            
            if score > best_score:
                best_score = score
                best_backup = (file, file_path, mtime)
    
    if not best_backup:
        print(f"  [ERROR] 상품 정보가 있는 백업 파일이 없습니다.")
        return False
    
    print(f"\n[2단계] 최적 백업 파일 선택")
    print(f"  선택된 파일: {best_backup[0]}")
    print(f"  상품 정보: Products + Packages + Plans = {best_score}개")
    
    # 복원 확인
    print(f"\n[3단계] 데이터베이스 복원 중...")
    
    # 기존 파일 백업
    if os.path.exists(main_db_path):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        current_backup = os.path.join(backup_dir, f'app_backup_before_restore_{timestamp}.db')
        try:
            shutil.copy2(main_db_path, current_backup)
            print(f"  [OK] 현재 데이터베이스 백업: {os.path.basename(current_backup)}")
        except Exception as e:
            print(f"  [WARNING] 백업 실패: {e}")
    
    # 복원 시도
    import time
    max_retries = 5
    for i in range(max_retries):
        try:
            time.sleep(0.5)
            # WAL 체크포인트
            try:
                temp_conn = sqlite3.connect(main_db_path, timeout=1.0)
                temp_conn.execute('PRAGMA wal_checkpoint(FULL)')
                temp_conn.close()
            except Exception:
                pass
            
            # 기존 파일 삭제
            if os.path.exists(main_db_path):
                os.remove(main_db_path)
            
            # WAL, SHM 파일 삭제
            for ext in ['-wal', '-shm']:
                wal_path = main_db_path + ext
                if os.path.exists(wal_path):
                    try:
                        os.remove(wal_path)
                    except Exception:
                        pass
            
            # 백업 파일 복사
            shutil.copy2(best_backup[1], main_db_path)
            print(f"  [OK] 데이터베이스 복원 완료")
            break
            
        except PermissionError:
            if i < max_retries - 1:
                print(f"  [INFO] 파일이 사용 중입니다. 대기 중... ({i+1}/{max_retries})")
            else:
                print(f"  [ERROR] 파일 복원 실패 (Flask 서버가 사용 중일 수 있음)")
                print(f"  [INFO] Flask 서버를 재시작한 후 다시 시도하세요.")
                return False
    
    # 복원 확인
    print(f"\n[4단계] 복원된 데이터베이스 확인 중...")
    products, packages, plans = check_database_products(main_db_path)
    
    if products is not None:
        print(f"  Products: {products}개")
        print(f"  Product Packages: {packages}개")
        print(f"  Subscription Plans: {plans}개")
        
        if products + packages + plans > 0:
            print(f"\n  [OK] 상품 정보 복원 완료!")
        else:
            print(f"\n  [WARNING] 상품 정보가 없습니다.")
    else:
        print(f"  [ERROR] 데이터베이스 확인 실패")
        return False
    
    print("\n" + "=" * 60)
    print("[OK] 백업 파일에서 데이터베이스 복원이 완료되었습니다!")
    print("=" * 60)
    print(f"\n복원된 데이터베이스: {main_db_path}")
    print(f"원본 백업 파일: {best_backup[0]}")
    print(f"\n[중요] Flask 서버를 재시작하면 새 데이터베이스를 사용합니다.")
    
    return True

if __name__ == '__main__':
    success = restore_from_backup()
    sys.exit(0 if success else 1)


