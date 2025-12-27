#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
전초기지(homepage1)에서 본진으로 완벽한 병합 스크립트
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
import json

# Windows 콘솔 인코딩 설정
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).parent.parent
HOMEPAGE1_DIR = PROJECT_ROOT / "homepage1"
MAIN_DIR = PROJECT_ROOT

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
}

# 의존성 매핑 (파일 확장자별 관련 파일 패턴)
DEPENDENCY_PATTERNS = {
    ".py": {
        "routes": ["templates", "static"],
        "templates": ["static/css", "static/js"],
    },
    ".html": {
        "templates": ["static/css", "static/js"],
    },
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
    # 절대 경로를 상대 경로로 변환
    try:
        rel_path = filepath.relative_to(PROJECT_ROOT)
    except ValueError:
        return True
    
    # homepage1 자체는 제외
    if "homepage1" in rel_path.parts and rel_path.parts[0] != "homepage1":
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


def find_dependency_files(filepath: Path, homepage1_files: Dict) -> Set[str]:
    """파일의 의존성 파일 찾기"""
    dependencies = set()
    
    # 파일 확장자 확인
    ext = filepath.suffix.lower()
    rel_path_str = str(filepath.relative_to(HOMEPAGE1_DIR)).replace("\\", "/")
    
    # 라우트 파일인 경우
    if "routes" in rel_path_str and ext == ".py":
        # 템플릿 파일 찾기
        route_name = filepath.stem.replace("_routes", "").replace("_", "")
        
        # 가능한 템플릿 경로
        template_patterns = [
            f"templates/{route_name}/",
            f"templates/{route_name.replace('_', '/')}/",
        ]
        
        for pattern in template_patterns:
            for file_key in homepage1_files.keys():
                if pattern in file_key and file_key.endswith(".html"):
                    dependencies.add(file_key)
        
        # 관련 CSS/JS 찾기
        for file_key in homepage1_files.keys():
            if "static" in file_key:
                # 라우트 이름과 관련된 정적 파일
                if route_name in file_key.lower() or filepath.stem.replace("_routes", "") in file_key.lower():
                    dependencies.add(file_key)
    
    # 템플릿 파일인 경우
    elif "templates" in rel_path_str and ext == ".html":
        # 템플릿에서 참조하는 CSS/JS 찾기
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                
                # CSS 참조 찾기
                import re
                css_matches = re.findall(r'["\']([^"\']*\.css)["\']', content)
                js_matches = re.findall(r'["\']([^"\']*\.js)["\']', content)
                
                for match in css_matches + js_matches:
                    # static 경로로 변환
                    if match.startswith("/static/"):
                        static_path = match[1:]  # /static/ -> static/
                        if static_path in homepage1_files:
                            dependencies.add(static_path)
                    elif "static" in match:
                        # 상대 경로 처리
                        for file_key in homepage1_files.keys():
                            if match.split("/")[-1] in file_key:
                                dependencies.add(file_key)
        except Exception as e:
            print(f"⚠️ 의존성 분석 실패: {filepath} - {e}")
    
    return dependencies


def compare_files(
    homepage1_files: Dict, main_files: Dict
) -> Tuple[List[str], List[str], List[str]]:
    """파일 비교 및 변경 사항 식별"""
    changed = []  # 변경된 파일
    new_files = []  # 새 파일
    missing = []  # 본진에 없는 파일
    
    # homepage1의 모든 파일 확인
    for rel_path, (filepath, hash_val, size) in homepage1_files.items():
        if rel_path in main_files:
            # 파일이 존재함 - 해시 비교
            main_hash = main_files[rel_path][1]
            if hash_val != main_hash:
                changed.append(rel_path)
        else:
            # 본진에 없는 파일
            new_files.append(rel_path)
    
    # 본진에만 있는 파일 확인 (삭제된 파일)
    for rel_path in main_files.keys():
        if rel_path not in homepage1_files:
            # homepage1에 없는 파일은 제외 (데이터베이스 등)
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
    homepage1_files: Dict,
    main_files: Dict,
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
        source_path = HOMEPAGE1_DIR / rel_path
        dest_path = MAIN_DIR / rel_path
        
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
    homepage1_files: Dict,
    main_files: Dict,
) -> str:
    """병합 보고서 생성"""
    report = []
    report.append("=" * 80)
    report.append("📊 병합 보고서")
    report.append("=" * 80)
    report.append(f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # 통계
    report.append("## 📈 통계")
    report.append(f"- 전초기지 파일 수: {len(homepage1_files)}")
    report.append(f"- 본진 파일 수: {len(main_files)}")
    report.append(f"- 변경된 파일: {len(changed)}")
    report.append(f"- 새 파일: {len(new_files)}")
    report.append(f"- 본진에만 있는 파일: {len(missing)}")
    report.append("")
    
    # 변경된 파일
    if changed:
        report.append("## 🔄 변경된 파일")
        for file in changed:
            homepage1_size = homepage1_files[file][2]
            main_size = main_files[file][2]
            report.append(f"- {file} ({homepage1_size} bytes -> {main_size} bytes)")
        report.append("")
    
    # 새 파일
    if new_files:
        report.append("## ✨ 새 파일")
        for file in new_files:
            size = homepage1_files[file][2]
            report.append(f"- {file} ({size} bytes)")
        report.append("")
    
    # 본진에만 있는 파일
    if missing:
        report.append("## ⚠️ 본진에만 있는 파일 (삭제 고려)")
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
    
    parser = argparse.ArgumentParser(description="전초기지에서 본진으로 병합")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="실제 복사 없이 시뮬레이션만 실행",
    )
    parser.add_argument(
        "--include-deps",
        action="store_true",
        default=True,
        help="의존성 파일 자동 포함 (기본: True)",
    )
    parser.add_argument(
        "--report",
        type=str,
        help="보고서 저장 경로",
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("🚀 전초기지 → 본진 병합 시작")
    print("=" * 80)
    print(f"모드: {'DRY-RUN (시뮬레이션)' if args.dry_run else '실제 병합'}")
    print("")
    
    # 1. 파일 스캔
    print("📂 전초기지 파일 스캔 중...")
    homepage1_files = scan_files(HOMEPAGE1_DIR)
    print(f"✅ 전초기지 파일 {len(homepage1_files)}개 발견")
    
    print("📂 본진 파일 스캔 중...")
    main_files = scan_files(MAIN_DIR)
    print(f"✅ 본진 파일 {len(main_files)}개 발견")
    print("")
    
    # 2. 파일 비교
    print("🔍 파일 비교 중...")
    changed, new_files, missing = compare_files(homepage1_files, main_files)
    print(f"✅ 변경된 파일: {len(changed)}개")
    print(f"✅ 새 파일: {len(new_files)}개")
    print(f"⚠️ 본진에만 있는 파일: {len(missing)}개")
    print("")
    
    # 3. 의존성 파일 추가
    files_to_copy = changed + new_files
    if args.include_deps:
        print("🔗 의존성 파일 분석 중...")
        dependency_files = set()
        
        for rel_path in files_to_copy:
            source_path = HOMEPAGE1_DIR / rel_path
            deps = find_dependency_files(source_path, homepage1_files)
            dependency_files.update(deps)
        
        # 이미 포함된 파일 제외
        dependency_files = dependency_files - set(files_to_copy)
        
        if dependency_files:
            print(f"✅ 의존성 파일 {len(dependency_files)}개 발견")
            files_to_copy.extend(dependency_files)
        print("")
    
    # 4. 파일 복사
    if files_to_copy:
        print(f"📋 복사할 파일: {len(files_to_copy)}개")
        print("")
        
        results = merge_files(files_to_copy, homepage1_files, main_files, args.dry_run)
        
        # 5. 보고서 생성
        report = generate_report(
            changed, new_files, missing, results, homepage1_files, main_files
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
            report_path = PROJECT_ROOT / "merge_report.txt"
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

