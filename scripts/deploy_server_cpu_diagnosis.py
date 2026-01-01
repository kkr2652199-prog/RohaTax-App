#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
배포 서버 CPU 급상승 진단 스크립트 (Python 버전)
실행: python3 scripts/deploy_server_cpu_diagnosis.py
"""

import os
import sys
import subprocess
import sqlite3
import time
from datetime import datetime
from pathlib import Path

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def run_command(cmd, shell=True):
    """명령어 실행 및 결과 반환"""
    try:
        result = subprocess.run(
            cmd,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "명령어 실행 시간 초과", 1
    except Exception as e:
        return f"오류: {str(e)}", 1

def check_cpu_processes():
    """CPU 사용량 상위 프로세스 확인"""
    print("\n[2단계] CPU 사용량 상위 프로세스 (상위 10개)")
    print("-" * 60)
    output, code = run_command("ps aux --sort=-%cpu | head -11")
    print(output)
    return output

def check_memory():
    """메모리 사용량 확인"""
    print("\n[3단계] 메모리 사용량")
    print("-" * 60)
    output, code = run_command("free -h")
    print(output)
    return output

def check_disk():
    """디스크 사용량 확인"""
    print("\n[4단계] 디스크 사용량")
    print("-" * 60)
    output, code = run_command("df -h")
    print(output)
    return output

def check_service_status():
    """Flask 서비스 상태 확인"""
    print("\n[5단계] Flask 서비스 상태")
    print("-" * 60)
    output, code = run_command("systemctl status rohatax --no-pager -l | head -20")
    print(output)
    return output

def check_service_logs():
    """서비스 로그 확인 (에러 위주)"""
    print("\n[6단계] 최근 서비스 로그 (최근 50줄, 에러 위주)")
    print("-" * 60)
    output, code = run_command("journalctl -u rohatax -n 50 --no-pager | grep -i -E 'error|exception|traceback|failed|critical' || echo '최근 에러 로그 없음'")
    print(output)
    return output

def check_python_processes():
    """Python 프로세스 확인"""
    print("\n[7단계] Python 프로세스 상세 정보")
    print("-" * 60)
    output, code = run_command("ps aux | grep -E 'python|gunicorn|flask' | grep -v grep")
    print(output)
    return output

def check_network_connections():
    """네트워크 연결 확인"""
    print("\n[8단계] 활성 네트워크 연결 수")
    print("-" * 60)
    # ss 명령어 우선 사용 (더 현대적이고 대부분의 리눅스에 기본 설치됨)
    established, code1 = run_command("ss -an | grep ESTABLISHED | wc -l")
    if code1 != 0:
        # ss가 없으면 netstat 시도
        established, code1 = run_command("netstat -an | grep ESTABLISHED | wc -l")
    
    time_wait, code2 = run_command("ss -an | grep TIME_WAIT | wc -l")
    if code2 != 0:
        # ss가 없으면 netstat 시도
        time_wait, code2 = run_command("netstat -an | grep TIME_WAIT | wc -l")
    
    if code1 == 0 and code2 == 0:
        print(f"ESTABLISHED 연결 수: {established}")
        print(f"TIME_WAIT 연결 수: {time_wait}")
    else:
        print("⚠️  netstat 또는 ss 명령어를 찾을 수 없습니다")
        print("   네트워크 연결 확인을 건너뜁니다")
        established = "0"
        time_wait = "0"
    
    return established, time_wait

def check_database():
    """데이터베이스 상태 확인"""
    print("\n[9단계] 데이터베이스 상태")
    print("-" * 60)
    
    # 프로젝트 루트 경로 (스크립트 위치에서 상위 두 단계)
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    db_path = project_root / 'database' / 'app.db'
    
    if db_path.exists():
        # 파일 크기
        size = db_path.stat().st_size
        size_mb = size / (1024 * 1024)
        print(f"데이터베이스 파일 크기: {size_mb:.2f} MB")
        
        # 파일 수정 시간
        mtime = datetime.fromtimestamp(db_path.stat().st_mtime)
        print(f"데이터베이스 파일 수정 시간: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 데이터베이스 잠금 확인 (간접적으로)
        try:
            conn = sqlite3.connect(str(db_path), timeout=1.0)
            cursor = conn.cursor()
            cursor.execute("PRAGMA busy_timeout = 1000")
            cursor.execute("SELECT 1")
            conn.close()
            print("✅ 데이터베이스 파일 잠금 없음 (정상 접근 가능)")
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e).lower():
                print("⚠️  데이터베이스 파일이 잠겨 있습니다!")
                print(f"   오류: {e}")
            else:
                print(f"⚠️  데이터베이스 접근 오류: {e}")
        except Exception as e:
            print(f"⚠️  데이터베이스 확인 중 오류: {e}")
    else:
        print(f"⚠️  데이터베이스 파일을 찾을 수 없습니다: {db_path}")
    
    return db_path.exists()

def check_system_load():
    """시스템 부하 확인"""
    print("\n[11단계] 시스템 부하 평균 (1분, 5분, 15분)")
    print("-" * 60)
    output, code = run_command("uptime")
    print(output)
    return output

def check_io_wait():
    """I/O 대기 프로세스 확인"""
    print("\n[12단계] I/O 대기 프로세스")
    print("-" * 60)
    output, code = run_command("ps aux | awk '$8 ~ /D/ {print $0}' | head -10 || echo 'I/O 대기 프로세스 없음'")
    print(output)
    return output

def main():
    """메인 진단 함수"""
    print("=" * 60)
    print("배포 서버 CPU 급상승 진단 시작")
    print("=" * 60)
    print(f"\n진단 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 시스템 기본 정보
    print("\n[1단계] 시스템 기본 정보")
    print("-" * 60)
    hostname, _ = run_command("hostname")
    uptime, _ = run_command("uptime")
    print(f"호스트명: {hostname}")
    print(f"Uptime: {uptime}")
    
    # 2. CPU 사용량 확인
    cpu_output = check_cpu_processes()
    
    # 3. 메모리 확인
    check_memory()
    
    # 4. 디스크 확인
    check_disk()
    
    # 5. 서비스 상태 확인
    check_service_status()
    
    # 6. 서비스 로그 확인
    log_output = check_service_logs()
    
    # 7. Python 프로세스 확인
    python_output = check_python_processes()
    
    # 8. 네트워크 연결 확인
    established, time_wait = check_network_connections()
    
    # 9. 데이터베이스 확인
    db_ok = check_database()
    
    # 10. 시스템 부하 확인
    check_system_load()
    
    # 11. I/O 대기 확인
    check_io_wait()
    
    # 진단 결과 요약
    print("\n" + "=" * 60)
    print("진단 결과 요약")
    print("=" * 60)
    
    # CPU 사용량이 높은 프로세스 확인
    if "python" in cpu_output.lower() or "gunicorn" in cpu_output.lower():
        print("\n⚠️  Python/Gunicorn 프로세스가 CPU를 많이 사용하고 있습니다")
        print("   → 서비스 로그를 확인하여 에러 패턴을 찾아보세요")
    
    # 네트워크 연결 수 확인
    try:
        established_count = int(established)
        if established_count > 100:
            print(f"\n⚠️  활성 네트워크 연결이 많습니다 ({established_count}개)")
            print("   → DDoS 공격 또는 무한 루프 가능성 확인 필요")
    except:
        pass
    
    # 데이터베이스 잠금 확인
    if not db_ok:
        print("\n⚠️  데이터베이스 파일을 찾을 수 없습니다")
    
    # 에러 로그 확인
    if "error" in log_output.lower() or "exception" in log_output.lower():
        print("\n⚠️  서비스 로그에 에러가 발견되었습니다")
        print("   → 위의 [6단계] 로그를 자세히 확인하세요")
    
    print("\n💡 다음 단계:")
    print("1. CPU 사용량이 높은 프로세스 확인")
    print("2. Flask 서비스 로그에서 에러 패턴 확인")
    print("3. 데이터베이스 잠금 확인")
    print("4. 네트워크 연결 수 확인 (DDoS 가능성)")
    print("5. 최근 코드 변경사항 확인")
    
    print("\n" + "=" * 60)
    print("진단 완료")
    print("=" * 60)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n진단이 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n진단 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

