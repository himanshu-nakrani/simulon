"""
conftest.py — install a `transformers` stub before any test module is imported.

The llm_service module loads T5Tokenizer and T5ForConditionalGeneration at
import time (module-level singleton).  By stubbing `transformers` here, in
conftest, we guarantee the stub is in sys.modules before pytest collects
test_llm_service.py.
"""

import sys
import types
from unittest.mock import MagicMock

# Build a minimal stub that satisfies the two names used by llm_service.py.
_stub = types.ModuleType("transformers")
_stub.T5Tokenizer = MagicMock()
_stub.T5ForConditionalGeneration = MagicMock()

# Only inject if the real package is not already present (or is already a stub).
existing = sys.modules.get("transformers")
if existing is None or not hasattr(existing, "T5Tokenizer"):
    sys.modules["transformers"] = _stub
elif not isinstance(existing.T5Tokenizer, MagicMock):
    # Real transformers is installed — replace with stub to keep tests fast.
    sys.modules["transformers"] = _stub
