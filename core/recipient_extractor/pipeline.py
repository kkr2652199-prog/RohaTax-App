"""Recipient extraction pipeline orchestration.

이 모듈은 `RecipientExtractor`가 담당하던 거대한 진입점을 분리해
파이프라인 전용 클래스로 위임합니다. 향후 단계별 모듈화를 위한
기초 작업으로, 기존 로직은 그대로 보존하면서 구조만 재편합니다.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .utils import (
    extract_address_simple,
    extract_amount,
    extract_business_number_simple,
    extract_email_simple,
    extract_representative_simple,
    extract_store_name_simple,
    extract_total_amount_simple,
    get_synonyms,
)


if TYPE_CHECKING:  # pragma: no cover - 순환 참조 방지용 타입 힌트
    from .main_extractor import RecipientExtractor


class RecipientExtractionPipeline:
    """`RecipientExtractor`가 수행하던 핵심 흐름을 담당하는 파이프라인."""

    def __init__(self, extractor: "RecipientExtractor") -> None:
        self.extractor = extractor
        # 로거는 빠른 접근을 위해 보관하지만, 나머지는 __getattr__ 위임
        self.logger = extractor.logger
        self._special_treatment_applied = False

    # ------------------------------------------------------------------
    # 공용 헬퍼
    # ------------------------------------------------------------------
    def __getattr__(self, item: str):
        """정의되지 않은 속성은 원본 extractor에게 위임."""

        return getattr(self.extractor, item)

    def reset_state(self) -> None:
        """실행 시마다 내부 상태 초기화."""

        self._special_treatment_applied = False

    # ------------------------------------------------------------------
    # 기존 진입점 로직 이관 (단순 추출)
    # ------------------------------------------------------------------
    def extract_recipients_simple(
        self,
        parsed_data: Dict[str, Any],
        industry: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """단순한 공급받는자 정보 추출 (지능앱 시트 검열 기술 적용)"""

        self.reset_state()

        if parsed_data["parsing_status"] != "success":
            self.logger.error("파싱 실패된 데이터로부터 추출 시도")
            return []

        # 업종별 지침 설정
        if industry:
            self.set_industry_guideline(industry)

        try:
            df = parsed_data["raw_data"]
            recipients: List[Dict[str, Any]] = []

            # 🎯 지능앱 시트 우선순위 선택 로직 적용 (1순위 시트가 이미 선택된 경우 중복 선택 방지)
            # file_parser에서 반환된 sheet_inspection_result에서 priority/fast_path 체크
            sheet_inspection_result = parsed_data.get("sheet_inspection_result", {})

            # 🚨 안전성 검증: sheet_inspection_result가 None인 경우 빈 딕셔너리로 처리
            if sheet_inspection_result is None:
                self.logger.warning(
                    "sheet_inspection_result가 None입니다. 빈 딕셔너리로 처리합니다."
                )
                sheet_inspection_result = {}

            # 🚨 안전성 검증: sheet_inspection_result가 딕셔너리가 아닌 경우 처리
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

            # 🔍 디버깅: 실제 데이터 구조 확인
            self.logger.info("🔍 parsed_data 키들: %s", list(parsed_data.keys()))
            self.logger.info("🔍 sheet_inspection_result: %s", sheet_inspection_result)
            self.logger.info(
                "🔍 priority 값: %s", sheet_inspection_result.get("priority")
            )
            self.logger.info("🔍 selected_sheet: %s", parsed_data.get("selected_sheet"))
            self.logger.info("🔍 1순위 시트 선택 여부: %s", is_priority_sheet_selected)

            # 🚨 추가 검증: selected_sheet가 있으면 1순위로 간주
            if (
                not is_priority_sheet_selected
                and parsed_data.get("selected_sheet")
            ):
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
                # 이미 선택된 1순위 시트 데이터 사용 (중복 검열 방지)
                df = parsed_data.get("raw_data")
                if df is None:
                    self.logger.error("❌ 1순위 시트 데이터가 없습니다. 변환을 중단합니다.")
                    raise ValueError("1순위 시트 데이터가 없어 변환을 중단합니다.")
                self.logger.info(
                    "✅ 1순위 시트 데이터 사용: '%s', fast_path=%s - 중복 검열 완전 방지",
                    parsed_data.get("selected_sheet", "Unknown"),
                    fast_path_enabled,
                )
            else:
                # 1순위 시트가 선택되지 않은 경우에만 시트 선택 로직 실행
                self.logger.info("🔍 1순위 시트 없음 - 시트 선택 로직 실행")
                sheet_priority_result = self._select_optimal_sheet_by_family_rule(
                    parsed_data
                )
                if sheet_priority_result:
                    self.logger.info(
                        "🎯 시트 우선순위 선택 완료: '%s' (아빠값: %s, 엄마값: %s)",
                        sheet_priority_result["sheet_name"],
                        sheet_priority_result["dad_value"],
                        sheet_priority_result["mom_value"],
                    )
                    # 선택된 시트의 데이터로 업데이트
                    df = sheet_priority_result["dataframe"]
                    parsed_data["raw_data"] = df
                    parsed_data["selected_sheet"] = sheet_priority_result[
                        "sheet_name"
                    ]

            # 지능앱 시트 검열 결과 활용
            sheet_inspection_result = parsed_data.get("sheet_inspection_result")
            selected_sheet = parsed_data.get("selected_sheet", "Unknown")

            if sheet_inspection_result:
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

            # 업종별 절대지침: 5가지 컬럼 찾기
            required_columns = ["가맹점명", "대표자명", "주소", "사업자번호", "이메일"]

            # FileParser에서 이미 헤더를 컬럼명으로 설정했으므로 컬럼명을 직접 사용
            column_names = [str(col).strip() for col in df.columns]
            normalized_column_names = [self.normalize_colname(col) for col in column_names]
            self.logger.info("컬럼명 확인: %s", column_names)

            # 5가지 컬럼이 있는지 확인
            found_columns = 0
            column_mapping: Dict[str, int] = {}

            for required in required_columns:
                for col_idx, col_name in enumerate(normalized_column_names):
                    # 개행문자 제거하여 정확한 비교
                    clean_col_name = str(col_name).replace("\n", " ").strip()

                    # 🚨 중요한 수정: 홈텍스 템플릿에서는 "공급받는자" 키워드 우선
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
                    if required in clean_col_name or any(
                        keyword in clean_col_name for keyword in get_synonyms(required)
                    ):
                        # 🔍 디버깅: 매칭 테스트 로그 추가
                        synonyms = get_synonyms(required)
                        matched_keywords = [k for k in synonyms if k in clean_col_name]
                        self.logger.debug(
                            "매칭 테스트: %s vs '%s' -> 동의어 매칭: %s",
                            required,
                            clean_col_name,
                            matched_keywords,
                        )
                        # 공급자 정보는 제외 (공급받는자가 우선)
                        if "공급자" in clean_col_name and required in clean_col_name:
                            continue  # 공급자 정보는 스킵, 공급받는자만 추출
                        found_columns += 1
                        column_mapping[required] = col_idx
                        self.logger.info(
                            "컬럼 매칭: %s → %s (컬럼 %d)",
                            required,
                            clean_col_name,
                            col_idx,
                        )
                        break

            if found_columns < 5:
                self.logger.error(
                    "5가지 필수 컬럼을 찾을 수 없습니다. 찾은 컬럼: %d개",
                    found_columns,
                )
                self.logger.error("찾은 컬럼 매핑: %s", column_mapping)
                return []

            # 서브지침 시스템 기반 강화 추출
            if self._check_and_apply_sub_guideline(industry, parsed_data):
                self.logger.info("🚀 서브지침 시스템 활성화 - 고급 추출 모드")
                extracted_data = self._extract_with_sub_guidelines(
                    df, column_mapping, column_names
                )
            else:
                # 기본 추출
                extracted_data = self._extract_with_basic_mode(
                    df, column_mapping, column_names
                )

            # 지능앱 동적 컬럼 매핑: 스코어링 기반 최적 컬럼 선택
            supply_amount_col, vat_amount_col = self.column_mapper.dynamic_column_mapping(
                df, column_names
            )
            if vat_amount_col is None:
                self.logger.info(
                    "FAMILY_RULE: MOM_NOT_FOUND -> considering AUX_RULE on mapping stage"
                )

            if supply_amount_col is None or vat_amount_col is None:
                self.logger.error("지능앱 동적 매핑: 공급가액 또는 부가세 컬럼을 찾을 수 없습니다")
                return []

            # 데이터 추출 (모든 행)
            skipped_vat_rows = 0
            for row_idx in range(len(df)):
                row = df.iloc[row_idx]

                # 5가지 필수 정보 추출
                business_number = extract_business_number_simple(row, column_names)
                store_name = extract_store_name_simple(row, column_names)
                representative = extract_representative_simple(row, column_names)
                address = extract_address_simple(row, column_names)
                email = extract_email_simple(row, column_names)

                # 6번, 7번 컬럼에서 금액 추출
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

                # 총금액(합계) 추출: 첨파 파일의 총금액이 있으면 그대로 사용, 없으면 공급가액+부가세
                total_amount = extract_total_amount_simple(
                    row=row,
                    column_names=column_names,
                    default_total=supply_amount + vat_amount,
                )

                # 부가세 검증
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

                # 최소 정보가 있는지 확인
                if business_number or store_name or representative:
                    recipient_info = {
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
                    recipients.append(recipient_info)

            # 중복 제거를 선행하면 합산 대상 행이 소실될 수 있으므로,
            # 먼저 통합(합산)부터 수행하고 필요 시 이후 단계에서 정리한다.
            unique_recipients = recipients

            # 🎯 사업자번호 기반 가족 통합 서브지침 적용 (항상 실행)
            if unique_recipients:
                # 2순위 시트 감지: 분산된 가족이 있는지 확인
                is_second_priority_sheet = self._detect_second_priority_sheet(
                    unique_recipients
                )

                # 사업자등록번호 누락 체크: 누락된 경우가 있으면 특별대우 적용
                missing_business_numbers = [
                    r
                    for r in unique_recipients
                    if not r.get("사업자등록번호")
                    or r.get("사업자등록번호").strip() == ""
                ]
                has_missing_business_numbers = len(missing_business_numbers) > 0

                # 2순위 시트 감지 또는 사업자등록번호 누락 시 특별대우 로직 적용 (한 번만 실행)
                if (
                    is_second_priority_sheet or has_missing_business_numbers
                ) and not self._special_treatment_applied:
                    if is_second_priority_sheet:
                        self.logger.info("🔄 2순위 시트 감지 - 특별대우 로직 적용 (1순위 + 2순위 통합)")
                    else:
                        self.logger.info(
                            "🔄 사업자등록번호 누락 감지 (%d건) - 특별대우 로직 적용",
                            len(missing_business_numbers),
                        )

                    try:
                        # 2순위 검열을 위한 컬럼 매핑 재수행
                        column_mapping = (
                            self.second_priority_handler.remap_headers_for_second_priority(
                                df, column_names
                            )
                        )

                        # 특별대우: 1순위 로직 + 2순위 로직 통합 사용
                        self.logger.info(
                            "🎯 특별대우: 1순위 지침 우선 적용하면서 2순위 검열 방식 통합"
                        )

                        # 2순위 검열로 공급받는자 정보 재추출
                        second_priority_recipients = (
                            self.second_priority_handler.extract_recipients_from_second_priority(
                                df, column_mapping, column_names
                            )
                        )

                        if second_priority_recipients and len(second_priority_recipients) > 0:
                            # 2순위 검열 성공: 2순위 결과 사용
                            unique_recipients = second_priority_recipients
                            self.logger.info(
                                "✅ 2순위 검열 성공: %d건 (특별대우 적용)",
                                len(unique_recipients),
                            )
                        else:
                            # 2순위 검열 실패: 1순위 결과를 2순위 방식으로 재처리
                            self.logger.warning(
                                "⚠️ 2순위 검열 실패 - 1순위 결과를 2순위 방식으로 재처리"
                            )

                            # 1순위 결과를 2순위 검열 방식으로 재처리
                            enhanced_recipients = self._enhance_first_priority_with_second_priority_logic(
                                unique_recipients,
                                df,
                                column_mapping,
                                column_names,
                            )
                            if enhanced_recipients:
                                unique_recipients = enhanced_recipients
                                self.logger.info(
                                    "✅ 1순위+2순위 통합 처리 완료: %d건",
                                    len(unique_recipients),
                                )
                            else:
                                self.logger.warning("⚠️ 통합 처리 실패 - 1순위 결과 유지")

                        # 특별대우 로직 실행 완료 플래그 설정 (무한 루프 방지)
                        self._special_treatment_applied = True
                    except Exception as exc:  # pragma: no cover - 방어적 로깅
                        self.logger.error("❌ 2순위 특별대우 로직 오류: %s", str(exc))
                        self.logger.warning("⚠️ 오류 발생 - 1순위 결과 유지")
                        # 오류 발생 시에도 플래그 설정하여 무한 루프 방지
                        self._special_treatment_applied = True

                # FileParser의 통합 함수 사용
                from ..file_parser import FileParser

                parser = FileParser()
                merged_recipients = parser._merge_families_by_business_number(
                    unique_recipients
                )

                if len(merged_recipients) < len(unique_recipients):
                    self.logger.info(
                        "🎯 사업자번호 기반 가족 통합 적용: %d → %d건",
                        len(unique_recipients),
                        len(merged_recipients),
                    )
                    unique_recipients = merged_recipients
                else:
                    # 통합은 불필요하지만 보정된 값은 반영해야 함
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

            guideline_name = self.get_current_guideline().get(
                "name", "알 수 없는 지침"
            )
            if skipped_vat_rows > 0:
                self.logger.info("부가세 누락/0/비숫자 스킵 행: %d건", skipped_vat_rows)
            self.logger.info(
                "지능앱 추출 완료: %d건 (지침: %s, 시트: %s)",
                len(unique_recipients),
                guideline_name,
                selected_sheet,
            )
            return unique_recipients

        except Exception as exc:  # pragma: no cover - 방어적 로깅
            self.logger.error("지능앱 추출 오류: %s", str(exc))
            return []

    # ------------------------------------------------------------------
    # 기존 진입점 로직 이관 (정식 추출)
    # ------------------------------------------------------------------
    def extract_recipients(
        self,
        parsed_data: Dict[str, Any],
        industry: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """파싱된 데이터에서 공급받는자 정보 추출 (업종별 지침 적용 + 지능앱 기술 통합)"""

        self.reset_state()

        if parsed_data["parsing_status"] != "success":
            self.logger.error("파싱 실패된 데이터로부터 추출 시도")
            return []

        # 📊 통계 수집 변수 초기화
        stats = {
            "email_auto_fixed_count": 0,
            "business_number_auto_fixed_count": 0,
            "vat_included_count": 0,
            "vat_zero_count": 0,
            "perfect_info_count": 0,
            "rows_processed": 0,
            "total_supply_amount": 0,
            "total_tax_amount": 0,
        }

        self.logger.debug("🔍 통계 수집 시작 - 초기값: %s", stats)

        # 🎯 핵심 수정: 파싱된 families 데이터가 있으면 직접 사용
        families = parsed_data.get("families", [])
        if families:
            self.logger.info("🎯 파싱된 families 데이터 직접 사용: %d개", len(families))

            # families 데이터를 공급받는자 형식으로 변환
            recipients: List[Dict[str, Any]] = []
            for family in families:
                # 전체 행 수 카운트 (VAT 0원이어도 전체 처리 행 수는 집계)
                stats["rows_processed"] += 1

                # VAT가 0원이면 recipient에 추가하지 않음 (전자세금계산서 발행 불가)
                if family.get("mom_amount", 0) <= 0:
                    stats["vat_zero_count"] += 1
                    continue

                stats["vat_included_count"] += 1
                stats["total_supply_amount"] += family.get("dad_amount", 0)
                stats["total_tax_amount"] += family.get("mom_amount", 0)

                # 이메일 자동 보정 감지
                if family.get("email_auto_fixed"):
                    stats["email_auto_fixed_count"] += 1

                # 사업자번호 자동 보정 감지
                if family.get("business_number_auto_fixed"):
                    stats["business_number_auto_fixed_count"] += 1

                recipient_info = {
                    "사업자등록번호": family.get("business_number", ""),
                    "상호": family.get("store_name", ""),
                    "대표명": family.get("representative", ""),
                    "사업장주소": family.get("address", ""),
                    "사업자이메일": family.get("email", ""),
                    "공급가액": family.get("dad_amount", 0),
                    "부가세": family.get("mom_amount", 0),
                    "요금합계": family.get("total_amount")
                    or family.get("dad_amount", 0) + family.get("mom_amount", 0),
                    "industry": family.get("industry", self.current_industry),
                    "selected_sheet": parsed_data.get("selected_sheet", "Unknown"),
                    "source": "families",
                }

                if (
                    recipient_info["사업자등록번호"]
                    and recipient_info["상호"]
                    and recipient_info["대표명"]
                    and recipient_info["사업장주소"]
                    and recipient_info["공급가액"] > 0
                    and recipient_info["부가세"] > 0
                ):
                    stats["perfect_info_count"] += 1

                recipients.append(recipient_info)

            self._log_stats(stats, parsed_data)
            return recipients

        # 업종별 지침 설정
        if industry:
            self.set_industry_guideline(industry)

        # 기본 추출 수행
        recipients = self.extract_recipients_simple(parsed_data, industry)

        # 추가 검증 및 보정
        validated_recipients = self.validator.validate_recipients(
            recipients, stats
        )

        # 인텔리전트 기능 적용 (예: 이메일 자동 보정)
        enriched_recipients = self.intelligent_features.enhance_recipients(
            validated_recipients, stats
        )

        # 통계 로그 출력
        self._log_stats(stats, parsed_data)
        return enriched_recipients


