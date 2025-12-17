"""병렬/배치 파일 처리 유틸리티.

FileParser가 수행하던 병렬 처리·배치 검증 책임을 전담하는 모듈입니다.
"""

from __future__ import annotations

import concurrent.futures
import importlib
import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional


def _load_parallel_processor():
    """병렬 처리 모듈을 지연 로딩하여 임포트 경로 문제를 방지."""

    module = importlib.import_module("core.file_parser_utils.parallel_processor")
    return module.ParallelFileProcessor, module.ProcessingMode

if TYPE_CHECKING:  # pragma: no cover - 순환 참조 방지용 타입 힌트
    from core.file_parser import FileParser


class ParallelRunner:
    """FileParser를 위한 병렬/배치 처리 헬퍼."""

    def __init__(self, parser: "FileParser", logger: Optional[logging.Logger] = None) -> None:
        self._parser = parser
        self._logger = logger or logging.getLogger(__name__)
        self._validator = parser.file_upload_validator
        self._supported_formats = list(parser.supported_formats)

    # ------------------------------------------------------------------
    # ThreadPoolExecutor 기반 병렬 처리
    # ------------------------------------------------------------------
    def parse_multiple_files_parallel(
        self,
        file_paths: List[Path],
        max_workers: int = 4,
    ) -> List[Dict[str, Any]]:
        if not file_paths:
            return []

        results: List[Dict[str, Any]] = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {
                executor.submit(self._parser.parse_file, path): path for path in file_paths
            }

            for future in concurrent.futures.as_completed(future_to_file):
                path = future_to_file[future]
                try:
                    result = future.result()
                    result["file_path"] = str(path)
                    results.append(result)
                    self._logger.info("병렬 처리 완료: %s", path)
                except Exception as exc:  # pragma: no cover - 방어적 로깅
                    error_result = self._parser._create_error_response(  # noqa: SLF001
                        f"병렬 처리 중 오류: {exc}"
                    )
                    error_result["file_path"] = str(path)
                    results.append(error_result)
                    self._logger.error("병렬 처리 실패: %s - %s", path, exc)

        return results

    def batch_validate_files(self, file_paths: List[Path], max_workers: int = 4) -> Dict[str, Any]:
        validation_results: Dict[str, Any] = {
            "valid_files": [],
            "invalid_files": [],
            "total_files": len(file_paths),
            "processing_time": 0.0,
        }

        if not file_paths:
            return validation_results

        start_time = time.time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {
                executor.submit(self._validator.validate, path): path for path in file_paths
            }

            for future in concurrent.futures.as_completed(future_to_file):
                path = future_to_file[future]
                try:
                    result = future.result()
                except Exception as exc:  # pragma: no cover - 방어적 로깅
                    validation_results["invalid_files"].append(str(path))
                    self._logger.error("파일 검증 실패: %s - %s", path, exc)
                    continue

                if result.is_valid:
                    validation_results["valid_files"].append(str(path))
                else:
                    validation_results["invalid_files"].append(str(path))
                    if result.message:
                        self._logger.warning(
                            "파일 검증 실패(%s): %s", path, result.message
                        )

        validation_results["processing_time"] = time.time() - start_time
        return validation_results

    # ------------------------------------------------------------------
    # ParallelFileProcessor 기반 고성능 처리
    # ------------------------------------------------------------------
    def parse_multiple_files_optimized(
        self,
        file_paths: List[Path],
        max_workers: int = 4,
    ) -> List[Dict[str, Any]]:
        if not file_paths:
            return []

        ParallelFileProcessor, ProcessingMode = _load_parallel_processor()
        processor = ParallelFileProcessor(
            max_workers=max_workers,
            processing_mode=ProcessingMode.HYBRID,
            chunk_size=50,
        )

        results = processor.process_files_parallel(
            [str(path) for path in file_paths],
            self._parse_single_file_optimized,
        )

        parsed_results: List[Dict[str, Any]] = []
        for item in results:
            if item.success:
                parsed_results.append(item.data)
            else:
                error_result = self._parser._create_error_response(  # noqa: SLF001
                    f"파일 처리 실패: {item.error}"
                )
                error_result["file_path"] = item.file_path
                parsed_results.append(error_result)

        report = processor.get_performance_report()
        self._logger.info(
            "최적화된 병렬 처리 완료: %s/%s 성공 (%.2f초, %.2f 파일/초)",
            report["successful_files"],
            report["total_files"],
            report["total_time"],
            report["throughput"],
        )

        return parsed_results

    def process_files_with_progress(
        self,
        file_paths: List[Path],
        progress_callback: Optional[Callable[[float, int, int], None]] = None,
    ) -> List[Dict[str, Any]]:
        if not file_paths:
            return []

        total_files = len(file_paths)
        collected_results: List[Dict[str, Any]] = []

        def _parse_and_track(path: str) -> Dict[str, Any]:
            result = self._parse_single_file_optimized(path)
            collected_results.append(result)
            if progress_callback:
                progress = len(collected_results) / total_files * 100
                progress_callback(progress, len(collected_results), total_files)
            return result

        ParallelFileProcessor, ProcessingMode = _load_parallel_processor()
        processor = ParallelFileProcessor(
            max_workers=4,
            processing_mode=ProcessingMode.THREAD,
            chunk_size=10,
        )

        results = processor.process_files_parallel(
            [str(path) for path in file_paths],
            _parse_and_track,
        )

        parsed_results: List[Dict[str, Any]] = []
        for item in results:
            if item.success:
                parsed_results.append(item.data)
            else:
                error_result = self._parser._create_error_response(  # noqa: SLF001
                    f"파일 처리 실패: {item.error}"
                )
                error_result["file_path"] = item.file_path
                parsed_results.append(error_result)

        if progress_callback:
            progress_callback(100.0, total_files, total_files)

        return parsed_results

    # ------------------------------------------------------------------
    # 보조 유틸
    # ------------------------------------------------------------------
    def validate_single_file(self, file_path: Path) -> bool:
        try:
            if not file_path.exists():
                return False

            if file_path.suffix.lower() not in self._supported_formats:
                return False

            if file_path.stat().st_size > 100 * 1024 * 1024:
                return False

            return True
        except Exception:  # pragma: no cover - 방어적 처리
            return False

    # ------------------------------------------------------------------
    # 내부 헬퍼
    # ------------------------------------------------------------------
    def _parse_single_file_optimized(self, file_path: str) -> Dict[str, Any]:
        path_obj = Path(file_path)
        return self._parser.parse_file(path_obj)

