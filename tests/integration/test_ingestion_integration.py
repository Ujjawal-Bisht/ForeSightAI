"""End-to-end ingestion integration test.

This test validates the reusable ingestion implementation against the real
cleaned JSONL dataset using only the first 12,000 records.

Run with:
    pytest -m integration tests/test_ingestion_integration.py -v

Requirements:
    - PostgreSQL must be running.
    - The review_dedupe table must already exist.
    - Database credentials must be available through the project's .env.
"""

from pathlib import Path

import pytest

from foresightai.database.connection import get_postgres_connection
from foresightai.ingestion.preprocessing import preprocess_chunk
from foresightai.ingestion.reader import read_dataset_in_chunks


PROJECT_ROOT = Path(__file__).resolve().parents[2]

CLEAN_DATASET_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "software_clean.jsonl"
)

TEST_RECORDS = 12_000
CHUNK_SIZE = 5_000
TEXT_COLUMN = "text"
RATING_COLUMN = "rating"


@pytest.mark.integration
def test_12k_ingestion_pipeline():
    """Validate JSONL -> reader -> preprocessing -> PostgreSQL dedupe."""
    if not CLEAN_DATASET_PATH.exists():
        pytest.fail(f"Clean dataset not found: {CLEAN_DATASET_PATH}")

    connection = get_postgres_connection()

    total_input = 0
    total_valid = 0
    total_duplicates = 0
    total_clean = 0
    chunks_processed = 0

    try:
        # Start from a clean deduplication state.
        with connection.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE review_dedupe;")
        connection.commit()

        for chunk in read_dataset_in_chunks(
            CLEAN_DATASET_PATH,
            chunk_size=CHUNK_SIZE,
        ):
            remaining = TEST_RECORDS - total_input
            if remaining <= 0:
                break

            if len(chunk) > remaining:
                chunk = chunk.iloc[:remaining].copy()

            clean_chunk, stats = preprocess_chunk(
                chunk=chunk,
                text_column=TEXT_COLUMN,
                rating_column=RATING_COLUMN,
                connection=connection,
            )

            connection.commit()

            chunks_processed += 1
            total_input += len(chunk)
            total_valid += stats.get("valid_before_deduplication", 0)
            total_duplicates += stats.get("duplicate_records", 0)
            total_clean += stats.get("clean_records", 0)

            assert len(clean_chunk) == stats.get(
                "clean_records", len(clean_chunk)
            )

            if total_input >= TEST_RECORDS:
                break

        assert total_input == TEST_RECORDS
        assert total_clean <= total_valid <= total_input
        assert total_duplicates + total_clean == total_valid
        assert chunks_processed > 0

        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM review_dedupe;")
            stored_hashes = cursor.fetchone()[0]

        assert stored_hashes == total_clean

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
