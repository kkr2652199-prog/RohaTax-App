import sqlite3

conn = sqlite3.connect('database/app.db')
cursor = conn.execute('SELECT id, username, plan_type FROM users WHERE username = ?', ('tlschs22',))
row = cursor.fetchone()
print(f"User: {row}")
conn.close()

