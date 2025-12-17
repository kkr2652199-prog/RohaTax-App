"""
관리자 대시보드 통계 API
Chart.js를 위한 통계 데이터 제공
"""

import sqlite3
from datetime import datetime, timedelta
from flask import jsonify
from core.responses import success, error
from core.db import get_conn_optimized as get_conn
from ..utils.auth import ensure_admin_for_json
from . import admin_bp


@admin_bp.route('/admin/api/dashboard-stats', methods=['GET'])
def get_dashboard_stats():
    """
    관리자 대시보드 통계 데이터 조회
    - daily_token_usage: 최근 7일간 날짜별 토큰 사용량
    - activity_distribution: 최근 30일간 활동 유형별 분포
    - hourly_traffic: 최근 24시간 시간대별 활동 건수
    """
    _, guard_response = ensure_admin_for_json()
    if guard_response is not None:
        return guard_response

    try:
        with get_conn() as conn:
            conn.row_factory = sqlite3.Row
            
            # 1. daily_token_usage: 최근 7일간 날짜별 토큰 사용량 합계
            daily_token_usage = _get_daily_token_usage(conn, days=7)
            
            # 2. activity_distribution: 최근 30일간 activity_type별 건수
            activity_distribution = _get_activity_distribution(conn, days=30)
            
            # 3. hourly_traffic: 최근 24시간 시간대별 활동 건수
            hourly_traffic = _get_hourly_traffic(conn, hours=24)
            
            return success('ok', data={
                'daily_token_usage': daily_token_usage,
                'activity_distribution': activity_distribution,
                'hourly_traffic': hourly_traffic
            })
            
    except Exception as e:
        return error(f'통계 데이터 조회 중 오류가 발생했습니다: {str(e)}', status=500)


def _get_daily_token_usage(conn: sqlite3.Connection, days: int = 7) -> list:
    """
    최근 N일간 날짜별 토큰 사용량 합계
    - token_history 테이블에서 change_type='use'인 경우만 집계
    - 빈 날짜는 0으로 채움
    - SQLite 호환: strftime 사용
    """
    # 최근 N일 날짜 범위 계산
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days - 1)
    
    # SQL GROUP BY로 집계 (성능 최적화)
    # SQLite는 DATE() 함수 대신 strftime('%Y-%m-%d', ...) 사용
    query = """
        SELECT 
            strftime('%Y-%m-%d', created_at) as date,
            COALESCE(SUM(ABS(amount)), 0) as total_usage
        FROM token_history
        WHERE change_type = 'use'
          AND strftime('%Y-%m-%d', created_at) >= ?
          AND strftime('%Y-%m-%d', created_at) <= ?
        GROUP BY strftime('%Y-%m-%d', created_at)
        ORDER BY date ASC
    """
    
    rows = conn.execute(query, (start_date.isoformat(), end_date.isoformat())).fetchall()
    
    # 결과를 딕셔너리로 변환
    usage_dict = {row['date']: int(row['total_usage']) for row in rows}
    
    # 빈 날짜를 0으로 채워서 반환
    result = []
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.isoformat()
        result.append({
            'date': date_str,
            'usage': usage_dict.get(date_str, 0)
        })
        current_date += timedelta(days=1)
    
    return result


def _get_activity_distribution(conn: sqlite3.Connection, days: int = 30) -> list:
    """
    최근 N일간 activity_type별 건수 (Pie 차트용)
    - activity_logs 테이블에서 집계
    """
    start_date = (datetime.now() - timedelta(days=days)).isoformat()
    
    # SQL GROUP BY로 집계 (성능 최적화)
    query = """
        SELECT 
            activity_type,
            COUNT(*) as count
        FROM activity_logs
        WHERE timestamp >= ?
          AND COALESCE(is_deleted, 0) = 0
        GROUP BY activity_type
        ORDER BY count DESC
    """
    
    rows = conn.execute(query, (start_date,)).fetchall()
    
    # 활동 유형 한글 번역
    activity_type_korean = {
        'FILE_CONVERT': '파일 변환',
        'TOKEN_GRANT_BY_ADMIN': '토큰 지급 (관리자)',
        'TOKEN_RESET_BY_ADMIN': '토큰 초기화 (관리자)',
        'GRADE_CHANGE_BY_ADMIN': '등급 변경 (관리자)',
        'USER_SOFT_DELETE_BY_ADMIN': '계정 비활성화 (관리자)',
        'USER_RESTORE_BY_ADMIN': '계정 복구 (관리자)',
        'USER_PURGE_BY_ADMIN': '계정 영구 삭제 (관리자)',
        'TOKEN_USE': '토큰 사용',
        'TOKEN_CHARGE': '토큰 충전',
        'LOGIN': '로그인',
        'LOGOUT': '로그아웃',
        'PROFILE_UPDATE': '프로필 수정'
    }
    
    result = []
    for row in rows:
        activity_type = row['activity_type']
        result.append({
            'type': activity_type,
            'label': activity_type_korean.get(activity_type, activity_type),
            'count': int(row['count'])
        })
    
    return result


def _get_hourly_traffic(conn: sqlite3.Connection, hours: int = 24) -> list:
    """
    최근 N시간 동안 시간대별(0~23시) 활동 발생 건수
    - activity_logs 테이블에서 집계
    - 빈 시간대는 0으로 채움
    - 최근 24시간 = 지금으로부터 24시간 전부터 현재까지
    """
    # 최근 24시간 전 시점 계산
    start_datetime = datetime.now() - timedelta(hours=hours)
    start_datetime_str = start_datetime.strftime('%Y-%m-%d %H:%M:%S')
    
    # SQL GROUP BY로 집계 (성능 최적화)
    # SQLite의 strftime으로 시간 추출
    query = """
        SELECT 
            CAST(strftime('%H', timestamp) AS INTEGER) as hour,
            COUNT(*) as count
        FROM activity_logs
        WHERE timestamp >= ?
          AND COALESCE(is_deleted, 0) = 0
        GROUP BY CAST(strftime('%H', timestamp) AS INTEGER)
        ORDER BY hour ASC
    """
    
    rows = conn.execute(query, (start_datetime_str,)).fetchall()
    
    # 결과를 딕셔너리로 변환
    traffic_dict = {row['hour']: int(row['count']) for row in rows}
    
    # 빈 시간대를 0으로 채워서 반환 (0~23시)
    result = []
    for hour in range(24):
        result.append({
            'hour': hour,
            'count': traffic_dict.get(hour, 0)
        })
    
    return result

