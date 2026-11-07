import { loadCatalog, searchGratefulDead } from '../api.js';
import { InfiniteScroll } from '../scroll.js';
import { playQueue, playAt } from '../player.js';
import { loadSession } from '../queue.js';
import { isSaved, toggleSaved } from '../library.js';
import { posterThumb } from '../utils.js';
import en from '../i18n/en.js';

const GENRES = ['Horror', 'Crime', 'Comedy', 'Drama', 'Sci-Fi', 'Western', 'Animation', 'Documentary', 'Musical', 'Romance', 'Foreign'];

const TYPES = [
  { label: 'Feature Film', value: 'feature'     },
  { label: 'Short Film',   value: 'short'        },
  { label: 'Cartoon',      value: 'cartoon'      },
  { label: 'Serial',       value: 'serial'       },
  { label: 'Series',       value: 'series'       },
  { label: 'Concert',      value: 'concert'      },
  { label: 'Newsreel',     value: 'newsreel'     },
  { label: 'Educational',  value: 'educational'  },
];

const ERAS = [
  { label: 'Silent Era',  value: 'silent'  },
  { label: '1930s–50s',   value: 'classic' },
  { label: '1960s–70s',   value: 'vintage' },
  { label: '1980s+',      value: 'modern'  },
];

const COLORS = [
  { label: 'Black & White', value: 'bw'        },
  { label: 'Color',         value: 'color'     },
  { label: 'Colorized',     value: 'colorized' },
];

export async function render(app) {
  const session   = loadSession();
  const recentRaw = _loadRecent();

  app.innerHTML = `
    ${session.film_id ? _resumeBar(session) : ''}

    ${recentRaw.length ? `
      <section class="mb-8">
        <h2 class="section-label">${en.home_recent}</h2>
        <div class="scroll-row">
          ${recentRaw.map((f, i) => _posterCard(f, i, 'recent')).join('')}
        </div>
      </section>` : ''}

    <section class="mb-8">
      <h2 class="section-label">${en.home_type}</h2>
      <div class="scroll-row">
        ${TYPES.map(t => `<button data-type="${t.value}" class="chip">${t.label}</button>`).join('')}
      </div>
    </section>

    <section class="mb-8">
      <h2 class="section-label">${en.home_genre}</h2>
      <div class="scroll-row">
        ${GENRES.map(g => `<button data-genre="${g.toLowerCase()}" class="chip">${g}</button>`).join('')}
        <button data-gd class="chip flex items-center gap-1.5">
          <img src="/movies/icons/gd-skull.png" alt="" class="w-4 h-4 object-contain" />
          Grateful Dead
        </button>
      </div>
    </section>

    <section class="mb-4">
      <div class="scroll-row items-center">
        <button id="btn-lang-toggle" class="chip flex items-center gap-1.5" aria-pressed="false">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
          English Only
        </button>
      </div>
    </section>

    <section class="mb-8">
      <h2 class="section-label">${en.home_era}</h2>
      <div class="scroll-row">
        ${ERAS.map(e => `<button data-era="${e.value}" class="chip">${e.label}</button>`).join('')}
      </div>
    </section>

    <section class="mb-8">
      <h2 class="section-label">${en.home_color}</h2>
      <div class="scroll-row">
        ${COLORS.map(c => `<button data-color="${c.value}" class="chip">${c.label}</button>`).join('')}
      </div>
    </section>

    <section id="results-section" class="mb-8 hidden">
      <div id="sticky-count-bar">
        <p id="results-count" class="text-xs text-white/40"></p>
        <button id="btn-play-all"
                class="flex items-center gap-1.5 text-xs font-medium text-accent hover:opacity-80 transition">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
          Play all
        </button>
      </div>
      <div id="results-list" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">${_skeletons(8)}</div>
      <p id="results-status" class="text-xs text-center py-4 text-white/30"></p>
    </section>

    <div id="home-empty" class="flex flex-col items-center justify-center py-16 gap-3 text-white/20">
      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18"/><line x1="7" y1="2" x2="7" y2="22"/><line x1="17" y1="2" x2="17" y2="22"/><line x1="2" y1="12" x2="22" y2="12"/><line x1="2" y1="7" x2="7" y2="7"/><line x1="2" y1="17" x2="7" y2="17"/><line x1="17" y1="17" x2="22" y2="17"/><line x1="17" y1="7" x2="22" y2="7"/>
      </svg>
      <p class="text-sm">Pick a filter above or search to start watching</p>
    </div>
  `;

  // ── Filter state ─────────────────────────────────────────
  const active = { genres: new Set(), types: new Set(), eras: new Set(), colors: new Set(), gd: false };
  let englishOnly  = false;
  let activeScroll = null;

  // ── Chip toggle helpers ───────────────────────────────────
  function _toggleChip(el, set, value) {
    if (set.has(value)) { set.delete(value); el.classList.remove('chip-active'); el.classList.add('chip'); }
    else                { set.add(value);    el.classList.add('chip-active');    el.classList.remove('chip'); }
    _refresh();
  }

  // ── Wire chips ────────────────────────────────────────────
  app.querySelectorAll('[data-genre]').forEach(el =>
    el.addEventListener('click', () => _toggleChip(el, active.genres, el.dataset.genre)));

  app.querySelectorAll('[data-type]').forEach(el =>
    el.addEventListener('click', () => _toggleChip(el, active.types, el.dataset.type)));

  app.querySelectorAll('[data-era]').forEach(el =>
    el.addEventListener('click', () => _toggleChip(el, active.eras, el.dataset.era)));

  app.querySelectorAll('[data-color]').forEach(el =>
    el.addEventListener('click', () => _toggleChip(el, active.colors, el.dataset.color)));

  app.querySelector('[data-gd]').addEventListener('click', function() {
    active.gd = !active.gd;
    this.classList.toggle('chip-active', active.gd);
    this.classList.toggle('chip', !active.gd);
    _refresh();
  });

  const langBtn = app.querySelector('#btn-lang-toggle');
  langBtn.addEventListener('click', () => {
    englishOnly = !englishOnly;
    langBtn.setAttribute('aria-pressed', englishOnly);
    langBtn.classList.toggle('chip-active', englishOnly);
    langBtn.classList.toggle('chip', !englishOnly);
    _refresh();
  });

  // ── Filter + render ───────────────────────────────────────
  async function _refresh() {
    const hasFilters = active.genres.size || active.types.size || active.eras.size || active.colors.size || active.gd || englishOnly;

    if (!hasFilters) {
      activeScroll?.destroy(); activeScroll = null;
      document.getElementById('results-section').classList.add('hidden');
      document.getElementById('home-empty').classList.remove('hidden');
      return;
    }

    let catalog = active.gd
      ? (await searchGratefulDead(99999, 0)).films
      : await loadCatalog();

    if (active.genres.size)  catalog = catalog.filter(f => active.genres.has(f.genre));
    if (active.types.size) {
      if (active.types.has('series')) {
        const types = new Set([...active.types].filter(t => t !== 'series'));
        catalog = catalog.filter(f => f.series_name || (types.size && types.has(f.type)));
      } else {
        catalog = catalog.filter(f => active.types.has(f.type));
      }
    }
    if (active.eras.size)    catalog = catalog.filter(f => active.eras.has(f.era));
    if (active.colors.size)  catalog = catalog.filter(f => active.colors.has(f.color));
    if (englishOnly)         catalog = catalog.filter(f => f.language === 'en');

    // Collapse series into single cards
    const seriesMap = new Map();
    const collapsed = [];
    for (const f of catalog) {
      if (f.series_name) {
        if (!seriesMap.has(f.series_name)) {
          seriesMap.set(f.series_name, { _isSeries: true, series_name: f.series_name, _eps: [], film_id: f.film_id, poster_url: f.poster_url, year: f.year });
          collapsed.push(seriesMap.get(f.series_name));
        }
        seriesMap.get(f.series_name)._eps.push(f);
      } else {
        collapsed.push(f);
      }
    }

    const PAGE = 20;
    activeScroll?.destroy();
    activeScroll = _loadPaged(
      offset => Promise.resolve({ films: collapsed.slice(offset, offset + PAGE), total: collapsed.length }),
      collapsed
    );
  }

  app.querySelectorAll('[data-recent]').forEach(el => {
    el.addEventListener('click', () => playQueue(recentRaw, parseInt(el.dataset.recent)));
  });

  app.querySelector('#btn-resume')?.addEventListener('click', () => {
    if (session.film) playAt(session.film, session.position_sec || 0);
  });
}

function _loadPaged(fetchFn, allFilms) {
  const section = document.getElementById('results-section');
  const list    = document.getElementById('results-list');
  const status  = document.getElementById('results-status');
  const bar     = document.getElementById('sticky-count-bar');
  document.getElementById('home-empty')?.classList.add('hidden');
  section.classList.remove('hidden');
  list.innerHTML = _skeletons(8);
  if (bar) bar.style.display = 'none';

  setTimeout(() => {
    const top = section.getBoundingClientRect().top + window.scrollY - 60;
    window.scrollTo({ top, behavior: 'smooth' });
  }, 50);

  let allLoaded = [];

  document.getElementById('btn-play-all')?.addEventListener('click', () => {
    if (allFilms?.length) playQueue(allFilms, 0);
  });

  const scroller = new InfiniteScroll({
    listEl: list, statusEl: status, fetchFn,
    renderFn: (films, offset, data) => {
      if (offset === 0) list.innerHTML = '';
      allLoaded = allLoaded.slice(0, offset).concat(films);
      list.insertAdjacentHTML('beforeend', films.map((f, i) => _filmCard(f, offset + i)).join(''));
      if (bar) {
        bar.style.display = 'flex';
        const countEl = document.getElementById('results-count');
        if (countEl) {
          const total = data?.total;
          countEl.textContent = total
            ? `${allLoaded.length.toLocaleString()} of ${total.toLocaleString()}`
            : `${allLoaded.length.toLocaleString()} loaded`;
        }
      }
    },
  });

  list.addEventListener('click', e => {
    const share = e.target.closest('[data-share]');
    if (share) {
      e.stopPropagation();
      const url = `${location.origin}/movies/#/film/${share.dataset.share}`;
      navigator.clipboard?.writeText(url).then(() => {
        share.classList.add('text-accent');
        setTimeout(() => share.classList.remove('text-accent'), 1500);
      });
      return;
    }
    const save = e.target.closest('[data-save]');
    if (save) {
      e.stopPropagation();
      const film = allLoaded.find(f => f.film_id === save.dataset.save);
      if (film) {
        const nowSaved = toggleSaved(film);
        save.classList.toggle('text-accent', nowSaved);
        save.classList.toggle('text-white/20', !nowSaved);
        save.querySelector('svg').setAttribute('fill', nowSaved ? 'currentColor' : 'none');
      }
      return;
    }
    const card = e.target.closest('[data-index]');
    if (card) playQueue(allLoaded, parseInt(card.dataset.index));
  });

  scroller.start();
  return scroller;
}

// ── Components ────────────────────────────────────────────

function _resumeBar(session) {
  const film  = session.film;
  const s     = film?.season_num ? `S${film.season_num}` : '';
  const e     = film?.episode_num ? `E${film.episode_num}` : '';
  const badge = s || e ? `${s}${e} — ` : '';
  const title = film?.series_name
    ? `${film.series_name}: ${badge}${film.title || ''}`
    : (film?.title || 'Last session');
  const pos   = session.position_sec ? _fmt(session.position_sec) : '';
  return `
    <div class="flex items-center justify-between bg-card rounded-lg px-4 py-3 mb-6"
         style="border:1px solid rgba(255,255,255,0.07)">
      <div class="min-w-0">
        <p class="text-xs text-white/40 mb-0.5">${en.home_continue}</p>
        <p class="text-sm font-medium truncate">${_esc(title)}${pos ? ` <span class="text-white/30 font-normal">· ${pos}</span>` : ''}</p>
      </div>
      <button id="btn-resume" class="ml-4 shrink-0 text-sm font-medium text-accent hover:opacity-80 transition">Resume</button>
    </div>`;
}

function _posterCard(film, index, type) {
  return `
    <button data-${type}="${index}" class="card flex-shrink-0 w-32 text-left">
      <div class="w-32 h-48 rounded-lg overflow-hidden mb-2">${posterThumb(film)}</div>
      <p class="text-xs font-medium truncate">${_esc(film.title)}</p>
      <p class="text-xs text-white/40 truncate">${film.year || ''}</p>
    </button>`;
}

function _filmCard(film, index) {
  if (film._isSeries) {
    return `
      <a href="#/series/${encodeURIComponent(film.series_name)}"
         class="card bg-card rounded-lg overflow-hidden cursor-pointer hover:bg-raised transition"
         style="border:1px solid rgba(255,255,255,0.06)">
        <div class="relative aspect-[2/3] overflow-hidden">
          ${posterThumb(film)}
          <span class="absolute bottom-1.5 right-1.5 text-[10px] tabular-nums bg-black/70 text-white/80 px-1.5 py-0.5 rounded">${film._eps.length} eps</span>
        </div>
        <div class="p-2">
          <p class="text-xs font-medium truncate leading-tight">${_esc(film.series_name)}</p>
          <p class="text-[10px] text-white/35 truncate mt-0.5">Series${film.year ? ` · ${film.year}` : ''}</p>
        </div>
      </a>`;
  }
  const duration = film.duration_sec ? _fmt(film.duration_sec) : '';
  const saved    = isSaved(film.film_id);
  const badges   = [film.year, film.color_label, film.era_label].filter(Boolean);
  return `
    <div data-index="${index}" data-film-id="${_esc(film.film_id)}"
         class="card bg-card rounded-lg overflow-hidden cursor-pointer hover:bg-raised transition"
         style="border:1px solid rgba(255,255,255,0.06)">
      <div class="relative aspect-[2/3] overflow-hidden">
        ${posterThumb(film)}
        ${duration ? `<span class="absolute bottom-1.5 right-1.5 text-[10px] tabular-nums bg-black/70 text-white/80 px-1.5 py-0.5 rounded">${duration}</span>` : ''}
        <button data-save="${_esc(film.film_id)}" aria-label="Save to watchlist"
                class="absolute top-1.5 right-1.5 p-1 rounded-full bg-black/50 transition hover:scale-110 ${saved ? 'text-accent' : 'text-white/50'}">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="${saved ? 'currentColor' : 'none'}" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
          </svg>
        </button>
        <button data-share="${_esc(film.film_id)}" aria-label="Share"
                class="absolute top-1.5 left-1.5 p-1 rounded-full bg-black/50 transition hover:scale-110 text-white/50">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/>
            <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>
          </svg>
        </button>
      </div>
      <div class="p-2">
        <p class="text-xs font-medium truncate leading-tight">${_esc(film.title)}</p>
        ${badges.length ? `<p class="text-[10px] text-white/35 truncate mt-0.5">${badges.join(' · ')}</p>` : ''}
      </div>
    </div>`;
}

function _fmt(sec) {
  sec = parseFloat(sec);
  if (isNaN(sec)) return '';
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = Math.floor(sec % 60).toString().padStart(2, '0');
  return h > 0 ? `${h}:${m.toString().padStart(2,'0')}:${s}` : `${m}:${s}`;
}

function _loadRecent() {
  try { return JSON.parse(localStorage.getItem('movies_recent')) || []; }
  catch { return []; }
}

function _skeletons(n) {
  return Array.from({ length: n }, () =>
    `<div class="rounded-lg overflow-hidden"><div class="skeleton aspect-[2/3] w-full"></div><div class="skeleton h-3 mt-2 w-3/4"></div></div>`
  ).join('');
}

function _esc(str) {
  return String(str ?? '').replace(/[&<>"']/g, c =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])
  );
}
