#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
homepage1 통계/결재/세무/활동 데이터 초기화 스크립트

초기화 대상:
- 유저 활동 통합관제실 통계: activity_logs, usage_logs, conversion_logs, token_history (use 타입만)
- 결재관리: payment_history
- 세무리포트: orders
- 활동: activity_logs

보존 대상:
- users (유저 정보)
- product_packages (상품 정보)
- subscription_plans (구독 플랜)
- gold_customers (골드 고객)
- policies (지원사업)
- 기타 설정 및 메타데이터
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
    backup_path = os.path.join(backup_dir, f'app_before_stats_reset_{timestamp}.db')
    
    import shutil
    shutil.copy2(DB_PATH, backup_path)
    print(f"[OK] 데이터베이스 백업 완료: {backup_path}")
    return backup_path


def get_user_count(conn):
    """유저 수 확인"""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    return cursor.fetchone()[0]


def reset_stats_data(conn):
    """통합관제실 통계 데이터 초기화"""
    cursor = conn.cursor()
    
    stats_tables = [
        ('activity_logs', '활동 로그'),
        ('usage_logs', '사용 로그'),
        ('conversion_logs', '변환 로그'),
    ]
    
    deleted_counts = {}
    
    print("\n=== 통합관제실 통계 데이터 삭제 시작 ===")
    for table, description in stats_tables:
        try:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if cursor.fetchone():
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count_before = cursor.fetchone()[0]
                
                cursor.execute(f"DELETE FROM {table}")
                deleted_counts[table] = count_before
                print(f"[OK] {description} ({table}): {count_before}개 삭제")
            else:
                print(f"[SKIP] {description} ({table}): 테이블 없음 (건너뜀)")
                deleted_counts[table] = 0
        except Exception as e:
            print(f"[ERROR] {description} ({table}) 삭제 실패: {e}")
            deleted_counts[table] = 0
    
    # token_history는 use 타입만 삭제
    print("\n=== token_history (use 타입) 처리 ===")
    try:
        cursor.execute("SELECT COUNT(*) FROM token_history WHERE change_type = 'use'")
        token_use_count = cursor.fetchone()[0]
        
        if token_use_count > 0:
            cursor.execute("DELETE FROM token_history WHERE change_type = 'use'")
            deleted_counts['token_history_use'] = token_use_count
            print(f"[OK] token_history (use 타입): {token_use_count}개 삭제")
        else:
            print("[SKIP] token_history (use 타입): 데이터 없음")
            deleted_counts['token_history_use'] = 0
    except Exception as e:
        print(f"[ERROR] token_history 처리 실패: {e}")
        deleted_counts['token_history_use'] = 0
    
    conn.commit()
    return deleted_counts


def reset_payment_data(conn):
    """결재관리 데이터 초기화"""
    cursor = conn.cursor()
    
    print("\n=== 결재관리 데이터 삭제 시작 ===")
    deleted_counts = {}
    
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='payment_history'")
        if cursor.fetchone():
            cursor.execute("SELECT COUNT(*) FROM payment_history")
            count_before = cursor.fetchone()[0]
            
            cursor.execute("DELETE FROM payment_history")
            deleted_counts['payment_history'] = count_before
            print(f"[OK] payment_history (결제 내역): {count_before}개 삭제")
        else:
            print("[SKIP] payment_history: 테이블 없음 (건너뜀)")
            deleted_counts['payment_history'] = 0
    except Exception as e:
        print(f"[ERROR] payment_history 삭제 실패: {e}")
        deleted_counts['payment_history'] = 0
    
    conn.commit()
    return deleted_counts


def reset_tax_data(conn):
    """세무리포트 데이터 초기화"""
    cursor = conn.cursor()
    
    print("\n=== 세무리포트 데이터 삭제 시작 ===")
    deleted_counts = {}
    
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orders'")
        if cursor.fetchone():
            cursor.execute("SELECT COUNT(*) FROM orders")
            count_before = cursor.fetchone()[0]
            
            cursor.execute("DELETE FROM orders")
            deleted_counts['orders'] = count_before
            print(f"[OK] orders (주문 내역): {count_before}개 삭제")
        else:
            print("[SKIP] orders: 테이블 없음 (건너뜀)")
            deleted_counts['orders'] = 0
    except Exception as e:
        print(f"[ERROR] orders 삭제 실패: {e}")
        deleted_counts['orders'] = 0
    
    conn.commit()
    return deleted_counts


def verify_preserved_data(conn):
    """보존된 데이터 확인"""
    cursor = conn.cursor()
    
    print("\n=== 보존된 데이터 확인 ===")
    
    # 유저 확인
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    print(f"[OK] users: {user_count}명 보존")
    
    # 상품 확인
    try:
        cursor.execute("SELECT COUNT(*) FROM product_packages")
        product_count = cursor.fetchone()[0]
        print(f"[OK] product_packages: {product_count}개 보존")
    except:
        print("[SKIP] product_packages: 테이블 없음")
    
    # 구독 플랜 확인
    try:
        cursor.execute("SELECT COUNT(*) FROM subscription_plans")
        plan_count = cursor.fetchone()[0]
        print(f"[OK] subscription_plans: {plan_count}개 보존")
    except:
        print("[SKIP] subscription_plans: 테이블 없음")
    
    # 골드 고객 확인
    try:
        cursor.execute("SELECT COUNT(*) FROM gold_customers")
        gold_count = cursor.fetchone()[0]
        print(f"[OK] gold_customers: {gold_count}개 보존")
    except:
        print("[SKIP] gold_customers: 테이블 없음")
    
    # 지원사업 확인
    try:
        cursor.execute("SELECT COUNT(*) FROM policies")
        policy_count = cursor.fetchone()[0]
        print(f"[OK] policies: {policy_count}개 보존")
    except:
        print("[SKIP] policies: 테이블 없음")


def main():
    """메인 함수"""
    print("=" * 60)
    print("homepage1 통계/결재/세무/활동 데이터 초기화 스크립트")
    print("=" * 60)
    
    # 데이터베이스 파일 확인
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] 데이터베이스 파일이 없습니다: {DB_PATH}")
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
            print("[WARNING] 유저가 없습니다. 계속 진행하시겠습니까?")
            response = input("계속하려면 'yes'를 입력하세요: ")
            if response.lower() != 'yes':
                print("작업 취소됨")
                return
        
        # 통계 데이터 삭제
        print("\n=== 2단계: 통합관제실 통계 데이터 삭제 ===")
        stats_deleted = reset_stats_data(conn)
        
        # 결재관리 데이터 삭제
        print("\n=== 3단계: 결재관리 데이터 삭제 ===")
        payment_deleted = reset_payment_data(conn)
        
        # 세무리포트 데이터 삭제
        print("\n=== 4단계: 세무리포트 데이터 삭제 ===")
        tax_deleted = reset_tax_data(conn)
        
        # 삭제 요약
        print("\n" + "=" * 60)
        print("=== 삭제 요약 ===")
        print("=" * 60)
        
        all_deleted = {**stats_deleted, **payment_deleted, **tax_deleted}
        total_deleted = 0
        
        print("\n[통합관제실 통계]")
        for table in ['activity_logs', 'usage_logs', 'conversion_logs', 'token_history_use']:
            if table in all_deleted and all_deleted[table] > 0:
                print(f"  - {table}: {all_deleted[table]}개 삭제")
                total_deleted += all_deleted[table]
        
        print("\n[결재관리]")
        if 'payment_history' in all_deleted and all_deleted['payment_history'] > 0:
            print(f"  - payment_history: {all_deleted['payment_history']}개 삭제")
            total_deleted += all_deleted['payment_history']
        
        print("\n[세무리포트]")
        if 'orders' in all_deleted and all_deleted['orders'] > 0:
            print(f"  - orders: {all_deleted['orders']}개 삭제")
            total_deleted += all_deleted['orders']
        
        if total_deleted == 0:
            print("\n  삭제된 데이터 없음")
        else:
            print(f"\n총 {total_deleted}개 레코드 삭제 완료")
        
        # 보존된 데이터 확인
        verify_preserved_data(conn)
        
        print("\n" + "=" * 60)
        print("[OK] 통계/결재/세무/활동 데이터 초기화 완료!")
        print("=" * 60)
        print(f"\n백업 파일: {backup_path}")
        print("\n보존된 데이터:")
        print("  - users (유저 정보)")
        print("  - product_packages (상품 정보)")
        print("  - subscription_plans (구독 플랜)")
        print("  - gold_customers (골드 고객)")
        print("  - policies (지원사업)")
        print("\n삭제된 데이터:")
        print("  - activity_logs (활동 로그)")
        print("  - usage_logs (사용 로그)")
        print("  - conversion_logs (변환 로그)")
        print("  - token_history (use 타입만)")
        print("  - payment_history (결제 내역)")
        print("  - orders (주문 내역)")
        
    except Exception as e:
        print(f"\n[ERROR] 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        conn.close()


if __name__ == '__main__':
    main()

