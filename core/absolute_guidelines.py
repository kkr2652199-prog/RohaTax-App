"""
절대지침 시스템 통합 모듈
모든 템플릿 기입 작업에 대한 절대적 규칙을 적용합니다.
"""

import os
import json
import re
from datetime import datetime
from typing import Dict, List, Tuple, Any
import sqlite3
from core.db import get_conn_optimized as get_conn

class AbsoluteGuidelines:
    """절대지침 시스템 메인 클래스"""
    
    def __init__(self):
        self.guidelines_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '절대지침')
        self.rules = self.load_all_rules()
        self.validation_engine = ValidationEngine()
    
    def load_all_rules(self) -> Dict[str, Any]:
        """모든 절대지침 규칙을 로드합니다"""
        rules = {
            'template': self.load_template_rules(),
            'supplier': self.load_supplier_rules(),
            'validation': self.load_validation_rules()
        }
        return rules
    
    def load_template_rules(self) -> Dict[str, Any]:
        """템플릿 규칙을 로드합니다"""
        template_rules = {
            'required_fields': {
                'supplier_name': {'position': 'A2', 'type': 'text', 'max_length': 50},
                'business_number': {'position': 'B2', 'type': 'number', 'length': 10},
                'representative_name': {'position': 'C2', 'type': 'text', 'max_length': 20},
                'address': {'position': 'D2', 'type': 'text', 'max_length': 200},
                'phone': {'position': 'E2', 'type': 'text', 'pattern': 'phone'},
                'email': {'position': 'F2', 'type': 'text', 'pattern': 'email'},
                'supply_amount': {'position': 'J2', 'type': 'number', 'decimal_places': 2},
                'tax_amount': {'position': 'K2', 'type': 'number', 'decimal_places': 2},
                'total_amount': {'position': 'L2', 'type': 'number', 'decimal_places': 2},
                'supply_date': {'position': 'M2', 'type': 'date', 'format': 'YYYY-MM-DD'},
                'issue_date': {'position': 'N2', 'type': 'date', 'format': 'YYYY-MM-DD'},
                'business_type': {'position': 'H7', 'type': 'text', 'max_length': 50},  # 공급자 업태
                'business_category': {'position': 'I7', 'type': 'text', 'max_length': 100}  # 공급자 종목
            },
            'optional_fields': {
                'fax': {'position': 'G2', 'type': 'text'},
                'website': {'position': 'H2', 'type': 'text'},
                'contact_person': {'position': 'I2', 'type': 'text'}
            },
            'validation_rules': {
                'tax_calculation': 'tax_amount = supply_amount * 0.1',
                'total_calculation': 'total_amount = supply_amount + tax_amount',
                'date_logic': 'issue_date <= supply_date'
            }
        }
        return template_rules
    
    def load_supplier_rules(self) -> Dict[str, Any]:
        """공급자 정보 규칙을 로드합니다"""
        supplier_rules = {
            'registration_requirements': [
                '사업자등록증 보유',
                '법정 대리인 확인',
                '연락처 정보 인증'
            ],
            'field_validation': {
                'supplier_name': {
                    'required': True,
                    'pattern': r'^[가-힣a-zA-Z0-9\s\.&\-]+$',
                    'min_length': 1,
                    'max_length': 50
                },
                'business_number': {
                    'required': True,
                    'pattern': r'^\d{3}-\d{2}-\d{5}$',
                    'checksum_validation': True
                },
                'representative_name': {
                    'required': True,
                    'pattern': r'^[가-힣a-zA-Z\s]+$',
                    'min_length': 1,
                    'max_length': 20
                },
                'phone': {
                    'required': True,
                    'pattern': r'^(02|0[3-9]\d|010|070)-\d{3,4}-\d{4}$'
                },
                'email': {
                    'required': True,
                    'pattern': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                },
                'business_type': {
                    'required': True,
                    'pattern': r'^[가-힣a-zA-Z0-9\s]+$',
                    'min_length': 2,
                    'max_length': 50
                },
                'business_category': {
                    'required': True,
                    'pattern': r'^[가-힣a-zA-Z0-9\s]+$',
                    'min_length': 3,
                    'max_length': 100
                }
            },
            'security_rules': {
                'encryption': 'AES-256',
                'access_control': 'role_based',
                'audit_logging': True
            }
        }
        return supplier_rules
    
    def load_validation_rules(self) -> Dict[str, Any]:
        """검증 규칙을 로드합니다"""
        validation_rules = {
            'stages': ['format', 'logic', 'external'],
            'performance_limits': {
                'format_validation': 100,  # ms
                'logic_validation': 200,  # ms
                'external_validation': 5000,  # ms
                'total_validation': 6000  # ms
            },
            'accuracy_requirements': {
                'format_validation': 100.0,  # %
                'logic_validation': 99.9,   # %
                'external_validation': 95.0, # %
                'total_validation': 99.5    # %
            }
        }
        return validation_rules
    
    def validate_template_data(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """템플릿 데이터에 대한 절대지침 검증을 수행합니다"""
        errors = []
        
        # 1. 필수 필드 검증
        required_fields = self.rules['template']['required_fields']
        for field, rules in required_fields.items():
            if field not in data or not data[field]:
                errors.append(f"E001: 필수 필드 '{field}'가 누락되었습니다")
        
        # 2. 형식 검증
        for field, value in data.items():
            if field in required_fields:
                field_rules = required_fields[field]
                success, error_msg = self.validate_field_format(value, field_rules, field)
                if not success:
                    errors.append(f"E002: {field} - {error_msg}")
        
        # 3. 논리 검증
        logic_errors = self.validate_business_logic(data)
        errors.extend(logic_errors)
        
        # 4. 중복 검증
        duplicate_errors = self.validate_duplicates(data)
        errors.extend(duplicate_errors)
        
        return len(errors) == 0, errors
    
    def validate_field_format(self, value: Any, rules: Dict[str, Any], field_name: str = None) -> Tuple[bool, str]:
        """개별 필드 형식 검증"""
        if rules['type'] == 'text':
            if not isinstance(value, str):
                return False, "텍스트 형식이 아닙니다"
            
            if len(value) > rules.get('max_length', 1000):
                return False, f"최대 길이({rules['max_length']})를 초과했습니다"
        
        elif rules['type'] == 'number':
            # 사업자등록번호는 특별 처리 (하이픈 포함 문자열)
            if field_name == 'business_number':
                if not isinstance(value, str):
                    return False, "사업자등록번호는 문자열 형식이어야 합니다"
                if not re.match(r'^\d{3}-\d{2}-\d{5}$', value):
                    return False, "사업자등록번호 형식이 올바르지 않습니다"
            else:
                try:
                    num_value = float(value)
                    if rules.get('decimal_places', 0) == 0 and num_value != int(num_value):
                        return False, "정수만 입력 가능합니다"
                except (ValueError, TypeError):
                    return False, "숫자 형식이 아닙니다"
        
        elif rules['type'] == 'date':
            try:
                datetime.strptime(str(value), '%Y-%m-%d')
            except ValueError:
                return False, "날짜 형식(YYYY-MM-DD)이 아닙니다"
        
        return True, "검증 통과"
    
    def validate_business_logic(self, data: Dict[str, Any]) -> List[str]:
        """비즈니스 로직 검증"""
        errors = []
        
        # 세액 계산 검증
        if 'supply_amount' in data and 'tax_amount' in data:
            supply_amount = float(data['supply_amount'])
            tax_amount = float(data['tax_amount'])
            expected_tax = supply_amount * 0.1
            
            if abs(tax_amount - expected_tax) > 0.01:
                errors.append("E003: 세액이 공급가액의 10%가 아닙니다")
        
        # 합계 계산 검증
        if 'supply_amount' in data and 'tax_amount' in data and 'total_amount' in data:
            supply_amount = float(data['supply_amount'])
            tax_amount = float(data['tax_amount'])
            total_amount = float(data['total_amount'])
            expected_total = supply_amount + tax_amount
            
            if abs(total_amount - expected_total) > 0.01:
                errors.append("E004: 합계금액이 공급가액 + 세액과 일치하지 않습니다")
        
        # 날짜 논리 검증
        if 'supply_date' in data and 'issue_date' in data:
            supply_date = datetime.strptime(data['supply_date'], '%Y-%m-%d')
            issue_date = datetime.strptime(data['issue_date'], '%Y-%m-%d')
            
            if issue_date > supply_date:
                errors.append("E005: 발행일자는 공급일자보다 늦을 수 없습니다")
        
        return errors
    
    def validate_duplicates(self, data: Dict[str, Any]) -> List[str]:
        """중복 검증"""
        errors = []
        
        # 사업자번호 중복 검사
        if 'business_number' in data:
            with get_conn() as conn:
                existing = conn.execute(
                    "SELECT id FROM users WHERE business_number = ?", 
                    (data['business_number'],)
                ).fetchone()
                
                if existing:
                    errors.append("E006: 이미 등록된 사업자등록번호입니다")
        
        # 이메일 중복 검사
        if 'email' in data:
            with get_conn() as conn:
                existing = conn.execute(
                    "SELECT id FROM users WHERE email = ?", 
                    (data['email'],)
                ).fetchone()
                
                if existing:
                    errors.append("E007: 이미 등록된 이메일입니다")
        
        return errors
    
    def log_validation_result(self, data: Dict[str, Any], success: bool, errors: List[str], user_id: int):
        """검증 결과를 로그에 기록합니다"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'data_keys': list(data.keys()),
            'success': success,
            'errors': errors,
            'validation_type': 'template_data'
        }
        
        # 데이터베이스에 로그 기록
        with get_conn() as conn:
            conn.execute(
                """INSERT INTO validation_logs 
                   (user_id, validation_type, success, errors, timestamp) 
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, 'template_data', success, json.dumps(errors), datetime.now())
            )
            conn.commit()
    
    def get_guideline_version(self) -> str:
        """현재 절대지침 버전을 반환합니다"""
        return "v1.0.0"
    
    def is_guideline_compliant(self, data: Dict[str, Any]) -> bool:
        """데이터가 절대지침을 준수하는지 확인합니다"""
        success, _ = self.validate_template_data(data)
        return success


class ValidationEngine:
    """검증 엔진 클래스"""
    
    def __init__(self):
        self.performance_metrics = {}
    
    def validate_business_number(self, business_number: str) -> Tuple[bool, str]:
        """사업자등록번호 체크섬 검증"""
        if not re.match(r'^\d{3}-\d{2}-\d{5}$', business_number):
            return False, "사업자등록번호 형식이 올바르지 않습니다"
        
        numbers = business_number.replace('-', '')
        weights = [1, 3, 7, 1, 3, 7, 1, 3, 5]
        
        checksum = 0
        for i in range(9):
            checksum += int(numbers[i]) * weights[i]
        
        checksum += int(numbers[8]) * 5 // 10
        remainder = checksum % 10
        check_digit = 10 - remainder if remainder != 0 else 0
        
        if check_digit != int(numbers[9]):
            return False, "사업자등록번호가 유효하지 않습니다"
        
        return True, "검증 통과"
    
    def validate_phone_number(self, phone: str) -> Tuple[bool, str]:
        """전화번호 형식 검증"""
        patterns = [
            r'^02-\d{3,4}-\d{4}$',  # 서울
            r'^0[3-6]\d-\d{3,4}-\d{4}$',  # 지역번호
            r'^010-\d{4}-\d{4}$',  # 휴대폰
            r'^070-\d{4}-\d{4}$'   # 인터넷전화
        ]
        
        for pattern in patterns:
            if re.match(pattern, phone):
                return True, "검증 통과"
        
        return False, "전화번호 형식이 올바르지 않습니다"
    
    def validate_email(self, email: str) -> Tuple[bool, str]:
        """이메일 형식 검증"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(pattern, email):
            return False, "이메일 형식이 올바르지 않습니다"
        
        # 테스트 도메인 차단
        domain = email.split('@')[1]
        if domain in ['example.com', 'test.com']:
            return False, "테스트 도메인은 사용할 수 없습니다"
        
        return True, "검증 통과"


# 전역 인스턴스
absolute_guidelines = AbsoluteGuidelines()
