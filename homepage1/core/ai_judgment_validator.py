"""
AI 판단 검증 및 이중 검증 시스템
- AI 판단 신뢰도 평가
- 이중 검증 시스템
- 안전한 파일 관리
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import hashlib
import difflib

class AIJudgmentValidator:
    """AI 판단 검증 시스템"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.validation_db_path = "core/ai_validation_db.json"
        self.validation_db = self._load_validation_db()
        
        # AI 판단 신뢰도 기준
        self.confidence_thresholds = {
            "high": 0.9,      # 높은 신뢰도
            "medium": 0.7,    # 중간 신뢰도
            "low": 0.5,       # 낮은 신뢰도
            "very_low": 0.3   # 매우 낮은 신뢰도
        }
        
        # 검증 규칙
        self.validation_rules = {
            "duplicate_detection": {
                "description": "중복 파일 감지 검증",
                "weight": 0.3,
                "checks": [
                    "file_size_comparison",
                    "content_hash_comparison",
                    "filename_similarity",
                    "directory_structure"
                ]
            },
            "importance_assessment": {
                "description": "파일 중요도 평가",
                "weight": 0.4,
                "checks": [
                    "file_extension_analysis",
                    "directory_location",
                    "file_size_significance",
                    "usage_frequency"
                ]
            },
            "safety_verification": {
                "description": "안전성 검증",
                "weight": 0.3,
                "checks": [
                    "system_file_protection",
                    "dependency_analysis",
                    "backup_availability",
                    "recovery_possibility"
                ]
            }
        }
        
        self.logger.info("AI 판단 검증 시스템 초기화 완료")
    
    def _load_validation_db(self) -> Dict[str, Any]:
        """검증 데이터베이스 로드"""
        if os.path.exists(self.validation_db_path):
            try:
                with open(self.validation_db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"검증 DB 로드 실패: {e}")
        
        return {
            "validation_history": [],
            "ai_performance": {},
            "false_positives": [],
            "false_negatives": [],
            "last_updated": datetime.now().isoformat()
        }
    
    def _save_validation_db(self):
        """검증 데이터베이스 저장"""
        try:
            self.validation_db["last_updated"] = datetime.now().isoformat()
            with open(self.validation_db_path, 'w', encoding='utf-8') as f:
                json.dump(self.validation_db, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"검증 DB 저장 실패: {e}")
    
    def validate_ai_judgment(self, file_path: str, ai_judgment: str, ai_confidence: float = 0.0) -> Dict[str, Any]:
        """AI 판단 종합 검증"""
        validation_result = {
            "file_path": file_path,
            "ai_judgment": ai_judgment,
            "ai_confidence": ai_confidence,
            "timestamp": datetime.now().isoformat(),
            "validation_scores": {},
            "overall_score": 0.0,
            "recommendation": "",
            "requires_human_review": False,
            "risk_level": "low"
        }
        
        # 각 검증 규칙별 점수 계산
        for rule_name, rule_config in self.validation_rules.items():
            score = self._calculate_rule_score(file_path, ai_judgment, rule_name, rule_config)
            validation_result["validation_scores"][rule_name] = score
        
        # 전체 점수 계산
        overall_score = self._calculate_overall_score(validation_result["validation_scores"])
        validation_result["overall_score"] = overall_score
        
        # 권장사항 결정
        validation_result["recommendation"] = self._get_validation_recommendation(overall_score, ai_confidence)
        validation_result["requires_human_review"] = self._requires_human_review(overall_score, ai_confidence)
        validation_result["risk_level"] = self._assess_risk_level(overall_score, ai_confidence)
        
        # 검증 기록 저장
        self.validation_db["validation_history"].append(validation_result)
        self._save_validation_db()
        
        self.logger.info(f"AI 판단 검증 완료: {file_path} → 점수: {overall_score:.2f}")
        return validation_result
    
    def _calculate_rule_score(self, file_path: str, ai_judgment: str, rule_name: str, rule_config: Dict[str, Any]) -> float:
        """특정 규칙의 점수 계산"""
        if rule_name == "duplicate_detection":
            return self._validate_duplicate_detection(file_path, ai_judgment)
        elif rule_name == "importance_assessment":
            return self._validate_importance_assessment(file_path, ai_judgment)
        elif rule_name == "safety_verification":
            return self._validate_safety_verification(file_path, ai_judgment)
        else:
            return 50.0  # 기본 점수
    
    def _validate_duplicate_detection(self, file_path: str, ai_judgment: str) -> float:
        """중복 감지 검증"""
        score = 50.0
        
        try:
            # 파일 크기 비교
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                if file_size == 0:
                    score += 20  # 빈 파일은 중복 가능성 높음
                elif file_size < 1024:  # 1KB 미만
                    score += 10  # 작은 파일은 중복 가능성 있음
            
            # 파일명 유사성 검사
            filename = os.path.basename(file_path)
            if any(keyword in filename.lower() for keyword in ['copy', 'duplicate', 'backup', 'old', 'temp']):
                score += 30  # 중복 관련 키워드 발견
            
            # 디렉토리 구조 분석
            if 'backup' in file_path.lower() or 'temp' in file_path.lower():
                score += 25  # 백업/임시 디렉토리
            
        except Exception as e:
            self.logger.error(f"중복 감지 검증 오류: {e}")
            score = 30.0  # 오류 시 낮은 점수
        
        return min(100.0, score)
    
    def _validate_importance_assessment(self, file_path: str, ai_judgment: str) -> float:
        """중요도 평가 검증"""
        score = 50.0
        
        try:
            # 파일 확장자 분석
            ext = os.path.splitext(file_path)[1].lower()
            important_extensions = ['.py', '.js', '.html', '.css', '.json', '.sql', '.md']
            if ext in important_extensions:
                score -= 20  # 중요한 확장자는 삭제 위험
            
            # 디렉토리 위치 분석
            if any(important_dir in file_path for important_dir in ['core/', 'routes/', 'templates/', 'static/', 'config/']):
                score -= 30  # 핵심 디렉토리는 삭제 위험
            
            # 파일 크기 중요성
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                if file_size > 1024 * 1024:  # 1MB 이상
                    score -= 15  # 큰 파일은 중요할 가능성
            
        except Exception as e:
            self.logger.error(f"중요도 평가 검증 오류: {e}")
            score = 30.0
        
        return max(0.0, score)
    
    def _validate_safety_verification(self, file_path: str, ai_judgment: str) -> float:
        """안전성 검증"""
        score = 50.0
        
        try:
            # 시스템 파일 보호
            system_files = ['app.py', 'main.py', 'run.py', 'requirements.txt', 'README.md']
            if any(sys_file in file_path for sys_file in system_files):
                score -= 40  # 시스템 파일은 매우 위험
            
            # 백업 가용성 확인
            backup_path = f"backups/{os.path.basename(file_path)}"
            if os.path.exists(backup_path):
                score += 20  # 백업 존재 시 안전
            
            # 복구 가능성 평가
            if 'delete' in ai_judgment.lower() and 'backup' not in ai_judgment.lower():
                score -= 25  # 백업 언급 없이 삭제 제안 시 위험
            
        except Exception as e:
            self.logger.error(f"안전성 검증 오류: {e}")
            score = 30.0
        
        return max(0.0, score)
    
    def _calculate_overall_score(self, validation_scores: Dict[str, float]) -> float:
        """전체 점수 계산"""
        total_score = 0.0
        total_weight = 0.0
        
        for rule_name, score in validation_scores.items():
            if rule_name in self.validation_rules:
                weight = self.validation_rules[rule_name]["weight"]
                total_score += score * weight
                total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 50.0
    
    def _get_validation_recommendation(self, overall_score: float, ai_confidence: float) -> str:
        """검증 권장사항 결정"""
        if overall_score >= 80 and ai_confidence >= 0.8:
            return "AI 판단이 신뢰할 만합니다. 안전하게 진행하세요."
        elif overall_score >= 60 and ai_confidence >= 0.6:
            return "AI 판단이 대체로 신뢰할 만합니다. 주의해서 진행하세요."
        elif overall_score >= 40:
            return "AI 판단에 의문이 있습니다. 사용자 확인이 필요합니다."
        else:
            return "AI 판단이 신뢰할 수 없습니다. 반드시 사용자 확인이 필요합니다."
    
    def _requires_human_review(self, overall_score: float, ai_confidence: float) -> bool:
        """인간 검토 필요 여부"""
        return overall_score < 60 or ai_confidence < 0.7
    
    def _assess_risk_level(self, overall_score: float, ai_confidence: float) -> str:
        """위험도 평가"""
        if overall_score >= 70 and ai_confidence >= 0.8:
            return "low"
        elif overall_score >= 50 and ai_confidence >= 0.6:
            return "medium"
        elif overall_score >= 30:
            return "high"
        else:
            return "critical"
    
    def record_false_positive(self, file_path: str, ai_judgment: str, actual_result: str):
        """거짓 양성 기록"""
        false_positive = {
            "file_path": file_path,
            "ai_judgment": ai_judgment,
            "actual_result": actual_result,
            "timestamp": datetime.now().isoformat()
        }
        
        self.validation_db["false_positives"].append(false_positive)
        self._save_validation_db()
        
        self.logger.warning(f"거짓 양성 기록: {file_path}")
    
    def record_false_negative(self, file_path: str, ai_judgment: str, actual_result: str):
        """거짓 음성 기록"""
        false_negative = {
            "file_path": file_path,
            "ai_judgment": ai_judgment,
            "actual_result": actual_result,
            "timestamp": datetime.now().isoformat()
        }
        
        self.validation_db["false_negatives"].append(false_negative)
        self._save_validation_db()
        
        self.logger.warning(f"거짓 음성 기록: {file_path}")
    
    def get_ai_performance_stats(self) -> Dict[str, Any]:
        """AI 성능 통계"""
        total_validations = len(self.validation_db["validation_history"])
        false_positives = len(self.validation_db["false_positives"])
        false_negatives = len(self.validation_db["false_negatives"])
        
        accuracy = 0.0
        if total_validations > 0:
            accuracy = ((total_validations - false_positives - false_negatives) / total_validations) * 100
        
        return {
            "total_validations": total_validations,
            "false_positives": false_positives,
            "false_negatives": false_negatives,
            "accuracy": accuracy,
            "precision": self._calculate_precision(),
            "recall": self._calculate_recall()
        }
    
    def _calculate_precision(self) -> float:
        """정밀도 계산"""
        false_positives = len(self.validation_db["false_positives"])
        total_validations = len(self.validation_db["validation_history"])
        
        if total_validations == 0:
            return 0.0
        
        true_positives = total_validations - false_positives
        return (true_positives / (true_positives + false_positives)) * 100 if (true_positives + false_positives) > 0 else 0.0
    
    def _calculate_recall(self) -> float:
        """재현율 계산"""
        false_negatives = len(self.validation_db["false_negatives"])
        total_validations = len(self.validation_db["validation_history"])
        
        if total_validations == 0:
            return 0.0
        
        true_positives = total_validations - false_negatives
        return (true_positives / (true_positives + false_negatives)) * 100 if (true_positives + false_negatives) > 0 else 0.0

# 전역 인스턴스
ai_judgment_validator = AIJudgmentValidator()














