#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
병합 후 검증 스크립트
- 복사된 파일의 해시 재확인
- 누락 파일 자동 감지
- 상세 검증 보고서 생성
"""

import os
import sys
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# Windows 콘솔 인코딩 설정
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

PROJECT_ROOT = Path(__file__).parent.parent
HOMEPAGE1_DIR = PROJECT_ROOT / "homepage1"
MAIN_DIR = PROJECT_ROOT


def get_file_hash(filepath: Path) -> str:
    """파일의 MD5 해시 계산"""
    try:
        with open(filepath, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception as e:
        return f"ERROR: {e}"


def verify_file(homepage1_path: Path, main_path: Path) -> Tuple[bool, str]:
    """파일 검증"""
    if not homepage1_path.exists():
        return False, "전초기지 파일 없음"
    
    if not main_path.exists():
        return False, "본진 파일 없음"
    
    homepage1_hash = get_file_hash(homepage1_path)
    main_hash = get_file_hash(main_path)
    
    if homepage1_hash.startswith("ERROR") or main_hash.startswith("ERROR"):
        return False, f"해시 계산 실패: {homepage1_hash} / {main_hash}"
    
    if homepage1_hash != main_hash:
        return False, f"해시 불일치: {homepage1_hash[:8]}... != {main_hash[:8]}..."
    
    return True, "OK"


def scan_and_verify() -> Dict:
    """전체 파일 스캔 및 검증"""
    results = {
        "verified": [],
        "mismatched": [],
        "missing_in_main": [],
        "missing_in_homepage1": [],
        "errors": [],
    }
    
    # homepage1 파일 스캔
    homepage1_files = {}
    for root, dirs, files in os.walk(HOMEPAGE1_DIR):
        # 제외 디렉토리 필터링
        dirs[:] = [d for d in dirs if d not in ["__pycache__", ".git", "node_modules"]]
        
        for file in files:
            if file.endswith((".pyc", ".pyo", ".log")):
                continue
            
            filepath = Path(root) / file
            rel_path = filepath.relative_to(HOMEPAGE1_DIR)
            rel_path_str = str(rel_path).replace("\\", "/")
            
            # .env 파일 제외 (환경 변수 파일은 환경별로 다름)
            if ".env" in rel_path_str:
                continue
            
            homepage1_files[rel_path_str] = filepath
    
    # 본진 파일과 비교
    for rel_path_str, homepage1_path in homepage1_files.items():
        main_path = MAIN_DIR / rel_path_str
        
        # 데이터베이스 등 제외
        if "database/app.db" in rel_path_str or "database/versions.db" in rel_path_str:
            continue
        
        # .env 파일 제외 (환경 변수 파일은 환경별로 다름)
        if ".env" in rel_path_str:
            continue
        
        # .git 디렉토리 제외
        if ".git" in rel_path_str:
            continue
        
        is_valid, message = verify_file(homepage1_path, main_path)
        
        if is_valid:
            results["verified"].append(rel_path_str)
        elif not main_path.exists():
            results["missing_in_main"].append(rel_path_str)
        else:
            results["mismatched"].append((rel_path_str, message))
    
    # 본진에만 있는 파일 확인
    for root, dirs, files in os.walk(MAIN_DIR):
        # homepage1 제외
        if "homepage1" in Path(root).parts:
            continue
        
        dirs[:] = [d for d in dirs if d not in ["__pycache__", ".git", "node_modules", "homepage1"]]
        
        for file in files:
            if file.endswith((".pyc", ".pyo", ".log")):
                continue
            
            filepath = Path(root) / file
            rel_path = filepath.relative_to(MAIN_DIR)
            rel_path_str = str(rel_path).replace("\\", "/")
            
            # 데이터베이스 등 제외
            if "database/app.db" in rel_path_str or "database/versions.db" in rel_path_str:
                continue
            
            # .env 파일 제외
            if ".env" in rel_path_str:
                continue
            
            # 백업 파일 제외
            if rel_path_str.endswith(".backup"):
                continue
            
            homepage1_path = HOMEPAGE1_DIR / rel_path_str
            if not homepage1_path.exists():
                results["missing_in_homepage1"].append(rel_path_str)
    
    return results


def generate_verification_report(results: Dict) -> str:
    """검증 보고서 생성"""
    report = []
    report.append("=" * 80)
    report.append("🔍 병합 검증 보고서")
    report.append("=" * 80)
    report.append(f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # 통계
    report.append("## 📊 검증 통계")
    report.append(f"- ✅ 검증 통과: {len(results['verified'])}개")
    report.append(f"- ❌ 해시 불일치: {len(results['mismatched'])}개")
    report.append(f"- ⚠️ 본진에 없음: {len(results['missing_in_main'])}개")
    report.append(f"- ℹ️ 전초기지에 없음: {len(results['missing_in_homepage1'])}개")
    report.append("")
    
    # 검증 통과
    if results["verified"]:
        report.append("## ✅ 검증 통과 파일")
        for file in results["verified"][:20]:  # 최대 20개만 표시
            report.append(f"- {file}")
        if len(results["verified"]) > 20:
            report.append(f"... 외 {len(results['verified']) - 20}개")
        report.append("")
    
    # 해시 불일치
    if results["mismatched"]:
        report.append("## ❌ 해시 불일치 파일 (즉시 확인 필요!)")
        for file, message in results["mismatched"]:
            report.append(f"- {file}")
            report.append(f"  이유: {message}")
        report.append("")
    
    # 본진에 없음
    if results["missing_in_main"]:
        report.append("## ⚠️ 본진에 없는 파일 (복사 누락!)")
        for file in results["missing_in_main"]:
            report.append(f"- {file}")
        report.append("")
    
    # 전초기지에 없음 (정상 - 본진 전용 파일)
    if results["missing_in_homepage1"]:
        report.append("## ℹ️ 전초기지에 없는 파일 (본진 전용)")
        for file in results["missing_in_homepage1"][:10]:  # 최대 10개만 표시
            report.append(f"- {file}")
        if len(results["missing_in_homepage1"]) > 10:
            report.append(f"... 외 {len(results['missing_in_homepage1']) - 10}개")
        report.append("")
    
    # 결론
    report.append("=" * 80)
    if results["mismatched"] or results["missing_in_main"]:
        report.append("❌ 검증 실패 - 위 파일들을 확인하고 재병합하세요!")
    else:
        report.append("✅ 모든 파일이 정상적으로 병합되었습니다!")
    report.append("=" * 80)
    
    return "\n".join(report)


def main():
    """메인 검증 프로세스"""
    print("=" * 80)
    print("🔍 병합 검증 시작")
    print("=" * 80)
    print("")
    
    results = scan_and_verify()
    report = generate_verification_report(results)
    
    print(report)
    
    # 보고서 저장
    report_path = PROJECT_ROOT / "merge_verification_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n📄 검증 보고서 저장: {report_path}")
    
    # 종료 코드
    if results["mismatched"] or results["missing_in_main"]:
        print("\n⚠️ 검증 실패 - 재병합이 필요합니다!")
        return 1
    else:
        print("\n✅ 검증 완료 - 모든 파일이 정상입니다!")
        return 0


if __name__ == "__main__":
    sys.exit(main())

