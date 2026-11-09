![header](icons/header.png)

[![Live Demo](https://img.shields.io/badge/live_demo-000000?logo=github)](https://shannon-goddard.github.io/movies/)
[![Catalog](https://img.shields.io/badge/21%2C289_films-FFFFE0)](data/index.json)
[![License](https://img.shields.io/badge/license-MIT-5B7C99)](LICENSE)
[![PWA](https://img.shields.io/badge/PWA-ready-b1430c?logo=pwa)](https://shannon-goddard.github.io/movies/)
[![Built with Amazon Q](https://img.shields.io/badge/built_with-Amazon_Q-FF9900?logo=amazonaws)](https://aws.amazon.com/q/)
[![Loyal9 LLC](https://img.shields.io/badge/dev-Loyal9_LLC-04aa6d)](https://shannon-goddard.loyal9.app/)

---

A free, ad-free streaming platform for 21,289 public domain and open-licensed films — served entirely from static files with zero backend, zero cost, and zero compromises on speed.

> **[▶ Watch now →](https://shannon-goddard.github.io/movies/)**

---

![demo](icons/demo.gif)

---

## Features

- **21,289 films** — features, shorts, cartoons, serials, concerts, newsreels, documentaries
- **13 genres · 7 types · 4 eras · 3 color modes** — stackable filter chips, instant results
- **320 series** — browse by series, episode lists, Play All, next-episode autoplay
- **Zero latency** — `index.json` preloaded by service worker on first visit, every filter is a pure in-memory array operation after that
- **PWA** — installable on any device, works offline for browsing
- **Google Cast** — stream to any Chromecast directly from the browser
- **Continue watching** — position saved every 10 seconds, resume bar on home screen
- **Recently watched** — last 20 films, one tap to jump back in
- **Watchlist** — save films to your library, persisted in localStorage
- **Share any film** — every card has a share button that copies a direct deep link
- **English Only toggle** — filter the full catalog to English-language films instantly
- **Grateful Dead chip** — 15 full concerts, one tap away 💀
- **Keyboard shortcuts** — Space, ←/→, ↑/↓, F, Escape
- **Double-tap seek** — left third = -10s, right third = +10s
- **Media Session API** — lock screen controls and hardware media keys

---

## How It Works

```
Internet Archive (11 collections, public domain + CC-licensed)
       │
       ▼
6-pass cleaning pipeline  →  21,289 surviving rows
       │                      genre / type / era / color / language / duration filters
       ▼
data/index.json  ──────────────────────────────────────────────────────►  GitHub Pages CDN
       │                                                                   ~3MB gzipped
       ▼                                                                   preloaded by SW
PWA / SPA  ──►  all filtering, search, and playback = client-side JS
                video streams served direct from Internet Archive
                0 GB stored · 0 servers · $0/month
```

No database. No API. No Lambda. No bill. Just a 3MB JSON file and a service worker.

---

## Catalog

| | |
|---|---|
| Total films | 21,289 |
| Genres | Action · Horror · Documentary · Crime · Drama · Comedy · Animation · Musical · Western · Educational · Sci-Fi · Romance · Other |
| Types | Feature · Short · Cartoon · Serial · Concert · Newsreel · Educational |
| Eras | Silent Era · 1930s–50s · 1960s–70s · 1980s+ |
| Series | 320 unique series, 5,364 serial episodes tagged with season/episode numbers |
| Source | [Internet Archive](https://archive.org) — public domain + Creative Commons |
| Durations | Patched from live DynamoDB export — 99.9% coverage |

The catalog was built through a multi-pass cleaning workstream — duration backfill, junk removal, year filtering, genre remapping, near-duplicate deduplication, title casing, series detection, and episode tagging. Full details in [CLEANING.md](cleaning/CLEANING.md).

---

## Getting Started

It's a static site — no build step, no dependencies.

```bash
git clone https://github.com/Shannon-Goddard/movies.git
cd movies
# open index.html in a browser, or serve locally:
npx serve .
```

The app loads `data/index.json` on first visit and caches it. Every filter and search after that is instant.

---

## Want to Scale This?

The full AWS infrastructure — DynamoDB, Lambda, API Gateway — was built alongside this project and is documented in the [architecture & technical roadmap](project_architecture_technical_roadmap.md). If your catalog grows beyond ~150k rows or you need user-generated data (ratings, play counts, comments), the [AWS setup guide](aws-setup-guide.md) walks through standing up the full stack. Flip one constant in `api.js` and it's live.

---

## Built With

| | |
|---|---|
| [Internet Archive](https://archive.org) | 21,289 public domain films, zero hosting cost |
| [GitHub Pages](https://pages.github.com) | Static hosting + CDN, free forever |
| [Amazon Q Developer](https://aws.amazon.com/q/developer/) | AI pair programmer — architecture, cleaning pipeline, every line of code |
| [Google Cast SDK](https://developers.google.com/cast) | Chromecast support, App ID `20706015` |
| [Google Analytics 4](https://analytics.google.com) | Anonymized watch data for future recommendations |
| [Tailwind CSS](https://tailwindcss.com) | Utility-first styling |

---

## License

[MIT](LICENSE) — free to use, fork, and build on.

---

<sub>Built by [Shannon Goddard / Loyal9 LLC](https://shannon-goddard.loyal9.app/) with [Amazon Q Developer](https://aws.amazon.com/q/developer/)</sub>
