"""
토큰 분리 회수 로직 실전 검증 스크립트
무료 토큰만 정확히 회수되는지 검증
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
import json
import sqlite3

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app import app
from core.db import get_conn
from core.token_manager import TokenManager


def setup_test_user(conn):
    """테스트용 유저 생성 또는 초기화"""
    cursor = conn.cursor()
    
    # 기존 유저 확인
    user = conn.execute(
        "SELECT id, username FROM users WHERE username = 'test_token_bot'"
    ).fetchone()
    
    if user:
        user_id = user['id']
        print(f"[INFO] 기존 테스트 유저 발견: ID {user_id}")
        
        # 기존 데이터 초기화
        conn.execute("DELETE FROM token_history WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM activity_logs WHERE user_id = ?", (user_id,))
        conn.execute(
            "UPDATE users SET token_balance = 0, tokens_used = 0 WHERE id = ?",
            (user_id,)
        )
        print(f"[INFO] 테스트 유저 데이터 초기화 완료")
    else:
        # 새 유저 생성
        cursor.execute(
            """
            INSERT INTO users (username, email, password, company_name, business_number, 
                             token_balance, tokens_used, plan_type, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """,
            (
                'test_token_bot',
                'test@token.bot',
                'dummy_hash',
                '테스트 회사',
                '1234567890',
                0,  # 초기 잔액 0
                0,
                'free',
                1
            )
        )
        user_id = cursor.lastrowid
        print(f"[INFO] 새 테스트 유저 생성: ID {user_id}")
    
    conn.commit()
    return user_id


def inject_test_tokens(conn, user_id):
    """테스트 토큰 주입 (함정 설치)"""
    cursor = conn.cursor()
    
    # Case A: 유료 토큰 100개 (만료일: 2030년 - 미래)
    future_date = (datetime.now() + timedelta(days=365*6)).strftime('%Y-%m-%d %H:%M:%S')
    
    conn.execute(
        """
        INSERT INTO token_history
        (user_id, changed_by, amount, change_type, meta, expires_at, source_type, is_expired_processed, created_at)
        VALUES (?, ?, ?, 'grant', ?, ?, 'PAID', 0, datetime('now', '-2 days', 'localtime'))
        """,
        (
            user_id,
            user_id,
            100,
            json.dumps({'test': 'paid_token', 'tag': '[검증용 유료 토큰]'}, ensure_ascii=False),
            future_date,
        )
    )
    print(f"[INJECT] 유료 토큰 100개 주입 (만료일: {future_date})")
    
    # Case B: 무료 토큰 50개 (만료일: 어제 - 과거)
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
    
    conn.execute(
        """
        INSERT INTO token_history
        (user_id, changed_by, amount, change_type, meta, expires_at, source_type, is_expired_processed, created_at)
        VALUES (?, ?, ?, 'grant', ?, ?, 'FREE', 0, datetime('now', '-3 days', 'localtime'))
        """,
        (
            user_id,
            user_id,
            50,
            json.dumps({'test': 'free_token', 'tag': '[검증용 무료 토큰]'}, ensure_ascii=False),
            yesterday,
        )
    )
    print(f"[INJECT] 무료 토큰 50개 주입 (만료일: {yesterday} - 이미 만료됨)")
    
    # 유저 잔액을 150개로 강제 설정
    conn.execute(
        "UPDATE users SET token_balance = 150 WHERE id = ?",
        (user_id,)
    )
    
    conn.commit()
    print(f"[INJECT] 유저 잔액을 150개로 설정 완료")
    
    return {
        'paid_amount': 100,
        'free_amount': 50,
        'total_balance': 150
    }


def verify_results(conn, user_id, expected_balance):
    """결과 검증"""
    print("\n" + "=" * 60)
    print("[VERIFICATION] 결과 검증 시작")
    print("=" * 60)
    
    # 1. 최종 잔액 확인
    user = conn.execute(
        "SELECT token_balance FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()
    
    actual_balance = user['token_balance'] if user else 0
    print(f"\n[1] 최종 토큰 잔액:")
    print(f"    예상: {expected_balance}개")
    print(f"    실제: {actual_balance}개")
    
    balance_correct = (actual_balance == expected_balance)
    if balance_correct:
        print(f"    ✅ 잔액 검증 성공!")
    else:
        print(f"    ❌ 잔액 검증 실패! (차이: {actual_balance - expected_balance}개)")
    
    # 2. activity_logs 확인
    recent_log = conn.execute(
        """
        SELECT activity_type, details, token_change, timestamp
        FROM activity_logs
        WHERE user_id = ? AND activity_type = 'TOKEN_EXPIRED'
        ORDER BY timestamp DESC
        LIMIT 1
        """,
        (user_id,)
    ).fetchone()
    
    print(f"\n[2] activity_logs 검증:")
    if recent_log:
        details_str = recent_log['details']
        details = json.loads(details_str) if isinstance(details_str, str) else details_str
        
        print(f"    활동 타입: {recent_log['activity_type']}")
        print(f"    토큰 변화: {recent_log['token_change']}개")
        print(f"    생성 시간: {recent_log['timestamp']}")
        print(f"    상세 정보: {json.dumps(details, ensure_ascii=False, indent=2)}")
        
        # 무료 토큰 만료 확인
        has_free_expiration = (
            details.get('type') == 'free_token_expiration' or
            '무료 토큰' in details.get('reason', '') or
            'free_token' in str(details).lower()
        )
        
        if has_free_expiration:
            print(f"    ✅ 무료 토큰 만료 로그 확인 성공!")
            log_correct = True
        else:
            print(f"    ⚠️ 무료 토큰 만료 표시가 명확하지 않음")
            log_correct = False
    else:
        print(f"    ❌ TOKEN_EXPIRED 로그를 찾을 수 없습니다!")
        log_correct = False
    
    # 3. token_history 만료 처리 확인
    expired_records = conn.execute(
        """
        SELECT id, amount, source_type, expires_at, is_expired_processed
        FROM token_history
        WHERE user_id = ? AND change_type = 'grant'
        ORDER BY created_at ASC
        """,
        (user_id,)
    ).fetchall()
    
    print(f"\n[3] token_history 상태:")
    for record in expired_records:
        status = "✅ 처리됨" if record['is_expired_processed'] == 1 else "⏳ 대기중"
        print(f"    - {record['source_type']} 토큰 {record['amount']}개: {status} (만료일: {record['expires_at']})")
    
    # 무료 토큰만 처리되었는지 확인
    free_processed = any(
        r['source_type'] == 'FREE' and r['is_expired_processed'] == 1
        for r in expired_records
    )
    paid_not_processed = all(
        r['source_type'] == 'PAID' and r['is_expired_processed'] == 0
        for r in expired_records if r['source_type'] == 'PAID'
    )
    
    if free_processed and paid_not_processed:
        print(f"    ✅ 무료 토큰만 만료 처리됨 (유료 토큰 보호 확인)")
        history_correct = True
    else:
        print(f"    ❌ 토큰 처리 상태가 예상과 다릅니다")
        history_correct = False
    
    return {
        'balance_correct': balance_correct,
        'log_correct': log_correct,
        'history_correct': history_correct,
        'actual_balance': actual_balance,
        'log_details': details if recent_log else None
    }


def cleanup_test_user(conn, user_id):
    """테스트 유저 삭제"""
    print("\n" + "=" * 60)
    print("[CLEANUP] 테스트 데이터 정리")
    print("=" * 60)
    
    conn.execute("DELETE FROM token_history WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM activity_logs WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    
    print(f"[CLEANUP] 테스트 유저 ID {user_id} 삭제 완료")


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("토큰 분리 회수 로직 실전 검증")
    print("=" * 60)
    
    with app.app_context():
        with get_conn() as conn:
            conn.row_factory = sqlite3.Row
            
            try:
                # 1. 테스트 유저 설정
                print("\n[STEP 1] 테스트 환경 조성")
                user_id = setup_test_user(conn)
                
                # 2. 테스트 토큰 주입
                print("\n[STEP 2] 테스트 토큰 주입 (함정 설치)")
                token_info = inject_test_tokens(conn, user_id)
                
                # 3. 만료 체크 실행
                print("\n[STEP 3] 심판의 시간 - 만료 체크 실행")
                token_manager = TokenManager()
                result = token_manager.check_and_deduct_expired_tokens(user_id)
                
                print(f"    처리 결과: {result}")
                
                # 4. 결과 검증
                expected_balance = token_info['total_balance'] - token_info['free_amount']
                verification = verify_results(conn, user_id, expected_balance)
                
                # 5. 최종 보고
                print("\n" + "=" * 60)
                print("[FINAL REPORT] 최종 검증 결과")
                print("=" * 60)
                
                all_passed = (
                    verification['balance_correct'] and
                    verification['log_correct'] and
                    verification['history_correct']
                )
                
                if all_passed:
                    print("✅ 모든 검증 통과!")
                    print(f"   - 잔액 검증: ✅ ({verification['actual_balance']}개)")
                    print(f"   - 로그 검증: ✅")
                    print(f"   - 히스토리 검증: ✅")
                    print("\n🎉 무료 토큰만 정확히 회수되고, 유료 토큰은 보호되었습니다!")
                else:
                    print("❌ 일부 검증 실패")
                    print(f"   - 잔액 검증: {'✅' if verification['balance_correct'] else '❌'}")
                    print(f"   - 로그 검증: {'✅' if verification['log_correct'] else '❌'}")
                    print(f"   - 히스토리 검증: {'✅' if verification['history_correct'] else '❌'}")
                
                # 6. 정리
                cleanup_test_user(conn, user_id)
                
                return all_passed
                
            except Exception as e:
                print(f"\n❌ 테스트 실행 중 오류 발생: {str(e)}")
                import traceback
                traceback.print_exc()
                return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

