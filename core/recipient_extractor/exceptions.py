"""Recipient extractor 전용 예외 정의."""


class RecipientExtractorError(RuntimeError):
    """공급받는자 추출 파이프라인 전반에서 발생하는 기본 예외."""


class StageExecutionError(RecipientExtractorError):
    """우선순위 규칙 실행 중 발생하는 예외."""


class PipelineExecutionError(RecipientExtractorError):
    """파이프라인 전체 실행 중 발생하는 예외."""


class NormalizationError(RecipientExtractorError):
    """정규화 단계에서 발생하는 예외."""



