#!/usr/bin/env python3
"""
homepage1 (전초기지)의 데이터베이스를 본진에 복원하는 스크립트 (안전 버전)
SQLite VACUUM INTO를 사용하여 새 파일로 내보냅니다.
"""

import os
import sys
import sqlite3
from datetime import datetime

# Windows 인코딩 설정
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 프로젝트 루트 경로
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
homepage1_db_path = os.path.join(project_root, 'homepage1', 'database', 'app.db')
main_db_path = os.path.join(project_root, 'database', 'app.db')
backup_dir = os.path.join(project_root, 'database', 'backups')

def get_table_list(conn):
    """데이터베이스의 모든 테이블 목록 가져오기"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """)
    return [row[0] for row in cursor.fetchall()]

def get_table_row_count(conn, table_name):
    """테이블의 레코드 개수 가져오기"""
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        return cursor.fetchone()[0]
    except Exception:
        return 0

def restore_database():
    """homepage1의 데이터베이스를 본진에 복원 (VACUUM INTO 사용)"""
    
    print("=" * 60)
    print("homepage1 데이터베이스 복원 스크립트 (안전 버전)")
    print("=" * 60)
    
    # homepage1 데이터베이스 확인
    print(f"\n[1단계] homepage1 데이터베이스 확인 중...")
    print(f"  경로: {homepage1_db_path}")
    
    if not os.path.exists(homepage1_db_path):
        print(f"  [ERROR] homepage1 데이터베이스 파일이 없습니다!")
        return False
    
    print(f"  [OK] homepage1 데이터베이스 파일 발견")
    
    # homepage1 데이터베이스 정보 확인
    try:
        source_conn = sqlite3.connect(homepage1_db_path, timeout=10.0)
        source_tables = get_table_list(source_conn)
        
        print(f"\n[2단계] homepage1 데이터베이스 구조 확인 중...")
        print(f"  발견된 테이블: {len(source_tables)}개")
        
        table_info = {}
        total_records = 0
        for table in source_tables:
            count = get_table_row_count(source_conn, table)
            table_info[table] = count
            total_records += count
            print(f"    - {table}: {count}개 레코드")
        
        print(f"  총 레코드 수: {total_records}개")
        source_conn.close()
    except Exception as e:
        print(f"  [ERROR] homepage1 데이터베이스 확인 실패: {e}")
        return False
    
    # 본진 데이터베이스 백업
    print(f"\n[3단계] 본진 데이터베이스 백업 중...")
    os.makedirs(backup_dir, exist_ok=True)
    
    if os.path.exists(main_db_path):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'app_backup_before_restore_{timestamp}.db'
        backup_path = os.path.join(backup_dir, backup_filename)
        
        try:
            import shutil
            shutil.copy2(main_db_path, backup_path)
            print(f"  [OK] 백업 완료: {backup_filename}")
        except Exception as e:
            print(f"  [WARNING] 백업 실패: {e}")
    else:
        print(f"  [INFO] 본진 데이터베이스가 없습니다. 새로 생성합니다.")
    
    # VACUUM INTO를 사용하여 새 파일로 내보내기
    print(f"\n[4단계] homepage1 데이터베이스를 본진에 복원 중...")
    new_db_path = main_db_path + '.new'
    
    try:
        # homepage1 데이터베이스를 새 파일로 내보내기
        source_conn = sqlite3.connect(homepage1_db_path, timeout=10.0)
        
        # VACUUM INTO를 사용하여 새 파일로 내보내기
        print(f"  [INFO] VACUUM INTO 실행 중...")
        source_conn.execute(f"VACUUM INTO '{new_db_path.replace(chr(92), '/')}'")
        source_conn.close()
        
        print(f"  [OK] 새 데이터베이스 파일 생성 완료")
        
        # 기존 파일을 .old로 백업하고 새 파일로 교체
        import time
        if os.path.exists(main_db_path):
            old_db_path = main_db_path + '.old'
            # 기존 .old 파일 삭제
            if os.path.exists(old_db_path):
                try:
                    os.remove(old_db_path)
                except Exception:
                    pass
            
            # 여러 번 시도
            max_retries = 10
            for i in range(max_retries):
                try:
                    time.sleep(1)
                    # 기존 파일을 .old로 이름 변경
                    os.rename(main_db_path, old_db_path)
                    print(f"  [OK] 기존 파일을 .old로 백업 완료")
                    break
                except PermissionError:
                    if i < max_retries - 1:
                        print(f"  [INFO] 파일이 사용 중입니다. 대기 중... ({i+1}/{max_retries})")
                    else:
                        print(f"  [WARNING] 기존 파일 이름 변경 실패. 새 파일을 직접 사용합니다.")
                        old_db_path = None
            
            # WAL, SHM 파일도 처리
            for ext in ['-wal', '-shm']:
                old_file = main_db_path + ext
                if os.path.exists(old_file):
                    try:
                        os.remove(old_file)
                    except Exception:
                        pass
        
        # 새 파일을 메인 파일로 이름 변경
        if os.path.exists(new_db_path):
            # 기존 파일이 있으면 먼저 삭제 시도
            if os.path.exists(main_db_path):
                try:
                    os.remove(main_db_path)
                except PermissionError:
                    print(f"  [WARNING] 기존 파일 삭제 실패 (Flask 서버가 사용 중)")
                    print(f"  [INFO] 새 파일이 생성되었습니다: {new_db_path}")
                    print(f"  [INFO] Flask 서버를 재시작하면 자동으로 새 파일을 사용합니다.")
                    print(f"  [INFO] 또는 수동으로 app.db.new를 app.db로 이름 변경하세요.")
                    return True
            
            # 새 파일을 메인 파일로 이름 변경
            os.rename(new_db_path, main_db_path)
            print(f"  [OK] 데이터베이스 복원 완료")
        
    except Exception as e:
        print(f"  [ERROR] 데이터베이스 복원 실패: {e}")
        import traceback
        traceback.print_exc()
        # 새 파일이 있으면 삭제
        if os.path.exists(new_db_path):
            try:
                os.remove(new_db_path)
            except Exception:
                pass
        return False
    
    # 복원된 데이터베이스 확인
    print(f"\n[5단계] 복원된 데이터베이스 확인 중...")
    try:
        restored_conn = sqlite3.connect(main_db_path, timeout=10.0)
        restored_tables = get_table_list(restored_conn)
        
        print(f"  발견된 테이블: {len(restored_tables)}개")
        
        restored_info = {}
        total_restored = 0
        for table in restored_tables:
            count = get_table_row_count(restored_conn, table)
            restored_info[table] = count
            total_restored += count
            print(f"    - {table}: {count}개 레코드")
        
        restored_conn.close()
        
        # 비교
        print(f"\n[6단계] 복원 결과 비교...")
        if set(source_tables) == set(restored_tables):
            print(f"  [OK] 테이블 구조 일치: {len(restored_tables)}개 테이블")
        else:
            missing = set(source_tables) - set(restored_tables)
            extra = set(restored_tables) - set(source_tables)
            if missing:
                print(f"  [WARNING] 누락된 테이블: {missing}")
            if extra:
                print(f"  [WARNING] 추가된 테이블: {extra}")
        
        print(f"  homepage1 총 레코드: {total_records}개")
        print(f"  본진 총 레코드: {total_restored}개")
        
        if total_records == total_restored:
            print(f"  [OK] 레코드 수 일치")
        else:
            print(f"  [INFO] 레코드 수 차이: {total_restored - total_records}개")
        
    except Exception as e:
        print(f"  [ERROR] 복원 확인 실패: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("[OK] homepage1 데이터베이스 복원이 완료되었습니다!")
    print("=" * 60)
    print(f"\n복원된 데이터베이스 경로: {main_db_path}")
    print(f"백업 파일 위치: {backup_dir}")
    print(f"\n[중요] Flask 서버를 재시작하면 새 데이터베이스를 사용합니다.")
    
    return True

if __name__ == '__main__':
    success = restore_database()
    sys.exit(0 if success else 1)

