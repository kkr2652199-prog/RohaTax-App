"""Priority stage two rule implementations."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .base_rules import BasePriorityRule, RuleContext


class PriorityStageTwoRule(BasePriorityRule):
    """2차 우선순위 규칙 – 특별대우 및 가족 통합 처리."""

    rule_name = "priority_stage_two"

    def run(
        self,
        context: RuleContext,
        recipients: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        if not recipients:
            return []

        parsed_data = context.parsed_data
        extras = context.extras

        df = extras.get("dataframe") or parsed_data.get("raw_data")
        if df is None:
            self.logger.warning("[Stage2] DataFrame이 없어 후속 처리를 생략합니다.")
            return recipients

        column_names = extras.get("column_names")
        if column_names is None:
            column_names = [str(col).strip() for col in df.columns]

        column_mapping = extras.get("column_mapping") or {}

        unique_recipients = list(recipients)

        is_second_priority_sheet = self._detect_second_priority_sheet(unique_recipients)
        missing_business_numbers = [
            r
            for r in unique_recipients
            if not r.get("사업자등록번호") or r.get("사업자등록번호").strip() == ""
        ]
        has_missing_business_numbers = len(missing_business_numbers) > 0

        if (
            is_second_priority_sheet or has_missing_business_numbers
        ) and not self.pipeline._special_treatment_applied:
            if is_second_priority_sheet:
                self.logger.info("🔄 2순위 시트 감지 - 특별대우 로직 적용 (1순위 + 2순위 통합)")
            else:
                self.logger.info(
                    "🔄 사업자등록번호 누락 감지 (%d건) - 특별대우 로직 적용",
                    len(missing_business_numbers),
                )

            try:
                column_mapping_second = (
                    self.second_priority_handler.remap_headers_for_second_priority(
                        df, column_names
                    )
                )
                extras["column_mapping_stage2"] = column_mapping_second
                extras["column_mapping"] = column_mapping_second

                second_priority_recipients = (
                    self.second_priority_handler.extract_recipients_from_second_priority(
                        df, column_mapping_second, column_names
                    )
                )

                if second_priority_recipients:
                    unique_recipients = second_priority_recipients
                    self.logger.info(
                        "✅ 2순위 검열 성공: %d건 (특별대우 적용)",
                        len(unique_recipients),
                    )
                else:
                    self.logger.warning(
                        "⚠️ 2순위 검열 실패 - 1순위 결과를 2순위 방식으로 재처리"
                    )
                    enhanced_recipients = (
                        self._enhance_first_priority_with_second_priority_logic(
                            unique_recipients,
                            df,
                            column_mapping_second,
                            column_names,
                        )
                    )
                    if enhanced_recipients:
                        unique_recipients = enhanced_recipients
                        self.logger.info(
                            "✅ 1순위+2순위 통합 처리 완료: %d건",
                            len(unique_recipients),
                        )
                    else:
                        self.logger.warning("⚠️ 통합 처리 실패 - 1순위 결과 유지")

                self.pipeline._special_treatment_applied = True
            except Exception as exc:  # pragma: no cover - 방어적 로깅
                self.logger.error("❌ 2순위 특별대우 로직 오류: %s", str(exc))
                self.logger.warning("⚠️ 오류 발생 - 1순위 결과 유지")
                self.pipeline._special_treatment_applied = True

        # 가족 통합 로직 (FileParser 재사용)
        try:
            from ...file_parser import FileParser

            parser = FileParser()
            merged_recipients = parser._merge_families_by_business_number(
                unique_recipients
            )
        except Exception as exc:  # pragma: no cover - 방어적 로깅
            self.logger.error("❌ 가족 통합 처리 중 오류: %s", str(exc))
            return unique_recipients

        if len(merged_recipients) < len(unique_recipients):
            self.logger.info(
                "🎯 사업자번호 기반 가족 통합 적용: %d → %d건",
                len(unique_recipients),
                len(merged_recipients),
            )
            unique_recipients = merged_recipients
        else:
            unique_recipients = merged_recipients
            if is_second_priority_sheet:
                self.logger.info(
                    "🎯 사업자번호 기반 가족 통합 적용: %d건 (2순위 시트, 분산된 가족 통합)",
                    len(unique_recipients),
                )
            else:
                self.logger.info(
                    "🎯 사업자번호 기반 가족 통합 적용: %d건 (통합 불필요, 보정 적용)",
                    len(unique_recipients),
                )

        return unique_recipients


