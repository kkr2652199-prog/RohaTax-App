"""헤더 및 시트 감지 로직 전담 모듈."""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional, Tuple

import openpyxl
from openpyxl.worksheet.worksheet import Worksheet
import pandas as pd

FamilyExtractor = Callable[[Worksheet, Dict[str, List[str]]], List[Dict[str, Any]]]
NumberParser = Callable[[Any], float]


class HeaderLocator:
    """엑셀/CSV 파일에서 최적의 시트와 헤더를 감지하는 전담 클래스."""

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        self.logger = logger or logging.getLogger(__name__)

    # ------------------------------------------------------------------
    # 공개 API
    # ------------------------------------------------------------------
    def inspect_all_sheets(
        self,
        workbook: openpyxl.Workbook,
        required_keywords: Dict[str, List[str]],
        family_extractor: Optional[FamilyExtractor] = None,
        number_parser: Optional[NumberParser] = None,
    ) -> Optional[Dict[str, Any]]:
        """모든 시트를 검열하여 최적의 시트를 선택한다."""

        weights, thresholds, override_all5 = self._get_scoring_config()
        forbidden_keywords_map = self._build_forbidden_keywords_map()

        best_result: Optional[Dict[str, Any]] = None
        sheet_results: List[Dict[str, Any]] = []

        priority_sheet = self._find_priority_sheet(
            workbook,
            required_keywords,
            forbidden_keywords_map,
            family_extractor,
            number_parser,
        )
        if priority_sheet:
            return priority_sheet

        self.logger.info(
            "1순위 시트 없음 - 기존 방식으로 시트 검열 진행"
        )

        sheet_names = sorted(workbook.sheetnames)
        self.logger.info(f"🔍 시트 검열 순서: {sheet_names}")

        for sheet_name in sheet_names:
            try:
                sheet = workbook[sheet_name]
                total_delivery_amount = self._find_max_delivery_amount(sheet)

                sheet_result = self._evaluate_sheet(
                    sheet,
                    sheet_name,
                    required_keywords,
                    forbidden_keywords_map,
                    family_extractor,
                    number_parser,
                )

                if not sheet_result:
                    continue

                headers_lower = [str(h).lower() for h in sheet_result["headers"]]

                def any_in(keys: List[str]) -> bool:
                    return any(
                        any(key in header for header in headers_lower) for key in keys
                    )

                has_bn = any_in(['사업자', '등록번호', '공급받는자사업자', '공급받는자 사업자'])

                representative_scores = [
                    self._score_representative_header(header)
                    for header in headers_lower
                ]

                strong_rep = any(score >= 60 for score in representative_scores)
                medium_rep = any(40 <= score < 60 for score in representative_scores)
                fallback_rep = any(20 <= score < 40 for score in representative_scores)
                registration_rep = any(
                    ('등록자' in header or '작성자' in header or '입력자' in header)
                    for header in headers_lower
                )

                if strong_rep:
                    representative_points = weights.get('representative', 10)
                elif medium_rep:
                    representative_points = max(int(weights.get('representative', 10) * 0.6), 4)
                elif fallback_rep:
                    representative_points = max(int(weights.get('representative', 10) * 0.4), 3)
                elif registration_rep:
                    representative_points = max(int(weights.get('representative', 10) * 0.2), 2)
                else:
                    representative_points = 0

                has_rep = representative_points > 0
                has_addr = any_in(['주소', '소재지', '사업장', '공급받는자주소', '공급받는자 주소'])
                has_email = any_in(['이메일', 'email', '메일', '공급받는자이메일', '공급받는자 이메일'])
                has_store = any_in(['가맹점', '상호', '상호명', '매장', '점포', '업체', '가게', '공급받는자상호', '공급받는자 상호', '매장명', '점포명'])

                found5 = sum([has_bn, has_rep, has_addr, has_email, has_store])

                sheet_score_pts = (
                    (weights.get('business_number', 30) if has_bn else 0)
                    + representative_points
                    + (weights.get('address', 30) if has_addr else 0)
                    + (weights.get('email', 20) if has_email else 0)
                    + (weights.get('store_name', 10) if has_store else 0)
                )

                sheet_result['core_fields_found'] = found5
                sheet_result['scoring_points'] = sheet_score_pts
                sheet_result['delivery_amount'] = total_delivery_amount

                if total_delivery_amount > 0:
                    delivery_bonus = min(total_delivery_amount / 1_000_000, 50)
                    sheet_result['delivery_bonus'] = delivery_bonus
                    sheet_result['score'] += delivery_bonus
                    self.logger.info(
                        "시트 '%s' 총배달 금액: %s원 (보너스: +%.1f점)",
                        sheet_name,
                        f"{total_delivery_amount:,.0f}",
                        delivery_bonus,
                    )

                sheet_results.append(sheet_result)

                if (
                    sheet_result.get('score', 0) > best_result.get('score', -1)
                    if best_result
                    else True
                ):
                    self.logger.info(
                        "최적 시트 후보 갱신: '%s' (점수 %.2f)",
                        sheet_name,
                        sheet_result.get('score', 0),
                    )
                    best_result = sheet_result

            except Exception as exc:
                self.logger.warning(
                    "시트 '%s' 검열 중 오류: %s",
                    sheet_name,
                    exc,
                )

        if sheet_results:
            delivery_sheets = [r for r in sheet_results if r.get('delivery_amount', 0) > 0]
            if delivery_sheets:
                delivery_sheets.sort(
                    key=lambda r: (r.get('delivery_amount', 0), r.get('sheet_name', '')),
                    reverse=True,
                )
                best_result = delivery_sheets[0]
                self.logger.info(
                    "🎯 총배달 금액 우선 선점: '%s' (총배달 금액: %s원)",
                    best_result['sheet_name'],
                    f"{best_result.get('delivery_amount', 0):,.0f}",
                )
            else:
                best_result = self._select_by_score(
                    sheet_results,
                    thresholds,
                    override_all5,
                )

        if best_result:
            self.logger.info(
                "최적 시트 선택: '%s' (원점수: %.2f, 가중치점: %.2f)",
                best_result['sheet_name'],
                best_result.get('score', 0),
                best_result.get('scoring_points', 0),
            )
        else:
            self.logger.warning("적합한 시트를 찾지 못했습니다.")

        return best_result

    def detect_header_row(self, sheet: Worksheet) -> int:
        """엑셀 시트에서 헤더 행을 감지한다."""

        max_row = sheet.max_row
        max_col = sheet.max_column

        title_rows = self._detect_title_rows(sheet, max_col)
        self.logger.info(f"🔍 제목/부제목 행 감지: {title_rows}")

        header_candidates: List[Tuple[int, float]] = []

        for row in range(1, min(1001, max_row + 1)):
            if row in title_rows:
                continue

            data_density = self._calculate_data_density(sheet, row, max_col)
            header_candidates.append((row, data_density))

        if not header_candidates:
            self.logger.warning("헤더 후보가 없습니다. 기본 헤더 행 사용")
            return 1

        header_candidates.sort(key=lambda x: (x[1], x[0]), reverse=True)
        best_header_row = header_candidates[0][0]

        self.logger.info(f"헤더 후보 분석: {header_candidates[:5]}...")
        self.logger.info(f"선택된 헤더 행: {best_header_row}")

        return best_header_row

    def detect_csv_header_row(
        self,
        df: pd.DataFrame,
        required_keywords: Dict[str, List[str]],
    ) -> int:
        """CSV 파일에서 헤더 행을 감지한다."""

        if len(df) == 0:
            return 0

        header_candidates: List[Dict[str, Any]] = []
        scan_rows = min(10, len(df))

        for row_idx in range(scan_rows):
            data_density = self._calculate_csv_data_density(df, row_idx)
            matched_fields = self._count_csv_matched_fields(
                df,
                row_idx,
                required_keywords,
            )

            field_match_score = (matched_fields / 5) * 0.8
            density_score = data_density * 0.2
            header_score = field_match_score + density_score

            if matched_fields >= 3:
                header_candidates.append(
                    {
                        'row': row_idx,
                        'data_density': data_density,
                        'matched_fields': matched_fields,
                        'header_score': header_score,
                    }
                )
                self.logger.debug(
                    "지능앱 CSV 헤더 후보: 행 %d, 점수 %.3f, 매칭 %d개",
                    row_idx,
                    header_score,
                    matched_fields,
                )

        if not header_candidates:
            density_scores = [
                (row, self._calculate_csv_data_density(df, row)) for row in range(scan_rows)
            ]
            density_scores.sort(key=lambda x: (x[1], -x[0]), reverse=True)
            best_header_row = density_scores[0][0]
            self.logger.warning(
                "지능앱 CSV 헤더 감지: 매칭된 헤더가 없어 데이터 밀도로 선택 - 행 %d",
                best_header_row,
            )
            return best_header_row

        header_candidates.sort(
            key=lambda x: (x['matched_fields'], x['header_score'], x['row']),
            reverse=True,
        )
        best_header = header_candidates[0]
        best_header_row = best_header['row']
        self.logger.info(
            "지능앱 CSV 헤더 감지: 최적 헤더 선택 - 행 %d (점수: %.3f, 매칭: %d개)",
            best_header_row,
            best_header['header_score'],
            best_header['matched_fields'],
        )

        return best_header_row

    # ------------------------------------------------------------------
    # 내부 유틸리티 (엑셀)
    # ------------------------------------------------------------------
    def _find_priority_sheet(
        self,
        workbook: openpyxl.Workbook,
        required_keywords: Dict[str, List[str]],
        forbidden_keywords_map: Dict[str, List[str]],
        family_extractor: Optional[FamilyExtractor],
        number_parser: Optional[NumberParser],
    ) -> Optional[Dict[str, Any]]:
        self.logger.info("🚀 1순위 시트 Fast-Path 검색 시작")

        best_sheet: Optional[Dict[str, Any]] = None
        max_dad_amount = 0.0

        sheet_names = sorted(workbook.sheetnames)
        self.logger.info(f"🔍 시트 검색 순서: {sheet_names}")

        for sheet_name in sheet_names:
            try:
                sheet = workbook[sheet_name]
                sheet_result = self._evaluate_sheet(
                    sheet,
                    sheet_name,
                    required_keywords,
                    forbidden_keywords_map,
                    family_extractor,
                    number_parser,
                )

                if not sheet_result:
                    continue

                matched_fields = sheet_result.get('matched_fields', 0)
                families = sheet_result.get('families', [])

                if matched_fields >= 5 and families:
                    max_dad_with_mom = self._get_max_dad_with_mom_same_row(
                        sheet_result,
                        number_parser,
                    )

                    if (
                        max_dad_with_mom > max_dad_amount
                        or (
                            max_dad_with_mom == max_dad_amount
                            and (
                                best_sheet is None
                                or sheet_name < best_sheet['sheet_name']
                            )
                        )
                    ):
                        max_dad_amount = max_dad_with_mom
                        best_sheet = sheet_result
                        best_sheet['max_dad_amount'] = max_dad_amount
                        best_sheet['priority'] = '1순위'

                        self.logger.info(
                            "🎯 1순위 시트 후보 발견: '%s' (아빠값: %s원)",
                            sheet_name,
                            f"{max_dad_amount:,.0f}",
                        )

            except Exception as exc:
                self.logger.warning(
                    "시트 '%s' 1순위 검색 중 오류: %s",
                    sheet_name,
                    exc,
                )

        if best_sheet:
            self.logger.info(
                "🏆 1순위 시트 최종 선택: '%s' (아빠값: %s원)",
                best_sheet['sheet_name'],
                f"{max_dad_amount:,.0f}",
            )
        else:
            self.logger.info("❌ 1순위 시트를 찾지 못했습니다.")

        return best_sheet

    def _evaluate_sheet(
        self,
        sheet: Worksheet,
        sheet_name: str,
        required_keywords: Dict[str, List[str]],
        forbidden_keywords_map: Dict[str, List[str]],
        family_extractor: Optional[FamilyExtractor],
        number_parser: Optional[NumberParser],
    ) -> Optional[Dict[str, Any]]:
        try:
            actual_max_row, actual_max_col = self._find_actual_data_range(sheet)
            max_row = actual_max_row
            max_col = min(actual_max_col, 50)

            if max_row < 2 or max_col < 5:
                return None

            header_candidates: List[Dict[str, Any]] = []
            scan_rows = min(1000, max_row)

            for row in range(1, scan_rows + 1):
                data_density = self._calculate_data_density(sheet, row, max_col)
                matched_fields = self._count_matched_fields(
                    sheet,
                    row,
                    max_col,
                    required_keywords,
                    forbidden_keywords_map,
                )

                field_match_score = (matched_fields / 5) * 0.8
                density_score = data_density * 0.2
                header_score = field_match_score + density_score

                if matched_fields >= 3:
                    non_empty_cells = 0
                    for col in range(1, max_col + 1):
                        cell_value = sheet.cell(row=row, column=col).value
                        if cell_value is not None and str(cell_value).strip():
                            non_empty_cells += 1

                    if non_empty_cells >= 5:
                        header_candidates.append(
                            {
                                'row': row,
                                'data_density': data_density,
                                'matched_fields': matched_fields,
                                'header_score': header_score,
                                'non_empty_cells': non_empty_cells,
                            }
                        )
                        self.logger.debug(
                            "지능앱 헤더 후보: 행 %d, 점수 %.3f, 매칭 %d개, 비어있지 않은 셀 %d개",
                            row,
                            header_score,
                            matched_fields,
                            non_empty_cells,
                        )

            if not header_candidates:
                self.logger.warning(
                    "지능앱 헤더 감지: 시트 '%s'에서 적합한 헤더를 찾지 못했습니다.",
                    sheet_name,
                )
                return None

            header_candidates.sort(
                key=lambda x: (
                    x['matched_fields'],
                    x['header_score'],
                    -x['row'],
                    x['row'],
                ),
                reverse=True,
            )

            best_header = header_candidates[0]
            header_row = best_header['row']
            self.logger.info(
                "지능앱 헤더 감지: 시트 '%s'에서 최적 헤더 선택 - 행 %d (점수: %.3f, 매칭: %d개)",
                sheet_name,
                header_row,
                best_header['header_score'],
                best_header['matched_fields'],
            )

            headers: List[str] = []
            for col in range(1, max_col + 1):
                cell_value = sheet.cell(row=header_row, column=col).value
                headers.append(str(cell_value) if cell_value is not None else f"Column_{col}")

            data: List[List[Any]] = []
            data_start_row = header_row + 1
            for row in range(data_start_row, max_row + 1):
                row_data = []
                for col in range(1, max_col + 1):
                    cell_value = sheet.cell(row=row, column=col).value
                    row_data.append(cell_value)
                data.append(row_data)

            data_quality_score = self._evaluate_data_quality(data, headers)
            final_score = best_header['header_score'] * 0.7 + data_quality_score * 0.3

            families: List[Dict[str, Any]] = []
            if family_extractor:
                try:
                    families = family_extractor(sheet, required_keywords)
                except Exception as exc:  # pragma: no cover - 안전 장치
                    self.logger.warning("가족 정보 추출 중 오류: %s", exc)

            return {
                'sheet_name': sheet_name,
                'header_row': header_row,
                'data_start_row': data_start_row,
                'headers': headers,
                'data': data,
                'score': final_score,
                'matched_fields': best_header['matched_fields'],
                'data_quality': data_quality_score,
                'total_rows': len(data),
                'actual_max_row': actual_max_row,
                'actual_max_col': actual_max_col,
                'families': families,
            }

        except Exception as exc:
            self.logger.error("시트 '%s' 평가 오류: %s", sheet_name, exc)
            return None

    def get_actual_data_range(self, sheet: Worksheet) -> Tuple[int, int]:
        """공개용: 실제 데이터 범위를 반환한다."""
        return self._find_actual_data_range(sheet)

    def _find_actual_data_range(self, sheet: Worksheet) -> Tuple[int, int]:
        actual_max_row = 1
        actual_max_col = 1

        try:
            for row in sheet.iter_rows():
                for cell in row:
                    if cell.value is not None and str(cell.value).strip():
                        if cell.row > actual_max_row:
                            actual_max_row = cell.row
                        if cell.column > actual_max_col:
                            actual_max_col = cell.column

            actual_max_row = max(actual_max_row, 2)
            actual_max_col = max(actual_max_col, 5)
            self.logger.info(
                "실제 데이터 범위 감지: 행 %d, 열 %d",
                actual_max_row,
                actual_max_col,
            )
        except Exception as exc:
            self.logger.warning("실제 데이터 범위 감지 중 오류: %s", exc)
            actual_max_row = min(sheet.max_row, 1000)
            actual_max_col = min(sheet.max_column, 50)

        return actual_max_row, actual_max_col

    def _find_max_delivery_amount(self, sheet: Worksheet) -> float:
        max_amount = 0.0
        delivery_keywords = ['총배달', '배달금액', '총금액', '합계', '총합', '배달요금', '총배달요금', '총배달금액']

        try:
            for row in sheet.iter_rows():
                for cell in row:
                    if cell.value is None:
                        continue

                    cell_value = str(cell.value).lower().strip()

                    if any(keyword in cell_value for keyword in delivery_keywords):
                        col_idx = cell.column
                        for data_row in sheet.iter_rows(min_row=cell.row + 1, min_col=col_idx, max_col=col_idx):
                            for data_cell in data_row:
                                if (
                                    isinstance(data_cell.value, (int, float))
                                    and data_cell.value > max_amount
                                ):
                                    max_amount = float(data_cell.value)
                        break
        except Exception as exc:
            self.logger.warning("총배달 금액 분석 중 오류: %s", exc)

        return max_amount

    def _get_max_dad_with_mom_same_row(
        self,
        sheet_result: Dict[str, Any],
        number_parser: Optional[NumberParser],
    ) -> float:
        try:
            families = sheet_result.get('families', [])
            if not families:
                return 0.0

            max_dad_amount = 0.0
            converter = number_parser or self._default_number_parser

            for family in families:
                dad_amount = converter(family.get('공급가액', 0))
                mom_amount = converter(family.get('부가세', 0))

                if dad_amount > 0 and mom_amount > 0:
                    if dad_amount > max_dad_amount:
                        max_dad_amount = dad_amount

            self.logger.debug(
                "🔍 같은 행 아빠값 최대값: %s원",
                f"{max_dad_amount:,.0f}",
            )
            return max_dad_amount
        except Exception as exc:
            self.logger.warning("같은 행 아빠값 최대값 계산 중 오류: %s", exc)
            return 0.0

    def _count_matched_fields(
        self,
        sheet: Worksheet,
        row: int,
        max_col: int,
        required_keywords: Dict[str, List[str]],
        forbidden_keywords_map: Dict[str, List[str]],
    ) -> int:
        matched_fields = set()
        max_col = min(max_col, 50)

        for col in range(1, max_col + 1):
            cell_value = sheet.cell(row=row, column=col).value
            if cell_value is None:
                continue

            cell_text = str(cell_value).lower().strip()

            for field_type, keywords in required_keywords.items():
                if field_type in matched_fields:
                    continue

                forbidden_keywords = forbidden_keywords_map.get(field_type, [])
                if any(keyword.lower() in cell_text for keyword in forbidden_keywords):
                    self.logger.debug(
                        "금지어 감지: %s 필드에서 금지어 발견 '%s' (행 %d, 컬럼 %d)",
                        field_type,
                        cell_text,
                        row,
                        col,
                    )
                    continue

                if any(keyword.lower() in cell_text for keyword in keywords):
                    matched_fields.add(field_type)
                    self.logger.debug(
                        "지능앱 헤더 감지: %s 매칭 '%s' → '%s' (행 %d, 컬럼 %d)",
                        field_type,
                        keywords[0],
                        cell_text,
                        row,
                        col,
                    )
                    break

        matched_count = len(matched_fields)
        self.logger.debug(
            "지능앱 헤더 감지: 행 %d에서 %d개 필드 매칭 (%s)",
            row,
            matched_count,
            matched_fields,
        )

        return matched_count

    def _detect_title_rows(self, sheet: Worksheet, max_col: int) -> List[int]:
        title_rows: List[int] = []

        for row in range(1, min(21, sheet.max_row + 1)):
            text_pattern = self._analyze_text_pattern(sheet, row, max_col)
            if self._is_title_pattern(text_pattern):
                title_rows.append(row)
                self.logger.debug(
                    "제목/부제목 행 감지: %d행 - %s",
                    row,
                    text_pattern,
                )

        return title_rows

    def _analyze_text_pattern(
        self,
        sheet: Worksheet,
        row: int,
        max_col: int,
    ) -> Dict[str, int]:
        text_count = 0
        number_count = 0
        empty_count = 0
        long_text_count = 0

        max_col = min(max_col, 50)

        for col in range(1, max_col + 1):
            cell_value = sheet.cell(row=row, column=col).value

            if cell_value is None or str(cell_value).strip() == '':
                empty_count += 1
            elif isinstance(cell_value, (int, float)):
                number_count += 1
            else:
                text_count += 1
                if len(str(cell_value).strip()) > 10:
                    long_text_count += 1

        return {
            'text_count': text_count,
            'number_count': number_count,
            'empty_count': empty_count,
            'long_text_count': long_text_count,
        }

    def _is_title_pattern(self, pattern: Dict[str, int]) -> bool:
        return (
            pattern['text_count'] >= 3
            and pattern['long_text_count'] >= 1
            and pattern['number_count'] <= 1
        )

    def _calculate_data_density(
        self,
        sheet: Worksheet,
        row: int,
        max_col: int,
    ) -> float:
        text_count = 0
        number_count = 0
        empty_count = 0

        max_col = min(max_col, 50)

        for col in range(1, max_col + 1):
            cell_value = sheet.cell(row=row, column=col).value

            if cell_value is None or str(cell_value).strip() == '':
                empty_count += 1
            elif isinstance(cell_value, (int, float)):
                number_count += 1
            else:
                text_count += 1

        total_cells = max_col
        if total_cells == 0:
            return 0.0

        text_ratio = text_count / total_cells
        number_ratio = number_count / total_cells
        empty_ratio = empty_count / total_cells

        header_score = text_ratio * 2 + number_ratio * 0.5 + empty_ratio * 0.1
        return header_score

    def _evaluate_data_quality(
        self,
        data: List[List[Any]],
        headers: List[str],
    ) -> float:
        if not data or not headers:
            return 0.0

        total_cells = len(data) * len(headers)
        if total_cells == 0:
            return 0.0

        empty_cells = 0
        for row in data:
            for cell in row:
                if cell is None or str(cell).strip() == "":
                    empty_cells += 1

        completeness_score = 1.0 - (empty_cells / total_cells)

        consistency_score = 0.0
        if len(data) > 1:
            row_lengths = [
                len([cell for cell in row if cell is not None and str(cell).strip()])
                for row in data
            ]
            if row_lengths:
                avg_length = sum(row_lengths) / len(row_lengths)
                variance = sum((length - avg_length) ** 2 for length in row_lengths) / len(row_lengths)
                consistency_score = max(0.0, 1.0 - (variance / (avg_length + 1)))

        quality_score = completeness_score * 0.7 + consistency_score * 0.3
        return min(1.0, max(0.0, quality_score))

    # ------------------------------------------------------------------
    # 내부 유틸리티 (CSV)
    # ------------------------------------------------------------------
    def _calculate_csv_data_density(self, df: pd.DataFrame, row_idx: int) -> float:
        if row_idx >= len(df):
            return 0.0

        row_data = df.iloc[row_idx]
        text_count = 0
        number_count = 0
        empty_count = 0

        for value in row_data:
            if pd.isna(value) or str(value).strip() == "":
                empty_count += 1
            elif isinstance(value, (int, float)):
                number_count += 1
            else:
                text_count += 1

        total_cells = len(row_data)
        if total_cells == 0:
            return 0.0

        text_ratio = text_count / total_cells
        number_ratio = number_count / total_cells
        empty_ratio = empty_count / total_cells

        header_score = text_ratio * 2 + number_ratio * 0.5 + empty_ratio * 0.1
        return header_score

    def _count_csv_matched_fields(
        self,
        df: pd.DataFrame,
        row_idx: int,
        required_keywords: Dict[str, List[str]],
    ) -> int:
        if row_idx >= len(df):
            return 0

        matched_fields = set()
        row_data = df.iloc[row_idx]

        for cell_value in row_data:
            if pd.isna(cell_value):
                continue

            cell_text = str(cell_value).lower().strip()

            for field_type, keywords in required_keywords.items():
                if field_type in matched_fields:
                    continue

                if any(keyword.lower() in cell_text for keyword in keywords):
                    matched_fields.add(field_type)
                    break

        matched_count = len(matched_fields)
        self.logger.debug(
            "지능앱 CSV 헤더 감지: 행 %d에서 %d개 필드 매칭 (%s)",
            row_idx,
            matched_count,
            matched_fields,
        )

        return matched_count

    # ------------------------------------------------------------------
    # 설정/빌더
    # ------------------------------------------------------------------
    def _build_forbidden_keywords_map(self) -> Dict[str, List[str]]:
        """필요 이상의 금지어를 적용하지 않는다."""
        return {
            'business_number': [],
            'store_name': [],
            'representative': [],
            'address': [],
            'email': [],
        }

    def _get_scoring_config(self) -> Tuple[Dict[str, int], Dict[str, int], bool]:
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

    def _score_representative_header(self, header: str) -> int:
        header_lower = header.strip().lower()

        if not header_lower or header_lower in {'', 'none', 'nan'}:
            return -100

        score = 0

        if '대표자' in header_lower:
            score += 90
        elif '대표' in header_lower:
            score += 70

        if any(keyword in header_lower for keyword in ['사장', '원장', '점주', '대표원장']):
            score += 60

        if any(keyword in header_lower for keyword in ['성명', '성함', '이름']):
            score += 40

        if any(keyword in header_lower for keyword in ['공급받는자', '수취인', '구매자', '거래처', '고객', '매입자', '업체', '가맹점', '매장', '점포', '업소']):
            score += 10

        if any(keyword in header_lower for keyword in ['담당', '매니저', '관리자', '점장']):
            score -= 30

        if any(keyword in header_lower for keyword in ['등록자', '작성자', '입력자']):
            score -= 50

        if '대표번호' in header_lower:
            score -= 80

        if '번호' in header_lower and not any(keyword in header_lower for keyword in ['성명', '성함', '이름']):
            score -= 60

        return score

    def _select_by_score(
        self,
        sheet_results: List[Dict[str, Any]],
        thresholds: Dict[str, int],
        override_all5: bool,
    ) -> Optional[Dict[str, Any]]:
        if not sheet_results:
            return None

        if override_all5:
            all5 = [r for r in sheet_results if r.get('core_fields_found', 0) >= 5]
            if all5:
                all5.sort(key=lambda r: (
                    r.get('scoring_points', 0),
                    r.get('total_rows', 0),
                    -r.get('header_row', 0),
                    r.get('sheet_name', ''),
                ), reverse=True)
                return all5[0]

            passing = [r for r in sheet_results if r.get('scoring_points', 0) >= thresholds.get('pass', 80)]
            if passing:
                passing.sort(key=lambda r: (
                    r.get('scoring_points', 0),
                    r.get('total_rows', 0),
                    -r.get('header_row', 0),
                    r.get('sheet_name', ''),
                ), reverse=True)
                return passing[0]

            candidates = [r for r in sheet_results if r.get('scoring_points', 0) >= thresholds.get('candidate', 70)]
            if candidates:
                candidates.sort(key=lambda r: (
                    r.get('scoring_points', 0),
                    r.get('total_rows', 0),
                    -r.get('header_row', 0),
                    r.get('sheet_name', ''),
                ), reverse=True)
                return candidates[0]

        sheet_results.sort(key=lambda r: (r.get('score', 0), r.get('sheet_name', '')), reverse=True)
        return sheet_results[0]

    # ------------------------------------------------------------------
    # 내부 공용 유틸리티
    # ------------------------------------------------------------------
    def _default_number_parser(self, value: Any) -> float:
        try:
            if value is None:
                return 0.0
            if isinstance(value, (int, float)):
                return float(value)
            stripped = str(value).strip().replace(',', '')
            return float(stripped) if stripped not in ['', 'None', 'nan'] else 0.0
        except Exception:
            return 0.0


