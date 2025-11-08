from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence

from dotenv import load_dotenv
from google import genai
from google.genai import types
from json_repair import repair_json


class GeminiLLM:
    """Wrapper around the Gemini SDK with file-backed system instructions."""

    MODEL = "gemini-flash-2.5"
    MAX_THINKING_BUDGET = 24_576

    def __init__(
        self,
        system_prompt_path: str | Path,
        *,
        client: genai.Client | None = None,
        dotenv_path: str | Path | None = None,
        filter_json: bool = False,
    ) -> None:
        self._system_prompt_path = Path(system_prompt_path)
        self._system_prompt = self._system_prompt_path.read_text(encoding="utf-8")
        if dotenv_path is not None:
            load_dotenv(dotenv_path=Path(dotenv_path))
        else:
            load_dotenv()
        self._client = client or genai.Client()
        self._filter_json = filter_json

    @property
    def system_prompt(self) -> str:
        return self._system_prompt

    def generate(self, user_prompts: Sequence[str]) -> Any:
        if not user_prompts:
            raise ValueError("user_prompts must not be empty.")

        contents = "\n".join(user_prompts)
        config = types.GenerateContentConfig(
            system_instruction=self._system_prompt,
            thinking_config=types.ThinkingConfig(thinking_budget=self.MAX_THINKING_BUDGET),
        )
        response = self._client.models.generate_content(
            model=self.MODEL,
            contents=contents,
            config=config,
        )
        if not self._filter_json:
            return response

        return self._parse_response_json(response)

    def _parse_response_json(self, response: Any) -> Any:
        """Extract and repair JSON content from a Gemini response."""
        text = getattr(response, "text", None)
        if not isinstance(text, str):
            raise AttributeError("Response object does not expose a text attribute for JSON parsing.")

        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("Response text does not contain JSON object delimiters.")

        json_fragment = text[start : end + 1]
        repaired = repair_json(json_fragment)
        return json.loads(repaired)
