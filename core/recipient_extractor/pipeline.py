"""Recipient extraction pipeline orchestration.

이 모듈은 `RecipientExtractor`가 담당하던 거대한 진입점을 분리해
파이프라인 전용 클래스로 위임합니다. 향후 단계별 모듈화를 위한
기초 작업으로, 기존 로직은 그대로 보존하면서 구조만 재편합니다.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .rules import PriorityStageOneRule, PriorityStageTwoRule, RuleContext


if TYPE_CHECKING:  # pragma: no cover - 순환 참조 방지용 타입 힌트
    from .main_extractor import RecipientExtractor


class RecipientExtractionPipeline:
    """`RecipientExtractor`가 수행하던 핵심 흐름을 담당하는 파이프라인."""

    def __init__(self, extractor: "RecipientExtractor") -> None:
        self.extractor = extractor
        # 로거는 빠른 접근을 위해 보관하지만, 나머지는 __getattr__ 위임
        self.logger = extractor.logger
        self._special_treatment_applied = False
        self.stage_one_rule = PriorityStageOneRule(self)
        self.stage_two_rule = PriorityStageTwoRule(self)

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

        # Apply industry guideline when provided
        if industry:
            self.set_industry_guideline(industry)

        context = RuleContext(
            parsed_data=parsed_data,
            stats={},
            industry=industry,
        )

        try:
            self.stage_one_rule.prepare(context)
            recipients = self.stage_one_rule.run(context)
            recipients = self.stage_one_rule.finalize(context, recipients)

            self.stage_two_rule.prepare(context)
            recipients = self.stage_two_rule.run(context, recipients)
            recipients = self.stage_two_rule.finalize(context, recipients)

            skipped_vat_rows = context.extras.get("skipped_vat_rows", 0)
            if skipped_vat_rows > 0:
                self.logger.info("부가세 누락/0/비숫자 스킵 행: %d건", skipped_vat_rows)

            guideline_name = self.get_current_guideline().get(
                "name", "알 수 없는 지침"
            )
            selected_sheet = context.extras.get(
                "selected_sheet", parsed_data.get("selected_sheet", "Unknown")
            )

            self.logger.info(
                "지능앱 추출 완료: %d건 (지침: %s, 시트: %s)",
                len(recipients),
                guideline_name,
                selected_sheet,
            )
            return recipients

        except Exception as exc:  # pragma: no cover - 방어적 로경
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

            self._log_stats(stats, parsed_data, len(recipients))
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
        self._log_stats(stats, parsed_data, len(enriched_recipients))
        return enriched_recipients


    def _log_stats(
        self, stats: Dict[str, Any], parsed_data: Dict[str, Any], recipient_count: int
    ) -> None:
        """공통 통계 로깅 헬퍼.

        기존 `RecipientExtractor`가 수행하던 통계 출력 로직을 유지하면서,
        파이프라인이 결과 요약을 기록하도록 한다.
        """

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

        guideline_name = self.get_current_guideline().get("name", "알 수 없는 지침")
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


