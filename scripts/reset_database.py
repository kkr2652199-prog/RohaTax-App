#!/usr/bin/env python3
"""
데이터베이스 초기화 스크립트
기존 데이터베이스를 백업한 후 새로 초기화합니다.
"""

import os
import sys
import shutil
from datetime import datetime

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from core.db import init_db, DB_PATH

def reset_database():
    """데이터베이스 초기화 (백업 후 재생성)"""
    
    print("=" * 60)
    print("데이터베이스 초기화 스크립트")
    print("=" * 60)
    
    # 데이터베이스 파일 경로
    db_path = DB_PATH
    backup_dir = os.path.join(os.path.dirname(db_path), 'backups')
    
    # 백업 디렉토리 생성
    os.makedirs(backup_dir, exist_ok=True)
    
    # 기존 데이터베이스가 있는 경우 백업
    if os.path.exists(db_path):
        # 백업 파일명 생성 (타임스탬프 포함)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'app_backup_{timestamp}.db'
        backup_path = os.path.join(backup_dir, backup_filename)
        
        print(f"\n[1단계] 기존 데이터베이스 백업 중...")
        print(f"  원본: {db_path}")
        print(f"  백업: {backup_path}")
        
        try:
            shutil.copy2(db_path, backup_path)
            print(f"  [OK] 백업 완료: {backup_filename}")
        except Exception as e:
            print(f"  [ERROR] 백업 실패: {e}")
            response = input("  백업 실패했지만 계속 진행하시겠습니까? (y/N): ")
            if response.lower() != 'y':
                print("  초기화를 취소했습니다.")
                return False
        
        # WAL, SHM 파일도 백업 (있는 경우)
        wal_path = db_path + '-wal'
        shm_path = db_path + '-shm'
        
        if os.path.exists(wal_path):
            shutil.copy2(wal_path, backup_path + '-wal')
            print(f"  [OK] WAL 파일 백업 완료")
        
        if os.path.exists(shm_path):
            shutil.copy2(shm_path, backup_path + '-shm')
            print(f"  [OK] SHM 파일 백업 완료")
    else:
        print(f"\n[1단계] 기존 데이터베이스가 없습니다. 새로 생성합니다.")
    
    # 기존 데이터베이스 파일 삭제
    print(f"\n[2단계] 기존 데이터베이스 파일 삭제 중...")
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"  [OK] 데이터베이스 파일 삭제 완료")
        
        # WAL, SHM 파일도 삭제
        wal_path = db_path + '-wal'
        shm_path = db_path + '-shm'
        if os.path.exists(wal_path):
            os.remove(wal_path)
        if os.path.exists(shm_path):
            os.remove(shm_path)
    except Exception as e:
        print(f"  [ERROR] 파일 삭제 실패: {e}")
        return False
    
    # 새 데이터베이스 초기화
    print(f"\n[3단계] 새 데이터베이스 초기화 중...")
    try:
        init_db()
        print(f"  [OK] 데이터베이스 초기화 완료")
        print(f"  새 데이터베이스 경로: {db_path}")
    except Exception as e:
        print(f"  [ERROR] 데이터베이스 초기화 실패: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("[OK] 데이터베이스 초기화가 완료되었습니다!")
    print("=" * 60)
    
    return True

if __name__ == '__main__':
    # Windows 인코딩 설정
    import io
    import sys
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
    # 명령줄 인자 확인 (--yes 또는 --auto로 자동 실행)
    auto_mode = '--yes' in sys.argv or '--auto' in sys.argv
    
    if not auto_mode:
        # 확인 메시지
        print("\n[경고] 이 작업은 기존 데이터베이스의 모든 데이터를 삭제합니다!")
        print("   백업은 자동으로 생성되지만, 중요한 데이터는 별도로 백업하세요.\n")
        
        try:
            response = input("정말 데이터베이스를 초기화하시겠습니까? (yes 입력): ")
            if response.lower() != 'yes':
                print("\n초기화를 취소했습니다.")
                sys.exit(0)
        except (EOFError, KeyboardInterrupt):
            print("\n초기화를 취소했습니다.")
            sys.exit(0)
    
    # 데이터베이스 초기화 실행
    success = reset_database()
    sys.exit(0 if success else 1)

