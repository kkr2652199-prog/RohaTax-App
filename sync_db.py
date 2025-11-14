"""
워크트리 간 데이터베이스 동기화 스크립트
homepage1의 데이터베이스를 메인 워크트리로 안전하게 복사합니다.
"""
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path


def backup_database(db_path: str) -> str:
    """
    데이터베이스 파일을 안전하게 백업합니다.
    
    Args:
        db_path: 백업할 데이터베이스 파일 경로
        
    Returns:
        백업 파일 경로
    """
    if not os.path.exists(db_path):
        return None
    
    # 백업 디렉토리 생성
    backup_dir = os.path.join(os.path.dirname(db_path), 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    
    # 백업 파일명 생성 (타임스탬프 포함)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"app_backup_before_sync_{timestamp}.db"
    backup_path = os.path.join(backup_dir, backup_filename)
    
    # 데이터베이스 파일 복사
    shutil.copy2(db_path, backup_path)
    
    return backup_path


def sync_database(source_db: str, dest_db: str) -> bool:
    """
    소스 데이터베이스를 대상 데이터베이스로 동기화합니다.
    
    Args:
        source_db: 소스 데이터베이스 파일 경로 (homepage1)
        dest_db: 대상 데이터베이스 파일 경로 (master)
        
    Returns:
        성공 여부
    """
    try:
        # 소스 데이터베이스 존재 확인
        if not os.path.exists(source_db):
            print(f"[ERROR] 오류: 소스 데이터베이스를 찾을 수 없습니다: {source_db}")
            return False
        
        # 대상 디렉토리 생성
        dest_dir = os.path.dirname(dest_db)
        os.makedirs(dest_dir, exist_ok=True)
        
        # 대상 데이터베이스 백업 (존재하는 경우)
        if os.path.exists(dest_db):
            backup_path = backup_database(dest_db)
            if backup_path:
                print(f"[OK] 기존 데이터베이스 백업 완료: {backup_path}")
            else:
                print("[WARNING] 백업 실패했지만 계속 진행합니다...")
        
        # 데이터베이스 파일 복사
        shutil.copy2(source_db, dest_db)
        
        # WAL 파일 복사 (존재하는 경우)
        source_wal = source_db + '-wal'
        dest_wal = dest_db + '-wal'
        if os.path.exists(source_wal):
            shutil.copy2(source_wal, dest_wal)
            print(f"[OK] WAL 파일 복사 완료")
        
        # SHM 파일 복사 (존재하는 경우)
        source_shm = source_db + '-shm'
        dest_shm = dest_db + '-shm'
        if os.path.exists(source_shm):
            shutil.copy2(source_shm, dest_shm)
            print(f"[OK] SHM 파일 복사 완료")
        
        # 파일 크기 확인
        source_size = os.path.getsize(source_db)
        dest_size = os.path.getsize(dest_db)
        
        if source_size == dest_size:
            print(f"[OK] 데이터베이스 동기화 완료 (크기: {source_size / 1024:.2f} KB)")
            return True
        else:
            print(f"[WARNING] 경고: 파일 크기가 다릅니다 (소스: {source_size}, 대상: {dest_size})")
            return False
            
    except Exception as e:
        print(f"[ERROR] 오류 발생: {str(e)}")
        return False


def main():
    """메인 함수"""
    # 프로젝트 루트 디렉토리 (스크립트가 위치한 디렉토리)
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # 기본 경로 설정
    homepage1_db = os.path.join(project_root, 'homepage1', 'database', 'app.db')
    master_db = os.path.join(project_root, 'database', 'app.db')
    
    # 명령줄 인자로 경로 지정 가능
    if len(sys.argv) >= 3:
        homepage1_db = sys.argv[1]
        master_db = sys.argv[2]
    elif len(sys.argv) == 2:
        print("사용법: python sync_db.py [homepage1_db_path] [master_db_path]")
        print("또는: python sync_db.py (기본 경로 사용)")
        sys.exit(1)
    
    print("=" * 60)
    print("워크트리 간 데이터베이스 동기화")
    print("=" * 60)
    print(f"\n소스 (homepage1): {homepage1_db}")
    print(f"대상 (master):    {master_db}\n")
    
    # 동기화 실행
    success = sync_database(homepage1_db, master_db)
    
    if success:
        print("\n" + "=" * 60)
        print("[SUCCESS] 데이터베이스 동기화 성공!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("[FAILED] 데이터베이스 동기화 실패!")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()

