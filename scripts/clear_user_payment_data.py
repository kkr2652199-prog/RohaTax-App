#!/usr/bin/env python3
"""
사용자 데이터 및 결제 데이터만 삭제하는 스크립트
시스템 설정, 제품 정보, 정책 등은 유지합니다.
"""

import os
import sys
import sqlite3
from datetime import datetime

# Windows 인코딩 설정
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from core.db import DB_PATH

def clear_user_payment_data():
    """사용자 데이터 및 결제 데이터만 삭제"""
    
    print("=" * 60)
    print("사용자 데이터 및 결제 데이터 삭제 스크립트")
    print("=" * 60)
    
    db_path = DB_PATH
    
    if not os.path.exists(db_path):
        print(f"\n[ERROR] 데이터베이스 파일이 없습니다: {db_path}")
        return False
    
    print(f"\n[1단계] 데이터베이스 연결 중...")
    print(f"  데이터베이스 경로: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path, timeout=10.0)
        cursor = conn.cursor()
        
        print(f"[OK] 데이터베이스 연결 성공")
        
        # 외래 키 제약 조건 비활성화
        print(f"\n[2단계] 외래 키 제약 조건 비활성화...")
        cursor.execute("PRAGMA foreign_keys = OFF")
        print(f"[OK] 외래 키 제약 조건 비활성화 완료")
        
        # 삭제할 테이블 목록 (사용자 데이터 및 결제 관련)
        tables_to_clear = [
            # 사용자 데이터
            'users',
            'usage_logs',
            'validation_logs',
            'token_history',
            'token_usage',
            'conversion_logs',
            'email_verification_logs',
            'email_verification_attempts',
            'password_reset_tokens',
            'sms_verification_codes',
            'notifications',
            'activity_logs',
            
            # 결제 및 구독 데이터
            'user_subscriptions',
            'orders',
            'payment_history',
            'gold_customers',
        ]
        
        # 유지할 테이블 (시스템 설정, 제품 정보 등)
        tables_to_keep = [
            'settings',
            'system_settings',
            'products',
            'product_packages',
            'subscription_plans',  # 구독 플랜 정의는 유지
            'policies',
        ]
        
        print(f"\n[3단계] 삭제할 테이블 확인 중...")
        deleted_count = 0
        
        for table in tables_to_clear:
            try:
                # 테이블 존재 확인
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                if cursor.fetchone():
                    # 데이터 개수 확인
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    
                    if count > 0:
                        # 데이터 삭제
                        cursor.execute(f"DELETE FROM {table}")
                        print(f"  [OK] {table}: {count}개 레코드 삭제")
                        deleted_count += count
                    else:
                        print(f"  [INFO] {table}: 데이터 없음 (건너뜀)")
                else:
                    print(f"  [INFO] {table}: 테이블 없음 (건너뜀)")
            except Exception as e:
                print(f"  [WARNING] {table} 삭제 실패: {e}")
        
        # 유지할 테이블 확인
        print(f"\n[4단계] 유지할 테이블 확인 중...")
        for table in tables_to_keep:
            try:
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                if cursor.fetchone():
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"  [OK] {table}: {count}개 레코드 유지")
            except Exception as e:
                print(f"  [INFO] {table}: 확인 불가 ({e})")
        
        # 변경사항 커밋
        conn.commit()
        print(f"\n[OK] 총 {deleted_count}개 레코드 삭제 완료")
        
        # 외래 키 제약 조건 다시 활성화
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # 연결 종료
        conn.close()
        
        print("\n" + "=" * 60)
        print("[OK] 사용자 데이터 및 결제 데이터 삭제가 완료되었습니다!")
        print("=" * 60)
        print("\n[유지된 데이터]")
        print("  - 시스템 설정 (settings, system_settings)")
        print("  - 제품 정보 (products, product_packages)")
        print("  - 구독 플랜 정의 (subscription_plans)")
        print("  - 정책 (policies)")
        
        return True
        
    except sqlite3.OperationalError as e:
        if "database is locked" in str(e).lower():
            print(f"\n[ERROR] 데이터베이스가 잠겨 있습니다.")
            print(f"  다른 프로세스(Flask 앱 등)가 데이터베이스를 사용 중입니다.")
            print(f"  모든 Python 프로세스를 종료한 후 다시 시도하세요.")
        else:
            print(f"\n[ERROR] 데이터베이스 작업 실패: {e}")
        return False
    except Exception as e:
        print(f"\n[ERROR] 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("\n[경고] 이 작업은 다음 데이터를 삭제합니다:")
    print("  - 모든 사용자 계정 및 정보")
    print("  - 모든 결제 내역 및 주문 정보")
    print("  - 모든 사용자 로그 및 활동 기록")
    print("  - 모든 구독 정보")
    print("\n[유지되는 데이터]")
    print("  - 시스템 설정")
    print("  - 제품 정보")
    print("  - 구독 플랜 정의")
    print("  - 정책")
    print()
    
    success = clear_user_payment_data()
    sys.exit(0 if success else 1)


