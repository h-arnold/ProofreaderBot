from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any, Callable, Protocol, Sequence

ProviderReporter = Callable[[str, "ProviderStatus", Exception | None], None]


class ProviderStatus(str, Enum):
    """Status used when reporting the outcome of a provider call."""

    SUCCESS = "success"
    QUOTA = "quota"
    FAILURE = "failure"
    UNSUPPORTED = "unsupported"


class LLMProviderError(Exception):
    """Generic failure raised by an LLM provider."""


class LLMQuotaError(LLMProviderError):
    """Raised when a provider reports quota or rate-limit exhaustion."""


class LLMProviderConfigurationError(LLMProviderError):
    """Raised when a provider cannot be configured or authenticated."""


class LLMProvider(Protocol):
    """Shared contract for LLM providers."""

    name: str

    def generate(
        self,
        user_prompts: Sequence[str],
        *,
        filter_json: bool = False,
    ) -> Any:
        """Produce a single response for the provided prompts."""
        ...

    def batch_generate(
        self,
        batch_payload: Sequence[Sequence[str]],
        *,
        filter_json: bool = False,
    ) -> Sequence[Any]:
        """Process multiple prompt groups in a single request."""
        ...

    def health_check(self) -> bool:
        """Optional quick check that returns True when the provider is ready."""
        ...


class ProviderFactory(Protocol):
    def __call__(
        self,
        *,
        system_prompt: str | Path,
        filter_json: bool,
        dotenv_path: str | Path | None,
    ) -> LLMProvider: ...
