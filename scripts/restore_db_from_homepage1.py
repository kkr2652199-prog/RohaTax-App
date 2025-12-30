#!/usr/bin/env python3
"""
homepage1 (전초기지)의 데이터베이스를 본진에 복원하는 스크립트
"""

import os
import sys
import shutil
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
    """homepage1의 데이터베이스를 본진에 복원"""
    
    print("=" * 60)
    print("homepage1 데이터베이스 복원 스크립트")
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
        for table in source_tables:
            count = get_table_row_count(source_conn, table)
            table_info[table] = count
            print(f"    - {table}: {count}개 레코드")
        
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
            shutil.copy2(main_db_path, backup_path)
            print(f"  [OK] 백업 완료: {backup_filename}")
            
            # WAL, SHM 파일도 백업
            wal_path = main_db_path + '-wal'
            shm_path = main_db_path + '-shm'
            
            if os.path.exists(wal_path):
                shutil.copy2(wal_path, backup_path + '-wal')
            if os.path.exists(shm_path):
                shutil.copy2(shm_path, backup_path + '-shm')
        except Exception as e:
            print(f"  [WARNING] 백업 실패: {e}")
    else:
        print(f"  [INFO] 본진 데이터베이스가 없습니다. 새로 생성합니다.")
    
    # homepage1 데이터베이스를 본진에 복사 (SQLite ATTACH 사용)
    print(f"\n[4단계] homepage1 데이터베이스를 본진에 복사 중...")
    try:
        # 임시 파일명으로 복사 (원자적 작업)
        temp_db_path = main_db_path + '.tmp'
        
        # homepage1 데이터베이스를 임시 파일로 복사
        shutil.copy2(homepage1_db_path, temp_db_path)
        print(f"  [OK] 임시 파일로 복사 완료")
        
        # WAL, SHM 파일도 복사 (있는 경우)
        source_wal = homepage1_db_path + '-wal'
        source_shm = homepage1_db_path + '-shm'
        temp_wal = temp_db_path + '-wal'
        temp_shm = temp_db_path + '-shm'
        
        if os.path.exists(source_wal):
            shutil.copy2(source_wal, temp_wal)
        if os.path.exists(source_shm):
            shutil.copy2(source_shm, temp_shm)
        
        # 기존 파일 삭제 시도 (있는 경우)
        import time
        if os.path.exists(main_db_path):
            # WAL 체크포인트 실행
            try:
                temp_conn = sqlite3.connect(main_db_path, timeout=1.0)
                temp_conn.execute('PRAGMA wal_checkpoint(FULL)')
                temp_conn.close()
            except Exception:
                pass
            
            # 여러 번 시도
            max_retries = 5
            for i in range(max_retries):
                try:
                    time.sleep(0.5)
                    # 기존 파일 삭제
                    if os.path.exists(main_db_path):
                        os.remove(main_db_path)
                    wal_path = main_db_path + '-wal'
                    shm_path = main_db_path + '-shm'
                    if os.path.exists(wal_path):
                        os.remove(wal_path)
                    if os.path.exists(shm_path):
                        os.remove(shm_path)
                    print(f"  [OK] 기존 데이터베이스 파일 삭제 완료")
                    break
                except PermissionError:
                    if i < max_retries - 1:
                        print(f"  [INFO] 파일이 사용 중입니다. 대기 중... ({i+1}/{max_retries})")
                    else:
                        # 강제로 임시 파일을 메인 파일로 교체 시도
                        print(f"  [WARNING] 파일 삭제 실패. 임시 파일로 교체 시도...")
                        try:
                            if os.path.exists(main_db_path):
                                os.rename(main_db_path, main_db_path + '.old')
                            os.rename(temp_db_path, main_db_path)
                            if os.path.exists(temp_wal):
                                os.rename(temp_wal, main_db_path + '-wal')
                            if os.path.exists(temp_shm):
                                os.rename(temp_shm, main_db_path + '-shm')
                            print(f"  [OK] 파일 교체 완료 (기존 파일은 .old 확장자로 백업됨)")
                        except Exception as e2:
                            print(f"  [ERROR] 파일 교체 실패: {e2}")
                            return False
        
        # 임시 파일을 메인 파일로 이름 변경
        if os.path.exists(temp_db_path):
            if not os.path.exists(main_db_path):
                os.rename(temp_db_path, main_db_path)
                if os.path.exists(temp_wal):
                    os.rename(temp_wal, main_db_path + '-wal')
                if os.path.exists(temp_shm):
                    os.rename(temp_shm, main_db_path + '-shm')
                print(f"  [OK] 데이터베이스 복사 완료")
            else:
                # 이미 메인 파일이 있으면 임시 파일 삭제
                os.remove(temp_db_path)
                if os.path.exists(temp_wal):
                    os.remove(temp_wal)
                if os.path.exists(temp_shm):
                    os.remove(temp_shm)
        
    except Exception as e:
        print(f"  [ERROR] 데이터베이스 복사 실패: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 복원된 데이터베이스 확인
    print(f"\n[5단계] 복원된 데이터베이스 확인 중...")
    try:
        restored_conn = sqlite3.connect(main_db_path, timeout=10.0)
        restored_tables = get_table_list(restored_conn)
        
        print(f"  발견된 테이블: {len(restored_tables)}개")
        
        restored_info = {}
        for table in restored_tables:
            count = get_table_row_count(restored_conn, table)
            restored_info[table] = count
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
        
        # 레코드 수 비교
        total_source = sum(table_info.values())
        total_restored = sum(restored_info.values())
        print(f"  homepage1 총 레코드: {total_source}개")
        print(f"  본진 총 레코드: {total_restored}개")
        
        if total_source == total_restored:
            print(f"  [OK] 레코드 수 일치")
        else:
            print(f"  [INFO] 레코드 수 차이: {total_restored - total_source}개")
        
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
    
    return True

if __name__ == '__main__':
    success = restore_database()
    sys.exit(0 if success else 1)

