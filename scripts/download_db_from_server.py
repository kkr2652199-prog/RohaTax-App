#!/usr/bin/env python3
"""
배포 서버(하늘저장소)에서 데이터베이스를 다운로드하여 본진에 복원하는 스크립트
"""

import os
import sys
import subprocess
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
SERVER_HOST = 'ubuntu@52.78.116.159'
SERVER_DB_PATH = '/home/ubuntu/RohaTax-App/database/app.db'
LOCAL_DB_PATH = os.path.join(project_root, 'database', 'app.db')
TEMP_DB_PATH = os.path.join(project_root, 'database', 'app.db.from_server')
backup_dir = os.path.join(project_root, 'database', 'backups')

def get_table_row_count(conn, table_name):
    """테이블의 레코드 개수 가져오기"""
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        return cursor.fetchone()[0]
    except Exception:
        return 0

def download_database_from_server():
    """배포 서버에서 데이터베이스 다운로드 및 복원"""
    
    print("=" * 60)
    print("배포 서버에서 데이터베이스 다운로드 및 복원")
    print("=" * 60)
    
    # 백업 디렉토리 생성
    os.makedirs(backup_dir, exist_ok=True)
    
    # 1. 본진 데이터베이스 백업
    print(f"\n[1단계] 본진 데이터베이스 백업 중...")
    if os.path.exists(LOCAL_DB_PATH):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'app_backup_before_server_restore_{timestamp}.db'
        backup_path = os.path.join(backup_dir, backup_filename)
        
        try:
            shutil.copy2(LOCAL_DB_PATH, backup_path)
            print(f"  [OK] 백업 완료: {backup_filename}")
        except Exception as e:
            print(f"  [WARNING] 백업 실패: {e}")
    else:
        print(f"  [INFO] 본진 데이터베이스가 없습니다.")
    
    # 2. 배포 서버에서 데이터베이스 다운로드
    print(f"\n[2단계] 배포 서버에서 데이터베이스 다운로드 중...")
    print(f"  서버: {SERVER_HOST}")
    print(f"  경로: {SERVER_DB_PATH}")
    print(f"  다운로드 위치: {TEMP_DB_PATH}")
    
    try:
        # SCP 명령어 실행
        scp_command = ['scp', f'{SERVER_HOST}:{SERVER_DB_PATH}', TEMP_DB_PATH]
        result = subprocess.run(scp_command, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"  [OK] 다운로드 완료")
        else:
            print(f"  [ERROR] 다운로드 실패")
            print(f"  오류 메시지: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print(f"  [ERROR] SCP 명령어를 찾을 수 없습니다.")
        print(f"  [INFO] Windows에서 SCP를 사용하려면 OpenSSH 클라이언트가 필요합니다.")
        print(f"  [INFO] 또는 수동으로 다운로드하세요:")
        print(f"    scp {SERVER_HOST}:{SERVER_DB_PATH} {TEMP_DB_PATH}")
        return False
    except Exception as e:
        print(f"  [ERROR] 다운로드 중 오류 발생: {e}")
        return False
    
    # 3. 다운로드한 데이터베이스 확인
    print(f"\n[3단계] 다운로드한 데이터베이스 확인 중...")
    if not os.path.exists(TEMP_DB_PATH):
        print(f"  [ERROR] 다운로드한 파일이 없습니다.")
        return False
    
    try:
        server_conn = sqlite3.connect(TEMP_DB_PATH, timeout=10.0)
        cursor = server_conn.cursor()
        
        # 테이블 목록 확인
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"  발견된 테이블: {len(tables)}개")
        
        # 주요 테이블 데이터 확인
        important_tables = ['users', 'products', 'product_packages', 'subscription_plans', 'orders', 'payment_history']
        print(f"\n  주요 테이블 데이터:")
        for table in important_tables:
            if table in tables:
                count = get_table_row_count(server_conn, table)
                print(f"    - {table}: {count}개 레코드")
        
        server_conn.close()
        
    except Exception as e:
        print(f"  [ERROR] 데이터베이스 확인 실패: {e}")
        return False
    
    # 4. 본진 데이터베이스에 복원
    print(f"\n[4단계] 본진 데이터베이스에 복원 중...")
    
    # 기존 파일 삭제 시도
    import time
    if os.path.exists(LOCAL_DB_PATH):
        max_retries = 5
        for i in range(max_retries):
            try:
                time.sleep(0.5)
                # WAL 체크포인트 실행
                try:
                    temp_conn = sqlite3.connect(LOCAL_DB_PATH, timeout=1.0)
                    temp_conn.execute('PRAGMA wal_checkpoint(FULL)')
                    temp_conn.close()
                except Exception:
                    pass
                
                os.remove(LOCAL_DB_PATH)
                print(f"  [OK] 기존 데이터베이스 파일 삭제 완료")
                break
            except PermissionError:
                if i < max_retries - 1:
                    print(f"  [INFO] 파일이 사용 중입니다. 대기 중... ({i+1}/{max_retries})")
                else:
                    print(f"  [WARNING] 기존 파일 삭제 실패 (Flask 서버가 사용 중일 수 있음)")
                    print(f"  [INFO] Flask 서버를 재시작한 후 수동으로 교체하세요:")
                    print(f"    - {TEMP_DB_PATH} → {LOCAL_DB_PATH}")
                    return True
        
        # WAL, SHM 파일도 삭제
        wal_path = LOCAL_DB_PATH + '-wal'
        shm_path = LOCAL_DB_PATH + '-shm'
        if os.path.exists(wal_path):
            try:
                os.remove(wal_path)
            except Exception:
                pass
        if os.path.exists(shm_path):
            try:
                os.remove(shm_path)
            except Exception:
                pass
    
    # 다운로드한 파일을 본진 파일로 복사
    try:
        shutil.copy2(TEMP_DB_PATH, LOCAL_DB_PATH)
        print(f"  [OK] 데이터베이스 복원 완료")
        
        # 임시 파일 삭제
        if os.path.exists(TEMP_DB_PATH):
            os.remove(TEMP_DB_PATH)
        
    except Exception as e:
        print(f"  [ERROR] 복원 실패: {e}")
        return False
    
    # 5. 복원된 데이터베이스 확인
    print(f"\n[5단계] 복원된 데이터베이스 최종 확인 중...")
    try:
        restored_conn = sqlite3.connect(LOCAL_DB_PATH, timeout=10.0)
        
        print(f"  주요 테이블 데이터:")
        for table in important_tables:
            try:
                count = get_table_row_count(restored_conn, table)
                print(f"    - {table}: {count}개 레코드")
            except Exception:
                print(f"    - {table}: 테이블 없음")
        
        restored_conn.close()
        
    except Exception as e:
        print(f"  [ERROR] 확인 실패: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("[OK] 배포 서버 데이터베이스 복원이 완료되었습니다!")
    print("=" * 60)
    print(f"\n복원된 데이터베이스 경로: {LOCAL_DB_PATH}")
    print(f"백업 파일 위치: {backup_dir}")
    print(f"\n[중요] Flask 서버를 재시작하면 새 데이터베이스를 사용합니다.")
    
    return True

if __name__ == '__main__':
    success = download_database_from_server()
    sys.exit(0 if success else 1)


