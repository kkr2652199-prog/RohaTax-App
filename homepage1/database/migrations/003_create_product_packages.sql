-- 상품(패키지) 관리 테이블 생성
-- 결제 시스템의 기초가 되는 상품 정보를 저장

CREATE TABLE IF NOT EXISTS product_packages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL, -- 상품명 (예: "Premium Event")
    description TEXT, -- 상품 설명
    price INTEGER NOT NULL DEFAULT 0, -- 가격 (원 단위, 예: 10000)
    token_amount INTEGER NOT NULL DEFAULT 0, -- 지급 토큰 수 (무제한은 -1)
    is_active INTEGER NOT NULL DEFAULT 1, -- 판매 중 여부 (1: 활성, 0: 비활성)
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime'))
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_product_packages_name ON product_packages (name);
CREATE INDEX IF NOT EXISTS idx_product_packages_is_active ON product_packages (is_active);
CREATE INDEX IF NOT EXISTS idx_product_packages_created_at ON product_packages (created_at);

