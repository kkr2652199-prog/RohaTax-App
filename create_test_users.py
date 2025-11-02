"""
테스트 유저 생성 스크립트
VIP, 프리미엄, 골드 회원 3명을 생성합니다.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.db import get_conn
from core.password_utils import hash_password

def create_test_users():
    """VIP, 프리미엄, 골드 테스트 유저 생성"""
    test_users = [
        {
            'username': 'tlschs21',
            'email': 'tlschs21@example.com',
            'password': 'kkr75223996',
            'company_name': 'VIP 테스트 회사',
            'plan_type': 'vip',
            'monthly_limit': 100,
            'token_balance': 100,
            'business_number': '1000000001',
            'representative_name': 'VIP테스트',
            'address': '서울시 강남구 VIP로 1',
            'phone': '010-1000-0001',
            'business_type': '서비스업',
            'business_category': '컨설팅'
        },
        {
            'username': 'tlschs22',
            'email': 'tlschs22@example.com',
            'password': 'kkr75223996',
            'company_name': '프리미엄 테스트 회사',
            'plan_type': 'vip-plus',
            'monthly_limit': 300,
            'token_balance': 300,
            'business_number': '2000000002',
            'representative_name': '프리미엄테스트',
            'address': '서울시 강남구 프리미엄로 2',
            'phone': '010-2000-0002',
            'business_type': '서비스업',
            'business_category': 'IT서비스'
        },
        {
            'username': 'tlschs23',
            'email': 'tlschs23@example.com',
            'password': 'kkr75223996',
            'company_name': '골드 테스트 회사',
            'plan_type': 'gold-vip',
            'monthly_limit': 0,  # 무제한
            'token_balance': 999999,
            'business_number': '3000000003',
            'representative_name': '골드테스트',
            'address': '서울시 강남구 골드로 3',
            'phone': '010-3000-0003',
            'business_type': '서비스업',
            'business_category': '프리미엄서비스'
        },
        {
            'username': 'tlschs24',
            'email': 'tlschs24@example.com',
            'password': 'kkr75223996',
            'company_name': '골드 테스트 회사 2',
            'plan_type': 'gold-vip',
            'monthly_limit': 0,
            'token_balance': 999999,
            'business_number': '3000000004',
            'representative_name': '골드테스트2',
            'address': '서울시 강남구 골드로 4',
            'phone': '010-3000-0004',
            'business_type': '서비스업',
            'business_category': '프리미엄서비스'
        },
        {
            'username': 'tlschs25',
            'email': 'tlschs25@example.com',
            'password': 'kkr75223996',
            'company_name': '골드 테스트 회사 3',
            'plan_type': 'gold-vip',
            'monthly_limit': 0,
            'token_balance': 999999,
            'business_number': '3000000005',
            'representative_name': '골드테스트3',
            'address': '서울시 강남구 골드로 5',
            'phone': '010-3000-0005',
            'business_type': '서비스업',
            'business_category': '프리미엄서비스'
        }
    ]
    
    with get_conn() as conn:
        created_count = 0
        updated_count = 0
        deleted_count = 0
        
        # 기존 테스트 유저 삭제 (test_vip, test_premium, test_gold)
        old_usernames = ['test_vip', 'test_premium', 'test_gold']
        for old_username in old_usernames:
            conn.execute("DELETE FROM users WHERE username = ?", (old_username,))
            deleted_count += 1
        
        for user_data in test_users:
            # 기존 유저 확인 (동일 username 또는 business_number)
            existing = conn.execute(
                "SELECT id FROM users WHERE username = ? OR business_number = ?",
                (user_data['username'], user_data['business_number'])
            ).fetchone()
            
            if existing:
                # 기존 유저 업데이트
                user_id = existing['id']
                password_hash = hash_password(user_data['password'])
                
                conn.execute("""
                    UPDATE users SET
                        email = ?, password = ?, company_name = ?, plan_type = ?,
                        monthly_limit = ?, token_balance = ?, tokens_used = 0,
                        business_number = ?, representative_name = ?, address = ?,
                        phone = ?, business_type = ?, business_category = ?,
                        is_active = 1, approval_status = 'approved',
                        updated_at = datetime('now')
                    WHERE id = ?
                """, (
                    user_data['email'],
                    password_hash,
                    user_data['company_name'],
                    user_data['plan_type'],
                    user_data['monthly_limit'],
                    user_data['token_balance'],
                    user_data['business_number'],
                    user_data['representative_name'],
                    user_data['address'],
                    user_data['phone'],
                    user_data['business_type'],
                    user_data['business_category'],
                    user_id
                ))
                
                updated_count += 1
                plan_display = {
                    'vip': 'VIP',
                    'vip-plus': '프리미엄',
                    'gold-vip': '골드'
                }.get(user_data['plan_type'], user_data['plan_type'])
                
                print(f"[UPDATE] {plan_display} 테스트 유저 업데이트 완료: {user_data['username']}")
                print(f"   - 비밀번호: {user_data['password']}")
                print(f"   - 이메일: {user_data['email']}")
                print(f"   - 토큰 잔액: {user_data['token_balance']}")
                continue
            
            # 비밀번호 해시화
            password_hash = hash_password(user_data['password'])
            
            # 유저 생성
            try:
                conn.execute("""
                    INSERT INTO users (
                        username, email, password, company_name, plan_type,
                        monthly_limit, used_count, is_active, is_admin,
                        token_balance, tokens_used, approval_status,
                        business_number, representative_name, address,
                        phone, business_type, business_category
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_data['username'],
                    user_data['email'],
                    password_hash,
                    user_data['company_name'],
                    user_data['plan_type'],
                    user_data['monthly_limit'],
                    0,  # used_count
                    1,  # is_active
                    0,  # is_admin
                    user_data['token_balance'],
                    0,  # tokens_used
                    'approved',
                    user_data['business_number'],
                    user_data['representative_name'],
                    user_data['address'],
                    user_data['phone'],
                    user_data['business_type'],
                    user_data['business_category']
                ))
                
                created_count += 1
                plan_display = {
                    'vip': 'VIP',
                    'vip-plus': '프리미엄',
                    'gold-vip': '골드'
                }.get(user_data['plan_type'], user_data['plan_type'])
                
                print(f"[OK] {plan_display} 테스트 유저 생성 완료: {user_data['username']}")
                print(f"   - 비밀번호: {user_data['password']}")
                print(f"   - 이메일: {user_data['email']}")
                print(f"   - 토큰 잔액: {user_data['token_balance']}")
                
            except Exception as e:
                print(f"[ERROR] 유저 '{user_data['username']}' 생성 실패: {str(e)}")
        
        conn.commit()
        
        print(f"\n[RESULT] 작업 완료: {created_count}명 생성, {updated_count}명 업데이트, {deleted_count}명 삭제")
        print("\n로그인 정보:")
        print("=" * 60)
        for user_data in test_users:
            plan_display = {
                'vip': 'VIP',
                'vip-plus': '프리미엄',
                'gold-vip': '골드'
            }.get(user_data['plan_type'], user_data['plan_type'])
            print(f"{plan_display}: {user_data['username']} / {user_data['password']}")
        print("=" * 60)

if __name__ == '__main__':
    print("테스트 유저 생성 시작...")
    print("-" * 60)
    create_test_users()
    print("-" * 60)
    print("테스트 유저 생성 완료!")

