"""
결제 관리 시스템 Pydantic 스키마
Jet Engine 기반 데이터 검증 및 타입 안정성 제공
"""

from pydantic import BaseModel, Field, validator
from typing import Optional
from enum import Enum
from datetime import datetime


class PaymentStatus(str, Enum):
    """결제 상태 Enum"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PaymentCreate(BaseModel):
    """결제 생성 요청 스키마"""
    user_id: int = Field(..., gt=0, description="사용자 ID")
    order_id: str = Field(..., min_length=1, max_length=100, description="주문 ID (Unique)")
    amount: int = Field(..., gt=0, description="결제 금액 (원 단위)")
    token_amount: int = Field(..., ge=0, description="지급될 토큰 수량")
    pg_provider: Optional[str] = Field(None, max_length=50, description="PG사 정보")
    status: PaymentStatus = Field(PaymentStatus.PENDING, description="결제 상태")
    
    @validator('order_id')
    def validate_order_id(cls, v):
        """주문 ID 검증"""
        if not v or not v.strip():
            raise ValueError('주문 ID는 필수입니다')
        return v.strip()
    
    @validator('amount')
    def validate_amount(cls, v):
        """결제 금액 검증"""
        if v <= 0:
            raise ValueError('결제 금액은 0보다 커야 합니다')
        return v
    
    class Config:
        """Pydantic 설정"""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PaymentResponse(BaseModel):
    """결제 응답 스키마"""
    id: int = Field(..., description="결제 ID")
    user_id: int = Field(..., description="사용자 ID")
    order_id: str = Field(..., description="주문 ID")
    amount: int = Field(..., description="결제 금액 (원 단위)")
    token_amount: int = Field(..., description="지급된 토큰 수량")
    status: PaymentStatus = Field(..., description="결제 상태")
    pg_provider: Optional[str] = Field(None, description="PG사 정보")
    created_at: str = Field(..., description="생성 일시")
    updated_at: str = Field(..., description="수정 일시")
    
    class Config:
        """Pydantic 설정"""
        use_enum_values = True
        orm_mode = True


class PaymentCreateManual(BaseModel):
    """수동 결제 생성 요청 스키마 (요금제 기반)"""
    user_id: int = Field(..., gt=0, description="사용자 ID")
    product_id: int = Field(..., gt=0, description="상품 ID")
    quantity: int = Field(1, gt=0, description="수량 (Standard일 경우만 사용, 기본값: 1)")
    status: PaymentStatus = Field(PaymentStatus.COMPLETED, description="결제 상태 (기본값: completed)")
    
    @validator('quantity')
    def validate_quantity(cls, v):
        """수량 검증"""
        if v <= 0:
            raise ValueError('수량은 1 이상이어야 합니다')
        return v
    
    class Config:
        """Pydantic 설정"""
        use_enum_values = True


class PaymentListResponse(BaseModel):
    """결제 목록 응답 스키마"""
    payments: list[PaymentResponse] = Field(..., description="결제 목록")
    total: int = Field(..., ge=0, description="전체 결제 수")
    page: int = Field(..., ge=1, description="현재 페이지")
    per_page: int = Field(..., ge=1, le=100, description="페이지당 항목 수")
    
    class Config:
        """Pydantic 설정"""
        use_enum_values = True

