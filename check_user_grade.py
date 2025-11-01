import sqlite3
import os

db_path = r'C:\Users\user\Desktop\RohaTax\database\app.db'
conn = sqlite3.connect(db_path)

cursor = conn.execute(
    'SELECT id, username, plan_type, token_balance, tokens_used FROM users WHERE username = ?',
    ('tlschs22',)
)
row = cursor.fetchone()

if row:
    print(f"사용자: {row[1]}")
    print(f"ID: {row[0]}")
    print(f"등급: {row[2]}")
    print(f"토큰 총량: {row[3]}")
    print(f"토큰 사용량: {row[4]}")
    print(f"남은 토큰: {(row[3] or 0) - (row[4] or 0)}")
else:
    print("사용자를 찾을 수 없습니다")

conn.close()

