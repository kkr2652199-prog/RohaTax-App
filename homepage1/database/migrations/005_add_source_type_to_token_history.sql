-- File: database/migrations/005_add_source_type_to_token_history.sql
-- Description: token_history 테이블에 source_type 컬럼 추가 (무료/유료 토큰 구분)

-- ====================================================================
-- 컬럼 추가: source_type
-- 목적: 무료 토큰(FREE)과 유료 토큰(PAID)을 구분하여 만료 시 무료 토큰만 회수
-- ====================================================================

-- source_type 컬럼 추가 (기본값: 'PAID' - 기존 데이터는 모두 유료로 간주)
ALTER TABLE token_history 
ADD COLUMN source_type TEXT DEFAULT 'PAID';

-- 인덱스 추가 (만료 체크 성능 최적화)
CREATE INDEX IF NOT EXISTS idx_token_history_source_type ON token_history(source_type);
CREATE INDEX IF NOT EXISTS idx_token_history_source_expires ON token_history(source_type, expires_at) 
WHERE expires_at IS NOT NULL;

-- ====================================================================
-- 기존 데이터 마이그레이션
-- ====================================================================

-- change_type이 'grant'이고 expires_at이 있는 경우, 
-- activity_logs에서 TOKEN_GRANT_BY_ADMIN인지 확인하여 무료 토큰으로 분류
-- (단, 정확한 매칭이 어려우므로 기본값 'PAID' 유지)
-- 향후 지급 시점부터 정확히 구분됨

