-- File: database/migrations/001_create_activity_logs.sql

-- Description: 'The Control Deck'을 위한 사용자 활동 로그 v2

-- ====================================================================
-- 테이블: activity_logs
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

    -- 관계 설정
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL, -- 사용자가 삭제되어도 로그는 남도록 변경
    FOREIGN KEY (performed_by_id) REFERENCES users (id) ON DELETE SET NULL -- 관리자가 삭제되어도 로그는 남도록 변경
);

-- ====================================================================
-- 인덱스 생성
-- ====================================================================

CREATE INDEX IF NOT EXISTS idx_activity_logs_user_id ON activity_logs (user_id);
CREATE INDEX IF NOT EXISTS idx_activity_logs_timestamp ON activity_logs (timestamp);
CREATE INDEX IF NOT EXISTS idx_activity_logs_activity_type ON activity_logs (activity_type);
CREATE INDEX IF NOT EXISTS idx_activity_logs_performed_by_id ON activity_logs (performed_by_id);



