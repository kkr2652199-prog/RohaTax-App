#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
배포 서버 종합 진단 스크립트

배포 서버의 모든 상태를 점검하고 보고서를 생성합니다.
"""

import subprocess
import os
import sys
from datetime import datetime
from pathlib import Path

def run_command(cmd, shell=False):
    """명령어 실행"""
    try:
        if shell:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        else:
            result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=30)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timeout", 1
    except Exception as e:
        return "", str(e), 1

def check_server_process():
    """서버 프로세스 확인"""
    print("\n=== 1. 서버 프로세스 확인 ===")
    stdout, stderr, code = run_command("netstat -ano | findstr :5000", shell=True)
    if code == 0 and stdout:
        print("[OK] 포트 5000에서 프로세스 실행 중")
        print(stdout)
        # PID 추출
        lines = stdout.split('\n')
        for line in lines:
            if 'LISTENING' in line:
                parts = line.split()
                if len(parts) > 4:
                    pid = parts[-1]
                    print(f"[INFO] 서버 PID: {pid}")
                    return pid
    else:
        print("[WARNING] 포트 5000에서 실행 중인 프로세스 없음")
    return None

def check_server_logs():
    """서버 로그 확인"""
    print("\n=== 2. 서버 로그 확인 ===")
    log_files = [
        "flask_server.log",
        "app.log",
        "logs/flask_server.log",
        "logs/app.log"
    ]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            print(f"[OK] 로그 파일 발견: {log_file}")
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    if lines:
                        print(f"[INFO] 최근 10줄:")
                        for line in lines[-10:]:
                            print(f"  {line.strip()}")
                        # 에러 확인
                        errors = [line for line in lines if 'ERROR' in line or 'error' in line or 'Exception' in line]
                        if errors:
                            print(f"[WARNING] 에러 로그 {len(errors)}개 발견")
                            for err in errors[-5:]:
                                print(f"  {err.strip()}")
            except Exception as e:
                print(f"[ERROR] 로그 파일 읽기 실패: {e}")
            break
    else:
        print("[INFO] 로그 파일을 찾을 수 없음")

def check_database():
    """데이터베이스 확인"""
    print("\n=== 3. 데이터베이스 확인 ===")
    db_paths = [
        "database/app.db",
        "homepage1/database/app.db"
    ]
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            print(f"[OK] 데이터베이스 파일 발견: {db_path}")
            file_size = os.path.getsize(db_path)
            print(f"[INFO] 파일 크기: {file_size / 1024 / 1024:.2f} MB")
            
            # SQLite 확인
            try:
                import sqlite3
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # 테이블 목록
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                print(f"[INFO] 테이블 수: {len(tables)}")
                
                # 주요 테이블 확인
                important_tables = ['users', 'payment_history', 'orders', 'activity_logs']
                for table in important_tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        print(f"  - {table}: {count}개")
                    except:
                        print(f"  - {table}: 테이블 없음")
                
                conn.close()
            except Exception as e:
                print(f"[ERROR] 데이터베이스 확인 실패: {e}")
            break
    else:
        print("[WARNING] 데이터베이스 파일을 찾을 수 없음")

def check_git_version():
    """Git 버전 확인"""
    print("\n=== 4. Git 버전 확인 ===")
    stdout, stderr, code = run_command("git log -1 --format=%H", shell=True)
    if code == 0 and stdout:
        commit_hash = stdout.strip()
        print(f"[OK] 현재 커밋 해시: {commit_hash[:8]}")
        
        stdout, stderr, code = run_command("git branch --show-current", shell=True)
        if code == 0:
            branch = stdout.strip()
            print(f"[INFO] 현재 브랜치: {branch}")
        
        stdout, stderr, code = run_command("git log -1 --format=%s", shell=True)
        if code == 0:
            commit_msg = stdout.strip()
            print(f"[INFO] 최근 커밋: {commit_msg}")
    else:
        print("[WARNING] Git 정보를 가져올 수 없음")

def check_environment():
    """환경 변수 확인"""
    print("\n=== 5. 환경 변수 확인 ===")
    env_vars = ['FLASK_RUN_HOST', 'FLASK_RUN_PORT', 'FLASK_ENV', 'SECRET_KEY']
    for var in env_vars:
        value = os.environ.get(var, 'Not set')
        if var == 'SECRET_KEY' and value != 'Not set':
            value = '***' + value[-4:] if len(value) > 4 else '***'
        print(f"  {var}: {value}")

def check_dependencies():
    """의존성 확인"""
    print("\n=== 6. 의존성 확인 ===")
    if os.path.exists("requirements.txt"):
        print("[OK] requirements.txt 존재")
        try:
            with open("requirements.txt", 'r') as f:
                lines = f.readlines()
                print(f"[INFO] 패키지 수: {len([l for l in lines if l.strip() and not l.startswith('#')])}")
        except Exception as e:
            print(f"[ERROR] requirements.txt 읽기 실패: {e}")
    else:
        print("[WARNING] requirements.txt 없음")
    
    # Python 버전
    print(f"[INFO] Python 버전: {sys.version}")

def check_resources():
    """시스템 리소스 확인"""
    print("\n=== 7. 시스템 리소스 확인 ===")
    try:
        import psutil
        disk = psutil.disk_usage('/')
        memory = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=1)
        
        print(f"[INFO] 디스크 사용량: {disk.percent:.1f}% ({disk.used / 1024 / 1024 / 1024:.2f} GB / {disk.total / 1024 / 1024 / 1024:.2f} GB)")
        print(f"[INFO] 메모리 사용량: {memory.percent:.1f}% ({memory.used / 1024 / 1024 / 1024:.2f} GB / {memory.total / 1024 / 1024 / 1024:.2f} GB)")
        print(f"[INFO] CPU 사용량: {cpu:.1f}%")
        
        if disk.percent > 90:
            print("[WARNING] 디스크 사용량이 90%를 초과했습니다!")
        if memory.percent > 90:
            print("[WARNING] 메모리 사용량이 90%를 초과했습니다!")
    except ImportError:
        print("[INFO] psutil이 설치되지 않아 상세 정보를 확인할 수 없습니다")

def check_health_endpoint():
    """헬스 체크 엔드포인트 확인"""
    print("\n=== 8. 헬스 체크 엔드포인트 확인 ===")
    try:
        import urllib.request
        import json
        response = urllib.request.urlopen('http://localhost:5000/health', timeout=5)
        data = json.loads(response.read().decode())
        print("[OK] 헬스 체크 성공")
        print(f"[INFO] 상태: {data.get('status', 'unknown')}")
        print(f"[INFO] 데이터베이스: {data.get('database', 'unknown')}")
        print(f"[INFO] 업타임: {data.get('uptime', 0):.1f}초")
    except Exception as e:
        print(f"[WARNING] 헬스 체크 실패: {e}")

def main():
    """메인 함수"""
    print("=" * 60)
    print("배포 서버 종합 진단")
    print("=" * 60)
    print(f"진단 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    check_server_process()
    check_server_logs()
    check_database()
    check_git_version()
    check_environment()
    check_dependencies()
    check_resources()
    check_health_endpoint()
    
    print("\n" + "=" * 60)
    print("진단 완료")
    print("=" * 60)

if __name__ == '__main__':
    main()

