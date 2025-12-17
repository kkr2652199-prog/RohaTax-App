"""
자동 파일 분할 시스템
- 새 파일 생성 시 자동으로 크기 체크
- 권장 크기 초과 시 자동 분할
- 현재 상태 파일은 보호
"""

import os
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from core.file_protection_system import file_protection_system

class AutoFileSplitter:
    """자동 파일 분할 시스템"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.protection_system = file_protection_system
        self.split_history = []
        
    def create_file_with_split_check(self, file_path: str, content: str, force_split: bool = False) -> Dict[str, Any]:
        """파일 생성 시 자동 분할 체크"""
        
        # 파일 검증
        validation = self.protection_system.validate_new_file(file_path, content)
        
        result = {
            "success": False,
            "file_path": file_path,
            "files_created": [],
            "validation": validation,
            "message": ""
        }
        
        # 보호된 파일인 경우
        if validation["is_protected"]:
            result["message"] = f"보호된 파일 - 수정 금지: {file_path}"
            self.logger.warning(f"보호된 파일 수정 시도: {file_path}")
            return result
        
        # 분할이 필요한 경우
        if validation["needs_split"] or force_split:
            return self._create_split_files(file_path, content, validation)
        
        # 일반 파일 생성
        try:
            self._ensure_directory_exists(file_path)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            result["success"] = True
            result["files_created"] = [file_path]
            result["message"] = f"파일 생성 완료: {file_path}"
            
            self.logger.info(f"파일 생성: {file_path}")
            
        except Exception as e:
            result["message"] = f"파일 생성 실패: {str(e)}"
            self.logger.error(f"파일 생성 실패: {file_path} - {str(e)}")
        
        return result
    
    def _create_split_files(self, file_path: str, content: str, validation: Dict[str, Any]) -> Dict[str, Any]:
        """분할 파일들 생성"""
        result = {
            "success": False,
            "file_path": file_path,
            "files_created": [],
            "validation": validation,
            "message": ""
        }
        
        try:
            split_files = validation["split_files"]
            if not split_files:
                result["message"] = "분할 파일 생성 실패"
                return result
            
            # 분할 파일들 생성
            for split_file_path, split_content in split_files.items():
                self._ensure_directory_exists(split_file_path)
                with open(split_file_path, 'w', encoding='utf-8') as f:
                    f.write(split_content)
                
                result["files_created"].append(split_file_path)
                self.logger.info(f"분할 파일 생성: {split_file_path}")
            
            result["success"] = True
            result["message"] = f"분할 파일 생성 완료: {len(result['files_created'])}개 파일"
            
            # 분할 기록 저장
            self.split_history.append({
                "original_file": file_path,
                "split_files": list(split_files.keys()),
                "timestamp": self._get_timestamp(),
                "line_count": validation["line_count"]
            })
            
        except Exception as e:
            result["message"] = f"분할 파일 생성 실패: {str(e)}"
            self.logger.error(f"분할 파일 생성 실패: {file_path} - {str(e)}")
        
        return result
    
    def _ensure_directory_exists(self, file_path: str):
        """디렉토리가 존재하지 않으면 생성"""
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
    
    def _get_timestamp(self) -> str:
        """현재 시간 문자열 반환"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def get_split_recommendation(self, file_path: str, content: str) -> Dict[str, Any]:
        """파일 분할 권장사항 조회"""
        validation = self.protection_system.validate_new_file(file_path, content)
        
        recommendation = {
            "file_path": file_path,
            "line_count": validation["line_count"],
            "needs_split": validation["needs_split"],
            "is_protected": validation["is_protected"],
            "recommendation": validation["recommendation"],
            "split_files": None,
            "action": ""
        }
        
        if validation["is_protected"]:
            recommendation["action"] = "현재 상태 파일 - 수정 금지"
        elif validation["needs_split"]:
            recommendation["action"] = "자동 분할 적용"
            recommendation["split_files"] = validation["split_files"]
        else:
            recommendation["action"] = "정상 크기 - 분할 불필요"
        
        return recommendation
    
    def get_split_history(self) -> List[Dict[str, Any]]:
        """분할 기록 조회"""
        return self.split_history
    
    def get_split_status(self) -> Dict[str, Any]:
        """분할 시스템 상태 조회"""
        return {
            "total_splits": len(self.split_history),
            "protection_system_status": self.protection_system.get_split_management_status(),
            "recent_splits": self.split_history[-5:] if self.split_history else []
        }
    
    def validate_existing_files(self, directory: str = ".") -> Dict[str, Any]:
        """기존 파일들의 분할 필요성 검증"""
        results = {
            "protected_files": [],
            "needs_split": [],
            "normal_files": [],
            "total_files": 0
        }
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file).replace('\\', '/')
                ext = file_path.split('.')[-1]
                
                # 감시 대상 파일만 체크
                if ext not in ['py', 'js', 'css', 'html', 'md', 'json']:
                    continue
                
                results["total_files"] += 1
                
                # 보호된 파일인지 확인
                if self.protection_system.is_protected_file(file_path):
                    results["protected_files"].append(file_path)
                    continue
                
                # 파일 크기 체크
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    validation = self.protection_system.validate_new_file(file_path, content)
                    
                    if validation["needs_split"]:
                        results["needs_split"].append({
                            "file": file_path,
                            "line_count": validation["line_count"],
                            "recommendation": validation["recommendation"]
                        })
                    else:
                        results["normal_files"].append(file_path)
                        
                except Exception as e:
                    self.logger.warning(f"파일 검증 실패: {file_path} - {str(e)}")
        
        return results

# 전역 인스턴스
auto_file_splitter = AutoFileSplitter()

