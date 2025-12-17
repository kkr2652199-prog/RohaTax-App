"""통계 수집 및 로깅 유틸리티 모듈."""

from __future__ import annotations

from typing import Any, Dict, Optional


class StatsTracker:
    """공급받는자 추출 파이프라인의 통계 수집을 담당하는 헬퍼."""

    _DEFAULT_TEMPLATE: Dict[str, Any] = {
        "email_auto_fixed_count": 0,
        "business_number_auto_fixed_count": 0,
        "vat_included_count": 0,
        "vat_zero_count": 0,
        "perfect_info_count": 0,
        "rows_processed": 0,
        "total_supply_amount": 0.0,
        "total_tax_amount": 0.0,
    }

    def __init__(self, logger) -> None:
        self.logger = logger
        self.stats: Dict[str, Any] = self._create_template()

    # ------------------------------------------------------------------
    # 기본 조작
    # ------------------------------------------------------------------
    def _create_template(self) -> Dict[str, Any]:
        return {key: (value if not isinstance(value, (int, float)) else type(value)(value))
                for key, value in self._DEFAULT_TEMPLATE.items()}

    def reset(self) -> None:
        self.stats = self._create_template()

    def as_dict(self) -> Dict[str, Any]:
        """외부 모듈과 공유하기 위한 원본 통계 딕셔너리."""

        return self.stats

    def increment(self, key: str, amount: int = 1) -> None:
        self.stats[key] = int(self.stats.get(key, 0) or 0) + amount

    def add_amount(self, key: str, amount: float) -> None:
        base = float(self.stats.get(key, 0) or 0)
        self.stats[key] = base + float(amount or 0)

    # ------------------------------------------------------------------
    # 도메인 전용 기록 로직
    # ------------------------------------------------------------------
    def record_family_row(
        self,
        supply_amount: Optional[float],
        vat_amount: Optional[float],
        *,
        email_auto_fixed: bool = False,
        business_number_auto_fixed: bool = False,
    ) -> bool:
        """families 데이터 한 행을 통계에 반영."""

        self.increment("rows_processed")

        vat_amount = float(vat_amount or 0)
        supply_amount = float(supply_amount or 0)

        if vat_amount <= 0:
            self.increment("vat_zero_count")
            return False

        self.increment("vat_included_count")
        self.add_amount("total_supply_amount", supply_amount)
        self.add_amount("total_tax_amount", vat_amount)

        if email_auto_fixed:
            self.increment("email_auto_fixed_count")

        if business_number_auto_fixed:
            self.increment("business_number_auto_fixed_count")

        return True

    def record_perfect_row(self) -> None:
        """필수 정보가 모두 채워진 행을 기록."""

        self.increment("perfect_info_count")

    # ------------------------------------------------------------------
    # 로깅
    # ------------------------------------------------------------------
    def log_summary(
        self,
        parsed_data: Dict[str, Any],
        recipient_count: int,
        guideline_name: str,
    ) -> None:
        """누적된 통계를 로그로 출력."""

        stats = self.stats

        rows_processed = stats.get("rows_processed", 0)
        vat_included = stats.get("vat_included_count", 0)
        vat_zero = stats.get("vat_zero_count", 0)
        email_fixed = stats.get("email_auto_fixed_count", 0)
        business_fixed = stats.get("business_number_auto_fixed_count", 0)

        self.logger.info(
            "📊 추출 통계: rows=%d, vat>0=%d, vat=0=%d, email_fix=%d, business_fix=%d",
            rows_processed,
            vat_included,
            vat_zero,
            email_fixed,
            business_fixed,
        )

        supply_total = stats.get("total_supply_amount")
        tax_total = stats.get("total_tax_amount")
        if supply_total or tax_total:
            self.logger.info(
                "💰 금액 합계: 공급가액=%.2f, 부가세=%.2f",
                supply_total or 0,
                tax_total or 0,
            )

        perfect_info = stats.get("perfect_info_count", 0)
        if perfect_info:
            self.logger.info("✨ 완벽한 정보 행: %d", perfect_info)

        selected_sheet = parsed_data.get("selected_sheet")
        if not selected_sheet:
            optimal = parsed_data.get("optimal_sheet") or {}
            selected_sheet = optimal.get("sheet_name", "Unknown")

        self.logger.info(
            "지능앱 추출 완료: %d건 (지침: %s, 시트: %s)",
            recipient_count,
            guideline_name,
            selected_sheet,
        )


