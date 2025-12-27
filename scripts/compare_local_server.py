#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""로컬과 서버 환경 비교 스크립트"""
import os
import sys
import sqlite3
from pathlib import Path
from typing import Dict, List, Tuple

# Windows 콘솔 인코딩 설정
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

PROJECT_ROOT = Path(__file__).parent.parent

def get_database_tables(db_path: Path) -> List[str]:
    """데이터베이스 테이블 목록 조회"""
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return tables
    except Exception as e:
        return [f"ERROR: {e}"]

def get_table_row_count(db_path: Path, table: str) -> int:
    """테이블 행 수 조회"""
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        return -1

def check_env_file() -> Dict[str, str]:
    """환경 변수 파일 확인"""
    env_file = PROJECT_ROOT / ".env"
    env_vars = {}
    
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()
    
    return env_vars

def check_static_files() -> Dict[str, int]:
    """정적 파일 확인"""
    static_dir = PROJECT_ROOT / "static"
    counts = {
        "css": 0,
        "js": 0,
        "images": 0,
        "videos": 0,
    }
    
    if static_dir.exists():
        for file_path in static_dir.rglob("*"):
            if file_path.is_file():
                ext = file_path.suffix.lower()
                if ext == ".css":
                    counts["css"] += 1
                elif ext == ".js":
                    counts["js"] += 1
                elif ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
                    counts["images"] += 1
                elif ext in [".mp4", ".mov", ".avi"]:
                    counts["videos"] += 1
    
    return counts

def main():
    """메인 비교 프로세스"""
    print("=" * 80)
    print("🔍 로컬 환경 분석")
    print("=" * 80)
    
    # 1. 데이터베이스 분석
    print("\n## 1. 데이터베이스 분석")
    db_path = PROJECT_ROOT / "database" / "app.db"
    
    if db_path.exists():
        print(f"✅ 데이터베이스 파일 존재: {db_path}")
        print(f"   크기: {db_path.stat().st_size / (1024*1024):.2f} MB")
        
        tables = get_database_tables(db_path)
        print(f"\n📊 테이블 목록 ({len(tables)}개):")
        for table in tables:
            count = get_table_row_count(db_path, table)
            if count >= 0:
                print(f"   - {table}: {count}행")
            else:
                print(f"   - {table}: 확인 실패")
    else:
        print(f"❌ 데이터베이스 파일 없음: {db_path}")
    
    # 2. 환경 변수 분석
    print("\n## 2. 환경 변수 분석")
    env_vars = check_env_file()
    
    if env_vars:
        print(f"✅ .env 파일 존재 ({len(env_vars)}개 변수)")
        for key in ["SECRET_KEY", "ENVIRONMENT", "DEBUG", "DATABASE_URL"]:
            if key in env_vars:
                value = env_vars[key]
                if key == "SECRET_KEY":
                    print(f"   - {key}: {'설정됨' if len(value) >= 32 else '길이 부족'} ({len(value)}자)")
                else:
                    print(f"   - {key}: {value}")
            else:
                print(f"   - {key}: 미설정")
    else:
        print("❌ .env 파일 없음")
    
    # 3. 정적 파일 분석
    print("\n## 3. 정적 파일 분석")
    static_counts = check_static_files()
    total = sum(static_counts.values())
    
    if total > 0:
        print(f"✅ 정적 파일 존재 ({total}개)")
        for file_type, count in static_counts.items():
            if count > 0:
                print(f"   - {file_type.upper()}: {count}개")
    else:
        print("⚠️ 정적 파일 없음")
    
    # 4. 디렉토리 구조 확인
    print("\n## 4. 디렉토리 구조 확인")
    required_dirs = ["database", "static", "templates", "routes", "core", "logs"]
    for dir_name in required_dirs:
        dir_path = PROJECT_ROOT / dir_name
        if dir_path.exists():
            print(f"   ✅ {dir_name}/")
        else:
            print(f"   ❌ {dir_name}/ (없음)")
    
    print("\n" + "=" * 80)
    print("📋 서버 환경과 비교 필요 항목:")
    print("=" * 80)
    print("1. 데이터베이스 테이블 구조 동일성")
    print("2. 환경 변수 설정 동일성")
    print("3. 정적 파일 존재 여부")
    print("4. 파일 권한 설정")
    print("5. 서버 자동 실행 설정 (Systemd)")
    print("=" * 80)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

