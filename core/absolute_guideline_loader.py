"""
지능앱 핵심 기술: 절대지침 시스템
동적 지침 로딩 및 적용을 담당하는 클래스
"""

import json
import os
import re
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

class AbsoluteGuidelineLoader:
    """절대지침 시스템 로더 및 관리자"""
    
    def __init__(self, config_path: str = None):
        """
        절대지침 로더 초기화
        
        Args:
            config_path: 절대지침 JSON 파일 경로
        """
        self.logger = logging.getLogger(__name__)
        
        if config_path is None:
            # 기본 경로 설정
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(current_dir, 'config', 'absolute_guidelines_v5.json')
        
        self.config_path = config_path
        self.guidelines = None
        self.load_guidelines()
    
    def load_guidelines(self) -> bool:
        """
        절대지침 v5를 로드하여 유저 정보 절대값 규칙을 반환합니다.
        
        Returns:
            bool: 로드 성공 여부
        """
        try:
            if not os.path.exists(self.config_path):
                self.logger.error(f"절대지침 파일이 존재하지 않습니다: {self.config_path}")
                return False
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.guidelines = json.load(f)
            
            self.logger.info(f"절대지침 v5 로드 완료: {self.guidelines.get('version', 'unknown')}")
            return True
            
        except Exception as e:
            self.logger.error(f"절대지침 v5 로드 실패: {e}")
            return False
    
    def get_guidelines(self) -> Optional[Dict[str, Any]]:
        """로드된 절대지침 반환"""
        return self.guidelines
    
    def apply_absolute_user_info_rules(self, user_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        절대지침 v5에 따라 유저 정보를 절대값으로 처리합니다.
        
        Args:
            user_info: 사용자 정보 딕셔너리
            
        Returns:
            Dict[str, Any]: 처리된 공급자 정보 또는 None
        """
        if not self.guidelines or not user_info:
            self.logger.warning("절대지침 또는 사용자 정보가 없습니다")
            return None
        
        try:
            # 절대지침 v5의 템플릿 필드 매핑 규칙 적용
            template_mapping = self.guidelines.get('absolute_rules', {}).get('template_field_mapping', {})
            
            # 유저 정보를 공급자 정보로 매핑
            supplier_info = {
                '공급자_상호': user_info.get('company_name', ''),
                '공급자_대표자': user_info.get('representative', ''),
                '공급자_사업자번호': user_info.get('business_number', ''),
                '공급자_주소': user_info.get('address', ''),
                '공급자_이메일': user_info.get('email', ''),
                '공급자_전화번호': user_info.get('phone', '')
            }
            
            # 데이터 검증 규칙 적용
            validation_result = self._validate_supplier_info(supplier_info)
            if not validation_result['valid']:
                self.logger.error(f"공급자 정보 검증 실패: {validation_result['errors']}")
                return None
            
            self.logger.info("절대지침 v5 적용 완료: 공급자 정보 검증 통과")
            return supplier_info
            
        except Exception as e:
            self.logger.error(f"절대지침 v5 적용 실패: {e}")
            return None
    
    def _validate_supplier_info(self, supplier_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        공급자 정보 검증
        
        Args:
            supplier_info: 검증할 공급자 정보
            
        Returns:
            Dict[str, Any]: 검증 결과
        """
        validation_rules = self.guidelines.get('absolute_rules', {}).get('data_validation_rules', {})
        errors = []
        
        # 사업자번호 검증
        business_number = supplier_info.get('공급자_사업자번호', '')
        if business_number:
            bn_regex = validation_rules.get('business_number', {}).get('validation_regex', '^[0-9]{10}$')
            if not re.match(bn_regex, business_number):
                errors.append(f"사업자번호 형식 오류: {business_number}")
        
        # 이메일 검증
        email = supplier_info.get('공급자_이메일', '')
        if email:
            email_regex = validation_rules.get('email', {}).get('validation_regex', '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$')
            if not re.match(email_regex, email):
                errors.append(f"이메일 형식 오류: {email}")
        
        # 필수 필드 검증
        required_fields = ['공급자_상호', '공급자_대표자', '공급자_사업자번호', '공급자_주소']
        missing_fields = [field for field in required_fields if not supplier_info.get(field)]
        
        if missing_fields:
            errors.append(f"필수 필드 누락: {', '.join(missing_fields)}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def get_template_cell_mapping(self) -> Dict[str, Any]:
        """템플릿 셀 매핑 규칙 반환"""
        return self.guidelines.get('absolute_rules', {}).get('template_cell_mapping', {})
    
    def get_absolute_values(self) -> Dict[str, str]:
        """절대값 규칙 반환"""
        return self.guidelines.get('absolute_rules', {}).get('absolute_values', {})
    
    def get_guideline_steps(self) -> Dict[str, Any]:
        """1-5단계 지침 반환"""
        return self.guidelines.get('guideline_steps', {})
    
    def get_error_handling_rules(self) -> Dict[str, Any]:
        """오류 처리 규칙 반환"""
        return self.guidelines.get('error_handling', {})
    
    def format_business_number(self, business_number: str) -> str:
        """
        사업자번호 형식 정리 (하이픈 제거)
        
        Args:
            business_number: 원본 사업자번호
            
        Returns:
            str: 정리된 사업자번호
        """
        if not business_number:
            return ""
        
        # 숫자만 추출
        digits = re.sub(r'[^0-9]', '', business_number)
        
        # 10자리인지 확인
        if len(digits) == 10:
            return digits
        else:
            self.logger.warning(f"사업자번호 길이 오류: {business_number} -> {digits}")
            return digits
    
    def format_date(self, date_obj: datetime) -> str:
        """
        날짜를 YYMMDD 형식으로 변환
        
        Args:
            date_obj: 날짜 객체
            
        Returns:
            str: YYMMDD 형식의 날짜 문자열
        """
        if isinstance(date_obj, str):
            try:
                date_obj = datetime.strptime(date_obj, '%Y-%m-%d')
            except ValueError:
                try:
                    date_obj = datetime.strptime(date_obj, '%Y%m%d')
                except ValueError:
                    self.logger.error(f"날짜 형식 변환 실패: {date_obj}")
                    return ""
        
        return date_obj.strftime('%y%m%d')
    
    def apply_guideline_step(self, step_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        특정 지침 단계 적용
        
        Args:
            step_name: 적용할 단계명 (step_1 ~ step_5)
            data: 처리할 데이터
            
        Returns:
            Dict[str, Any]: 처리 결과
        """
        steps = self.get_guideline_steps()
        step_info = steps.get(step_name)
        
        if not step_info:
            self.logger.error(f"지침 단계를 찾을 수 없습니다: {step_name}")
            return {'success': False, 'error': f'Unknown step: {step_name}'}
        
        self.logger.info(f"지침 단계 적용: {step_info.get('name', step_name)}")
        
        try:
            if step_name == 'step_1':
                return self._apply_step_1(data)
            elif step_name == 'step_2':
                return self._apply_step_2(data)
            elif step_name == 'step_3':
                return self._apply_step_3(data)
            elif step_name == 'step_4':
                return self._apply_step_4(data)
            elif step_name == 'step_5':
                return self._apply_step_5(data)
            else:
                return {'success': False, 'error': f'Unimplemented step: {step_name}'}
                
        except Exception as e:
            self.logger.error(f"지침 단계 적용 실패 ({step_name}): {e}")
            return {'success': False, 'error': str(e)}
    
    def _apply_step_1(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """1단계: 사용자 정보 로드"""
        user_info = data.get('user_info', {})
        if not user_info:
            return {'success': False, 'error': '사용자 정보가 없습니다'}
        
        return {'success': True, 'user_info': user_info}
    
    def _apply_step_2(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """2단계: 절대값 검증"""
        user_info = data.get('user_info', {})
        supplier_info = self.apply_absolute_user_info_rules(user_info)
        
        if not supplier_info:
            return {'success': False, 'error': '공급자 정보 검증 실패'}
        
        return {'success': True, 'supplier_info': supplier_info}
    
    def _apply_step_3(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """3단계: 템플릿 매핑"""
        supplier_info = data.get('supplier_info', {})
        template_mapping = self.get_template_cell_mapping()
        
        mapped_data = {}
        for cell, mapping_info in template_mapping.items():
            field = mapping_info.get('field')
            if field in supplier_info:
                mapped_data[cell] = supplier_info[field]
        
        return {'success': True, 'mapped_data': mapped_data}
    
    def _apply_step_4(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """4단계: 절대값 적용"""
        absolute_values = self.get_absolute_values()
        mapped_data = data.get('mapped_data', {})
        
        # 절대값 추가
        for cell, value in absolute_values.items():
            if cell != 'description':
                mapped_data[cell] = value
        
        return {'success': True, 'final_data': mapped_data}
    
    def _apply_step_5(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """5단계: 최종 검증"""
        final_data = data.get('final_data', {})
        
        # B7 셀(작성일자) 설정
        issue_date = data.get('issue_date')
        if issue_date:
            # 사용자가 선택한 날짜를 YYMMDD 형식으로 변환
            try:
                from datetime import datetime
                if isinstance(issue_date, str):
                    # ISO 형식 (YYYY-MM-DD)을 YYMMDD로 변환
                    if '-' in issue_date:
                        date_obj = datetime.strptime(issue_date, '%Y-%m-%d')
                        final_data['B7'] = date_obj.strftime('%y%m%d')
                    else:
                        final_data['B7'] = issue_date
                else:
                    final_data['B7'] = self.format_date(issue_date)
            except Exception as e:
                self.logger.warning(f"날짜 변환 실패, 현재 날짜 사용: {e}")
                from datetime import datetime
                current_date = datetime.now()
                final_data['B7'] = self.format_date(current_date)
        else:
            # 날짜가 없으면 현재 날짜로 설정
            from datetime import datetime
            current_date = datetime.now()
            final_data['B7'] = self.format_date(current_date)
        
        # 필수 셀 확인 (B7 제외 - 동적으로 설정됨)
        required_cells = ['A7', 'C7', 'D7', 'E7']
        missing_cells = [cell for cell in required_cells if cell not in final_data or not final_data[cell]]
        
        if missing_cells:
            return {'success': False, 'error': f'필수 셀 누락: {missing_cells}'}
        
        return {'success': True, 'validated_data': final_data}


# 싱글톤 인스턴스
absolute_guideline_loader = AbsoluteGuidelineLoader()


def get_absolute_guideline_loader() -> AbsoluteGuidelineLoader:
    """절대지침 로더 싱글톤 인스턴스 반환"""
    return absolute_guideline_loader






