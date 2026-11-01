import { PAGE_SIZE } from './api.js';

export class InfiniteScroll {
  constructor({ listEl, statusEl, fetchFn, renderFn }) {
    this._listEl   = listEl;
    this._statusEl = statusEl;
    this._fetchFn  = fetchFn;
    this._renderFn = renderFn;
    this._offset   = 0;
    this._loading  = false;
    this._done     = false;
    this._observer = null;
  }

  start() {
    this._load();
    this._observe();
  }

  destroy() {
    this._observer?.disconnect();
    this._done = true;
  }

  async _load() {
    if (this._loading || this._done) return;
    this._loading = true;
    try {
      const data   = await this._fetchFn(this._offset);
      const films  = data.films || data.tracks || data.results || [];
      this._renderFn(films, this._offset);
      this._offset += films.length;
      if (films.length < PAGE_SIZE) {
        this._done = true;
        if (this._statusEl) this._statusEl.textContent = '';
      }
    } catch (e) {
      if (this._statusEl) this._statusEl.textContent = 'Failed to load. Try again.';
    } finally {
      this._loading = false;
    }
  }

  _observe() {
    if (!('IntersectionObserver' in window)) return;
    const sentinel = document.createElement('div');
    sentinel.style.height = '1px';
    this._listEl.after(sentinel);
    this._observer = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting) this._load();
    }, { rootMargin: '200px' });
    this._observer.observe(sentinel);
  }
}
