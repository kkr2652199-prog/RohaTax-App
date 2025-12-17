import sqlite3
import sys

# 프로젝트 루트 경로 확보
sys.path.append('.')

from core.db import get_conn


def seed_products():
    print("🚀 상품 데이터 주입 시작...")
    try:
        with get_conn() as conn:
            cursor = conn.cursor()

            # 1. 기존 데이터 초기화 (충돌 방지)
            cursor.execute("DELETE FROM products")

            # 2. 데이터 준비 (이벤트 2종 + 유료 3종)
            products = [
                # (name, description, price, token_amount, duration_days, type, is_active)
                # Event 1: Welcome
                ('Welcome Event', '신규 가입 혜택 (50토큰)', 0, 50, 0, 'event', 1),
                # Event 2: Period
                ('Welcome Period Event', '신규 가입 혜택 (3일 무료)', 0, 0, 3, 'event_period', 1),

                # Paid 1: Standard
                ('Standard', '필요할 때만 사용하는 유연한 플랜', 300, 1, 0, 'package', 1),
                # Paid 2: Premium
                ('Premium', '100건 패키지로 한 번에 해결', 15000, 100, 0, 'package', 1),
                # Paid 3: Gold
                ('Gold', '세무사/대리 발급 전문', 100000, 999999, 30, 'subscription', 1),
            ]

            # 3. 데이터 삽입
            cursor.executemany(
                """
                INSERT INTO products 
                (name, description, price, token_amount, duration_days, type, is_active, vat_included, created_at, updated_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """,
                products,
            )

            conn.commit()
            print(f"✅ 총 {len(products)}개의 상품이 성공적으로 등록되었습니다.")

    except Exception as e:
        print(f"❌ 데이터 주입 실패: {e}")


if __name__ == "__main__":
    seed_products()


