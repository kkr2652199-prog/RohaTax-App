#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
homepage1 데이터베이스 활동 내역만 초기화 스크립트

주의사항:
- 유저 정보는 보존 (users 테이블)
- 결제 내역은 보존 (payment_history, orders)
- 상품 정보는 보존 (products, product_packages, subscription_plans)
- 활동 내역만 삭제 (usage_logs, validation_logs, conversion_logs, activity_logs, token_history)
"""

import sqlite3
import os
from datetime import datetime

# 데이터베이스 경로
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'app.db')


def get_conn():
    """데이터베이스 연결"""
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def backup_database():
    """데이터베이스 백업"""
    backup_dir = os.path.join(os.path.dirname(DB_PATH), 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(backup_dir, f'app_before_activity_reset_{timestamp}.db')
    
    import shutil
    shutil.copy2(DB_PATH, backup_path)
    print(f"✅ 데이터베이스 백업 완료: {backup_path}")
    return backup_path


def get_user_count(conn):
    """유저 수 확인"""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    return cursor.fetchone()[0]


def reset_activity_logs(conn):
    """활동 내역만 삭제"""
    cursor = conn.cursor()
    
    # 삭제할 테이블 목록 (활동 내역만)
    activity_tables = [
        'usage_logs',           # 사용 로그
        'validation_logs',      # 검증 로그
        'conversion_logs',      # 변환 로그
        'activity_logs',        # 활동 로그 (마이그레이션으로 생성됨)
    ]
    
    deleted_counts = {}
    
    print("\n=== 활동 내역 삭제 시작 ===")
    for table in activity_tables:
        try:
            # 테이블 존재 확인
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if cursor.fetchone():
                # 삭제 전 개수 확인
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count_before = cursor.fetchone()[0]
                
                # 삭제 실행
                cursor.execute(f"DELETE FROM {table}")
                deleted_counts[table] = count_before
                print(f"✅ {table}: {count_before}개 삭제")
            else:
                print(f"⏭️  {table}: 테이블 없음 (건너뜀)")
                deleted_counts[table] = 0
        except Exception as e:
            print(f"❌ {table} 삭제 실패: {e}")
            deleted_counts[table] = 0
    
    # token_history는 특별 처리 (토큰 잔액 계산에 사용될 수 있으므로 확인 필요)
    print("\n=== token_history 처리 ===")
    try:
        cursor.execute("SELECT COUNT(*) FROM token_history")
        token_history_count = cursor.fetchone()[0]
        
        if token_history_count > 0:
            print(f"⚠️  token_history에 {token_history_count}개 레코드가 있습니다.")
            print("   토큰 잔액 계산에 사용될 수 있으므로, 사용(use) 타입만 삭제합니다.")
            
            # 'use' 타입만 삭제 (토큰 사용 내역)
            cursor.execute("DELETE FROM token_history WHERE change_type = 'use'")
            deleted_use = cursor.rowcount
            print(f"✅ token_history (use 타입): {deleted_use}개 삭제")
            deleted_counts['token_history_use'] = deleted_use
        else:
            print("⏭️  token_history: 데이터 없음")
            deleted_counts['token_history_use'] = 0
    except Exception as e:
        print(f"❌ token_history 처리 실패: {e}")
        deleted_counts['token_history_use'] = 0
    
    conn.commit()
    
    return deleted_counts


def verify_preserved_data(conn):
    """보존된 데이터 확인"""
    cursor = conn.cursor()
    
    print("\n=== 보존된 데이터 확인 ===")
    
    # 유저 확인
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    print(f"✅ users: {user_count}명 보존")
    
    # 결제 내역 확인
    try:
        cursor.execute("SELECT COUNT(*) FROM payment_history")
        payment_count = cursor.fetchone()[0]
        print(f"✅ payment_history: {payment_count}개 보존")
    except:
        print("⏭️  payment_history: 테이블 없음")
    
    # 주문 확인
    try:
        cursor.execute("SELECT COUNT(*) FROM orders")
        order_count = cursor.fetchone()[0]
        print(f"✅ orders: {order_count}개 보존")
    except:
        print("⏭️  orders: 테이블 없음")
    
    # 상품 확인
    try:
        cursor.execute("SELECT COUNT(*) FROM product_packages")
        product_count = cursor.fetchone()[0]
        print(f"✅ product_packages: {product_count}개 보존")
    except:
        print("⏭️  product_packages: 테이블 없음")
    
    # 구독 플랜 확인
    try:
        cursor.execute("SELECT COUNT(*) FROM subscription_plans")
        plan_count = cursor.fetchone()[0]
        print(f"✅ subscription_plans: {plan_count}개 보존")
    except:
        print("⏭️  subscription_plans: 테이블 없음")


def main():
    """메인 함수"""
    print("=" * 60)
    print("homepage1 활동 내역 초기화 스크립트")
    print("=" * 60)
    
    # 데이터베이스 파일 확인
    if not os.path.exists(DB_PATH):
        print(f"❌ 데이터베이스 파일이 없습니다: {DB_PATH}")
        return
    
    # 백업 생성
    print("\n=== 1단계: 데이터베이스 백업 ===")
    backup_path = backup_database()
    
    # 데이터베이스 연결
    conn = get_conn()
    
    try:
        # 유저 수 확인
        user_count = get_user_count(conn)
        print(f"\n현재 유저 수: {user_count}명")
        
        if user_count == 0:
            print("⚠️  유저가 없습니다. 계속 진행하시겠습니까?")
            response = input("계속하려면 'yes'를 입력하세요: ")
            if response.lower() != 'yes':
                print("작업 취소됨")
                return
        
        # 활동 내역 삭제
        print("\n=== 2단계: 활동 내역 삭제 ===")
        deleted_counts = reset_activity_logs(conn)
        
        # 삭제 요약
        print("\n=== 삭제 요약 ===")
        total_deleted = 0
        for table, count in deleted_counts.items():
            if count > 0:
                print(f"  {table}: {count}개 삭제")
                total_deleted += count
        
        if total_deleted == 0:
            print("  삭제된 데이터 없음")
        else:
            print(f"\n총 {total_deleted}개 레코드 삭제 완료")
        
        # 보존된 데이터 확인
        verify_preserved_data(conn)
        
        print("\n" + "=" * 60)
        print("✅ 활동 내역 초기화 완료!")
        print("=" * 60)
        print(f"\n백업 파일: {backup_path}")
        print("\n보존된 데이터:")
        print("  - users (유저 정보)")
        print("  - payment_history (결제 내역)")
        print("  - orders (주문)")
        print("  - product_packages (상품)")
        print("  - subscription_plans (구독 플랜)")
        print("\n삭제된 데이터:")
        print("  - usage_logs (사용 로그)")
        print("  - validation_logs (검증 로그)")
        print("  - conversion_logs (변환 로그)")
        print("  - activity_logs (활동 로그)")
        print("  - token_history (use 타입만)")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        conn.close()


if __name__ == '__main__':
    main()

