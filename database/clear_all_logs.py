"""
통합 관제실 로그 기록 초기화 스크립트

주의: 이 스크립트는 모든 로그 기록을 영구적으로 삭제합니다.
사용자 정보(users 테이블)는 유지되며, 로그 기록만 삭제됩니다.

삭제 대상:
- activity_logs (활동 로그)
- token_history (토큰 이력)
- conversion_logs (변환 로그)
- usage_logs (사용 로그)
- validation_logs (검증 로그)
- payment_history (결제 이력, 존재하는 경우)
"""

import sqlite3
import os
import sys
from pathlib import Path
from datetime import datetime

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 프로젝트 루트 경로 (homepage1 디렉토리)
script_path = Path(__file__).resolve()
# database/clear_all_logs.py -> homepage1/database/clear_all_logs.py
project_root = script_path.parent.parent  # homepage1
db_path = project_root / 'database' / 'app.db'

def clear_all_logs():
    """모든 로그 기록을 초기화합니다."""
    
    if not db_path.exists():
        print(f"❌ 데이터베이스 파일을 찾을 수 없습니다: {db_path}")
        return False
    
    # 백업 파일명 생성
    backup_filename = f"app_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    backup_path = project_root / 'database' / 'backups' / backup_filename
    
    try:
        # 백업 디렉토리 생성
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 데이터베이스 백업
        print(f"📦 데이터베이스 백업 중: {backup_filename}")
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✅ 백업 완료: {backup_path}")
        
        # 데이터베이스 연결
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 삭제 전 레코드 수 확인
        tables_to_clear = [
            'activity_logs',
            'token_history',
            'conversion_logs',
            'usage_logs',
            'validation_logs',
            'payment_history'
        ]
        
        print("\n📊 삭제 전 레코드 수:")
        total_records = 0
        for table in tables_to_clear:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  - {table}: {count:,}건")
                total_records += count
            except sqlite3.OperationalError:
                print(f"  - {table}: 테이블 없음 (건너뜀)")
        
        print(f"\n총 {total_records:,}건의 로그 기록이 삭제됩니다.\n")
        
        # 자동 실행 모드 (명령줄 인자로 --auto 전달 시)
        auto_mode = '--auto' in sys.argv or '--yes' in sys.argv
        
        if not auto_mode:
            # 사용자 확인
            try:
                response = input("⚠️  정말로 모든 로그 기록을 삭제하시겠습니까? (yes/no): ")
                if response.lower() != 'yes':
                    print("❌ 작업이 취소되었습니다.")
                    conn.close()
                    return False
            except (EOFError, KeyboardInterrupt):
                print("\n⚠️  대화형 입력이 불가능합니다. --auto 옵션을 사용하세요.")
                print("   예: python clear_all_logs.py --auto")
                conn.close()
                return False
        else:
            print("⚠️  자동 모드: 모든 로그 기록을 삭제합니다...")
        
        # 로그 테이블 초기화
        print("\n🗑️  로그 기록 삭제 중...")
        deleted_counts = {}
        
        for table in tables_to_clear:
            try:
                # 테이블 존재 확인
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                if cursor.fetchone():
                    cursor.execute(f"DELETE FROM {table}")
                    deleted_count = cursor.rowcount
                    deleted_counts[table] = deleted_count
                    print(f"  ✅ {table}: {deleted_count:,}건 삭제 완료")
                else:
                    print(f"  ⚠️  {table}: 테이블 없음 (건너뜀)")
            except sqlite3.Error as e:
                print(f"  ❌ {table}: 삭제 실패 - {str(e)}")
        
        # AUTOINCREMENT 시퀀스 리셋 (SQLite는 자동으로 처리하지만 명시적으로)
        for table in tables_to_clear:
            try:
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                if cursor.fetchone():
                    # SQLite는 AUTOINCREMENT를 자동으로 관리하므로 별도 작업 불필요
                    pass
            except:
                pass
        
        # VACUUM 실행 (데이터베이스 최적화)
        print("\n🔧 데이터베이스 최적화 중...")
        conn.execute("VACUUM")
        
        # 변경사항 커밋
        conn.commit()
        conn.close()
        
        # 삭제 후 결과
        print("\n📊 삭제 결과:")
        total_deleted = sum(deleted_counts.values())
        for table, count in deleted_counts.items():
            print(f"  - {table}: {count:,}건 삭제됨")
        
        print(f"\n✅ 총 {total_deleted:,}건의 로그 기록이 삭제되었습니다.")
        print(f"📦 백업 파일: {backup_path}")
        print("\n✨ 통합 관제실 로그 초기화 완료!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("통합 관제실 로그 기록 초기화 스크립트")
    print("=" * 60)
    print("\n⚠️  경고: 이 스크립트는 모든 로그 기록을 영구적으로 삭제합니다.")
    print("   사용자 정보(users 테이블)는 유지됩니다.\n")
    
    success = clear_all_logs()
    
    if success:
        print("\n✅ 작업이 성공적으로 완료되었습니다.")
    else:
        print("\n❌ 작업이 실패했습니다.")

