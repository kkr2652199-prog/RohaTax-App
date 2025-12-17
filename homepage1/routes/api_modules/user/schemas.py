"""
User API Pydantic 스키마
데이터 검증 및 타입 안정성 제공
API Turbocharger 리팩토링 - Phase 1
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime

# ============================================
# Enums
# ============================================

class SortField(str, Enum):
    """정렬 필드 화이트리스트"""
    DATE = "date"
    LOG_TYPE = "log_type"
    FILENAME = "filename"
    CUSTOMER_NAME = "customer_name"
    AMOUNT = "amount"
    PLAN_TYPE = "plan_type"

class SortOrder(str, Enum):
    """정렬 순서"""
    ASC = "asc"
    DESC = "desc"

class LogType(str, Enum):
    """로그 타입"""
    CONVERSION = "CONVERSION"
    GRANT = "GRANT"
    RESET = "RESET"
    UNKNOWN = "UNKNOWN"

# ============================================
# Request Models
# ============================================

class MyHomeDataRequest(BaseModel):
    """마이홈 데이터 조회 요청"""
    limit: int = Field(
        default=15, 
        ge=1, 
        le=100, 
        description="페이지 크기 (1-100)"
    )
    offset: int = Field(
        default=0, 
        ge=0, 
        description="오프셋 (0 이상)"
    )
    sort: SortField = Field(
        default=SortField.DATE, 
        description="정렬 필드"
    )
    order: SortOrder = Field(
        default=SortOrder.DESC, 
        description="정렬 순서"
    )
    
    @validator('limit')
    def validate_limit(cls, v):
        """limit 검증: 1-100 범위"""
        if v < 1:
            raise ValueError('limit은 1 이상이어야 합니다')
        if v > 100:
            raise ValueError('limit은 100을 초과할 수 없습니다')
        return v
    
    @validator('offset')
    def validate_offset(cls, v):
        """offset 검증: 0 이상"""
        if v < 0:
            raise ValueError('offset은 0 이상이어야 합니다')
        return v
    
    class Config:
        """Pydantic 설정"""
        use_enum_values = True
        validate_assignment = True

class DeleteRequest(BaseModel):
    """삭제 요청"""
    ids: List[int] = Field(
        ..., 
        min_items=1, 
        description="삭제할 항목 ID 리스트"
    )
    
    @validator('ids')
    def validate_ids(cls, v):
        """ids 검증: 최소 1개 이상, 모든 값이 양수"""
        if not v or len(v) == 0:
            raise ValueError('삭제할 항목이 없습니다')
        if any(id_val <= 0 for id_val in v):
            raise ValueError('모든 ID는 1 이상이어야 합니다')
        return v
    
    class Config:
        """Pydantic 설정"""
        validate_assignment = True

class RefreshTokensRequest(BaseModel):
    """토큰 새로고침 요청"""
    user_id: int = Field(
        ..., 
        gt=0, 
        description="사용자 ID"
    )
    token_amount: int = Field(
        default=100, 
        gt=0, 
        le=10000, 
        description="토큰 양 (1-10000)"
    )
    
    @validator('user_id')
    def validate_user_id(cls, v):
        """user_id 검증: 1 이상"""
        if v <= 0:
            raise ValueError('user_id는 1 이상이어야 합니다')
        return v
    
    @validator('token_amount')
    def validate_token_amount(cls, v):
        """token_amount 검증: 1-10000 범위"""
        if v <= 0:
            raise ValueError('token_amount는 1 이상이어야 합니다')
        if v > 10000:
            raise ValueError('token_amount는 10000을 초과할 수 없습니다')
        return v
    
    class Config:
        """Pydantic 설정"""
        validate_assignment = True

# ============================================
# Response Models
# ============================================

class ActivityItem(BaseModel):
    """활동 항목"""
    id: int = Field(..., description="항목 ID")
    datetime_kst: str = Field(..., description="날짜/시간 (KST)")
    plan_type: str = Field(..., description="플랜 타입")
    log_type: LogType = Field(..., description="로그 타입")
    filename: Optional[str] = Field(None, description="파일명")
    customer_name: Optional[str] = Field(None, description="고객명")
    charge_amount: int = Field(..., ge=0, description="충전 금액 (0 이상)")
    usage_amount: int = Field(..., ge=0, description="사용 금액 (0 이상)")
    balance_after: int = Field(..., ge=0, description="잔액 (0 이상)")
    
    @validator('charge_amount', 'usage_amount', 'balance_after')
    def validate_non_negative(cls, v):
        """음수 금액 검증"""
        if v < 0:
            raise ValueError('금액은 0 이상이어야 합니다')
        return v
    
    class Config:
        """Pydantic 설정"""
        use_enum_values = True

class MyHomeDataResponse(BaseModel):
    """마이홈 데이터 응답"""
    success: bool = Field(default=True, description="성공 여부")
    total_count: int = Field(..., ge=0, description="총 개수 (0 이상)")
    activity_history: List[ActivityItem] = Field(..., description="활동 내역 리스트")
    
    @validator('total_count')
    def validate_total_count(cls, v):
        """total_count 검증: 0 이상"""
        if v < 0:
            raise ValueError('total_count는 0 이상이어야 합니다')
        return v
    
    class Config:
        """Pydantic 설정"""
        validate_assignment = True

class DeleteResponse(BaseModel):
    """삭제 응답"""
    success: bool = Field(default=True, description="성공 여부")
    deleted: int = Field(..., ge=0, description="삭제된 항목 수 (0 이상)")
    
    @validator('deleted')
    def validate_deleted(cls, v):
        """deleted 검증: 0 이상"""
        if v < 0:
            raise ValueError('deleted는 0 이상이어야 합니다')
        return v
    
    class Config:
        """Pydantic 설정"""
        validate_assignment = True

class UserInfo(BaseModel):
    """사용자 정보"""
    id: int = Field(..., description="사용자 ID")
    username: str = Field(..., description="사용자명")
    plan_type: str = Field(..., description="플랜 타입")
    is_admin: bool = Field(..., description="관리자 여부")
    created_at: str = Field(..., description="생성일시")
    
    class Config:
        """Pydantic 설정"""
        validate_assignment = True

class TokenStatus(BaseModel):
    """토큰 상태"""
    total_tokens: int = Field(..., ge=0, description="총 토큰 (0 이상)")
    used_tokens: int = Field(..., ge=0, description="사용 토큰 (0 이상)")
    available_tokens: int = Field(..., ge=0, description="사용 가능 토큰 (0 이상)")
    usage_percentage: float = Field(..., ge=0, le=100, description="사용률 (0-100)")
    
    @validator('usage_percentage')
    def validate_usage_percentage(cls, v):
        """usage_percentage 검증: 0-100 범위"""
        if v < 0:
            raise ValueError('usage_percentage는 0 이상이어야 합니다')
        if v > 100:
            raise ValueError('usage_percentage는 100을 초과할 수 없습니다')
        return v
    
    class Config:
        """Pydantic 설정"""
        validate_assignment = True

class ServiceStats(BaseModel):
    """서비스 통계"""
    total_conversions: int = Field(..., ge=0, description="총 변환 수 (0 이상)")
    successful_conversions: int = Field(..., ge=0, description="성공한 변환 수 (0 이상)")
    avg_conversion_time: float = Field(..., ge=0, description="평균 변환 시간 (0 이상)")
    total_file_size: int = Field(..., ge=0, description="총 파일 크기 (0 이상)")
    success_rate: float = Field(..., ge=0, le=100, description="성공률 (0-100)")
    
    @validator('success_rate')
    def validate_success_rate(cls, v):
        """success_rate 검증: 0-100 범위"""
        if v < 0:
            raise ValueError('success_rate는 0 이상이어야 합니다')
        if v > 100:
            raise ValueError('success_rate는 100을 초과할 수 없습니다')
        return v
    
    class Config:
        """Pydantic 설정"""
        validate_assignment = True

class RecentUsage(BaseModel):
    """최근 사용 내역"""
    action: str = Field(..., description="액션")
    meta: Dict[str, Any] = Field(..., description="메타데이터")
    created_at: str = Field(..., description="생성일시")
    
    class Config:
        """Pydantic 설정"""
        validate_assignment = True

class TokenStatusData(BaseModel):
    """토큰 상태 데이터"""
    user_info: UserInfo = Field(..., description="사용자 정보")
    token_status: TokenStatus = Field(..., description="토큰 상태")
    service_stats: ServiceStats = Field(..., description="서비스 통계")
    recent_usage: List[RecentUsage] = Field(..., description="최근 사용 내역")
    last_updated: str = Field(..., description="마지막 업데이트 시간")
    
    class Config:
        """Pydantic 설정"""
        validate_assignment = True

class TokenStatusResponse(BaseModel):
    """토큰 상태 응답"""
    success: bool = Field(default=True, description="성공 여부")
    data: TokenStatusData = Field(..., description="토큰 상태 데이터")
    
    class Config:
        """Pydantic 설정"""
        validate_assignment = True

class DailyStats(BaseModel):
    """일별 통계"""
    date: str = Field(..., description="날짜")
    conversions: int = Field(..., ge=0, description="변환 수 (0 이상)")
    success_rate: float = Field(..., ge=0, le=100, description="성공률 (0-100)")
    avg_time: float = Field(..., ge=0, description="평균 시간 (0 이상)")
    file_size: int = Field(..., ge=0, description="파일 크기 (0 이상)")
    
    class Config:
        """Pydantic 설정"""
        validate_assignment = True

class MonthlyUsage(BaseModel):
    """월별 사용량"""
    month: str = Field(..., description="월 (YYYY-MM)")
    conversions: int = Field(..., ge=0, description="변환 수 (0 이상)")
    token_usage: int = Field(..., ge=0, description="토큰 사용량 (0 이상)")
    
    class Config:
        """Pydantic 설정"""
        validate_assignment = True

class UsageHistoryData(BaseModel):
    """사용 내역 데이터"""
    daily_stats: List[DailyStats] = Field(..., description="일별 통계")
    monthly_usage: List[MonthlyUsage] = Field(..., description="월별 사용량")
    
    class Config:
        """Pydantic 설정"""
        validate_assignment = True

class UsageHistoryResponse(BaseModel):
    """사용 내역 응답"""
    success: bool = Field(default=True, description="성공 여부")
    data: UsageHistoryData = Field(..., description="사용 내역 데이터")
    
    class Config:
        """Pydantic 설정"""
        validate_assignment = True

class RefreshTokensResponse(BaseModel):
    """토큰 새로고침 응답"""
    success: bool = Field(default=True, description="성공 여부")
    message: str = Field(..., description="메시지")
    data: Dict[str, Any] = Field(..., description="응답 데이터")
    
    class Config:
        """Pydantic 설정"""
        validate_assignment = True

class TokenSummaryData(BaseModel):
    """토큰 요약 데이터"""
    total_tokens: int = Field(..., ge=0, description="총 토큰 (0 이상)")
    used_tokens: int = Field(..., ge=0, description="사용 토큰 (0 이상)")
    available_tokens: int = Field(..., ge=0, description="사용 가능 토큰 (0 이상)")
    
    class Config:
        """Pydantic 설정"""
        validate_assignment = True

class TokenSummaryResponse(BaseModel):
    """토큰 요약 응답"""
    success: bool = Field(default=True, description="성공 여부")
    data: TokenSummaryData = Field(..., description="토큰 요약 데이터")
    last_updated: str = Field(..., description="마지막 업데이트 시간")
    
    class Config:
        """Pydantic 설정"""
        validate_assignment = True

class ActivityLogItem(BaseModel):
    """활동 로그 항목"""
    id: int = Field(..., description="로그 ID")
    timestamp: str = Field(..., description="타임스탬프")
    user_plan_snapshot: Optional[str] = Field(None, description="사용자 플랜 스냅샷")
    activity_type: str = Field(..., description="활동 타입")
    details: Optional[str] = Field(None, description="상세 정보")
    token_change: Optional[int] = Field(None, description="토큰 변경량")
    token_balance_before: Optional[int] = Field(None, description="변경 전 토큰 잔액")
    token_balance_after: Optional[int] = Field(None, description="변경 후 토큰 잔액")
    activity_type_korean: str = Field(..., description="활동 타입 (한글)")
    details_summary: str = Field(..., description="상세 정보 요약")
    
    class Config:
        """Pydantic 설정"""
        validate_assignment = True

class ActivityLogsResponse(BaseModel):
    """활동 로그 응답"""
    success: bool = Field(default=True, description="성공 여부")
    data: List[ActivityLogItem] = Field(..., description="활동 로그 리스트")
    
    class Config:
        """Pydantic 설정"""
        validate_assignment = True

