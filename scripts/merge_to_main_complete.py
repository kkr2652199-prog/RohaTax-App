#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
homepage1 전초기지 → 본진(main) 완전 병합 스크립트
- homepage1에서 삭제된 파일도 본진에서 삭제
- 환경 변수 파일은 제외
- homepage1과 100% 일치하게 병합
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime

# Windows 콘솔 인코딩 설정
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent.parent
HOMEPAGE1_DIR = PROJECT_ROOT / "homepage1"
MAIN_DIR = PROJECT_ROOT

# 제외할 파일/디렉토리 패턴 (환경 변수 및 워크트리별 파일)
EXCLUDE_PATTERNS = [
    '.git',
    '__pycache__',
    '*.pyc',
    '.env',
    'env.example',  # env.example은 병합 (환경 변수 예제는 동일)
    'database/app.db',
    'database/backups',
    'kweon.md',  # 각 워크트리별로 관리
    'node_modules',
    '*.log',
    '.DS_Store',
    'Thumbs.db',
]

# 워크트리 구분 파일 (병합하지 않음)
WORKTREE_SPECIFIC_FILES = [
    'config/settings.py',  # PORT 기본값: homepage1=5001, 본진=5000
    'start_server_5001.bat',  # homepage1 전용
    'start_server_5000.bat',  # 본진용
]

def should_exclude(file_path: Path, relative_path: str) -> bool:
    """파일이 제외 대상인지 확인"""
    rel_str = relative_path.replace('\\', '/')
    
    # 제외 패턴 확인
    for pattern in EXCLUDE_PATTERNS:
        if pattern in rel_str or rel_str.endswith(pattern):
            return True
    
    # 워크트리 구분 파일 확인
    for worktree_file in WORKTREE_SPECIFIC_FILES:
        if rel_str == worktree_file or rel_str.endswith('/' + worktree_file):
            return True
    
    return False

def get_deleted_files():
    """homepage1에서 삭제된 파일 목록 가져오기"""
    deleted_files = []
    
    # git 명령어로 삭제된 파일 확인 (최근 2개 커밋)
    import subprocess
    try:
        result = subprocess.run(
            ['git', 'diff', 'HEAD~2..HEAD', '--name-status', '--diff-filter=D'],
            cwd=HOMEPAGE1_DIR,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        for line in result.stdout.split('\n'):
            if line.strip().startswith('D\t'):
                file_path = line.strip()[2:].strip()
                if file_path and not should_exclude(Path(file_path), file_path):
                    deleted_files.append(file_path)
    except Exception as e:
        print(f"⚠️ 삭제된 파일 목록 가져오기 실패: {e}")
    
    return deleted_files

def delete_files_in_main(deleted_files):
    """본진에서 삭제된 파일 삭제"""
    deleted_count = 0
    error_count = 0
    
    print("\n" + "=" * 60)
    print("본진에서 삭제된 파일 처리")
    print("=" * 60)
    
    for rel_path in deleted_files:
        target_path = MAIN_DIR / rel_path
        
        if target_path.exists():
            try:
                if target_path.is_file():
                    target_path.unlink()
                    print(f"[삭제] {rel_path}")
                    deleted_count += 1
                elif target_path.is_dir():
                    shutil.rmtree(target_path)
                    print(f"[삭제] {rel_path}/ (디렉토리)")
                    deleted_count += 1
            except Exception as e:
                print(f"[오류] {rel_path}: {e}")
                error_count += 1
        else:
            print(f"[건너뜀] {rel_path} (이미 없음)")
    
    print(f"\n삭제 완료: {deleted_count}개, 오류: {error_count}개")
    return deleted_count, error_count

def merge_files():
    """homepage1의 파일을 본진으로 병합"""
    copied_files = []
    skipped_files = []
    error_files = []
    
    print("\n" + "=" * 60)
    print("homepage1 → 본진 병합 시작")
    print("=" * 60)
    print(f"전초기지: {HOMEPAGE1_DIR}")
    print(f"본진: {MAIN_DIR}")
    print()
    
    # homepage1의 모든 파일 스캔
    for root, dirs, files in os.walk(HOMEPAGE1_DIR):
        # .git 디렉토리 제외
        if '.git' in root:
            dirs[:] = []
            continue
        
        # 제외 디렉토리 필터링
        dirs[:] = [d for d in dirs if d not in ['__pycache__', 'node_modules', '.git']]
        
        for file in files:
            source_path = Path(root) / file
            relative_path = source_path.relative_to(HOMEPAGE1_DIR)
            rel_str = str(relative_path).replace('\\', '/')
            
            # 제외 대상 확인
            if should_exclude(source_path, rel_str):
                skipped_files.append(rel_str)
                continue
            
            # 대상 경로 생성
            target_path = MAIN_DIR / relative_path
            
            try:
                # 디렉토리 생성
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                # 파일 복사
                shutil.copy2(source_path, target_path)
                copied_files.append(rel_str)
                print(f"[복사] {rel_str}")
            except Exception as e:
                error_files.append((rel_str, str(e)))
                print(f"[오류] {rel_str}: {e}")
    
    print("\n" + "=" * 60)
    print("병합 완료")
    print("=" * 60)
    print(f"복사된 파일: {len(copied_files)}개")
    print(f"건너뛴 파일: {len(skipped_files)}개")
    print(f"오류 파일: {len(error_files)}개")
    
    if error_files:
        print("\n오류 발생 파일:")
        for file, error in error_files:
            print(f"  - {file}: {error}")
    
    return len(copied_files), len(skipped_files), len(error_files)

def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("homepage1 → 본진 완전 병합")
    print("=" * 60)
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. homepage1에서 삭제된 파일 목록 가져오기
    print("\n[1단계] 삭제된 파일 목록 확인 중...")
    deleted_files = get_deleted_files()
    print(f"삭제된 파일: {len(deleted_files)}개")
    
    # 2. 본진에서 삭제된 파일 삭제
    if deleted_files:
        print("\n[2단계] 본진에서 삭제된 파일 삭제 중...")
        delete_files_in_main(deleted_files)
    else:
        print("\n[2단계] 삭제할 파일 없음")
    
    # 3. homepage1의 파일을 본진으로 병합
    print("\n[3단계] homepage1 파일 병합 중...")
    copied, skipped, errors = merge_files()
    
    # 4. 워크트리 구분 파일 안내
    print("\n" + "=" * 60)
    print("워크트리 구분 파일 안내")
    print("=" * 60)
    print("다음 파일들은 워크트리별로 다르게 설정되어야 합니다:")
    for file in WORKTREE_SPECIFIC_FILES:
        print(f"  - {file}")
    print("\n본진(main) 설정:")
    print("  - config/settings.py: PORT 기본값을 5000으로 확인 필요")
    print("  - start_server_5001.bat: homepage1 전용 (본진에는 없어야 함)")
    print("  - start_server_5000.bat: 본진용으로 유지")
    
    print("\n" + "=" * 60)
    print("병합 완료!")
    print(f"종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n[ERROR] 병합 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

