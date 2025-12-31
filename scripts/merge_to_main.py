#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
homepage1 전초기지 → 본진(main) 병합 스크립트

워크트리 구분 파일 제외:
- config/settings.py (PORT 기본값: homepage1=5001, 본진=5000)
- start_server_5001.bat (homepage1 전용)
- start_server_5000.bat (본진용, 있다면)
- .env (환경 변수 파일)
- database/app.db (데이터베이스는 별도 동기화)
"""

import os
import shutil
import hashlib
from pathlib import Path

# 경로 설정
HOMEPAGE1_DIR = Path(__file__).parent.parent
MAIN_DIR = HOMEPAGE1_DIR.parent

# 제외할 파일/디렉토리 패턴
EXCLUDE_PATTERNS = [
    '.git',
    '__pycache__',
    '*.pyc',
    '.env',
    'database/app.db',
    'database/backups',
    'kweon.md',  # 각 워크트리별로 관리
]

# 워크트리 구분 파일 (병합 후 수동 조정 필요)
WORKTREE_SPECIFIC_FILES = [
    'config/settings.py',  # PORT 기본값
    'start_server_5001.bat',  # homepage1 전용
    'start_server_5000.bat',  # 본진용
]


def get_file_hash(file_path):
    """파일의 MD5 해시 반환"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def should_exclude(file_path, relative_path):
    """파일이 제외 대상인지 확인"""
    # 절대 경로를 상대 경로로 변환
    rel_str = str(relative_path).replace('\\', '/')
    
    # 제외 패턴 확인
    for pattern in EXCLUDE_PATTERNS:
        if pattern in rel_str or rel_str.endswith(pattern):
            return True
    
    # 워크트리 구분 파일은 제외하지 않음 (병합 후 수동 조정)
    return False


def merge_files():
    """homepage1의 파일을 본진으로 병합"""
    copied_files = []
    skipped_files = []
    error_files = []
    
    print("=" * 60)
    print("homepage1 → 본진 병합 시작")
    print("=" * 60)
    print(f"전초기지: {HOMEPAGE1_DIR}")
    print(f"본진: {MAIN_DIR}")
    print()
    
    # homepage1의 모든 파일 스캔
    for root, dirs, files in os.walk(HOMEPAGE1_DIR):
        # .git 디렉토리 제외
        if '.git' in root:
            continue
        
        for file in files:
            source_path = Path(root) / file
            relative_path = source_path.relative_to(HOMEPAGE1_DIR)
            
            # 제외 대상 확인
            if should_exclude(source_path, relative_path):
                skipped_files.append(relative_path)
                continue
            
            # 대상 경로 생성
            target_path = MAIN_DIR / relative_path
            
            try:
                # 디렉토리 생성
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                # 파일 복사
                shutil.copy2(source_path, target_path)
                copied_files.append(relative_path)
                print(f"[OK] {relative_path}")
            except Exception as e:
                error_files.append((relative_path, str(e)))
                print(f"[ERROR] {relative_path}: {e}")
    
    # 워크트리 구분 파일 처리 안내
    print()
    print("=" * 60)
    print("병합 완료")
    print("=" * 60)
    print(f"복사된 파일: {len(copied_files)}개")
    print(f"건너뛴 파일: {len(skipped_files)}개")
    print(f"오류 파일: {len(error_files)}개")
    
    if error_files:
        print("\n오류 발생 파일:")
        for file, error in error_files:
            print(f"  - {file}: {error}")
    
    # 워크트리 구분 파일 안내
    print()
    print("=" * 60)
    print("워크트리 구분 파일 수동 조정 필요")
    print("=" * 60)
    print("다음 파일들은 워크트리별로 다르게 설정되어야 합니다:")
    for file in WORKTREE_SPECIFIC_FILES:
        print(f"  - {file}")
    print()
    print("본진(main) 설정:")
    print("  - config/settings.py: PORT 기본값을 5000으로 변경")
    print("  - start_server_5001.bat: 삭제 또는 무시")
    print("  - start_server_5000.bat: 본진용으로 유지")
    
    return len(copied_files), len(skipped_files), len(error_files)


if __name__ == '__main__':
    try:
        copied, skipped, errors = merge_files()
        print()
        print("=" * 60)
        if errors == 0:
            print("[SUCCESS] 병합 완료!")
        else:
            print(f"[WARNING] 병합 완료 (오류 {errors}개)")
        print("=" * 60)
    except Exception as e:
        print(f"\n[ERROR] 병합 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

