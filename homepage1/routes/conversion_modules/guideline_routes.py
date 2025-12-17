"""
절대지침 검증 라우트 모듈
절대지침 관련 기능 (검증, 버전 조회 등)
"""

from flask import Blueprint, request, session
from core.responses import success, error
from core.absolute_guidelines import absolute_guidelines
from ..utils.auth import ensure_login_for_json

guideline_bp = Blueprint('guideline', __name__)


@guideline_bp.route('/api/validate-template-data', methods=['POST'])
def validate_template_data():
    """템플릿 데이터 절대지침 검증 API"""
    user_id, guard_response = ensure_login_for_json()
    if guard_response is not None:
        return guard_response
    
    try:
        data = request.get_json(silent=True) or {}
        
        # 절대지침 검증 수행
        success_result, errors = absolute_guidelines.validate_template_data(data)
        
        # 검증 결과 로그 기록
        absolute_guidelines.log_validation_result(
            data, success_result, errors, user_id
        )
        
        if success_result:
            return success('절대지침 검증 통과', data={
                'compliant': True,
                'errors': [],
                'guideline_version': absolute_guidelines.get_guideline_version()
            })
        else:
            return error('절대지침 검증 실패', data={
                'compliant': False,
                'errors': errors,
                'guideline_version': absolute_guidelines.get_guideline_version()
            }, status=422)
            
    except Exception as e:
        return error(f'검증 처리 실패: {str(e)}', status=500)

