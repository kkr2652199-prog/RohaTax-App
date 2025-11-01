import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'database', 'app.db')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # 사용자의 tokens_used를 360으로 되돌림
    cursor.execute("UPDATE users SET tokens_used = 360 WHERE username = ?", ('tlschs22',))
    conn.commit()
    
    # 확인
    cursor.execute("SELECT username, token_balance, tokens_used FROM users WHERE username = ?", ('tlschs22',))
    row = cursor.fetchone()
    if row:
        print(f"사용자: {row[0]}")
        print(f"토큰 지급: {row[1]}")
        print(f"토큰 사용: {row[2]}")
        print(f"남은 토큰: {row[1] - row[2]}")
        print("토큰 상태가 360으로 복원되었습니다.")
except Exception as e:
    print(f"오류 발생: {e}")
finally:
    conn.close()

