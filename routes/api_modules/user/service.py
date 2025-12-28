"""
User Service
비즈니스 로직 담당 (데이터 변환, 캐싱, 검증 등)
API Turbocharger 리팩토링 - Phase 1
"""
from typing import List, Dict, Any, Optional
import sqlite3
import json
from datetime import datetime, timezone, timedelta
from .repository import UserRepository
from .schemas import (
    MyHomeDataRequest,
    MyHomeDataResponse,
    ActivityItem,
    DeleteRequest,
    DeleteResponse,
    TokenStatusResponse,
    TokenStatusData,
    UserInfo,
    TokenStatus,
    ServiceStats,
    RecentUsage,
    UsageHistoryResponse,
    UsageHistoryData,
    DailyStats,
    MonthlyUsage,
    RefreshTokensRequest,
    RefreshTokensResponse,
    TokenSummaryResponse,
    TokenSummaryData,
    ActivityLogItem,
    ActivityLogsResponse,
    LogType
)
import logging

logger = logging.getLogger(__name__)

class UserService:
    """사용자 비즈니스 로직 서비스"""
    
    # 활동 유형 번역 사전
    ACTIVITY_TYPE_MAP = {
        "TOKEN_GRANT_BY_ADMIN": "토큰 지급 (관리자)",
        "TOKEN_RESET_BY_ADMIN": "토큰 초기화 (관리자)",
        "FILE_CONVERT": "파일 변환",
        "GRADE_CHANGE_BY_ADMIN": "등급 변경 (관리자)",
        "TOKEN_USE": "토큰 사용",
        "TOKEN_CHARGE": "토큰 충전",
        "LOGIN": "로그인",
        "USER_LOGIN": "회원 로그인",
        "USER_LOGOUT": "로그아웃",
        "LOGOUT": "로그아웃",
        "PROFILE_UPDATE": "프로필 수정"
    }
    
    def __init__(self, repository: UserRepository):
        """Service 초기화"""
        self.repository = repository
        self.logger = logger
    
    def get_myhome_data(
        self,
        conn: sqlite3.Connection,
        user_id: int,
        request: MyHomeDataRequest
    ) -> MyHomeDataResponse:
        """
        마이홈 데이터 조회
        
        Args:
            conn: 데이터베이스 연결
            user_id: 사용자 ID
            request: 요청 데이터
        
        Returns:
            MyHomeDataResponse: 마이홈 데이터 응답
        """
        # DB 조회
        items = self.repository.get_myhome_data(
            conn=conn,
            user_id=user_id,
            limit=request.limit,
            offset=request.offset,
            sort=request.sort.value,
            order=request.order.value
        )
        
        # 총 개수 조회
        total_count = self.repository.get_total_count(conn, user_id)
        
        # 데이터 변환 (비즈니스 로직)
        activity = [self._transform_activity_item(item) for item in items]
        
        return MyHomeDataResponse(
            success=True,
            total_count=total_count,
            activity_history=activity
        )
    
    def _transform_activity_item(self, row: sqlite3.Row) -> ActivityItem:
        """
        활동 항목 변환 (비즈니스 로직)
        
        Args:
            row: 데이터베이스 행
        
        Returns:
            ActivityItem: 변환된 활동 항목
        """
        # JSON 파싱
        try:
            meta_obj = json.loads(row['meta']) if row['meta'] else {}
        except Exception:
            meta_obj = {}
        
        # 로그 타입 변환
        log_type = self._convert_log_type(row['change_type'])
        
        # 날짜 변환 (KST)
        datetime_kst = self._convert_to_kst(row['created_at'])
        
        # 금액 계산
        amt = int(row['amount'] or 0)
        charge_amount = amt if amt > 0 else 0
        usage_amount = abs(amt) if amt < 0 else 0
        
        return ActivityItem(
            id=int(row['id']),
            datetime_kst=datetime_kst,
            plan_type=row['plan_type'] or '',
            log_type=log_type,
            filename=meta_obj.get('file_name') or meta_obj.get('file'),
            customer_name=meta_obj.get('customer_name'),
            charge_amount=charge_amount,
            usage_amount=usage_amount,
            balance_after=int(row['balance_after'] or 0)
        )
    
    def _convert_log_type(self, change_type: str) -> LogType:
        """
        로그 타입 변환
        
        Args:
            change_type: 변경 타입
        
        Returns:
            LogType: 변환된 로그 타입
        """
        ct = (change_type or '').lower()
        if ct == 'use':
            return LogType.CONVERSION
        elif ct == 'grant':
            return LogType.GRANT
        elif ct == 'reset':
            return LogType.RESET
        else:
            return LogType.UNKNOWN
    
    def _convert_to_kst(self, created_at: str) -> str:
        """
        날짜를 KST로 변환
        
        Args:
            created_at: 생성일시 문자열
        
        Returns:
            str: KST 형식의 날짜 문자열
        """
        try:
            dt_str = str(created_at)
            try:
                dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            except Exception:
                dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
                dt = dt.replace(tzinfo=timezone.utc)
            kst = dt.astimezone(timezone(timedelta(hours=9)))
            return kst.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            return str(created_at)
    
    def delete_items(
        self,
        conn: sqlite3.Connection,
        user_id: int,
        request: DeleteRequest
    ) -> DeleteResponse:
        """
        항목 삭제
        
        Args:
            conn: 데이터베이스 연결
            user_id: 사용자 ID
            request: 삭제 요청
        
        Returns:
            DeleteResponse: 삭제 응답
        """
        deleted_count = self.repository.delete_token_history_items(
            conn=conn,
            user_id=user_id,
            item_ids=request.ids
        )
        
        return DeleteResponse(
            success=True,
            deleted=deleted_count
        )
    
    def get_token_status(
        self,
        conn: sqlite3.Connection,
        user_id: int
    ) -> TokenStatusResponse:
        """
        토큰 상태 조회
        
        Args:
            conn: 데이터베이스 연결
            user_id: 사용자 ID
        
        Returns:
            TokenStatusResponse: 토큰 상태 응답
        """
        data = self.repository.get_token_status_data(conn, user_id)
        
        if not data or not data.get('user'):
            raise ValueError('사용자 정보를 찾을 수 없습니다')
        
        user = data['user']  # sqlite3.Row
        summary = data.get('summary')  # sqlite3.Row or None
        recent_usage = data.get('recent_usage', [])  # List[sqlite3.Row]
        conversion_stats = data.get('conversion_stats')  # sqlite3.Row or None
        
        # 토큰 계산 (sqlite3.Row는 인덱싱 사용)
        total_tokens = summary['total_charged'] if summary else 0
        used_tokens = summary['total_used'] if summary else 0
        available_tokens = total_tokens - used_tokens
        
        # 토큰 사용률 계산
        usage_percentage = (used_tokens / total_tokens * 100) if total_tokens > 0 else 0
        
        # 변환 통계 계산 (sqlite3.Row는 인덱싱 사용)
        total_conversions = conversion_stats['total_conversions'] if conversion_stats and conversion_stats['total_conversions'] is not None else 0
        successful_conversions = conversion_stats['successful_conversions'] if conversion_stats and conversion_stats['successful_conversions'] is not None else 0
        avg_conversion_time = conversion_stats['avg_conversion_time'] if conversion_stats and conversion_stats['avg_conversion_time'] is not None else 0
        total_file_size = conversion_stats['total_file_size'] if conversion_stats and conversion_stats['total_file_size'] is not None else 0
        success_rate = (successful_conversions / total_conversions * 100) if total_conversions > 0 else 0
        
        return TokenStatusResponse(
            success=True,
            data=TokenStatusData(
                user_info=UserInfo(
                    id=user['id'],
                    username=user['username'],
                    plan_type=user['plan_type'] or '',
                    is_admin=bool(user['is_admin']),
                    created_at=user['created_at']
                ),
                token_status=TokenStatus(
                    total_tokens=total_tokens,
                    used_tokens=used_tokens,
                    available_tokens=available_tokens,
                    usage_percentage=round(usage_percentage, 1)
                ),
                service_stats=ServiceStats(
                    total_conversions=total_conversions,
                    successful_conversions=successful_conversions,
                    avg_conversion_time=round(avg_conversion_time or 0, 2),
                    total_file_size=total_file_size or 0,
                    success_rate=round(success_rate, 1)
                ),
                recent_usage=[
                    RecentUsage(
                        action=row['action'],
                        meta=json.loads(row['meta']) if row['meta'] else {},
                        created_at=row['created_at']
                    ) for row in recent_usage
                ],
                last_updated=datetime.now().isoformat()
            )
        )
    
    def get_usage_history(
        self,
        conn: sqlite3.Connection,
        user_id: int
    ) -> UsageHistoryResponse:
        """
        사용 내역 조회
        
        Args:
            conn: 데이터베이스 연결
            user_id: 사용자 ID
        
        Returns:
            UsageHistoryResponse: 사용 내역 응답
        """
        data = self.repository.get_usage_history_data(conn, user_id)
        
        period_stats = data.get('period_stats', [])
        monthly_usage = data.get('monthly_usage', [])
        
        # 일별 통계 변환 (sqlite3.Row는 인덱싱 사용)
        daily_stats = []
        for row in period_stats:
            daily_conversions = row['daily_conversions'] or 0
            daily_success = row['daily_success'] or 0
            success_rate = (daily_success / daily_conversions * 100) if daily_conversions > 0 else 0
            
            daily_stats.append(DailyStats(
                date=row['date'],
                conversions=daily_conversions,
                success_rate=round(success_rate, 1),
                avg_time=round(row['avg_time'] or 0, 2),
                file_size=row['daily_file_size'] or 0
            ))
        
        # 월별 사용량 변환 (sqlite3.Row는 인덱싱 사용)
        monthly_usage_list = [
            MonthlyUsage(
                month=row['month'],
                conversions=row['conversions'] or 0,
                token_usage=row['token_usage'] or 0
            ) for row in monthly_usage
        ]
        
        return UsageHistoryResponse(
            success=True,
            data=UsageHistoryData(
                daily_stats=daily_stats,
                monthly_usage=monthly_usage_list
            )
        )
    
    def refresh_tokens(
        self,
        conn: sqlite3.Connection,
        user_id: int,
        request: RefreshTokensRequest,
        admin_id: int
    ) -> RefreshTokensResponse:
        """
        토큰 새로고침 (관리자용)
        
        Args:
            conn: 데이터베이스 연결
            user_id: 사용자 ID
            request: 새로고침 요청
            admin_id: 관리자 ID
        
        Returns:
            RefreshTokensResponse: 새로고침 응답
        """
        result = self.repository.refresh_user_tokens(
            conn=conn,
            user_id=request.user_id,
            token_amount=request.token_amount,
            admin_id=admin_id
        )
        
        return RefreshTokensResponse(
            success=True,
            message=f'{result["username"]}님에게 {request.token_amount}토큰이 추가되었습니다',
            data=result
        )
    
    def get_token_summary(
        self,
        conn: sqlite3.Connection,
        user_id: int
    ) -> TokenSummaryResponse:
        """
        토큰 요약 조회
        
        Args:
            conn: 데이터베이스 연결
            user_id: 사용자 ID
        
        Returns:
            TokenSummaryResponse: 토큰 요약 응답
        """
        summary = self.repository.get_token_summary(conn, user_id)
        
        # summary가 None인 경우 기본값 사용 (안전장치)
        if not summary:
            self.logger.warning(f"토큰 요약 정보 없음 (기본값 사용): user_id={user_id}")
            total_tokens = 0
            used_tokens = 0
            available_tokens = 0
        else:
            # sqlite3.Row는 인덱싱 사용
            total_tokens = summary['total_charged'] if summary['total_charged'] is not None else 0
            used_tokens = summary['total_used'] if summary['total_used'] is not None else 0
            available_tokens = total_tokens - used_tokens
        
        return TokenSummaryResponse(
            success=True,
            data=TokenSummaryData(
                total_tokens=int(total_tokens),
                used_tokens=int(used_tokens),
                available_tokens=int(available_tokens)
            ),
            last_updated=datetime.now().isoformat()
        )
    
    def get_activity_logs(
        self,
        conn: sqlite3.Connection,
        user_id: int,
        page: int,
        limit: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        activity_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        활동 로그 조회
        
        Args:
            conn: 데이터베이스 연결
            user_id: 사용자 ID
        
        Returns:
            Dict[str, Any]: 활동 로그 및 페이지네이션 정보
        """
        repo_result = self.repository.get_activity_logs(
            conn=conn,
            user_id=user_id,
            page=page,
            limit=limit,
            start_date=start_date,
            end_date=end_date,
            activity_type=activity_type
        )
        logs = repo_result.get('logs', [])
        total_count = repo_result.get('total_count', 0)
        
        # 결과 변환 및 번역 적용
        result_logs = []
        for log in logs:
            try:
                # sqlite3.Row를 dict로 변환
                if hasattr(log, 'keys'):
                    log_dict = dict(log)
                else:
                    # 튜플인 경우 처리
                    log_dict = {
                        'id': log[0] if len(log) > 0 else 0,
                        'timestamp': log[1] if len(log) > 1 else '',
                        'user_plan_snapshot': log[2] if len(log) > 2 else None,
                        'activity_type': log[3] if len(log) > 3 else '',
                        'details': log[4] if len(log) > 4 else None,
                        'token_change': log[5] if len(log) > 5 else 0,
                        'token_balance_before': log[6] if len(log) > 6 else None,
                        'token_balance_after': log[7] if len(log) > 7 else None,
                    }
                
                # 활동 유형 번역
                activity_type = log_dict.get('activity_type', '') or ''
                activity_type_korean = self.ACTIVITY_TYPE_MAP.get(activity_type, activity_type) or activity_type
                
                # 상세 정보 요약
                details_summary = self._summarize_details(
                    activity_type,
                    log_dict.get('details')
                ) or '세부 정보 없음'
                
                result_logs.append(ActivityLogItem(
                    id=log_dict.get('id', 0),
                    timestamp=log_dict.get('timestamp', ''),
                    user_plan_snapshot=log_dict.get('user_plan_snapshot'),
                    activity_type=activity_type,
                    details=log_dict.get('details'),
                    token_change=log_dict.get('token_change'),
                    token_balance_before=log_dict.get('token_balance_before'),
                    token_balance_after=log_dict.get('token_balance_after'),
                    activity_type_korean=activity_type_korean,
                    details_summary=details_summary
                ).dict())
            except Exception as e:
                logger.error(f"활동 로그 변환 오류: {str(e)}, log={log}", exc_info=True)
                continue
        
        total_pages = (total_count + limit - 1) // limit if limit > 0 else 0

        return {
            'success': True,
            'data': {
                'logs': result_logs,
                'pagination': {
                    'current_page': page,
                    'items_per_page': limit,
                    'total_pages': total_pages,
                    'total_count': total_count
                }
            }
        }
    
    def _summarize_details(self, activity_type: str, details_str: Optional[str]) -> str:
        """
        상세 정보를 요약 문장으로 변환
        
        Args:
            activity_type: 활동 타입
            details_str: 상세 정보 문자열
        
        Returns:
            str: 요약된 상세 정보
        """
        if not details_str:
            return '세부 정보 없음'
        
        try:
            details = json.loads(details_str) if isinstance(details_str, str) else details_str
            
            if activity_type == 'TOKEN_GRANT_BY_ADMIN':
                amount = details.get('granted_amount', 0)
                return f"{amount} 토큰 지급"
            
            elif activity_type == 'TOKEN_RESET_BY_ADMIN':
                return "토큰 잔액 초기화"
            
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

