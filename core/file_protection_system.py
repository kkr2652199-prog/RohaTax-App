"""
AI 실수 방지 파일 보호 시스템
- 파일 중요도 분류 및 보호
- AI 판단 검증 시스템
- 안전한 파일 삭제 관리
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import hashlib

class FileProtectionSystem:
    """파일 보호 및 AI 실수 방지 시스템"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.protection_db_path = "core/file_protection_db.json"
        self.protection_db = self._load_protection_db()
        
        # 현재 상태 파일들 (수정 금지)
        self.protected_files = {
            'core/file_parser.py': '현재 상태 유지',
            'routes/conversion.py': '현재 상태 유지', 
            'static/js/conversion.js': '현재 상태 유지',
            'static/css/conversion.css': '현재 상태 유지',
            'core/conversion_engine.py': '현재 상태 유지',
            'core/file_manager.py': '현재 상태 유지',
            'core/recipient_extractor/main_extractor.py': '현재 상태 유지',
            'routes/conversion_original.py': '현재 상태 유지',
            'static/js/conversion_original.js': '현재 상태 유지',
            'static/css/conversion_original.css': '현재 상태 유지',
            'static/css/conversion_part01.css': '현재 상태 유지',
            'static/js/conversion_part01.js': '현재 상태 유지',
            '절대지침/검증규칙/데이터검증규칙.md': '현재 상태 유지',
            '절대지침/공급받는자정보관리지침/공급받는자_통합관리_절대지침.md': '현재 상태 유지',
            '절대지침/업종별절대지침/배달대행사_정산서_절대지침.md': '현재 상태 유지',
            'config/industry_config.json': '현재 상태 유지',
            'backup_files/conversion_engine_original.py': '현재 상태 유지',
            'backup_files/file_manager_original.py': '현재 상태 유지',
            'backup_files/file_parser_original.py': '현재 상태 유지',
            'core/recipient_extractor/main_extractor_original.py': '현재 상태 유지'
        }
        
        # 분할 관리 규칙
        self.split_rules = {
            'max_lines': {
                'py': 500,
                'js': 400, 
                'css': 400,
                'md': 300,
                'json': 200
            },
            'naming_pattern': '{name}_part{number:02d}.{ext}',
            'linker_pattern': '{name}_linker.{ext}'
        }
        
        # 새 파일 생성 시 자동 분할 적용
        self.auto_split_enabled = True
        
        # 파일 중요도 분류 기준
        self.importance_levels = {
            "🔴 중요": {
                "description": "절대 삭제 금지 파일",
                "score": 100,
                "patterns": [
                    "app.py", "main.py", "run.py",
                    "core/", "routes/", "templates/",
                    "static/", "config/", "database/",
                    "절대지침/", "*.db", "*.sqlite",
                    "requirements.txt", "README.md"
                ],
                "auto_backup": True,
                "user_confirmation": True
            },
            "🟡 일반": {
                "description": "백업 후 삭제 가능 파일",
                "score": 50,
                "patterns": [
                    "temp/", "cache/", "logs/",
                    "backup_files/", "*.log", "*.tmp",
                    "*.bak", "*.old"
                ],
                "auto_backup": True,
                "user_confirmation": False
            },
            "🟢 안전": {
                "description": "자유롭게 삭제 가능 파일",
                "score": 10,
                "patterns": [
                    "__pycache__/", "*.pyc", "*.pyo",
                    ".DS_Store", "Thumbs.db", "*.swp",
                    "*.swo", "*~"
                ],
                "auto_backup": False,
                "user_confirmation": False
            }
        }
        
        self.logger.info("파일 보호 시스템 초기화 완료")
    
    def _load_protection_db(self) -> Dict[str, Any]:
        """보호 데이터베이스 로드"""
        if os.path.exists(self.protection_db_path):
            try:
                with open(self.protection_db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"보호 DB 로드 실패: {e}")
        
        return {
            "protected_files": {},
            "deletion_history": [],
            "ai_judgments": [],
            "last_updated": datetime.now().isoformat()
        }
    
    def _save_protection_db(self):
        """보호 데이터베이스 저장"""
        try:
            self.protection_db["last_updated"] = datetime.now().isoformat()
            with open(self.protection_db_path, 'w', encoding='utf-8') as f:
                json.dump(self.protection_db, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"보호 DB 저장 실패: {e}")
    
    def classify_file_importance(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """파일 중요도 분류"""
        file_path = str(file_path)
        
        # 이미 분류된 파일인지 확인
        if file_path in self.protection_db["protected_files"]:
            cached = self.protection_db["protected_files"][file_path]
            return cached["level"], cached
        
        # 중요도 패턴 매칭
        for level, config in self.importance_levels.items():
            for pattern in config["patterns"]:
                if self._match_pattern(file_path, pattern):
                    classification = {
                        "level": level,
                        "score": config["score"],
                        "description": config["description"],
                        "auto_backup": config["auto_backup"],
                        "user_confirmation": config["user_confirmation"],
                        "pattern_matched": pattern,
                        "classified_at": datetime.now().isoformat()
                    }
                    
                    # 캐시에 저장
                    self.protection_db["protected_files"][file_path] = classification
                    self._save_protection_db()
                    
                    self.logger.info(f"파일 분류: {file_path} → {level}")
                    return level, classification
        
        # 기본값: 일반 파일
        default_classification = {
            "level": "🟡 일반",
            "score": 50,
            "description": "기본 일반 파일",
            "auto_backup": True,
            "user_confirmation": False,
            "pattern_matched": "default",
            "classified_at": datetime.now().isoformat()
        }
        
        self.protection_db["protected_files"][file_path] = default_classification
        self._save_protection_db()
        
        return "🟡 일반", default_classification
    
    def _match_pattern(self, file_path: str, pattern: str) -> bool:
        """패턴 매칭 (간단한 와일드카드 지원)"""
        import fnmatch
        return fnmatch.fnmatch(file_path, pattern) or fnmatch.fnmatch(os.path.basename(file_path), pattern)
    
    def validate_ai_judgment(self, file_path: str, ai_judgment: str, confidence: float = 0.0) -> Dict[str, Any]:
        """AI 판단 검증"""
        importance_level, classification = self.classify_file_importance(file_path)
        
        validation_result = {
            "file_path": file_path,
            "ai_judgment": ai_judgment,
            "ai_confidence": confidence,
            "importance_level": importance_level,
            "classification": classification,
            "validation_score": self._calculate_validation_score(ai_judgment, importance_level, confidence),
            "recommendation": self._get_recommendation(importance_level, confidence),
            "requires_user_confirmation": classification["user_confirmation"],
            "timestamp": datetime.now().isoformat()
        }
        
        # AI 판단 기록 저장
        self.protection_db["ai_judgments"].append(validation_result)
        self._save_protection_db()
        
        self.logger.info(f"AI 판단 검증: {file_path} → {validation_result['recommendation']}")
        return validation_result
    
    def _calculate_validation_score(self, ai_judgment: str, importance_level: str, confidence: float) -> float:
        """검증 점수 계산"""
        base_score = 50.0
        
        # 중요도에 따른 가중치
        importance_weights = {
            "🔴 중요": 0.8,  # 중요 파일은 더 엄격하게 검증
            "🟡 일반": 1.0,  # 일반 파일은 기본 검증
            "🟢 안전": 1.2   # 안전 파일은 관대하게 검증
        }
        
        weight = importance_weights.get(importance_level, 1.0)
        
        # AI 신뢰도 반영
        confidence_factor = confidence * 0.5
        
        # 최종 점수 계산
        final_score = (base_score * weight) + confidence_factor
        
        return min(100.0, max(0.0, final_score))
    
    def _get_recommendation(self, importance_level: str, confidence: float) -> str:
        """권장사항 결정"""
        if importance_level == "🔴 중요":
            if confidence < 0.9:
                return "사용자 확인 필요 - 중요 파일입니다"
            else:
                return "신중한 검토 후 진행"
        elif importance_level == "🟡 일반":
            if confidence < 0.7:
                return "백업 후 진행 권장"
            else:
                return "안전하게 진행 가능"
        else:  # 🟢 안전
            return "자유롭게 진행 가능"
    
    def can_delete_file(self, file_path: str, ai_judgment: str = "", confidence: float = 0.0) -> Dict[str, Any]:
        """파일 삭제 가능 여부 확인"""
        validation = self.validate_ai_judgment(file_path, ai_judgment, confidence)
        
        result = {
            "can_delete": False,
            "requires_backup": False,
            "requires_confirmation": False,
            "reason": "",
            "validation": validation
        }
        
        importance_level = validation["importance_level"]
        
        if importance_level == "🔴 중요":
            result["can_delete"] = False
            result["requires_confirmation"] = True
            result["reason"] = "중요 파일은 삭제할 수 없습니다"
        elif importance_level == "🟡 일반":
            result["can_delete"] = True
            result["requires_backup"] = True
            result["reason"] = "백업 후 삭제 가능"
        else:  # 🟢 안전
            result["can_delete"] = True
            result["reason"] = "안전하게 삭제 가능"
        
        return result
    
    def log_deletion_attempt(self, file_path: str, ai_judgment: str, user_confirmed: bool = False):
        """삭제 시도 기록"""
        deletion_record = {
            "file_path": file_path,
            "ai_judgment": ai_judgment,
            "user_confirmed": user_confirmed,
            "timestamp": datetime.now().isoformat(),
            "success": False  # 실제 삭제는 별도 함수에서 처리
        }
        
        self.protection_db["deletion_history"].append(deletion_record)
        self._save_protection_db()
        
        self.logger.info(f"삭제 시도 기록: {file_path} (사용자 승인: {user_confirmed})")
    
    def get_protection_status(self) -> Dict[str, Any]:
        """보호 시스템 상태 조회"""
        return {
            "total_protected_files": len(self.protection_db["protected_files"]),
            "deletion_attempts": len(self.protection_db["deletion_history"]),
            "ai_judgments": len(self.protection_db["ai_judgments"]),
            "importance_levels": list(self.importance_levels.keys()),
            "last_updated": self.protection_db["last_updated"]
        }
    
    def get_file_protection_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """특정 파일의 보호 정보 조회"""
        if file_path in self.protection_db["protected_files"]:
            return self.protection_db["protected_files"][file_path]
        return None
    
    # ==================== 파일 분할 관리 시스템 ====================
    
    def is_protected_file(self, file_path: str) -> bool:
        """현재 상태 파일인지 확인"""
        return file_path in self.protected_files
    
    def should_split_file(self, file_path: str, line_count: int) -> bool:
        """파일 분할이 필요한지 확인"""
        if self.is_protected_file(file_path):
            return False  # 보호된 파일은 분할하지 않음
            
        ext = file_path.split('.')[-1]
        max_lines = self.split_rules['max_lines'].get(ext, 500)
        
        return line_count > max_lines
    
    def generate_split_names(self, file_path: str) -> Dict[str, str]:
        """분할 파일명 생성"""
        base_name = file_path.rsplit('.', 1)[0]
        ext = file_path.split('.')[-1]
        
        return {
            'part01': f"{base_name}_part01.{ext}",
            'part02': f"{base_name}_part02.{ext}",
            'linker': f"{base_name}_linker.{ext}"
        }
    
    def create_split_files(self, file_path: str, content: str) -> Optional[Dict[str, str]]:
        """파일을 자동으로 분할"""
        if not self.should_split_file(file_path, len(content.split('\n'))):
            return None
            
        lines = content.split('\n')
        ext = file_path.split('.')[-1]
        max_lines = self.split_rules['max_lines'].get(ext, 500)
        
        # 분할 파일들 생성
        split_files = {}
        for i, start_line in enumerate(range(0, len(lines), max_lines), 1):
            end_line = min(start_line + max_lines, len(lines))
            part_content = '\n'.join(lines[start_line:end_line])
            
            part_name = f"{file_path.rsplit('.', 1)[0]}_part{i:02d}.{ext}"
            split_files[part_name] = part_content
            
        # 링커 파일 생성
        linker_content = self._generate_linker_content(file_path, split_files)
        linker_name = f"{file_path.rsplit('.', 1)[0]}_linker.{ext}"
        split_files[linker_name] = linker_content
        
        return split_files
    
    def _generate_linker_content(self, original_file: str, split_files: Dict[str, str]) -> str:
        """링커 파일 내용 생성"""
        ext = original_file.split('.')[-1]
        
        if ext == 'py':
            return self._generate_python_linker(original_file, split_files)
        elif ext == 'js':
            return self._generate_javascript_linker(original_file, split_files)
        elif ext == 'css':
            return self._generate_css_linker(original_file, split_files)
        else:
            return self._generate_generic_linker(original_file, split_files)
    
    def _generate_python_linker(self, original_file: str, split_files: Dict[str, str]) -> str:
        """Python 링커 파일 생성"""
        linker_content = f'''"""
{original_file} 링커 파일
분할된 파일들을 통합하여 원본 기능을 제공합니다.
"""
'''
        for part_file in split_files.keys():
            if part_file.endswith('_linker.py'):
                continue
            module_name = part_file.replace('.py', '').replace('/', '.')
            linker_content += f"from {module_name} import *\n"
            
        return linker_content
    
    def _generate_javascript_linker(self, original_file: str, split_files: Dict[str, str]) -> str:
        """JavaScript 링커 파일 생성"""
        linker_content = f'''/**
 * {original_file} 링커 파일
 * 분할된 파일들을 통합하여 원본 기능을 제공합니다.
 */
'''
        for part_file in split_files.keys():
            if part_file.endswith('_linker.js'):
                continue
            linker_content += f"// {part_file} 내용 포함\n"
            
        return linker_content
    
    def _generate_css_linker(self, original_file: str, split_files: Dict[str, str]) -> str:
        """CSS 링커 파일 생성"""
        linker_content = f'''/*
 * {original_file} 링커 파일
 * 분할된 파일들을 통합하여 원본 기능을 제공합니다.
 */
'''
        for part_file in split_files.keys():
            if part_file.endswith('_linker.css'):
                continue
            linker_content += f"/* {part_file} 내용 포함 */\n"
            
        return linker_content
    
    def _generate_generic_linker(self, original_file: str, split_files: Dict[str, str]) -> str:
        """일반 파일 링커 생성"""
        return f'''/*
 * {original_file} 링커 파일
 * 분할된 파일들을 통합하여 원본 기능을 제공합니다.
 * 
 * 분할된 파일들:
 * {chr(10).join(f" * - {part}" for part in split_files.keys() if not part.endswith('_linker'))}
 */
'''
    
    def validate_new_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """새 파일 생성 시 분할 검증"""
        lines = content.split('\n')
        line_count = len(lines)
        
        result = {
            "file_path": file_path,
            "line_count": line_count,
            "needs_split": False,
            "split_files": None,
            "is_protected": False,
            "recommendation": ""
        }
        
        # 보호된 파일인지 확인
        if self.is_protected_file(file_path):
            result["is_protected"] = True
            result["recommendation"] = "현재 상태 파일 - 수정 금지"
            return result
        
        # 분할 필요 여부 확인
        if self.should_split_file(file_path, line_count):
            result["needs_split"] = True
            result["split_files"] = self.create_split_files(file_path, content)
            result["recommendation"] = f"파일 크기 초과 ({line_count}줄) - 자동 분할 적용"
        else:
            result["recommendation"] = "정상 크기 - 분할 불필요"
        
        return result
    
    def get_split_management_status(self) -> Dict[str, Any]:
        """분할 관리 시스템 상태 조회"""
        return {
            "protected_files_count": len(self.protected_files),
            "auto_split_enabled": self.auto_split_enabled,
            "split_rules": self.split_rules,
            "protected_files": list(self.protected_files.keys())
        }

# 전역 인스턴스
file_protection_system = FileProtectionSystem()

