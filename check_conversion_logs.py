"""
변환 로그 확인 스크립트
최근 변환 기록과 토큰 차감 내역을 확인합니다.
"""

import sqlite3
import json
from datetime import datetime
from core.db import get_conn

def check_recent_conversions():
    """최근 변환 로그 확인"""
    print("=" * 80)
    print("최근 변환 로그 확인")
    print("=" * 80)
    
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        
        # 최근 변환 로그 (최근 5개)
        conversions = conn.execute(
            """
            SELECT 
                cl.id,
                cl.user_id,
                u.username,
                cl.original_filename,
                cl.converted_filename,
                cl.status,
                cl.conversion_time,
                cl.file_size,
                cl.error_message,
                cl.created_at
            FROM conversion_logs cl
            JOIN users u ON cl.user_id = u.id
            ORDER BY cl.created_at DESC
            LIMIT 5
            """
        ).fetchall()
        
        if not conversions:
            print("❌ 변환 로그가 없습니다.")
            return
        
        for i, conv in enumerate(conversions, 1):
            print(f"\n[{i}] 변환 ID: {conv['id']}")
            print(f"    사용자: {conv['username']} (ID: {conv['user_id']})")
            print(f"    원본 파일: {conv['original_filename']}")
            print(f"    변환 파일: {conv['converted_filename']}")
            print(f"    상태: {conv['status']}")
            print(f"    변환 시간: {conv['conversion_time']}초")
            print(f"    파일 크기: {conv['file_size']} bytes")
            print(f"    생성 시간: {conv['created_at']}")
            if conv['error_message']:
                print(f"    오류 메시지: {conv['error_message']}")

def check_recent_activity_logs():
    """최근 활동 로그 확인 (토큰 관련)"""
    print("\n" + "=" * 80)
    print("최근 활동 로그 확인 (토큰 관련)")
    print("=" * 80)
    
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        
        # 최근 활동 로그 (최근 10개)
        activities = conn.execute(
            """
            SELECT 
                al.id,
                al.user_id,
                u.username,
                al.activity_type,
                al.details,
                al.token_change,
                al.token_balance_before,
                al.token_balance_after,
                al.timestamp
            FROM activity_logs al
            JOIN users u ON al.user_id = u.id
            WHERE al.activity_type IN ('FILE_CONVERT', 'TOKEN_EXPIRED', 'TOKEN_GRANT_BY_ADMIN', 'TOKEN_PURCHASE')
            ORDER BY al.timestamp DESC
            LIMIT 10
            """
        ).fetchall()
        
        if not activities:
            print("❌ 활동 로그가 없습니다.")
            return
        
        for i, act in enumerate(activities, 1):
            print(f"\n[{i}] 활동 ID: {act['id']}")
            print(f"    사용자: {act['username']} (ID: {act['user_id']})")
            print(f"    활동 유형: {act['activity_type']}")
            
            # details 파싱
            try:
                details = json.loads(act['details']) if act['details'] else {}
                if details:
                    print(f"    상세 정보:")
                    for key, value in details.items():
                        if key in ['total_recipients', 'template_count', 'actual_templates', 'tokens_deducted']:
                            print(f"      - {key}: {value}")
            except:
                print(f"    상세 정보: {act['details']}")
            
            print(f"    토큰 변경: {act['token_change']}")
            print(f"    토큰 잔액 (이전): {act['token_balance_before']}")
            print(f"    토큰 잔액 (이후): {act['token_balance_after']}")
            print(f"    시간: {act['timestamp']}")

def check_user_token_status():
    """사용자 토큰 상태 확인"""
    print("\n" + "=" * 80)
    print("최근 변환한 사용자 토큰 상태")
    print("=" * 80)
    
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        
        # 최근 변환한 사용자들
        recent_users = conn.execute(
            """
            SELECT DISTINCT
                u.id,
                u.username,
                u.token_balance,
                u.tokens_used,
                (u.token_balance - COALESCE(u.tokens_used, 0)) as available_tokens
            FROM users u
            JOIN conversion_logs cl ON u.id = cl.user_id
            WHERE cl.created_at >= datetime('now', '-1 hour')
            ORDER BY cl.created_at DESC
            LIMIT 5
            """
        ).fetchall()
        
        if not recent_users:
            print("❌ 최근 1시간 내 변환한 사용자가 없습니다.")
            return
        
        for i, user in enumerate(recent_users, 1):
            print(f"\n[{i}] 사용자: {user['username']} (ID: {user['id']})")
            print(f"    토큰 잔액: {user['token_balance']}")
            print(f"    사용한 토큰: {user['tokens_used']}")
            print(f"    사용 가능 토큰: {user['available_tokens']}")

def check_token_deduction_details():
    """토큰 차감 상세 내역 확인"""
    print("\n" + "=" * 80)
    print("토큰 차감 상세 내역 (최근 FILE_CONVERT 활동)")
    print("=" * 80)
    
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        
        # FILE_CONVERT 활동 상세 확인
        converts = conn.execute(
            """
            SELECT 
                al.id,
                al.user_id,
                u.username,
                al.details,
                al.token_change,
                al.token_balance_before,
                al.token_balance_after,
                al.timestamp
            FROM activity_logs al
            JOIN users u ON al.user_id = u.id
            WHERE al.activity_type = 'FILE_CONVERT'
            ORDER BY al.timestamp DESC
            LIMIT 3
            """
        ).fetchall()
        
        if not converts:
            print("❌ FILE_CONVERT 활동 로그가 없습니다.")
            return
        
        for i, conv in enumerate(converts, 1):
            print(f"\n[{i}] 변환 활동 ID: {conv['id']}")
            print(f"    사용자: {conv['username']} (ID: {conv['user_id']})")
            
            # details 파싱
            try:
                details = json.loads(conv['details']) if conv['details'] else {}
                if details:
                    print(f"    📊 변환 상세 정보:")
                    print(f"      - total_recipients: {details.get('total_recipients', 'N/A')}")
                    print(f"      - template_count: {details.get('template_count', 'N/A')}")
                    print(f"      - actual_templates: {details.get('actual_templates', 'N/A')}")
                    print(f"      - tokens_deducted: {details.get('tokens_deducted', 'N/A')}")
                    print(f"      - conversion_id: {details.get('conversion_id', 'N/A')}")
            except Exception as e:
                print(f"    상세 정보 파싱 오류: {e}")
                print(f"    원본: {conv['details']}")
            
            print(f"    💰 토큰 변경: {conv['token_change']}")
            print(f"    💰 토큰 잔액 (이전): {conv['token_balance_before']}")
            print(f"    💰 토큰 잔액 (이후): {conv['token_balance_after']}")
            print(f"    ⏰ 시간: {conv['timestamp']}")

if __name__ == "__main__":
    try:
        check_recent_conversions()
        check_recent_activity_logs()
        check_user_token_status()
        check_token_deduction_details()
        
        print("\n" + "=" * 80)
        print("✅ 로그 확인 완료")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

