"""
토큰 만료일 계산 로직 정확성 검증
Welcome Event 구매 후 만료일 확인
"""
import sqlite3
import os
from datetime import datetime
from core.payment.service import PaymentService
from core.payment.schemas import PaymentStatus

DB_PATH = os.path.join(os.path.dirname(__file__), 'database', 'app.db')

def buy_and_check():
    """Welcome Event 구매 후 만료일 확인"""
    conn = None
    try:
        print("=" * 60)
        print("🧪 토큰 만료일 계산 로직 검증")
        print("=" * 60)
        print(f"📁 DB 경로: {DB_PATH}\n")
        
        # 1. Welcome Event 상품 ID 찾기
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print("1️⃣ Welcome Event 상품 정보 조회...")
        product = cursor.execute(
            """
            SELECT id, name, token_amount, token_validity_days
            FROM products
            WHERE name LIKE '%Welcome%Event%' AND type = 'event'
            LIMIT 1
            """
        ).fetchone()
        
        if not product:
            print("   ❌ Welcome Event 상품을 찾을 수 없습니다.")
            return
        
        product_id = product['id']
        product_name = product['name']
        token_validity_days = product['token_validity_days'] if 'token_validity_days' in product.keys() else None
        
        print(f"   ✅ 상품 발견:")
        print(f"      - 상품 ID: {product_id}")
        print(f"      - 상품명: {product_name}")
        print(f"      - 설정된 유효기간: {token_validity_days}일")
        
        if not token_validity_days or token_validity_days <= 0:
            print(f"   ⚠️ 유효기간이 설정되지 않았습니다. 관리자 페이지에서 설정해주세요.")
            return
        
        # 2. PaymentService로 구매 처리
        user_id = 2
        print(f"\n2️⃣ PaymentService로 구매 처리 중... (사용자 ID: {user_id})")
        
        payment_service = PaymentService()
        payment_result = payment_service.create_payment(
            user_id=user_id,
            product_id=product_id,
            quantity=1,
            admin_user_id=1,
            status=PaymentStatus.COMPLETED
        )
        
        print(f"   ✅ 구매 완료")
        print(f"      - 결제 ID: {payment_result.id}")
        print(f"      - 주문번호: {payment_result.order_id}")
        
        # 3. 방금 지급된 토큰 기록 조회
        print(f"\n3️⃣ 방금 지급된 토큰 기록 조회...")
        
        grant_record = cursor.execute(
            """
            SELECT id, user_id, amount, created_at, expires_at
            FROM token_history
            WHERE user_id = ?
              AND change_type = 'grant'
              AND expires_at IS NOT NULL
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (user_id,)
        ).fetchone()
        
        if not grant_record:
            print("   ❌ 토큰 지급 기록을 찾을 수 없습니다.")
            return
        
        record_id = grant_record['id']
        created_at_str = grant_record['created_at']
        expires_at_str = grant_record['expires_at']
        amount = grant_record['amount']
        
        print(f"   ✅ 기록 발견:")
        print(f"      - 기록 ID: {record_id}")
        print(f"      - 지급량: {amount}")
        print(f"      - 지급 일시: {created_at_str}")
        print(f"      - 만료 일시: {expires_at_str}")
        
        # 4. 날짜 차이 계산
        print(f"\n4️⃣ 날짜 차이 계산...")
        
        try:
            created_at = datetime.strptime(created_at_str, '%Y-%m-%d %H:%M:%S')
            expires_at = datetime.strptime(expires_at_str, '%Y-%m-%d %H:%M:%S')
            
            time_diff = expires_at - created_at
            days_diff = time_diff.days
            hours_diff = time_diff.total_seconds() / 3600
            
            print(f"   - 계산된 기간: {days_diff}일 ({hours_diff:.1f}시간)")
            print(f"   - 설정된 기간: {token_validity_days}일")
            
            # 정확성 검증 (약 1시간 오차 허용)
            expected_hours = token_validity_days * 24
            if abs(hours_diff - expected_hours) <= 1:
                match_status = "일치함"
                status_icon = "✅"
            else:
                match_status = "불일치함"
                status_icon = "❌"
            
            print(f"\n" + "=" * 60)
            print("📊 검증 결과")
            print("=" * 60)
            print(f"지급 일시: {created_at_str}")
            print(f"만료 일시: {expires_at_str}")
            print(f"계산된 기간: {days_diff}일 ({hours_diff:.1f}시간)")
            print(f"{status_icon} Commander의 설정({token_validity_days}일)과 {match_status}")
            print("=" * 60)
            
        except Exception as e:
            print(f"   ❌ 날짜 파싱 오류: {str(e)}")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    buy_and_check()

