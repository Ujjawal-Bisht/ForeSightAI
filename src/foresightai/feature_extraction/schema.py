from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


Sentiment = Literal[
    "positive",
    "negative",
    "neutral",
    "mixed",
    "unknown",
]


class AspectSignal(BaseModel):
    aspect: str
    sentiment: Sentiment


class ReviewFeatureExtraction(BaseModel):
    overall_sentiment: Sentiment
    aspects: list[AspectSignal]
    pain_points: list[str]
    preferences: list[str]
    feature_requests: list[str]
    behavioral_signals: list[str]