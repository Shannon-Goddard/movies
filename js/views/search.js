import { searchFilms } from '../api.js';
import { InfiniteScroll } from '../scroll.js';
import { playQueue } from '../player.js';
import { isSaved, toggleSaved } from '../library.js';
import { posterThumb } from '../utils.js';

export async function render(app, query = '') {
  app.innerHTML = `
    <div id="search-results-wrap">
      ${query ? `
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
      ` : `
        <div class="flex flex-col items-center justify-center py-20 gap-3 text-white/20">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <p class="text-sm">Search for a film, director, or keyword</p>
        </div>
      `}
    </div>
  `;

  if (!query) return;

  const list   = document.getElementById('results-list');
  const status = document.getElementById('results-status');
  const bar    = document.getElementById('sticky-count-bar');
  let allLoaded = [];

  document.getElementById('btn-play-all')?.addEventListener('click', () => {
    if (allLoaded.length) playQueue(allLoaded, 0);
  });

  const scroller = new InfiniteScroll({
    listEl: list, statusEl: status,
    fetchFn: offset => searchFilms(query, 20, offset),
    renderFn: (films, offset) => {
      if (offset === 0) list.innerHTML = '';
      allLoaded = allLoaded.slice(0, offset).concat(films);
      list.insertAdjacentHTML('beforeend', films.map((f, i) => _filmCard(f, offset + i)).join(''));
      if (bar) {
        bar.style.display = 'flex';
        const countEl = document.getElementById('results-count');
        if (countEl) countEl.textContent = `${allLoaded.length.toLocaleString()} results`;
      }
    },
  });

  list.addEventListener('click', e => {
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
}

function _filmCard(film, index) {
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
