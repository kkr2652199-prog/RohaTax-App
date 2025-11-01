import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'database', 'app.db')

conn = sqlite3.connect(db_path)
cursor = conn.execute('SELECT id, username, plan_type FROM users WHERE username = ?', ('tlschs22',))
row = cursor.fetchone()

if row:
    print(f"ID: {row[0]}")
    print(f"Username: {row[1]}")
    print(f"Plan Type: {row[2]}")
    print(f"Plan Type Type: {type(row[2])}")
    print(f"Plan Type == 'gold-vip': {row[2] == 'gold-vip'}")
else:
    print("사용자를 찾을 수 없습니다.")

conn.close()

