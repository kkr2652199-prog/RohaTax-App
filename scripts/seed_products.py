"""
상품 패키지 초기 데이터 삽입 스크립트
3가지 고정 요금제: Standard, Premium, Gold
"""

import sqlite3
import os
import sys

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.db import get_conn_optimized

def seed_products():
    """상품 패키지 초기 데이터 삽입"""
    print("=" * 50)
    print("상품 패키지 초기 데이터 삽입 시작")
    print("=" * 50)
    
    try:
        with get_conn_optimized() as conn:
            conn.row_factory = sqlite3.Row
            
            # 기존 데이터 삭제
            print("\n[1단계] 기존 상품 데이터 삭제 중...")
            conn.execute("DELETE FROM product_packages")
            conn.commit()
            print("기존 데이터 삭제 완료")
            
            # 3개 고정 요금제 삽입
            print("\n[2단계] 고정 요금제 데이터 삽입 중...")
            
            products = [
                {
                    'id': 1,
                    'name': 'Standard',
                    'description': '기준 단가 (토큰 1개당 가격)',
                    'price': 500,
                    'token_amount': 1,
                    'is_active': True
                },
                {
                    'id': 2,
                    'name': 'Premium',
                    'description': '할인 패키지 (100토큰)',
                    'price': 25000,
                    'token_amount': 100,
                    'is_active': True
                },
                {
                    'id': 3,
                    'name': 'Gold',
                    'description': '무제한권 (월 이용료)',
                    'price': 50000,
                    'token_amount': -1,  # 무제한
                    'is_active': True
                }
            ]
            
            for product in products:
                conn.execute(
                    """
                    INSERT INTO product_packages (id, name, description, price, token_amount, is_active, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime'), strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime'))
                    """,
                    (
                        product['id'],
                        product['name'],
                        product['description'],
                        product['price'],
                        product['token_amount'],
                        product['is_active']
                    )
                )
                print(f"  - {product['name']} (ID: {product['id']}) 삽입 완료")
            
            conn.commit()
            
            # 삽입된 데이터 확인
            print("\n[3단계] 삽입된 데이터 확인...")
            rows = conn.execute(
                "SELECT id, name, price, token_amount, is_active FROM product_packages ORDER BY id"
            ).fetchall()
            
            print("\n삽입된 상품 목록:")
            print("-" * 50)
            for row in rows:
                token_info = "무제한" if row['token_amount'] == -1 else f"{row['token_amount']}토큰"
                status = "판매 중" if row['is_active'] else "판매 중지"
                print(f"ID: {row['id']:2d} | {row['name']:10s} | {row['price']:8d}원 | {token_info:8s} | {status}")
            print("-" * 50)
            
            print(f"\n총 {len(rows)}개 상품 삽입 완료!")
            print("=" * 50)
            
    except Exception as e:
        print(f"\n오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    seed_products()




