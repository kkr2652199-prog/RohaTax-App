"""
상품(패키지) 관리 Pydantic 스키마
데이터 검증 및 직렬화를 위한 모델 정의
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from enum import Enum


class ProductStatus(str, Enum):
    """상품 활성화 상태"""
    ACTIVE = "active"
    INACTIVE = "inactive"


ALLOWED_PRODUCT_TYPES = {
    'basic',
    'package',
    'subscription',
    'event',
    'event_period'
}


class ProductCreate(BaseModel):
    """상품 생성 요청 스키마"""
    name: str = Field(..., min_length=1, max_length=100, description="상품명")
    description: Optional[str] = Field(None, max_length=500, description="상품 설명")
    price: int = Field(..., ge=0, description="가격 (원 단위)")
    token_amount: int = Field(..., ge=-1, description="지급 토큰 수 (무제한은 -1)")
    is_active: bool = Field(True, description="판매 중 여부")
    type: str = Field('basic', description="상품 유형")
    vat_included: bool = Field(False, description="부가세 포함 여부")
    duration_days: Optional[int] = Field(
        None,
        ge=0,
        description="기간제 상품 제공 일수 (없으면 None)"
    )
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('상품명은 필수 입력 항목입니다')
        return v.strip()
    
    @validator('price')
    def validate_price(cls, v):
        if v < 0:
            raise ValueError('가격은 0원 이상이어야 합니다')
        return v
    
    @validator('token_amount')
    def validate_token_amount(cls, v):
        if v < -1:
            raise ValueError('토큰 수량은 -1(무제한) 이상이어야 합니다')
        return v
    
    @validator('type')
    def validate_type(cls, v):
        value = (v or 'basic').strip().lower()
        if value not in ALLOWED_PRODUCT_TYPES:
            raise ValueError(f"허용되지 않은 상품 유형입니다: {value}")
        return value


class ProductUpdate(BaseModel):
    """상품 수정 요청 스키마"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="상품명")
    description: Optional[str] = Field(None, max_length=500, description="상품 설명")
    price: Optional[int] = Field(None, ge=0, description="가격 (원 단위)")
    token_amount: Optional[int] = Field(None, ge=-1, description="지급 토큰 수 (무제한은 -1)")
    is_active: Optional[bool] = Field(None, description="판매 중 여부")
    type: Optional[str] = Field(None, description="상품 유형")
    vat_included: Optional[bool] = Field(None, description="부가세 포함 여부")
    duration_days: Optional[int] = Field(
        None,
        ge=0,
        description="기간제 상품 제공 일수 (없으면 None)"
    )
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('상품명은 필수 입력 항목입니다')
        return v.strip() if v else v
    
    @validator('price')
    def validate_price(cls, v):
        if v is not None and v < 0:
            raise ValueError('가격은 0원 이상이어야 합니다')
        return v
    
    @validator('token_amount')
    def validate_token_amount(cls, v):
        if v is not None and v < -1:
            raise ValueError('토큰 수량은 -1(무제한) 이상이어야 합니다')
        return v
    
    @validator('type')
    def validate_type(cls, v):
        if v is None:
            return v
        value = v.strip().lower()
        if value not in ALLOWED_PRODUCT_TYPES:
            raise ValueError(f"허용되지 않은 상품 유형입니다: {value}")
        return value


class ProductResponse(BaseModel):
    """상품 응답 스키마"""
    id: int = Field(..., gt=0, description="상품 ID")
    name: str = Field(..., description="상품명")
    description: Optional[str] = Field(None, description="상품 설명")
    price: int = Field(..., description="가격 (원 단위)")
    token_amount: int = Field(..., description="지급 토큰 수 (무제한은 -1)")
    is_active: bool = Field(..., description="판매 중 여부")
    type: Optional[str] = Field(None, description="상품 유형")
    vat_included: bool = Field(False, description="부가세 포함 여부")
    duration_days: Optional[int] = Field(None, description="기간제 상품 제공 일수")
    created_at: str = Field(..., description="생성 일시")
    updated_at: str = Field(..., description="업데이트 일시")
    
    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """상품 목록 응답 스키마"""
    products: List[ProductResponse]
    total: int = Field(..., description="전체 상품 수")
    page: int = Field(..., description="현재 페이지")
    per_page: int = Field(..., description="페이지당 항목 수")
    
    class Config:
        from_attributes = True

