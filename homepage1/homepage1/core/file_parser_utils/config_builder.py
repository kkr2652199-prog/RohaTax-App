"""설정 및 빌더 전담 모듈."""

from __future__ import annotations

from typing import Dict, List, Tuple


def build_forbidden_keywords_map() -> Dict[str, List[str]]:
    """필요 이상의 금지어를 적용하지 않는다."""
    return {
        'business_number': [],
        'store_name': [],
        'representative': [],
        'address': [],
        'email': [],
    }


def get_scoring_config() -> Tuple[Dict[str, int], Dict[str, int], bool]:
    """점수 설정을 반환한다."""
    weights = {
        'business_number': 30,
        'representative': 10,
        'address': 30,
        'email': 20,
        'store_name': 10,
    }
    thresholds = {'pass': 80, 'candidate': 70}
    override_all5 = True
    return weights, thresholds, override_all5


