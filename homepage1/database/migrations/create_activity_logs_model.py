"""
활동 로그 테이블 생성 마이그레이션 스크립트

이 스크립트는 SQLAlchemy 모델을 기반으로 activity_logs 테이블을 생성합니다.
실제 데이터베이스 변경 전에 반드시 검토 및 승인이 필요합니다.
"""
import sqlite3
import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.db import get_conn


def create_activity_logs_table():
    """
    activity_logs 테이블을 생성하는 마이그레이션 함수
    
    주의: 이 함수는 실제 데이터베이스를 변경합니다.
    실행 전에 반드시 백업을 수행하세요.
    """
    migration_sql = """
    -- ====================================================================
    -- 활동 로그 테이블 생성 마이그레이션
    -- 목적: 사용자와 관리자의 모든 활동을 기록하여 완벽한 감사 추적 기능 제공
    -- ====================================================================
    
    CREATE TABLE IF NOT EXISTS activity_logs (
        -- 기본 키 및 식별 정보
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,  -- 활동의 대상이 되는 사용자
        timestamp TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now', 'localtime')),
        
        -- 활동 주체 (Actor) 정보
        performed_by_id INTEGER,   -- 활동을 수행한 주체 (사용자 자신 or 관리자). NULL일 경우 시스템.
        performed_by_type TEXT,    -- 'USER' 또는 'ADMIN' 또는 'SYSTEM'
        
        -- 활동 분류 정보
        activity_type TEXT NOT NULL,  -- 'FILE_CONVERT', 'TOKEN_PURCHASE', 'GRADE_CHANGE_BY_ADMIN' 등
        details TEXT,                 -- 상세 정보 (JSON). 예: {"filename": "a.xlsx", "from_grade": "vip", "to_grade": "gold"}
        
        -- 토큰 및 비용 정보 ('경제 헌법')
        token_change INTEGER NOT NULL DEFAULT 0,
        potential_cost INTEGER NOT NULL DEFAULT 0,
        token_balance_before INTEGER,  -- 활동 '전' 잔액
        token_balance_after INTEGER,   -- 활동 '후' 잔액
        
        -- 데이터 스냅샷
        user_plan_snapshot TEXT,   -- 활동 당시 사용자의 등급 (예: 'vip', 'gold'). 변경 추적용.
        
        -- 소프트 삭제 플래그
        is_deleted INTEGER NOT NULL DEFAULT 0,  -- 삭제 여부 (0: 활성, 1: 삭제됨)
        
        -- 관계 설정
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL, -- 사용자가 삭제되어도 로그는 남도록 변경
        FOREIGN KEY (performed_by_id) REFERENCES users (id) ON DELETE SET NULL -- 관리자가 삭제되어도 로그는 남도록 변경
    );
    
    -- ====================================================================
    -- 인덱스 생성 (성능 최적화)
    -- ====================================================================
    
    CREATE INDEX IF NOT EXISTS idx_activity_logs_user_id ON activity_logs (user_id);
    CREATE INDEX IF NOT EXISTS idx_activity_logs_timestamp ON activity_logs (timestamp);
    CREATE INDEX IF NOT EXISTS idx_activity_logs_activity_type ON activity_logs (activity_type);
    CREATE INDEX IF NOT EXISTS idx_activity_logs_performed_by_id ON activity_logs (performed_by_id);
    CREATE INDEX IF NOT EXISTS idx_activity_logs_is_deleted ON activity_logs (is_deleted);
    CREATE INDEX IF NOT EXISTS idx_activity_logs_user_timestamp ON activity_logs (user_id, timestamp);
    """
    
    try:
        with get_conn() as conn:
            conn.executescript(migration_sql)
            conn.commit()
            print("[완료] 활동 로그 테이블 생성 완료")
            print("[완료] 인덱스 생성 완료")
            return True
    except sqlite3.Error as e:
        print(f"[오류] 마이그레이션 실행 중 오류 발생: {str(e)}")
        return False
    except Exception as e:
        print(f"[오류] 예상치 못한 오류 발생: {str(e)}")
        return False


def verify_table_structure():
    """
    생성된 테이블 구조를 검증하는 함수
    """
    try:
        with get_conn() as conn:
            cursor = conn.cursor()
            
            # 테이블 존재 확인
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='activity_logs'
            """)
            
            if not cursor.fetchone():
                print("[경고] activity_logs 테이블이 존재하지 않습니다.")
                return False
            
            # 테이블 구조 확인
            cursor.execute("PRAGMA table_info(activity_logs)")
            columns = cursor.fetchall()
            
            print("\n[테이블 구조] activity_logs 테이블 구조:")
            print("-" * 80)
            for col in columns:
                print(f"  {col[1]:<25} {col[2]:<15} {'NOT NULL' if col[3] else 'NULL':<10} DEFAULT: {col[4] or 'None'}")
            print("-" * 80)
            
            # 인덱스 확인
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND tbl_name='activity_logs'
            """)
            indexes = cursor.fetchall()
            
            print(f"\n[인덱스] 생성된 인덱스 ({len(indexes)}개):")
            for idx in indexes:
                print(f"  - {idx[0]}")
            
            return True
            
    except Exception as e:
        print(f"[오류] 테이블 검증 중 오류 발생: {str(e)}")
        return False


if __name__ == '__main__':
    """
    마이그레이션 스크립트 직접 실행 시
    
    주의: 실제 데이터베이스를 변경합니다.
    실행 전에 반드시 백업을 수행하세요.
    """
    print("=" * 80)
    print("활동 로그 테이블 생성 마이그레이션")
    print("=" * 80)
    print("\n⚠️  경고: 이 스크립트는 실제 데이터베이스를 변경합니다.")
    print("⚠️  실행 전에 반드시 데이터베이스 백업을 수행하세요.\n")
    
    response = input("마이그레이션을 실행하시겠습니까? (yes/no): ")
    
    if response.lower() == 'yes':
        print("\n🔄 마이그레이션 실행 중...")
        if create_activity_logs_table():
            print("\n🔍 테이블 구조 검증 중...")
            verify_table_structure()
            print("\n✅ 마이그레이션 완료!")
        else:
            print("\n❌ 마이그레이션 실패!")
    else:
        print("\n❌ 마이그레이션이 취소되었습니다.")

