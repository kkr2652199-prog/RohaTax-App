"""
골드 회원 전용 고객 관리 API
- GET /api/gold/customers: 고객 목록 조회
- POST /api/gold/customers: 고객 생성
- PUT /api/gold/customers/<id>: 고객 수정
- DELETE /api/gold/customers/<id>: 고객 삭제
"""

import logging
import re
import json
from flask import Blueprint, request, jsonify, session
from functools import wraps
from typing import Dict, Any

from core.db import get_conn_optimized as get_conn
from core.validation_utils import validate_business_number, validate_email, validate_phone

logger = logging.getLogger(__name__)

gold_customers_bp = Blueprint('gold_customers', __name__)

def login_required(f):
    """로그인 필요 데코레이터"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            return jsonify({'success': False, 'error': '로그인이 필요합니다'}), 401
        return f(*args, **kwargs)
    return decorated_function

def gold_member_required(f):
    """골드 회원 필수 데코레이터"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': '로그인이 필요합니다'}), 401
        
        with get_conn() as conn:
            user = conn.execute(
                "SELECT plan_type FROM users WHERE id = ? AND is_deleted = 0",
                (user_id,)
            ).fetchone()
            
            if not user:
                return jsonify({'success': False, 'error': '사용자를 찾을 수 없습니다'}), 404
            
            if user['plan_type'] not in ['gold', 'gold-vip']:
                return jsonify({'success': False, 'error': '골드 회원만 이용 가능한 기능입니다'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

def validate_customer_data(data: Dict[str, Any]) -> tuple:
    """고객 데이터 유효성 검증"""
    errors = []
    
    # 필수 필드 검증
    required_fields = ['company_name', 'representative_name', 'address', 'business_number']
    for field in required_fields:
        if not data.get(field) or not str(data[field]).strip():
            field_names = {
                'company_name': '업체명',
                'representative_name': '대표자명',
                'address': '주소',
                'business_number': '사업자등록번호'
            }
            errors.append(f"{field_names.get(field, field)}은(는) 필수 입력 항목입니다")
    
    # 사업자등록번호 검증 (10자리 숫자, 체크섬)
    business_number = data.get('business_number', '').strip()
    if business_number:
        if not validate_business_number(business_number):
            errors.append('유효하지 않은 사업자등록번호입니다')
    
    # 이메일 검증 (선택사항)
    email = data.get('email', '').strip()
    if email and not validate_email(email):
        errors.append('유효하지 않은 이메일 주소입니다')
    
    # 전화번호 검증 (선택사항)
    phone = data.get('phone', '').strip()
    if phone and not validate_phone(phone):
        errors.append('유효하지 않은 전화번호입니다 (예: 010-1234-5678)')
    
    # 업태·종목 검증 (JSON 형식)
    business_kind = data.get('business_kind', '')
    if business_kind:
        try:
            if isinstance(business_kind, str):
                kind_data = json.loads(business_kind)
            else:
                kind_data = business_kind
            
            if not isinstance(kind_data, dict) or '업태' not in kind_data or '종목' not in kind_data:
                errors.append('업태·종목은 {"업태":"","종목":""} 형식이어야 합니다')
        except (json.JSONDecodeError, TypeError):
            errors.append('유효하지 않은 업태·종목 형식입니다')
    
    return len(errors) == 0, errors

@gold_customers_bp.route('/api/gold/customers', methods=['GET'])
@login_required
@gold_member_required
def get_customers():
    """골드 고객 목록 조회 (페이지네이션, 검색 옵션)"""
    try:
        user_id = session.get('user_id')
        search = request.args.get('search', '').strip()
        limit = request.args.get('limit', 15, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        with get_conn() as conn:
            # 검색 조건
            where_clause = "user_id = ? AND is_deleted = 0"
            params = [user_id]
            
            if search:
                where_clause += " AND (company_name LIKE ? OR business_number LIKE ? OR representative_name LIKE ?)"
                params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
            
            # 전체 개수 조회
            count_query = f"SELECT COUNT(*) as total FROM gold_customers WHERE {where_clause}"
            total = conn.execute(count_query, params).fetchone()['total']
            
            # 목록 조회
            query = f"SELECT * FROM gold_customers WHERE {where_clause} ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            customers = conn.execute(query, params).fetchall()
            
            return jsonify({
                'success': True,
                'data': [dict(row) for row in customers],
                'total': total,
                'limit': limit,
                'offset': offset
            })
    
    except Exception as e:
        logger.error(f"고객 목록 조회 오류: {str(e)}")
        return jsonify({'success': False, 'error': '고객 목록 조회 중 오류가 발생했습니다'}), 500

@gold_customers_bp.route('/api/gold/customers', methods=['POST'])
@login_required
@gold_member_required
def create_customer():
    """골드 고객 생성"""
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': '요청 데이터가 없습니다'}), 400
        
        # 유효성 검증
        is_valid, errors = validate_customer_data(data)
        if not is_valid:
            return jsonify({'success': False, 'errors': errors}), 400
        
        # DB 저장
        with get_conn() as conn:
            # 중복 확인 (활성 레코드)
            business_number = data['business_number'].strip()
            existing = conn.execute(
                "SELECT id FROM gold_customers WHERE user_id = ? AND business_number = ? AND is_deleted = 0",
                (user_id, business_number)
            ).fetchone()
            
            if existing:
                return jsonify({'success': False, 'error': '이미 등록된 사업자등록번호입니다'}), 409
            
            # 업태·종목 JSON 처리
            business_kind = data.get('business_kind', '')
            if isinstance(business_kind, dict):
                business_kind = json.dumps(business_kind, ensure_ascii=False)
            
            # INSERT
            cursor = conn.execute(
                """INSERT INTO gold_customers 
                   (user_id, business_number, company_name, representative_name, address, phone, email, business_kind)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    user_id,
                    business_number,
                    data['company_name'].strip(),
                    data['representative_name'].strip(),
                    data['address'].strip(),
                    data.get('phone', '').strip(),
                    data.get('email', '').strip(),
                    business_kind
                )
            )
            conn.commit()
            
            # 생성된 고객 반환
            customer = conn.execute(
                "SELECT * FROM gold_customers WHERE id = ?",
                (cursor.lastrowid,)
            ).fetchone()
            
            return jsonify({
                'success': True,
                'message': '고객이 등록되었습니다',
                'data': dict(customer)
            }), 201
    
    except Exception as e:
        logger.error(f"고객 생성 오류: {str(e)}")
        if 'UNIQUE' in str(e) or 'idx_unique_active_customer' in str(e):
            return jsonify({'success': False, 'error': '이미 등록된 사업자등록번호입니다'}), 409
        return jsonify({'success': False, 'error': '고객 등록 중 오류가 발생했습니다'}), 500

@gold_customers_bp.route('/api/gold/customers/<int:customer_id>', methods=['PUT'])
@login_required
@gold_member_required
def update_customer(customer_id):
    """골드 고객 수정"""
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': '요청 데이터가 없습니다'}), 400
        
        # 유효성 검증
        is_valid, errors = validate_customer_data(data)
        if not is_valid:
            return jsonify({'success': False, 'errors': errors}), 400
        
        with get_conn() as conn:
            # 소유권 확인
            customer = conn.execute(
                "SELECT * FROM gold_customers WHERE id = ? AND user_id = ? AND is_deleted = 0",
                (customer_id, user_id)
            ).fetchone()
            
            if not customer:
                return jsonify({'success': False, 'error': '고객을 찾을 수 없습니다'}), 404
            
            # 중복 확인 (수정 시 다른 활성 레코드와의 충돌)
            business_number = data['business_number'].strip()
            if business_number != customer['business_number']:
                existing = conn.execute(
                    "SELECT id FROM gold_customers WHERE user_id = ? AND business_number = ? AND is_deleted = 0 AND id != ?",
                    (user_id, business_number, customer_id)
                ).fetchone()
                
                if existing:
                    return jsonify({'success': False, 'error': '이미 등록된 사업자등록번호입니다'}), 409
            
            # 업태·종목 JSON 처리
            business_kind = data.get('business_kind', '')
            if isinstance(business_kind, dict):
                business_kind = json.dumps(business_kind, ensure_ascii=False)
            
            # UPDATE
            conn.execute(
                """UPDATE gold_customers
                   SET business_number = ?, company_name = ?, representative_name = ?, address = ?, 
                       phone = ?, email = ?, business_kind = ?, updated_at = datetime('now')
                   WHERE id = ? AND user_id = ?""",
                (
                    business_number,
                    data['company_name'].strip(),
                    data['representative_name'].strip(),
                    data['address'].strip(),
                    data.get('phone', '').strip(),
                    data.get('email', '').strip(),
                    business_kind,
                    customer_id,
                    user_id
                )
            )
            conn.commit()
            
            # 수정된 고객 반환
            updated_customer = conn.execute(
                "SELECT * FROM gold_customers WHERE id = ?",
                (customer_id,)
            ).fetchone()
            
            return jsonify({
                'success': True,
                'message': '고객 정보가 수정되었습니다',
                'data': dict(updated_customer)
            })
    
    except Exception as e:
        logger.error(f"고객 수정 오류: {str(e)}")
        if 'UNIQUE' in str(e) or 'idx_unique_active_customer' in str(e):
            return jsonify({'success': False, 'error': '이미 등록된 사업자등록번호입니다'}), 409
        return jsonify({'success': False, 'error': '고객 정보 수정 중 오류가 발생했습니다'}), 500

@gold_customers_bp.route('/api/gold/customers/<int:customer_id>', methods=['DELETE'])
@login_required
@gold_member_required
def delete_customer(customer_id):
    """골드 고객 삭제 (소프트 삭제)"""
    try:
        user_id = session.get('user_id')
        
        with get_conn() as conn:
            # 소유권 확인
            customer = conn.execute(
                "SELECT * FROM gold_customers WHERE id = ? AND user_id = ? AND is_deleted = 0",
                (customer_id, user_id)
            ).fetchone()
            
            if not customer:
                return jsonify({'success': False, 'error': '고객을 찾을 수 없습니다'}), 404
            
            # 소프트 삭제
            conn.execute(
                "UPDATE gold_customers SET is_deleted = 1, updated_at = datetime('now') WHERE id = ? AND user_id = ?",
                (customer_id, user_id)
            )
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': '고객이 삭제되었습니다'
            })
    
    except Exception as e:
        logger.error(f"고객 삭제 오류: {str(e)}")
        return jsonify({'success': False, 'error': '고객 삭제 중 오류가 발생했습니다'}), 500


