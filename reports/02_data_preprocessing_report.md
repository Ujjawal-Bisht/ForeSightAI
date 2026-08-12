# 02 — Data Preprocessing Report

**Notebook:** `notebooks/ingestion/02_data_preprocessing.ipynb`
**Input:** `data/raw/Software.jsonl`
**Corresponds to:** Methodology Stage 1 (Data Collection & Preprocessing)

## What We Checked

- Full-file schema and row count (chunked, no cleaning)
- Field-level validation logic: missing text, empty text, invalid ratings, language filtering
- Text normalization (HTML stripping via BeautifulSoup, whitespace collapsing)
- Duplicate detection, tested two ways: pandas in-memory `.duplicated()`, and a persistent SHA-256 hash store in PostgreSQL
- Data sufficiency against the project's 10,000-review minimum

## What We Found

### Schema and scale
- **4,880,181 total rows** in the Software category file — far more than needed; confirms sampling down is the right call, not a full-file pass
- **1 consistent key-set** across all rows — every record has the same 10 fields (`rating`, `title`, `text`, `images`, `asin`, `parent_asin`, `user_id`, `timestamp`, `helpful_vote`, `verified_purchase`). No schema drift to handle
- Correctly identified as review data (`text`, `rating` present), not the metadata file

### Field validation — working as designed
Tested against 4 explicit cases, all correct:
| Input | Result |
|---|---|
| Valid record | `valid: True` |
| `text: None` | `missing_text` |
| `text: "     "` (whitespace only) | `empty_text` |
| `rating: 7` (out of 1–5) | `invalid_rating` |

`validate_rating()` correctly rejects booleans, non-numeric values, and out-of-range numbers before they reach the pipeline.

### Duplicate detection — two methods, two very different results

**Method 1 — pandas `.duplicated()` on the real first 10,000 rows** (subset: asin, user_id, rating, normalized title, normalized text):
```
Before : 10,000
Removed: 2
After  : 9,998
```
This is a clean, trustworthy result — a genuinely low duplicate rate (0.02%), and it was validated first against an artificial test case (a manually duplicated row was correctly caught).

**Method 2 — PostgreSQL persistent hash store**, tested on the same 20-row sample and later on 10,000 fresh rows, reported:
```
duplicate_records: 20   (out of 20)
duplicate_records: 10,000   (out of 10,000)
```

**This second result should not be reported as a real duplicate rate, and here's why.** Tracing the execution order in the notebook (via the `execution_count` values, which reveal actual run order, not just cell position):

- The 20-row sample was run through `preprocess_chunk()` **multiple times in a row** without truncating the table between runs (visible directly — one cell is literally labeled "Second run" and shows the same 100% duplicate result). Every run after the first will show 100% duplicates by design, since the hashes are already stored.
- The hash function itself was independently verified correct: the same 20 records, hashed directly without touching the database, produced **20 unique hashes** — no collision bug.
- The insert/check logic was also verified correct in isolation (`insert_review_hash`, `is_duplicate_hash` both behaved exactly as expected against known test hashes).
- The 10,000-row test at the end almost certainly hit the same pattern — the table was truncated once, but the surrounding execution counts (jumping from 88 to 91, skipping two runs) suggest the insert cell was likely run more than once before the final displayed output.

**Conclusion: this is a test-workflow artifact from repeated interactive re-runs against a persistent table, not a defect in the deduplication logic.** All the individual pieces (hashing, insert, conflict detection) passed their unit-level checks. But as currently written, the notebook doesn't make this clear to a reader — someone skimming the output would reasonably conclude "100% of this dataset is duplicated," which is wrong and worth avoiding in anything that gets referenced later (report, viva, professor review).

**Recommendation:** treat the pandas-based result (2 duplicates in 10,000, i.e. ~0.02%) as the trustworthy figure for reporting. For the PostgreSQL path specifically, add a `TRUNCATE` at the start of any real pipeline run (not just during dev testing), and consider adding a one-line markdown note in the notebook itself clarifying that the 20/20 and 10,000/10,000 results reflect repeated test execution, not real data.

### Data sufficiency check — currently fails, and this matters for sampling strategy

```
Data sufficiency check FAILED: 9,998 valid reviews available, but 10,000 are required.
```

Taking exactly the first 10,000 raw rows and cleaning them yields only 9,998 after removing 2 duplicates — just short of the synopsis's stated minimum. This confirms something worth locking in now: **always pull more raw rows than the target** (e.g. 12,000–15,000) before cleaning, never sample to the exact minimum. This matches advice from earlier in this project but is now backed by an actual measured deficit rather than a general precaution.

### Language filtering — one setting worth a second look

`KEEP_UNDETECTABLE_LANGUAGE = False` combined with `MIN_REVIEW_TEXT_LENGTH = 3` creates some tension: very short reviews (several real samples were things like "WOW", "fun app", "Fun!!!!") pass the length filter but may fail language detection simply because `langdetect` can't confidently classify very short strings — and those get rejected outright rather than kept. This could quietly remove a meaningful share of genuinely-English short reviews. Worth checking the actual rejection-reason counts (`rejected_non_english_or_undetectable` in the stats dict) on a full run before deciding if this is acceptable or too aggressive.

### One unused constant
`MIN_REVIEW_TEXT_LENGTH = 3` is defined in the config cell but doesn't appear to be referenced anywhere in the validation logic (`validate_review_record` checks only for empty text, not a minimum length). Worth confirming whether this was meant to be wired in, or can be removed.

## Decisions This Informs

- **Sampling target:** pull 12,000–15,000 raw rows minimum, not exactly 10,000, to guarantee the post-cleaning minimum is met
- **Reported duplicate rate:** use the pandas-validated ~0.02% figure in the synopsis/report, not the PostgreSQL test numbers
- **Before any real pipeline run:** truncate `review_dedupe` first, and treat it as a stateful table that must be reset between independent runs, not between records within a run
- **Language filter:** worth a dedicated check of how many short-but-valid English reviews are being dropped before finalizing this setting

## Open Items
- Confirm whether `MIN_REVIEW_TEXT_LENGTH` should be wired into validation or removed
- Run the full pipeline once with a truncated table on a clean 12,000+ row sample and report those final, unambiguous numbers before moving to Stage 3 (persona generation)
