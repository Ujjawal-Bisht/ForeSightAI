from pathlib import Path

import pandas as pd
import pytest

from foresightai.ingestion.reader import read_dataset_in_chunks


def create_jsonl_file(path: Path, records: list[dict]) -> None:
    """Create a small JSONL file for reader tests."""
    pd.DataFrame(records).to_json(
        path,
        orient="records",
        lines=True,
        force_ascii=False,
    )


def test_read_dataset_in_chunks_returns_expected_number_of_chunks(tmp_path):
    """The reader should split a JSONL dataset into the requested chunk size."""
    input_path = tmp_path / "sample.jsonl"
    records = [
        {"id": index, "text": f"review {index}", "rating": 5}
        for index in range(10)
    ]
    create_jsonl_file(input_path, records)

    chunks = list(read_dataset_in_chunks(input_path, chunk_size=4))

    assert len(chunks) == 3
    assert [len(chunk) for chunk in chunks] == [4, 4, 2]


def test_read_dataset_in_chunks_preserves_record_count(tmp_path):
    """The reader must not lose or duplicate records."""
    input_path = tmp_path / "sample.jsonl"
    records = [
        {"id": index, "text": f"review {index}", "rating": index % 5 + 1}
        for index in range(17)
    ]
    create_jsonl_file(input_path, records)

    chunks = list(read_dataset_in_chunks(input_path, chunk_size=5))
    combined = pd.concat(chunks, ignore_index=True)

    assert len(combined) == 17
    assert combined["id"].tolist() == list(range(17))


def test_read_dataset_in_chunks_preserves_columns(tmp_path):
    """The reader should preserve the dataset columns."""
    input_path = tmp_path / "sample.jsonl"
    records = [
        {
            "asin": "A001",
            "user_id": "U001",
            "rating": 5,
            "title": "Good",
            "text": "Very useful software.",
        },
        {
            "asin": "A002",
            "user_id": "U002",
            "rating": 2,
            "title": "Poor",
            "text": "Difficult to use.",
        },
    ]
    create_jsonl_file(input_path, records)

    chunk = next(read_dataset_in_chunks(input_path, chunk_size=10))

    assert set(chunk.columns) == {
        "asin",
        "user_id",
        "rating",
        "title",
        "text",
    }


def test_read_dataset_in_chunks_rejects_invalid_chunk_size(tmp_path):
    """Invalid chunk sizes should fail clearly."""
    input_path = tmp_path / "sample.jsonl"
    create_jsonl_file(
        input_path,
        [{"id": 1, "text": "test", "rating": 5}],
    )

    with pytest.raises((ValueError, TypeError)):
        list(read_dataset_in_chunks(input_path, chunk_size=0))


def test_read_dataset_in_chunks_missing_file_raises_error(tmp_path):
    """A missing input file should raise an appropriate error."""
    missing_path = tmp_path / "missing.jsonl"

    with pytest.raises((FileNotFoundError, ValueError)):
        list(read_dataset_in_chunks(missing_path, chunk_size=5))
