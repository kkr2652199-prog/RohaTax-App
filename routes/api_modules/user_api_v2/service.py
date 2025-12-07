"""
User API v2 - Service Layer
비즈니스 로직 처리 및 데이터 변환 (반드시 dict 형태로 변환하여 리턴)
"""
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import sqlite3

logger = logging.getLogger(__name__)


class UserService:
    """사용자 비즈니스 로직 처리"""
    
    # 활동 유형 번역 사전
    ACTIVITY_TYPE_MAP = {
        "TOKEN_GRANT_BY_ADMIN": "토큰 지급 (관리자)",
        "TOKEN_RESET_BY_ADMIN": "토큰 초기화 (관리자)",
        "FILE_CONVERT": "파일 변환",
        "GRADE_CHANGE_BY_ADMIN": "등급 변경 (관리자)",
        "TOKEN_USE": "토큰 사용",
        "TOKEN_CHARGE": "토큰 충전",
        "LOGIN": "로그인",
        "LOGOUT": "로그아웃",
        "PROFILE_UPDATE": "프로필 수정"
    }
    
    def __init__(self, repository):
        """Service 초기화"""
        self.repository = repository
        self.logger = logger
    
    def get_myhome_data(
        self,
        conn: sqlite3.Connection,
        user_id: int,
        limit: int,
        offset: int,
        sort: str,
        order: str
    ) -> Dict[str, Any]:
        """
        마이홈 데이터 조회 및 변환
        
        Returns:
            Dict: {'success': bool, 'total_count': int, 'activity_history': List[Dict]}
        """
        # DB 조회
        items = self.repository.get_myhome_data(
            conn=conn,
            user_id=user_id,
            limit=limit,
            offset=offset,
            sort=sort,
            order=order
        )
        
        # 총 개수 조회
        total_count = self.repository.get_total_count(conn, user_id)
        
        # 데이터 변환 (sqlite3.Row → dict)
        activity = []
        for r in items:
            # balance_after는 이미 쿼리에서 계산되어 있음
            balance_after = r['balance_after'] if r['balance_after'] is not None else 0
            
            # meta JSON 파싱
            try:
                meta_obj = json.loads(r['meta']) if r['meta'] else {}
            except Exception:
                meta_obj = {}
            
            # change_type → log_type 변환
            ct = (r['change_type'] or '').lower()
            if ct == 'use':
                log_type = 'CONVERSION'
            elif ct == 'grant':
                log_type = 'GRANT'
            elif ct == 'reset':
                log_type = 'RESET'
            else:
                log_type = (r['change_type'] or 'UNKNOWN').upper()
            
            # KST 날짜 포맷팅
            created_raw = r['created_at']
            dt_str = str(created_raw)
            try:
                try:
                    dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                except Exception:
                    dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
                    dt = dt.replace(tzinfo=timezone.utc)
                kst = dt.astimezone(timezone(timedelta(hours=9)))
                datetime_kst = kst.strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                datetime_kst = dt_str
            
            # 금액 계산
            amt = int(r['amount'] or 0)
            charge_amount = amt if amt > 0 else 0
            usage_amount = abs(amt) if amt < 0 else 0
            
            # dict로 변환하여 추가
            activity.append({
                'id': int(r['id']),
                'datetime_kst': datetime_kst,
                'plan_type': r['plan_type'] or '',
                'log_type': log_type,
                'filename': meta_obj.get('file_name') or meta_obj.get('file') or None,
                'customer_name': meta_obj.get('customer_name'),
                'charge_amount': int(charge_amount),
                'usage_amount': int(usage_amount),
                'balance_after': int(balance_after or 0)
            })
        
        return {
            'success': True,
            'total_count': int(total_count),
            'activity_history': activity
        }
    
    def delete_token_history_items(
        self,
        conn: sqlite3.Connection,
        user_id: int,
        item_ids: List[int]
    ) -> Dict[str, Any]:
        """토큰 히스토리 항목 삭제"""
        deleted_count = self.repository.delete_token_history_items(
            conn=conn,
            user_id=user_id,
            item_ids=item_ids
        )
        
        return {
            'success': True,
            'deleted': deleted_count
        }
    
    def get_token_status(
        self,
        conn: sqlite3.Connection,
        user_id: int
    ) -> Dict[str, Any]:
        """토큰 상태 조회"""
        # 사용자 정보 조회
        user = self.repository.get_user_info(conn, user_id)
        if not user:
            return {'error': '사용자 정보를 찾을 수 없습니다'}
        
        # 토큰 요약 조회
        summary = self.repository.get_token_summary(conn, user_id)
        if not summary:
            total_tokens = 0
            used_tokens = 0
        else:
            total_tokens = summary['total_charged']
            used_tokens = summary['total_used']
        
        available_tokens = total_tokens - used_tokens
        usage_percentage = (used_tokens / total_tokens * 100) if total_tokens > 0 else 0
        
        # 최근 사용 내역 조회
        recent_usage = self.repository.get_recent_usage(conn, user_id, limit=5)
        recent_usage_list = []
        for row in recent_usage:
            try:
                meta_obj = json.loads(row['meta']) if row['meta'] else {}
            except Exception:
                meta_obj = {}
            recent_usage_list.append({
                'action': row['action'],
                'meta': meta_obj,
                'created_at': row['created_at']
            })
        
        # 변환 통계 조회
        conversion_stats = self.repository.get_conversion_stats(conn, user_id)
        if not conversion_stats:
            conversion_stats_dict = {
                'total_conversions': 0,
                'successful_conversions': 0,
                'avg_conversion_time': 0,
                'total_file_size': 0,
                'success_rate': 0
            }
        else:
            total_conv = conversion_stats['total_conversions'] or 0
            success_conv = conversion_stats['successful_conversions'] or 0
            conversion_stats_dict = {
                'total_conversions': total_conv,
                'successful_conversions': success_conv,
                'avg_conversion_time': round(conversion_stats['avg_conversion_time'] or 0, 2),
                'total_file_size': conversion_stats['total_file_size'] or 0,
                'success_rate': round((success_conv / total_conv * 100) if total_conv > 0 else 0, 1)
            }
        
        return {
            'success': True,
            'data': {
                'user_info': {
                    'id': user['id'],
                    'username': user['username'],
                    'plan_type': user['plan_type'],
                    'is_admin': bool(user['is_admin']),
                    'created_at': user['created_at']
                },
                'token_status': {
                    'total_tokens': total_tokens,
                    'used_tokens': user['tokens_used'],
                    'available_tokens': available_tokens,
                    'usage_percentage': round(usage_percentage, 1)
                },
                'service_stats': conversion_stats_dict,
                'recent_usage': recent_usage_list,
                'last_updated': datetime.now().isoformat()
            }
        }
    
    def get_usage_history(
        self,
        conn: sqlite3.Connection,
        user_id: int
    ) -> Dict[str, Any]:
        """사용 내역 조회"""
        stats = self.repository.get_usage_history_stats(conn, user_id)
        
        # period_stats 변환
        daily_stats = []
        for row in stats['period_stats']:
            daily_conv = row['daily_conversions']
            daily_success = row['daily_success']
            daily_stats.append({
                'date': row['date'],
                'conversions': daily_conv,
                'success_rate': round((daily_success / daily_conv * 100) if daily_conv > 0 else 0, 1),
                'avg_time': round(row['avg_time'] or 0, 2),
                'file_size': row['daily_file_size'] or 0
            })
        
        # monthly_usage 변환
        monthly_usage = []
        for row in stats['monthly_usage']:
            monthly_usage.append({
                'month': row['month'],
                'conversions': row['conversions'],
                'token_usage': row['token_usage']
            })
        
        return {
            'success': True,
            'data': {
                'daily_stats': daily_stats,
                'monthly_usage': monthly_usage
            }
        }
    
    def refresh_tokens(
        self,
        conn: sqlite3.Connection,
        user_id: int,
        token_amount: int,
        admin_id: int
    ) -> Dict[str, Any]:
        """토큰 새로고침 (관리자용)"""
        user = self.repository.refresh_user_tokens(
            conn=conn,
            user_id=user_id,
            token_amount=token_amount,
            admin_id=admin_id
        )
        
        if not user:
            return {'error': '사용자를 찾을 수 없습니다'}
        
        # 사용 로그 기록 (기존 로직 유지)
        try:
            conn.execute(
                "INSERT INTO usage_logs (user_id, action, meta) VALUES (?, ?, ?)",
                (user_id, 'token_refresh', json.dumps({
                    'amount': token_amount,
                    'admin_id': admin_id,
                    'timestamp': datetime.now().isoformat()
                }))
            )
        except Exception as e:
            self.logger.warning(f"사용 로그 기록 실패: {str(e)}")
        
        return {
            'success': True,
            'message': f'{user["username"]}님에게 {token_amount}토큰이 추가되었습니다',
            'data': {
                'user_id': user_id,
                'token_amount': token_amount,
                'admin_id': admin_id,
                'timestamp': datetime.now().isoformat()
            }
        }
    
    def get_token_summary(
        self,
        conn: sqlite3.Connection,
        user_id: int
    ) -> Dict[str, Any]:
        """토큰 요약 조회 (v2)"""
        summary = self.repository.get_token_summary(conn, user_id)
        
        if not summary:
            total_tokens = 0
            used_tokens = 0
        else:
            total_tokens = summary['total_charged']
            used_tokens = summary['total_used']
        
        available_tokens = total_tokens - used_tokens
        
        return {
            'success': True,
            'data': {
                'total_tokens': int(total_tokens),
                'used_tokens': int(used_tokens),
                'available_tokens': int(available_tokens)
            },
            'last_updated': datetime.now().isoformat()
        }
    
    def get_activity_logs(
        self,
        conn: sqlite3.Connection,
        user_id: int
    ) -> Dict[str, Any]:
        """활동 로그 조회 (v2)"""
        logs = self.repository.get_activity_logs(conn, user_id)
        
        # 결과를 dict 리스트로 변환하고 번역 적용
        result_logs = []
        for log in logs:
            log_dict = dict(log)  # sqlite3.Row → dict 변환
            # 활동 유형 번역
            log_dict['activity_type_korean'] = self._translate_activity_type(log_dict['activity_type'])
            # 상세 정보 요약
            log_dict['details_summary'] = self._summarize_details(log_dict['activity_type'], log_dict['details'])
            result_logs.append(log_dict)
        
        return {
            'success': True,
            'data': result_logs
        }
    
    def _translate_activity_type(self, activity_type: str) -> str:
        """활동 유형을 한글로 번역"""
        return self.ACTIVITY_TYPE_MAP.get(activity_type, activity_type)
    
    def _summarize_details(self, activity_type: str, details_str: Optional[str]) -> str:
        """상세 정보를 요약 문장으로 변환"""
        if not details_str:
            return '세부 정보 없음'
        
        try:
            details = json.loads(details_str) if isinstance(details_str, str) else details_str
            
            if activity_type == 'TOKEN_GRANT_BY_ADMIN':
                amount = details.get('granted_amount', 0)
                return f"{amount} 토큰 지급"
            
            elif activity_type == 'TOKEN_RESET_BY_ADMIN':
                # 무료 토큰만 초기화한 경우와 전체 초기화를 구분
                reason = details.get('reason', '')
                if '무료 토큰만 초기화' in reason:
                    reset_free_tokens = details.get('reset_free_tokens', 0)
                    paid_preserved = details.get('paid_tokens_preserved', 0)
                    return f"무료 토큰 {reset_free_tokens}개 초기화 (유료 토큰 {paid_preserved}개 유지)"
                else:
                    return "토큰 잔액 초기화"
            
            elif activity_type == 'TOKEN_EXPIRED':
                # 무료 토큰 만료 로그 표시
                expiration_type = details.get('type', '')
                total_deducted = details.get('total_deducted', 0)
                expired_count = details.get('expired_count', 0)
                
                if expiration_type == 'free_token_expiration':
                    return f"무료 토큰 {total_deducted}개 만료로 자동 회수 ({expired_count}건)"
                else:
                    return f"토큰 {total_deducted}개 만료 ({expired_count}건)"
            
            elif activity_type == 'FILE_CONVERT':
                filename = details.get('filename', '파일')
                rows = details.get('extracted_rows', 0)
                return f"{filename} ({rows}건)"
            
            elif activity_type == 'GRADE_CHANGE_BY_ADMIN':
                old_plan = details.get('old_plan', '')
                new_plan = details.get('new_plan', '')
                return f"{old_plan} → {new_plan}"
            
            elif activity_type == 'TOKEN_USE':
                amount = details.get('amount', 0)
                return f"{amount} 토큰 사용"
            
            elif activity_type == 'TOKEN_CHARGE':
                amount = details.get('amount', 0)
                return f"{amount} 토큰 충전"
            
            elif activity_type == 'PROFILE_UPDATE':
                fields = details.get('updated_fields', [])
                if fields:
                    return f"{', '.join(fields)} 수정"
                return "프로필 정보 수정"
            
            else:
                # 기본적으로 JSON을 문자열로 반환하되, 주요 필드만 추출
                if isinstance(details, dict):
                    if 'amount' in details:
                        return f"금액: {details['amount']}"
                    elif 'filename' in details:
                        return f"파일: {details['filename']}"
                    return str(details)
                return str(details)
                
        except (json.JSONDecodeError, TypeError, AttributeError):
            # JSON 파싱 실패 시 원본 문자열 반환 (너무 길면 잘라서)
            if isinstance(details_str, str) and len(details_str) > 50:
                return details_str[:50] + "..."
            return str(details_str) if details_str else '세부 정보 없음'

