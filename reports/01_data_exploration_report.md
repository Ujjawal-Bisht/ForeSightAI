# Data Exploration Report --- `01_data_exploration.ipynb`

## 1. Overview

This report documents the findings from the `01_data_exploration.ipynb`
notebook used in the ForeSightAI project.

The notebook is designed to inspect the raw Amazon Reviews 2023 Software
dataset **before implementing any cleaning or preprocessing logic**. It
is read-only: it does not remove, modify, normalize, or filter records.
Instead, it examines the dataset structure and data-quality
characteristics that will later inform `dedupe()`, `filter_valid()`, and
`normalize()` in `preprocessing.py`.

Because the raw dataset is large, the notebook reads it in chunks rather
than loading the complete file into memory.

## 2. Dataset Examined

-   **File:** `../../data/raw/Software.jsonl`
-   **Format:** JSON Lines (`.jsonl`)
-   **Product category:** Software
-   **Total raw records:** **4,880,181**
-   **Chunk size in the executed exploration:** 5,000 records
-   **Chunks processed:** 977
-   **Python version:** 3.12.4

The dataset is substantially larger than the project's minimum
10,000-review requirement, so sufficient raw data is available for the
study.

The chunked-reading approach is appropriate for this dataset because the
complete 4.88-million-record file does not need to be loaded into memory
at once.

# 3. Step-by-Step Findings

## Step 1 --- Row Count and Schema

### Objective

The first step determines:

1.  The total number of records.
2.  The columns present in the dataset.
3.  Whether individual records have a consistent set of fields.

The JSONL file is read chunk by chunk. The notebook accumulates the row
count and discovered columns and also examines the keys present in each
individual JSON record.

### Findings

-   **Total records:** 4,880,181
-   **Chunks processed:** 977
-   **Chunk size:** 5,000 records
-   **Distinct key-sets:** 1

A **key-set** is the set of fields that are present in an individual
record. One distinct key-set means that the records were structurally
consistent according to the notebook's presence check.

### Interpretation

This is a positive result. The dataset does not appear to contain
multiple substantially different record structures that would require
separate preprocessing logic.

------------------------------------------------------------------------

## Step 2 --- Review Data vs. Metadata Check

### Objective

This step checks whether the downloaded file resembles a customer-review
dataset rather than a product metadata file.

The notebook compares discovered column names against review-like fields
such as `text`, `rating`, `reviewtext`, and `user_id`, as well as
metadata-like fields such as `title`, `brand`, `price`, and `main_cat`.

### Findings

The exploration identified:

-   **Rating column:** `rating`
-   **Review text column:** `text`

The final summary did not trigger the warning that the file was metadata
rather than review data.

### Conclusion

The selected file is appropriate for the intended customer-review
analysis pipeline.

------------------------------------------------------------------------

## Step 3 --- Most Common Key-Sets

### Objective

This step provides more detail if Step 1 finds more than one record
structure. It can identify fields that are present in some records but
absent in others.

### Finding

Step 1 found:

> **Distinct key-sets: 1**

Therefore, no record-level schema variation was identified.

### Conclusion

No additional schema-specific handling is currently required.

------------------------------------------------------------------------

## Step 4 --- Sample Records

### Objective

This step inspects actual review records to understand their raw
structure and content.

The notebook reads only a small number of chunks and then selects a
reproducible random sample using seed `42`. This prevents the entire
4.88-million-record dataset from being materialized merely for visual
inspection.

### Finding

The sample confirmed the presence of the expected review content and
also provided examples used later to investigate HTML markup.

### Important interpretation

This sample is **only for exploration**. It does not define the amount
of data that will be used by the final persona-generation pipeline. The
later preprocessing stage can process the complete selected dataset in
chunks.

------------------------------------------------------------------------

## Step 5 --- Rating Distribution

### Objective

This step examines the distribution of customer ratings across the
dataset.

The notebook first searches common candidate names and identifies the
actual rating field before counting ratings chunk by chunk.

### Finding

> **Rating column: `rating`**

The rating distribution was accumulated across the raw dataset rather
than estimated from the small exploratory sample.

The exact frequency output is not preserved in the uploaded notebook's
execution metadata, so this report does not invent numerical rating
frequencies.

### Why this matters

The rating distribution will later help with:

-   Understanding the balance of customer opinions.
-   Detecting possible class imbalance.
-   Designing the research-data sampling strategy.
-   Checking whether the processed dataset remains representative.

------------------------------------------------------------------------

## Step 6 --- Missing / Null / Empty Review Text

### Objective

This step determines whether records lack usable review text.

The notebook separately counts null values and empty or whitespace-only
strings.

### Findings

-   **Text column:** `text`
-   **Null values:** 0
-   **Null/empty text in the Step 8 full scan:** 324 records
-   **Approximate proportion:** 0.0066% of all 4,880,181 records

The displayed `0.0%` is only a formatting effect because the percentage
was displayed with one decimal place.

### Interpretation

Missing or empty review text is extremely uncommon.

The 324 unusable records should nevertheless be removed during
preprocessing because they cannot provide meaningful input to the LLM
feature-extraction stage.

### Notebook-state note

An earlier interactive run produced 648 empty strings. This was caused
by an accumulator being reused without being reset before another scan.
The later Step 8 result is 324. For reproducibility, counters such as
`null_text_count` and `empty_text_count` should be initialized in the
same cell that performs the scan.

------------------------------------------------------------------------

## Step 7 --- Rough Non-English and Malformed-Content Estimate

### Objective

This step estimates the presence of non-English reviews and HTML-like
markup.

It intentionally uses a sample rather than the full dataset because
language detection across millions of reviews would be unnecessarily
expensive during exploratory analysis.

The sample size was increased from 200 to **1,000 reviews** to obtain a
more stable exploratory estimate.

### Final exploratory result

  Metric                                   Result
  ----------------------------------- -----------
  Sample size                               1,000
  Estimated non-English                       110
  Estimated non-English proportion      **11.0%**
  Undetectable / ambiguous                      1
  Undetectable proportion                **0.1%**
  Records containing HTML-like tags            97
  HTML-tag proportion                    **9.7%**

### Non-English reviews

The sample contained **110 non-English reviews out of 1,000 (11.0%)**.

This is a substantial enough proportion to justify an explicit
language-filtering rule for the current English-language project scope.

However, 11.0% is a **sample estimate**, not an exact percentage for the
entire 4.88-million-record dataset.

### Undetectable reviews

Only 1 sampled review (0.1%) could not be confidently classified by the
language detector.

The preprocessing pipeline should still define how such records are
handled.

### HTML-containing reviews

The sample contained 97 records (9.7%) with HTML-like tags. Inspection
of the examples showed actual markup such as:

``` html
<br />
```

and repeated line-break tags.

These tags are formatting artifacts rather than useful customer
information.

### Preprocessing implication

HTML-containing reviews should **not** be discarded simply because they
contain markup. Instead, the tags should be removed while preserving the
underlying customer text.

For example:

``` text
"This product works well.<br /><br />The installation was easy."
```

should become approximately:

``` text
"This product works well. The installation was easy."
```

------------------------------------------------------------------------

## Step 8 --- Exploration Summary

The final summary combines the main findings and checks whether the file
contains the fields required for review analysis.

### Final confirmed results

  Property                                                   Finding
  -------------------------------------------- ---------------------
  Raw records                                          **4,880,181**
  Chunks processed                                   **977 × 5,000**
  Distinct key-sets                                            **1**
  Rating column                                         **`rating`**
  Review text column                                      **`text`**
  Null/empty text                                    **324 records**
  Sampled reviews for language/HTML analysis               **1,000**
  Estimated non-English                          **11.0%** of sample
  Undetectable                                    **0.1%** of sample
  HTML-containing                                 **9.7%** of sample

The summary did not identify the file as an incorrect metadata file.

# 4. Overall Data-Quality Assessment

  Area                                          Finding Assessment
  ---------------------------- ------------------------ -----------------------------
  Dataset size                        4,880,181 records Sufficient
  Chunked reading                            977 chunks Appropriate
  Schema consistency                 1 distinct key-set Good
  Review identification          Review fields detected Suitable
  Rating field                                 `rating` Confirmed
  Review text field                              `text` Confirmed
  Null text                                           0 Very good
  Empty text                                        324 Very small proportion
  Non-English estimate                  11.0% of sample Requires filtering decision
  Language detection failure             0.1% of sample Low
  HTML estimate                          9.7% of sample Requires normalization

# 5. Preprocessing Requirements Derived from the Exploration

The exploration provides evidence for the following preliminary
preprocessing rules.

### 1. Duplicate removal

Duplicate reviews should be identified and removed so that repeated
records do not disproportionately influence customer representations.

### 2. Missing/empty text removal

Records with null or empty review text should be removed because they
cannot provide meaningful input to the LLM feature-extraction stage.

### 3. English-language filtering

Non-English reviews should be filtered according to the project's
current English-language scope.

The 11.0% figure is an exploratory estimate only; the actual
preprocessing pipeline will apply the language rule to the selected
research dataset.

### 4. HTML removal

HTML tags such as `<br />` should be removed while retaining the
underlying review text.

### 5. Whitespace normalization

Excessive or formatting-related whitespace should be normalized after
HTML removal.

### 6. Rating validation

The `rating` field should be checked for invalid or unexpected values
before downstream processing.

### 7. Preserve meaningful language

Aggressive operations such as stop-word removal, stemming, or
indiscriminate punctuation removal should not be introduced without a
research justification. The project is modeling customer opinions, so
potentially meaningful emotional and contextual information should be
retained.

# 6. Raw Dataset vs. Research Dataset

The raw file contains approximately **4.88 million reviews**, while the
project synopsis specifies a minimum of **10,000 reviews** for the
selected product category.

These are different concepts:

-   **Available raw data:** 4,880,181 reviews.
-   **Cleaned data:** records remaining after preprocessing.
-   **Research dataset:** the reproducibly selected subset used for LLM
    feature extraction, embeddings, clustering, and persona generation.

The project does not need to send all 4.88 million reviews through the
LLM API simply because they are available. The final research sample
size should be selected deliberately based on statistical coverage,
computational resources, API cost, and the requirements of the
persona-count validation experiment.

# 7. Conclusion

The `01_data_exploration.ipynb` notebook successfully established the
basic structure and quality characteristics of the raw Software review
dataset without modifying the source data.

The dataset contains **4,880,181 reviews** and shows a **consistent
record structure with one distinct key-set**. The required review fields
were identified as `text` and `rating`. Missing review text is extremely
uncommon, with 324 null/empty records identified in the full scan. A
1,000-review exploratory sample estimated that **11.0%** of reviews are
non-English and **9.7%** contain HTML-like markup, while **0.1%** could
not be classified by the language detector.

These findings provide sufficient evidence to move from exploration to
preprocessing.

The next stage should implement chunk-based preprocessing that:

1.  Removes duplicates.
2.  Removes null/empty review text.
3.  Applies the English-language filtering rule.
4.  Removes HTML markup while preserving review content.
5.  Normalizes whitespace.
6.  Validates ratings.
7.  Produces a clean dataset for LLM-based feature extraction.

The exploration notebook should remain read-only. Actual transformations
should be implemented separately in:

``` text
src/foresightai/ingestion/preprocessing.py
```

# 8. Exploration-to-Preprocessing Transition

``` text
RAW SOFTWARE REVIEWS
        │
        │  4,880,181 records
        ▼
┌─────────────────────────────┐
│ 01 — DATA EXPLORATION       │
│                             │
│ ✓ Schema                    │
│ ✓ Row count                 │
│ ✓ Sample records            │
│ ✓ Rating field              │
│ ✓ Text field                │
│ ✓ Missing text              │
│ ✓ Language estimate         │
│ ✓ HTML estimate             │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│ 02 — PREPROCESSING          │
│                             │
│ • Deduplication             │
│ • Empty-text removal        │
│ • Language filtering        │
│ • HTML removal              │
│ • Whitespace normalization  │
│ • Rating validation         │
└──────────────┬──────────────┘
               │
               ▼
        CLEAN DATASET
               │
               ▼
       FEATURE EXTRACTION
               │
               ▼
       PERSONA GENERATION
```

## Status

**Exploration phase:** Completed

**Next phase:** Data preprocessing

**Primary implementation file:**
`src/foresightai/ingestion/preprocessing.py`

