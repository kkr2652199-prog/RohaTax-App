#!/usr/bin/env python3
"""데이터베이스 상태 확인 스크립트"""

import sqlite3
import os

def check_db(db_path, name):
    if not os.path.exists(db_path):
        print(f"{name}: 파일이 없습니다")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 테이블 목록
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"\n{name}: {len(tables)}개 테이블")
        print(f"  테이블: {', '.join(tables[:10])}")
        
        # 주요 테이블 확인
        for table in ['products', 'product_packages', 'subscription_plans', 'users']:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  {table}: {count}개")
            except Exception:
                print(f"  {table}: 테이블 없음")
        
        conn.close()
    except Exception as e:
        print(f"{name}: 오류 - {e}")

# 본진 데이터베이스 확인
check_db('database/app.db', '본진 데이터베이스')

# homepage1 데이터베이스 확인
check_db('homepage1/database/app.db', 'Homepage1 데이터베이스')


