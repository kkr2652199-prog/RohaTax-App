import sqlite3

db_path = r'C:\Users\user\Desktop\RohaTax\database\app.db'
conn = sqlite3.connect(db_path)

# Gold VIP로 변경
conn.execute(
    "UPDATE users SET plan_type = ? WHERE id = 3",
    ('gold-vip',)
)
conn.commit()

# 확인
cursor = conn.execute(
    'SELECT id, username, plan_type, tokens_used FROM users WHERE id = 3'
)
row = cursor.fetchone()

print(f"등급 변경 완료:")
print(f"사용자: {row[1]}")
print(f"등급: {row[2]}")
print(f"현재 토큰 사용량: {row[3]}")

conn.close()

