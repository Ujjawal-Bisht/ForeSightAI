from pathlib import Path

import environ
import yaml


BASE_DIR = Path(__file__).resolve().parents[3]

# --------------------------------------------------
# Environment variables
# --------------------------------------------------

env = environ.Env()
env.read_env(BASE_DIR / ".env")


# --------------------------------------------------
# YAML configuration
# --------------------------------------------------

CONFIG_PATH = BASE_DIR / "config" / "config.yaml"

with CONFIG_PATH.open("r", encoding="utf-8") as file:
    CONFIG = yaml.safe_load(file)


# --------------------------------------------------
# Ingestion configuration
# --------------------------------------------------

CHUNK_SIZE = 5000
MIN_REVIEW_ROWS = 10_000


# --------------------------------------------------
# LLM configuration
# --------------------------------------------------

LLM_CONFIG = CONFIG.get("llm", {})

LLM_PROVIDER = LLM_CONFIG.get("provider", "google")
LLM_MODEL = LLM_CONFIG.get("model", "gemini-3.8-flash")
LLM_THINKING_LEVEL = LLM_CONFIG.get("thinking_level", "low")
LLM_MAX_RETRIES = LLM_CONFIG.get("max_retries", 2)
LLM_TIMEOUT = LLM_CONFIG.get("timeout", 60)

FEATURE_EXTRACTION_CONFIG = LLM_CONFIG.get(
    "feature_extraction",
    {}
)

FEATURE_EXTRACTION_TEMPERATURE = FEATURE_EXTRACTION_CONFIG.get(
    "temperature"
)

FEATURE_EXTRACTION_MAX_OUTPUT_TOKENS = FEATURE_EXTRACTION_CONFIG.get(
    "max_output_tokens",
    2048,
)


# --------------------------------------------------
# API credentials
# --------------------------------------------------

GOOGLE_API_KEY = env("GEMINI_API_KEY", default=None)