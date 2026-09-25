"""
Unit tests for the provider-agnostic LLMExtractor.

These tests use a fake LLM function.
No Gemini API calls are made.

Run:
pytest tests/unit/feature_extraction/test_llm_extractor.py -v
"""

import pytest

from foresightai.feature_extraction.llm_extractor import (
    LLMExtractor,
    build_extraction_prompt,
    load_extraction_prompt,
)


PROMPT_TEMPLATE = """
Extract features from this software review.

Title: {title}
Rating: {rating}
Review:
{review_text}

Return JSON only.
"""


VALID_LLM_RESPONSE = """
{
    "overall_sentiment": "positive",
    "aspects": [
        {
            "aspect": "usability",
            "sentiment": "positive"
        }
    ],
    "pain_points": [
        "slow startup"
    ],
    "preferences": [
        "simple interface"
    ],
    "feature_requests": [
        "dark mode"
    ],
    "behavioral_signals": [
        "usability_focused"
    ]
}
"""


def test_build_extraction_prompt():
    """Review information should be inserted into the prompt template."""
    prompt = build_extraction_prompt(
        template=PROMPT_TEMPLATE,
        review_text="The application is easy to use.",
        title="Great application",
        rating=5,
    )

    assert "Great application" in prompt
    assert "5" in prompt
    assert "The application is easy to use." in prompt


def test_extractor_returns_validated_result():
    """A valid LLM response should produce a validated extraction object."""

    def fake_generate(prompt: str) -> str:
        assert "The application is easy to use." in prompt
        return VALID_LLM_RESPONSE

    extractor = LLMExtractor(
        generate_fn=fake_generate,
        prompt_template=PROMPT_TEMPLATE,
    )

    result = extractor.extract_review(
        review_text="The application is easy to use.",
        title="Great application",
        rating=5,
    )

    assert result.overall_sentiment == "positive"
    assert result.aspects[0].aspect == "usability"
    assert result.feature_requests == ["dark mode"]


def test_extractor_retries_after_invalid_response():
    """The extractor should retry when the LLM returns invalid JSON."""

    calls = 0

    def fake_generate(prompt: str) -> str:
        nonlocal calls

        calls += 1

        if calls == 1:
            return "This is not valid JSON."

        return VALID_LLM_RESPONSE

    extractor = LLMExtractor(
        generate_fn=fake_generate,
        prompt_template=PROMPT_TEMPLATE,
        max_retries=1,
    )

    result = extractor.extract_review(
        review_text="The application is easy to use.",
    )

    assert calls == 2
    assert result.overall_sentiment == "positive"