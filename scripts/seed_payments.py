"""
결제 관리 시스템 더미 데이터 생성 스크립트
최근 7일간 20건의 결제 내역을 생성하여 UI 검증용 데이터 주입
"""

import sqlite3
import os
import random
from datetime import datetime, timedelta
from typing import List, Tuple

# 프로젝트 루트 경로
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(PROJECT_ROOT, 'database', 'app.db')


def get_available_user_ids() -> List[int]:
    """DB에서 사용 가능한 유저 ID 목록 조회"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT id FROM users WHERE COALESCE(is_deleted, 0) = 0 ORDER BY id"
        )
        user_ids = [row['id'] for row in cursor.fetchall()]
        conn.close()
        
        if not user_ids:
            # 유저가 없으면 1번 사용
            return [1]
        
        return user_ids
    except Exception as e:
        print(f"[WARNING] 유저 ID 조회 실패: {str(e)}")
        return [1]


def generate_order_id(date: datetime, sequence: int) -> str:
    """주문번호 생성: ORD-YYYYMMDD-XXXX 형식"""
    date_str = date.strftime('%Y%m%d')
    sequence_str = str(sequence).zfill(4)
    return f"ORD-{date_str}-{sequence_str}"


def generate_payment_data(user_ids: List[int]) -> List[Tuple]:
    """결제 더미 데이터 생성"""
    payments = []
    
    # 상태 분포: completed(15), pending(3), failed(1), cancelled(1)
    status_distribution = (
        ['completed'] * 15 +
        ['pending'] * 3 +
        ['failed'] * 1 +
        ['cancelled'] * 1
    )
    random.shuffle(status_distribution)
    
    # 최근 7일간 날짜 생성
    today = datetime.now()
    dates = [today - timedelta(days=i) for i in range(7)]
    
    # 날짜별로 분산 배치 (20건을 7일간 분산)
    date_index = 0
    sequence_counter = {}  # 날짜별 시퀀스 카운터
    
    for i in range(20):
        # 날짜 선택 (최근 날짜에 더 많이 배치)
        if i < 10:
            # 최근 3일
            date = random.choice(dates[:3])
        elif i < 17:
            # 중간 2일
            date = random.choice(dates[3:5])
        else:
            # 나머지 2일
            date = random.choice(dates[5:])
        
        # 시간 랜덤 생성 (9시 ~ 18시)
        hour = random.randint(9, 18)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        payment_datetime = date.replace(hour=hour, minute=minute, second=second)
        
        # 시퀀스 카운터 초기화
        date_key = date.strftime('%Y%m%d')
        if date_key not in sequence_counter:
            sequence_counter[date_key] = 0
        sequence_counter[date_key] += 1
        
        # 주문번호 생성
        order_id = generate_order_id(date, sequence_counter[date_key])
        
        # 상태 선택
        status = status_distribution[i]
        
        # 금액 생성 (5,000원 ~ 50,000원, 5,000원 단위)
        amount = random.randrange(5000, 50001, 5000)
        
        # 토큰 수량 계산 (금액의 1/1000 또는 랜덤)
        # 예: 10,000원 = 10토큰 또는 10,000원 = 20토큰 (2배율)
        token_multiplier = random.choice([1, 1.5, 2])
        token_amount = int(amount / 1000 * token_multiplier)
        
        # 유저 ID 선택
        user_id = random.choice(user_ids)
        
        # PG사 선택 (랜덤)
        pg_providers = ['iamport', 'toss', 'kakaopay', 'nicepay', None]
        pg_provider = random.choice(pg_providers)
        
        # created_at, updated_at 포맷팅
        created_at = payment_datetime.strftime('%Y-%m-%d %H:%M:%S')
        updated_at = created_at  # 초기에는 동일
        
        payments.append((
            user_id,
            order_id,
            amount,
            token_amount,
            status,
            pg_provider,
            created_at,
            updated_at
        ))
    
    return payments


def insert_payments(payments: List[Tuple]) -> int:
    """결제 데이터를 DB에 삽입"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 기존 데이터 확인
        cursor.execute("SELECT COUNT(*) FROM payment_history")
        before_count = cursor.fetchone()[0]
        
        # 데이터 삽입
        cursor.executemany(
            """
            INSERT INTO payment_history 
            (user_id, order_id, amount, token_amount, status, pg_provider, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            payments
        )
        
        conn.commit()
        
        # 삽입 후 개수 확인
        cursor.execute("SELECT COUNT(*) FROM payment_history")
        after_count = cursor.fetchone()[0]
        
        inserted_count = after_count - before_count
        conn.close()
        
        return inserted_count
        
    except sqlite3.IntegrityError as e:
        print(f"[ERROR] 데이터 삽입 실패 (중복 주문번호 가능): {str(e)}")
        return 0
    except Exception as e:
        print(f"[ERROR] 데이터 삽입 중 오류: {str(e)}")
        return 0


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("결제 관리 시스템 더미 데이터 생성 스크립트")
    print("=" * 60)
    
    # DB 파일 확인
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] 데이터베이스 파일을 찾을 수 없습니다: {DB_PATH}")
        return
    
    print(f"[INFO] 데이터베이스 경로: {DB_PATH}")
    
    # 유저 ID 조회
    print("[INFO] 사용 가능한 유저 ID 조회 중...")
    user_ids = get_available_user_ids()
    print(f"[INFO] 사용 가능한 유저 ID: {user_ids}")
    
    # 더미 데이터 생성
    print("[INFO] 더미 데이터 생성 중...")
    payments = generate_payment_data(user_ids)
    
    print(f"[INFO] 생성된 결제 데이터: {len(payments)}건")
    print("\n생성된 데이터 샘플 (처음 3건):")
    for i, payment in enumerate(payments[:3], 1):
        print(f"  {i}. 주문번호: {payment[1]}, 금액: {payment[2]:,}원, 상태: {payment[4]}, 일시: {payment[6]}")
    
    # 상태별 통계
    status_count = {}
    for payment in payments:
        status = payment[4]
        status_count[status] = status_count.get(status, 0) + 1
    
    print("\n상태별 분포:")
    for status, count in status_count.items():
        print(f"  - {status}: {count}건")
    
    # DB에 삽입
    print("\n[INFO] 데이터베이스에 삽입 중...")
    inserted_count = insert_payments(payments)
    
    if inserted_count > 0:
        print(f"[SUCCESS] 더미 데이터 {inserted_count}건 삽입 완료!")
        print("\n이제 관리자 대시보드의 '결제 관리' 탭에서 데이터를 확인할 수 있습니다.")
    else:
        print("[WARNING] 데이터 삽입 실패 또는 중복 데이터로 인해 삽입되지 않았습니다.")
    
    print("=" * 60)


if __name__ == '__main__':
    main()

