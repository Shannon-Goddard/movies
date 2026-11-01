const BASE_URL = 'https://3m0629omkh.execute-api.us-east-1.amazonaws.com/v1';
const PAGE_SIZE = 20;

async function request(path) {
  const response = await fetch(`${BASE_URL}${path}`);
  if (!response.ok) throw new Error(`API error ${response.status} on ${path}`);
  return response.json();
}

/** GET /films/search?q={query}&limit={n}&offset={n} */
export function searchFilms(query, limit = PAGE_SIZE, offset = 0) {
  return request(`/films/search?q=${encodeURIComponent(query)}&limit=${limit}&offset=${offset}`);
}

/** GET /films/search?genre={genre}&limit={n}&offset={n} */
export function searchByGenre(genre, limit = PAGE_SIZE, offset = 0) {
  return request(`/films/search?genre=${encodeURIComponent(genre)}&limit=${limit}&offset=${offset}`);
}

/** GET /films/search?type={type}&limit={n}&offset={n} */
export function searchByType(type, limit = PAGE_SIZE, offset = 0) {
  return request(`/films/search?type=${encodeURIComponent(type)}&limit=${limit}&offset=${offset}`);
}

/** GET /films/search?era={era}&limit={n}&offset={n} */
export function searchByEra(era, limit = PAGE_SIZE, offset = 0) {
  return request(`/films/search?era=${encodeURIComponent(era)}&limit=${limit}&offset=${offset}`);
}

/** GET /films/search?color={bw|color}&limit={n}&offset={n} */
export function searchByColor(color, limit = PAGE_SIZE, offset = 0) {
  return request(`/films/search?color=${encodeURIComponent(color)}&limit=${limit}&offset=${offset}`);
}

/** GET /stats */
export function getStats() {
  return request('/stats');
}

export { PAGE_SIZE };
