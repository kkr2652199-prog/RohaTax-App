#!/usr/bin/env python3
"""
sample_invoice4.xlsx 변환 재현/진단 스크립트 (콘솔 이모지/유니코드 미사용)
사용자: tlschs23 / 비밀번호: kkr75223996 (DB 조회)
"""

import os
import sys
from pathlib import Path
import sqlite3

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.db import get_conn
from core.conversion_engine import ConversionEngine


def get_user_info(username: str):
    """DB에서 사용자 기본 정보 조회 (공급자 정보로 사용)"""
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT id, username, email, company_name, business_number, representative_name,
                   phone, address
            FROM users
            WHERE username = ? AND COALESCE(is_deleted,0) = 0
            ORDER BY id DESC LIMIT 1
            """,
            (username,)
        ).fetchone()
        if not row:
            return None
        return {
            'user_id': row['id'],
            'username': row['username'],
            'email': row['email'],
            'company_name': row['company_name'],
            'business_number': row['business_number'],
            'representative': row['representative_name'],
            'phone': row['phone'],
            'address': row['address'],
        }


def main():
    username = "tlschs23"
    sample_path = str(project_root / "tests" / "input" / "sample_invoice4.xlsx")
    if not os.path.exists(sample_path):
        print("ERROR: 테스트 파일이 존재하지 않습니다:", sample_path)
        sys.exit(1)

    user_info = get_user_info(username)
    if not user_info:
        print("ERROR: 사용자를 찾을 수 없습니다:", username)
        sys.exit(1)

    engine = ConversionEngine()

    print("[1/2] 파일 변환 시작:", sample_path)
    try:
        result = engine.convert_file(
            uploaded_file_path=sample_path,
            supplier_info={
                'company_name': user_info.get('company_name'),
                'business_number': user_info.get('business_number'),
                'representative_name': user_info.get('representative'),
                'address': user_info.get('address'),
                'email': user_info.get('email'),
                'phone': user_info.get('phone'),
            },
            template_id="hometax_official",
            industry_type="delivery",
            guidelines=None,
            issue_date=None,
            file_name="sample_invoice4",
            user_info=user_info,
        )
    except Exception as e:
        print("ERROR: 변환 수행 중 예외 발생:", e)
        raise

    print("[2/2] 변환 결과")
    print("  success:", result.get('success'))
    print("  files:", result.get('files'))
    print("  total_recipients:", result.get('total_recipients'))
    if 'conversion_log' in result:
        print("  conversion_log (tail):")
        for line in result['conversion_log'][-10:]:
            print("   -", line)
    if not result.get('success'):
        print("  error:", result.get('error'))
        print("  details:", result.get('details'))


if __name__ == "__main__":
    sys.exit(main())



