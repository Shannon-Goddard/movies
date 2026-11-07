import { getSeriesMap, getSeriesEpisodes } from '../api.js';
import { playQueue } from '../player.js';
import { posterThumb } from '../utils.js';

export async function renderSeries(app) {
  app.innerHTML = `<p class="text-white/30 text-sm text-center py-12">Loading series…</p>`;
  const map = await getSeriesMap();

  // Sort by episode count desc
  const series = [...map.entries()]
    .map(([name, eps]) => ({ name, eps, count: eps.length, year: eps[0]?.year || '' }))
    .sort((a, b) => b.count - a.count);

  app.innerHTML = `
    <h2 class="text-base font-semibold mb-4">Series <span class="text-white/30 font-normal text-sm">${series.length}</span></h2>
    <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4" id="series-grid">
      ${series.map(s => _seriesCard(s)).join('')}
    </div>`;

  app.querySelector('#series-grid').addEventListener('click', e => {
    const card = e.target.closest('[data-series]');
    if (card) renderEpisodes(app, decodeURIComponent(card.dataset.series));
  });
}

export async function renderEpisodes(app, seriesName) {
  app.innerHTML = `<p class="text-white/30 text-sm text-center py-12">Loading…</p>`;
  const eps = await getSeriesEpisodes(seriesName);

  app.innerHTML = `
    <div class="flex items-center gap-3 mb-5">
      <button id="btn-back-series" class="text-white/40 hover:text-white transition">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
      </button>
      <div class="min-w-0">
        <h2 class="text-base font-semibold truncate">${_esc(seriesName)}</h2>
        <p class="text-xs text-white/30">${eps.length} episode${eps.length !== 1 ? 's' : ''}</p>
      </div>
      <button id="btn-play-series"
              class="ml-auto shrink-0 flex items-center gap-1.5 text-sm font-medium text-accent hover:opacity-80 transition">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
        Play all
      </button>
    </div>
    <div class="flex flex-col gap-2" id="ep-list">
      ${eps.map((f, i) => _epRow(f, i)).join('')}
    </div>`;

  app.querySelector('#btn-back-series').addEventListener('click', () => renderSeries(app));
  app.querySelector('#btn-play-series').addEventListener('click', () => playQueue(eps, 0));

  app.querySelector('#ep-list').addEventListener('click', e => {
    const row = e.target.closest('[data-ep-index]');
    if (row) playQueue(eps, parseInt(row.dataset.epIndex));
  });
}

function _seriesCard(s) {
  const thumb = s.eps[0];
  return `
    <div data-series="${_esc(encodeURIComponent(s.name))}"
         class="card bg-card rounded-lg overflow-hidden cursor-pointer hover:bg-raised transition"
         style="border:1px solid rgba(255,255,255,0.06)">
      <div class="relative aspect-[2/3] overflow-hidden">
        ${posterThumb(thumb)}
        <span class="absolute bottom-1.5 right-1.5 text-[10px] tabular-nums bg-black/70 text-white/80 px-1.5 py-0.5 rounded">
          ${s.count} eps
        </span>
      </div>
      <div class="p-2">
        <p class="text-xs font-medium truncate leading-tight">${_esc(s.name)}</p>
        <p class="text-[10px] text-white/35 truncate mt-0.5">${s.year || ''}</p>
      </div>
    </div>`;
}

function _epRow(film, index) {
  const s = film.season_num ? `S${film.season_num}` : '';
  const e = film.episode_num ? `E${film.episode_num}` : '';
  const badge = s || e ? `${s}${e}` : `#${index + 1}`;
  const dur = film.duration_sec ? _fmt(film.duration_sec) : '';
  return `
    <div data-ep-index="${index}" data-film-id="${_esc(film.film_id)}"
         class="flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-pointer hover:bg-raised transition"
         style="border:1px solid rgba(255,255,255,0.05)">
      <div class="w-16 h-10 rounded overflow-hidden shrink-0">${posterThumb(film)}</div>
      <div class="min-w-0 flex-1">
        <p class="text-xs font-medium truncate">${_esc(film.title)}</p>
        <p class="text-[10px] text-white/35 mt-0.5">${badge}${dur ? ` · ${dur}` : ''}</p>
      </div>
      <svg class="shrink-0 text-white/20" width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
    </div>`;
}

function _fmt(sec) {
  sec = parseFloat(sec);
  if (isNaN(sec)) return '';
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = Math.floor(sec % 60).toString().padStart(2, '0');
  return h > 0 ? `${h}:${m.toString().padStart(2, '0')}:${s}` : `${m}:${s}`;
}

function _esc(str) {
  return String(str ?? '').replace(/[&<>\"']/g, c =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])
  );
}
