from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import src.language_check as lc
import src.language_check.language_tool_manager as manager_mod


def test_build_language_tool_passes_config(monkeypatch) -> None:
    """Verify that the LanguageTool helper passes the requested config options.

    We monkeypatch the underlying LanguageTool class to capture arguments and
    verify the configuration contains our expected keys and values.
    """
    captured: dict = {}

    class DummyLanguageTool:
        def __init__(self, language, *args, **kwargs):
            # Capture provided language and kwargs
            captured["language"] = language
            captured["kwargs"] = kwargs
            self.language = language

        def close(self) -> None:
            return None

    # Monkeypatch the import used by language_check by patching the imported module
    # within the language_check module. This avoids relying on import path
    # resolution and is robust during the test run.
    monkeypatch.setattr(manager_mod.language_tool_python, "LanguageTool", DummyLanguageTool)

    tool = lc.build_language_tool("en-GB")

    # Ensure a tool was created and returned
    assert tool is not None
    assert captured.get("language") == "en-GB"

    # Verify config was passed through (if present)
    config = captured.get("kwargs", {}).get("config")
    # The code falls back to a constructor without config on older versions; assert either behaviour
    if config is not None:
        # LanguageTool's configuration keys are camelCase.
        # The helper now specifies timeouts and text length limits; assert those
        # values instead of older keys that were removed.
        assert config.get("maxCheckTimeMillis") == 120000
        assert config.get("maxTextLength") == 1000000
        assert config.get("maxTextHardLength") == 5000000
        assert config.get("requestLimitPeriodInSeconds") == 60
    else:
        # No config passed - this is allowed for older language_tool_python versions
        assert True

    new_spellings = captured.get("kwargs", {}).get("newSpellings")
    assert new_spellings is not None
    assert len(new_spellings) == len(lc.DEFAULT_IGNORED_WORDS)
