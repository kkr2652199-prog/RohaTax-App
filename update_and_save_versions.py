#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
패키지를 최신 버전으로 업데이트하고 requirements.txt에 반영
"""
import sys
import subprocess
import re

def run_command(cmd, check=True):
    """명령어 실행"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=check
        )
        return result.stdout.strip(), result.stderr.strip()
    except subprocess.CalledProcessError as e:
        return e.stdout.strip(), e.stderr.strip()

def get_installed_version(package_name):
    """설치된 패키지 버전 확인"""
    stdout, _ = run_command(f'"{sys.executable}" -m pip show {package_name}', check=False)
    if "Version:" in stdout:
        for line in stdout.split('\n'):
            if line.startswith('Version:'):
                return line.replace('Version:', '').strip()
    return None

def update_package(package_name):
    """패키지 업데이트"""
    print(f"  업데이트 중: {package_name}...")
    stdout, stderr = run_command(f'"{sys.executable}" -m pip install --upgrade {package_name}')
    if "Successfully installed" in stdout or "Requirement already satisfied" in stdout:
        return True
    return False

def main():
    print("=" * 70)
    print("Python 패키지 최신 버전 업데이트 및 requirements.txt 갱신")
    print("=" * 70)
    print()
    
    # pip 업데이트
    print("[1/3] pip 최신 버전으로 업데이트...")
    run_command(f'"{sys.executable}" -m pip install --upgrade pip')
    print()
    
    # 패키지 목록
    packages = [
        "Flask", "Werkzeug", "Jinja2", "MarkupSafe", "itsdangerous", 
        "click", "blinker", "sqlalchemy", "pandas", "openpyxl", 
        "xlrd", "requests", "psutil", "python-dotenv", "APScheduler", 
        "bcrypt", "Flask-Limiter", "gunicorn"
    ]
    
    print("[2/3] 패키지 업데이트 중...")
    print()
    
    updated_packages = {}
    
    for pkg in packages:
        if update_package(pkg):
            version = get_installed_version(pkg)
            if version:
                updated_packages[pkg] = version
                print(f"    [OK] {pkg} -> {version}")
        else:
            print(f"    [FAIL] {pkg} 업데이트 실패")
    
    print()
    print("[3/3] requirements.txt 업데이트 중...")
    
    # requirements.txt 읽기
    try:
        with open('requirements.txt', 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"오류: requirements.txt 읽기 실패 - {e}")
        return
    
    # 각 패키지 버전 업데이트
    for pkg, version in updated_packages.items():
        # 패키지명 정규화 (대소문자 구분)
        patterns = [
            (rf'^{pkg}==[\d.]+', f'{pkg}=={version}'),
            (rf'^{pkg.lower()}==[\d.]+', f'{pkg.lower()}=={version}'),
            (rf'^{pkg.upper()}==[\d.]+', f'{pkg.upper()}=={version}'),
        ]
        
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    # requirements.txt 쓰기
    try:
        with open('requirements.txt', 'w', encoding='utf-8') as f:
            f.write(content)
        print("    [OK] requirements.txt 업데이트 완료")
    except Exception as e:
        print(f"    [FAIL] requirements.txt 쓰기 실패 - {e}")
        return
    
    print()
    print("=" * 70)
    print("업데이트 완료!")
    print("=" * 70)
    print()
    print("업데이트된 패키지:")
    for pkg, version in updated_packages.items():
        print(f"  {pkg:<20} {version}")
    print()
    print("requirements.txt 파일이 자동으로 업데이트되었습니다.")

if __name__ == "__main__":
    main()

