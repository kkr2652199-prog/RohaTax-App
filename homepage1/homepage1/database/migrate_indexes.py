"""
데이터베이스 인덱스 마이그레이션 스크립트
기존 데이터베이스에 성능 최적화 인덱스를 추가합니다.
"""

import sqlite3
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def apply_indexes():
    """데이터베이스에 인덱스 적용"""
    db_path = "database/app.db"
    
    if not os.path.exists(db_path):
        logger.error(f"데이터베이스 파일을 찾을 수 없습니다: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 인덱스 생성 쿼리들
        indexes = [
            # 사용자 테이블 인덱스
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
            "CREATE INDEX IF NOT EXISTS idx_users_business_number ON users(business_number)",
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_users_is_deleted ON users(is_deleted)",
            "CREATE INDEX IF NOT EXISTS idx_users_plan_type ON users(plan_type)",
            "CREATE INDEX IF NOT EXISTS idx_users_token_balance ON users(token_balance)",
            "CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at)",
            
            # 사용 로그 인덱스
            "CREATE INDEX IF NOT EXISTS idx_usage_logs_user_id ON usage_logs(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_usage_logs_created_at ON usage_logs(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_usage_logs_action ON usage_logs(action)",
            
            # 검증 로그 인덱스
            "CREATE INDEX IF NOT EXISTS idx_validation_logs_user_id ON validation_logs(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_validation_logs_timestamp ON validation_logs(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_validation_logs_validation_type ON validation_logs(validation_type)",
            "CREATE INDEX IF NOT EXISTS idx_validation_logs_success ON validation_logs(success)",
            
            # 토큰 이력 인덱스
            "CREATE INDEX IF NOT EXISTS idx_token_history_user_id ON token_history(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_token_history_changed_by ON token_history(changed_by)",
            "CREATE INDEX IF NOT EXISTS idx_token_history_created_at ON token_history(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_token_history_change_type ON token_history(change_type)",
            
            # 변환 로그 인덱스
            "CREATE INDEX IF NOT EXISTS idx_conversion_logs_user_id ON conversion_logs(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_conversion_logs_status ON conversion_logs(status)",
            "CREATE INDEX IF NOT EXISTS idx_conversion_logs_created_at ON conversion_logs(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_conversion_logs_file_size ON conversion_logs(file_size)",
            "CREATE INDEX IF NOT EXISTS idx_conversion_logs_conversion_time ON conversion_logs(conversion_time)",
            
            # 복합 인덱스
            "CREATE INDEX IF NOT EXISTS idx_users_active_deleted ON users(is_active, is_deleted)",
            "CREATE INDEX IF NOT EXISTS idx_conversion_logs_user_status ON conversion_logs(user_id, status)",
            "CREATE INDEX IF NOT EXISTS idx_conversion_logs_status_created ON conversion_logs(status, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_token_history_user_created ON token_history(user_id, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_usage_logs_user_created ON usage_logs(user_id, created_at)"
        ]
        
        # 인덱스 생성 실행
        created_count = 0
        for index_query in indexes:
            try:
                cursor.execute(index_query)
                created_count += 1
                logger.info(f"인덱스 생성 완료: {index_query.split('idx_')[1].split(' ')[0]}")
            except Exception as e:
                logger.warning(f"인덱스 생성 실패: {e}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ 데이터베이스 인덱스 마이그레이션 완료: {created_count}개 인덱스 생성")
        return True
        
    except Exception as e:
        logger.error(f"❌ 인덱스 마이그레이션 실패: {e}")
        return False

def check_indexes():
    """현재 인덱스 상태 확인"""
    db_path = "database/app.db"
    
    if not os.path.exists(db_path):
        logger.error(f"데이터베이스 파일을 찾을 수 없습니다: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 인덱스 목록 조회
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
        indexes = cursor.fetchall()
        
        logger.info(f"📊 현재 인덱스 개수: {len(indexes)}개")
        for index in indexes:
            logger.info(f"  - {index[0]}")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"인덱스 확인 실패: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("🔍 현재 인덱스 상태 확인...")
    check_indexes()
    print("\n🚀 인덱스 마이그레이션 시작...")
    apply_indexes()
    print("\n✅ 마이그레이션 완료!")
