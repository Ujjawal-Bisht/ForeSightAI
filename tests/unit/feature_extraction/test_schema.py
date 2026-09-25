"""
Unit tests for the ForeSightAI review feature-extraction schema.

Run:
pytest tests/unit/feature_extraction/test_schema.py -v
"""

import pytest
from pydantic import ValidationError

from foresightai.feature_extraction.schema import (
    AspectSignal,
    ReviewFeatureExtraction,
)


def valid_extraction_data() -> dict:
    """Return a valid feature-extraction payload for testing."""
    return {
        "overall_sentiment": "positive",
        "aspects": [
            {
                "aspect": "usability",
                "sentiment": "positive",
            }
        ],
        "pain_points": [
            "slow startup",
        ],
        "preferences": [
            "simple interface",
        ],
        "feature_requests": [
            "dark mode",
        ],
        "behavioral_signals": [
            "usability_focused",
        ],
    }


def test_valid_review_feature_extraction():
    """Valid extraction data should create a schema object."""
    data = valid_extraction_data()

    result = ReviewFeatureExtraction.model_validate(data)

    assert isinstance(result, ReviewFeatureExtraction)
    assert result.overall_sentiment == "positive"
    assert len(result.aspects) == 1
    assert result.aspects[0].aspect == "usability"


def test_missing_required_field_raises_validation_error():
    """Missing required fields should fail schema validation."""
    data = valid_extraction_data()
    data.pop("feature_requests")

    with pytest.raises(ValidationError):
        ReviewFeatureExtraction.model_validate(data)


def test_invalid_aspect_sentiment_raises_validation_error():
    """An invalid aspect sentiment should fail schema validation."""
    data = valid_extraction_data()
    data["aspects"][0]["sentiment"] = "very_positive"

    with pytest.raises(ValidationError):
        ReviewFeatureExtraction.model_validate(data)