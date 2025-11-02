"""파싱 결과 리포팅/요약 유틸리티."""

from __future__ import annotations

import logging
from typing import Any, Dict

import pandas as pd


class ReportingUtils:
    """리포트 및 요약 데이터를 생성하는 헬퍼."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger(__name__)

    def analyze_data_sections(self, df: pd.DataFrame) -> Dict[str, Any]:
        """데이터 섹션 정보를 분석한다."""

        sections = {
            "header_section": None,
            "data_section": None,
            "summary_section": None,
            "total_rows": len(df),
        }

        try:
            sections["data_section"] = df.to_dict("records")

            if len(df) > 3:
                sections["summary_section"] = df.tail(3).to_dict("records")

            self.logger.info("데이터 섹션 분석 완료: 총 %d행", len(df))
        except Exception as exc:  # pragma: no cover - 보호 로깅
            self.logger.error("데이터 섹션 분석 오류: %s", exc)

        return sections

    def build_preview(self, parsed_data: Dict[str, Any], max_rows: int = 10) -> Dict[str, Any]:
        """미리보기 데이터를 생성한다."""

        if parsed_data.get("parsing_status") != "success":
            return {"error": "파싱 실패"}

        try:
            df: pd.DataFrame = parsed_data["raw_data"]
            preview = df.head(max_rows)
            return {
                "headers": list(df.columns),
                "preview_data": preview.to_dict("records"),
                "total_rows": len(df),
                "file_type": parsed_data.get("file_type"),
            }
        except Exception as exc:  # pragma: no cover - 보호 로깅
            self.logger.error("데이터 미리보기 오류: %s", exc)
            return {"error": f"미리보기 생성 오류: {exc}"}

    def extract_text_content(self, parsed_data: Dict[str, Any]) -> str:
        """텍스트 분석 등을 위한 전체 텍스트 콘텐츠를 생성한다."""

        if parsed_data.get("parsing_status") != "success":
            return ""

        try:
            df: pd.DataFrame = parsed_data["raw_data"]
            texts: list[str] = []

            for _, row in df.iterrows():
                for value in row.values:
                    if pd.notna(value):
                        value_str = str(value).strip()
                        if value_str:
                            texts.append(value_str)

            return " ".join(texts)
        except Exception as exc:  # pragma: no cover - 보호 로깅
            self.logger.error("텍스트 추출 오류: %s", exc)
            return ""


