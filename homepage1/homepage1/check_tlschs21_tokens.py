"""tlschs21 사용자의 토큰 소각 문제 분석"""
import sqlite3
from datetime import datetime
import os

# 데이터베이스 경로
db_path = os.path.join(os.path.dirname(__file__), 'database', 'app.db')

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

# 사용자 정보 조회
user = conn.execute(
    'SELECT id, username, token_balance, plan_type, free_trial_expired_at, subscription_end_date FROM users WHERE username = ?',
    ('tlschs21',)
).fetchone()

if not user:
    print("❌ 사용자를 찾을 수 없습니다: tlschs21")
    conn.close()
    exit(1)

print("=" * 60)
print("=== tlschs21 사용자 정보 ===")
print("=" * 60)
print(f"ID: {user['id']}")
print(f"Username: {user['username']}")
print(f"Token Balance: {user['token_balance']}")
print(f"Plan Type: {user['plan_type']}")
print(f"Free Trial Expired At: {user['free_trial_expired_at']}")
print(f"Subscription End Date: {user['subscription_end_date']}")

# 현재 시간
now = datetime.now()
print(f"\n현재 시간: {now.strftime('%Y-%m-%d %H:%M:%S')}")

# 무료 기간 종료 여부 확인
if user['free_trial_expired_at']:
    try:
        trial_end = datetime.strptime(user['free_trial_expired_at'], '%Y-%m-%d %H:%M:%S')
        is_expired = now > trial_end
        print(f"\n무료 기간 종료일: {user['free_trial_expired_at']}")
        print(f"무료 기간 만료 여부: {'✅ 만료됨' if is_expired else '❌ 아직 유효함'}")
    except:
        print(f"\n⚠️ 무료 기간 종료일 파싱 오류: {user['free_trial_expired_at']}")

print("\n" + "=" * 60)
print("=== 토큰 히스토리 (최근 15개) ===")
print("=" * 60)
tokens = conn.execute(
    """
    SELECT id, amount, change_type, source_type, expires_at, is_expired_processed, created_at, meta
    FROM token_history 
    WHERE user_id = ? 
    ORDER BY created_at DESC 
    LIMIT 15
    """,
    (user['id'],)
).fetchall()

for t in tokens:
    print(f"\n[ID: {t['id']}]")
    print(f"  Amount: {t['amount']}")
    print(f"  Change Type: {t['change_type']}")
    print(f"  Source Type: {t['source_type']}")
    print(f"  Expires At: {t['expires_at']}")
    print(f"  Is Expired Processed: {t['is_expired_processed']}")
    print(f"  Created At: {t['created_at']}")
    if t['meta']:
        print(f"  Meta: {t['meta'][:100]}...")

print("\n" + "=" * 60)
print("=== 만료된 토큰 (미처리) ===")
print("=" * 60)
expired = conn.execute(
    """
    SELECT id, amount, expires_at, source_type, is_expired_processed, created_at
    FROM token_history 
    WHERE user_id = ? 
      AND expires_at IS NOT NULL 
      AND expires_at < datetime('now', 'localtime')
      AND COALESCE(is_expired_processed, 0) = 0 
      AND change_type = 'grant'
    ORDER BY created_at ASC
    """,
    (user['id'],)
).fetchall()

if not expired:
    print("❌ 만료된 미처리 토큰이 없습니다.")
else:
    print(f"✅ 만료된 미처리 토큰 {len(expired)}개 발견:")
    for e in expired:
        print(f"\n[ID: {e['id']}]")
        print(f"  Amount: {e['amount']}")
        print(f"  Source Type: {e['source_type']}")
        print(f"  Expires At: {e['expires_at']}")
        print(f"  Created At: {e['created_at']}")
        print(f"  Is Expired Processed: {e['is_expired_processed']}")

print("\n" + "=" * 60)
print("=== source_type='FREE'인 만료된 토큰 (실제 소각 대상) ===")
print("=" * 60)
free_expired = conn.execute(
    """
    SELECT id, amount, expires_at, source_type, is_expired_processed, created_at
    FROM token_history 
    WHERE user_id = ? 
      AND expires_at IS NOT NULL 
      AND expires_at < datetime('now', 'localtime')
      AND COALESCE(is_expired_processed, 0) = 0 
      AND change_type = 'grant'
      AND COALESCE(source_type, 'PAID') = 'FREE'
    ORDER BY created_at ASC
    """,
    (user['id'],)
).fetchall()

if not free_expired:
    print("❌ source_type='FREE'인 만료된 미처리 토큰이 없습니다.")
    print("\n⚠️ 원인 분석:")
    print("   1. source_type이 'FREE'가 아닐 수 있습니다.")
    print("   2. expires_at이 NULL일 수 있습니다.")
    print("   3. 이미 is_expired_processed = 1로 처리되었을 수 있습니다.")
else:
    print(f"✅ source_type='FREE'인 만료된 미처리 토큰 {len(free_expired)}개 발견:")
    total_amount = 0
    for e in free_expired:
        print(f"\n[ID: {e['id']}]")
        print(f"  Amount: {e['amount']}")
        print(f"  Source Type: {e['source_type']}")
        print(f"  Expires At: {e['expires_at']}")
        print(f"  Created At: {e['created_at']}")
        total_amount += e['amount']
    print(f"\n총 소각 대상 토큰: {total_amount}개")

print("\n" + "=" * 60)
print("=== 토큰 소각 함수 호출 시점 확인 ===")
print("=" * 60)
print("토큰 소각 함수는 다음 시점에 호출됩니다:")
print("1. 로그인 시 (auth_routes.py)")
print("2. get_user_subscription 호출 시 (subscription_utils.py)")
print("\n⚠️ 사용자가 로그인하지 않으면 토큰 소각이 실행되지 않습니다!")

conn.close()


