"""LLM Service wrapping google/flan-t5-base for input structuring and explanation generation."""

import json
import logging
import re

from transformers import T5ForConditionalGeneration, T5Tokenizer

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level singleton — loaded once at import time to avoid cold-start
# overhead on every request.
# ---------------------------------------------------------------------------
_MODEL_NAME = "google/flan-t5-base"

_tokenizer = T5Tokenizer.from_pretrained(_MODEL_NAME)
_model = T5ForConditionalGeneration.from_pretrained(_MODEL_NAME)


class LLMService:
    """Wraps flan-t5-base for two tasks: input structuring and explanation generation."""

    def __init__(self) -> None:
        self._tokenizer = _tokenizer
        self._model = _model

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def structure_input(self, decision_text: str) -> dict:
        """Extract decision, options, and factors from free-form text.

        Returns a dict with keys ``decision``, ``options`` (≥2 items), and
        ``factors`` (≥1 item).  Never raises — falls back to a safe default
        dict on any parse failure.
        """
        prompt = (
            "Return ONLY valid JSON, no other text.\n"
            f"Extract from: '{decision_text}'\n"
            'Format: {"decision": "...", "options": ["...", "..."], "factors": ["..."]}'
        )

        raw_output = self._generate(prompt, max_new_tokens=200)

        try:
            match = re.search(r"\{.*\}", raw_output, re.DOTALL)
            if match is None:
                raise ValueError("No JSON object found in model output")

            structured = json.loads(match.group(0))

            assert "decision" in structured
            assert "options" in structured and len(structured["options"]) >= 2
            assert "factors" in structured and len(structured["factors"]) >= 1

            return structured

        except Exception:
            logger.warning(
                "LLM output unparseable, using fallback. Raw output: %r", raw_output
            )
            return {
                "decision": decision_text,
                "options": ["proceed", "do not proceed"],
                "factors": ["risk", "reward"],
            }

    def generate_explanation(
        self, structured: dict, best_option: str, results: list
    ) -> str:
        """Produce a plain-text explanation of why *best_option* is recommended.

        Only the top 2–3 scenarios from *results* are included in the prompt to
        keep it focused and reduce noise.
        """
        top_scenarios = results[:3]

        scenario_lines = "\n".join(
            f"- {r.get('scenario', r.get('name', 'scenario'))}: "
            f"salary={r.get('salary', 'N/A')}, "
            f"happiness={r.get('happiness', 'N/A')}, "
            f"risk={r.get('risk_score', 'N/A')}"
            for r in top_scenarios
        )

        prompt = (
            f"The best decision option is: {best_option}\n"
            f"Top scenarios:\n{scenario_lines}\n"
            "Explain in 2-3 sentences why this option is recommended."
        )

        return self._generate(prompt, max_new_tokens=150)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _generate(self, prompt: str, max_new_tokens: int = 200) -> str:
        """Tokenize *prompt*, run inference, and return decoded output string."""
        inputs = self._tokenizer(
            prompt, return_tensors="pt", truncation=True, max_length=512
        )
        output_ids = self._model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
        )
        return self._tokenizer.decode(output_ids[0], skip_special_tokens=True)
