"""
보안 및 검증 라우트 모듈
보안 상태, 알림, 지침 버전 등의 보안 관련 기능
"""

from flask import Blueprint, session, jsonify, request
from core.responses import success, error
from core.absolute_guidelines import absolute_guidelines
from core.file_validator import file_validator
from core.notification_system import notification_system
from core.security import generate_csrf_token
from datetime import datetime

security_bp = Blueprint('security', __name__)


@security_bp.route('/api/guidelines/version', methods=['GET'])
def get_guidelines_version():
    """절대지침 버전 조회 API"""
    try:
        version = absolute_guidelines.get_guideline_version()
        return success('절대지침 버전 조회 성공', data={
            'version': version,
            'last_updated': '2025-10-01',
            'status': 'active'
        })
    except Exception as e:
        return error(f'버전 조회 실패: {str(e)}', status=500)


@security_bp.route('/api/security/status', methods=['GET'])
def get_security_status():
    """보안 시스템 상태 조회 API"""
    if not session.get('user_id') or not session.get('is_admin'):
        return error('관리자 권한이 필요합니다', status=403)
    
    try:
        # 파일 검증 시스템 상태
        validation_summary = file_validator.get_validation_summary()
        
        # 알림 시스템 상태
        notification_stats = notification_system.get_notification_stats()
        
        # 최근 알림 목록
        recent_notifications = notification_system.get_notifications(limit=10)
        
        return success('보안 시스템 상태 조회 성공', data={
            'file_validation': validation_summary,
            'notifications': notification_stats,
            'recent_notifications': recent_notifications,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return error(f'보안 시스템 상태 조회 실패: {str(e)}', status=500)


@security_bp.route('/api/security/notifications', methods=['GET'])
def get_notifications():
    """알림 목록 조회 API"""
    if not session.get('user_id') or not session.get('is_admin'):
        return error('관리자 권한이 필요합니다', status=403)
    
    try:
        category = request.args.get('category')
        priority = request.args.get('priority')
        limit = int(request.args.get('limit', 50))
        
        notifications = notification_system.get_notifications(
            category=category,
            priority=priority,
            limit=limit
        )
        
        return success('알림 목록 조회 성공', data={
            'notifications': notifications,
            'count': len(notifications)
        })
        
    except Exception as e:
        return error(f'알림 목록 조회 실패: {str(e)}', status=500)


@security_bp.route('/api/security/notifications/<int:notification_id>/read', methods=['POST'])
def mark_notification_read(notification_id):
    """알림 읽음 처리 API"""
    if not session.get('user_id') or not session.get('is_admin'):
        return error('관리자 권한이 필요합니다', status=403)
    
    try:
        success_result = notification_system.mark_as_read(notification_id)
        
        if success_result:
            return success('알림 읽음 처리 완료', data={
                'notification_id': notification_id,
                'status': 'read'
            })
        else:
            return error('알림 읽음 처리 실패', status=500)
            
    except Exception as e:
        return error(f'알림 읽음 처리 실패: {str(e)}', status=500)


@security_bp.route('/api/security/validation/test', methods=['POST'])
def test_validation():
    """파일 검증 시스템 테스트 API (관리자 전용)"""
    if not session.get('user_id') or not session.get('is_admin'):
        return error('관리자 권한이 필요합니다', status=403)
    
    try:
        data = request.get_json()
        test_type = data.get('test_type', 'basic')
        
        if test_type == 'basic':
            result = file_validator.run_basic_validation_test()
        elif test_type == 'security':
            result = file_validator.run_security_validation_test()
        elif test_type == 'performance':
            result = file_validator.run_performance_test()
        else:
            return error('유효하지 않은 테스트 타입입니다', status=400)
        
        return success('검증 시스템 테스트 완료', data={
            'test_type': test_type,
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return error(f'검증 시스템 테스트 실패: {str(e)}', status=500)


