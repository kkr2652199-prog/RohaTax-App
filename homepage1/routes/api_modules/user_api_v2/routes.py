"""
User API v2 - Router Layer
Flask 라우팅 정의 (기존 엔드포인트 URL과 100% 동일하게 유지)
"""
from flask import Blueprint, jsonify, request, session
from core.db import get_conn_optimized as get_conn
import sqlite3
import logging
from .repository import UserRepository
from .service import UserService

logger = logging.getLogger(__name__)


def create_user_api_blueprint() -> Blueprint:
    """
    User API Blueprint 생성
    
    Returns:
        Blueprint: Flask Blueprint 인스턴스
    """
    bp = Blueprint('user_api_v2', __name__, url_prefix='/api')
    
    # 의존성 주입 (Repository, Service)
    repository = UserRepository()
    service = UserService(repository=repository)
    
    @bp.route('/myhome-data')
    def myhome_data():
        """마이홈 데이터 조회"""
        if not session.get('user_id'):
            return jsonify({'success': False, 'error': '로그인이 필요합니다'}), 401
        
        limit = request.args.get('limit', 15, type=int)
        offset = request.args.get('offset', 0, type=int)
        sort = (request.args.get('sort') or 'date').strip().lower()
        order = (request.args.get('order') or 'desc').strip().lower()
        order = 'asc' if order == 'asc' else 'desc'
        
        try:
            with get_conn() as conn:
                conn.row_factory = sqlite3.Row
                result = service.get_myhome_data(
                    conn=conn,
                    user_id=session['user_id'],
                    limit=limit,
                    offset=offset,
                    sort=sort,
                    order=order
                )
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"마이홈 데이터 조회 오류: {str(e)}", exc_info=True)
            return jsonify({'success': False, 'error': f'서버 오류: {str(e)}'}), 500
    
    @bp.route('/myhome-data/delete', methods=['POST'])
    def myhome_data_delete():
        """항목 삭제"""
        if not session.get('user_id'):
            return jsonify({'success': False, 'error': '로그인이 필요합니다'}), 401
        
        data = request.get_json(silent=True) or {}
        ids = data.get('ids') or []
        if not isinstance(ids, list) or not ids:
            return jsonify({'success': False, 'error': '삭제할 항목이 없습니다'}), 400
        
        try:
            # ID 리스트를 정수로 변환
            item_ids = []
            for raw in ids:
                try:
                    item_ids.append(int(raw))
                except Exception:
                    continue
            
            if not item_ids:
                return jsonify({'success': False, 'error': '유효한 항목 ID가 없습니다'}), 400
            
            with get_conn() as conn:
                result = service.delete_token_history_items(
                    conn=conn,
                    user_id=session['user_id'],
                    item_ids=item_ids
                )
                conn.commit()
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"항목 삭제 오류: {str(e)}", exc_info=True)
            return jsonify({'success': False, 'error': f'삭제 중 오류: {str(e)}'}), 500
    
    @bp.route('/user/token-status')
    def get_token_status():
        """실시간 토큰 상태 조회 API"""
        if not session.get('user_id'):
            return jsonify({'error': '로그인이 필요합니다'}), 401
        
        try:
            with get_conn() as conn:
                conn.row_factory = sqlite3.Row
                result = service.get_token_status(
                    conn=conn,
                    user_id=session['user_id']
                )
            
            if 'error' in result:
                return jsonify(result), 404
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"토큰 상태 조회 오류: {str(e)}", exc_info=True)
            return jsonify({'error': f'서버 오류: {str(e)}'}), 500
    
    @bp.route('/user/usage-history')
    def get_usage_history():
        """사용 내역 조회 API"""
        if not session.get('user_id'):
            return jsonify({'error': '로그인이 필요합니다'}), 401
        
        try:
            with get_conn() as conn:
                conn.row_factory = sqlite3.Row
                result = service.get_usage_history(
                    conn=conn,
                    user_id=session['user_id']
                )
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"사용 내역 조회 오류: {str(e)}", exc_info=True)
            return jsonify({'error': f'서버 오류: {str(e)}'}), 500
    
    @bp.route('/user/refresh-tokens', methods=['POST'])
    def refresh_tokens():
        """토큰 새로고침 API (관리자용)"""
        if not session.get('user_id') or not session.get('is_admin'):
            return jsonify({'error': '관리자 권한이 필요합니다'}), 403
        
        try:
            data = request.get_json()
            user_id = data.get('user_id')
            token_amount = data.get('token_amount', 100)
            
            if not user_id or not isinstance(token_amount, int) or token_amount <= 0:
                return jsonify({'error': '유효하지 않은 요청입니다'}), 400
            
            with get_conn() as conn:
                result = service.refresh_tokens(
                    conn=conn,
                    user_id=user_id,
                    token_amount=token_amount,
                    admin_id=session['user_id']
                )
                conn.commit()
            
            if 'error' in result:
                return jsonify(result), 404
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"토큰 새로고침 오류: {str(e)}", exc_info=True)
            return jsonify({'error': f'서버 오류: {str(e)}'}), 500
    
    @bp.route('/v2/user/token-summary')
    def get_token_summary_v2():
        """토큰 요약 조회 API (v2)"""
        if not session.get('user_id'):
            return jsonify({'success': False, 'error': '로그인이 필요합니다'}), 401
        
        try:
            with get_conn() as conn:
                conn.row_factory = sqlite3.Row
                result = service.get_token_summary(
                    conn=conn,
                    user_id=session['user_id']
                )
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"토큰 요약 조회 오류: {str(e)}", exc_info=True)
            return jsonify({'success': False, 'error': f'서버 오류: {str(e)}'}), 500
    
    @bp.route('/v2/user/activity-logs')
    def get_user_activity_logs_v2():
        """활동 로그 조회 API (v2)"""
        if not session.get('user_id'):
            return jsonify({'success': False, 'error': '로그인이 필요합니다'}), 401
        
        try:
            with get_conn() as conn:
                conn.row_factory = sqlite3.Row
                result = service.get_activity_logs(
                    conn=conn,
                    user_id=session['user_id']
                )
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"활동 로그 조회 오류: {str(e)}", exc_info=True)
            return jsonify({'success': False, 'error': f'서버 오류: {str(e)}'}), 500
    
    return bp

