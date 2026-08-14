import hashlib
import html
import json
from collections import Counter
from bs4 import BeautifulSoup
import pandas as pd
import re
from langdetect import detect, LangDetectException
from foresightai.database.repositories.review_hash_repository import (
    is_duplicate_hash,
    insert_review_hash,
)

CHUNK_SIZE = 5000

MIN_REVIEW_ROWS = 10_000
MIN_REVIEW_TEXT_LENGTH = 3

REMOVE_HTML_TAGS = True
VALID_RATINGS = {1, 2, 3, 4, 5}
ALLOW_NUMERIC_STRING_RATINGS = True

LANGUAGE_FILTER_ENABLED = True
TARGET_LANGUAGE = "en"
KEEP_UNDETECTABLE_LANGUAGE = False

SUPPORTED_EXTENSIONS = {".json", ".jsonl", ".csv", ".xls", ".xlsx"}

HTML_TAG_PATTERN = re.compile(r"<[^>]+>")

def find_column(columns, candidates):
    lookup = {str(c).strip().lower(): c for c in columns}
    for candidate in candidates:
        if candidate in lookup:
            return lookup[candidate]
    return None

def iter_json_records(path):
    """Yield dictionaries from JSON or JSONL input."""
    if path.suffix.lower() == ".jsonl":
        with path.open("r", encoding="utf-8") as f:
            for line_number, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSONL at line {line_number}: {exc}") from exc
                if not isinstance(record, dict):
                    raise ValueError(f"JSONL line {line_number} is not an object/record.")
                yield record
        return

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        list_values = [v for v in data.values() if isinstance(v, list)]
        if len(list_values) == 1 and all(isinstance(x, dict) for x in list_values[0]):
            yield from list_values[0]
        else:
            yield data
    elif isinstance(data, list):
        for record in data:
            if not isinstance(record, dict):
                raise ValueError("JSON array contains a non-object item.")
            yield record
    else:
        raise ValueError("JSON root must be an object or an array of objects.")

def iter_tabular_records(path):
    """Yield dictionaries from CSV/Excel input."""
    if path.suffix.lower() == ".csv":
        for chunk in pd.read_csv(path, chunksize=CHUNK_SIZE):
            yield from chunk.to_dict(orient="records")
    elif path.suffix.lower() in {".xls", ".xlsx"}:
        frame = pd.read_excel(path)
        yield from frame.to_dict(orient="records")
    else:
        raise ValueError(f"Unsupported tabular format: {path.suffix}")


def iter_records(path):
    """Unified record iterator for JSON/CSV/Excel."""
    if path.suffix.lower() in {".json", ".jsonl"}:
        yield from iter_json_records(path)
    else:
        yield from iter_tabular_records(path)


def is_present(value):
    if isinstance(value, (list, dict)):
        return True
    try:
        return bool(pd.notna(value))
    except (TypeError, ValueError):
        return True

def inspect_schema(path, max_records=None):
    key_sets = Counter()
    all_columns = set()
    rows_seen = 0

    for record in iter_records(path):
        rows_seen += 1
        all_columns.update(record.keys())
        key_set = frozenset(k for k, v in record.items() if is_present(v))
        key_sets[key_set] += 1

        if max_records is not None and rows_seen >= max_records:
            break

    return rows_seen, all_columns, key_sets


def clean_html(text):
    """Remove HTML markup while retaining visible textual content."""
    text = html.unescape(str(text))
    if not REMOVE_HTML_TAGS:
        return text

    if BeautifulSoup is not None:
        return BeautifulSoup(text, "html.parser").get_text(" ")

    # Fallback for environments without BeautifulSoup.
    return re.sub(r"<[^>]*>", " ", text)

def normalize_whitespace(text):
    """Collapse repeated whitespace without changing meaningful wording."""
    return re.sub(r"\s+", " ", str(text)).strip()

def normalize_review_text(text):
    """
    Normalize review text while preserving meaningful content.

    Steps:
    1. Handle null/empty values.
    2. Remove HTML only when HTML tags are actually present.
    3. Normalize whitespace.
    """

    if text is None:
        return ""

    text = str(text)

    # --------------------------------------------------
    # Remove HTML only when HTML-like tags are present
    # --------------------------------------------------

    if HTML_TAG_PATTERN.search(text):
        text = BeautifulSoup(
            text,
            "html.parser"
        ).get_text(" ")

    # --------------------------------------------------
    # Normalize whitespace
    # --------------------------------------------------

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def validate_rating(value):
    """Return an integer rating in the accepted 1–5 range, otherwise None."""
    if value is None:
        return None

    if isinstance(value, bool):
        return None

    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None

    if numeric.is_integer() and int(numeric) in VALID_RATINGS:
        return int(numeric)

    return None

def detect_language(text):
    if not text or not LANGUAGE_FILTER_ENABLED:
        return TARGET_LANGUAGE

    if detect is None:
        raise ImportError(
            "langdetect is required when LANGUAGE_FILTER_ENABLED=True. "
            "Install it or disable language filtering explicitly."
        )

    try:
        return detect(text)
    except LangDetectException:
        return None

def language_is_acceptable(text):
    if not LANGUAGE_FILTER_ENABLED:
        return True, TARGET_LANGUAGE

    language = detect_language(text)
    if language is None:
        return KEEP_UNDETECTABLE_LANGUAGE, None

    return language == TARGET_LANGUAGE, language

def detect_file_format(path):
    extension = path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file format: {extension}. "
            f"Supported formats: {sorted(SUPPORTED_EXTENSIONS)}"
        )

    return extension[1:]  # Remove the leading dot from the extension


def validate_review_schema(
    all_columns,
    text_col,
    rating_col,
    review_like_fields,
    metadata_like_fields
):
    """
    Validate whether the dataset contains sufficient review-related fields.

    Parameters
    ----------
    all_columns : iterable
        Column names detected in the dataset.

    text_col : str or None
        Detected review-text column.

    rating_col : str or None
        Detected rating column.

    review_like_fields : set
        Known names/aliases for review-related fields.

    metadata_like_fields : set
        Known names/aliases for metadata-related fields.

    Returns
    -------
    dict
        Schema validation information.
    """

    # Normalize column names for comparison
    lower_columns = {
        str(column).lower().strip()
        for column in all_columns
    }

    review_hits = lower_columns & review_like_fields
    metadata_hits = lower_columns & metadata_like_fields

    # Basic review-data validation
    if text_col is None:
        raise ValueError(
            "No review-text column was found. "
            "The input may be metadata-only or use an unsupported schema."
        )

    if rating_col is None:
        raise ValueError(
            "No rating column was found. "
            "Confirm that the selected dataset contains review data and ratings."
        )

    return {
        "review_like_fields_found": sorted(review_hits),
        "metadata_like_fields_found": sorted(metadata_hits),
        "text_column": text_col,
        "rating_column": rating_col,
        "is_valid_review_dataset": True
    }


def normalize_for_duplicate(value):
    if pd.isna(value):
        return ""

    value = str(value)

    # Normalize whitespace
    value = re.sub(r"\s+", " ", value)

    # Remove leading/trailing whitespace
    return value.strip()

MIN_REVIEW_COUNT = 10_000

def validate_data_sufficiency(
    valid_review_count,
    minimum_reviews=MIN_REVIEW_COUNT
):
    """
    Check whether the dataset contains enough valid reviews
    for the downstream persona-generation pipeline.

    Parameters
    ----------
    valid_review_count : int
        Number of reviews remaining after preprocessing.

    minimum_reviews : int, optional
        Minimum number of valid reviews required.

    Returns
    -------
    dict
        Data sufficiency result.
    """

    valid_review_count = int(valid_review_count)
    minimum_reviews = int(minimum_reviews)

    is_sufficient = valid_review_count >= minimum_reviews

    result = {
        "valid_review_count": valid_review_count,
        "minimum_required": minimum_reviews,
        "is_sufficient": is_sufficient,
        "deficit": max(0, minimum_reviews - valid_review_count)
    }

    if is_sufficient:
        print(
            f"Data sufficiency check PASSED: "
            f"{valid_review_count:,} valid reviews available "
            f"(minimum required: {minimum_reviews:,})."
        )
    else:
        print(
            f"Data sufficiency check FAILED: "
            f"{valid_review_count:,} valid reviews available, "
            f"but {minimum_reviews:,} are required."
        )

    return result

def validate_review_record(
    record,
    text_col="text",
    rating_col="rating"
):
    """
    Validate a single review record.

    Returns
    -------
    dict
        Validation result containing:
        - valid
        - reason
        - normalized_text
        - normalized_rating
        - detected_language
    """

    # --------------------------------------------------
    # 1. Validate and normalize review text
    # --------------------------------------------------

    raw_text = record.get(text_col)

    normalized_text = normalize_review_text(raw_text)

    if len(normalized_text) < MIN_REVIEW_TEXT_LENGTH:
        return {
            "valid": False,
            "reason": "empty_or_too_short",
            "normalized_text": normalized_text,
            "normalized_rating": None,
            "detected_language": None,
        }

    # --------------------------------------------------
    # 2. Validate rating
    # --------------------------------------------------

    normalized_rating = validate_rating(
        record.get(rating_col)
    )

    if normalized_rating is None:
        return {
            "valid": False,
            "reason": "invalid_rating",
            "normalized_text": normalized_text,
            "normalized_rating": None,
            "detected_language": None,
        }

    # --------------------------------------------------
    # 3. Validate language
    # --------------------------------------------------

    language_accepted, detected_language = (
        language_is_acceptable(normalized_text)
    )

    if not language_accepted:
        return {
            "valid": False,
            "reason": (
                "undetectable_language"
                if detected_language is None
                else "non_english"
            ),
            "normalized_text": normalized_text,
            "normalized_rating": normalized_rating,
            "detected_language": detected_language,
        }

    # --------------------------------------------------
    # 4. Record is valid
    # --------------------------------------------------

    return {
        "valid": True,
        "reason": None,
        "normalized_text": normalized_text,
        "normalized_rating": normalized_rating,
        "detected_language": detected_language,
    }


def generate_review_hash(
    record,
    asin_col="asin",
    user_id_col="user_id",
    rating_col="rating",
    title_col="title_normalized",
    text_col="text_normalized"
):
    """
    Generate a deterministic SHA-256 hash for a cleaned review.

    The hash is based on the review identity and normalized content.

    Parameters
    ----------
    record : dict
        Cleaned review record.

    asin_col : str
        Product identifier column.

    user_id_col : str
        Customer identifier column.

    rating_col : str
        Review rating column.

    title_col : str
        Normalized review title column.

    text_col : str
        Normalized review text column.

    Returns
    -------
    str
        SHA-256 hexadecimal hash.
    """

    # Extract values
    asin = record.get(asin_col, "")
    user_id = record.get(user_id_col, "")
    rating = record.get(rating_col, "")
    title = record.get(title_col, "")
    text = record.get(text_col, "")

    # Convert values to strings and normalize whitespace
    asin = str(asin).strip()
    user_id = str(user_id).strip()
    rating = str(rating).strip()
    title = " ".join(str(title).split())
    text = " ".join(str(text).split())

    # Create a deterministic canonical representation
    canonical_record = (
        f"asin={asin}|"
        f"user_id={user_id}|"
        f"rating={rating}|"
        f"title={title}|"
        f"text={text}"
    )

    # Generate SHA-256 hash
    review_hash = hashlib.sha256(
        canonical_record.encode("utf-8")
    ).hexdigest()

    return review_hash


def is_duplicate_postgres(connection, review_hash, table_name="review_dedupe", column="review_hash"):
    """
    Check whether a review_hash already exists in a Postgres table.

    This is a best-effort helper that works with common DB APIs (psycopg2/psycopg).
    It returns False on any error (to avoid failing the entire preprocessing pipeline).
    """
    if connection is None or not review_hash:
        return False

    try:
        cur = connection.cursor()
        try:
            cur.execute(
                f"SELECT 1 FROM {table_name} WHERE {column} = %s LIMIT 1",
                (review_hash,)
            )
            return cur.fetchone() is not None
        finally:
            try:
                cur.close()
            except Exception:
                pass
    except Exception:
        # On any DB error, treat as non-duplicate to avoid blocking ingestion.
        return False

def preprocess_record(
    record,
    text_col="text",
    rating_col="rating",
    title_col="title",
    asin_col="asin",
    user_id_col="user_id"
):
    """
    Preprocess a single raw review record.

    Steps:
        1. Validate review text
        2. Normalize review text
        3. Validate rating
        4. Validate language
        5. Normalize title
        6. Generate duplicate hash

    Returns
    -------
    tuple
        (clean_record, None) if valid
        (None, rejection_reason) if invalid
    """

    # --------------------------------------------------
    # 1. Validate the review record
    # --------------------------------------------------

    validation = validate_review_record(
        record=record,
        text_col=text_col,
        rating_col=rating_col
    )

    if not validation["valid"]:
        return None, validation["reason"]

    # --------------------------------------------------
    # 2. Create a copy so the original record
    #    is never modified
    # --------------------------------------------------

    clean_record = record.copy()

    # --------------------------------------------------
    # 3. Store normalized text and rating
    # --------------------------------------------------

    clean_record["text_normalized"] = validation["normalized_text"]

    clean_record[rating_col] = validation["normalized_rating"]

    # --------------------------------------------------
    # 4. Normalize title
    # --------------------------------------------------

    clean_record["title_normalized"] = normalize_review_text(
        record.get(title_col)
    )

    # --------------------------------------------------
    # 5. Generate deterministic duplicate hash
    # --------------------------------------------------

    clean_record["review_hash"] = generate_review_hash(
        clean_record,
        asin_col=asin_col,
        user_id_col=user_id_col,
        rating_col=rating_col,
        title_col="title_normalized",
        text_col="text_normalized"
    )

    return clean_record, None

def preprocess_chunk(
    chunk,
    text_column,
    rating_column,
    connection,
):
    stats = Counter()
    clean_records = []
    valid_before_dedup = 0

    for record_idx, record in enumerate(chunk.to_dict(orient="records")):

        clean_record, rejection_reason = preprocess_record(
            record=record,
            text_col=text_column,
            rating_col=rating_column,
        )

        if clean_record is None:
            stats[rejection_reason] += 1
            continue

        valid_before_dedup += 1

        # Use savepoint to isolate database operations
        savepoint_name = f"sp_{record_idx}"
        
        try:
            # Create savepoint
            with connection.cursor() as cur:
                cur.execute(f"SAVEPOINT {savepoint_name}")
            
            if is_duplicate_postgres(
                connection=connection,
                review_hash=clean_record["review_hash"]
            ):
                stats["duplicate_records"] += 1
                # Release savepoint on success
                with connection.cursor() as cur:
                    cur.execute(f"RELEASE {savepoint_name}")
                continue

            insert_review_hash(
                review_hash=clean_record["review_hash"],
                connection=connection
            )

            clean_records.append(clean_record)
            # Release savepoint on success
            with connection.cursor() as cur:
                cur.execute(f"RELEASE {savepoint_name}")
        
        except Exception as e:
            # Rollback to savepoint on error
            try:
                with connection.cursor() as cur:
                    cur.execute(f"ROLLBACK TO {savepoint_name}")
            except Exception:
                pass
            print(f"[DEBUG] Error at record {record_idx}: {type(e).__name__}: {e}")
            stats["database_errors"] += 1
            continue

    stats["input_records"] = len(chunk)
    stats["valid_before_deduplication"] = valid_before_dedup
    stats["clean_records"] = len(clean_records)

    if clean_records:
        clean_chunk = pd.DataFrame(clean_records)
    else:
        clean_chunk = pd.DataFrame()

    return clean_chunk, stats