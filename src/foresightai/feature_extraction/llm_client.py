from __future__ import annotations

from google import genai
from google.genai import types


class GeminiClient:
    """Client wrapper for the Google Gemini API."""

    def __init__(
        self,
        api_key: str,
        model: str,
        thinking_level: str = "low",
        max_output_tokens: int = 2048,
    ) -> None:

        if not api_key:
            raise ValueError("Google API key is required.")

        if not model:
            raise ValueError("Gemini model is required.")

        self.model = model
        self.thinking_level = thinking_level
        self.max_output_tokens = max_output_tokens

        self.client = genai.Client(api_key=api_key)

    def generate(self, prompt: str) -> str:
        """
        Send a prompt to Gemini and return the generated text.
        """

        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(
                    thinking_level=self.thinking_level
                ),
                max_output_tokens=self.max_output_tokens,
                response_mime_type="application/json",
            ),
        )

        if not response.text:
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        return response.text