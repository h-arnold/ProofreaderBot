from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from .provider import LLMProvider


class MistralLLM(LLMProvider):
    """Stub implementation until a real Mistral integration is provided."""

    name = "mistral"

    def __init__(
        self,
        system_prompt: str | Path,
        *,
        filter_json: bool = False,
        dotenv_path: str | Path | None = None,
    ) -> None:
        self._system_prompt = system_prompt
        self._filter_json = filter_json
        self._dotenv_path = dotenv_path

    def generate(
        self,
        user_prompts: Sequence[str],
        *,
        filter_json: bool = False,
    ) -> Any:
        raise NotImplementedError("Mistral integration is not available yet.")

    def batch_generate(
        self,
        batch_payload: Sequence[Sequence[str]],
        *,
        filter_json: bool = False,
    ) -> Sequence[Any]:
        raise NotImplementedError("Batch support for Mistral is not available yet.")

    def health_check(self) -> bool:
        return False