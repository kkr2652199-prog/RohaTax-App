"""
관리자 API 모듈
/api/admin/* 엔드포인트를 처리하는 Blueprint
"""

from flask import Blueprint, jsonify, session
from core.db import get_conn_optimized as get_conn
import sqlite3
from datetime import datetime

admin_api_bp = Blueprint('admin_api', __name__, url_prefix='/api')


@admin_api_bp.route('/admin/dashboard')
def admin_dashboard():
    """관리자 대시보드 API"""
    if not session.get('user_id') or not session.get('is_admin'):
        return jsonify({'error': '관리자 권한이 필요합니다'}), 403
    
    try:
        with get_conn() as conn:
            conn.row_factory = sqlite3.Row
            
            # 전체 사용자 통계
            user_stats = conn.execute(
                """
                SELECT 
                    COUNT(*) as total_users,
                    COUNT(CASE WHEN is_active = 1 THEN 1 END) as active_users,
                    COUNT(CASE WHEN plan_type = 'vip' THEN 1 END) as vip_users,
                    COUNT(CASE WHEN created_at >= date('now', '-30 days') THEN 1 END) as new_users_30d
                FROM users 
                WHERE COALESCE(is_deleted, 0) = 0
                """
            ).fetchone()
            
            # 토큰 사용 통계 (표준 법률: activity_logs 기반, 가장 최근 리셋 이후만 계산)
            # 표준 법률(/api/v2/user/token-summary)과 완전히 동일한 로직을 사용
            token_stats = conn.execute(
                """
                WITH user_resets AS (
                    -- 각 사용자별로 가장 최근의 TOKEN_RESET_BY_ADMIN 이벤트 시간을 찾는다 (표준 법률)
                    SELECT 
                        user_id,
                        MAX(timestamp) as reset_time
                    FROM activity_logs
                    WHERE activity_type = 'TOKEN_RESET_BY_ADMIN'
                      AND COALESCE(is_deleted, 0) = 0
                      AND user_id IN (SELECT id FROM users WHERE COALESCE(is_deleted, 0) = 0)
                    GROUP BY user_id
                ),
                user_summaries AS (
                    -- 각 사용자별로 표준 법률에 따라 토큰 계산 (리셋 이후만)
                    SELECT 
                        al.user_id,
                        COALESCE(SUM(CASE WHEN al.token_change > 0 AND al.activity_type != 'TOKEN_RESET_BY_ADMIN' THEN al.token_change ELSE 0 END), 0) as total_charged,
                        COALESCE(SUM(CASE WHEN al.token_change < 0 AND al.activity_type != 'TOKEN_RESET_BY_ADMIN' THEN ABS(al.token_change) ELSE 0 END), 0) as total_used
                    FROM activity_logs al
                    LEFT JOIN user_resets ur ON al.user_id = ur.user_id
                    WHERE COALESCE(al.is_deleted, 0) = 0
                      AND (ur.reset_time IS NULL OR al.timestamp >= ur.reset_time)
                      AND al.user_id IN (SELECT id FROM users WHERE COALESCE(is_deleted, 0) = 0)
                    GROUP BY al.user_id
                )
                SELECT 
                    COALESCE(SUM(total_charged), 0) as total_tokens_issued,
                    COALESCE(SUM(total_used), 0) as total_tokens_used,
                    COALESCE(AVG(total_charged - total_used), 0) as avg_available_tokens
                FROM user_summaries
                """
            ).fetchone()
            
            # 변환 통계
            conversion_stats = conn.execute(
                """
                SELECT 
                    COUNT(*) as total_conversions,
                    COUNT(CASE WHEN status = 'success' THEN 1 END) as successful_conversions,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_conversions,
                    AVG(conversion_time) as avg_conversion_time,
                    SUM(file_size) as total_file_size
                FROM conversion_logs 
                WHERE created_at >= date('now', '-30 days')
                """
            ).fetchone()
            
            # 최근 활동
            recent_activity = conn.execute(
                """
                SELECT 
                    u.username,
                    cl.original_filename,
                    cl.status,
                    cl.conversion_time,
                    cl.created_at
                FROM conversion_logs cl
                JOIN users u ON cl.user_id = u.id
                WHERE cl.created_at >= date('now', '-7 days')
                ORDER BY cl.created_at DESC
                LIMIT 20
                """
            ).fetchall()
            
            return jsonify({
                'success': True,
                'data': {
                    'user_stats': {
                        'total_users': user_stats['total_users'],
                        'active_users': user_stats['active_users'],
                        'vip_users': user_stats['vip_users'],
                        'new_users_30d': user_stats['new_users_30d']
                    },
                    'token_stats': {
                        'total_issued': token_stats['total_tokens_issued'] or 0,
                        'total_used': token_stats['total_tokens_used'] or 0,
                        'avg_available': round(token_stats['avg_available_tokens'] or 0, 1),
                        'usage_rate': round(
                            (token_stats['total_tokens_used'] / token_stats['total_tokens_issued'] * 100)
                            if token_stats['total_tokens_issued'] > 0 else 0, 1
                        )
                    },
                    'conversion_stats': {
                        'total_conversions': conversion_stats['total_conversions'],
                        'successful_conversions': conversion_stats['successful_conversions'],
                        'failed_conversions': conversion_stats['failed_conversions'],
                        'success_rate': round(
                            (conversion_stats['successful_conversions'] / conversion_stats['total_conversions'] * 100)
                            if conversion_stats['total_conversions'] > 0 else 0, 1
                        ),
                        'avg_conversion_time': round(conversion_stats['avg_conversion_time'] or 0, 2),
                        'total_file_size': conversion_stats['total_file_size'] or 0
                    },
                    'recent_activity': [
                        {
                            'username': row['username'],
                            'filename': row['original_filename'],
                            'status': row['status'],
                            'conversion_time': round(row['conversion_time'] or 0, 2),
                            'created_at': row['created_at']
                        } for row in recent_activity
                    ],
                    'last_updated': datetime.now().isoformat()
                }
            })
            
    except Exception as e:
        return jsonify({'error': f'서버 오류: {str(e)}'}), 500

