#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""상용화 준비 상태 점검 스크립트"""
import os
import sys
from pathlib import Path

# Windows 콘솔 인코딩 설정
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def check_secret_key():
    """SECRET_KEY 확인"""
    print("\n=== SECRET_KEY 점검 ===")
    secret_key = os.getenv("SECRET_KEY", "")
    if secret_key:
        if len(secret_key) >= 32:
            print("✅ SECRET_KEY: 설정됨 (길이:", len(secret_key), "자)")
        else:
            print("⚠️ SECRET_KEY: 설정됨 (길이 부족:", len(secret_key), "자, 32자 이상 권장)")
    else:
        print("❌ SECRET_KEY: 미설정")
        print("   생성 방법: python -c \"import secrets; print(secrets.token_hex(32))\"")
    return bool(secret_key and len(secret_key) >= 32)

def check_environment():
    """환경 설정 확인"""
    print("\n=== 환경 설정 점검 ===")
    env = os.getenv("ENVIRONMENT", "development")
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    print(f"ENVIRONMENT: {env}")
    print(f"DEBUG: {debug}")
    
    if env == "production":
        if not debug:
            print("✅ 프로덕션 환경 설정 정상")
            return True
        else:
            print("❌ 프로덕션 환경에서 DEBUG=True (보안 위험!)")
            return False
    else:
        print("⚠️ 개발 환경 (ENVIRONMENT=production 설정 필요)")
        return False

def check_env_file():
    """.env 파일 확인"""
    print("\n=== .env 파일 점검 ===")
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env 파일 존재")
        # .gitignore 확인
        gitignore = Path(".gitignore")
        if gitignore.exists():
            content = gitignore.read_text(encoding="utf-8", errors="ignore")
            if ".env" in content:
                print("✅ .env가 .gitignore에 포함됨")
            else:
                print("⚠️ .env가 .gitignore에 없음 (Git에 커밋될 수 있음!)")
        return True
    else:
        print("⚠️ .env 파일 없음")
        return False

def check_database():
    """데이터베이스 확인"""
    print("\n=== 데이터베이스 점검 ===")
    db_path = Path("database/app.db")
    if db_path.exists():
        size_mb = db_path.stat().st_size / (1024 * 1024)
        print(f"✅ 데이터베이스 파일 존재: {size_mb:.2f} MB")
        
        # 백업 디렉토리 확인
        backup_dir = Path("database/backups")
        if backup_dir.exists():
            backups = list(backup_dir.glob("*.db"))
            print(f"✅ 백업 파일: {len(backups)}개")
        else:
            print("⚠️ 백업 디렉토리 없음")
        return True
    else:
        print("❌ 데이터베이스 파일 없음")
        return False

def check_server_status():
    """서버 상태 확인"""
    print("\n=== 서버 상태 점검 ===")
    try:
        import requests
        response = requests.get("http://localhost:5000", timeout=2)
        if response.status_code == 200:
            print("✅ 서버 정상 실행 중 (포트 5000)")
            return True
        else:
            print(f"⚠️ 서버 응답: {response.status_code}")
            return False
    except Exception as e:
        print(f"⚠️ 서버 연결 실패: {e}")
        print("   서버가 실행 중이지 않을 수 있습니다")
        return False

def main():
    """메인 점검 프로세스"""
    print("=" * 80)
    print("🚀 상용화 준비 상태 점검")
    print("=" * 80)
    
    results = {
        "secret_key": check_secret_key(),
        "environment": check_environment(),
        "env_file": check_env_file(),
        "database": check_database(),
        "server": check_server_status(),
    }
    
    print("\n" + "=" * 80)
    print("📊 점검 결과 요약")
    print("=" * 80)
    
    critical_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    for key, value in results.items():
        status = "✅" if value else "❌"
        print(f"{status} {key.replace('_', ' ').title()}")
    
    print(f"\n완료: {critical_count}/{total_count}")
    
    if critical_count == total_count:
        print("\n✅ 모든 필수 항목이 준비되었습니다!")
    else:
        print("\n⚠️ 일부 항목이 준비되지 않았습니다.")
        print("   상용화_점검_체크리스트.md 파일을 참고하세요.")
    
    print("=" * 80)
    
    return 0 if critical_count == total_count else 1

if __name__ == "__main__":
    sys.exit(main())

