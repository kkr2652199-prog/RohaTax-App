"""
업종별 설정 파일 로더
JSON 설정 파일에서 업종별 규칙을 동적으로 로드하는 클래스
"""

import json
import os
import logging
from typing import Dict, Any, Optional

class IndustryConfigLoader:
    """업종별 설정을 JSON 파일에서 로드하는 클래스"""
    
    def __init__(self, config_path: str = "config/industry_config.json"):
        """
        설정 파일 로더 초기화
        
        Args:
            config_path (str): 설정 파일 경로
        """
        self.config_path = config_path
        self.logger = logging.getLogger(__name__)
        self._config_cache = None
        self._load_config()
    
    def _load_config(self) -> None:
        """설정 파일을 로드하고 캐시에 저장"""
        try:
            if not os.path.exists(self.config_path):
                self.logger.error(f"설정 파일을 찾을 수 없습니다: {self.config_path}")
                self._config_cache = {}
                return
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config_cache = json.load(f)
            
            self.logger.info(f"업종별 설정 파일 로드 완료: {len(self._config_cache)}개 업종")
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON 파싱 오류: {e}")
            self._config_cache = {}
        except Exception as e:
            self.logger.error(f"설정 파일 로드 오류: {e}")
            self._config_cache = {}
    
    def reload_config(self) -> None:
        """설정 파일을 다시 로드"""
        self.logger.info("업종별 설정 파일 재로드 중...")
        self._load_config()


    def get_config(self, industry: str) -> Optional[Dict[str, Any]]:
        """
        특정 업종의 설정을 반환
        
        Args:
            industry (str): 업종명 (delivery, general, tax_accountant, other)
            
        Returns:
            Optional[Dict[str, Any]]: 업종 설정 딕셔너리 또는 None
        """
        if not self._config_cache:
            self.logger.warning("설정 캐시가 비어있습니다")
            return None
        
        config = self._config_cache.get(industry)
        if config:
            self.logger.debug(f"업종 '{industry}' 설정 로드: {config.get('name', 'Unknown')}")
        else:
            self.logger.warning(f"업종 '{industry}' 설정을 찾을 수 없습니다")
        
        return config
    
    def get_industry_config(self, industry: str) -> Optional[Dict[str, Any]]:
        """특정 업종의 설정을 반환 (get_config와 동일)"""
        return self.get_config(industry)
    
    def get_all_industries(self) -> Dict[str, Dict[str, Any]]:
        """
        모든 업종 설정을 반환
        
        Returns:
            Dict[str, Dict[str, Any]]: 모든 업종 설정 딕셔너리
        """
        return self._config_cache or {}
    
    def get_industry_list(self) -> list:
        """
        사용 가능한 업종 목록을 반환
        
        Returns:
            list: 업종명 목록
        """
        return list(self._config_cache.keys()) if self._config_cache else []
    
    def get_industry_info(self, industry: str) -> Optional[Dict[str, str]]:
        """
        업종의 기본 정보를 반환 (이름, 설명 등)
        
        Args:
            industry (str): 업종명
            
        Returns:
            Optional[Dict[str, str]]: 업종 기본 정보 딕셔너리 또는 None
        """
        config = self.get_config(industry)
        if not config:
            return None
        
        return {
            'name': config.get('name', 'Unknown'),
            'description': config.get('description', ''),
            'status': config.get('status', 'unknown')
        }
    
    def save_industry_config(self, industry: str, config: Dict[str, Any]) -> bool:
        """
        특정 업종의 설정을 저장
        
        Args:
            industry (str): 업종명
            config (Dict[str, Any]): 저장할 설정
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            if not self._config_cache:
                self._config_cache = {}
            
            self._config_cache[industry] = config
            self._save_config()
            self.logger.info(f"업종 '{industry}' 설정 저장 완료")
            return True
            
        except Exception as e:
            self.logger.error(f"업종 '{industry}' 설정 저장 실패: {e}")
            return False
    
    def delete_industry_config(self, industry: str) -> bool:
        """
        특정 업종의 설정을 삭제
        
        Args:
            industry (str): 삭제할 업종명
            
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            if self._config_cache and industry in self._config_cache:
                del self._config_cache[industry]
                self._save_config()
                self.logger.info(f"업종 '{industry}' 설정 삭제 완료")
                return True
            else:
                self.logger.warning(f"삭제할 업종 '{industry}' 설정을 찾을 수 없습니다")
                return False
                
        except Exception as e:
            self.logger.error(f"업종 '{industry}' 설정 삭제 실패: {e}")
            return False
    
    def _save_config(self) -> None:
        """설정을 파일에 저장"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config_cache, f, ensure_ascii=False, indent=2)
            
            self.logger.debug(f"설정 파일 저장 완료: {self.config_path}")

        except Exception as e:
            self.logger.error(f"설정 파일 저장 오류: {e}")


# 전역 설정 로더 인스턴스
industry_config_loader = IndustryConfigLoader()