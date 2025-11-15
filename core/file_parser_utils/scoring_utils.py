"""점수 계산 유틸리티 전담 모듈."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

import pandas as pd
from openpyxl.worksheet.worksheet import Worksheet

logger = logging.getLogger(__name__)


def count_matched_fields(
    sheet: Worksheet,
    row: int,
    max_col: int,
    required_keywords: Dict[str, List[str]],
    forbidden_keywords_map: Dict[str, List[str]],
) -> int:
    """필드 매칭 개수를 계산한다."""
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
                logger.debug(
                    "금지어 감지: %s 필드에서 금지어 발견 '%s' (행 %d, 컬럼 %d)",
                    field_type,
                    cell_text,
                    row,
                    col,
                )
                continue

            if any(keyword.lower() in cell_text for keyword in keywords):
                matched_fields.add(field_type)
                logger.debug(
                    "지능앱 헤더 감지: %s 매칭 '%s' → '%s' (행 %d, 컬럼 %d)",
                    field_type,
                    keywords[0],
                    cell_text,
                    row,
                    col,
                )
                break

    matched_count = len(matched_fields)
    logger.debug(
        "지능앱 헤더 감지: 행 %d에서 %d개 필드 매칭 (%s)",
        row,
        matched_count,
        matched_fields,
    )

    return matched_count


def calculate_data_density(
    sheet: Worksheet,
    row: int,
    max_col: int,
) -> float:
    """데이터 밀도를 계산한다."""
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


def evaluate_data_quality(
    data: List[List[Any]],
    headers: List[str],
) -> float:
    """데이터 품질을 평가한다."""
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


def calculate_csv_data_density(df: pd.DataFrame, row_idx: int) -> float:
    """CSV 데이터 밀도를 계산한다."""
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


def count_csv_matched_fields(
    df: pd.DataFrame,
    row_idx: int,
    required_keywords: Dict[str, List[str]],
) -> int:
    """CSV 필드 매칭 개수를 계산한다."""
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
    logger.debug(
        "지능앱 CSV 헤더 감지: 행 %d에서 %d개 필드 매칭 (%s)",
        row_idx,
        matched_count,
        matched_fields,
    )

    return matched_count


def score_representative_header(header: str) -> int:
    """대표자 헤더 점수를 계산한다."""
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

