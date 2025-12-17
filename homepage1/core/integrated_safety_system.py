"""
AI 실수 방지 통합 안전장치 시스템
- 모든 보호 시스템 통합 관리
- 사용자 인터페이스 제공
- 실시간 모니터링 및 알림
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

# 보호 시스템들 import
from .file_protection_system import file_protection_system
from .ai_judgment_validator import ai_judgment_validator
from .safe_file_deletion_system import safe_file_deletion_system
from .auto_recovery_system import auto_recovery_system
from .auto_backup_manager import auto_backup_manager

class IntegratedSafetySystem:
    """통합 안전장치 시스템"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 하위 시스템들
        self.file_protection = file_protection_system
        self.ai_validator = ai_judgment_validator
        self.deletion_system = safe_file_deletion_system
        self.recovery_system = auto_recovery_system
        self.backup_manager = auto_backup_manager
        
        # 통합 설정
        self.safety_settings = {
            "ai_safety_enabled": True,
            "auto_backup_enabled": True,
            "recovery_enabled": True,
            "user_confirmation_required": True,
            "notification_enabled": True,
            "monitoring_enabled": True
        }
        
        self.logger.info("통합 안전장치 시스템 초기화 완료")
    
    def analyze_file_safety(self, file_path: str, ai_judgment: str = "", ai_confidence: float = 0.0) -> Dict[str, Any]:
        """파일 안전성 종합 분석"""
        try:
            # 1. 파일 중요도 분류
            importance_level, classification = self.file_protection.classify_file_importance(file_path)
            
            # 2. AI 판단 검증
            validation_result = self.ai_validator.validate_ai_judgment(file_path, ai_judgment, ai_confidence)
            
            # 3. 삭제 가능성 확인
            deletion_check = self.deletion_system.can_delete_file(file_path, ai_judgment, ai_confidence)
            
            # 4. 백업 상태 확인
            backup_status = self.backup_manager.get_backup_status()
            
            # 종합 분석 결과
            safety_analysis = {
                "file_path": file_path,
                "timestamp": datetime.now().isoformat(),
                "importance_level": importance_level,
                "classification": classification,
                "ai_validation": validation_result,
                "deletion_check": deletion_check,
                "backup_status": backup_status,
                "overall_risk": self._calculate_overall_risk(importance_level, validation_result, deletion_check),
                "recommendations": self._generate_recommendations(importance_level, validation_result, deletion_check),
                "safety_score": self._calculate_safety_score(importance_level, validation_result, deletion_check)
            }
            
            self.logger.info(f"파일 안전성 분석 완료: {file_path} → 위험도: {safety_analysis['overall_risk']}")
            return safety_analysis
            
        except Exception as e:
            self.logger.error(f"파일 안전성 분석 실패: {e}")
            return {
                "file_path": file_path,
                "error": str(e),
                "overall_risk": "critical",
                "recommendations": ["시스템 오류로 인해 수동 확인이 필요합니다"]
            }
    
    def _calculate_overall_risk(self, importance_level: str, validation_result: Dict[str, Any], deletion_check: Dict[str, Any]) -> str:
        """전체 위험도 계산"""
        risk_factors = []
        
        # 중요도 기반 위험도
        if importance_level == "🔴 중요":
            risk_factors.append("high")
        elif importance_level == "🟡 일반":
            risk_factors.append("medium")
        else:
            risk_factors.append("low")
        
        # AI 검증 기반 위험도
        if validation_result["overall_score"] < 40:
            risk_factors.append("high")
        elif validation_result["overall_score"] < 70:
            risk_factors.append("medium")
        else:
            risk_factors.append("low")
        
        # 삭제 가능성 기반 위험도
        if not deletion_check["can_delete"]:
            risk_factors.append("low")
        elif deletion_check["requires_confirmation"]:
            risk_factors.append("medium")
        else:
            risk_factors.append("high")
        
        # 위험도 결정
        if "high" in risk_factors:
            return "high"
        elif "medium" in risk_factors:
            return "medium"
        else:
            return "low"
    
    def _generate_recommendations(self, importance_level: str, validation_result: Dict[str, Any], deletion_check: Dict[str, Any]) -> List[str]:
        """권장사항 생성"""
        recommendations = []
        
        # 중요도 기반 권장사항
        if importance_level == "🔴 중요":
            recommendations.append("중요 파일이므로 신중한 검토가 필요합니다")
            recommendations.append("삭제 전 반드시 백업을 생성하세요")
        
        # AI 검증 기반 권장사항
        if validation_result["requires_human_review"]:
            recommendations.append("AI 판단에 의문이 있으므로 사용자 확인이 필요합니다")
        
        if validation_result["overall_score"] < 60:
            recommendations.append("AI 판단의 신뢰도가 낮으므로 수동 검토를 권장합니다")
        
        # 삭제 가능성 기반 권장사항
        if deletion_check["requires_backup"]:
            recommendations.append("삭제 전 자동 백업이 생성됩니다")
        
        if deletion_check["requires_confirmation"]:
            recommendations.append("사용자 승인이 필요합니다")
        
        return recommendations
    
    def _calculate_safety_score(self, importance_level: str, validation_result: Dict[str, Any], deletion_check: Dict[str, Any]) -> float:
        """안전 점수 계산 (0-100)"""
        base_score = 50.0
        
        # 중요도 기반 점수 조정
        if importance_level == "🔴 중요":
            base_score += 30  # 중요 파일은 높은 점수
        elif importance_level == "🟡 일반":
            base_score += 10  # 일반 파일은 중간 점수
        else:
            base_score -= 10  # 안전 파일은 낮은 점수
        
        # AI 검증 점수 반영
        ai_score = validation_result["overall_score"]
        base_score = (base_score + ai_score) / 2
        
        # 삭제 가능성 점수 반영
        if not deletion_check["can_delete"]:
            base_score += 20  # 삭제 불가능하면 안전
        elif deletion_check["requires_confirmation"]:
            base_score += 10  # 승인 필요하면 중간 안전
        
        return min(100.0, max(0.0, base_score))
    
    def safe_file_operation(self, operation: str, file_path: str, ai_judgment: str = "", 
                           ai_confidence: float = 0.0, user_confirmed: bool = False) -> Dict[str, Any]:
        """안전한 파일 작업 실행"""
        try:
            # 안전성 분석
            safety_analysis = self.analyze_file_safety(file_path, ai_judgment, ai_confidence)
            
            # 작업별 처리
            if operation == "delete":
                return self._safe_delete_file(file_path, ai_judgment, ai_confidence, user_confirmed, safety_analysis)
            elif operation == "modify":
                return self._safe_modify_file(file_path, ai_judgment, ai_confidence, user_confirmed, safety_analysis)
            elif operation == "move":
                return self._safe_move_file(file_path, ai_judgment, ai_confidence, user_confirmed, safety_analysis)
            else:
                return {
                    "success": False,
                    "reason": f"지원하지 않는 작업입니다: {operation}"
                }
                
        except Exception as e:
            self.logger.error(f"안전한 파일 작업 실패: {e}")
            return {
                "success": False,
                "reason": f"작업 중 오류 발생: {str(e)}"
            }
    
    def _safe_delete_file(self, file_path: str, ai_judgment: str, ai_confidence: float, 
                         user_confirmed: bool, safety_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """안전한 파일 삭제"""
        # 삭제 요청 생성
        deletion_request = self.deletion_system.request_file_deletion(file_path, ai_judgment, ai_confidence)
        
        if not deletion_request["success"]:
            return deletion_request
        
        # 사용자 승인 필요 시
        if deletion_request["requires_confirmation"] and not user_confirmed:
            return {
                "success": False,
                "reason": "사용자 승인이 필요합니다",
                "deletion_id": deletion_request["deletion_id"],
                "requires_confirmation": True,
                "safety_analysis": safety_analysis
            }
        
        # 삭제 승인 처리
        if deletion_request["deletion_id"]:
            confirmation_result = self.deletion_system.confirm_deletion(
                deletion_request["deletion_id"], 
                user_confirmed, 
                f"AI 판단: {ai_judgment}"
            )
            
            if confirmation_result["success"]:
                # 복구 시스템에 등록
                self.recovery_system.register_file_for_recovery(
                    file_path,
                    confirmation_result["backup_path"],
                    deletion_request["deletion_id"],
                    f"AI 판단에 의한 삭제: {ai_judgment}"
                )
            
            return confirmation_result
        
        return deletion_request
    
    def _safe_modify_file(self, file_path: str, ai_judgment: str, ai_confidence: float, 
                         user_confirmed: bool, safety_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """안전한 파일 수정"""
        # 수정 전 백업 생성
        backup_path = self.backup_manager.create_backup(file_path, description=f"수정 전 백업: {ai_judgment}")
        
        if not backup_path:
            return {
                "success": False,
                "reason": "백업 생성 실패로 수정을 중단합니다"
            }
        
        # 복구 시스템에 등록
        self.recovery_system.register_file_for_recovery(
            file_path,
            backup_path,
            f"MODIFY_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            f"AI 판단에 의한 수정: {ai_judgment}"
        )
        
        return {
            "success": True,
            "reason": "파일 수정을 위한 백업이 생성되었습니다",
            "backup_path": backup_path,
            "safety_analysis": safety_analysis
        }
    
    def _safe_move_file(self, file_path: str, ai_judgment: str, ai_confidence: float, 
                       user_confirmed: bool, safety_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """안전한 파일 이동"""
        # 이동 전 백업 생성
        backup_path = self.backup_manager.create_backup(file_path, description=f"이동 전 백업: {ai_judgment}")
        
        if not backup_path:
            return {
                "success": False,
                "reason": "백업 생성 실패로 이동을 중단합니다"
            }
        
        return {
            "success": True,
            "reason": "파일 이동을 위한 백업이 생성되었습니다",
            "backup_path": backup_path,
            "safety_analysis": safety_analysis
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """전체 시스템 상태 조회"""
        return {
            "safety_settings": self.safety_settings,
            "file_protection": self.file_protection.get_protection_status(),
            "ai_validator": self.ai_validator.get_ai_performance_stats(),
            "deletion_system": self.deletion_system.get_system_status(),
            "recovery_system": self.recovery_system.get_recovery_status(),
            "backup_manager": self.backup_manager.get_backup_status(),
            "last_updated": datetime.now().isoformat()
        }
    
    def emergency_recovery(self, file_path: str) -> Dict[str, Any]:
        """긴급 복구"""
        try:
            # 최신 백업 찾기
            latest_backup = self.backup_manager.get_latest_backup(file_path)
            
            if not latest_backup:
                return {
                    "success": False,
                    "reason": "복구할 백업을 찾을 수 없습니다"
                }
            
            # 복구 실행
            recovery_result = self.recovery_system.manual_recovery(
                file_path,
                latest_backup["backup_path"],
                "emergency_recovery"
            )
            
            return recovery_result
            
        except Exception as e:
            self.logger.error(f"긴급 복구 실패: {e}")
            return {
                "success": False,
                "reason": f"긴급 복구 중 오류 발생: {str(e)}"
            }
    
    def cleanup_system(self):
        """시스템 정리"""
        try:
            # 백업 정리
            self.backup_manager.cleanup_duplicate_backups()
            
            # 복구 시스템 정리
            self.recovery_system.cleanup_old_recovery_data()
            
            # 삭제 시스템 정리
            self.deletion_system.cleanup_old_backups()
            
            self.logger.info("시스템 정리 완료")
            
        except Exception as e:
            self.logger.error(f"시스템 정리 실패: {e}")

# 전역 인스턴스
integrated_safety_system = IntegratedSafetySystem()







