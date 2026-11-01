import { getSaved, toggleSaved } from '../library.js';
import { playQueue } from '../player.js';
import { posterThumb } from '../utils.js';

export function render(app) {
  const films = getSaved();

  if (!films.length) {
    app.innerHTML = `
      <div class="flex flex-col items-center justify-center py-20 gap-3 text-white/20">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
        </svg>
        <p class="text-sm">Your watchlist is empty</p>
        <p class="text-xs">Tap the heart on any film to save it</p>
      </div>`;
    return;
  }

  app.innerHTML = `
    <div class="flex items-center justify-between mb-4">
      <h2 class="section-label">Watchlist · ${films.length} film${films.length !== 1 ? 's' : ''}</h2>
      <button id="btn-play-all"
              class="flex items-center gap-1.5 text-xs font-medium text-accent hover:opacity-80 transition">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
        Play all
      </button>
    </div>
    <div id="library-grid" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
      ${films.map((f, i) => _filmCard(f, i)).join('')}
    </div>`;

  document.getElementById('btn-play-all')?.addEventListener('click', () => playQueue(films, 0));

  document.getElementById('library-grid').addEventListener('click', e => {
    const save = e.target.closest('[data-save]');
    if (save) {
      e.stopPropagation();
      const film = films.find(f => f.film_id === save.dataset.save);
      if (film) { toggleSaved(film); render(app); }
      return;
    }
    const card = e.target.closest('[data-index]');
    if (card) playQueue(films, parseInt(card.dataset.index));
  });
}

function _filmCard(film, index) {
  const duration = film.duration_sec ? _fmt(film.duration_sec) : '';
  const badges   = [film.year, film.color_label].filter(Boolean);
  return `
    <div data-index="${index}" data-film-id="${_esc(film.film_id)}"
         class="card bg-card rounded-lg overflow-hidden cursor-pointer hover:bg-raised transition"
         style="border:1px solid rgba(255,255,255,0.06)">
      <div class="relative aspect-[2/3] overflow-hidden">
        ${posterThumb(film)}
        ${duration ? `<span class="absolute bottom-1.5 right-1.5 text-[10px] tabular-nums bg-black/70 text-white/80 px-1.5 py-0.5 rounded">${duration}</span>` : ''}
        <button data-save="${_esc(film.film_id)}" aria-label="Remove from watchlist"
                class="absolute top-1.5 right-1.5 p-1 rounded-full bg-black/50 text-accent transition hover:scale-110">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
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

function _esc(str) {
  return String(str ?? '').replace(/[&<>"']/g, c =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])
  );
}
