-- File: database/migrations/002_create_payment_history.sql

-- Description: 결제 관리 시스템을 위한 결제 이력 테이블
-- Jet Engine 기반 최신 기술 스택 적용

-- ====================================================================
-- 테이블: payment_history
-- 목적: 사용자 결제 이력을 기록하여 결제 관리 및 감사 추적 기능 제공
-- ====================================================================

CREATE TABLE IF NOT EXISTS payment_history (
    -- 기본 키 및 식별 정보
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    order_id TEXT UNIQUE NOT NULL,  -- 주문 ID (Unique 제약)
    
    -- 결제 정보
    amount INTEGER NOT NULL,        -- 결제 금액 (원 단위)
    token_amount INTEGER NOT NULL,  -- 지급된 토큰 수량
    
    -- 결제 상태 및 PG 정보
    status TEXT NOT NULL DEFAULT 'pending',  -- 'pending', 'completed', 'failed', 'cancelled'
    pg_provider TEXT,               -- PG사 정보 (예: 'iamport', 'toss', 'kakaopay')
    
    -- 타임스탬프
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')),
    
    -- 외래키 제약
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- 인덱스 생성 (성능 최적화)
CREATE INDEX IF NOT EXISTS idx_payment_history_user_id ON payment_history(user_id);
CREATE INDEX IF NOT EXISTS idx_payment_history_order_id ON payment_history(order_id);
CREATE INDEX IF NOT EXISTS idx_payment_history_status ON payment_history(status);
CREATE INDEX IF NOT EXISTS idx_payment_history_created_at ON payment_history(created_at);

-- ====================================================================
-- 초기 데이터 (선택사항)
-- ====================================================================
-- 필요시 샘플 데이터 삽입

