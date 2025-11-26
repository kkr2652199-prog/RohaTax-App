import sqlite3
conn = sqlite3.connect('database/test_app.db')
cur = conn.cursor()
row = cur.execute('SELECT id, email FROM users WHERE email = ?', ('kweon4309@naver.com',)).fetchone()
print(row)
conn.close()
