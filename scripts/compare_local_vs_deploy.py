#!/usr/bin/env python3
"""
로컬 vs 배포서버 환경 차이 확인 스크립트
- 로컬에서 실행하여 배포서버와 비교할 정보 수집
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

def check_environment():
    """환경변수 확인"""
    print("\n" + "="*60)
    print("[환경변수 확인]")
    print("="*60)
    
    google_key = os.environ.get('GOOGLE_API_KEY')
    gemini_key = os.environ.get('GEMINI_API_KEY')
    
    print(f"GOOGLE_API_KEY: {'✅ 설정됨' if google_key else '❌ 설정 안 됨'}")
    if google_key:
        print(f"   길이: {len(google_key)}")
        print(f"   앞 10자: {google_key[:10]}...")
    
    print(f"GEMINI_API_KEY: {'✅ 설정됨' if gemini_key else '❌ 설정 안 됨'}")
    if gemini_key:
        print(f"   길이: {len(gemini_key)}")
        print(f"   앞 10자: {gemini_key[:10]}...")
    
    # .env 파일 확인
    env_file = PROJECT_ROOT / '.env'
    if env_file.exists():
        print(f"\n.env 파일 존재: ✅")
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                content = f.read()
                has_google = 'GOOGLE_API_KEY' in content
                has_gemini = 'GEMINI_API_KEY' in content
                print(f"   GOOGLE_API_KEY 포함: {'✅' if has_google else '❌'}")
                print(f"   GEMINI_API_KEY 포함: {'✅' if has_gemini else '❌'}")
        except Exception as e:
            print(f"   .env 파일 읽기 실패: {e}")
    else:
        print(f"\n.env 파일 존재: ❌")


def check_code_version():
    """코드 버전 확인"""
    print("\n" + "="*60)
    print("[코드 버전 확인]")
    print("="*60)
    
    studio_api = PROJECT_ROOT / 'routes' / 'playground_routes' / 'studio_api.py'
    if studio_api.exists():
        print(f"studio_api.py 존재: ✅")
        # _get_api_key 함수가 있는지 확인
        with open(studio_api, 'r', encoding='utf-8') as f:
            content = f.read()
            has_get_api_key = 'def _get_api_key(user_id: int)' in content
            has_sqlite3_row = 'sqlite3.Row' in content
            has_logging = 'logger.info' in content or 'logger.error' in content
            
            print(f"   _get_api_key 함수: {'✅' if has_get_api_key else '❌'}")
            print(f"   sqlite3.Row 사용: {'✅' if has_sqlite3_row else '❌'}")
            print(f"   상세 로깅: {'✅' if has_logging else '❌'}")
    else:
        print(f"studio_api.py 존재: ❌")


def check_database():
    """데이터베이스 확인"""
    print("\n" + "="*60)
    print("[데이터베이스 확인]")
    print("="*60)
    
    import sqlite3
    db_path = PROJECT_ROOT / 'database' / 'app.db'
    
    if not db_path.exists():
        print(f"❌ 데이터베이스 파일이 없습니다: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # google_api_key 컬럼 존재 확인
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'google_api_key' not in columns:
            print("❌ users 테이블에 google_api_key 컬럼이 없습니다!")
            conn.close()
            return
        
        # 사용자별 API 키 확인
        cursor.execute("""
            SELECT id, username, 
                   CASE 
                       WHEN google_api_key IS NULL THEN 'NULL'
                       WHEN google_api_key = '' THEN '빈 문자열'
                       ELSE '있음'
                   END as key_status
            FROM users 
            WHERE COALESCE(is_deleted, 0) = 0
            ORDER BY id
        """)
        
        users = cursor.fetchall()
        print(f"\n활성 사용자 {len(users)}명:")
        for user in users:
            print(f"   ID {user['id']}: {user['username']} - API 키: {user['key_status']}")
        
        conn.close()
    except Exception as e:
        print(f"❌ 데이터베이스 조회 중 오류: {e}")


def main():
    print("\n" + "="*60)
    print("로컬 환경 확인 (배포서버와 비교용)")
    print("="*60)
    print(f"\n프로젝트 루트: {PROJECT_ROOT}")
    
    check_environment()
    check_code_version()
    check_database()
    
    print("\n" + "="*60)
    print("[비교 방법]")
    print("="*60)
    print("\n배포서버에서 동일한 스크립트를 실행하여 비교하세요:")
    print("  python3 scripts/compare_local_vs_deploy.py")
    print("\n또는 배포서버에서 다음 정보만 확인:")
    print("  1. 환경변수: echo $GOOGLE_API_KEY")
    print("  2. .env 파일: cat .env | grep GOOGLE_API_KEY")
    print("  3. 데이터베이스: python3 scripts/deploy_server_google_key_diagnosis.py")


if __name__ == '__main__':
    main()

