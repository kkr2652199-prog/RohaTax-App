"""
파일 이동 검증 시스템
- 파일 이동 전 목적지 경로 유효성 검증
- 웹 접근성 검증
- 자동 복구 시스템
"""

import os
import shutil
import requests
import threading
import time
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import json

class FileValidator:
    """파일 이동 및 웹 접근성 검증 시스템"""
    
    def __init__(self, root_path: str, base_url: str = "http://localhost:8080"):
        self.root_path = root_path
        self.base_url = base_url
        self.validation_log = []
        self.recovery_log = []
        
        # 웹 접근 가능한 정적 파일 패턴
        self.web_accessible_patterns = {
            'css': ['*.css'],
            'js': ['*.js'],
            'images': ['*.png', '*.jpg', '*.jpeg', '*.gif', '*.ico', '*.svg'],
            'fonts': ['*.woff', '*.woff2', '*.ttf', '*.eot']
        }
        
        # 올바른 웹 경로 매핑
        self.web_path_mapping = {
            'css': '/static/css/',
            'js': '/static/js/',
            'images': '/static/images/',
            'fonts': '/static/fonts/'
        }
    
    def validate_destination_path(self, file_path: str, target_folder: str) -> Tuple[bool, str]:
        """파일 이동 전 목적지 경로 유효성 검증"""
        try:
            # 파일 확장자 확인
            file_ext = os.path.splitext(file_path)[1].lower()
            filename = os.path.basename(file_path)
            
            # 웹 접근 가능한 파일인지 확인
            is_web_file = False
            expected_subfolder = None
            
            for file_type, patterns in self.web_accessible_patterns.items():
                for pattern in patterns:
                    if filename.endswith(pattern.replace('*', '')):
                        is_web_file = True
                        expected_subfolder = file_type
                        break
                if is_web_file:
                    break
            
            # 웹 파일인 경우 올바른 하위 폴더로 이동해야 함
            if is_web_file and expected_subfolder:
                expected_path = os.path.join(target_folder, expected_subfolder)
                
                # 하위 폴더가 존재하는지 확인
                if not os.path.exists(expected_path):
                    return False, f"웹 파일 {filename}은 {expected_subfolder} 하위 폴더로 이동해야 합니다. 폴더가 존재하지 않습니다: {expected_path}"
                
                # 올바른 경로인지 확인
                if target_folder.endswith(expected_subfolder):
                    return True, f"올바른 경로: {expected_path}"
                else:
                    return False, f"웹 파일 {filename}은 {expected_subfolder} 하위 폴더로 이동해야 합니다. 현재 경로: {target_folder}"
            
            # 일반 파일인 경우 기본 검증
            if not os.path.exists(target_folder):
                return False, f"목적지 폴더가 존재하지 않습니다: {target_folder}"
            
            return True, f"유효한 목적지 경로: {target_folder}"
            
        except Exception as e:
            return False, f"경로 검증 중 오류 발생: {str(e)}"
    
    def validate_web_accessibility(self, file_path: str, target_path: str) -> Tuple[bool, str]:
        """정적 파일 이동 후 웹 접근 가능성 검증"""
        try:
            filename = os.path.basename(file_path)
            file_ext = os.path.splitext(filename)[1].lower()
            
            # 웹 접근 가능한 파일인지 확인
            web_type = None
            for file_type, patterns in self.web_accessible_patterns.items():
                for pattern in patterns:
                    if filename.endswith(pattern.replace('*', '')):
                        web_type = file_type
                        break
                if web_type:
                    break
            
            if not web_type:
                return True, f"웹 파일이 아님: {filename}"
            
            # 웹 URL 구성
            web_url = f"{self.base_url}{self.web_path_mapping[web_type]}{filename}"
            
            # 웹 접근 테스트
            try:
                response = requests.get(web_url, timeout=5)
                if response.status_code == 200:
                    return True, f"웹 접근 성공: {web_url}"
                else:
                    return False, f"웹 접근 실패 (HTTP {response.status_code}): {web_url}"
            except requests.RequestException as e:
                return False, f"웹 접근 테스트 실패: {web_url} - {str(e)}"
                
        except Exception as e:
            return False, f"웹 접근성 검증 중 오류 발생: {str(e)}"
    
    def auto_recover_file(self, file_path: str, failed_target: str) -> Tuple[bool, str]:
        """웹 접근 실패 시 자동으로 파일 위치 복구"""
        try:
            filename = os.path.basename(file_path)
            file_ext = os.path.splitext(filename)[1].lower()
            
            # 파일 타입 확인
            web_type = None
            for file_type, patterns in self.web_accessible_patterns.items():
                for pattern in patterns:
                    if filename.endswith(pattern.replace('*', '')):
                        web_type = file_type
                        break
                if web_type:
                    break
            
            if not web_type:
                return False, f"웹 파일이 아님: {filename}"
            
            # 올바른 복구 경로 생성
            correct_path = os.path.join(self.root_path, 'static', web_type, filename)
            
            # 올바른 폴더가 존재하는지 확인하고 생성
            correct_folder = os.path.dirname(correct_path)
            if not os.path.exists(correct_folder):
                os.makedirs(correct_folder, exist_ok=True)
            
            # 파일이 잘못된 위치에 있는지 확인
            if os.path.exists(failed_target):
                # 올바른 위치로 이동
                shutil.move(failed_target, correct_path)
                recovery_msg = f"파일 복구 완료: {failed_target} → {correct_path}"
                
                # 복구 로그 기록
                self.recovery_log.append({
                    'timestamp': datetime.now().isoformat(),
                    'original_path': file_path,
                    'failed_target': failed_target,
                    'recovered_path': correct_path,
                    'web_type': web_type,
                    'status': 'success'
                })
                
                return True, recovery_msg
            else:
                return False, f"복구할 파일이 존재하지 않음: {failed_target}"
                
        except Exception as e:
            error_msg = f"자동 복구 실패: {str(e)}"
            self.recovery_log.append({
                'timestamp': datetime.now().isoformat(),
                'original_path': file_path,
                'failed_target': failed_target,
                'error': error_msg,
                'status': 'failed'
            })
            return False, error_msg
    
    def log_validation(self, file_path: str, target_path: str, validation_result: bool, message: str):
        """검증 결과 로깅"""
        self.validation_log.append({
            'timestamp': datetime.now().isoformat(),
            'file_path': file_path,
            'target_path': target_path,
            'validation_result': validation_result,
            'message': message
        })
    
    def get_validation_summary(self) -> Dict:
        """검증 요약 정보 반환"""
        total_validations = len(self.validation_log)
        successful_validations = sum(1 for log in self.validation_log if log['validation_result'])
        failed_validations = total_validations - successful_validations
        
        total_recoveries = len(self.recovery_log)
        successful_recoveries = sum(1 for log in self.recovery_log if log['status'] == 'success')
        failed_recoveries = total_recoveries - successful_recoveries
        
        return {
            'validation_summary': {
                'total': total_validations,
                'successful': successful_validations,
                'failed': failed_validations,
                'success_rate': (successful_validations / total_validations * 100) if total_validations > 0 else 0
            },
            'recovery_summary': {
                'total': total_recoveries,
                'successful': successful_recoveries,
                'failed': failed_recoveries,
                'success_rate': (successful_recoveries / total_recoveries * 100) if total_recoveries > 0 else 0
            },
            'recent_validations': self.validation_log[-10:] if self.validation_log else [],
            'recent_recoveries': self.recovery_log[-10:] if self.recovery_log else []
        }

# 전역 인스턴스
file_validator = FileValidator(".")
