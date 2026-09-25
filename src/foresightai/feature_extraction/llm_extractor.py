"""
LLM-based review feature extraction for ForeSightAI.

The module is intentionally provider-agnostic. The actual LLM provider/client
is injected into LLMExtractor so provider-specific SDK code does not get mixed
with feature-extraction logic.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from pydantic import ValidationError

from foresightai.feature_extraction.schema import ReviewFeatureExtraction


LLMGenerateFunction = Callable[[str], str]


def load_extraction_prompt(prompt_path: str | Path) -> str:
    """Load the review feature-extraction prompt from disk."""
    path = Path(prompt_path)

    if not path.exists():
        raise FileNotFoundError(f"Extraction prompt not found: {path}")

    return path.read_text(encoding="utf-8")


def build_extraction_prompt(
    template: str,
    review_text: str,
    title: str | None = None,
    rating: int | float | None = None,
) -> str:
    """Insert one review into the extraction prompt template."""

    if not template.strip():
        raise ValueError("Prompt template cannot be empty.")

    if not isinstance(review_text, str) or not review_text.strip():
        raise ValueError("review_text must be a non-empty string.")

    return template.format(
        title=title or "",
        rating="" if rating is None else rating,
        review_text=review_text,
    )


def _extract_json_object(raw_response: str) -> dict[str, Any]:
    """Parse a JSON object from a plain or fenced LLM response."""

    if not isinstance(raw_response, str) or not raw_response.strip():
        raise ValueError("LLM returned an empty response.")

    response = raw_response.strip()

    # Handle Markdown code fences such as:
    #
    # ```json
    # {...}
    # ```
    if response.startswith("```"):
        lines = response.splitlines()

        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        response = "\n".join(lines).strip()

        if response.lower().startswith("json"):
            response = response[4:].lstrip()

    try:
        parsed = json.loads(response)
    except json.JSONDecodeError as exc:
        raise ValueError("LLM response is not valid JSON.") from exc

    if not isinstance(parsed, dict):
        raise ValueError("LLM response must be a JSON object.")

    return parsed


class LLMExtractor:
    """Provider-agnostic extractor for one software-product review."""

    def __init__(
        self,
        generate_fn: LLMGenerateFunction,
        prompt_template: str,
        max_retries: int = 2,
    ) -> None:
        if not callable(generate_fn):
            raise TypeError("generate_fn must be callable.")

        if not prompt_template.strip():
            raise ValueError("prompt_template cannot be empty.")

        if max_retries < 0:
            raise ValueError("max_retries cannot be negative.")

        self.generate_fn = generate_fn
        self.prompt_template = prompt_template
        self.max_retries = max_retries

    def extract_review(
        self,
        review_text: str,
        title: str | None = None,
        rating: int | float | None = None,
    ) -> ReviewFeatureExtraction:
        """Extract and validate structured features from one review."""

        prompt = build_extraction_prompt(
            template=self.prompt_template,
            review_text=review_text,
            title=title,
            rating=rating,
        )

        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                raw_response = self.generate_fn(prompt)

                result = _extract_json_object(raw_response)

                return ReviewFeatureExtraction.model_validate(result)

            except (ValueError, TypeError, ValidationError) as exc:
                last_error = exc

                if attempt == self.max_retries:
                    break

        raise RuntimeError(
            f"Feature extraction failed after "
            f"{self.max_retries + 1} attempt(s)."
        ) from last_error


__all__ = [
    "LLMExtractor",
    "build_extraction_prompt",
    "load_extraction_prompt",
]