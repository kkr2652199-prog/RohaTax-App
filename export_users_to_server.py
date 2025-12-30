#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
로컬 데이터베이스의 사용자 데이터를 서버에 입력할 수 있는 SQL 생성
서버의 users 테이블 구조에 맞춰서 생성 (서버에 없는 컬럼 제외)
"""
import sqlite3
import sys

DB_PATH = 'database/app.db'

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

try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 로컬 테이블 구조 확인
    cursor.execute('PRAGMA table_info(users)')
    local_columns = {col[1]: i for i, col in enumerate(cursor.fetchall())}
    
    # 사용자 데이터 조회
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    
    print(f"-- 총 {len(users)}명의 사용자 데이터")
    print("-- 서버 users 테이블 구조에 맞춘 SQL (서버에 없는 컬럼 제외)")
    print()
    print("BEGIN TRANSACTION;")
    print("DELETE FROM users;")
    print()
    
    for user in users:
        # 서버에 있는 컬럼만 사용
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
                # SQL 인젝션 방지: 작은따옴표 이스케이프
                escaped = val.replace("'", "''")
                server_vals.append(f"'{escaped}'")
            elif isinstance(val, int):
                server_vals.append(str(val))
            else:
                server_vals.append(f"'{str(val)}'")
        
        cols_str = ', '.join(server_cols)
        vals_str = ', '.join(server_vals)
        print(f"INSERT INTO users ({cols_str}) VALUES ({vals_str});")
    
    print()
    print("COMMIT;")
    
    conn.close()
    
except Exception as e:
    print(f"오류: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)

