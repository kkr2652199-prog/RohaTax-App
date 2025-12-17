"""수신자 파이프라인 모듈.

공급받는자 데이터 추출과 통계 계산을 전담하는 보조 클래스를 제공한다.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Callable


logger = logging.getLogger(__name__)


class RecipientPipelineError(RuntimeError):
    """수신자 파이프라인 실행 중 발생한 오류."""


@dataclass
class RecipientPipelineResult:
    """수신자 파이프라인 실행 결과."""

    recipients: List[Dict[str, Any]]
    extraction_summary: Dict[str, Any]
    detailed_stats: Dict[str, Any]
    log_entries: List[str]


class RecipientPipeline:
    """수신자 데이터 추출 및 통계 처리를 담당하는 파이프라인."""

    def __init__(
        self,
        guideline_manager: Any,
        extractor_factory: Callable[[], Any],
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.guideline_manager = guideline_manager
        self.extractor_factory = extractor_factory
        self.logger = logger or logging.getLogger(__name__)

    def run(
        self,
        parsed_data: Dict[str, Any],
        industry_type: Optional[str] = None,
    ) -> RecipientPipelineResult:
        """공급받는자 데이터를 정제하고 통계를 계산한다."""

        industry = industry_type or "delivery"
        log_entries: List[str] = ["2단계: 업종별 절대지침 적용 시작"]
        self.logger.info("[RECIPIENT] 업종별 절대지침 적용 시작 (industry=%s)", industry)

        selected_guideline = self.guideline_manager.select_guideline(industry)
        if not self.guideline_manager.is_guideline_ready():
            self.logger.warning(
                "[RECIPIENT] 지침 미구현 상태로 진행: %s", selected_guideline.get("name") if isinstance(selected_guideline, dict) else "Unknown"
            )

        self._validate_guideline(selected_guideline)

        extractor = self.extractor_factory()
        extractor.set_industry_guideline(industry, selected_guideline)
        recipients = extractor.extract_recipients_simple(parsed_data, industry)

        if not recipients:
            raise RecipientPipelineError("공급받는자 정보를 추출할 수 없습니다.")

        detailed_stats = self._build_detailed_stats(recipients)
        log_entries.append(f"업종별 절대지침 적용 완료: {len(recipients)}건")

        extraction_summary = extractor.get_extraction_summary(recipients)

        return RecipientPipelineResult(
            recipients=recipients,
            extraction_summary=extraction_summary,
            detailed_stats=detailed_stats,
            log_entries=log_entries,
        )

    # ------------------------------------------------------------------
    # 내부 유틸리티
    # ------------------------------------------------------------------
    def _validate_guideline(self, guideline: Any) -> None:
        if guideline is None:
            raise RecipientPipelineError("업종별 지침을 찾을 수 없습니다.")
        if not isinstance(guideline, dict):
            raise RecipientPipelineError("업종별 지침 형식이 올바르지 않습니다.")

    def _build_detailed_stats(self, recipients: List[Dict[str, Any]]) -> Dict[str, Any]:
        stats_template = {
            "total_count": len(recipients),
            "success_rate": 100 if recipients else 0,
            "rows_processed": 0,
            "vat_included_count": 0,
            "vat_zero_count": 0,
            "total_supply_amount": 0,
            "total_tax_amount": 0,
            "email_auto_fixed_count": 0,
            "business_number_auto_fixed_count": 0,
            "perfect_info_count": 0,
            "email_auto_fixed_sample_from": None,
            "email_auto_fixed_sample_to": None,
            "business_auto_fixed_sample_from": None,
            "business_auto_fixed_sample_to": None,
        }

        if recipients and isinstance(recipients[0], dict):
            raw_stats = recipients[0].get("_stats", {}) or {}
            for key in stats_template.keys():
                if key in raw_stats and raw_stats[key] is not None:
                    stats_template[key] = raw_stats[key]

        return stats_template

    # 이전 _filter_valid_data 로직을 파이프라인 내로 이동
    def filter_valid_data(self, matched_data: List[Dict[str, Any]], guideline: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """업종별 지침에 따른 유효 데이터 필터링."""

        current_guideline = guideline or {}
        min_valid_fields = current_guideline.get("min_valid_fields", 3)
        confidence_threshold = current_guideline.get("confidence_threshold", 0.3)
        required_fields = ["사업자등록번호", "상호", "대표명", "사업장주소", "사업자이메일"]

        valid_data: List[Dict[str, Any]] = []
        for data in matched_data:
            valid_fields = sum(1 for field in required_fields if str(data.get(field, "")).strip())
            if valid_fields < min_valid_fields:
                continue

            confidence = data.get("confidence")
            if confidence is not None and confidence < confidence_threshold:
                continue

            valid_data.append(data)

        self.logger.info(
            "[RECIPIENT] 유효 데이터 필터링: %d건 → %d건 (최소필드=%d, 신뢰도=%.2f)",
            len(matched_data),
            len(valid_data),
            min_valid_fields,
            confidence_threshold,
        )
        return valid_data
