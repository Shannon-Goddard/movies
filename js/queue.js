const STORAGE_KEY = 'movies_queue';
const SESSION_KEY = 'movies_session';

let queue = [];
let currentIndex = 0;

export function setQueue(films, startIndex = 0) {
  queue = films;
  currentIndex = startIndex;
  _persist();
}

export function getQueue()        { return queue; }
export function getCurrentIndex() { return currentIndex; }
export function getCurrentFilm()  { return queue[currentIndex] || null; }

export function next() {
  if (currentIndex < queue.length - 1) { currentIndex++; _persist(); return getCurrentFilm(); }
  return null;
}

export function prev() {
  if (currentIndex > 0) { currentIndex--; _persist(); return getCurrentFilm(); }
  return null;
}

export function random() {
  if (!queue.length) return null;
  currentIndex = Math.floor(Math.random() * queue.length);
  _persist();
  return getCurrentFilm();
}

export function savePosition(positionSec) {
  const film = getCurrentFilm();
  if (!film) return;
  localStorage.setItem(SESSION_KEY, JSON.stringify({
    film_id: film.film_id,
    position_sec: positionSec,
    film,
  }));
}

export function loadSession() {
  try { return JSON.parse(localStorage.getItem(SESSION_KEY)) || {}; }
  catch { return {}; }
}

export function clearSession() {
  localStorage.removeItem(SESSION_KEY);
  localStorage.removeItem(STORAGE_KEY);
}

function _persist() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify({ queue, currentIndex }));
}

// Restore queue on module load
try {
  const saved = JSON.parse(localStorage.getItem(STORAGE_KEY));
  if (saved?.queue?.length) { queue = saved.queue; currentIndex = saved.currentIndex || 0; }
} catch { /* ignore */ }
