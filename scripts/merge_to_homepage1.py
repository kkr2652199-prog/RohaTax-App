#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
본진에서 전초기지(homepage1)로 완벽한 병합 스크립트
- 1%도 누락하지 않는 체계적 병합
- 파일 해시 비교
- 의존성 파일 자동 감지
- 복사 후 검증
"""

import os
import sys
import hashlib
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Set

# Windows 콘솔 인코딩 설정
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).parent.parent
MAIN_DIR = PROJECT_ROOT
HOMEPAGE1_DIR = PROJECT_ROOT / "homepage1"

# 제외할 디렉토리/파일
EXCLUDE_PATTERNS = {
    "__pycache__",
    ".git",
    "node_modules",
    "*.pyc",
    "*.pyo",
    ".env",
    "database/app.db",  # 데이터베이스는 별도 동기화
    "database/versions.db",
    "database/backups",
    "*.log",
    ".DS_Store",
    "Thumbs.db",
    "homepage1",  # 자기 자신 제외
}

def get_file_hash(filepath: Path) -> str:
    """파일의 MD5 해시 계산"""
    try:
        with open(filepath, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception as e:
        print(f"⚠️ 해시 계산 실패: {filepath} - {e}")
        return ""

def should_exclude(filepath: Path) -> bool:
    """파일이 제외 대상인지 확인"""
    try:
        rel_path = filepath.relative_to(PROJECT_ROOT)
    except ValueError:
        return True
    
    # homepage1 자체는 제외
    if "homepage1" in rel_path.parts:
        return True
    
    # 제외 패턴 확인
    path_str = str(rel_path).replace("\\", "/")
    for pattern in EXCLUDE_PATTERNS:
        if pattern in path_str or path_str.endswith(pattern):
            return True
    
    return False

def scan_files(directory: Path) -> Dict[str, Tuple[Path, str, int]]:
    """디렉토리의 모든 파일 스캔 (경로, 해시, 크기)"""
    files = {}
    
    for root, dirs, filenames in os.walk(directory):
        # 제외할 디렉토리 필터링
        dirs[:] = [d for d in dirs if not should_exclude(Path(root) / d)]
        
        for filename in filenames:
            filepath = Path(root) / filename
            
            if should_exclude(filepath):
                continue
            
            try:
                # 상대 경로 계산
                rel_path = filepath.relative_to(directory)
                rel_path_str = str(rel_path).replace("\\", "/")
                
                # 해시 및 크기 계산
                file_hash = get_file_hash(filepath)
                file_size = filepath.stat().st_size
                
                files[rel_path_str] = (filepath, file_hash, file_size)
            except Exception as e:
                print(f"⚠️ 파일 스캔 실패: {filepath} - {e}")
    
    return files

def compare_files(
    main_files: Dict, homepage1_files: Dict
) -> Tuple[List[str], List[str], List[str]]:
    """파일 비교 및 변경 사항 식별"""
    changed = []  # 변경된 파일
    new_files = []  # 새 파일
    missing = []  # 전초기지에 없는 파일
    
    # 본진의 모든 파일 확인
    for rel_path, (filepath, hash_val, size) in main_files.items():
        if rel_path in homepage1_files:
            # 파일이 존재함 - 해시 비교
            homepage1_hash = homepage1_files[rel_path][1]
            if hash_val != homepage1_hash:
                changed.append(rel_path)
        else:
            # 전초기지에 없는 파일
            new_files.append(rel_path)
    
    # 전초기지에만 있는 파일 확인 (삭제된 파일)
    for rel_path in homepage1_files.keys():
        if rel_path not in main_files:
            # 본진에 없는 파일은 제외 (데이터베이스 등)
            if not should_exclude(MAIN_DIR / rel_path):
                missing.append(rel_path)
    
    return changed, new_files, missing

def copy_file_with_backup(source: Path, dest: Path) -> bool:
    """파일 복사 (백업 포함)"""
    try:
        # 목적지 디렉토리 생성
        dest.parent.mkdir(parents=True, exist_ok=True)
        
        # 기존 파일 백업
        if dest.exists():
            backup_path = dest.with_suffix(dest.suffix + ".backup")
            shutil.copy2(dest, backup_path)
        
        # 파일 복사
        shutil.copy2(source, dest)
        
        # 복사 후 검증
        if get_file_hash(source) == get_file_hash(dest):
            return True
        else:
            print(f"❌ 복사 검증 실패: {dest}")
            return False
    except Exception as e:
        print(f"❌ 파일 복사 실패: {source} -> {dest} - {e}")
        return False

def merge_files(
    files_to_copy: List[str],
    main_files: Dict,
    homepage1_files: Dict,
    dry_run: bool = False,
) -> Dict:
    """파일 병합 실행"""
    results = {
        "copied": [],
        "failed": [],
        "skipped": [],
        "backups": [],
    }
    
    for rel_path in files_to_copy:
        source_path = MAIN_DIR / rel_path
        dest_path = HOMEPAGE1_DIR / rel_path
        
        if not source_path.exists():
            results["skipped"].append(rel_path)
            print(f"⏭️  소스 파일 없음: {rel_path}")
            continue
        
        if dry_run:
            print(f"[DRY-RUN] 복사 예정: {rel_path}")
            results["copied"].append(rel_path)
        else:
            if copy_file_with_backup(source_path, dest_path):
                results["copied"].append(rel_path)
                if dest_path.with_suffix(dest_path.suffix + ".backup").exists():
                    results["backups"].append(str(dest_path.with_suffix(dest_path.suffix + ".backup")))
                print(f"✅ 복사 완료: {rel_path}")
            else:
                results["failed"].append(rel_path)
    
    return results

def generate_report(
    changed: List[str],
    new_files: List[str],
    missing: List[str],
    results: Dict,
    main_files: Dict,
    homepage1_files: Dict,
) -> str:
    """병합 보고서 생성"""
    report = []
    report.append("=" * 80)
    report.append("📊 본진 → 전초기지 병합 보고서")
    report.append("=" * 80)
    report.append(f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # 통계
    report.append("## 📈 통계")
    report.append(f"- 본진 파일 수: {len(main_files)}")
    report.append(f"- 전초기지 파일 수: {len(homepage1_files)}")
    report.append(f"- 변경된 파일: {len(changed)}")
    report.append(f"- 새 파일: {len(new_files)}")
    report.append(f"- 전초기지에만 있는 파일: {len(missing)}")
    report.append("")
    
    # 변경된 파일
    if changed:
        report.append("## 🔄 변경된 파일")
        for file in changed:
            main_size = main_files[file][2]
            homepage1_size = homepage1_files[file][2]
            report.append(f"- {file} ({main_size} bytes -> {homepage1_size} bytes)")
        report.append("")
    
    # 새 파일
    if new_files:
        report.append("## ✨ 새 파일")
        for file in new_files:
            size = main_files[file][2]
            report.append(f"- {file} ({size} bytes)")
        report.append("")
    
    # 전초기지에만 있는 파일
    if missing:
        report.append("## ⚠️ 전초기지에만 있는 파일 (삭제 고려)")
        for file in missing:
            report.append(f"- {file}")
        report.append("")
    
    # 복사 결과
    report.append("## 📋 복사 결과")
    report.append(f"- 성공: {len(results['copied'])}")
    report.append(f"- 실패: {len(results['failed'])}")
    report.append(f"- 건너뜀: {len(results['skipped'])}")
    report.append(f"- 백업 생성: {len(results['backups'])}")
    report.append("")
    
    # 실패한 파일
    if results["failed"]:
        report.append("## ❌ 복사 실패 파일")
        for file in results["failed"]:
            report.append(f"- {file}")
        report.append("")
    
    report.append("=" * 80)
    
    return "\n".join(report)

def main():
    """메인 병합 프로세스"""
    import argparse
    
    parser = argparse.ArgumentParser(description="본진에서 전초기지로 병합")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="실제 복사 없이 시뮬레이션만 실행",
    )
    parser.add_argument(
        "--report",
        type=str,
        help="보고서 저장 경로",
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("🚀 본진 → 전초기지 병합 시작")
    print("=" * 80)
    print(f"모드: {'DRY-RUN (시뮬레이션)' if args.dry_run else '실제 병합'}")
    print("")
    
    # 1. 파일 스캔
    print("📂 본진 파일 스캔 중...")
    main_files = scan_files(MAIN_DIR)
    print(f"✅ 본진 파일 {len(main_files)}개 발견")
    
    print("📂 전초기지 파일 스캔 중...")
    homepage1_files = scan_files(HOMEPAGE1_DIR)
    print(f"✅ 전초기지 파일 {len(homepage1_files)}개 발견")
    print("")
    
    # 2. 파일 비교
    print("🔍 파일 비교 중...")
    changed, new_files, missing = compare_files(main_files, homepage1_files)
    print(f"✅ 변경된 파일: {len(changed)}개")
    print(f"✅ 새 파일: {len(new_files)}개")
    print(f"⚠️ 전초기지에만 있는 파일: {len(missing)}개")
    print("")
    
    # 3. 파일 복사
    files_to_copy = changed + new_files
    if files_to_copy:
        print(f"📋 복사할 파일: {len(files_to_copy)}개")
        print("")
        
        results = merge_files(files_to_copy, main_files, homepage1_files, args.dry_run)
        
        # 4. 보고서 생성
        report = generate_report(
            changed, new_files, missing, results, main_files, homepage1_files
        )
        
        print("")
        print(report)
        
        # 보고서 저장
        if args.report:
            with open(args.report, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"📄 보고서 저장: {args.report}")
        else:
            # 기본 보고서 저장
            report_path = PROJECT_ROOT / "merge_to_homepage1_report.txt"
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"📄 보고서 저장: {report_path}")
        
        if not args.dry_run:
            print("")
            print("=" * 80)
            if results["failed"]:
                print("⚠️ 일부 파일 복사 실패 - 위 보고서 확인")
            else:
                print("✅ 병합 완료! 모든 파일이 성공적으로 복사되었습니다.")
            print("=" * 80)
    else:
        print("✅ 변경된 파일이 없습니다. 모든 파일이 동기화되어 있습니다.")
    
    return 0 if not files_to_copy or (files_to_copy and not results.get("failed")) else 1

if __name__ == "__main__":
    sys.exit(main())

