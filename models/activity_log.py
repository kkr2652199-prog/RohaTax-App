"""
활동 로그 데이터베이스 모델

제국의 모든 활동 기록을 담는 중앙 정보국의 핵심 모델

주의: 이 모델은 SQLAlchemy를 사용합니다.
설치가 필요한 경우: pip install sqlalchemy
"""
from datetime import datetime
from typing import Optional, Dict, Any
import json

# SQLAlchemy 의존성 (설치 필요: pip install sqlalchemy)
try:
    from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import relationship
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    # SQLAlchemy가 설치되지 않은 경우를 위한 더미 클래스
    SQLALCHEMY_AVAILABLE = False
    Column = Integer = String = Text = DateTime = ForeignKey = None
    declarative_base = lambda: type('Base', (), {})
    relationship = lambda *args, **kwargs: None

Base = declarative_base()


class ActivityLog(Base):
    """
    활동 로그 모델 클래스
    
    사용자와 관리자의 모든 활동을 기록하여 완벽한 감사 추적 기능을 제공합니다.
    """
    __tablename__ = 'activity_logs'
    
    # 기본 키 및 식별 정보
    id = Column(Integer, primary_key=True, autoincrement=True, comment='고유 식별자')
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=False, comment='활동의 대상이 되는 사용자 ID')
    timestamp = Column(DateTime, nullable=False, default=datetime.now, comment='활동이 발생한 시간')
    
    # 활동 주체 (Actor) 정보
    performed_by_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, comment='활동을 수행한 주체 (사용자 자신 or 관리자). NULL일 경우 시스템.')
    performed_by_type = Column(String(20), nullable=True, comment='활동 주체 유형: USER, ADMIN, SYSTEM')
    
    # 활동 분류 정보
    activity_type = Column(String(100), nullable=False, comment='활동 유형 (예: LOGIN, FILE_CONVERT, TOKEN_CHANGE, TOKEN_RESET_BY_ADMIN)')
    details = Column(Text, nullable=True, comment='활동에 대한 상세 정보 (JSON 형식)')
    
    # 토큰 및 비용 정보 ('경제 헌법')
    token_change = Column(Integer, nullable=False, default=0, comment='토큰 변화량 (양수: 충전, 음수: 사용)')
    potential_cost = Column(Integer, nullable=False, default=0, comment='예상 비용')
    token_balance_before = Column(Integer, nullable=True, comment='활동 전 토큰 잔액')
    token_balance_after = Column(Integer, nullable=True, comment='활동 후 토큰 잔액')
    
    # 데이터 스냅샷
    user_plan_snapshot = Column(String(50), nullable=True, comment='활동 당시 사용자의 등급 (예: vip, gold). 변경 추적용.')
    
    # 소프트 삭제 플래그
    is_deleted = Column(Integer, nullable=False, default=0, comment='삭제 여부 (0: 활성, 1: 삭제됨)')
    
    # 관계 설정 (선택적)
    # user = relationship('User', foreign_keys=[user_id], backref='activity_logs')
    # performed_by = relationship('User', foreign_keys=[performed_by_id], backref='performed_activities')
    
    def __repr__(self):
        return f"<ActivityLog(id={self.id}, user_id={self.user_id}, activity_type='{self.activity_type}', timestamp='{self.timestamp}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        모델 인스턴스를 딕셔너리로 변환
        
        Returns:
            Dict: 활동 로그 데이터를 담은 딕셔너리
        """
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'timestamp': self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else str(self.timestamp),
            'performed_by_id': self.performed_by_id,
            'performed_by_type': self.performed_by_type,
            'activity_type': self.activity_type,
            'token_change': self.token_change,
            'potential_cost': self.potential_cost,
            'token_balance_before': self.token_balance_before,
            'token_balance_after': self.token_balance_after,
            'user_plan_snapshot': self.user_plan_snapshot,
            'is_deleted': self.is_deleted
        }
        
        # details를 JSON으로 파싱 시도
        if self.details:
            try:
                result['details'] = json.loads(self.details)
            except (json.JSONDecodeError, TypeError):
                result['details'] = self.details
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActivityLog':
        """
        딕셔너리로부터 모델 인스턴스 생성
        
        Args:
            data: 활동 로그 데이터를 담은 딕셔너리
            
        Returns:
            ActivityLog: 생성된 모델 인스턴스
        """
        # details를 JSON 문자열로 변환
        if 'details' in data and isinstance(data['details'], (dict, list)):
            data['details'] = json.dumps(data['details'], ensure_ascii=False)
        
        # timestamp를 datetime으로 변환
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            try:
                data['timestamp'] = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                data['timestamp'] = datetime.now()
        
        return cls(**data)

