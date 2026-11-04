# Catalog Cleaning Workstream

Source: `cleaning/raw.csv` — full DynamoDB export, 167,018 rows.

Each pass is documented here with its script, rules, and results.
The final clean CSV becomes the source of truth for re-ingestion.

---

## Catalog Snapshot (at export)

### Collections Ingested

| Collection | Status |
|---|---|
| feature_films | ✅ Done |
| short_films | ✅ Done |
| silent_films | ✅ Done |
| horror_and_suspense | ✅ Done |
| animationandcartoons | ✅ Done |
| westerns | ✅ Done |
| educational_films | ✅ Done |
| classic_tv | ✅ Done |
| film_noir | ✅ Done |
| serials | ✅ Done |
| live_concerts | ✅ Done |
| newsandpublicaffairs | ⛔ Skipped — replaced with live_concerts |

**Total raw rows: 167,018**

### Known Data Quality Issues (pre-cleaning)

| Field | Issue |
|---|---|
| `duration_sec` | ~98% missing — IA `runtime` field rarely populated |
| `year` | Malformed values present — e.g. `"201"` instead of `"2015"` |
| `genre` | Large `other` bucket — items that didn't match any subject tag in `_GENRE_MAP` |
| `language` | Not populated at ingestion — detection needed |

---

## Passes

### Pass 1 — Duration Backfill

**Script:** `cleaning/scripts/backfill_duration.py`
**Input:** Live DynamoDB (items where `duration_sec` is null)
**Output:** DynamoDB updated in place + `backfill_duration_progress.json` checkpoint

Two-pass approach:
- **Pass 1a** — IA metadata API: `https://archive.org/metadata/{identifier}/files` — looks for video file with a `length` field. Fast (~0.3s/item).
- **Pass 1b** — ffprobe fallback on `stream_url` for anything still missing. Slower, requires `ffmpeg`.

Resumable — checkpoints every 100 items.

**Results:** ✅ Complete

| | Count |
|---|---|
| Total items scanned | 88,325 |
| Filled via IA metadata API | 88,151 |
| Still missing after both passes | 174 |
| Coverage | 99.8% |

174 remaining have no duration available anywhere — likely truly undocumented uploads.

---

### Pass 2 — Junk Removal

**Script:** `cleaning/scripts/junk_removal.py`
**Rule:** Flag items below duration threshold.
- `type = short` → exclude if `duration_sec < 180`
- `type = cartoon` → exclude if `duration_sec < 300`
- everything else → exclude if `duration_sec < 600`

**Results:** ✅ Complete

| | Count |
|---|---|
| Total rows | 167,018 |
| Flagged | 115,531 |
| Surviving | 51,487 |

---

### Pass 3 — Year Filter & Cleanup

**Script:** `cleaning/scripts/reset_and_filter.py`

Reset all flags, then apply single rule: exclude `year >= 1990`. Year extracted from title via regex where `year` field was empty.

**Results:** ✅ Complete

| | Count |
|---|---|
| Flagged (year >= 1990) | 119,189 |
| Surviving | 47,829 |
| Years extracted from titles | 1,069 |

Year cutoff rationale: everything after 1990 is modern uploads, news streams, user content. Pre-1990 = legitimate classic content.

---

### Pass 3b — Trailer Flag

**Script:** `cleaning/scripts/flag_title_keywords.py`

Flagged rows with junk keywords in title (currently: `trailer`).

**Results:** ✅ Complete — 1,344 flagged, 46,485 surviving.

---

### Pass 4 — Genre & Type Remap

**Script:** `cleaning/scripts/remap_genres.py`

#### Remap Rules Applied

**Collection-based:**
- `westerns` → `genre: western`
- `film_noir` → `genre: crime`
- `horror_and_suspense` → `genre: horror`
- `animationandcartoons` → `genre: animation`

**Type-based:**
- `concert` type → `genre: musical`
- `newsreel` type → `genre: documentary`
- `educational` type → `genre: educational`
- `serial` type → `genre: action`

**Language detection:**
- Non-Latin characters in title (Turkish `ş ğ ı ç ö ü`, etc.) → `language: foreign`
- Known foreign keywords (`Deutsche`, `Wochenschau`, `VOSE`, etc.) → `language: foreign`
- Everything else → `language: en`

**Results:** ✅ Complete — 23,089 remapped total.

---

### Pass 4b — Title Keyword Remap

**Script:** `cleaning/scripts/remap_title_keywords.py`

Scanned remaining `other` genre rows for genre keywords in title. 13 keyword lists ordered by specificity — horror, sci-fi, western, crime, comedy, musical, documentary, romance, drama, action.

**Results:** ✅ Complete — 1,471 remapped, 9,107 still `other`.

---

### Pass 5 — Other Bucket Cleanup

**Script:** `cleaning/scripts/pass5_other_cleanup.py`

Three sub-passes targeting the remaining 9,107 `other` rows and broader catalog quality.

#### Pass 5a — Numeric Title Flag
Flag rows where the entire title is numbers/punctuation only.
- **Result:** 0 flagged (already cleaned by prior passes)

#### Pass 5b — Near-Duplicate Dedup

> **Note on how we got here:** This took several attempts to get right.
>
> - **Attempt 1** — `SequenceMatcher` fuzzy scoring (threshold 0.85) on sorted neighbors. Flagged 9,975 — way too aggressive. "Carnival of Souls", "His Girl Friday", "Earthworm Tractors" all incorrectly flagged as dupes.
> - **Attempt 2** — Bucketed by first word, fuzzy scoring within bucket + 4-char prefix early break. Still flagged 12,182 — "Rocky Horror Picture Show", "Dracula", "House on Haunted Hill" all caught in false positives.
> - **Attempt 3** — Exact norm-key match after stripping trailing noise tokens (year, resolution, format). Flagged 6,089 — still wrong. Same classics appearing in sample.
> - **Attempt 4 (final)** — First 3 words exact match as bucket key, then **prefix-substring check**: only flag as duplicate if one norm title is a word-boundary prefix of the other. This matches the actual duplicate pattern in the catalog — same title with year/metadata appended at the end. Articles (`the`, `a`, `an`) skipped before taking first 3 words to avoid massive false-positive buckets.

**Final rule:** bucket by first 3 words (article-skipped) → within bucket, flag as dupe only if `longer_title.startswith(shorter_title)` at a word boundary. Keep longest duration, flag the rest.

**Result:** 4,414 flagged ✅

Sample of correctly caught dupes:
- `"The Little Shop of Horrors (1960)"` (4353s) kept over `"The Little Shop of Horrors (1960)"` (4289s)
- `"House on Haunted Hill"` kept over `"House On Haunted Hill 1959"`
- `"1933 - Adolf Hitler - Regierungserklaerung..."` variants — year/metadata suffix pattern

#### Pass 5c — Year Backfill from Title
For surviving rows still missing `year`, extract via regex from title.
- **Result:** 86 years backfilled.

**Pass 5 totals:**

| | Count |
|---|---|
| Near-duplicates flagged | 4,414 |
| Years backfilled | 86 |
| Surviving after Pass 5 | 34,962 |

---

## Current State

**Surviving rows: 34,962**

| Genre | Count | % |
|---|---|---|
| horror | 8,495 | 24.3% |
| other | 7,293 | 20.9% |
| action | 6,115 | 17.5% |
| documentary | 2,604 | 7.4% |
| animation | 2,239 | 6.4% |
| musical | 2,035 | 5.8% |
| crime | 1,712 | 4.9% |
| comedy | 1,236 | 3.5% |
| drama | 1,204 | 3.4% |
| western | 833 | 2.4% |
| educational | 694 | 2.0% |
| sci-fi | 383 | 1.1% |
| romance | 119 | 0.3% |

| Type | Count | % |
|---|---|---|
| feature | 21,615 | 61.8% |
| serial | 6,638 | 19.0% |
| cartoon | 2,133 | 6.1% |
| short | 1,705 | 4.9% |
| concert | 1,609 | 4.6% |
| educational | 827 | 2.4% |
| newsreel | 435 | 1.2% |

**Grateful Dead concerts:** 15 surviving.

---

## Pending

### Pass 6 — IA Description/Subject Backfill for `other`

**Script:** `cleaning/scripts/fetch_ia_descriptions.py`
**Target:** 7,293 surviving rows with `genre = other`
**Output:** `cleaning/other_ia_meta.csv`

Fetches `description` and `subject` tags from IA metadata API for each `other` row. At 0.5s/request ~60 minutes. Fully resumable.

Once complete, a keyword scanner will run against `description` + `subjects` fields to remap genres — far more reliable signal than title scanning.

---

## Filter Chips (Finalized)

**Type:** `Feature` · `Serial` · `Short` · `Cartoon` · `Concert` · `Newsreel` · `Educational`

**Genre:** `Horror` · `Crime` · `Comedy` · `Drama` · `Sci-Fi` · `Western` · `Animation` · `Documentary` · `Musical` · `Romance` · `Foreign`

**Language toggle:** `English Only` (default off) — filters on `language` field (`en` / `foreign`)

---

## Files

| File | Description |
|---|---|
| `raw.csv` | 🔒 Full raw DynamoDB export — do not modify |
| `tag_audit.txt` | Latest genre/type/collection distribution of surviving rows |
| `other.csv` | Surviving `other` genre rows for manual review |
| `other_ia_meta.csv` | IA description/subject fetch results (pending) |
| `scripts/backfill_duration.py` | Pass 1 — duration backfill via IA API + ffprobe |
| `scripts/junk_removal.py` | Pass 2 — duration threshold filter |
| `scripts/reset_and_filter.py` | Pass 3 — year >= 1990 exclusion + year extraction from title |
| `scripts/flag_title_keywords.py` | Pass 3b — trailer keyword flag |
| `scripts/remap_genres.py` | Pass 4 — collection/type/language remaps |
| `scripts/remap_title_keywords.py` | Pass 4b — title keyword genre scan |
| `scripts/pass5_other_cleanup.py` | Pass 5 — numeric flag + near-dupe dedup + year backfill |
| `scripts/tag_audit.py` | Audit tool — genre/type/collection counts for surviving rows |
| `scripts/title_word_audit.py` | Audit tool — top 100 words in surviving titles |
| `scripts/export_review_csv.py` | Export surviving rows to review.csv |
| `scripts/export_other_csv.py` | Export other-genre surviving rows to other.csv |
| `scripts/fetch_ia_descriptions.py` | Pass 6 — IA description/subject fetch for other rows |
| `scripts/check_dupes.py` | Debug tool — spot-check near-duplicate flagged rows |
