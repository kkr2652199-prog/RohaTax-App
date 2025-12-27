#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
서버에서 실행할 상품 데이터 삽입 스크립트
AWS Lightsail 서버에서 실행용
"""

import sqlite3
import os
import sys
from pathlib import Path

# 프로젝트 루트 경로 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 데이터베이스 경로
DB_PATH = project_root / 'database' / 'app.db'

def seed_products():
    """상품 데이터 삽입"""
    print("=" * 60)
    print("🚀 상품 데이터 삽입 시작")
    print("=" * 60)
    
    if not DB_PATH.exists():
        print(f"❌ 데이터베이스 파일을 찾을 수 없습니다: {DB_PATH}")
        sys.exit(1)
    
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # 기존 데이터 확인 및 삭제 (선택사항)
        print("\n[1단계] 기존 상품 데이터 확인 중...")
        existing = c.execute("SELECT COUNT(*) as count FROM products").fetchone()
        print(f"   기존 상품 수: {existing['count']}개")
        
        # 상품 데이터 준비
        products = [
            # (name, description, price, token_amount, duration_days, type, is_active)
            ('Welcome Event', '신규 가입 혜택 (50토큰)', 0, 50, 0, 'event', 1),
            ('Welcome Period Event', '신규 가입 혜택 (3일 무료)', 0, 0, 3, 'event_period', 1),
            ('Standard', '필요할 때만 사용하는 유연한 플랜', 300, 1, 0, 'package', 1),
            ('Premium', '100건 패키지로 한 번에 해결', 15000, 100, 0, 'package', 1),
            ('Gold', '세무사/대리 발급 전문', 100000, 999999, 30, 'subscription', 1),
        ]
        
        print("\n[2단계] 상품 데이터 삽입 중...")
        inserted_count = 0
        skipped_count = 0
        
        for p in products:
            name, description, price, token_amount, duration_days, product_type, is_active = p
            
            # 중복 확인
            c.execute('SELECT id FROM products WHERE name = ?', (name,))
            if c.fetchone():
                print(f"   ⚠️  건너뜀: {name} (이미 존재)")
                skipped_count += 1
                continue
            
            # 데이터 삽입
            c.execute(
                """INSERT INTO products 
                   (name, description, price, token_amount, duration_days, type, is_active, vat_included, created_at, updated_at) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, 0, datetime('now', 'localtime'), datetime('now', 'localtime'))""",
                (name, description, price, token_amount, duration_days, product_type, is_active)
            )
            print(f"   ✅ 삽입 완료: {name}")
            inserted_count += 1
        
        conn.commit()
        
        # 결과 확인
        print("\n[3단계] 삽입된 데이터 확인...")
        rows = c.execute(
            "SELECT id, name, price, token_amount, type, is_active FROM products ORDER BY id"
        ).fetchall()
        
        print("\n" + "=" * 60)
        print("📊 삽입된 상품 목록:")
        print("-" * 60)
        for row in rows:
            status = "활성" if row['is_active'] else "비활성"
            print(f"ID: {row['id']:2d} | {row['name']:20s} | {row['price']:8d}원 | {row['token_amount']:6d}토큰 | {row['type']:15s} | {status}")
        print("-" * 60)
        print(f"\n✅ 완료!")
        print(f"   - 새로 삽입: {inserted_count}개")
        print(f"   - 건너뜀: {skipped_count}개")
        print(f"   - 전체 상품: {len(rows)}개")
        print("=" * 60)
        
        conn.close()
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    seed_products()




