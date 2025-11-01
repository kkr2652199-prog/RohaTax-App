"""
관리자용 분석 대시보드 API
"""
from flask import Blueprint, jsonify, render_template
from core.database_manager import db_manager
from core.system_manager import system_manager
import logging

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')

@analytics_bp.route('/dashboard')
def dashboard():
    """관리자 대시보드"""
    try:
        # 변환 통계
        conversion_stats = db_manager.get_conversion_stats()
        
        # 최근 에러들
        recent_errors = db_manager.get_recent_errors(10)
        
        # 시스템 리포트
        system_report = system_manager.generate_report()
        
        return jsonify({
            'status': 'success',
            'data': {
                'conversion_stats': conversion_stats,
                'recent_errors': recent_errors,
                'system_report': system_report
            }
        })
    except Exception as e:
        logging.error(f"대시보드 데이터 조회 오류: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@analytics_bp.route('/stats')
def stats():
    """변환 통계 API"""
    try:
        stats = db_manager.get_conversion_stats()
        return jsonify({'status': 'success', 'stats': stats})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@analytics_bp.route('/errors')
def errors():
    """에러 로그 API"""
    try:
        errors = db_manager.get_recent_errors()
        return jsonify({'status': 'success', 'errors': errors})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@analytics_bp.route('/files')
def file_history():
    """파일 변환 기록 API"""
    filename = request.args.get('filename')
    if not filename:
        return jsonify({'status': 'error', 'message': 'filename parameter required'}), 400
    
    try:
        history = db_manager.get_file_conversion_history(filename)
        return jsonify({'status': 'success', 'history': history})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@analytics_bp.route('/cleanup', methods=['POST'])
def cleanup_logs():
    """오래된 로그 정리 API"""
    try:
        days_to_keep = request.json.get('days_to_keep', 90)
        deleted_count = db_manager.cleanup_old_logs(days_to_keep)
        
        return jsonify({
            'status': 'success', 
            'message': f'{deleted_count}개의 오래된 로그가 정리되었습니다.'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500









