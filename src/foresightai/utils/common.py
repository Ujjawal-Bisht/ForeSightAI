import json
import logging
from pathlib import Path
import pandas as pd
import yaml


SUPPORTED_FORMATS = {".csv", ".json", ".jsonl"}


def detect_format(path: str | Path) -> str:
    ext = Path(path).suffix.lower()
    if ext not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported file format '{ext}'. Supported: {SUPPORTED_FORMATS}"
        )
    return ext

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
        ))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def read_uploaded_data(path: str | Path) -> pd.DataFrame:
    """
    Reads a user-uploaded file in .csv, .json, or .jsonl format into a
    DataFrame. This is the single entry point the desktop app's upload
    handler should call — callers never need to know which format was
    actually uploaded.
    """
    path = Path(path)
    ext = detect_format(path)
    logger = get_logger(__name__)

    try:
        if ext == ".csv":
            df = pd.read_csv(path)
        elif ext == ".jsonl":
            df = pd.read_json(path, lines=True)
        elif ext == ".json":
            # Could be a JSON array of records, or one dict per line
            # without proper JSONL formatting - try the common case first.
            try:
                df = pd.read_json(path, lines=False)
            except ValueError:
                df = pd.read_json(path, lines=True)
    except Exception as e:
        raise ValueError(f"Failed to read '{path.name}' as {ext}: {e}") from e

    if df.empty:
        raise ValueError(f"'{path.name}' was read successfully but contains no rows.")

    logger.info(f"Loaded {len(df):,} rows from {path.name} ({ext})")
    return df


def save_dataframe(df: pd.DataFrame, path: str | Path, fmt: str | None = None):
    """
    Saves a DataFrame in .csv, .json, or .jsonl format. If fmt isn't given,
    it's inferred from the file extension in `path`.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fmt = fmt or detect_format(path)

    if fmt == ".csv":
        df.to_csv(path, index=False)
    elif fmt == ".jsonl":
        df.to_json(path, orient="records", lines=True)
    elif fmt == ".json":
        df.to_json(path, orient="records", indent=2)

    get_logger(__name__).info(f"Saved {len(df):,} rows to {path.name} ({fmt})")


def validate_required_columns(df: pd.DataFrame, required: list[str], filename: str = ""):
    """
    Checks that an uploaded file has the columns your pipeline actually
    needs (e.g. review text + rating), rather than failing confusingly
    three steps later in preprocessing.
    """
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(
            f"Uploaded file{' ' + filename if filename else ''} is missing "
            f"required column(s): {missing}. Found columns: {list(df.columns)}"
        )

def read_yaml(path: str | Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def save_json(data, path: str | Path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def load_json(path: str | Path):
    with open(path) as f:
        return json.load(f)


def create_directories(paths: list[str | Path]):
    for p in paths:
        Path(p).mkdir(parents=True, exist_ok=True)
