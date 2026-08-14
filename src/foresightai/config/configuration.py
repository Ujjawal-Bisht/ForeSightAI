from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parents[3]

env = environ.Env()
env.read_env(BASE_DIR / ".env")

CHUNK_SIZE = 5000
MIN_REVIEW_ROWS = 10_000