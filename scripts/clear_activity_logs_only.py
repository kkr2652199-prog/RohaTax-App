#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
유저 활동 내역만 초기화하는 스크립트

⚠️ 주의사항:
- 유저 정보는 절대 건들지 않음
- 시스템 로직은 그대로 유지
- activity_logs 테이블만 삭제
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
    backup_path = BACKUP_DIR / f"app_db_before_clear_activity_{timestamp}.db"
    
    print(f"📦 데이터베이스 백업 생성 중: {backup_path}")
    
    # SQLite 백업
    source_conn = sqlite3.connect(str(DB_PATH))
    backup_conn = sqlite3.connect(str(backup_path))
    source_conn.backup(backup_conn)
    source_conn.close()
    backup_conn.close()
    
    print(f"✅ 백업 완료: {backup_path}")
    return backup_path

def clear_activity_logs(conn):
    """유저 활동 내역만 삭제"""
    cursor = conn.cursor()
    
    print("\n" + "=" * 60)
    print("유저 활동 내역 초기화")
    print("=" * 60)
    
    # 삭제 전 레코드 수 확인
    try:
        cursor.execute("SELECT COUNT(*) FROM activity_logs")
        before_count = cursor.fetchone()[0]
        print(f"\n[삭제 전] activity_logs: {before_count:,}개")
    except sqlite3.OperationalError:
        print("\n⚠️  activity_logs 테이블이 존재하지 않습니다.")
        return 0
    
    # 활동 로그 삭제
    print("\n🗑️  활동 로그 삭제 중...")
    cursor.execute("DELETE FROM activity_logs")
    deleted_count = cursor.rowcount
    
    # 커밋
    conn.commit()
    
    # 삭제 후 확인
    cursor.execute("SELECT COUNT(*) FROM activity_logs")
    after_count = cursor.fetchone()[0]
    
    print(f"[삭제 후] activity_logs: {after_count:,}개")
    print(f"\n✅ {deleted_count:,}개 활동 로그 삭제 완료")
    
    return deleted_count

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
    print("유저 활동 내역 초기화 스크립트")
    print("=" * 60)
    print("\n⚠️  주의사항:")
    print("  - 유저 정보는 절대 건들지 않습니다")
    print("  - 시스템 로직은 그대로 유지됩니다")
    print("  - activity_logs 테이블만 삭제됩니다")
    print()
    
    # 확인
    response = input("유저 활동 내역을 초기화하시겠습니까? (yes/no): ")
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
        # 활동 로그 삭제
        deleted_count = clear_activity_logs(conn)
        
        # 유저 정보 확인
        verify_users_intact(conn)
        
        print("\n" + "=" * 60)
        print("✅ 작업 완료!")
        print("=" * 60)
        print(f"백업 파일: {backup_path}")
        print(f"삭제된 활동 로그: {deleted_count:,}개")
        print("\n✅ 유저 정보는 그대로 유지되었습니다.")
        print("✅ 시스템 로직은 그대로 유지되었습니다.")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        print(f"백업 파일에서 복원하세요: {backup_path}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    main()

