"""
지침 매니저 - 업종별 지침 관리 및 적용
간단한 구조로 업종별 지침을 관리하고 적용
"""

import logging
from typing import Dict, Any, Optional
from .industry_config_loader import industry_config_loader

logger = logging.getLogger(__name__)

class GuidelineManager:
    """지침 매니저 - 업종별 지침 관리"""
    
    def __init__(self):
        """지침 매니저 초기화"""
        self.logger = logger
        self.current_guideline = None
        self.current_industry = None
        
        # 설정 파일 로더 초기화
        self.config_loader = industry_config_loader
        self.logger.info("지침 매니저 초기화 완료 (설정 파일 기반)")
    
    def select_guideline(self, industry: str) -> Dict[str, Any]:
        """
        업종별 지침 선택 (설정 파일 기반)
        
        Args:
            industry: 업종 ('delivery', 'general', 'tax_accountant', 'other')
            
        Returns:
            Dict: 선택된 지침 정보
        """
        # 설정 파일에서 업종별 지침 정보 로드
        industry_info = self.config_loader.get_industry_info(industry)
        
        # 🚨 안전성 검증: industry_info가 None인 경우 처리
        if not industry_info:
            self.logger.warning(f"알 수 없는 업종: {industry}, 배달대행사 기본값 사용")
            industry_info = self.config_loader.get_industry_info('delivery')
            
            # 🚨 추가 안전성 검증: 기본값도 None인 경우 처리
            if not industry_info:
                self.logger.error("배달대행사 기본 지침도 찾을 수 없습니다. 빈 지침으로 처리합니다.")
                industry_info = {
                    'name': 'Unknown',
                    'description': '지침을 찾을 수 없습니다',
                    'status': 'unknown'
                }
                industry = 'delivery'
        
        # 🚨 안전성 검증: industry_info가 딕셔너리가 아닌 경우 처리
        if not isinstance(industry_info, dict):
            self.logger.error(f"업종 지침이 딕셔너리가 아닙니다: {type(industry_info)}. 빈 지침으로 처리합니다.")
            industry_info = {
                'name': 'Unknown',
                'description': '지침 형식이 올바르지 않습니다',
                'status': 'unknown'
            }
        
        # 현재 지침 설정
        self.current_industry = industry
        self.current_guideline = industry_info
        
        self.logger.info(f"지침 선택: {industry_info.get('name', 'Unknown')}")
        
        return self.current_guideline
    
    def get_current_guideline(self) -> Optional[Dict[str, Any]]:
        """현재 선택된 지침 반환"""
        return self.current_guideline
    
    def get_current_industry(self) -> Optional[str]:
        """현재 선택된 업종 반환"""
        return self.current_industry
    
    def is_guideline_ready(self) -> bool:
        """현재 지침이 사용 준비되었는지 확인"""
        if not self.current_guideline:
            return False
        
        # 🚨 안전성 검증: current_guideline이 딕셔너리가 아닌 경우 처리
        if not isinstance(self.current_guideline, dict):
            self.logger.warning(f"현재 지침이 딕셔너리가 아닙니다: {type(self.current_guideline)}")
            return False
        
        return self.current_guideline.get('status', 'unknown') == 'ready'
    
    def get_guideline_status(self) -> Dict[str, Any]:
        """지침 상태 정보 반환 (설정 파일 기반)"""
        return {
            'current_industry': self.current_industry,
            'current_guideline': self.current_guideline,
            'is_ready': self.is_guideline_ready(),
            'all_guidelines': self.config_loader.get_all_industries()
        }
