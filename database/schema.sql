PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  email TEXT,
  password TEXT,
  company_name TEXT,
  business_number TEXT UNIQUE, -- 사업자등록번호 (10자리)
  representative_name TEXT, -- 대표자명
  phone TEXT, -- 휴대폰번호
  address TEXT, -- 사업자 주소
  business_type TEXT, -- 업태
  business_category TEXT, -- 종목
  plan_type TEXT NOT NULL DEFAULT 'free',
  used_count INTEGER NOT NULL DEFAULT 0,
  monthly_limit INTEGER NOT NULL DEFAULT 50,
  is_active INTEGER NOT NULL DEFAULT 1,
  is_admin INTEGER NOT NULL DEFAULT 0,
  token_balance INTEGER DEFAULT 0,
  tokens_used INTEGER DEFAULT 0,
  last_refill_date TEXT, -- 마지막 토큰 리필 날짜
  subscription_status TEXT DEFAULT 'active', -- 구독 상태: active, suspended, cancelled
  subscription_id TEXT, -- 외부 결제 시스템 구독 ID
  trial_end_date TEXT, -- 무료 체험 종료 날짜
  is_deleted INTEGER NOT NULL DEFAULT 0, -- 소프트 삭제
  deleted_at TEXT, -- 삭제 시간
  approval_status TEXT NOT NULL DEFAULT 'approved', -- 승인 상태
  terms_agreed INTEGER NOT NULL DEFAULT 0, -- 이용약관 동의 (0: 미동의, 1: 동의)
  privacy_agreed INTEGER NOT NULL DEFAULT 0, -- 개인정보 수집 및 이용 동의 (0: 미동의, 1: 동의)
  terms_agreed_at TEXT, -- 이용약관 동의 일시
  privacy_agreed_at TEXT, -- 개인정보 수집 및 이용 동의 일시
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS usage_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER,
  action TEXT NOT NULL,
  meta TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT
);

CREATE TABLE IF NOT EXISTS validation_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER,
  validation_type TEXT NOT NULL,
  success INTEGER NOT NULL,
  errors TEXT,
  timestamp TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS token_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  changed_by INTEGER,
  amount INTEGER NOT NULL,
  change_type TEXT NOT NULL, -- grant, use, reset, revoke, expire, REFUND
  meta TEXT,
  expires_at TEXT, -- 토큰 만료일 (무료 토큰의 경우)
  is_expired_processed INTEGER DEFAULT 0, -- 만료 처리 여부 (0: 미처리, 1: 처리됨)
  source_type TEXT DEFAULT 'PAID', -- 토큰 출처: 'FREE' (무료), 'PAID' (유료)
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY(user_id) REFERENCES users(id),
  FOREIGN KEY(changed_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS conversion_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER,
  original_filename TEXT,
  converted_filename TEXT,
  file_size INTEGER,
  conversion_time REAL, -- 변환 소요 시간 (초)
  status TEXT NOT NULL DEFAULT 'pending', -- pending, success, failed
  error_message TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY(user_id) REFERENCES users(id)
);

-- 성능 최적화를 위한 인덱스
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_business_number ON users(business_number);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_is_deleted ON users(is_deleted);
CREATE INDEX IF NOT EXISTS idx_users_plan_type ON users(plan_type);
CREATE INDEX IF NOT EXISTS idx_users_token_balance ON users(token_balance);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

CREATE INDEX IF NOT EXISTS idx_usage_logs_user_id ON usage_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_logs_created_at ON usage_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_usage_logs_action ON usage_logs(action);

CREATE INDEX IF NOT EXISTS idx_validation_logs_user_id ON validation_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_validation_logs_timestamp ON validation_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_validation_logs_validation_type ON validation_logs(validation_type);
CREATE INDEX IF NOT EXISTS idx_validation_logs_success ON validation_logs(success);

CREATE INDEX IF NOT EXISTS idx_token_history_user_id ON token_history(user_id);
CREATE INDEX IF NOT EXISTS idx_token_history_changed_by ON token_history(changed_by);
CREATE INDEX IF NOT EXISTS idx_token_history_created_at ON token_history(created_at);
CREATE INDEX IF NOT EXISTS idx_token_history_change_type ON token_history(change_type);

CREATE INDEX IF NOT EXISTS idx_conversion_logs_user_id ON conversion_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_conversion_logs_status ON conversion_logs(status);
CREATE INDEX IF NOT EXISTS idx_conversion_logs_created_at ON conversion_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_conversion_logs_file_size ON conversion_logs(file_size);
CREATE INDEX IF NOT EXISTS idx_conversion_logs_conversion_time ON conversion_logs(conversion_time);

-- 복합 인덱스 (자주 함께 사용되는 컬럼들)
CREATE INDEX IF NOT EXISTS idx_users_active_deleted ON users(is_active, is_deleted);
CREATE INDEX IF NOT EXISTS idx_conversion_logs_user_status ON conversion_logs(user_id, status);
CREATE INDEX IF NOT EXISTS idx_conversion_logs_status_created ON conversion_logs(status, created_at);
CREATE INDEX IF NOT EXISTS idx_token_history_user_created ON token_history(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_usage_logs_user_created ON usage_logs(user_id, created_at);

-- 비밀번호 재설정 토큰 테이블
CREATE TABLE IF NOT EXISTS password_reset_tokens (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  token TEXT UNIQUE NOT NULL,
  expires_at TEXT NOT NULL,
  used INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY(user_id) REFERENCES users(id)
);

-- 비밀번호 재설정 토큰 인덱스
CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_token ON password_reset_tokens(token);
CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_user_id ON password_reset_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_expires_at ON password_reset_tokens(expires_at);

-- SMS 인증 코드 테이블
-- 주의: phone_number는 정규화된 형식(하이픈 제거)으로 저장되므로 FOREIGN KEY 제약조건 없음
CREATE TABLE IF NOT EXISTS sms_verification_codes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  phone_number TEXT NOT NULL,
  code TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  is_verified INTEGER NOT NULL DEFAULT 0,
  verified_at TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- SMS 인증 코드 인덱스
CREATE INDEX IF NOT EXISTS idx_sms_codes_phone ON sms_verification_codes(phone_number);
CREATE INDEX IF NOT EXISTS idx_sms_codes_expires ON sms_verification_codes(expires_at);
CREATE INDEX IF NOT EXISTS idx_sms_codes_verified ON sms_verification_codes(is_verified);

-- 구독 플랜 테이블 (VIP/VIP-Plus/GoldVIP 요금제 정의)
CREATE TABLE IF NOT EXISTS subscription_plans (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  plan_name TEXT NOT NULL UNIQUE,  -- 'vip', 'vip-plus', 'gold-vip'
  display_name TEXT NOT NULL,      -- 'VIP', 'VIP Plus', 'Gold VIP'
  price INTEGER NOT NULL,          -- 가격 (원)
  token_amount INTEGER NOT NULL,   -- 토큰 수량 (무제한은 -1)
  is_unlimited INTEGER NOT NULL DEFAULT 0,  -- 무제한 여부
  expiry_days INTEGER NOT NULL,    -- 구독 기간 (일)
  features TEXT,                   -- JSON: 기능 목록
  is_active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 유저 구독 테이블 (현재 활성 구독 상태)
CREATE TABLE IF NOT EXISTS user_subscriptions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  plan_id INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'active',  -- 'active', 'expired', 'cancelled'
  purchased_at TEXT NOT NULL DEFAULT (datetime('now')),
  expires_at TEXT NOT NULL,
  remaining_tokens INTEGER,  -- 남은 토큰 (무제한은 -1)
  auto_renew INTEGER NOT NULL DEFAULT 0,  -- 자동 갱신 여부
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY(user_id) REFERENCES users(id),
  FOREIGN KEY(plan_id) REFERENCES subscription_plans(id)
);

-- 구독 플랜 인덱스
CREATE INDEX IF NOT EXISTS idx_subscription_plans_plan_name ON subscription_plans(plan_name);
CREATE INDEX IF NOT EXISTS idx_subscription_plans_is_active ON subscription_plans(is_active);

-- 유저 구독 인덱스
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user_id ON user_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_plan_id ON user_subscriptions(plan_id);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_status ON user_subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_expires_at ON user_subscriptions(expires_at);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_active ON user_subscriptions(user_id, status, expires_at);

-- 기본 구독 플랜 데이터 (언제든 수정 가능)
INSERT OR IGNORE INTO subscription_plans (plan_name, display_name, price, token_amount, is_unlimited, expiry_days, features) VALUES
('vip', 'VIP', 20000, 100, 0, 30, '["토큰 100개", "1개월 사용", "우선 지원"]'),
('vip-plus', 'VIP Plus', 100000, 300, 0, 30, '["토큰 300개", "1개월 사용", "우선 지원", "할인 혜택"]'),
('gold-vip', 'Gold VIP', 300000, -1, 1, 30, '["무제한 토큰", "1개월 사용", "최우선 지원", "모든 기능"]');

-- 골드 회원 전용 고객 리스트 관리 테이블
CREATE TABLE IF NOT EXISTS gold_customers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  business_number TEXT NOT NULL,  -- 사업자등록번호 (10자리)
  company_name TEXT NOT NULL,  -- 업체명
  representative_name TEXT NOT NULL,  -- 대표자명
  address TEXT NOT NULL,  -- 주소
  phone TEXT,  -- 전화번호
  email TEXT,  -- 이메일
  business_kind TEXT,  -- 업태·종목 (JSON: {"업태":"","종목":""})
  is_deleted INTEGER NOT NULL DEFAULT 0,  -- 소프트 삭제
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY(user_id) REFERENCES users(id)
);

-- 골드 고객 인덱스
CREATE INDEX IF NOT EXISTS idx_gold_customers_user_id ON gold_customers(user_id);
CREATE INDEX IF NOT EXISTS idx_gold_customers_business_number ON gold_customers(business_number);
CREATE INDEX IF NOT EXISTS idx_gold_customers_is_deleted ON gold_customers(is_deleted);

-- 고유성 제약: 활성 레코드에 대해서만 동일 사업자번호 중복 방지
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_active_customer ON gold_customers(user_id, business_number) WHERE is_deleted = 0;

-- 복합 인덱스 (활성 고객 조회 최적화)
CREATE INDEX IF NOT EXISTS idx_gold_customers_user_active ON gold_customers(user_id, is_deleted);

