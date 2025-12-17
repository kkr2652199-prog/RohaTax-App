"""산업(업종)별 후처리 규칙 모듈.

가족(사업자) 데이터 통합과 금액 보정 등 업종 특화 로직을 담당한다.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Callable, Dict, List, Optional

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


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
        """중복 가족 데이터를 통합한다. (Pandas 기반 구현)"""
        
        # Pandas 사용 불가 시 legacy 함수로 fallback
        if not PANDAS_AVAILABLE:
            self.logger.warning("Pandas 미설치 - Legacy 함수 사용")
            return self._merge_family_data_legacy(families)
        
        try:
            if not families:
                return []
            
            self.logger.info("가족 통합 시작 (Pandas): %d개 정보", len(families))
            
            # 1. DataFrame 변환
            df = pd.DataFrame(families)
            
            # 2. 그룹핑 키 생성 (우선순위: 사업자번호 > 대표자명 > 금액)
            def create_group_key(row):
                biz = str(row.get('business_number', '')).strip() if pd.notna(row.get('business_number')) else ''
                if biz:
                    return biz
                
                rep = str(row.get('representative', '')).strip() if pd.notna(row.get('representative')) else ''
                if rep:
                    return f"rep_{rep}"
                
                dad = self._to_number(row.get('dad_amount', 0))
                return f"amount_{dad}"
            
            df['group_key'] = df.apply(create_group_key, axis=1)
            
            # 3. 그룹 크기 확인
            group_sizes = df.groupby('group_key').size()
            single_groups = group_sizes[group_sizes == 1].index
            multi_groups = group_sizes[group_sizes > 1].index
            
            # 4. 단일 그룹 처리 (원본 유지)
            single_df = df[df['group_key'].isin(single_groups)].copy()
            
            # 5. 다중 그룹 통합
            def max_by_length(series):
                """가장 긴 문자열 선택"""
                non_null = series.dropna().astype(str)
                if len(non_null) == 0:
                    return ''
                # 빈 문자열 제외
                non_empty = non_null[non_null.str.len() > 0]
                if len(non_empty) == 0:
                    return ''
                return non_empty.loc[non_empty.str.len().idxmax()]
            
            # 금액 필드: 합산 (숫자 변환 후)
            def sum_amounts(series):
                """금액 합산 (숫자 변환 포함)"""
                total = 0.0
                for val in series:
                    total += self._to_number(val)
                return total
            
            # 다중 그룹만 처리
            if len(multi_groups) > 0:
                multi_df = df[df['group_key'].isin(multi_groups)]
                
                # Aggregation 딕셔너리 구성
                agg_dict = {
                    'dad_amount': sum_amounts,
                    'mom_amount': sum_amounts,
                }
                
                # 문자열 필드: 가장 긴 것 선택
                string_fields = ['business_number', 'representative', 'address', 'email', 'store_name']
                for field in string_fields:
                    if field in multi_df.columns:
                        agg_dict[field] = max_by_length
                
                # 그룹핑 및 통합
                merged_multi = multi_df.groupby('group_key').agg(agg_dict).reset_index()
                
                # integration_count 추가
                merged_multi['integration_count'] = group_sizes[multi_groups].values
                
                # 결과 병합
                if len(single_groups) > 0:
                    result_df = pd.concat([single_df, merged_multi], ignore_index=True)
                else:
                    result_df = merged_multi
            else:
                # 다중 그룹이 없으면 단일 그룹만 반환
                result_df = single_df
            
            # 6. Dict 리스트로 변환
            result = result_df.to_dict('records')
            
            # 7. integration_count가 없는 경우 추가 (단일 그룹)
            for record in result:
                if 'integration_count' not in record:
                    record['integration_count'] = 1
            
            self.logger.info("가족 통합 결과 (Pandas): %d개 → %d개", len(families), len(result))
            
            # 로깅 (단일/다중 그룹)
            for key in single_groups:
                self.logger.info("단일 가족 유지: %s", key)
            for key in multi_groups:
                self.logger.info("가족 통합 완료: %s (%d개 → 1개)", key, group_sizes[key])
            
            return result
            
        except Exception as e:
            self.logger.error(f"Pandas 통합 중 오류 발생 - Legacy 함수로 fallback: {str(e)}")
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


