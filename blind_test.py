"""
토큰 유효기간 설정 반영 여부 블라인드 테스트
관리자가 변경한 설정값을 시스템이 정확히 읽어오는지 검증
"""
import sqlite3
import os
from datetime import datetime
from core.payment.service import PaymentService
from core.payment.schemas import PaymentStatus

DB_PATH = os.path.join(os.path.dirname(__file__), 'database', 'app.db')

def blind_test():
    """블라인드 테스트: 설정값과 실제 기록된 기간 비교"""
    conn = None
    try:
        print("=" * 60)
        print("🔍 토큰 유효기간 설정 반영 여부 블라인드 테스트")
        print("=" * 60)
        print(f"📁 DB 경로: {DB_PATH}\n")
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Step 1: 설정 확인
        print("Step 1️⃣: products 테이블에서 설정값 조회...")
        product = cursor.execute(
            """
            SELECT id, name, token_validity_days
            FROM products
            WHERE id = 4
            """
        ).fetchone()
        
        if not product:
            print("   ❌ Welcome Event 상품(ID: 4)을 찾을 수 없습니다.")
            return
        
        product_id = product['id']
        product_name = product['name']
        configured_days = product['token_validity_days']
        
        if configured_days is None:
            print("   ⚠️ 유효기간이 설정되지 않았습니다. (NULL)")
            configured_days = 0
        else:
            configured_days = int(configured_days)
        
        print(f"   ✅ 상품 정보:")
        print(f"      - 상품 ID: {product_id}")
        print(f"      - 상품명: {product_name}")
        print(f"      - 현재 DB에 설정된 유효기간: {configured_days}일")
        
        if configured_days <= 0:
            print(f"\n   ⚠️ 유효기간이 0일 이하입니다. 만료일이 기록되지 않을 수 있습니다.")
        
        # Step 2: 구매 실행
        user_id = 2
        print(f"\nStep 2️⃣: PaymentService로 구매 처리 중... (사용자 ID: {user_id})")
        
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
        
        # Step 3: 검증 - 방금 생성된 token_history 조회
        print(f"\nStep 3️⃣: 방금 생성된 토큰 기록 조회 및 검증...")
        
        grant_record = cursor.execute(
            """
            SELECT id, user_id, amount, created_at, expires_at
            FROM token_history
            WHERE user_id = ?
              AND change_type = 'grant'
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
        print(f"      - 만료 일시: {expires_at_str if expires_at_str else 'NULL (무제한)'}")
        
        # 만료일이 없는 경우 처리
        if not expires_at_str:
            if configured_days <= 0:
                print(f"\n   ✅ 예상대로 만료일이 기록되지 않았습니다. (설정값: {configured_days}일)")
                print(f"\n" + "=" * 60)
                print("📊 검증 결과")
                print("=" * 60)
                print(f"시스템이 감지한 설정값: {configured_days}일")
                print(f"실제 기록된 만료 기간: 무제한 (만료일 없음)")
                print(f"✅ 결론: 설정값과 기록된 기간이 일치합니다. (0일 이하 = 무제한)")
                print("=" * 60)
                return
            else:
                print(f"\n   ❌ 설정값이 {configured_days}일인데 만료일이 기록되지 않았습니다.")
                print(f"\n" + "=" * 60)
                print("📊 검증 결과")
                print("=" * 60)
                print(f"시스템이 감지한 설정값: {configured_days}일")
                print(f"실제 기록된 만료 기간: 기록되지 않음")
                print(f"❌ 결론: 설정값과 기록된 기간이 불일치합니다.")
                print("=" * 60)
                return
        
        # 날짜 차이 계산
        try:
            created_at = datetime.strptime(created_at_str, '%Y-%m-%d %H:%M:%S')
            expires_at = datetime.strptime(expires_at_str, '%Y-%m-%d %H:%M:%S')
            
            time_diff = expires_at - created_at
            recorded_days = time_diff.days
            recorded_hours = time_diff.total_seconds() / 3600
            
            print(f"\n   📊 계산 결과:")
            print(f"      - 실제 기록된 만료 기간: {recorded_days}일 ({recorded_hours:.1f}시간)")
            
            # 정확성 검증 (약 1시간 오차 허용)
            expected_hours = configured_days * 24
            if abs(recorded_hours - expected_hours) <= 1:
                match_status = "일치합니다"
                status_icon = "✅"
            else:
                match_status = "불일치합니다"
                status_icon = "❌"
            
            print(f"\n" + "=" * 60)
            print("📊 검증 결과")
            print("=" * 60)
            print(f"시스템이 감지한 설정값: {configured_days}일")
            print(f"실제 기록된 만료 기간: {recorded_days}일 ({recorded_hours:.1f}시간)")
            print(f"{status_icon} 결론: 설정값과 기록된 기간이 {match_status}")
            print("=" * 60)
            
        except Exception as e:
            print(f"   ❌ 날짜 파싱 오류: {str(e)}")
            print(f"\n" + "=" * 60)
            print("📊 검증 결과")
            print("=" * 60)
            print(f"시스템이 감지한 설정값: {configured_days}일")
            print(f"실제 기록된 만료 기간: 계산 불가 (오류 발생)")
            print(f"❌ 결론: 설정값과 기록된 기간을 비교할 수 없습니다.")
            print("=" * 60)
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    blind_test()

