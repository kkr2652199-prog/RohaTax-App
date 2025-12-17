"""
구독 플랜 및 유저 구독 테이블 생성 스크립트
"""
import sqlite3
import os
import logging

logger = logging.getLogger(__name__)


def create_subscription_tables():
    """구독 관련 테이블 생성"""
    try:
        # schema.sql에서 추가된 부분만 실행
        db_path = os.path.join(os.path.dirname(__file__), 'app.db')
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 구독 플랜 테이블 생성
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscription_plans (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          plan_name TEXT NOT NULL UNIQUE,
          display_name TEXT NOT NULL,
          price INTEGER NOT NULL,
          token_amount INTEGER NOT NULL,
          is_unlimited INTEGER NOT NULL DEFAULT 0,
          expiry_days INTEGER NOT NULL,
          features TEXT,
          is_active INTEGER NOT NULL DEFAULT 1,
          created_at TEXT NOT NULL DEFAULT (datetime('now')),
          updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """)
        
        # 유저 구독 테이블 생성
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_subscriptions (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER NOT NULL,
          plan_id INTEGER NOT NULL,
          status TEXT NOT NULL DEFAULT 'active',
          purchased_at TEXT NOT NULL DEFAULT (datetime('now')),
          expires_at TEXT NOT NULL,
          remaining_tokens INTEGER,
          auto_renew INTEGER NOT NULL DEFAULT 0,
          created_at TEXT NOT NULL DEFAULT (datetime('now')),
          updated_at TEXT NOT NULL DEFAULT (datetime('now')),
          FOREIGN KEY(user_id) REFERENCES users(id),
          FOREIGN KEY(plan_id) REFERENCES subscription_plans(id)
        );
        """)
        
        # 인덱스 생성
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_subscription_plans_plan_name ON subscription_plans(plan_name);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_subscription_plans_is_active ON subscription_plans(is_active);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user_id ON user_subscriptions(user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_subscriptions_plan_id ON user_subscriptions(plan_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_subscriptions_status ON user_subscriptions(status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_subscriptions_expires_at ON user_subscriptions(expires_at);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_subscriptions_active ON user_subscriptions(user_id, status, expires_at);")
        
        # 기본 플랜 데이터 삽입
        cursor.execute("""
        INSERT OR IGNORE INTO subscription_plans (plan_name, display_name, price, token_amount, is_unlimited, expiry_days, features) VALUES
        ('vip', 'VIP', 20000, 100, 0, 30, '["토큰 100개", "1개월 사용", "우선 지원"]'),
        ('vip-plus', 'VIP Plus', 100000, 300, 0, 30, '["토큰 300개", "1개월 사용", "우선 지원", "할인 혜택"]'),
        ('gold-vip', 'Gold VIP', 300000, -1, 1, 30, '["무제한 토큰", "1개월 사용", "최우선 지원", "모든 기능"]');
        """)
        
        conn.commit()
        conn.close()
        
        logger.info("구독 테이블 생성 완료")
        print("구독 테이블 생성 완료")
        print("VIP: 20,000원 (100토큰)")
        print("VIP Plus: 100,000원 (300토큰)")
        print("Gold VIP: 300,000원 (무제한)")
        
        return True
        
    except Exception as e:
        logger.error(f"구독 테이블 생성 중 오류: {str(e)}")
        print(f"오류: {str(e)}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("구독 플랜 테이블 생성 스크립트")
    print("=" * 60)
    
    create_subscription_tables()
    
    print("=" * 60)
    print("완료")
    print("=" * 60)


