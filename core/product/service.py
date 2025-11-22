"""
상품(패키지) 관리 서비스 레이어
Jet Engine 기반 Service Layer 패턴 적용
비즈니스 로직과 데이터베이스 접근 분리
"""

from __future__ import annotations

import sqlite3
import logging
from typing import Optional, List, Dict, Any

from core.db import get_conn_optimized as get_conn
from .schemas import ProductCreate, ProductUpdate, ProductResponse, ProductListResponse

logger = logging.getLogger(__name__)


class ProductService:
    """상품 관리 서비스 클래스"""
    
    def __init__(self):
        """ProductService 초기화"""
        self.logger = logger
    
    def create_product(self, product_data: ProductCreate) -> ProductResponse:
        """
        상품 생성
        
        Args:
            product_data: 상품 생성 데이터
            
        Returns:
            ProductResponse: 생성된 상품 정보
            
        Raises:
            ValueError: 유효하지 않은 데이터
        """
        try:
            with get_conn() as conn:
                conn.row_factory = sqlite3.Row
                
                # 상품명 중복 확인 (선택사항 - 필요시 활성화)
                # existing = conn.execute(
                #     "SELECT id FROM product_packages WHERE name = ? AND is_active = 1",
                #     (product_data.name,)
                # ).fetchone()
                # 
                # if existing:
                #     raise ValueError(f"이미 존재하는 상품명입니다: {product_data.name}")
                
                # 상품 생성
                cursor = conn.execute(
                    """
                    INSERT INTO product_packages 
                    (name, description, price, token_amount, is_active, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime'), strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime'))
                    """,
                    (
                        product_data.name,
                        product_data.description,
                        product_data.price,
                        product_data.token_amount,
                        1 if product_data.is_active else 0,
                    )
                )
                
                conn.commit()
                product_id = cursor.lastrowid
                
                # 생성된 상품 정보 조회
                return self.get_product_by_id(product_id)
                
        except sqlite3.IntegrityError as e:
            self.logger.error(f"상품 생성 중 DB 제약 조건 위반: {str(e)}")
            raise ValueError("상품 생성 실패: 데이터베이스 제약 조건 위반")
        except Exception as e:
            self.logger.error(f"상품 생성 중 오류: {str(e)}")
            raise
    
    def get_product_by_id(self, product_id: int) -> ProductResponse:
        """
        상품 ID로 상품 정보 조회
        
        Args:
            product_id: 상품 ID
            
        Returns:
            ProductResponse: 상품 정보
            
        Raises:
            ValueError: 상품을 찾을 수 없음
        """
        with get_conn() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT id, name, description, price, token_amount, is_active, created_at, updated_at
                FROM product_packages
                WHERE id = ?
                """,
                (product_id,)
            ).fetchone()
            
            if not row:
                raise ValueError(f"상품을 찾을 수 없습니다: ID {product_id}")
            
            return ProductResponse(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                price=row['price'],
                token_amount=row['token_amount'],
                is_active=bool(row['is_active']),
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
    
    def get_all_products(
        self,
        page: int = 1,
        per_page: int = 20,
        is_active: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        상품 목록 조회 (페이징 지원)
        
        Args:
            page: 페이지 번호 (1부터 시작)
            per_page: 페이지당 항목 수
            is_active: 활성화 상태 필터 (None: 전체, True: 활성만, False: 비활성만)
            
        Returns:
            Dict: 상품 목록 및 페이징 정보
        """
        with get_conn() as conn:
            conn.row_factory = sqlite3.Row
            
            # WHERE 조건 구성
            where_conditions = []
            params = []
            
            if is_active is not None:
                where_conditions.append("is_active = ?")
                params.append(1 if is_active else 0)
            
            where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
            
            # 전체 개수 조회
            total_row = conn.execute(
                f"SELECT COUNT(*) as total FROM product_packages {where_clause}",
                tuple(params)
            ).fetchone()
            total = total_row['total'] if total_row else 0
            
            # 페이징 계산
            offset = (page - 1) * per_page
            
            # 상품 목록 조회
            rows = conn.execute(
                f"""
                SELECT id, name, description, price, token_amount, is_active, created_at, updated_at
                FROM product_packages
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                tuple(params + [per_page, offset])
            ).fetchall()
            
            products = []
            for row in rows:
                try:
                    product_obj = ProductResponse(
                        id=row['id'],
                        name=row['name'],
                        description=row['description'],
                        price=row['price'],
                        token_amount=row['token_amount'],
                        is_active=bool(row['is_active']),
                        created_at=row['created_at'],
                        updated_at=row['updated_at']
                    )
                    # Pydantic v1/v2 호환성: .dict() 또는 .model_dump() 사용
                    if hasattr(product_obj, 'model_dump'):
                        products.append(product_obj.model_dump())
                    else:
                        products.append(product_obj.dict())
                except Exception as e:
                    self.logger.error(f"상품 응답 객체 변환 중 오류 발생: {e} - Row: {row}")
                    products.append(dict(row))  # Fallback to raw dict
            
            return {
                'products': products,
                'total': total,
                'page': page,
                'per_page': per_page
            }
    
    def update_product(self, product_id: int, product_data: ProductUpdate) -> ProductResponse:
        """
        상품 정보 수정
        
        Args:
            product_id: 상품 ID
            product_data: 수정할 상품 데이터
            
        Returns:
            ProductResponse: 수정된 상품 정보
            
        Raises:
            ValueError: 상품을 찾을 수 없음 또는 유효하지 않은 데이터
        """
        try:
            with get_conn() as conn:
                conn.row_factory = sqlite3.Row
                
                # 상품 존재 확인
                existing = conn.execute(
                    "SELECT id FROM product_packages WHERE id = ?",
                    (product_id,)
                ).fetchone()
                
                if not existing:
                    raise ValueError(f"상품을 찾을 수 없습니다: ID {product_id}")
                
                # 업데이트할 필드 구성
                update_fields = []
                params = []
                
                if product_data.name is not None:
                    update_fields.append("name = ?")
                    params.append(product_data.name)
                
                if product_data.description is not None:
                    update_fields.append("description = ?")
                    params.append(product_data.description)
                
                if product_data.price is not None:
                    update_fields.append("price = ?")
                    params.append(product_data.price)
                
                if product_data.token_amount is not None:
                    update_fields.append("token_amount = ?")
                    params.append(product_data.token_amount)
                
                if product_data.is_active is not None:
                    update_fields.append("is_active = ?")
                    params.append(1 if product_data.is_active else 0)
                
                if not update_fields:
                    # 수정할 필드가 없으면 기존 정보 반환
                    return self.get_product_by_id(product_id)
                
                # updated_at 업데이트
                update_fields.append("updated_at = strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')")
                params.append(product_id)
                
                # 상품 정보 업데이트
                conn.execute(
                    f"""
                    UPDATE product_packages
                    SET {', '.join(update_fields)}
                    WHERE id = ?
                    """,
                    tuple(params)
                )
                
                conn.commit()
                
                # 수정된 상품 정보 조회
                return self.get_product_by_id(product_id)
                
        except ValueError:
            raise
        except Exception as e:
            self.logger.error(f"상품 수정 중 오류: {str(e)}")
            raise ValueError(f"상품 수정 실패: {str(e)}")
    
    def delete_product(self, product_id: int) -> bool:
        """
        상품 삭제 (소프트 삭제: is_active = 0)
        
        Args:
            product_id: 상품 ID
            
        Returns:
            bool: 삭제 성공 여부
            
        Raises:
            ValueError: 상품을 찾을 수 없음
        """
        try:
            with get_conn() as conn:
                # 상품 존재 확인
                existing = conn.execute(
                    "SELECT id FROM product_packages WHERE id = ?",
                    (product_id,)
                ).fetchone()
                
                if not existing:
                    raise ValueError(f"상품을 찾을 수 없습니다: ID {product_id}")
                
                # 소프트 삭제 (is_active = 0)
                conn.execute(
                    """
                    UPDATE product_packages
                    SET is_active = 0, updated_at = strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')
                    WHERE id = ?
                    """,
                    (product_id,)
                )
                
                conn.commit()
                return True
                
        except ValueError:
            raise
        except Exception as e:
            self.logger.error(f"상품 삭제 중 오류: {str(e)}")
            raise ValueError(f"상품 삭제 실패: {str(e)}")

