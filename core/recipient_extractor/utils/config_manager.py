"""
설정 관리 모듈
업종별 설정 및 지침 관리 전담
"""

from typing import Dict, List, Any, Optional
import logging

from ...industry_config_loader import industry_config_loader

logger = logging.getLogger(__name__)


class ConfigManager:
    """업종별 설정 및 지침 관리 클래스"""
    
    def __init__(self, logger_instance: Optional[logging.Logger] = None):
        """설정 관리자 초기화"""
        self.log = logger_instance or logger
        self.current_industry = None
        self.current_guideline = None
        self.config_loader = industry_config_loader
        self.store_keywords = []
        
        # 기본 키워드 (배달대행사용)
        self.store_keywords = self.get_store_keywords('delivery')
        self.log.info("업종별 설정 파일 로더 초기화 완료")
    
    def get_store_keywords(self, industry: str) -> List[str]:
        """설정 파일에서 업종별 상호 키워드를 가져옴"""
        config = self.config_loader.get_industry_config(industry)
        if config and 'store_keywords' in config:
            return config['store_keywords']
        return []
    
    def get_industry_config(self, industry: str) -> Dict[str, Any]:
        """설정 파일에서 업종별 설정을 가져옴"""
        return self.config_loader.get_industry_config(industry) or {}
    
    def get_sub_guidelines(self, industry: str) -> Dict[str, Any]:
        """서브 지침 가져오기"""
        main_config = self.get_industry_config(industry)
        return main_config.get('sub_guidelines', {})
    
    def set_industry_guideline(self, industry: str, guideline: Dict[str, Any] = None) -> None:
        """업종별 지침 설정 (설정 파일 기반)"""
        self.current_industry = industry
        
        # 설정 파일에서 업종별 규칙 로드
        config = self.get_industry_config(industry)
        if config:
            self.current_guideline = config
            self.store_keywords = config.get('store_keywords', [])
            self.log.info(f"업종별 지침 적용: {config.get('name', 'Unknown')}")
        else:
            # 알 수 없는 업종인 경우 배달대행사 기본값 사용
            self.current_industry = 'delivery'
            self.current_guideline = self.get_industry_config('delivery')
            self.store_keywords = self.get_store_keywords('delivery')
            self.log.warning(f"알 수 없는 업종 '{industry}', 배달대행사 지침으로 대체")
    
    def get_current_guideline(self) -> Dict[str, Any]:
        """현재 적용된 지침 반환 (설정 파일 기반)"""
        return self.current_guideline or self.get_industry_config('delivery')
    
    def is_guideline_ready(self) -> bool:
        """현재 지침이 사용 준비되었는지 확인"""
        if not self.current_guideline:
            return False
        return self.current_guideline.get('status', 'ready') == 'ready'

