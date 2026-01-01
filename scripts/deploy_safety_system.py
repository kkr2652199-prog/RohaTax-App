#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
배포 서버 안전장치 시스템

- 배포 전 자동 백업
- 버전 관리
- 롤백 기능
- 복구 시스템
"""

import os
import subprocess
import shutil
import json
from datetime import datetime
from pathlib import Path

DEPLOYMENT_HISTORY_FILE = "deployment_history.json"
BACKUP_DIR = "database/backups"
DEPLOYMENT_BACKUP_DIR = "deployment_backups"

def ensure_directories():
    """필요한 디렉토리 생성"""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    os.makedirs(DEPLOYMENT_BACKUP_DIR, exist_ok=True)

def get_current_commit():
    """현재 Git 커밋 해시 가져오기"""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%H"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception as e:
        print(f"[ERROR] Git 커밋 해시 가져오기 실패: {e}")
    return None

def get_current_branch():
    """현재 브랜치 가져오기"""
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception as e:
        print(f"[ERROR] Git 브랜치 가져오기 실패: {e}")
    return None

def backup_database():
    """데이터베이스 백업"""
    db_path = "database/app.db"
    if not os.path.exists(db_path):
        print("[WARNING] 데이터베이스 파일이 없습니다")
        return None
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(BACKUP_DIR, f"app_backup_{timestamp}.db")
    
    try:
        shutil.copy2(db_path, backup_path)
        print(f"[OK] 데이터베이스 백업 완료: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"[ERROR] 데이터베이스 백업 실패: {e}")
        return None

def save_deployment_info(commit_hash, branch, backup_path):
    """배포 정보 저장"""
    ensure_directories()
    
    deployment_info = {
        "timestamp": datetime.now().isoformat(),
        "commit_hash": commit_hash,
        "branch": branch,
        "database_backup": backup_path,
        "status": "deployed"
    }
    
    # 기존 히스토리 로드
    history = []
    if os.path.exists(DEPLOYMENT_HISTORY_FILE):
        try:
            with open(DEPLOYMENT_HISTORY_FILE, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except:
            history = []
    
    # 새 배포 정보 추가
    history.append(deployment_info)
    
    # 최근 10개만 유지
    history = history[-10:]
    
    # 저장
    try:
        with open(DEPLOYMENT_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        print(f"[OK] 배포 정보 저장 완료: {DEPLOYMENT_HISTORY_FILE}")
        return True
    except Exception as e:
        print(f"[ERROR] 배포 정보 저장 실패: {e}")
        return False

def get_last_deployment():
    """마지막 배포 정보 가져오기"""
    if not os.path.exists(DEPLOYMENT_HISTORY_FILE):
        return None
    
    try:
        with open(DEPLOYMENT_HISTORY_FILE, 'r', encoding='utf-8') as f:
            history = json.load(f)
        if history:
            return history[-1]
    except Exception as e:
        print(f"[ERROR] 배포 히스토리 읽기 실패: {e}")
    return None

def rollback_to_commit(commit_hash):
    """특정 커밋으로 롤백"""
    print(f"\n=== 롤백 시작: {commit_hash[:8]} ===")
    
    # 현재 상태 백업
    current_commit = get_current_commit()
    if current_commit:
        backup_database()
    
    # Git 체크아웃
    try:
        result = subprocess.run(
            ["git", "checkout", commit_hash],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print(f"[OK] 코드 롤백 완료: {commit_hash[:8]}")
            return True
        else:
            print(f"[ERROR] 롤백 실패: {result.stderr}")
            return False
    except Exception as e:
        print(f"[ERROR] 롤백 중 오류: {e}")
        return False

def rollback_to_last_deployment():
    """마지막 배포로 롤백"""
    last_deploy = get_last_deployment()
    if not last_deploy:
        print("[ERROR] 배포 히스토리가 없습니다")
        return False
    
    commit_hash = last_deploy.get('commit_hash')
    if not commit_hash:
        print("[ERROR] 커밋 해시를 찾을 수 없습니다")
        return False
    
    print(f"[INFO] 마지막 배포 커밋: {commit_hash[:8]}")
    return rollback_to_commit(commit_hash)

def list_deployment_history():
    """배포 히스토리 목록"""
    if not os.path.exists(DEPLOYMENT_HISTORY_FILE):
        print("[INFO] 배포 히스토리가 없습니다")
        return
    
    try:
        with open(DEPLOYMENT_HISTORY_FILE, 'r', encoding='utf-8') as f:
            history = json.load(f)
        
        print("\n=== 배포 히스토리 ===")
        for i, deploy in enumerate(reversed(history), 1):
            timestamp = deploy.get('timestamp', 'Unknown')
            commit = deploy.get('commit_hash', 'Unknown')[:8]
            branch = deploy.get('branch', 'Unknown')
            status = deploy.get('status', 'Unknown')
            print(f"{i}. {timestamp} | {commit} | {branch} | {status}")
    except Exception as e:
        print(f"[ERROR] 히스토리 읽기 실패: {e}")

def main():
    """메인 함수"""
    import sys
    
    if len(sys.argv) < 2:
        print("사용법:")
        print("  python deploy_safety_system.py backup          # 배포 전 백업")
        print("  python deploy_safety_system.py rollback        # 마지막 배포로 롤백")
        print("  python deploy_safety_system.py rollback <hash> # 특정 커밋으로 롤백")
        print("  python deploy_safety_system.py history         # 배포 히스토리 확인")
        return
    
    command = sys.argv[1]
    
    if command == "backup":
        print("=== 배포 전 백업 ===")
        commit_hash = get_current_commit()
        branch = get_current_branch()
        backup_path = backup_database()
        
        if commit_hash and backup_path:
            save_deployment_info(commit_hash, branch, backup_path)
            print(f"\n[OK] 백업 완료")
            print(f"  커밋: {commit_hash[:8]}")
            print(f"  브랜치: {branch}")
            print(f"  DB 백업: {backup_path}")
    
    elif command == "rollback":
        if len(sys.argv) > 2:
            commit_hash = sys.argv[2]
            rollback_to_commit(commit_hash)
        else:
            rollback_to_last_deployment()
    
    elif command == "history":
        list_deployment_history()
    
    else:
        print(f"[ERROR] 알 수 없는 명령어: {command}")

if __name__ == '__main__':
    main()

