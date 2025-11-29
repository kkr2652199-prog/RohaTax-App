"""
상품(패키지) 관리 서비스 레이어
Jet Engine 기반 Service Layer 패턴 적용
비즈니스 로직과 데이터베이스 접근 분리
"""

from __future__ import annotations

import sqlite3
import logging
from typing import Optional, Dict, Any, List

from core.db import get_conn_optimized as get_conn
from .schemas import ProductCreate, ProductUpdate, ProductResponse

logger = logging.getLogger(__name__)

PRODUCT_COLUMNS = """
    id,
    name,
    description,
    price,
    token_amount,
    type,
    vat_included,
    duration_days,
    token_validity_days,
    one_time_limit,
    is_active,
    created_at,
    updated_at
"""


class ProductService:
    """상품 관리 서비스 클래스"""

    def __init__(self) -> None:
        self.logger = logger

    # ------------------------------------------------------------------ #
    # 내부 유틸
    # ------------------------------------------------------------------ #
    @staticmethod
    def _row_to_response(row: sqlite3.Row) -> ProductResponse:
        """
        sqlite3.Row → ProductResponse 변환 헬퍼
        (Row 객체는 dict.get을 지원하지 않으므로 keys() 체크 후 인덱싱)
        """
        row_keys = set(row.keys())
        
        token_validity = None
        if 'token_validity_days' in row_keys:
            token_validity = row['token_validity_days']
        
        one_time_limit = None
        if 'one_time_limit' in row_keys:
            one_time_limit = row['one_time_limit']
        
        return ProductResponse(
            id=row['id'],
            name=row['name'],
            description=row['description'],
            price=row['price'],
            token_amount=row['token_amount'],
            type=row['type'],
            vat_included=bool(row['vat_included']),
            duration_days=row['duration_days'],
            token_validity_days=token_validity,
            one_time_limit=one_time_limit,
            is_active=bool(row['is_active']),
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    # ------------------------------------------------------------------ #
    # CRUD
    # ------------------------------------------------------------------ #
    def create_product(self, product_data: ProductCreate) -> ProductResponse:
        """신규 상품 생성"""
        try:
            with get_conn() as conn:
                conn.row_factory = sqlite3.Row

                cursor = conn.execute(
                    """
                    INSERT INTO products (
                        name,
                        description,
                        price,
                        token_amount,
                        type,
                        vat_included,
                        duration_days,
                        token_validity_days,
                        one_time_limit,
                        is_active,
                        created_at,
                        updated_at
                    ) VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                        datetime('now', 'localtime'),
                        datetime('now', 'localtime')
                    )
                    """,
                    (
                        product_data.name,
                        product_data.description,
                        product_data.price,
                        product_data.token_amount,
                        product_data.type,
                        1 if product_data.vat_included else 0,
                        product_data.duration_days,
                        product_data.token_validity_days,
                        product_data.one_time_limit or 0,
                        1 if product_data.is_active else 0,
                    )
                )

                conn.commit()
                product_id = cursor.lastrowid
                return self.get_product_by_id(product_id)

        except sqlite3.IntegrityError as exc:
            self.logger.error("상품 생성 중 제약 조건 위반: %s", exc)
            raise ValueError("상품 생성 실패: 데이터베이스 제약 조건 위반")
        except Exception as exc:
            self.logger.error("상품 생성 중 오류: %s", exc)
            raise

    def get_product_by_id(self, product_id: int) -> ProductResponse:
        """상품 단건 조회"""
        with get_conn() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                f"""
                SELECT {PRODUCT_COLUMNS}
                FROM products
                WHERE id = ?
                """,
                (product_id,)
            ).fetchone()

            if not row:
                raise ValueError(f"상품을 찾을 수 없습니다: ID {product_id}")

            return self._row_to_response(row)

    def get_all_products(
        self,
        page: int = 1,
        per_page: int = 20,
        is_active: Optional[bool] = None
    ) -> Dict[str, Any]:
        """상품 목록 조회 (페이징 지원)"""
        with get_conn() as conn:
            conn.row_factory = sqlite3.Row

            where_conditions: List[str] = []
            params: List[Any] = []

            if is_active is not None:
                where_conditions.append("is_active = ?")
                params.append(1 if is_active else 0)

            where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""

            total_row = conn.execute(
                f"SELECT COUNT(*) as total FROM products {where_clause}",
                tuple(params)
            ).fetchone()
            total = total_row['total'] if total_row else 0

            offset = (page - 1) * per_page

            rows = conn.execute(
                f"""
                SELECT {PRODUCT_COLUMNS}
                FROM products
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                tuple(params + [per_page, offset])
            ).fetchall()

            products = []
            for row in rows:
                try:
                    product_obj = self._row_to_response(row)
                    if hasattr(product_obj, 'model_dump'):
                        products.append(product_obj.model_dump())
                    else:
                        products.append(product_obj.dict())
                except Exception as exc:
                    self.logger.error("상품 응답 객체 변환 중 오류: %s - Row: %s", exc, dict(row))
                    products.append(dict(row))

            return {
                'products': products,
                'total': total,
                'page': page,
                'per_page': per_page
            }

    def update_product(self, product_id: int, product_data: ProductUpdate) -> ProductResponse:
        """상품 정보 수정"""
        try:
            with get_conn() as conn:
                conn.row_factory = sqlite3.Row

                existing = conn.execute(
                    "SELECT id FROM products WHERE id = ?",
                    (product_id,)
                ).fetchone()

                if not existing:
                    raise ValueError(f"상품을 찾을 수 없습니다: ID {product_id}")

                update_fields: List[str] = []
                params: List[Any] = []

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

                if product_data.type is not None:
                    update_fields.append("type = ?")
                    params.append(product_data.type)

                if product_data.vat_included is not None:
                    update_fields.append("vat_included = ?")
                    params.append(1 if product_data.vat_included else 0)

                if product_data.duration_days is not None:
                    update_fields.append("duration_days = ?")
                    params.append(product_data.duration_days)

                if product_data.token_validity_days is not None:
                    update_fields.append("token_validity_days = ?")
                    params.append(product_data.token_validity_days)

                if product_data.one_time_limit is not None:
                    update_fields.append("one_time_limit = ?")
                    params.append(product_data.one_time_limit)

                if product_data.is_active is not None:
                    update_fields.append("is_active = ?")
                    params.append(1 if product_data.is_active else 0)

                if not update_fields:
                    return self.get_product_by_id(product_id)

                update_fields.append("updated_at = datetime('now', 'localtime')")
                params.append(product_id)

                conn.execute(
                    f"""
                    UPDATE products
                    SET {', '.join(update_fields)}
                    WHERE id = ?
                    """,
                    tuple(params)
                )

                conn.commit()
                return self.get_product_by_id(product_id)

        except ValueError:
            raise
        except Exception as exc:
            self.logger.error("상품 수정 중 오류: %s", exc)
            raise ValueError(f"상품 수정 실패: {str(exc)}")

    def delete_product(self, product_id: int) -> bool:
        """상품 삭제 (소프트 삭제)"""
        try:
            with get_conn() as conn:
                existing = conn.execute(
                    "SELECT id FROM products WHERE id = ?",
                    (product_id,)
                ).fetchone()

                if not existing:
                    raise ValueError(f"상품을 찾을 수 없습니다: ID {product_id}")

                conn.execute(
                    """
                    UPDATE products
                    SET is_active = 0,
                        updated_at = datetime('now', 'localtime')
                    WHERE id = ?
                    """,
                    (product_id,)
                )

                conn.commit()
                return True

        except ValueError:
            raise
        except Exception as exc:
            self.logger.error("상품 삭제 중 오류: %s", exc)
            raise ValueError(f"상품 삭제 실패: {str(exc)}")
