"""
실시간 알림 시스템
- 중요한 파일 변경 시 즉시 알림
- 웹 접근 실패 시 즉시 알림
- 자동 복구 완료 시 알림
"""

import os
import threading
import time
from datetime import datetime
from typing import List, Dict, Callable
import json

class NotificationSystem:
    """실시간 알림 시스템"""
    
    def __init__(self):
        self.notifications = []
        self.subscribers = []
        self.is_running = False
        self.notification_thread = None
        self.max_notifications = 1000
        
        # 알림 우선순위
        self.priority_levels = {
            'critical': 1,    # 시스템 중단, 웹 접근 불가
            'high': 2,       # 중요한 파일 변경, 복구 필요
            'medium': 3,      # 일반적인 파일 변경
            'low': 4         # 정보성 알림
        }
    
    def add_subscriber(self, callback: Callable):
        """알림 구독자 추가"""
        self.subscribers.append(callback)
    
    def remove_subscriber(self, callback: Callable):
        """알림 구독자 제거"""
        if callback in self.subscribers:
            self.subscribers.remove(callback)
    
    def send_notification(self, title: str, message: str, priority: str = 'medium', 
                         category: str = 'system', data: Dict = None):
        """알림 전송"""
        notification = {
            'id': len(self.notifications) + 1,
            'timestamp': datetime.now().isoformat(),
            'title': title,
            'message': message,
            'priority': priority,
            'priority_level': self.priority_levels.get(priority, 3),
            'category': category,
            'data': data or {},
            'read': False
        }
        
        # 알림 목록에 추가
        self.notifications.append(notification)
        
        # 최대 개수 초과 시 오래된 알림 삭제
        if len(self.notifications) > self.max_notifications:
            self.notifications = self.notifications[-self.max_notifications:]
        
        # 구독자들에게 알림 전송
        for subscriber in self.subscribers:
            try:
                subscriber(notification)
            except Exception as e:
                print(f"알림 전송 실패: {e}")
        
        # 콘솔에 즉시 출력
        priority_symbol = {
            'critical': '🚨',
            'high': '⚠️',
            'medium': 'ℹ️',
            'low': '📝'
        }.get(priority, 'ℹ️')
        
        print(f"{priority_symbol} [{priority.upper()}] {title}: {message}")
    
    def send_file_move_notification(self, file_path: str, target_path: str, success: bool):
        """파일 이동 알림"""
        if success:
            self.send_notification(
                title="파일 이동 완료",
                message=f"파일이 성공적으로 이동되었습니다: {os.path.basename(file_path)} → {target_path}",
                priority='medium',
                category='file_operation',
                data={'file_path': file_path, 'target_path': target_path, 'operation': 'move'}
            )
        else:
            self.send_notification(
                title="파일 이동 실패",
                message=f"파일 이동에 실패했습니다: {os.path.basename(file_path)}",
                priority='high',
                category='file_operation',
                data={'file_path': file_path, 'target_path': target_path, 'operation': 'move'}
            )
    
    def send_web_access_failure_notification(self, file_path: str, web_url: str, error: str):
        """웹 접근 실패 알림"""
        self.send_notification(
            title="웹 접근 실패",
            message=f"정적 파일에 웹에서 접근할 수 없습니다: {os.path.basename(file_path)}",
            priority='critical',
            category='web_access',
            data={'file_path': file_path, 'web_url': web_url, 'error': error}
        )
    
    def send_auto_recovery_notification(self, file_path: str, recovered_path: str, success: bool):
        """자동 복구 알림"""
        if success:
            self.send_notification(
                title="자동 복구 완료",
                message=f"파일이 자동으로 복구되었습니다: {os.path.basename(file_path)} → {recovered_path}",
                priority='high',
                category='auto_recovery',
                data={'file_path': file_path, 'recovered_path': recovered_path, 'operation': 'recovery'}
            )
        else:
            self.send_notification(
                title="자동 복구 실패",
                message=f"파일 자동 복구에 실패했습니다: {os.path.basename(file_path)}",
                priority='critical',
                category='auto_recovery',
                data={'file_path': file_path, 'operation': 'recovery'}
            )
    
    def send_validation_notification(self, file_path: str, validation_result: bool, message: str):
        """검증 결과 알림"""
        priority = 'high' if not validation_result else 'medium'
        self.send_notification(
            title="파일 검증 결과",
            message=f"{os.path.basename(file_path)}: {message}",
            priority=priority,
            category='validation',
            data={'file_path': file_path, 'validation_result': validation_result, 'message': message}
        )
    
    def get_notifications(self, category: str = None, priority: str = None, 
                         unread_only: bool = False, limit: int = 50) -> List[Dict]:
        """알림 목록 조회"""
        filtered_notifications = self.notifications.copy()
        
        # 카테고리 필터링
        if category:
            filtered_notifications = [n for n in filtered_notifications if n['category'] == category]
        
        # 우선순위 필터링
        if priority:
            filtered_notifications = [n for n in filtered_notifications if n['priority'] == priority]
        
        # 읽지 않은 알림만 필터링
        if unread_only:
            filtered_notifications = [n for n in filtered_notifications if not n['read']]
        
        # 최신순 정렬 및 개수 제한
        filtered_notifications.sort(key=lambda x: x['timestamp'], reverse=True)
        return filtered_notifications[:limit]
    
    def mark_as_read(self, notification_id: int):
        """알림을 읽음으로 표시"""
        for notification in self.notifications:
            if notification['id'] == notification_id:
                notification['read'] = True
                break
    
    def mark_all_as_read(self):
        """모든 알림을 읽음으로 표시"""
        for notification in self.notifications:
            notification['read'] = True
    
    def get_notification_stats(self) -> Dict:
        """알림 통계 반환"""
        total = len(self.notifications)
        unread = sum(1 for n in self.notifications if not n['read'])
        
        by_priority = {}
        for priority in self.priority_levels.keys():
            by_priority[priority] = sum(1 for n in self.notifications if n['priority'] == priority)
        
        by_category = {}
        categories = set(n['category'] for n in self.notifications)
        for category in categories:
            by_category[category] = sum(1 for n in self.notifications if n['category'] == category)
        
        return {
            'total': total,
            'unread': unread,
            'read': total - unread,
            'by_priority': by_priority,
            'by_category': by_category
        }
    
    def clear_notifications(self, older_than_days: int = 7):
        """오래된 알림 삭제"""
        cutoff_date = datetime.now().timestamp() - (older_than_days * 24 * 60 * 60)
        
        original_count = len(self.notifications)
        self.notifications = [
            n for n in self.notifications 
            if datetime.fromisoformat(n['timestamp']).timestamp() > cutoff_date
        ]
        
        deleted_count = original_count - len(self.notifications)
        if deleted_count > 0:
            self.send_notification(
                title="알림 정리 완료",
                message=f"{deleted_count}개의 오래된 알림이 삭제되었습니다.",
                priority='low',
                category='system'
            )

# 전역 인스턴스
notification_system = NotificationSystem()
