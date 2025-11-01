"""
Show the latest password reset token from database
"""
import sqlite3
from datetime import datetime

DB_PATH = r"database/app.db"

print("=" * 60)
print("Password Reset Token Viewer")
print("=" * 60)

try:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get user input for email
    email = input("\n이메일 주소를 입력하세요: ").strip()
    
    if not email:
        print("이메일 주소를 입력해야 합니다.")
        input("\nPress Enter to exit...")
        exit(0)
    
    # Find user
    user = cursor.execute(
        "SELECT id, username, email FROM users WHERE email = ?",
        (email,)
    ).fetchone()
    
    if not user:
        print(f"\n❌ 이메일 '{email}'로 등록된 사용자를 찾을 수 없습니다.")
        input("\nPress Enter to exit...")
        exit(0)
    
    print(f"\n✅ 사용자 발견: {user['username']} (ID: {user['id']})")
    
    # Get latest reset token
    token_row = cursor.execute(
        """
        SELECT token, expires_at, used, created_at 
        FROM password_reset_tokens 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT 1
        """,
        (user['id'],)
    ).fetchone()
    
    if not token_row:
        print("\n❌ 비밀번호 재설정 토큰이 생성되지 않았습니다.")
        print("먼저 비밀번호 찾기를 통해 토큰을 생성하세요.")
        input("\nPress Enter to exit...")
        exit(0)
    
    token = token_row['token']
    expires_at = token_row['expires_at']
    used = token_row['used']
    created_at = token_row['created_at']
    
    print("\n" + "=" * 60)
    print("📧 비밀번호 재설정 토큰 정보")
    print("=" * 60)
    print(f"이메일: {email}")
    print(f"사용자: {user['username']}")
    print(f"토큰: {token}")
    print(f"생성 시간: {created_at}")
    print(f"만료 시간: {expires_at}")
    print(f"사용 여부: {'사용됨' if used else '사용 안됨'}")
    print(f"\n🔗 재설정 링크:")
    print(f"http://localhost:3000/reset-password/{token}")
    print("=" * 60)
    
    # Check if expired
    expiry = datetime.fromisoformat(expires_at)
    if datetime.now() > expiry:
        print("\n⚠️  경고: 토큰이 만료되었습니다.")
    
    if used:
        print("\n⚠️  경고: 토큰이 이미 사용되었습니다.")
    
    conn.close()
    
except sqlite3.Error as e:
    print(f"\n❌ 데이터베이스 오류: {e}")
except Exception as e:
    print(f"\n❌ 오류: {e}")

input("\nPress Enter to exit...")

