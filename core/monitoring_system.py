"""
변환 성공률 추적 및 모니터링 시스템
- 실시간 변환 성공률 추적
- 사용자 활동 로그 분석
- 성능 메트릭 수집
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from core.db import get_conn_optimized as get_conn

logger = logging.getLogger(__name__)

@dataclass
class ConversionMetrics:
    """변환 메트릭 데이터 클래스"""
    total_conversions: int
    successful_conversions: int
    failed_conversions: int
    success_rate: float
    avg_processing_time: float
    total_users: int
    active_users: int
    period_days: int

@dataclass
class UserActivity:
    """사용자 활동 데이터 클래스"""
    user_id: int
    username: str
    last_login: str
    total_conversions: int
    successful_conversions: int
    tokens_used: int
    tokens_remaining: int
    activity_score: float

class MonitoringSystem:
    def __init__(self):
        self.metrics_cache = {}
        self.cache_duration = 300  # 5분 캐시
    
    def get_conversion_success_rate(self, days: int = 30) -> ConversionMetrics:
        """변환 성공률 조회"""
        cache_key = f"success_rate_{days}"
        
        # 캐시 확인
        if cache_key in self.metrics_cache:
            cached_data, cached_time = self.metrics_cache[cache_key]
            if (datetime.now() - cached_time).seconds < self.cache_duration:
                return cached_data
        
        try:
            with get_conn() as conn:
                conn.row_factory = sqlite3.Row
                
                # 기본 통계
                stats = conn.execute("""
                    SELECT 
                        COUNT(*) as total_conversions,
                        SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful_conversions,
                        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_conversions,
                        AVG(CASE WHEN status = 'success' THEN conversion_time ELSE NULL END) as avg_processing_time
                    FROM conversion_logs 
                    WHERE created_at >= datetime('now', '-{} days')
                """.format(days)).fetchone()
                
                # 사용자 통계
                user_stats = conn.execute("""
                    SELECT 
                        COUNT(*) as total_users,
                        COUNT(CASE WHEN last_login >= datetime('now', '-7 days') THEN 1 END) as active_users
                    FROM users 
                    WHERE is_deleted = 0
                """).fetchone()
                
                # 성공률 계산
                success_rate = 0.0
                if stats['total_conversions'] > 0:
                    success_rate = (stats['successful_conversions'] / stats['total_conversions']) * 100
                
                metrics = ConversionMetrics(
                    total_conversions=stats['total_conversions'] or 0,
                    successful_conversions=stats['successful_conversions'] or 0,
                    failed_conversions=stats['failed_conversions'] or 0,
                    success_rate=success_rate,
                    avg_processing_time=stats['avg_processing_time'] or 0.0,
                    total_users=user_stats['total_users'] or 0,
                    active_users=user_stats['active_users'] or 0,
                    period_days=days
                )
                
                # 캐시 저장
                self.metrics_cache[cache_key] = (metrics, datetime.now())
                
                logger.info(f"📊 변환 성공률 조회 완료: {success_rate:.1f}% ({days}일)")
                return metrics
                
        except Exception as e:
            logger.error(f"변환 성공률 조회 실패: {e}")
            return ConversionMetrics(0, 0, 0, 0.0, 0.0, 0, 0, days)
    
    def get_user_activity_analysis(self, days: int = 30) -> List[UserActivity]:
        """사용자 활동 분석"""
        try:
            with get_conn() as conn:
                conn.row_factory = sqlite3.Row
                
                users = conn.execute("""
                    SELECT 
                        u.id, u.username, u.last_login,
                        u.token_balance, u.tokens_used,
                        COUNT(cl.id) as total_conversions,
                        SUM(CASE WHEN cl.status = 'success' THEN 1 ELSE 0 END) as successful_conversions
                    FROM users u
                    LEFT JOIN conversion_logs cl ON u.id = cl.user_id 
                        AND cl.created_at >= datetime('now', '-{} days')
                    WHERE u.is_deleted = 0
                    GROUP BY u.id, u.username, u.last_login, u.token_balance, u.tokens_used
                    ORDER BY total_conversions DESC
                """.format(days)).fetchall()
                
                activities = []
                for user in users:
                    # 활동 점수 계산 (변환 횟수 + 최근 로그인)
                    activity_score = 0.0
                    
                    # 변환 활동 점수 (70%)
                    if user['total_conversions'] > 0:
                        conversion_score = min(user['total_conversions'] * 10, 70)
                        activity_score += conversion_score
                    
                    # 최근 로그인 점수 (30%)
                    if user['last_login']:
                        last_login = datetime.fromisoformat(user['last_login'].replace('Z', '+00:00'))
                        days_since_login = (datetime.now() - last_login).days
                        
                        if days_since_login <= 7:
                            login_score = 30
                        elif days_since_login <= 30:
                            login_score = 20
                        else:
                            login_score = 10
                        
                        activity_score += login_score
                    
                    activities.append(UserActivity(
                        user_id=user['id'],
                        username=user['username'],
                        last_login=user['last_login'] or 'Never',
                        total_conversions=user['total_conversions'] or 0,
                        successful_conversions=user['successful_conversions'] or 0,
                        tokens_used=user['tokens_used'] or 0,
                        tokens_remaining=(user['token_balance'] or 0) - (user['tokens_used'] or 0),
                        activity_score=activity_score
                    ))
                
                logger.info(f"👥 사용자 활동 분석 완료: {len(activities)}명 ({days}일)")
                return activities
                
        except Exception as e:
            logger.error(f"사용자 활동 분석 실패: {e}")
            return []
    
    def get_performance_trends(self, days: int = 7) -> Dict:
        """성능 트렌드 분석"""
        try:
            with get_conn() as conn:
                conn.row_factory = sqlite3.Row
                
                # 일별 통계
                daily_stats = conn.execute("""
                    SELECT 
                        DATE(created_at) as date,
                        COUNT(*) as total_conversions,
                        SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful_conversions,
                        AVG(CASE WHEN status = 'success' THEN conversion_time ELSE NULL END) as avg_time
                    FROM conversion_logs 
                    WHERE created_at >= datetime('now', '-{} days')
                    GROUP BY DATE(created_at)
                    ORDER BY date DESC
                """.format(days)).fetchall()
                
                # 시간대별 통계
                hourly_stats = conn.execute("""
                    SELECT 
                        strftime('%H', created_at) as hour,
                        COUNT(*) as conversions,
                        AVG(CASE WHEN status = 'success' THEN conversion_time ELSE NULL END) as avg_time
                    FROM conversion_logs 
                    WHERE created_at >= datetime('now', '-{} days')
                    GROUP BY strftime('%H', created_at)
                    ORDER BY hour
                """.format(days)).fetchall()
                
                trends = {
                    'daily': [dict(row) for row in daily_stats],
                    'hourly': [dict(row) for row in hourly_stats],
                    'summary': {
                        'total_days': days,
                        'avg_daily_conversions': sum(row['total_conversions'] for row in daily_stats) / max(len(daily_stats), 1),
                        'peak_hour': max(hourly_stats, key=lambda x: x['conversions'])['hour'] if hourly_stats else None
                    }
                }
                
                logger.info(f"📈 성능 트렌드 분석 완료: {days}일")
                return trends
                
        except Exception as e:
            logger.error(f"성능 트렌드 분석 실패: {e}")
            return {'daily': [], 'hourly': [], 'summary': {}}
    
    def generate_monitoring_report(self) -> Dict:
        """모니터링 리포트 생성"""
        logger.info("📋 모니터링 리포트 생성 시작")
        
        # 기본 메트릭
        metrics_30d = self.get_conversion_success_rate(30)
        metrics_7d = self.get_conversion_success_rate(7)
        
        # 사용자 활동
        user_activities = self.get_user_activity_analysis(30)
        
        # 성능 트렌드
        trends = self.get_performance_trends(7)
        
        # 상위 활성 사용자
        top_users = sorted(user_activities, key=lambda x: x.activity_score, reverse=True)[:5]
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'period': '30일',
            'metrics': {
                '30_days': {
                    'total_conversions': metrics_30d.total_conversions,
                    'success_rate': round(metrics_30d.success_rate, 2),
                    'avg_processing_time': round(metrics_30d.avg_processing_time, 2),
                    'total_users': metrics_30d.total_users,
                    'active_users': metrics_30d.active_users
                },
                '7_days': {
                    'total_conversions': metrics_7d.total_conversions,
                    'success_rate': round(metrics_7d.success_rate, 2),
                    'avg_processing_time': round(metrics_7d.avg_processing_time, 2)
                }
            },
            'user_activity': {
                'total_users': len(user_activities),
                'active_users': len([u for u in user_activities if u.activity_score > 50]),
                'top_users': [
                    {
                        'username': user.username,
                        'conversions': user.total_conversions,
                        'success_rate': round((user.successful_conversions / max(user.total_conversions, 1)) * 100, 1),
                        'activity_score': round(user.activity_score, 1)
                    }
                    for user in top_users
                ]
            },
            'trends': trends,
            'recommendations': self._generate_recommendations(metrics_30d, user_activities)
        }
        
        logger.info("✅ 모니터링 리포트 생성 완료")
        return report
    
    def _generate_recommendations(self, metrics: ConversionMetrics, activities: List[UserActivity]) -> List[str]:
        """개선 권장사항 생성"""
        recommendations = []
        
        # 성공률 기반 권장사항
        if metrics.success_rate < 90:
            recommendations.append(f"⚠️ 변환 성공률이 {metrics.success_rate:.1f}%로 낮습니다. 변환 로직 개선이 필요합니다.")
        
        if metrics.success_rate > 95:
            recommendations.append(f"✅ 변환 성공률이 {metrics.success_rate:.1f}%로 우수합니다.")
        
        # 사용자 활동 기반 권장사항
        inactive_users = len([u for u in activities if u.activity_score < 20])
        if inactive_users > 0:
            recommendations.append(f"👥 {inactive_users}명의 비활성 사용자가 있습니다. 재활성화 캠페인을 고려하세요.")
        
        # 처리 시간 기반 권장사항
        if metrics.avg_processing_time > 60:
            recommendations.append(f"⏱️ 평균 처리 시간이 {metrics.avg_processing_time:.1f}초로 길어 성능 최적화가 필요합니다.")
        
        # 토큰 사용량 기반 권장사항
        high_token_users = len([u for u in activities if u.tokens_used > 50])
        if high_token_users > 0:
            recommendations.append(f"💰 {high_token_users}명의 사용자가 높은 토큰을 사용하고 있습니다. 수익 기회가 있습니다.")
        
        return recommendations

# 전역 인스턴스
monitoring_system = MonitoringSystem()
