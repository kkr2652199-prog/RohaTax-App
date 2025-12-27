#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
로컬 데이터베이스를 서버로 동기화하는 스크립트
서버의 users 테이블 구조에 맞춰서 데이터를 변환하여 전송
"""
import sqlite3
import sys
import subprocess
import os

# 서버에 있는 컬럼만 사용 (schema.sql 기준)
SERVER_COLUMNS = [
    'id', 'username', 'email', 'password', 'company_name', 'business_number',
    'representative_name', 'phone', 'address', 'business_type', 'business_category',
    'plan_type', 'used_count', 'monthly_limit', 'is_active', 'is_admin',
    'token_balance', 'tokens_used', 'last_refill_date', 'subscription_status',
    'subscription_id', 'trial_end_date', 'is_deleted', 'deleted_at',
    'approval_status', 'terms_agreed', 'privacy_agreed', 'terms_agreed_at',
    'privacy_agreed_at', 'google_api_key', 'created_at', 'updated_at'
]

LOCAL_DB = 'database/app.db'
SERVER_HOST = 'ubuntu@52.78.116.159'
SERVER_DB_PATH = '/home/ubuntu/RohaTax-App/database/app.db'

def export_users_to_sql():
    """로컬 users 데이터를 서버용 SQL로 변환"""
    if not os.path.exists(LOCAL_DB):
        print(f"ERROR: 로컬 데이터베이스 없음: {LOCAL_DB}")
        return None
    
    conn = sqlite3.connect(LOCAL_DB)
    cursor = conn.cursor()
    
    # 로컬 테이블 구조 확인
    cursor.execute('PRAGMA table_info(users)')
    local_columns = {col[1]: i for i, col in enumerate(cursor.fetchall())}
    
    # 사용자 데이터 조회
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    
    # SQL 생성
    sql_lines = [
        "BEGIN TRANSACTION;",
        "DELETE FROM users;",
        ""
    ]
    
    for user in users:
        server_cols = []
        server_vals = []
        
        for col_name in SERVER_COLUMNS:
            if col_name in local_columns:
                idx = local_columns[col_name]
                val = user[idx] if idx < len(user) else None
            else:
                val = None
            
            server_cols.append(col_name)
            
            if val is None:
                server_vals.append('NULL')
            elif isinstance(val, str):
                escaped = val.replace("'", "''")
                server_vals.append(f"'{escaped}'")
            elif isinstance(val, int):
                server_vals.append(str(val))
            else:
                server_vals.append(f"'{str(val)}'")
        
        cols_str = ', '.join(server_cols)
        vals_str = ', '.join(server_vals)
        sql_lines.append(f"INSERT INTO users ({cols_str}) VALUES ({vals_str});")
    
    sql_lines.append("")
    sql_lines.append("COMMIT;")
    
    conn.close()
    
    return '\n'.join(sql_lines)

def generate_server_script(sql_content):
    """서버에서 실행할 Python 스크립트 생성"""
    return f"""#!/usr/bin/env python3
import sqlite3

sql = \"\"\"
{sql_content}
\"\"\"

conn = sqlite3.connect('database/app.db')
cursor = conn.cursor()
cursor.executescript(sql)
conn.commit()

cursor.execute('SELECT COUNT(*) FROM users')
count = cursor.fetchone()[0]
print(f"Inserted {{count}} users")

cursor.execute('SELECT id, username, is_admin FROM users')
users = cursor.fetchall()
for u in users:
    print(f"  ID {{u[0]}}: {{u[1]}} (admin={{u[2]}})")

conn.close()
print("Done!")
"""

def main():
    print("=" * 60)
    print("로컬 -> 서버 데이터베이스 동기화")
    print("=" * 60)
    
    # 1. 로컬 데이터베이스에서 SQL 생성
    print("\n[1] 로컬 데이터베이스 읽는 중...")
    sql_content = export_users_to_sql()
    
    if not sql_content:
        sys.exit(1)
    
    print("OK: SQL 생성 완료")
    
    # 2. 서버 스크립트 생성
    print("\n[2] 서버 실행 스크립트 생성 중...")
    server_script = generate_server_script(sql_content)
    
    # 임시 파일로 저장
    temp_script = 'temp_sync_db.py'
    with open(temp_script, 'w', encoding='utf-8') as f:
        f.write(server_script)
    
    print(f"OK: 스크립트 생성: {temp_script}")
    
    # 3. 서버로 전송 및 실행 안내
    print("\n[3] 서버로 전송 방법:")
    print(f"   방법 1: scp로 전송 후 실행")
    print(f"   scp {temp_script} {SERVER_HOST}:/tmp/")
    print(f"   ssh {SERVER_HOST} 'cd /home/ubuntu/RohaTax-App && sudo python3 /tmp/{temp_script}'")
    print()
    print(f"   방법 2: 직접 복사해서 서버에서 실행")
    print(f"   (서버 터미널에서 아래 내용 실행)")
    print()
    print("-" * 60)
    print(server_script)
    print("-" * 60)
    
    print("\nOK: 준비 완료!")
    print(f"   임시 파일: {temp_script}")
    print("   이 파일을 삭제하려면: rm temp_sync_db.py")

if __name__ == '__main__':
    main()

