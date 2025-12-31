#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
본진 데이터베이스를 homepage1로 복사하는 스크립트

주의사항:
- 본진의 DB를 homepage1에 복사
- 활동 내역은 초기화 (reset_activity_logs_only.py 실행)
- 유저 정보, 결제 내역, 상품 정보는 보존
"""

import sqlite3
import os
import shutil
from datetime import datetime

# 경로 설정
MAIN_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'database', 'app.db')
HOMEPAGE1_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'app.db')
BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'backups')


def backup_homepage1_db():
    """homepage1 DB 백업"""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(BACKUP_DIR, f'app_before_sync_{timestamp}.db')
    
    if os.path.exists(HOMEPAGE1_DB_PATH):
        shutil.copy2(HOMEPAGE1_DB_PATH, backup_path)
        print(f"✅ homepage1 DB 백업 완료: {backup_path}")
        return backup_path
    else:
        print("⚠️  homepage1 DB 파일이 없습니다 (새로 생성됩니다)")
        return None


def copy_main_db_to_homepage1():
    """본진 DB를 homepage1로 복사"""
    if not os.path.exists(MAIN_DB_PATH):
        print(f"❌ 본진 DB 파일이 없습니다: {MAIN_DB_PATH}")
        return False
    
    # homepage1 database 디렉토리 생성
    os.makedirs(os.path.dirname(HOMEPAGE1_DB_PATH), exist_ok=True)
    
    # 본진 DB 복사
    shutil.copy2(MAIN_DB_PATH, HOMEPAGE1_DB_PATH)
    print(f"✅ 본진 DB 복사 완료: {HOMEPAGE1_DB_PATH}")
    
    # 파일 권한 확인
    if os.path.exists(HOMEPAGE1_DB_PATH):
        file_size = os.path.getsize(HOMEPAGE1_DB_PATH)
        print(f"✅ 복사된 DB 크기: {file_size:,} bytes")
        return True
    else:
        print("❌ DB 복사 실패")
        return False


def verify_db_sync():
    """DB 동기화 확인"""
    if not os.path.exists(HOMEPAGE1_DB_PATH):
        print("❌ homepage1 DB 파일이 없습니다")
        return False
    
    conn = sqlite3.connect(HOMEPAGE1_DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    
    print("\n=== DB 동기화 확인 ===")
    
    # 테이블 목록 확인
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"✅ 테이블 수: {len(tables)}개")
    
    # 주요 테이블 데이터 확인
    check_tables = ['users', 'payment_history', 'product_packages', 'subscription_plans']
    for table in check_tables:
        if table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"✅ {table}: {count}개")
            except Exception as e:
                print(f"⚠️  {table}: 확인 실패 ({e})")
        else:
            print(f"⏭️  {table}: 테이블 없음")
    
    conn.close()
    return True


def main():
    """메인 함수"""
    print("=" * 60)
    print("본진 → homepage1 데이터베이스 동기화")
    print("=" * 60)
    
    # 1. homepage1 DB 백업
    print("\n=== 1단계: homepage1 DB 백업 ===")
    backup_path = backup_homepage1_db()
    
    # 2. 본진 DB 복사
    print("\n=== 2단계: 본진 DB 복사 ===")
    if not copy_main_db_to_homepage1():
        return
    
    # 3. 동기화 확인
    print("\n=== 3단계: 동기화 확인 ===")
    verify_db_sync()
    
    print("\n" + "=" * 60)
    print("✅ DB 동기화 완료!")
    print("=" * 60)
    print("\n다음 단계:")
    print("  python scripts/reset_activity_logs_only.py")
    print("  (활동 내역 초기화 실행)")
    
    if backup_path:
        print(f"\n백업 파일: {backup_path}")


if __name__ == '__main__':
    main()

