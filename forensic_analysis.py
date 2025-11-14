#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
법의학 분석 스크립트
activity_logs와 users 테이블의 데이터를 비교 분석
"""
import sqlite3
import sys

# user_id 지정 (기본값: 1)
user_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1

print(f"\n=== 법의학 분석 보고서 (user_id: {user_id}) ===\n")

try:
    conn = sqlite3.connect('database/app.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. 사용자 정보 확인
    user_info = cursor.execute(
        "SELECT id, username, token_balance, tokens_used FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()
    
    if not user_info:
        print(f"ERROR: user_id {user_id} not found")
        sys.exit(1)
    
    print(f"사용자 정보:")
    print(f"  ID: {user_info['id']}")
    print(f"  Username: {user_info['username']}")
    print(f"  users.token_balance: {user_info['token_balance']}")
    print(f"  users.tokens_used: {user_info['tokens_used']}")
    print()
    
    # 2. activity_logs 테이블 심문 (전체 로그)
    activity_summary = cursor.execute(
        """
        SELECT
            COUNT(*) as total_logs,
            SUM(CASE WHEN token_change > 0 THEN token_change ELSE 0 END) as total_charged,
            SUM(CASE WHEN token_change < 0 THEN ABS(token_change) ELSE 0 END) as total_used,
            SUM(token_change) as net_change
        FROM activity_logs
        WHERE user_id = ? AND COALESCE(is_deleted, 0) = 0
        """,
        (user_id,)
    ).fetchone()
    
    print("=== activity_logs 테이블 (전체 로그) ===")
    print(f"  총 로그 수: {activity_summary['total_logs']}")
    print(f"  총 충전량 (token_change > 0): {activity_summary['total_charged'] or 0}")
    print(f"  총 사용량 (ABS(token_change < 0)): {activity_summary['total_used'] or 0}")
    print(f"  순 변화량 (SUM(token_change)): {activity_summary['net_change'] or 0}")
    print()
    
    # 3. activity_logs 테이블 심문 (리셋 이후만)
    reset_summary = cursor.execute(
        """
        WITH last_reset AS (
            SELECT MAX(timestamp) as reset_time
            FROM activity_logs
            WHERE user_id = ? AND activity_type = 'TOKEN_RESET_BY_ADMIN'
              AND COALESCE(is_deleted, 0) = 0
        )
        SELECT
            COUNT(*) as total_logs,
            COALESCE(SUM(CASE WHEN al.token_change > 0 AND al.activity_type != 'TOKEN_RESET_BY_ADMIN' THEN al.token_change ELSE 0 END), 0) as total_charged,
            COALESCE(SUM(CASE WHEN al.token_change < 0 AND al.activity_type != 'TOKEN_RESET_BY_ADMIN' THEN ABS(al.token_change) ELSE 0 END), 0) as total_used
        FROM activity_logs al, last_reset lr
        WHERE al.user_id = ?
          AND (lr.reset_time IS NULL OR al.timestamp >= lr.reset_time)
          AND COALESCE(al.is_deleted, 0) = 0
        """,
        (user_id, user_id)
    ).fetchone()
    
    print("=== activity_logs 테이블 (리셋 이후만 - /api/v2/user/token-summary 로직) ===")
    print(f"  총 로그 수: {reset_summary['total_logs']}")
    print(f"  총 충전량: {reset_summary['total_charged']}")
    print(f"  총 사용량: {reset_summary['total_used']}")
    print(f"  계산된 잔액: {reset_summary['total_charged'] - reset_summary['total_used']}")
    print()
    
    # 4. users 테이블 심문
    print("=== users 테이블 ===")
    print(f"  token_balance: {user_info['token_balance']}")
    print(f"  tokens_used: {user_info['tokens_used']}")
    print(f"  계산된 잔액 (token_balance - tokens_used): {(user_info['token_balance'] or 0) - (user_info['tokens_used'] or 0)}")
    print()
    
    # 5. 비교 분석
    print("=== 비교 분석 ===")
    activity_balance = reset_summary['total_charged'] - reset_summary['total_used']
    users_balance = (user_info['token_balance'] or 0) - (user_info['tokens_used'] or 0)
    
    print(f"  activity_logs 기반 잔액: {activity_balance}")
    print(f"  users 테이블 기반 잔액: {users_balance}")
    print(f"  차이: {abs(activity_balance - users_balance)}")
    print()
    
    # 6. 최근 활동 로그 샘플
    recent_logs = cursor.execute(
        """
        SELECT 
            timestamp,
            activity_type,
            token_change
        FROM activity_logs
        WHERE user_id = ? AND COALESCE(is_deleted, 0) = 0
        ORDER BY timestamp DESC
        LIMIT 10
        """,
        (user_id,)
    ).fetchall()
    
    print("=== 최근 활동 로그 (최근 10개) ===")
    for log in recent_logs:
        print(f"  {log['timestamp']} | {log['activity_type']} | token_change: {log['token_change']}")
    print()
    
    # 7. 리셋 이벤트 확인
    reset_events = cursor.execute(
        """
        SELECT 
            timestamp,
            activity_type,
            token_change
        FROM activity_logs
        WHERE user_id = ? AND activity_type = 'TOKEN_RESET_BY_ADMIN'
          AND COALESCE(is_deleted, 0) = 0
        ORDER BY timestamp DESC
        """,
        (user_id,)
    ).fetchall()
    
    print("=== TOKEN_RESET_BY_ADMIN 이벤트 ===")
    if reset_events:
        for reset in reset_events:
            print(f"  {reset['timestamp']} | token_change: {reset['token_change']}")
    else:
        print("  리셋 이벤트 없음")
    print()
    
    conn.close()
    
except Exception as e:
    print(f"ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

