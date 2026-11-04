const DATA_URL  = '/movies/data/index.json';
const PAGE_SIZE = 20;

let _catalog = null;

async function loadCatalog() {
  if (_catalog) return _catalog;
  const res = await fetch(DATA_URL);
  if (!res.ok) throw new Error(`Failed to load catalog: ${res.status}`);
  _catalog = await res.json();
  return _catalog;
}

function _page(arr, offset, limit = PAGE_SIZE) {
  const slice = arr.slice(offset, offset + limit);
  return { films: slice, total: arr.length, count: slice.length, offset };
}

function _filter(films, language) {
  return language ? films.filter(f => f.language === language) : films;
}

export async function searchByGenre(genre, limit = PAGE_SIZE, offset = 0, language = '') {
  const all = await loadCatalog();
  const filtered = _filter(all.filter(f => f.genre === genre), language);
  return _page(filtered, offset, limit);
}

export async function searchByType(type, limit = PAGE_SIZE, offset = 0, language = '') {
  const all = await loadCatalog();
  const filtered = _filter(all.filter(f => f.type === type), language);
  return _page(filtered, offset, limit);
}

export async function searchByEra(era, limit = PAGE_SIZE, offset = 0, language = '') {
  const all = await loadCatalog();
  const filtered = _filter(all.filter(f => f.era === era), language);
  return _page(filtered, offset, limit);
}

export async function searchByColor(color, limit = PAGE_SIZE, offset = 0, language = '') {
  const all = await loadCatalog();
  const filtered = _filter(all.filter(f => f.color === color), language);
  return _page(filtered, offset, limit);
}

export async function searchFilms(query, limit = PAGE_SIZE, offset = 0, language = '') {
  const all = await loadCatalog();
  const q = query.toLowerCase();
  const filtered = _filter(
    all.filter(f =>
      f.title?.toLowerCase().includes(q) ||
      f.director?.toLowerCase().includes(q) ||
      f.genre?.toLowerCase().includes(q)
    ),
    language
  );
  return _page(filtered, offset, limit);
}

export async function searchGratefulDead(limit = PAGE_SIZE, offset = 0) {
  const all = await loadCatalog();
  const filtered = all.filter(f => f.title?.toLowerCase().includes('grateful dead'));
  return _page(filtered, offset, limit);
}

export function getStats() {
  if (_catalog) {
    const total = _catalog.length;
    return Promise.resolve({ total_films: total });
  }
  return loadCatalog().then(all => ({ total_films: all.length }));
}

export { PAGE_SIZE };
