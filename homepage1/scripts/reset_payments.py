"""
결제 내역 초기화 스크립트
payment_history 테이블의 모든 데이터 삭제 및 ID 시퀀스 초기화
"""

import sqlite3
import os
import sys

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.db import get_conn_optimized

def reset_payments():
    """결제 내역 초기화"""
    print("=" * 50)
    print("결제 내역 초기화 시작")
    print("=" * 50)
    
    try:
        with get_conn_optimized() as conn:
            conn.row_factory = sqlite3.Row
            
            # 기존 데이터 개수 확인
            count_before = conn.execute("SELECT COUNT(*) as count FROM payment_history").fetchone()['count']
            print(f"\n[현재 상태] 결제 내역: {count_before}건")
            
            # 모든 데이터 삭제
            print("\n[1단계] 결제 내역 데이터 삭제 중...")
            conn.execute("DELETE FROM payment_history")
            conn.commit()
            print("데이터 삭제 완료")
            
            # ID 시퀀스 초기화 (SQLite는 DELETE 후에도 시퀀스가 유지되므로 명시적으로 초기화)
            print("\n[2단계] ID 시퀀스 초기화 중...")
            # SQLite에서 시퀀스 초기화는 sqlite_sequence 테이블을 사용
            conn.execute("DELETE FROM sqlite_sequence WHERE name='payment_history'")
            conn.commit()
            print("ID 시퀀스 초기화 완료")
            
            # 삭제 후 데이터 개수 확인
            count_after = conn.execute("SELECT COUNT(*) as count FROM payment_history").fetchone()['count']
            print(f"\n[최종 상태] 결제 내역: {count_after}건")
            
            print("\n" + "=" * 50)
            print("결제 내역 초기화 완료!")
            print("=" * 50)
            
    except Exception as e:
        print(f"\n[오류] 결제 내역 초기화 실패: {str(e)}")
        raise

if __name__ == "__main__":
    reset_payments()

