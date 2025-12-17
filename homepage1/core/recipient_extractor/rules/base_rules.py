"""Base definitions for recipient extraction priority rules.

이 모듈은 파이프라인 내부에서 단계별 우선순위 규칙을 pluggable 하게
적용할 수 있도록 하는 공통 인터페이스를 제공한다. 실제 로직은
`priority_stage_one.py` 등의 하위 모듈에서 구현한다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol


class SupportsLogger(Protocol):
    """Pipeline이 보유한 logger 속성을 타입 안전하게 참조하기 위한 Protocol."""

    logger: Any


@dataclass(slots=True)
class RuleContext:
    """우선순위 규칙에 전달되는 공통 컨텍스트 데이터 구조."""

    parsed_data: Dict[str, Any]
    stats: Dict[str, Any] = field(default_factory=dict)
    industry: Optional[str] = None
    extras: Dict[str, Any] = field(default_factory=dict)


class RuleExecutionError(RuntimeError):
    """우선순위 규칙 실행 중 발생한 예외."""


class BasePriorityRule:
    """우선순위 규칙 구현 시 상속해야 하는 기본 클래스."""

    rule_name: str = "base"

    def __init__(self, pipeline: SupportsLogger) -> None:
        self.pipeline = pipeline
        self.logger = getattr(pipeline, "logger", None)

    def __getattr__(self, item: str):
        return getattr(self.pipeline, item)

    def prepare(self, context: RuleContext) -> None:
        """규칙 실행 전에 필요한 준비 작업이 있다면 오버라이드한다."""

    def run(
        self,
        context: RuleContext,
        recipients: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """규칙 실행에 대한 기본 구현. 하위 클래스에서 반드시 오버라이드한다."""

        raise NotImplementedError("Priority rule must implement run() method")

    def finalize(
        self, context: RuleContext, recipients: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """규칙 실행 후 후처리 단계가 필요하면 오버라이드한다."""

        return recipients


