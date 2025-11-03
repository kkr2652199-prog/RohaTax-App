"""파일 파싱 사전 검증 파이프라인."""

from __future__ import annotations

import logging
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .validators import FileUploadValidator, ValidationResult


@dataclass(frozen=True)
class PreValidationResult:
    """파일 파싱 전에 수행하는 사전 검증 결과."""

    is_valid: bool
    message: Optional[str] = None
    file_type: Optional[str] = None
    suffix: Optional[str] = None


class ValidationPipeline:
    """FileParser가 활용하는 사전 검증 파이프라인."""

    def __init__(
        self,
        upload_validator: FileUploadValidator,
        *,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self._upload_validator = upload_validator
        self._logger = logger or logging.getLogger(__name__)

    def run(self, file_path: Path) -> PreValidationResult:
        """파일 존재 여부/확장자/손상 여부 등을 순차적으로 검증한다."""

        file_path = Path(file_path)

        upload_result = self._upload_validator.validate(file_path)
        if not upload_result.is_valid:
            return PreValidationResult(False, upload_result.message)

        suffix = file_path.suffix.lower()

        if suffix in {".xlsx", ".xls"}:
            excel_result = self._validate_excel(file_path, suffix)
            if not excel_result.is_valid:
                return PreValidationResult(
                    False,
                    excel_result.message,
                    file_type="excel",
                    suffix=suffix,
                )
            return PreValidationResult(True, file_type="excel", suffix=suffix)

        if suffix == ".csv":
            csv_result = self._validate_csv(file_path)
            if not csv_result.is_valid:
                return PreValidationResult(
                    False,
                    csv_result.message,
                    file_type="csv",
                    suffix=suffix,
                )
            return PreValidationResult(True, file_type="csv", suffix=suffix)

        self._logger.warning("지원하지 않는 파일 확장자: %s", suffix or "<없음>")
        return PreValidationResult(
            False,
            f"지원하지 않는 파일 형식입니다. ({suffix or '확장자 없음'})",
            suffix=suffix,
        )

    # ------------------------------------------------------------------
    # 내부 검증 단계
    # ------------------------------------------------------------------
    def _validate_excel(self, file_path: Path, suffix: str) -> ValidationResult:
        try:
            if suffix == ".xlsx" and not zipfile.is_zipfile(file_path):
                self._logger.error("손상된 Excel 구조 감지: %s", file_path)
                return ValidationResult(
                    False,
                    "업로드하신 Excel 파일이 손상되었거나 지원하지 않는 형식입니다. "
                    "엑셀에서 '다른 이름으로 저장' 후 다시 시도해주세요.",
                )
        except Exception as exc:  # pragma: no cover - 방어적 로깅
            self._logger.error("Excel 파일 구조 검증 중 오류: %s", exc)
            return ValidationResult(
                False,
                "Excel 파일 검증 중 오류가 발생했습니다. 관리자에게 문의해주세요.",
            )

        return ValidationResult(True)

    def _validate_csv(self, file_path: Path) -> ValidationResult:
        try:
            if file_path.stat().st_size == 0:
                self._logger.warning("CSV 파일이 비어 있습니다: %s", file_path)
                return ValidationResult(False, "CSV 파일이 비어 있습니다.")
        except FileNotFoundError:
            return ValidationResult(False, "업로드된 파일을 찾을 수 없습니다.")
        except Exception as exc:  # pragma: no cover - 방어적 로깅
            self._logger.error("CSV 파일 검증 중 오류: %s", exc)
            return ValidationResult(
                False,
                "CSV 파일 검증 중 오류가 발생했습니다. 관리자에게 문의해주세요.",
            )

        return ValidationResult(True)


