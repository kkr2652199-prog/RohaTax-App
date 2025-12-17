"""변환 엔진 컨텍스트 관리 모듈."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import logging


logger = logging.getLogger(__name__)


class ContextValidationError(RuntimeError):
    """컨텍스트 준비 중 발생한 검증 오류."""


@dataclass
class ConversionContext:
    """정상화된 변환 실행 컨텍스트."""

    industry: str
    template_id: str
    supplier_info: Dict[str, Any]
    issue_date: Optional[str]
    file_name: Optional[str]
    user_info: Optional[Dict[str, Any]]


class ConversionContextManager:
    """변환 엔진 입력값을 검증하고 표준 컨텍스트를 생성한다."""

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        self.logger = logger or logging.getLogger(__name__)

    def prepare(
        self,
        *,
        uploaded_file_path: str,
        supplier_info: Optional[Dict[str, Any]],
        template_id: Optional[str],
        industry_type: Optional[str],
        issue_date: Optional[str],
        file_name: Optional[str],
        user_info: Optional[Dict[str, Any]],
        conversion_log: Optional[List[str]] = None,
    ) -> ConversionContext:
        """입력값을 검증하고 표준화된 컨텍스트를 반환한다."""

        log = conversion_log if conversion_log is not None else []

        if not uploaded_file_path or not os.path.exists(uploaded_file_path):
            raise ContextValidationError("업로드된 파일을 찾을 수 없습니다.")

        template = template_id or "hometax_bulk"
        industry = industry_type or "delivery"
        sanitized_supplier = dict(supplier_info or {})

        if user_info:
            log.append("기본 사용자 정보 검증")
            if not user_info.get("business_number") or not user_info.get("company_name"):
                raise ContextValidationError("필수 사용자 정보가 누락되었습니다")

            # 공급자 정보가 비어 있을 경우 사용자 정보를 기본값으로 채운다.
            sanitized_supplier.setdefault("supplier_business_number", user_info.get("business_number", ""))
            sanitized_supplier.setdefault("supplier_name", user_info.get("company_name", ""))
            sanitized_supplier.setdefault("supplier_representative", user_info.get("representative_name", ""))
            sanitized_supplier.setdefault("supplier_email", user_info.get("email", ""))
            log.append("기본 사용자 정보 검증 완료")

        resolved_file_name = file_name or os.path.basename(uploaded_file_path)

        log.append("컨텍스트 준비 완료")
        self.logger.info(
            "[CONTEXT] 업종=%s, 템플릿=%s, 파일명=%s", industry, template, resolved_file_name
        )

        return ConversionContext(
            industry=industry,
            template_id=template,
            supplier_info=sanitized_supplier,
            issue_date=issue_date,
            file_name=resolved_file_name,
            user_info=user_info,
        )
