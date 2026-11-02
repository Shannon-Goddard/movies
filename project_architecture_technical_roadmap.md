# Architecture & Technical Roadmap: Free Open-Licensed Film Streaming Platform

This document is the master engineering blueprint for the platform. It reflects the current live state of the project and the forward roadmap.

Built by [Amazon Q](https://aws.amazon.com/q/developer/) alongside Shannon Goddard.

---

## Current Live State

| Layer | Status | Detail |
|---|---|---|
| DynamoDB table | ✅ Live | `movies`, `us-east-1` |
| GSIs | ✅ All 4 ACTIVE | genre-index, type-index, era-index, color-index |
| Ingestion — short_films | ✅ Done | 2,819 written, 262 deduped |
| Ingestion — silent_films | ✅ Done | 3,474 written, 1 deduped |
| Ingestion — educational_films | 🔄 Running | ~9,900+ written |
| Ingestion — newsandpublicaffairs | 🔄 Running | ~9,700+ written |
| Ingestion — horror_and_suspense | 🔄 Running | ~9,100+ written |
| Ingestion — animationandcartoons | 🔄 Running | ~9,600+ written |
| Ingestion — classic_tv | 🔄 Resuming | ~9,800+ written |
| Ingestion — feature_films | 🔄 Resuming | ~8,200+ written |
| **Total catalog** | **61,719+ films (growing)** | Internet Archive — 8 collections |
| Genre mapping | ✅ Done | 11 genres mapped from 12,000-item real tag sample |
| Era detection | ✅ Done | silent / classic / vintage / modern from year |
| Color detection | ✅ Done | bw / color / colorized from subject + description tags |
| API — `/films/search` | ✅ Live | `q=`, `genre=`, `type=`, `era=`, `color=`, `limit=`, `offset=` |
| API — `/stats` | ✅ Live | `total_films`, `by_type`, `by_era`, `by_color` |
| Lambda memory | ✅ 256MB | Both Lambdas, 15s timeout |
| Decimal serialization | ✅ Fixed | Custom JSON encoder handles DynamoDB Decimal types |
| Frontend PWA | ✅ Live | `https://shannon-goddard.github.io/movies/` |
| Icons | ✅ Done | Real PNG icons — icon-192, icon-512, logo-192, logo-512, preview 1200×630 |
| Service worker | ✅ Live | Shell cache + video stream cache |
| Google Cast | ✅ Wired | App ID `20706015`, unpublished — test devices only |
| Google Analytics | ✅ Live | GA4, anonymized |
| Google Search Console | ✅ Verified | Sitemap submitted |
| Legal pages | ✅ Done | about, privacy, terms, licenses |

**API base URL:** `https://3m0629omkh.execute-api.us-east-1.amazonaws.com/v1`
**Frontend:** `https://shannon-goddard.github.io/movies/`

---

## Architecture Overview

```
[ Data Source ]
  Internet Archive (8 collections — public domain + CC-licensed films)
       │
       ▼
[ Ingestion Layer ]  ← resumable, last_id checkpointing every 100 writes
       │             ← genre map built from 12,000-item real tag sample
       │             ← era + color detected at ingest time
       ▼
[ AWS DynamoDB ] ──────────────────> Film index (film_id PK + 4 GSIs)
       │
       ▼
[ AWS API Gateway + Lambda ] ──────> Serverless REST API
       │
       ▼
[ GitHub Pages (Frontend) ] ────────> PWA / SPA Video Player
       │
       ├──> Casual viewers       (browse by genre, era, color)
       ├──> Film enthusiasts     (search by title/director, watchlist)
       ├──> Mobile users         (PWA install, fullscreen, tap controls)
       └──> TV viewers           (Google Cast to Chromecast)
```

---

## 1. Database Schema (DynamoDB — Flat, Live)

```json
{
  "film_id":      "a3f2c1d4e5b6...",
  "title":        "The General",
  "director":     "Buster Keaton",
  "year":         1926,
  "genre":        "comedy",
  "type":         "feature",
  "era":          "silent",
  "era_label":    "Silent Era",
  "color":        "bw",
  "color_label":  "B&W",
  "stream_url":   "https://archive.org/download/...",
  "poster_url":   "https://archive.org/services/img/...",
  "source":       "internet_archive",
  "source_url":   "https://archive.org/details/...",
  "license_type": "https://creativecommons.org/publicdomain/mark/1.0/",
  "collection":   "feature_films",
  "duration_sec": 6765,
  "ingested_at":  "2026-11-01T10:00:00+00:00"
}
```

`era` and `color` are optional — items where year or color cannot be detected are written without those fields rather than failing DynamoDB GSI key validation.

`director` is normalized to a string at ingest time — IA sometimes returns it as a list.

---

## 2. DynamoDB GSIs (All 4 Deployed & ACTIVE)

| Index | Hash Key | Range Key | Used By |
|---|---|---|---|
| `genre-index` | `genre` | `film_id` | `/films/search?genre=` |
| `type-index` | `type` | `film_id` | `/films/search?type=` |
| `era-index` | `era` | `film_id` | `/films/search?era=` |
| `color-index` | `color` | `film_id` | `/films/search?color=` |

---

## 3. Genre Mapping

The genre map was built by sampling 12,000 real items across all 8 IA collections and aggregating subject tags. This approach yields significantly more genre matches than relying on schema headers alone — covering English and Spanish tags found in the actual corpus.

| Genre | Key Tags |
|---|---|
| horror | horror, terror, scary, paranormal, slasher, zombie, creepypasta, miedo, fantasmas |
| sci-fi | sci-fi, science fiction, fantasy |
| animation | animation, cartoon, soviet cartoon, anime |
| documentary | documentary, history, wwii, war, newsreel, deutsche wochenschau |
| educational | education, educational, lecture, government |
| musical | musical, music, variety show |
| comedy | comedy, humor, funny, parody, comedia, sitcom |
| crime | crime, murder, film noir, mystery, thriller, suspense |
| action | action, adventure, western, cliffhanger, serial |
| romance | romance, love |
| drama | drama, silent drama, family, indie |

Items with no matching tags are stored as `genre: other`.

---

## 4. Technical Roadmap

### Phase 1: AWS Infrastructure ✅ Complete

- DynamoDB table `movies` with 4 GSIs — PAY_PER_REQUEST
- IAM role `movies-lambda-role` scoped to `movies` table and `movies-*` log groups
- Lambda `movies-search` — GET /films/search
- Lambda `movies-stats` — GET /stats
- API Gateway `movies-api` — CORS enabled, deployed to stage `v1`
- Decimal JSON serialization fix — DynamoDB returns numbers as Decimal

---

### Phase 2: Ingestion Pipeline ✅ Complete

- Genre map built from real IA subject tag sample (12,000 docs across 8 collections)
- Era detection from year field — silent / classic / vintage / modern
- Color detection from subject + description tags — bw / color / colorized
- Null GSI key handling — era and color only written when detected
- Director field normalization — list → string
- Resume checkpointing — last_id saved every 100 writes, `--resume` flag restarts from identifier range query (not cursor — IA cursors expire after ~30-40 min on large collections)
- Fixed collection queries — `educational_films` and `horror_and_suspense` use subject: queries, not collection: queries

---

### Phase 3: Frontend PWA ✅ Complete

- Video overlay player — fullscreen, tap to show/hide controls
- Double-tap seek zones — left = -10s, right = +10s
- Google Cast SDK wired — App ID `20706015`
- Watchlist — localStorage, `movies_*` keys
- Queue management — session persistence
- Infinite scroll — IntersectionObserver sentinel
- Filter chips — Genre, Type, Era, Color
- Poster grid — 2/3 aspect ratio cards
- Keyboard shortcuts — Space, ←/→, F, Escape
- Media Session API — lock screen / hardware controls
- PWA manifest + service worker — installable, offline shell

---

### Phase 4: Production Hardening 🔜 Pending

- **4.1** WAF rate limiting — attach WebACL to API Gateway stage `v1`
- **4.2** CORS lock — restrict `Access-Control-Allow-Origin` from `*` to `https://shannon-goddard.github.io`
- **4.3** CloudWatch alarms — Lambda error rate, 5xx rate
- **4.4** Publish Google Cast app — currently unpublished, test devices only

---

### Phase 5: Automated Lifecycle Maintenance 🔜 Pending

- **5.1** Monthly ingestion cron — EventBridge rule → Lambda trigger to pick up new IA uploads
- **5.2** Dead link health checker — periodic HEAD requests on stream_urls, mark dead items
- **5.3** Resume on failure — EventBridge retry on cursor expiry errors

---

### Phase 6: Feature Expansion 🔜 Pending

| Feature | Notes |
|---|---|
| Continue watching | Save position every 10s, resume bar on home |
| Recently watched | `movies_recent` localStorage, capped at 20 |
| Subtitle support | IA items sometimes include .srt/.vtt — parse and load via `<track>` |
| Custom Cast receiver | Register branded receiver for subtitle support on TV |
| Director pages | Drill-down from film card → all films by director |
| Collections view | Browse by IA collection |
| Download button | `stream_url` with `download` attr for public domain items |
| **Subgenre system** | Add `subgenre` field — map horror tags to Supernatural, Slasher, Zombie, etc. Items with `genre: other` get subgenre from collection (e.g. `horror_and_suspense` → `subgenre: horror`). Netflix-style horizontal rows per subgenre on home screen. |
| **Collection-based genre remap** | One-time script — scan all items where `genre = other`, remap genre from collection (e.g. `horror_and_suspense` → `genre: horror`). Run after all ingestion complete. |

---

### Phase 7: UX Restructure 🔜 Pending

**Top-level navigation — 5 content buckets:**

| Tab | Collections | Type value |
|---|---|---|
| Movies | feature_films, short_films, silent_films, horror_and_suspense, film_noir, westerns | feature, short |
| TV | classic_tv, serials | serial |
| Cartoons | animationandcartoons | cartoon |
| News | newsandpublicaffairs | newsreel |
| Education | educational_films | educational |

**Subcategory rows per tab (Netflix-style horizontal swipe):**
- Movies → Black & White, Silent Films, Shorts, Horror, Comedy, Westerns, Romance, Noir, Sci-Fi, Action, Drama
- TV → subcategories TBD after subject tag audit
- Cartoons → subcategories TBD after subject tag audit
- News → subcategories TBD after subject tag audit
- Education → subcategories TBD after subject tag audit

**Tag-based curated rows** (driven by IA subject tags, built during cleaning pass):
- Horror → Vampires, Zombies, Ghosts, Creature Features, Slasher
- Western → Cowboys, Outlaws, Spaghetti Westerns
- Sci-Fi → Aliens, Space, Mad Scientists, Giant Monsters
- Tag vocabulary finalized after high-frequency subject tag scan across full catalog

**Other UX enhancements:**

| Feature | Notes |
|---|---|
| **Random film button** | "I'm feeling lucky" — picks a random film from the full catalog |
| **Trending / Most played** | Track play counts in DynamoDB, surface top films per genre |
| **New additions row** | Filter by `ingested_at` descending — recently added films |
| **Decade filter** | 1920s, 1930s, 1940s etc. More granular than era chips |
| **Duration filter** | Under 30 min / 30–90 min / 90+ min |
| **Director page** | Tap director name → all films by that director |
| **Watch history** | Auto-populated, separate from watchlist, last 5 in continue watching row |
| **Share / deep link** | `#/film/{film_id}` route, share button on film card |
| **Content warning** | Dismissible first-visit banner + notice on about.html. Add `mature` flag during cleaning pass with UI filter toggle. |

---

### Phase 8: Catalog Cleaning 🔜 Pending (after all ingestion complete)

Same 4-pass pattern as music project (`music/cleaning/`). Scripts to be created in `backend/cleaning/`.

**Pass 1 — Bad stream URLs**
- `probe_bad_urls.py` — identify non-ASCII characters in stream_url paths
- `clean_stream_url.py` — remove items with non-Latin or accented Latin filenames that will fail in the video player

**Pass 2 — Genre remap**
- `probe_collection_genre.py` — scan items where `genre = other`, group by collection, show counts
- `remap_collection_genre.py` — SET genre from collection for all `other` items (e.g. `horror_and_suspense` → `horror`)
- `probe_subgenre.py` — audit subject tags within each collection to build subgenre buckets
- `apply_subgenres.py` — write `subgenre` field based on subject tag mapping + collection fallback

**Pass 3 — Duplicates**
- `probe_dupes.py` — scan for duplicate `stream_url` values (film_id = md5(stream_url) should prevent true dupes but verify)
- `probe_title_dupes.py` — same title + year combinations across collections

**Pass 4 — Duration**
- `probe_duration.py` — missing and zero duration_sec by collection
- `clean_duration.py` — null out zero values, accept missing gaps (display-only field)

---

## 5. Ingestion Collections

| Collection | Status | Written | Deduped | Notes |
|---|---|---|---|---|
| short_films | ✅ Done | 2,819 | 262 | Short films, experimental |
| silent_films | ✅ Done | 3,474 | 1 | Pre-talkie era |
| educational_films | 🔄 Running | ~9,900+ | 31 | Uses subject:educational query |
| newsandpublicaffairs | 🔄 Running | ~9,700+ | 47 | Newsreels, historical footage |
| horror_and_suspense | 🔄 Running | ~9,100+ | 148 | Uses subject:horror OR subject:suspense query |
| animationandcartoons | 🔄 Running | ~9,600+ | 14 | Cartoons, animated shorts |
| classic_tv | 🔄 Resuming | ~9,800+ | 4 | Old TV episodes, serials |
| feature_films | 🔄 Resuming | ~8,200+ | 1,684 | Public domain features |

> IA scrape cursors expire after ~30-40 minutes on large collections. Use `--resume` to restart from the last saved identifier. Progress is checkpointed every 100 writes to `ia_resume_{collection}.json`.

---

## 6. Known Issues & Fixes

| Issue | Status | Notes |
|---|---|---|
| DynamoDB GSI null key rejection | ✅ Fixed | era and color only written when non-null |
| IA cursor expiry on large collections | ✅ Mitigated | `--resume` uses identifier range query instead of cursor |
| `datetime.utcnow()` deprecation | ✅ Fixed | Replaced with `datetime.now(timezone.utc)` |
| Decimal not JSON serializable | ✅ Fixed | Custom `_serial()` encoder in both Lambdas |
| director field as list | ✅ Fixed | Normalized to string at ingest time |
| subject field as non-string | ✅ Fixed | `_resolve_genre()` and `_color()` skip non-string entries |
| Cast chrome-extension error in browser | ✅ Expected | Cast SDK only activates when a Chromecast is on the network |

---

## 7. Folder Structure

```
movies/
├── backend/
│   ├── api/
│   │   ├── search.py               # Lambda: GET /films/search (q, genre, type, era, color)
│   │   └── stats.py                # Lambda: GET /stats — total_films, by_type, by_era, by_color
│   └── ingestion/
│       └── ingest_ia.py            # IA — 8 collections, resumable, genre/era/color detection
│
├── css/
│   └── app.css
│
├── icons/
│   ├── movies-icon.png             # Source — transparent bg
│   ├── movies-logo.png             # Source — black bg
│   ├── icon-192.png                # PWA + favicon
│   ├── icon-512.png                # PWA splash
│   ├── logo-192.png                # Home screen icon
│   ├── logo-512.png                # Home screen icon large
│   └── preview.png                 # OG image 1200×630
│
├── js/
│   ├── app.js                      # SPA router (hash-based)
│   ├── api.js                      # API client — BASE_URL, all search functions
│   ├── player.js                   # Video player — tap controls, Cast SDK, keyboard shortcuts
│   ├── queue.js                    # Queue management, session persistence
│   ├── library.js                  # Watchlist — localStorage movies_* keys
│   ├── scroll.js                   # InfiniteScroll utility
│   ├── utils.js                    # posterThumb(), coverGradient()
│   ├── i18n/
│   │   └── en.js                   # String constants
│   └── views/
│       ├── home.js                 # Filter chips + poster grid
│       ├── search.js               # Search results
│       └── library.js              # Watchlist view
│
├── .gitignore
├── about.html
├── aws-setup-guide.md
├── index.html
├── LICENSE
├── licenses.html
├── manifest.json
├── privacy.html
├── project_architecture_technical_roadmap.md
├── robots.txt
├── service-worker.js
├── sitemap.xml
└── terms.html
```

---

## 8. Key AWS Resources

| Resource | Value |
|---|---|
| Region | `us-east-1` |
| DynamoDB table | `movies` |
| Lambda — search | `movies-search` (256MB, 15s) |
| Lambda — stats | `movies-stats` (256MB, 15s) |
| Lambda role | `movies-lambda-role` |
| API Gateway | `movies-api` (`3m0629omkh`) |
| API base URL | `https://3m0629omkh.execute-api.us-east-1.amazonaws.com/v1` |
| Cast App ID | `20706015` (unpublished) |
| Frontend | `https://shannon-goddard.github.io/movies/` |
| GitHub repo | `https://github.com/Shannon-Goddard/movies` |

---

## 9. Architectural Differentiators

- **Zero-storage streaming** — 0 GB video stored, all streams served direct from Internet Archive
- **Real tag-informed genre mapping** — genre map built from actual corpus sample, not assumed schema
- **Null-safe GSI design** — optional metadata fields never block writes
- **Resumable ingestion** — identifier-range checkpointing survives IA cursor expiry on multi-hour runs
- **Cast-native** — IA MP4 direct URLs work with Default Media Receiver out of the box
- **Decoupled serverless stack** — GitHub Pages + Lambda + DynamoDB, free-tier friendly
- **Single source, maximum coverage** — Internet Archive's 8 film collections cover features, shorts, animation, silent era, educational, classic TV, newsreels, and horror
