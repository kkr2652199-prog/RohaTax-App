"""
전자세금계산서 템플릿 관리 시스템
"""
import os
import json
from typing import Dict, List, Optional
from pathlib import Path

class TemplateManager:
    """전자세금계산서 템플릿 관리 클래스"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent.parent / "templates_data"
        self.excel_templates_path = self.base_path / "excel_templates"
        self.template_config_path = self.base_path / "template_config.json"
        
        # 템플릿 설정 초기화
        self._init_template_config()
    
    def _init_template_config(self):
        """템플릿 설정 파일 초기화"""
        if not self.template_config_path.exists():
            default_config = {
                "templates": {
                    "hometax_official": {
                        "name": "홈텍스 공식 세금계산서",
                        "description": "홈텍스에서 제공하는 공식 전자세금계산서 템플릿",
                        "file": "standard/홈텍스제공 공식파일(일반)1~50.xlsx",
                        "sheet_name": "엑셀업로드양식",
                        "header_row": 1,
                        "fields": {
                            "company_name": "공급자명",
                            "business_number": "사업자등록번호",
                            "representative_name": "대표자명",
                            "address": "주소",
                            "phone": "전화번호",
                            "email": "이메일",
                            "invoice_date": "발행일",
                            "invoice_number": "세금계산서번호",
                            "supply_date": "공급일",
                            "supply_amount": "공급가액",
                            "tax_amount": "세액",
                            "total_amount": "합계금액"
                        }
                    }
                },
                "last_updated": "2024-10-01T12:00:00Z"
            }
            
            with open(self.template_config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
    
    def get_available_templates(self) -> List[Dict]:
        """사용 가능한 템플릿 목록 반환"""
        try:
            with open(self.template_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            templates = []
            for template_id, template_info in config.get("templates", {}).items():
                template_path = self.excel_templates_path / template_info["file"]
                
                templates.append({
                    "id": template_id,
                    "name": template_info["name"],
                    "description": template_info["description"],
                    "file_path": str(template_path),
                    "exists": template_path.exists(),
                    "sheet_name": template_info.get("sheet_name", ""),
                    "header_row": template_info.get("header_row", 1),
                    "fields": template_info.get("fields", {})
                })
            
            return templates
        except Exception as e:
            print(f"템플릿 목록 조회 실패: {e}")
            return []
    
    def get_template_info(self, template_id: str) -> Optional[Dict]:
        """특정 템플릿 정보 반환"""
        templates = self.get_available_templates()
        for template in templates:
            if template["id"] == template_id:
                return template
        return None
    
    def validate_template_file(self, template_id: str) -> bool:
        """템플릿 파일 존재 여부 확인"""
        template_info = self.get_template_info(template_id)
        if not template_info:
            return False
        
        template_path = Path(template_info["file_path"])
        return template_path.exists()
    
    def get_template_path(self, template_id: str) -> Optional[str]:
        """템플릿 파일 경로 반환"""
        template_info = self.get_template_info(template_id)
        if not template_info:
            return None
        
        template_path = Path(template_info["file_path"])
        if template_path.exists():
            return str(template_path)
        return None
    
    def add_template(self, template_id: str, template_info: Dict) -> bool:
        """새 템플릿 추가"""
        try:
            with open(self.template_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            config["templates"][template_id] = template_info
            config["last_updated"] = self._get_current_timestamp()
            
            with open(self.template_config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"템플릿 추가 실패: {e}")
            return False
    
    def remove_template(self, template_id: str) -> bool:
        """템플릿 제거"""
        try:
            with open(self.template_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            if template_id in config["templates"]:
                del config["templates"][template_id]
                config["last_updated"] = self._get_current_timestamp()
                
                with open(self.template_config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
                
                return True
            return False
        except Exception as e:
            print(f"템플릿 제거 실패: {e}")
            return False
    
    def _get_current_timestamp(self) -> str:
        """현재 시간 반환"""
        from datetime import datetime
        return datetime.now().isoformat() + "Z"
    
    def get_template_directory(self) -> str:
        """템플릿 디렉토리 경로 반환"""
        return str(self.excel_templates_path)
    
    def create_template_directory(self, template_type: str) -> str:
        """템플릿 타입별 디렉토리 생성"""
        template_dir = self.excel_templates_path / template_type
        template_dir.mkdir(parents=True, exist_ok=True)
        return str(template_dir)


# 전역 템플릿 매니저 인스턴스
template_manager = TemplateManager()
