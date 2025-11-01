import sqlite3
import sys

conn = sqlite3.connect('database/app.db')
conn.row_factory = sqlite3.Row
cursor = conn.execute("SELECT username, password FROM users WHERE username IN ('tlschs23', 'tlschs22')")
for row in cursor.fetchall():
    print(f"Username={row['username']}, Password={row['password']}")
conn.close()
