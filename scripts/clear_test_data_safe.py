#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
배포 서버 테스트 데이터만 안전하게 삭제하는 스크립트

⚠️ 주의사항:
- 유저 정보는 절대 건들지 않음
- 기능은 그대로 유지
- 테스트 데이터만 삭제:
  - 결제 로그 (payment_history)
  - 활동 로그 (activity_logs)
  - 황동 구매 내역 (token_history에서 구매 관련)
"""

import os
import sys
import sqlite3
from datetime import datetime
from pathlib import Path

# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "database" / "app.db"
BACKUP_DIR = PROJECT_ROOT / "database" / "backups"

def create_backup():
    """데이터베이스 백업 생성"""
    if not DB_PATH.exists():
        print("❌ 오류: 데이터베이스 파일을 찾을 수 없습니다.")
        sys.exit(1)
    
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"app_db_before_clear_test_{timestamp}.db"
    
    print(f"📦 데이터베이스 백업 생성 중: {backup_path}")
    
    # SQLite 백업
    source_conn = sqlite3.connect(str(DB_PATH))
    backup_conn = sqlite3.connect(str(backup_path))
    source_conn.backup(backup_conn)
    source_conn.close()
    backup_conn.close()
    
    print(f"✅ 백업 완료: {backup_path}")
    return backup_path

def get_table_counts(conn):
    """테이블별 레코드 수 확인"""
    cursor = conn.cursor()
    counts = {}
    
    tables = [
        'users',
        'payment_history',
        'activity_logs',
        'token_history',
        'conversion_logs'
    ]
    
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            counts[table] = cursor.fetchone()[0]
        except sqlite3.OperationalError:
            counts[table] = 0
    
    return counts

def clear_test_data(conn):
    """테스트 데이터만 안전하게 삭제"""
    cursor = conn.cursor()
    
    print("\n" + "=" * 60)
    print("테스트 데이터 삭제 시작")
    print("=" * 60)
    
    # 삭제 전 레코드 수 확인
    before_counts = get_table_counts(conn)
    print("\n[삭제 전 레코드 수]")
    for table, count in before_counts.items():
        print(f"  {table}: {count}개")
    
    deleted_counts = {}
    
    # 1. 결제 로그 삭제 (payment_history)
    print("\n[1] 결제 로그 삭제 중...")
    try:
        cursor.execute("SELECT COUNT(*) FROM payment_history")
        before = cursor.fetchone()[0]
        cursor.execute("DELETE FROM payment_history")
        deleted_counts['payment_history'] = before
        print(f"  ✅ {before}개 결제 로그 삭제됨")
    except sqlite3.OperationalError as e:
        print(f"  ⚠️  payment_history 테이블 없음: {e}")
        deleted_counts['payment_history'] = 0
    
    # 2. 활동 로그 삭제 (activity_logs)
    print("\n[2] 활동 로그 삭제 중...")
    try:
        cursor.execute("SELECT COUNT(*) FROM activity_logs")
        before = cursor.fetchone()[0]
        cursor.execute("DELETE FROM activity_logs")
        deleted_counts['activity_logs'] = before
        print(f"  ✅ {before}개 활동 로그 삭제됨")
    except sqlite3.OperationalError as e:
        print(f"  ⚠️  activity_logs 테이블 없음: {e}")
        deleted_counts['activity_logs'] = 0
    
    # 3. 황동 구매 내역 삭제 (token_history에서 구매 관련)
    print("\n[3] 황동 구매 내역 삭제 중...")
    try:
        # 구매 관련 토큰 이력 삭제 (change_type이 'grant'이고 source_type이 'PAID'인 것)
        cursor.execute("""
            SELECT COUNT(*) FROM token_history 
            WHERE change_type = 'grant' AND source_type = 'PAID'
        """)
        before = cursor.fetchone()[0]
        
        cursor.execute("""
            DELETE FROM token_history 
            WHERE change_type = 'grant' AND source_type = 'PAID'
        """)
        deleted_counts['token_history_purchase'] = before
        print(f"  ✅ {before}개 구매 내역 삭제됨")
    except sqlite3.OperationalError as e:
        print(f"  ⚠️  token_history 테이블 없음: {e}")
        deleted_counts['token_history_purchase'] = 0
    
    # 4. 변환 로그 삭제 (conversion_logs) - 테스트 데이터
    print("\n[4] 변환 로그 삭제 중...")
    try:
        cursor.execute("SELECT COUNT(*) FROM conversion_logs")
        before = cursor.fetchone()[0]
        cursor.execute("DELETE FROM conversion_logs")
        deleted_counts['conversion_logs'] = before
        print(f"  ✅ {before}개 변환 로그 삭제됨")
    except sqlite3.OperationalError as e:
        print(f"  ⚠️  conversion_logs 테이블 없음: {e}")
        deleted_counts['conversion_logs'] = 0
    
    # 커밋
    conn.commit()
    
    # 삭제 후 레코드 수 확인
    after_counts = get_table_counts(conn)
    print("\n[삭제 후 레코드 수]")
    for table, count in after_counts.items():
        print(f"  {table}: {count}개")
    
    print("\n" + "=" * 60)
    print("테스트 데이터 삭제 완료")
    print("=" * 60)
    
    total_deleted = sum(deleted_counts.values())
    print(f"\n총 삭제된 레코드: {total_deleted}개")
    
    return deleted_counts

def verify_users_intact(conn):
    """유저 정보가 그대로인지 확인"""
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT id, username, email, plan_type, token_balance FROM users LIMIT 5")
        sample_users = cursor.fetchall()
        
        print("\n" + "=" * 60)
        print("✅ 유저 정보 확인 (절대 건들지 않음)")
        print("=" * 60)
        print(f"총 유저 수: {user_count}명")
        print("\n[샘플 유저 정보]")
        for user in sample_users:
            print(f"  ID: {user[0]}, 사용자명: {user[1]}, 이메일: {user[2]}, 등급: {user[3]}, 토큰: {user[4]}")
        
        return True
    except sqlite3.OperationalError as e:
        print(f"⚠️  users 테이블 확인 실패: {e}")
        return False

def main():
    """메인 함수"""
    print("=" * 60)
    print("배포 서버 테스트 데이터 삭제 스크립트")
    print("=" * 60)
    print("\n⚠️  주의사항:")
    print("  - 유저 정보는 절대 건들지 않습니다")
    print("  - 기능은 그대로 유지됩니다")
    print("  - 테스트 데이터만 삭제됩니다:")
    print("    • 결제 로그 (payment_history)")
    print("    • 활동 로그 (activity_logs)")
    print("    • 황동 구매 내역 (token_history)")
    print("    • 변환 로그 (conversion_logs)")
    print()
    
    # 확인
    response = input("계속하시겠습니까? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("취소되었습니다.")
        sys.exit(0)
    
    # 데이터베이스 파일 확인
    if not DB_PATH.exists():
        print(f"❌ 오류: 데이터베이스 파일을 찾을 수 없습니다: {DB_PATH}")
        sys.exit(1)
    
    # 백업 생성
    backup_path = create_backup()
    
    # 데이터베이스 연결
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    
    try:
        # 테스트 데이터 삭제
        deleted_counts = clear_test_data(conn)
        
        # 유저 정보 확인
        verify_users_intact(conn)
        
        print("\n" + "=" * 60)
        print("✅ 작업 완료!")
        print("=" * 60)
        print(f"백업 파일: {backup_path}")
        print("\n삭제된 데이터:")
        for table, count in deleted_counts.items():
            if count > 0:
                print(f"  - {table}: {count}개")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        print(f"백업 파일에서 복원하세요: {backup_path}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    main()

