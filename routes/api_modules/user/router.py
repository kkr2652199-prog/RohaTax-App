"""
User API 라우터
엔드포인트 라우팅만 담당 (비즈니스 로직 없음)
API Turbocharger 리팩토링 - Phase 1
"""
from flask import Blueprint, request, session
from core.db import get_conn_optimized as get_conn
from core.responses import success, error
from .schemas import (
    MyHomeDataRequest,
    DeleteRequest,
    RefreshTokensRequest,
)
from .service import UserService
from .repository import UserRepository
import logging

logger = logging.getLogger(__name__)

def create_user_api_blueprint() -> Blueprint:
    """
    User API Blueprint 생성
    
    Returns:
        Blueprint: Flask Blueprint 인스턴스
    """
    bp = Blueprint('user_api', __name__, url_prefix='/api')
    
    # 의존성 주입 (Repository, Service)
    repository = UserRepository()
    service = UserService(repository=repository)
    
    @bp.route('/myhome-data')
    def myhome_data():
        """마이홈 데이터 조회"""
        if not session.get('user_id'):
            return error('로그인이 필요합니다', status=401)
        
        try:
            # Pydantic 검증
            request_data = MyHomeDataRequest(
                limit=request.args.get('limit', 15, type=int),
                offset=request.args.get('offset', 0, type=int),
                sort=request.args.get('sort', 'date'),
                order=request.args.get('order', 'desc')
            )
            
            # DB 연결 주입
            with get_conn() as conn:
                response = service.get_myhome_data(
                    conn=conn,
                    user_id=session['user_id'],
                    request=request_data
                )
            
            return success(data=response.dict())
            
        except ValueError as e:
            return error(str(e), status=400)
        except Exception as e:
            logger.error(f"마이홈 데이터 조회 오류: {str(e)}", exc_info=True)
            return error(f'서버 오류: {str(e)}', status=500)
    
    @bp.route('/myhome-data/delete', methods=['POST'])
    def myhome_data_delete():
        """항목 삭제"""
        if not session.get('user_id'):
            return error('로그인이 필요합니다', status=401)
        
        try:
            # Pydantic 검증
            request_data = DeleteRequest(**request.get_json(silent=True) or {})
            
            # DB 연결 주입
            with get_conn() as conn:
                response = service.delete_items(
                    conn=conn,
                    user_id=session['user_id'],
                    request=request_data
                )
            
            return success(data=response.dict())
            
        except ValueError as e:
            return error(str(e), status=400)
        except Exception as e:
            logger.error(f"항목 삭제 오류: {str(e)}", exc_info=True)
            return error(f'삭제 중 오류: {str(e)}', status=500)
    
    @bp.route('/user/token-status')
    def get_token_status():
        """실시간 토큰 상태 조회 API"""
        if not session.get('user_id'):
            return error('로그인이 필요합니다', status=401)
        
        try:
            # DB 연결 주입
            with get_conn() as conn:
                response = service.get_token_status(
                    conn=conn,
                    user_id=session['user_id']
                )
            
            return success(data=response.dict())
            
        except ValueError as e:
            return error(str(e), status=404)
        except Exception as e:
            logger.error(f"토큰 상태 조회 오류: {str(e)}", exc_info=True)
            return error(f'서버 오류: {str(e)}', status=500)
    
    @bp.route('/user/usage-history')
    def get_usage_history():
        """사용 내역 조회 API"""
        if not session.get('user_id'):
            return error('로그인이 필요합니다', status=401)
        
        try:
            # DB 연결 주입
            with get_conn() as conn:
                response = service.get_usage_history(
                    conn=conn,
                    user_id=session['user_id']
                )
            
            return success(data=response.dict())
            
        except Exception as e:
            logger.error(f"사용 내역 조회 오류: {str(e)}", exc_info=True)
            return error(f'서버 오류: {str(e)}', status=500)
    
    @bp.route('/user/refresh-tokens', methods=['POST'])
    def refresh_tokens():
        """토큰 새로고침 API (관리자용)"""
        if not session.get('user_id') or not session.get('is_admin'):
            return error('관리자 권한이 필요합니다', status=403)
        
        try:
            # Pydantic 검증
            request_data = RefreshTokensRequest(**request.get_json(silent=True) or {})
            
            # DB 연결 주입
            with get_conn() as conn:
                response = service.refresh_tokens(
                    conn=conn,
                    user_id=request_data.user_id,
                    request=request_data,
                    admin_id=session['user_id']
                )
            
            return success(data=response.dict())
            
        except ValueError as e:
            return error(str(e), status=400)
        except Exception as e:
            logger.error(f"토큰 새로고침 오류: {str(e)}", exc_info=True)
            return error(f'서버 오류: {str(e)}', status=500)
    
    @bp.route('/v2/user/token-summary')
    def get_token_summary_v2():
        """토큰 요약 조회 API (v2)"""
        if not session.get('user_id'):
            return error('로그인이 필요합니다', status=401)
        
        try:
            # DB 연결 주입
            with get_conn() as conn:
                response = service.get_token_summary(
                    conn=conn,
                    user_id=session['user_id']
                )
            
            # response.data를 직접 전달 (중첩 구조 방지)
            if hasattr(response, 'data') and response.data:
                # Pydantic 모델의 dict() 또는 model_dump() 사용
                if hasattr(response.data, 'model_dump'):
                    data_dict = response.data.model_dump()
                elif hasattr(response.data, 'dict'):
                    data_dict = response.data.dict()
                else:
                    data_dict = dict(response.data) if hasattr(response.data, '__dict__') else {}
                return success(data=data_dict)
            else:
                return error('토큰 요약 데이터가 없습니다', status=404)
            
        except ValueError as e:
            return error(str(e), status=404)
        except Exception as e:
            logger.error(f"토큰 요약 조회 오류: {str(e)}", exc_info=True)
            return error(f'서버 오류: {str(e)}', status=500)
    
    @bp.route('/v2/user/activity-logs')
    def get_user_activity_logs_v2():
        """활동 로그 조회 API (v2)"""
        if not session.get('user_id'):
            return error('로그인이 필요합니다', status=401)
        
        try:
            # DB 연결 주입
            page = request.args.get('page', 1, type=int)
            limit = request.args.get('limit', 10, type=int)
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            activity_type = request.args.get('type')
            current_user_id = session['user_id']
            with get_conn() as conn:
                response = service.get_activity_logs(
                    conn=conn,
                    user_id=current_user_id,
                    page=page,
                    limit=limit,
                    start_date=start_date,
                    end_date=end_date,
                    activity_type=activity_type
                )
            
            # response 구조: {'success': True, 'data': {'logs': [...], 'pagination': {...}}}
            # response['data']는 {'logs': [...], 'pagination': {...}} 형태
            logs = response['data'].get('logs', [])
            try:
                log_count = len(logs) if isinstance(logs, list) else 0
            except TypeError:
                log_count = 0
            
            print(f"[DEBUG] 요청한 user_id: {current_user_id}")
            print(f"[DEBUG] 파라미터: page={page}, limit={limit}, start={start_date}, end={end_date}, type={activity_type}")
            print(f"[DEBUG] 조회된 데이터 개수: {log_count}")
            print(f"[DEBUG] response['data'] 타입: {type(response['data'])}")
            print(f"[DEBUG] response['data'] 키: {list(response['data'].keys()) if isinstance(response['data'], dict) else 'not dict'}")
            
            # response['data']를 그대로 전달 (이미 {'logs': [...], 'pagination': {...}} 형태)
            return success(data=response['data'])
            
        except Exception as e:
            logger.error(f"활동 로그 조회 오류: {str(e)}", exc_info=True)
            return error(f'서버 오류: {str(e)}', status=500)
    
    return bp

