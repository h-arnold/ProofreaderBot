from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Sequence

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.llm.provider import (
    LLMProvider,
    LLMProviderError,
    LLMQuotaError,
    ProviderStatus,
)
from src.llm.service import LLMService


class _DummyProvider(LLMProvider):
    name = "dummy"

    def __init__(
        self, *, result: Any | None = None, error: Exception | None = None
    ) -> None:
        self._result = result
        self._error = error

    def generate(
        self,
        user_prompts: Sequence[str],
        *,
        filter_json: bool = False,
    ) -> Any:
        if self._error:
            raise self._error
        return self._result

    def batch_generate(
        self,
        batch_payload: Sequence[Sequence[str]],
        *,
        filter_json: bool = False,
    ) -> Sequence[Any]:
        if self._error:
            raise self._error
        return [self._result]

    def health_check(self) -> bool:
        return True


def test_generate_uses_priority_order() -> None:
    service = LLMService(
        [
            _DummyProvider(result="first"),
            _DummyProvider(result="second"),
        ]
    )

    assert service.generate(["prompt"]) == "first"


def test_generate_falls_back_when_quota_exhausted() -> None:
    service = LLMService(
        [
            _DummyProvider(error=LLMQuotaError("limit")),
            _DummyProvider(result="success"),
        ]
    )

    assert service.generate(["prompt"]) == "success"


def test_generate_raises_on_failed_provider() -> None:
    service = LLMService(
        [
            _DummyProvider(error=LLMProviderError("boom")),
            _DummyProvider(result="ignored"),
        ]
    )

    with pytest.raises(LLMProviderError):
        service.generate(["prompt"])


def test_batch_generate_skips_unsupported_provider() -> None:
    class _UnsupportedProvider(_DummyProvider):
        def batch_generate(
            self,
            batch_payload: Sequence[Sequence[str]],
            *,
            filter_json: bool = False,
        ) -> Sequence[Any]:
            raise NotImplementedError()

    service = LLMService(
        [
            _UnsupportedProvider(),
            _DummyProvider(result="batch-success"),
        ]
    )

    assert service.batch_generate([["prompt"]]) == ["batch-success"]


def test_batch_generate_raises_when_all_quota() -> None:
    service = LLMService(
        [
            _DummyProvider(error=LLMQuotaError("limit")),
            _DummyProvider(error=LLMQuotaError("limit")),
        ]
    )

    with pytest.raises(LLMQuotaError):
        service.batch_generate([["prompt"]])


def test_reporting_hook_records_statuses() -> None:
    events: list[tuple[str, ProviderStatus, Exception | None]] = []

    def reporter(
        name: str, status: ProviderStatus, error: Exception | None = None
    ) -> None:
        events.append((name, status, error))

    service = LLMService(
        [
            _DummyProvider(error=LLMQuotaError("limit")),
            _DummyProvider(result="final"),
        ],
        reporter=reporter,
    )

    service.generate(["prompt"])

    assert len(events) == 2
    assert events[0][1] == ProviderStatus.QUOTA
    assert events[1][1] == ProviderStatus.SUCCESS
