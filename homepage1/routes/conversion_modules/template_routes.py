"""
템플릿 관리 라우트 모듈
템플릿 조회, 업로드, 검증 등의 템플릿 관련 기능
"""

from flask import Blueprint, session, jsonify, request
from core.responses import success, error
# from core.template_manager import template_manager
import os

template_bp = Blueprint('template', __name__)


@template_bp.route('/api/templates', methods=['GET'])
def get_templates():
    """사용 가능한 템플릿 목록 조회 API"""
    if not session.get('user_id'):
        return error('로그인이 필요합니다', status=401)
    
    try:
        templates = template_manager.get_available_templates()
        return success('템플릿 목록 조회 성공', data={'templates': templates})
    except Exception as e:
        return error(f'템플릿 목록 조회 실패: {str(e)}', status=500)


@template_bp.route('/api/templates/<template_id>', methods=['GET'])
def get_template_info(template_id):
    """특정 템플릿 정보 조회 API"""
    if not session.get('user_id'):
        return error('로그인이 필요합니다', status=401)
    
    try:
        template_info = template_manager.get_template_info(template_id)
        if not template_info:
            return error('템플릿을 찾을 수 없습니다', status=404)
        
        return success('템플릿 정보 조회 성공', data={'template': template_info})
    except Exception as e:
        return error(f'템플릿 정보 조회 실패: {str(e)}', status=500)


@template_bp.route('/api/templates/<template_id>/validate', methods=['GET'])
def validate_template(template_id):
    """템플릿 파일 유효성 검사 API"""
    if not session.get('user_id'):
        return error('로그인이 필요합니다', status=401)
    
    try:
        is_valid = template_manager.validate_template_file(template_id)
        template_path = template_manager.get_template_path(template_id)
        
        return success('템플릿 유효성 검사 완료', data={
            'template_id': template_id,
            'is_valid': is_valid,
            'file_path': template_path
        })
    except Exception as e:
        return error(f'템플릿 유효성 검사 실패: {str(e)}', status=500)


@template_bp.route('/api/templates/upload', methods=['POST'])
def upload_template():
    """템플릿 파일 업로드 API (관리자 전용)"""
    if not session.get('user_id') or not session.get('is_admin'):
        return error('관리자 권한이 필요합니다', status=403)
    
    try:
        # 업로드된 파일 확인
        if 'template_file' not in request.files:
            return error('템플릿 파일이 없습니다', status=400)
        
        template_file = request.files['template_file']
        if template_file.filename == '':
            return error('파일이 선택되지 않았습니다', status=400)
        
        # 파일 확장자 검증
        if not template_file.filename.lower().endswith(('.xlsx', '.xlsm', '.xls')):
            return error('Excel 파일만 업로드 가능합니다', status=400)
        
        # 템플릿 정보 파싱
        template_id = request.form.get('template_id')
        template_name = request.form.get('template_name')
        template_description = request.form.get('template_description')
        sheet_name = request.form.get('sheet_name', 'Sheet1')
        header_row = int(request.form.get('header_row', 1))
        
        if not all([template_id, template_name]):
            return error('템플릿 ID와 이름은 필수입니다', status=400)
        
        # 템플릿 디렉토리 생성
        template_dir = template_manager.create_template_directory(template_id)
        
        # 파일 저장
        filename = f"{template_id}_template.xlsx"
        file_path = os.path.join(template_dir, filename)
        template_file.save(file_path)
        
        # 템플릿 설정에 추가
        template_info = {
            "name": template_name,
            "description": template_description or f"{template_name} 템플릿",
            "file": f"{template_id}/{filename}",
            "sheet_name": sheet_name,
            "header_row": header_row,
            "fields": {}  # 나중에 필드 매핑 추가 가능
        }
        
        success_result = template_manager.add_template(template_id, template_info)
        
        if success_result:
            return success('템플릿 업로드 성공', data={
                'template_id': template_id,
                'template_name': template_name,
                'file_path': file_path
            })
        else:
            return error('템플릿 설정 추가 실패', status=500)
            
    except Exception as e:
        return error(f'템플릿 업로드 실패: {str(e)}', status=500)


@template_bp.route('/api/validate-template-data', methods=['POST'])
def validate_template_data():
    """템플릿 데이터 유효성 검사 API"""
    if not session.get('user_id'):
        return error('로그인이 필요합니다', status=401)
    
    try:
        data = request.get_json()
        template_id = data.get('template_id')
        
        if not template_id:
            return error('템플릿 ID가 필요합니다', status=400)
        
        # 템플릿 파일 유효성 검사
        is_valid = template_manager.validate_template_file(template_id)
        
        if not is_valid:
            return error('템플릿 파일이 유효하지 않습니다', status=400)
        
        # 템플릿 정보 조회
        template_info = template_manager.get_template_info(template_id)
        
        return success('템플릿 데이터 유효성 검사 완료', data={
            'template_id': template_id,
            'is_valid': is_valid,
            'template_info': template_info
        })
        
    except Exception as e:
        return error(f'템플릿 데이터 유효성 검사 실패: {str(e)}', status=500)


