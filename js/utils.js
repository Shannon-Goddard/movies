const GRADIENTS = [
  'linear-gradient(135deg,#1a1a2e,#16213e)',
  'linear-gradient(135deg,#0f3460,#533483)',
  'linear-gradient(135deg,#1b1b2f,#2c2c54)',
  'linear-gradient(135deg,#2d132c,#ee4540)',
  'linear-gradient(135deg,#0d0d0d,#1a1a1a)',
  'linear-gradient(135deg,#162447,#1f4068)',
];

export function coverGradient(id) {
  const n = String(id).split('').reduce((a, c) => a + c.charCodeAt(0), 0);
  return GRADIENTS[n % GRADIENTS.length];
}

export function posterThumb(film) {
  if (film.poster_url) {
    return `<img src="${_esc(film.poster_url)}" class="w-full h-full object-cover" alt="" loading="lazy" />`;
  }
  return `
    <div class="w-full h-full flex items-center justify-center"
         style="background:${coverGradient(film.film_id)}">
      <svg width="28" height="28" viewBox="0 0 24 24" fill="rgba(255,255,255,0.2)">
        <path d="M18 3H6a3 3 0 0 0-3 3v12a3 3 0 0 0 3 3h12a3 3 0 0 0 3-3V6a3 3 0 0 0-3-3zM6 5h12a1 1 0 0 1 1 1v1l-3 2-3-2-3 2-3-2V6a1 1 0 0 1 1-1zm13 13a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1v-8l3 2 3-2 3 2 3-2v8z"/>
      </svg>
    </div>`;
}

function _esc(str) {
  return String(str ?? '').replace(/[&<>"']/g, c =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])
  );
}
