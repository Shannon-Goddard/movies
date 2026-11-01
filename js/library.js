const KEY = 'movies_library';

function _load() {
  try { return JSON.parse(localStorage.getItem(KEY)) || []; }
  catch { return []; }
}

function _save(list) {
  localStorage.setItem(KEY, JSON.stringify(list));
}

export function isSaved(film_id) {
  return _load().some(f => f.film_id === film_id);
}

export function toggleSaved(film) {
  let list = _load();
  const exists = list.some(f => f.film_id === film.film_id);
  if (exists) {
    list = list.filter(f => f.film_id !== film.film_id);
  } else {
    list.unshift(film);
  }
  _save(list);
  return !exists;
}

export function getSaved() {
  return _load();
}
