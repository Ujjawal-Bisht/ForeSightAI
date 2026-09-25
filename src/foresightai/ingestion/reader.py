from pathlib import Path

import pandas as pd


def read_dataset_in_chunks(
    path: str | Path,
    chunk_size: int = 5_000,
):
    """
    Read a supported dataset incrementally in chunks.

    Supported formats:
        - JSONL
        - CSV

    Parameters
    ----------
    path:
        Path to the input dataset.

    chunk_size:
        Number of records to load into each chunk.

    Yields
    ------
    pandas.DataFrame
        One chunk of the dataset.
    """

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {path}"
        )

    if not isinstance(chunk_size, int) or chunk_size <= 0:
        raise ValueError(
            "chunk_size must be a positive integer."
        )

    suffix = path.suffix.lower()

    if suffix == ".jsonl":
        reader = pd.read_json(
            path,
            lines=True,
            chunksize=chunk_size,
        )

    elif suffix == ".csv":
        reader = pd.read_csv(
            path,
            chunksize=chunk_size,
        )

    else:
        raise ValueError(
            f"Unsupported dataset format: {suffix}"
        )

    for chunk in reader:
        yield chunk