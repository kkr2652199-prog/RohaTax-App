#!/usr/bin/env python3
import sqlite3

sql = """
BEGIN TRANSACTION;
DELETE FROM users;

INSERT INTO users (id, username, email, password, company_name, business_number, representative_name, phone, address, business_type, business_category, plan_type, used_count, monthly_limit, is_active, is_admin, token_balance, tokens_used, last_refill_date, subscription_status, subscription_id, trial_end_date, is_deleted, deleted_at, approval_status, terms_agreed, privacy_agreed, terms_agreed_at, privacy_agreed_at, google_api_key, created_at, updated_at) VALUES (1, 'kweon4309', 'kweon4309@admin.com', '5c737172d2ea8ff8a9df9b6f5a372241:8a09804affa389d2539db2d4f886437f5627576cb3b6d7ec5a9230c67973613d', '관리자', '9999999999', '관리자', '02-1234-5678', '1111', '정보통신업', '소프트웨어개발11', 'free', 0, 0, 1, 1, 2000, 0, NULL, 'active', NULL, NULL, 0, NULL, 'approved', 0, 0, NULL, NULL, NULL, '2025-10-01 08:23:36', '2025-12-24 13:53:29');
INSERT INTO users (id, username, email, password, company_name, business_number, representative_name, phone, address, business_type, business_category, plan_type, used_count, monthly_limit, is_active, is_admin, token_balance, tokens_used, last_refill_date, subscription_status, subscription_id, trial_end_date, is_deleted, deleted_at, approval_status, terms_agreed, privacy_agreed, terms_agreed_at, privacy_agreed_at, google_api_key, created_at, updated_at) VALUES (2, 'tlschs21', 'kweon4309@naver.com', 'kkr75223996', '바로고인천연수', '2131299908', '권강록', '010-9702-3996', '인천시연수구 옥련동 308-1 1층 2호11', '협회 및 단체수리 및 기타 개인서비스업', '서비스1', 'free', 0, 50, 1, 0, 2000, 0, NULL, 'active', NULL, NULL, 0, NULL, 'approved', 0, 0, NULL, NULL, 'AIzaSyAaNUnVtB2K1LiE9M6lcQqUa-A0rwusY0o', '2025-10-01 09:30:12', '2025-12-24 16:24:48');
INSERT INTO users (id, username, email, password, company_name, business_number, representative_name, phone, address, business_type, business_category, plan_type, used_count, monthly_limit, is_active, is_admin, token_balance, tokens_used, last_refill_date, subscription_status, subscription_id, trial_end_date, is_deleted, deleted_at, approval_status, terms_agreed, privacy_agreed, terms_agreed_at, privacy_agreed_at, google_api_key, created_at, updated_at) VALUES (3, 'tlschs22', 'kkr2652199@gmail.com', 'kkr75223996', '냠냠박스', '2131299907', '정구한', '010-7522-2199', '인천 연수구 청량로185번길 37 (옥련동, sm프라자)', '협회및 단체 수리 및 기타 개인서비스업', '쿽서비스배달원', 'free', 0, 50, 1, 0, 20, 0, NULL, 'active', NULL, NULL, 0, NULL, 'approved', 0, 0, NULL, NULL, NULL, '2025-10-01 09:56:00', '2025-12-24 19:11:56');
INSERT INTO users (id, username, email, password, company_name, business_number, representative_name, phone, address, business_type, business_category, plan_type, used_count, monthly_limit, is_active, is_admin, token_balance, tokens_used, last_refill_date, subscription_status, subscription_id, trial_end_date, is_deleted, deleted_at, approval_status, terms_agreed, privacy_agreed, terms_agreed_at, privacy_agreed_at, google_api_key, created_at, updated_at) VALUES (11, 'tlschs25', 'dyddmlehd7@naver.com', '$2b$12$Mu5ldqPnB/M.oExwOcTo5uzO5ekyudyFcb1X2LzKxNql9zuN2XrIG', '유유서비스', '7163801238', '최유철', '010-5196-0208', '경기도 안산시단원구석수로 104,402호(선부동,대성파크뷰)', '협회 및 단체, 수리 및 기타 개인서비스업', '쿽서비스배달업', 'free', 0, 50, 1, 0, 2000, 0, NULL, 'active', NULL, NULL, 0, NULL, 'approved', 0, 0, NULL, NULL, NULL, '2025-11-10 03:01:17', '2025-12-24 16:14:18');
INSERT INTO users (id, username, email, password, company_name, business_number, representative_name, phone, address, business_type, business_category, plan_type, used_count, monthly_limit, is_active, is_admin, token_balance, tokens_used, last_refill_date, subscription_status, subscription_id, trial_end_date, is_deleted, deleted_at, approval_status, terms_agreed, privacy_agreed, terms_agreed_at, privacy_agreed_at, google_api_key, created_at, updated_at) VALUES (12, 'tlschs26', 'ewdfw@naver.com', '$2b$12$YaP4anSuGH383Qy9.C2eNO108tfI.q7BbqjX1Q7LpxQ3htimAyKhK', '경아두마리치킨', '6930901560', '황호민', '010-9702-3995', '인천시관역시 연수구비료대로216 1층', '일반음식점', '치킨1', 'free', 0, 50, 1, 0, 0, 0, NULL, 'active', NULL, NULL, 0, NULL, 'approved', 0, 0, NULL, NULL, NULL, '2025-11-30 01:29:39', '2025-12-24 16:49:22');

COMMIT;
"""

conn = sqlite3.connect('database/app.db')
cursor = conn.cursor()
cursor.executescript(sql)
conn.commit()

cursor.execute('SELECT COUNT(*) FROM users')
count = cursor.fetchone()[0]
print(f"Inserted {count} users")

cursor.execute('SELECT id, username, is_admin FROM users')
users = cursor.fetchall()
for u in users:
    print(f"  ID {u[0]}: {u[1]} (admin={u[2]})")

conn.close()
print("Done!")
