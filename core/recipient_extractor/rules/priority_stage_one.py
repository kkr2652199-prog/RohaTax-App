"""Priority stage one rule implementations."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..exceptions import StageExecutionError
from ..utils import (
    extract_address_simple,
    extract_amount,
    extract_business_number_simple,
    extract_email_simple,
    extract_representative_simple,
    extract_store_name_simple,
    extract_total_amount_simple,
    get_synonyms,
)
from .base_rules import BasePriorityRule, RuleContext


class PriorityStageOneRule(BasePriorityRule):
    """1차 우선순위 규칙 – 핵심 추출 로직."""

    rule_name = "priority_stage_one"

    def run(
        self,
        context: RuleContext,
        recipients: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        parsed_data = context.parsed_data
        extras = context.extras

        try:
            df = parsed_data["raw_data"]
        except KeyError:
            self.logger.error("❌ raw_data가 존재하지 않아 1순위 추출을 중단합니다.")
            return []

        recipients_list: List[Dict[str, Any]] = []
        sheet_inspection_result = parsed_data.get("sheet_inspection_result", {})

        if sheet_inspection_result is None:
            self.logger.warning(
                "sheet_inspection_result가 None입니다. 빈 딕셔너리로 처리합니다."
            )
            sheet_inspection_result = {}

        if not isinstance(sheet_inspection_result, dict):
            self.logger.warning(
                "sheet_inspection_result가 딕셔너리가 아닙니다: %s. 빈 딕셔너리로 처리합니다.",
                type(sheet_inspection_result),
            )
            sheet_inspection_result = {}

        fast_path_enabled = bool(sheet_inspection_result.get("fast_path"))
        is_priority_sheet_selected = (
            sheet_inspection_result.get("priority") == "1순위"
            or fast_path_enabled
        )

        self.logger.info("🔍 parsed_data 키들: %s", list(parsed_data.keys()))
        self.logger.info("🔍 sheet_inspection_result: %s", sheet_inspection_result)
        self.logger.info("🔍 priority 값: %s", sheet_inspection_result.get("priority"))
        self.logger.info("🔍 selected_sheet: %s", parsed_data.get("selected_sheet"))
        self.logger.info("🔍 1순위 시트 선택 여부: %s", is_priority_sheet_selected)

        if not is_priority_sheet_selected and parsed_data.get("selected_sheet"):
            self.logger.info(
                "🎯 selected_sheet 존재: '%s' - 1순위 시트로 간주",
                parsed_data.get("selected_sheet"),
            )
            is_priority_sheet_selected = True

        if is_priority_sheet_selected:
            self.logger.info(
                "🎯 1순위 시트 이미 선택됨: '%s' - 중복 선택 방지",
                parsed_data.get("selected_sheet", "Unknown"),
            )
            df = parsed_data.get("raw_data")
            if df is None:
                self.logger.error("❌ 1순위 시트 데이터가 없습니다. 변환을 중단합니다.")
                raise StageExecutionError("1순위 시트 데이터가 없어 변환을 중단합니다.")
            self.logger.info(
                "✅ 1순위 시트 데이터 사용: '%s', fast_path=%s - 중복 검열 완전 방지",
                parsed_data.get("selected_sheet", "Unknown"),
                fast_path_enabled,
            )
        else:
            self.logger.info("🔍 1순위 시트 없음 - 시트 선택 로직 실행")
            sheet_priority_result = self.pipeline._select_optimal_sheet_by_family_rule(
                parsed_data
            )
            if sheet_priority_result:
                self.logger.info(
                    "🎯 시트 우선순위 선택 완료: '%s' (아빠값: %s, 엄마값: %s)",
                    sheet_priority_result["sheet_name"],
                    sheet_priority_result["dad_value"],
                    sheet_priority_result["mom_value"],
                )
                df = sheet_priority_result["dataframe"]
                parsed_data["raw_data"] = df
                parsed_data["selected_sheet"] = sheet_priority_result["sheet_name"]

        # 최신 시트 검열 정보를 반영해 로그 출력
        sheet_inspection_result = parsed_data.get("sheet_inspection_result")
        selected_sheet = parsed_data.get("selected_sheet", "Unknown")

        if sheet_inspection_result and isinstance(sheet_inspection_result, dict):
            score = sheet_inspection_result.get("score", 0.0)
            matched_fields = sheet_inspection_result.get("matched_fields", 0)
            data_quality = sheet_inspection_result.get("data_quality", 0.0)
            self.logger.info(
                "지능앱 시트 검열 결과 활용: '%s' 시트 (점수: %.2f)",
                selected_sheet,
                score,
            )
            self.logger.info(
                "매칭된 필드: %d개, 데이터 품질: %.2f",
                matched_fields,
                data_quality,
            )

        required_columns = ["가맹점명", "대표자명", "주소", "사업자번호", "이메일"]

        column_names = [str(col).strip() for col in df.columns]
        normalized_column_names = [self.normalize_colname(col) for col in column_names]
        self.logger.info("컬럼명 확인: %s", column_names)

        found_columns = 0
        column_mapping: Dict[str, int] = {}

        for required in required_columns:
            for col_idx, col_name in enumerate(normalized_column_names):
                clean_col_name = str(col_name).replace("\n", " ").strip()

                if "공급받는자" in clean_col_name and required in clean_col_name:
                    found_columns += 1
                    column_mapping[required] = col_idx
                    self.logger.info(
                        "✅ 홈텍스 템플릿 매칭: %s → %s (컬럼 %d)",
                        required,
                        clean_col_name,
                        col_idx,
                    )
                    break

                synonyms = get_synonyms(required)
                if required in clean_col_name or any(
                    keyword in clean_col_name for keyword in synonyms
                ):
                    matched_keywords = [k for k in synonyms if k in clean_col_name]
                    self.logger.debug(
                        "매칭 테스트: %s vs '%s' -> 동의어 매칭: %s",
                        required,
                        clean_col_name,
                        matched_keywords,
                    )
                    if "공급자" in clean_col_name and required in clean_col_name:
                        continue
                    found_columns += 1
                    column_mapping[required] = col_idx
                    self.logger.info(
                        "컬럼 매칭: %s → %s (컬럼 %d)",
                        required,
                        clean_col_name,
                        col_idx,
                    )
                    break

        if found_columns < len(required_columns):
            self.logger.error(
                "5가지 필수 컬럼을 찾을 수 없습니다. 찾은 컬럼: %d개",
                found_columns,
            )
            self.logger.error("찾은 컬럼 매핑: %s", column_mapping)
            return []

        if self.pipeline._check_and_apply_sub_guideline(context.industry, parsed_data):
            self.logger.info("🚀 서브지침 시스템 활성화 - 고급 추출 모드")
            extracted_data = self.pipeline._extract_with_sub_guidelines(
                df, column_mapping, column_names
            )
        else:
            extracted_data = self.pipeline._extract_with_basic_mode(
                df, column_mapping, column_names
            )

        supply_amount_col, vat_amount_col = self.column_mapper.dynamic_column_mapping(
            df, column_names
        )
        if vat_amount_col is None:
            self.logger.info(
                "FAMILY_RULE: MOM_NOT_FOUND -> considering AUX_RULE on mapping stage"
            )

        if supply_amount_col is None or vat_amount_col is None:
            self.logger.error(
                "지능앱 동적 매핑: 공급가액 또는 부가세 컬럼을 찾을 수 없습니다"
            )
            return []

        skipped_vat_rows = 0

        for row_idx in range(len(df)):
            row = df.iloc[row_idx]

            business_number = extract_business_number_simple(row, column_names)
            store_name = extract_store_name_simple(row, column_names)
            representative = extract_representative_simple(row, column_names)
            address = extract_address_simple(row, column_names)
            email = extract_email_simple(row, column_names)

            supply_amount = extract_amount(row.iloc[supply_amount_col])
            vat_amount = extract_amount(row.iloc[vat_amount_col])

            try:
                supply_header = (
                    column_names[supply_amount_col]
                    if 0 <= supply_amount_col < len(column_names)
                    else f"idx{supply_amount_col}"
                )
                vat_header = (
                    column_names[vat_amount_col]
                    if 0 <= vat_amount_col < len(column_names)
                    else f"idx{vat_amount_col}"
                )
                self.logger.info(
                    "💾 금액 추출 원천(row %d): 공급가액[%s]=%s, 부가세[%s]=%s",
                    row_idx,
                    supply_header,
                    supply_amount,
                    vat_header,
                    vat_amount,
                )
            except Exception:  # pragma: no cover - 로깅 실패는 치명적이지 않음
                pass

            total_amount = extract_total_amount_simple(
                row=row,
                column_names=column_names,
                default_total=(supply_amount or 0) + (vat_amount or 0),
            )

            try:
                if vat_amount is None or vat_amount <= 0:
                    skipped_vat_rows += 1
                    self.logger.debug(
                        "FAMILY_RULE_SKIP: row=%d mom_missing_or_zero", row_idx
                    )
                    continue
            except Exception:
                skipped_vat_rows += 1
                continue

            if business_number or store_name or representative:
                recipients_list.append(
                    {
                        "사업자등록번호": business_number,
                        "상호": store_name,
                        "대표명": representative,
                        "사업장주소": address,
                        "사업자이메일": email,
                        "공급가액": supply_amount,
                        "부가세": vat_amount,
                        "요금합계": total_amount,
                        "source_row": row_idx,
                        "industry": self.current_industry,
                        "selected_sheet": selected_sheet,
                    }
                )

        extras["dataframe"] = df
        extras["column_names"] = column_names
        extras["column_mapping"] = column_mapping
        extras["skipped_vat_rows"] = skipped_vat_rows
        extras["selected_sheet"] = selected_sheet
        extras["extracted_data"] = extracted_data

        return recipients_list


