#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Python 패키지 및 도구 최신 버전 확인 스크립트
"""
import sys
import subprocess
import json
import requests
from packaging import version

def get_python_version():
    """현재 Python 버전 확인"""
    return sys.version.split()[0]

def get_installed_packages():
    """설치된 패키지 목록 및 버전 확인"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--format=json"],
            capture_output=True,
            text=True,
            check=True
        )
        packages = json.loads(result.stdout)
        return {pkg['name'].lower(): pkg['version'] for pkg in packages}
    except Exception as e:
        print(f"[오류] 패키지 목록 확인 실패: {e}")
        return {}

def get_latest_version(package_name):
    """PyPI에서 최신 버전 확인"""
    try:
        url = f"https://pypi.org/pypi/{package_name}/json"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data['info']['version']
    except Exception as e:
        return None
    return None

def check_pip_version():
    """pip 버전 확인"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except:
        return "확인 불가"

def check_uv_version():
    """uv 버전 확인"""
    try:
        result = subprocess.run(
            ["uv", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except:
        return "미설치"

def main():
    print("=" * 70)
    print("Python 및 패키지 버전 확인")
    print("=" * 70)
    print()
    
    # Python 버전
    python_ver = get_python_version()
    print(f"[Python] 현재 버전: {python_ver}")
    print(f"         실행 경로: {sys.executable}")
    print()
    
    # pip 버전
    pip_info = check_pip_version()
    print(f"[pip] {pip_info}")
    print()
    
    # uv 버전
    uv_info = check_uv_version()
    print(f"[uv] {uv_info}")
    print()
    
    # requirements.txt에 있는 패키지들
    required_packages = [
        "Flask", "Werkzeug", "Jinja2", "MarkupSafe", "itsdangerous", "click", "blinker",
        "sqlalchemy", "pandas", "openpyxl", "xlrd", "requests", "psutil",
        "python-dotenv", "APScheduler", "bcrypt", "Flask-Limiter", "gunicorn"
    ]
    
    print("=" * 70)
    print("주요 패키지 버전 비교")
    print("=" * 70)
    print()
    print(f"{'패키지명':<25} {'현재 버전':<15} {'최신 버전':<15} {'상태':<10}")
    print("-" * 70)
    
    installed = get_installed_packages()
    
    updates_available = []
    up_to_date = []
    not_installed = []
    
    for pkg in required_packages:
        pkg_lower = pkg.lower()
        current = installed.get(pkg_lower, "미설치")
        latest = get_latest_version(pkg)
        
        if current == "미설치":
            status = "❌ 미설치"
            not_installed.append(pkg)
        elif latest:
            try:
                if version.parse(current) < version.parse(latest):
                    status = "⚠️ 업데이트 필요"
                    updates_available.append((pkg, current, latest))
                else:
                    status = "✅ 최신"
                    up_to_date.append(pkg)
            except:
                status = "❓ 확인 불가"
        else:
            status = "❓ 확인 불가"
        
        latest_str = latest if latest else "확인 불가"
        print(f"{pkg:<25} {current:<15} {latest_str:<15} {status:<10}")
    
    print()
    print("=" * 70)
    print("요약")
    print("=" * 70)
    print(f"✅ 최신 버전: {len(up_to_date)}개")
    print(f"⚠️ 업데이트 필요: {len(updates_available)}개")
    print(f"❌ 미설치: {len(not_installed)}개")
    print()
    
    if updates_available:
        print("업데이트 가능한 패키지:")
        for pkg, current, latest in updates_available:
            print(f"  - {pkg}: {current} → {latest}")
        print()
        print("업데이트 명령어:")
        print(f"  {sys.executable} -m pip install --upgrade " + " ".join([pkg.lower() for pkg, _, _ in updates_available]))
    
    if not_installed:
        print("미설치 패키지:")
        for pkg in not_installed:
            print(f"  - {pkg}")
        print()
        print("설치 명령어:")
        print(f"  {sys.executable} -m pip install " + " ".join(not_installed))

if __name__ == "__main__":
    main()

