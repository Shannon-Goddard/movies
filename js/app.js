import './player.js';
import { render as renderHome }    from './views/home.js';
import { render as renderSearch }  from './views/search.js';
import { render as renderLibrary } from './views/library.js';

const app = document.getElementById('app');

// ── Router ────────────────────────────────────────────────

async function route() {
  const hash = location.hash || '#/';
  const [path, ...rest] = hash.slice(1).split('?');
  const params = Object.fromEntries(new URLSearchParams(rest.join('?')));

  if (document.startViewTransition) {
    document.startViewTransition(() => _dispatch(path, params));
  } else {
    _dispatch(path, params);
  }
}

async function _dispatch(path, params) {
  app.innerHTML = '';

  document.querySelectorAll('.nav-link, .bottom-nav-item').forEach(el => {
    const href = el.getAttribute('href');
    el.classList.toggle('active', href === `#${path}` || (href === '#/' && (path === '/' || path === '')));
  });

  if (path === '/' || path === '') {
    await renderHome(app);
  } else if (path === '/search') {
    await renderSearch(app, params.q || '');
  } else if (path === '/library') {
    renderLibrary(app);
  } else {
    app.innerHTML = `<p class="text-white/50 mt-12 text-center">Page not found.</p>`;
  }
}

// ── Search form ───────────────────────────────────────────

document.getElementById('search-form').addEventListener('submit', e => {
  e.preventDefault();
  const q = document.getElementById('search-input').value.trim();
  if (q) location.hash = `#/search?q=${encodeURIComponent(q)}`;
});

// ── Service Worker ────────────────────────────────────────

if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/movies/service-worker.js')
    .catch(e => console.warn('SW registration failed:', e));
}

// ── Back to top ───────────────────────────────────────────

const backToTop = document.getElementById('back-to-top');
window.addEventListener('scroll', () => {
  backToTop.classList.toggle('visible', window.scrollY > 300);
}, { passive: true });
backToTop.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));

// ── Now playing row indicator ─────────────────────────────

document.addEventListener('filmchange', e => {
  document.querySelectorAll('[data-film-id]').forEach(row => {
    row.classList.toggle('now-playing', row.dataset.filmId === e.detail.film_id);
  });
});

// ── Boot ──────────────────────────────────────────────────

window.addEventListener('hashchange', route);
route();
