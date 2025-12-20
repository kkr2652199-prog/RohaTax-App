#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Python 패키지 업데이트 확인 (간단 버전)
의존성 없이 실행 가능
"""
import sys
import subprocess
import json

def run_command(cmd):
    """명령어 실행"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except Exception as e:
        return f"오류: {e}"

def main():
    print("=" * 70)
    print("Python 환경 및 패키지 버전 확인")
    print("=" * 70)
    print()
    
    # Python 버전
    python_ver = run_command(f'"{sys.executable}" --version')
    print(f"[Python] {python_ver}")
    print(f"         경로: {sys.executable}")
    print()
    
    # pip 버전
    pip_ver = run_command(f'"{sys.executable}" -m pip --version')
    print(f"[pip] {pip_ver}")
    print()
    
    # 설치된 패키지 목록 (JSON 형식)
    print("=" * 70)
    print("설치된 주요 패키지 버전")
    print("=" * 70)
    print()
    
    packages_to_check = [
        "Flask", "Werkzeug", "Jinja2", "MarkupSafe", "itsdangerous", 
        "click", "blinker", "SQLAlchemy", "pandas", "openpyxl", 
        "xlrd", "requests", "psutil", "python-dotenv", "APScheduler", 
        "bcrypt", "Flask-Limiter", "gunicorn"
    ]
    
    for pkg in packages_to_check:
        version_info = run_command(f'"{sys.executable}" -m pip show {pkg}')
        if "Version:" in version_info:
            version_line = [line for line in version_info.split('\n') if line.startswith('Version:')]
            if version_line:
                version = version_line[0].replace('Version:', '').strip()
                print(f"  {pkg:<20} {version}")
    
    print()
    print("=" * 70)
    print("업데이트 가능한 패키지 확인")
    print("=" * 70)
    print()
    
    outdated = run_command(f'"{sys.executable}" -m pip list --outdated')
    if outdated and "Package" in outdated:
        print(outdated)
    else:
        print("모든 패키지가 최신 버전입니다.")
    
    print()
    print("=" * 70)
    print("추가 정보")
    print("=" * 70)
    print()
    print("최신 버전 확인 방법:")
    print("  1. pip list --outdated")
    print("  2. pip show <패키지명>")
    print("  3. https://pypi.org 에서 검색")
    print()
    print("업데이트 방법:")
    print("  pip install --upgrade <패키지명>")
    print("  pip install --upgrade -r requirements.txt")

if __name__ == "__main__":
    main()

