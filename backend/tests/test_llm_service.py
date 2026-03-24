"""Property-based tests for LLMService.

Property 6: LLM structuring always returns valid dict
Validates: Requirements 2.1, 2.2, 2.3, 2.4

The `transformers` package is stubbed out in conftest.py so the module-level
singleton in llm_service.py does not attempt to load the real model.
"""

from unittest.mock import MagicMock

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from backend.app.services.llm_service import LLMService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MALFORMED_OUTPUTS = [
    "not json at all",
    "{ broken",
    "",
    "null",
    '{"decision": "x"}',
    '{"decision": "x", "options": ["only_one"], "factors": ["f"]}',
    '{"decision": "x", "options": ["a", "b"], "factors": []}',
    "<<<invalid>>>",
    "True",
    "[]",
]


def _make_service(raw_output: str) -> LLMService:
    """Return an LLMService whose _generate() always returns *raw_output*."""
    mock_tokenizer = MagicMock()
    mock_tokenizer.return_value = {"input_ids": MagicMock()}
    mock_tokenizer.decode.return_value = raw_output

    mock_model = MagicMock()
    mock_model.generate.return_value = [MagicMock()]

    # Bypass __init__ to avoid touching the module-level singleton.
    service = LLMService.__new__(LLMService)
    service._tokenizer = mock_tokenizer
    service._model = mock_model
    return service


# ---------------------------------------------------------------------------
# Property 6: LLM structuring always returns valid dict
# Validates: Requirements 2.1, 2.2, 2.3, 2.4
# ---------------------------------------------------------------------------

@given(decision_text=st.text(min_size=1))
@settings(max_examples=50)
def test_structure_input_always_returns_valid_dict(decision_text):
    """**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

    For any non-empty decision_text, even when the model returns malformed
    output, structure_input must:
    - return a dict
    - contain key 'decision'
    - contain key 'options' with len >= 2
    - contain key 'factors' with len >= 1
    - never raise an exception
    """
    service = _make_service("not json at all")
    result = service.structure_input(decision_text)

    assert isinstance(result, dict), "structure_input must return a dict"
    assert "decision" in result, "result must contain 'decision' key"
    assert "options" in result, "result must contain 'options' key"
    assert "factors" in result, "result must contain 'factors' key"
    assert len(result["options"]) >= 2, "options must have at least 2 elements"
    assert len(result["factors"]) >= 1, "factors must have at least 1 element"


@pytest.mark.parametrize("malformed_output", MALFORMED_OUTPUTS)
def test_structure_input_fallback_on_malformed_output(malformed_output):
    """Verify fallback dict is returned for each known malformed output variant."""
    service = _make_service(malformed_output)
    result = service.structure_input("Should I switch jobs?")

    assert isinstance(result, dict)
    assert "decision" in result
    assert "options" in result
    assert "factors" in result
    assert len(result["options"]) >= 2
    assert len(result["factors"]) >= 1
