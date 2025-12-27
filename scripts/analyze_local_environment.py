#!/usr/bin/env python3
"""
로컬 환경 완전 분석 스크립트
로컬의 데이터베이스, 환경 변수, 파일 구조를 분석하여 서버와 비교할 수 있도록 합니다.
"""

import sqlite3
import os
import json
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
DB_PATH = project_root / 'database' / 'app.db'
OUTPUT_FILE = project_root / 'local_environment_analysis.json'


def analyze_database():
    """데이터베이스 완전 분석"""
    if not DB_PATH.exists():
        return {"error": "데이터베이스 파일 없음"}
    
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 테이블 목록
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    
    # 각 테이블의 구조 및 데이터 개수
    table_info = {}
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        row_count = cursor.fetchone()[0]
        
        table_info[table] = {
            "columns": columns,
            "row_count": row_count
        }
    
    conn.close()
    
    return {
        "tables": tables,
        "table_info": table_info,
        "total_tables": len(tables)
    }


def analyze_env_file():
    """환경 변수 파일 분석"""
    env_file = project_root / '.env'
    if not env_file.exists():
        return {"exists": False}
    
    env_vars = {}
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                # SECRET_KEY는 값만 표시 (보안)
                if 'SECRET' in key.upper() or 'KEY' in key.upper():
                    env_vars[key] = "***설정됨***" if value else "미설정"
                else:
                    env_vars[key] = value
    
    return {
        "exists": True,
        "variables": env_vars
    }


def analyze_static_files():
    """정적 파일 분석"""
    static_dir = project_root / 'static'
    if not static_dir.exists():
        return {"exists": False}
    
    files = []
    for root, dirs, filenames in os.walk(static_dir):
        for filename in filenames:
            filepath = Path(root) / filename
            relative_path = filepath.relative_to(static_dir)
            files.append({
                "path": str(relative_path),
                "size": filepath.stat().st_size,
                "exists": True
            })
    
    return {
        "exists": True,
        "file_count": len(files),
        "files": files
    }


def analyze_requirements():
    """의존성 패키지 분석"""
    requirements_file = project_root / 'requirements.txt'
    if not requirements_file.exists():
        return {"exists": False}
    
    packages = []
    with open(requirements_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                packages.append(line)
    
    return {
        "exists": True,
        "packages": packages,
        "package_count": len(packages)
    }


def main():
    """메인 분석 프로세스"""
    print("=" * 60)
    print("🔍 로컬 환경 완전 분석 시작")
    print("=" * 60)
    
    analysis = {
        "timestamp": datetime.now().isoformat(),
        "project_root": str(project_root),
        "database": analyze_database(),
        "environment": analyze_env_file(),
        "static_files": analyze_static_files(),
        "requirements": analyze_requirements()
    }
    
    # JSON 파일로 저장
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)
    
    # 요약 출력
    print("\n📊 분석 결과 요약:")
    print(f"  - 데이터베이스 테이블: {analysis['database'].get('total_tables', 0)}개")
    print(f"  - 환경 변수: {len(analysis['environment'].get('variables', {}))}개")
    print(f"  - 정적 파일: {analysis['static_files'].get('file_count', 0)}개")
    print(f"  - 패키지: {analysis['requirements'].get('package_count', 0)}개")
    
    print(f"\n✅ 분석 결과 저장: {OUTPUT_FILE}")
    print("\n이 파일을 서버와 비교하여 차이점을 찾을 수 있습니다.")


if __name__ == '__main__':
    main()

