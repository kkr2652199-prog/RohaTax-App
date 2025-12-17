"""변환 엔진 통계 수집 유틸리티."""

from __future__ import annotations

import time
from typing import Any, Dict, Optional


class StatsCollector:
    """변환 엔진 실행 중 통계를 수집하고 계산한다."""

    def __init__(self) -> None:
        self._start_time = time.time()
        self._stats: Dict[str, Any] = {
            "total_count": 0,
            "success_rate": 0,
            "rows_processed": 0,
            "files_generated": 0,
            "vat_included_count": 0,
            "vat_zero_count": 0,
            "total_supply_amount": 0,
            "total_tax_amount": 0,
            "email_auto_fixed_count": 0,
            "business_number_auto_fixed_count": 0,
            "perfect_info_count": 0,
            "processing_time": 0,
            "per_second": 0,
            "email_auto_fixed_sample_from": None,
            "email_auto_fixed_sample_to": None,
            "business_auto_fixed_sample_from": None,
            "business_auto_fixed_sample_to": None,
        }

    @property
    def stats(self) -> Dict[str, Any]:
        """현재 수집된 통계를 반환한다."""

        return self._stats

    def merge(self, stats: Optional[Dict[str, Any]]) -> None:
        """외부 통계 값을 병합한다."""

        if not stats:
            return

        for key, value in stats.items():
            if value is not None:
                self._stats[key] = value

    def mark_files_generated(self, count: int) -> None:
        self._stats["files_generated"] = count

    def finalize(self, total_count: Optional[int] = None) -> Dict[str, Any]:
        """최종 통계를 계산한다."""

        end_time = time.time()
        processing_time = round(end_time - self._start_time, 2)
        self._stats["processing_time"] = processing_time

        if total_count is not None:
            self._stats["total_count"] = total_count

        if processing_time > 0:
            self._stats["per_second"] = round(self._stats["total_count"] / processing_time, 1)
        else:
            self._stats["per_second"] = 0

        return self._stats
