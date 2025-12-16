"""숫자 파싱 전담 모듈."""

from __future__ import annotations

from typing import Any


def default_number_parser(value: Any) -> float:
    """기본 숫자 파서."""
    try:
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        stripped = str(value).strip().replace(',', '')
        return float(stripped) if stripped not in ['', 'None', 'nan'] else 0.0
    except Exception:
        return 0.0


