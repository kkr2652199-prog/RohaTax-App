import sqlite3
import sys

conn = sqlite3.connect('database/app.db')
conn.row_factory = sqlite3.Row
cursor = conn.execute("SELECT id, username, email, plan_type FROM users WHERE username IN ('tlschs23', 'tlschs22')")
for row in cursor.fetchall():
    print(f"ID={row['id']}, Username={row['username']}, Email={row['email']}, Plan={row['plan_type']}")
conn.close()
