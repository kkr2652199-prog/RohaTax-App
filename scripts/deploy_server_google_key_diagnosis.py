#!/usr/bin/env python3
"""
배포 서버 구글 API 키 진단 스크립트
- 데이터베이스에서 사용자별 API 키 확인
- 환경변수 API 키 확인
- 실제 API 호출 테스트
"""

import os
import sys
import sqlite3
from pathlib import Path

# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / 'database' / 'app.db'

def check_database_api_keys():
    """데이터베이스에서 사용자별 API 키 확인"""
    print("\n" + "="*60)
    print("[1단계] 데이터베이스 사용자별 API 키 확인")
    print("="*60)
    
    if not DB_PATH.exists():
        print(f"❌ 데이터베이스 파일이 없습니다: {DB_PATH}")
        return []
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # google_api_key 컬럼 존재 확인
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'google_api_key' not in columns:
            print("❌ users 테이블에 google_api_key 컬럼이 없습니다!")
            return []
        
        # 사용자별 API 키 조회
        cursor.execute("""
            SELECT id, username, email, 
                   google_api_key,
                   CASE 
                       WHEN google_api_key IS NULL THEN 'NULL'
                       WHEN google_api_key = '' THEN '빈 문자열'
                       ELSE '있음'
                   END as key_status,
                   LENGTH(google_api_key) as key_length,
                   CASE 
                       WHEN google_api_key LIKE 'AIzaSy%' THEN '유효 형식'
                       WHEN google_api_key IS NOT NULL AND LENGTH(google_api_key) >= 20 THEN '형식 확인 필요'
                       ELSE '형식 오류'
                   END as key_format
            FROM users 
            WHERE COALESCE(is_deleted, 0) = 0
            ORDER BY id
        """)
        
        users = cursor.fetchall()
        
        if not users:
            print("⚠️ 활성 사용자가 없습니다.")
            return []
        
        print(f"\n총 {len(users)}명의 활성 사용자 발견:\n")
        
        users_with_keys = []
        for user in users:
            user_id = user['id']
            username = user['username']
            email = user['email']
            api_key = user['google_api_key']
            key_status = user['key_status']
            key_length = user['key_length'] if user['key_length'] else 0
            key_format = user['key_format']
            
            status_icon = "✅" if key_status == '있음' else "❌"
            print(f"{status_icon} 사용자 ID: {user_id}, 사용자명: {username}")
            print(f"   이메일: {email}")
            print(f"   API 키 상태: {key_status}")
            if api_key:
                print(f"   API 키 길이: {key_length}")
                print(f"   API 키 형식: {key_format}")
                print(f"   API 키 앞 10자: {api_key[:10]}...")
                if key_status == '있음':
                    users_with_keys.append({
                        'id': user_id,
                        'username': username,
                        'api_key': api_key
                    })
            print()
        
        conn.close()
        return users_with_keys
        
    except Exception as e:
        print(f"❌ 데이터베이스 조회 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return []


def check_environment_variables():
    """환경변수에서 API 키 확인"""
    print("\n" + "="*60)
    print("[2단계] 서버 환경변수 API 키 확인")
    print("="*60)
    
    google_key = os.environ.get('GOOGLE_API_KEY')
    gemini_key = os.environ.get('GEMINI_API_KEY')
    
    print(f"\nGOOGLE_API_KEY: {'✅ 설정됨' if google_key else '❌ 설정 안 됨'}")
    if google_key:
        print(f"   길이: {len(google_key)}")
        print(f"   앞 10자: {google_key[:10]}...")
        print(f"   뒤 10자: ...{google_key[-10:]}")
        # API 키 형식 검증
        if google_key.startswith('AIzaSy'):
            print(f"   형식: ✅ 유효 (AIzaSy로 시작)")
        elif len(google_key) >= 20:
            print(f"   형식: ⚠️ 확인 필요 (길이는 충분하지만 AIzaSy로 시작하지 않음)")
        else:
            print(f"   형식: ❌ 유효하지 않음 (너무 짧음)")
    
    print(f"\nGEMINI_API_KEY: {'✅ 설정됨' if gemini_key else '❌ 설정 안 됨'}")
    if gemini_key:
        print(f"   길이: {len(gemini_key)}")
        print(f"   앞 10자: {gemini_key[:10]}...")
        print(f"   뒤 10자: ...{gemini_key[-10:]}")
        # API 키 형식 검증
        if gemini_key.startswith('AIzaSy'):
            print(f"   형식: ✅ 유효 (AIzaSy로 시작)")
        elif len(gemini_key) >= 20:
            print(f"   형식: ⚠️ 확인 필요 (길이는 충분하지만 AIzaSy로 시작하지 않음)")
        else:
            print(f"   형식: ❌ 유효하지 않음 (너무 짧음)")
    
    # .env 파일 확인
    env_file = PROJECT_ROOT / '.env'
    if env_file.exists():
        print(f"\n.env 파일 존재: ✅")
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                content = f.read()
                has_google_key = 'GOOGLE_API_KEY' in content
                has_gemini_key = 'GEMINI_API_KEY' in content
                print(f"   GOOGLE_API_KEY 포함: {'✅' if has_google_key else '❌'}")
                print(f"   GEMINI_API_KEY 포함: {'✅' if has_gemini_key else '❌'}")
        except Exception as e:
            print(f"   .env 파일 읽기 실패: {e}")
    else:
        print(f"\n.env 파일 존재: ❌")
    
    return google_key or gemini_key


def test_api_key_retrieval():
    """실제 _get_api_key 함수 로직 테스트 (가상환경 사용)"""
    print("\n" + "="*60)
    print("[3단계] API 키 조회 로직 테스트")
    print("="*60)
    
    # 가상환경 경로 확인
    venv_path = PROJECT_ROOT / 'venv'
    venv_python = venv_path / 'bin' / 'python3'
    
    if not venv_python.exists():
        print("⚠️ 가상환경을 찾을 수 없습니다. 직접 테스트를 건너뜁니다.")
        print("   대신 수동으로 다음 명령어를 실행하세요:")
        print(f"   source {venv_path}/bin/activate")
        print(f"   python3 -c \"from routes.playground_routes.studio_api import _get_api_key; print(_get_api_key(2))\"")
        return
    
    try:
        import subprocess
        
        # 가상환경의 Python으로 테스트 스크립트 실행
        test_script = f"""
import sys
sys.path.insert(0, '{PROJECT_ROOT}')
from routes.playground_routes.studio_api import _get_api_key
import sqlite3

DB_PATH = '{DB_PATH}'
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor.execute("SELECT id FROM users WHERE COALESCE(is_deleted, 0) = 0 LIMIT 3")
test_user_ids = [row['id'] for row in cursor.fetchall()]
conn.close()

print(f"테스트 사용자 ID: {{test_user_ids}}")

for user_id in test_user_ids:
    try:
        print(f"[테스트] user_id={{user_id}}에서 API 키 조회 시도...")
        api_key = _get_api_key(user_id)
        print(f"✅ 성공! API 키 길이: {{len(api_key)}}, 앞 10자: {{api_key[:10]}}...")
    except Exception as e:
        print(f"❌ 실패: {{e}}")
        import traceback
        traceback.print_exc()
"""
        
        result = subprocess.run(
            [str(venv_python), '-c', test_script],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(PROJECT_ROOT)
        )
        
        if result.returncode == 0:
            print(result.stdout)
        else:
            print(f"❌ 테스트 실행 실패:")
            print(result.stderr)
            print("\n수동 테스트 방법:")
            print(f"   source {venv_path}/bin/activate")
            print(f"   python3 -c \"from routes.playground_routes.studio_api import _get_api_key; print(_get_api_key(2))\"")
            
    except subprocess.TimeoutExpired:
        print("⚠️ 테스트 실행 시간 초과")
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


def check_recent_logs():
    """최근 로그에서 API 키 관련 에러 확인"""
    print("\n" + "="*60)
    print("[4단계] 최근 로그에서 API 키 관련 에러 확인")
    print("="*60)
    
    try:
        import subprocess
        result = subprocess.run(
            ['sudo', 'journalctl', '-u', 'rohatax', '-n', '200', '--no-pager'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print(f"⚠️ 로그 조회 실패 (권한 문제일 수 있음): {result.stderr}")
            return
        
        logs = result.stdout
        api_key_errors = []
        get_api_key_logs = []
        
        for line in logs.split('\n'):
            if 'api_key' in line.lower() or 'api key' in line.lower():
                api_key_errors.append(line)
            if '_get_api_key' in line:
                get_api_key_logs.append(line)
        
        if api_key_errors:
            print(f"\n✅ API 키 관련 로그 {len(api_key_errors)}개 발견:\n")
            for log in api_key_errors[-10:]:  # 최근 10개만
                print(f"  {log}")
        else:
            print("\n⚠️ API 키 관련 로그가 없습니다.")
        
        if get_api_key_logs:
            print(f"\n✅ _get_api_key 함수 호출 로그 {len(get_api_key_logs)}개 발견:\n")
            for log in get_api_key_logs[-10:]:  # 최근 10개만
                print(f"  {log}")
        else:
            print("\n⚠️ _get_api_key 함수 호출 로그가 없습니다.")
            
    except FileNotFoundError:
        print("⚠️ journalctl 명령어를 찾을 수 없습니다.")
    except subprocess.TimeoutExpired:
        print("⚠️ 로그 조회 시간 초과")
    except Exception as e:
        print(f"❌ 로그 조회 중 오류 발생: {e}")


def main():
    """메인 함수"""
    print("\n" + "="*60)
    print("배포 서버 구글 API 키 진단 시작")
    print("="*60)
    print(f"\n프로젝트 루트: {PROJECT_ROOT}")
    print(f"데이터베이스 경로: {DB_PATH}")
    
    # 1. 데이터베이스 확인
    users_with_keys = check_database_api_keys()
    
    # 2. 환경변수 확인
    env_key = check_environment_variables()
    
    # 3. API 키 조회 로직 테스트
    test_api_key_retrieval()
    
    # 4. 최근 로그 확인
    check_recent_logs()
    
    # 종합 결과
    print("\n" + "="*60)
    print("[종합 결과]")
    print("="*60)
    
    if users_with_keys:
        print(f"✅ 데이터베이스에 API 키가 있는 사용자: {len(users_with_keys)}명")
        for user in users_with_keys:
            print(f"   - {user['username']} (ID: {user['id']})")
    else:
        print("❌ 데이터베이스에 API 키가 있는 사용자가 없습니다.")
    
    if env_key:
        print(f"✅ 환경변수에 API 키가 설정되어 있습니다.")
    else:
        print("❌ 환경변수에 API 키가 설정되어 있지 않습니다.")
    
    print("\n진단 완료!")
    print("\n다음 단계:")
    print("1. 위 결과를 확인하여 문제점 파악")
    print("2. 필요시 사용자별 API 키 등록 또는 환경변수 설정")
    print("3. Flask 서비스 재시작: sudo systemctl restart rohatax")


if __name__ == '__main__':
    main()

