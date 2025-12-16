"""파일 업로드 및 형식 검증 유틸리티."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ValidationResult:
    """단일 파일 검증 결과."""

    is_valid: bool
    message: Optional[str] = None


class FileUploadValidator:
    """파일 업로드 사전 검증 전용 유틸리티."""

    def __init__(
        self,
        supported_formats: Iterable[str],
        max_size_mb: int = 100,
        *,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.supported_formats = {fmt.lower() for fmt in supported_formats}
        self.max_size_mb = max_size_mb
        self.logger = logger or logging.getLogger(__name__)

    def validate(self, file_path: Path) -> ValidationResult:
        """파일 존재 여부, 확장자, 크기를 순차적으로 검증한다."""

        file_path = Path(file_path)

        if not self._exists(file_path):
            return ValidationResult(False, "업로드된 파일을 찾을 수 없습니다.")

        if not self._has_supported_extension(file_path):
            return ValidationResult(
                False,
                f"지원하지 않는 파일 형식입니다. ({file_path.suffix or '확장자 없음'})",
            )

        if not self._within_size_limit(file_path):
            return ValidationResult(
                False,
                f"파일 크기가 {self.max_size_mb}MB 제한을 초과합니다.",
            )

        return ValidationResult(True)

    def _exists(self, file_path: Path) -> bool:
        exists = file_path.exists()
        if not exists:
            self.logger.warning("파일을 찾을 수 없습니다: %s", file_path)
        return exists

    def _has_supported_extension(self, file_path: Path) -> bool:
        extension = file_path.suffix.lower()
        if extension not in self.supported_formats:
            self.logger.warning("지원하지 않는 파일 확장자: %s", extension or "<없음>")
            return False
        return True

    def _within_size_limit(self, file_path: Path) -> bool:
        try:
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
        except FileNotFoundError:
            self.logger.warning("크기 확인 중 파일이 사라졌습니다: %s", file_path)
            return False

        if file_size_mb > self.max_size_mb:
            self.logger.warning(
                "파일 크기가 제한을 초과했습니다: %.2fMB (제한: %dMB)",
                file_size_mb,
                self.max_size_mb,
            )
            return False

        return True
