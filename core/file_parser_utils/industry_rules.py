"""산업(업종)별 후처리 규칙 모듈.

가족(사업자) 데이터 통합과 금액 보정 등 업종 특화 로직을 담당한다.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Callable, Dict, List, Optional

try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    np = None


class IndustryRules:
    """업종별 후처리 규칙 적용기."""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        number_parser: Optional[Callable[[Any], float]] = None,
    ) -> None:
        self.logger = logger or logging.getLogger(__name__)
        self._to_number = number_parser or self._default_to_number

    # ------------------------------------------------------------------
    # 공개 API
    # ------------------------------------------------------------------
    def extract_family_from_row(
        self,
        sheet,
        row_num: int,
        column_mapping: Dict[str, int],
        actual_max_col: int,
    ) -> Optional[Dict[str, Any]]:
        """주어진 행에서 5형제 가족 정보를 추출한다."""

        try:
            family_data: Dict[str, Any] = {}

            # 아빠 금액
            if "dad_amount" in column_mapping:
                dad_cell = sheet.cell(row_num, column_mapping["dad_amount"])
                dad_value = self._to_number(dad_cell.value)
                if dad_value and dad_value > 0:
                    family_data["dad_amount"] = dad_value

            # 엄마 금액
            if "mom_amount" in column_mapping:
                mom_cell = sheet.cell(row_num, column_mapping["mom_amount"])
                mom_value = self._to_number(mom_cell.value)
                if mom_value and mom_value > 0:
                    family_data["mom_amount"] = mom_value

            # 5형제 정보
            if "business_number" in column_mapping:
                business_value = sheet.cell(row_num, column_mapping["business_number"]).value
                business_value = str(business_value).strip() if business_value is not None else ""
                if business_value and self._is_business_number(business_value):
                    family_data["business_number"] = business_value

            if "store_name" in column_mapping:
                store_value = sheet.cell(row_num, column_mapping["store_name"]).value
                store_value = str(store_value).strip() if store_value is not None else ""
                if store_value and len(store_value) > 1:
                    family_data["store_name"] = store_value

            if "representative" in column_mapping:
                rep_value = sheet.cell(row_num, column_mapping["representative"]).value
                rep_value = str(rep_value).strip() if rep_value is not None else ""
                if rep_value and self._is_representative_name(rep_value):
                    family_data["representative"] = rep_value

            if "address" in column_mapping:
                addr_value = sheet.cell(row_num, column_mapping["address"]).value
                addr_value = str(addr_value).strip() if addr_value is not None else ""
                if addr_value and self._is_address(addr_value):
                    family_data["address"] = addr_value

            if "email" in column_mapping:
                email_value = sheet.cell(row_num, column_mapping["email"]).value
                email_value = str(email_value).strip() if email_value is not None else ""
                if email_value and "@" in email_value and "." in email_value:
                    family_data["email"] = email_value

            if family_data and self._is_valid_family(family_data):
                return family_data

        except Exception as exc:  # pragma: no cover - 보호 로깅
            self.logger.debug("행 %s 가족 추출 중 오류: %s", row_num, exc)

        return None

    def merge_family_data(self, families: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        중복 가족 데이터를 통합한다. [Pandas Jet Engine Version]
        
        - 기존 로직 100% 준수 (키 우선순위: Biz > Rep > Amount)
        - 벡터화 연산(Vectorized Operation)으로 성능 극대화
        """
        if not families:
            return []

        # PANDAS_AVAILABLE 플래그 확인 (안전장치)
        if not PANDAS_AVAILABLE:
            self.logger.warning("Pandas 모듈을 찾을 수 없어 Legacy 방식으로 처리합니다.")
            return self._merge_family_data_legacy(families)

        try:
            # 1. 데이터프레임 생성
            df = pd.DataFrame(families)
            
            # 빈 문자열/공백 처리 (NaN으로 변환하여 벡터 연산 용이하게)
            str_cols = ['business_number', 'representative', 'address', 'email', 'store_name']
            for col in str_cols:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip().replace('', np.nan)

            # 숫자형 컬럼 처리
            num_cols = ['dad_amount', 'mom_amount']
            for col in num_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                else:
                    df[col] = 0

            # 2. 그룹핑 키 생성 (Vectorized: Biz > Rep > Amount)
            # combine_first를 사용하여 우선순위 적용
            key_biz = df['business_number']
            
            key_rep = 'rep_' + df['representative'].fillna('')
            key_rep = key_rep.where(df['representative'].notna(), np.nan)
            
            key_amt = 'amount_' + df['dad_amount'].astype(str)
            
            df['group_key'] = key_biz.combine_first(key_rep).combine_first(key_amt)

            # 3. 집계 로직 (문자열: Max Length, 숫자: Sum)
            def get_longest_str(series):
                valid = series.dropna()
                if valid.empty: 
                    return ""
                # 길이가 가장 긴 값의 인덱스를 찾아 반환
                return valid.loc[valid.str.len().idxmax()]

            agg_rules = {
                'dad_amount': 'sum',
                'mom_amount': 'sum',
                'business_number': get_longest_str,
                'representative': get_longest_str,
                'address': get_longest_str,
                'email': get_longest_str,
                'store_name': get_longest_str,
            }
            
            # 실제 존재하는 컬럼만 집계 규칙에 포함
            final_agg = {k: v for k, v in agg_rules.items() if k in df.columns}
            
            # 4. 그룹핑 실행
            grouped = df.groupby('group_key', as_index=False).agg(final_agg)
            
            # 5. 그룹 크기 계산 및 integration_count 추가
            group_sizes = df.groupby('group_key').size()
            grouped['integration_count'] = grouped['group_key'].map(group_sizes).fillna(1).astype(int)
            
            # group_key 컬럼 제거 (최종 결과에는 필요 없음)
            if 'group_key' in grouped.columns:
                grouped = grouped.drop(columns=['group_key'])
            
            self.logger.info(f"가족 통합 완료: {len(families)} -> {len(grouped)} (Pandas Engine)")
            return grouped.to_dict('records')

        except Exception as e:
            self.logger.error(f"Pandas 통합 중 오류 발생, Legacy 방식으로 전환: {str(e)}")
            import traceback
            self.logger.error(f"상세 오류: {traceback.format_exc()}")
            return self._merge_family_data_legacy(families)
    
    def _merge_family_data_legacy(self, families: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """중복 가족 데이터를 통합한다. (Legacy 구현 - 비상용)"""

        if not families:
            return []

        self.logger.info("가족 통합 시작 (Legacy): %d개 정보", len(families))

        family_groups: Dict[str, List[Dict[str, Any]]] = {}
        for family in families:
            business_number = str(family.get("business_number", "")).strip()
            family_key = business_number

            if not family_key:
                representative = str(family.get("representative", "")).strip()
                if representative:
                    family_key = f"rep_{representative}"

            if not family_key:
                family_key = f"amount_{family.get('dad_amount', 0)}"

            family_groups.setdefault(family_key, []).append(family)

        merged_families: List[Dict[str, Any]] = []
        for key, group in family_groups.items():
            if len(group) == 1:
                merged_families.append(group[0])
                self.logger.info("단일 가족 유지: %s", key)
            else:
                merged = self._integrate_family_group(group)
                merged_families.append(merged)
                self.logger.info("가족 통합 완료: %s (%d개 → 1개)", key, len(group))

        self.logger.info("가족 통합 결과 (Legacy): %d개 → %d개", len(families), len(merged_families))
        return merged_families

    def merge_families_by_business_number(
        self,
        families: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """사업자번호 기준으로 가족을 재통합한다."""

        grouped: Dict[str, Dict[str, Any]] = {}

        for family in families:
            biz = str(family.get("사업자등록번호") or family.get("business_number") or "").strip()
            if not biz:
                continue

            supply = self._to_number(family.get("공급가액", family.get("supply_amount", 0)))
            vat = self._to_number(family.get("부가세", family.get("vat_amount", 0)))

            if biz not in grouped:
                grouped[biz] = family.copy()
                grouped[biz]["공급가액"] = supply
                grouped[biz]["부가세"] = vat
                grouped[biz]["요금합계"] = supply + vat
                self.logger.info("[AGG-NEW] 사업자 %s 초기 등록", biz)
                continue

            existing = grouped[biz]
            old_supply = self._to_number(existing.get("공급가액", 0))
            old_vat = self._to_number(existing.get("부가세", 0))

            new_supply = old_supply + supply
            new_vat = old_vat + vat

            existing["공급가액"] = new_supply
            existing["부가세"] = new_vat
            existing["요금합계"] = new_supply + new_vat

            for field in ("store_name", "상호", "대표자명", "대표자", "사업장주소", "주소", "사업자이메일", "이메일"):
                candidate = family.get(field)
                if candidate and len(str(candidate)) > len(str(existing.get(field, ""))):
                    existing[field] = candidate

            self.logger.info("[AGG-SUM] %s 갱신: 공급가액 %.0f, 부가세 %.0f", biz, new_supply, new_vat)

        return list(grouped.values())

    def apply_dad_fallback_logic(self, families: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """부가세(엄마) 금액을 기준으로 공급가액(아빠)을 보정한다."""

        for family in families:
            supply_amount = self._to_number(family.get("공급가액", family.get("dad_amount", 0)))
            vat_amount = self._to_number(family.get("부가세", family.get("mom_amount", 0)))

            if vat_amount == 0:
                family["공급가액"] = 0
                family["요금합계"] = 0
                self.logger.info("[VAT-0] 부가세 0 → 공급가액 0 설정")
                continue

            if supply_amount == 0 and vat_amount > 0:
                calculated_supply = vat_amount * 10
                family["공급가액"] = calculated_supply
                family["요금합계"] = calculated_supply + vat_amount
                self.logger.info("[VAT->SUPPLY] %s", calculated_supply)
                continue

            expected_vat = supply_amount * 0.1
            if abs(vat_amount - expected_vat) > 1:
                corrected_supply = vat_amount * 10
                family["공급가액"] = corrected_supply
                family["요금합계"] = corrected_supply + vat_amount
                self.logger.info("[VAT-CORRECT] 엄마 %.0f → 아빠 %.0f", vat_amount, corrected_supply)

        return families

    # ------------------------------------------------------------------
    # 내부 헬퍼
    # ------------------------------------------------------------------
    @staticmethod
    def _default_to_number(value: Any) -> float:
        try:
            if value is None:
                return 0.0
            if isinstance(value, (int, float)):
                return float(value)
            s = str(value).strip().replace(",", "")
            return float(s) if s not in ("", "None", "nan") else 0.0
        except Exception:
            return 0.0

    def _integrate_family_group(self, family_group: List[Dict[str, Any]]) -> Dict[str, Any]:
        integrated = {
            "dad_amount": 0,
            "mom_amount": 0,
            "business_number": "",
            "representative": "",
            "address": "",
            "email": "",
            "store_name": "",
            "integration_count": len(family_group),
        }

        for family in family_group:
            dad_amount = self._to_number(family.get("dad_amount", 0))
            mom_amount = self._to_number(family.get("mom_amount", 0))

            integrated["dad_amount"] += dad_amount
            integrated["mom_amount"] += mom_amount

            for field in ("business_number", "representative", "address", "email", "store_name"):
                candidate = family.get(field)
                if candidate and len(str(candidate)) > len(str(integrated.get(field, ""))):
                    integrated[field] = candidate

        return integrated

    @staticmethod
    def _is_business_number(value: str) -> bool:
        pattern = r"^\d{3}-?\d{2}-?\d{5}$|^\d{10}$"
        return bool(re.match(pattern, value))

    @staticmethod
    def _is_representative_name(value: str) -> bool:
        pattern = r"^[가-힣]{2,4}$"
        return bool(re.match(pattern, value)) and not value.isdigit()

    @staticmethod
    def _is_address(value: str) -> bool:
        keywords = ["시", "구", "동", "로", "길", "번지", "아파트", "빌딩"]
        return any(keyword in value for keyword in keywords) and len(value) > 5

    @staticmethod
    def _is_valid_family(family_data: Dict[str, Any]) -> bool:
        return family_data.get("dad_amount", 0) > 0


