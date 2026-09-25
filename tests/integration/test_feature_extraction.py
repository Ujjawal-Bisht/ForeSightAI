"""
Integration test for the ForeSightAI feature-extraction pipeline.

This test verifies that the provider-agnostic LLM extractor,
JSON parsing, and Pydantic schema work together.

No external LLM API is called.

Run:
pytest tests/integration/test_feature_extraction.py -v
"""

import pytest

from foresightai.feature_extraction.llm_extractor import LLMExtractor


PROMPT_TEMPLATE = """
Extract customer features from this software review.

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
        },
        {
            "aspect": "performance",
            "sentiment": "negative"
        }
    ],
    "pain_points": [
        "slow startup"
    ],
    "preferences": [
        "simple interface"
    ],
    "feature_requests": [
        "faster startup"
    ],
    "behavioral_signals": [
        "usability_focused",
        "performance_sensitive"
    ]
}
"""


@pytest.mark.integration
def test_feature_extraction_pipeline():
    """
    Verify the complete feature-extraction pipeline using a fake LLM.
    """

    def fake_generate(prompt: str) -> str:
        # Verify that the extractor actually constructed the prompt.
        assert "Professional Software" in prompt
        assert "The software is easy to use" in prompt
        assert "4" in prompt

        return VALID_LLM_RESPONSE

    extractor = LLMExtractor(
        generate_fn=fake_generate,
        prompt_template=PROMPT_TEMPLATE,
        max_retries=2,
    )

    result = extractor.extract_review(
        review_text="The software is easy to use, but startup is slow.",
        title="Professional Software",
        rating=4,
    )

    # Schema-level validation through the complete pipeline.
    assert result.overall_sentiment == "positive"

    assert len(result.aspects) == 2
    assert result.aspects[0].aspect == "usability"
    assert result.aspects[1].aspect == "performance"

    assert result.pain_points == ["slow startup"]
    assert result.preferences == ["simple interface"]
    assert result.feature_requests == ["faster startup"]

    assert "usability_focused" in result.behavioral_signals
    assert "performance_sensitive" in result.behavioral_signals