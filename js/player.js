import * as Queue from './queue.js';

const overlay   = document.getElementById('video-overlay');
const videoEl   = document.getElementById('video-el');
const topBar    = document.getElementById('video-top-bar');
const controls  = document.getElementById('video-controls');

// Top bar elements
const btnClose    = document.getElementById('btn-close');
const videoTitle  = document.getElementById('video-title');
const btnCast     = document.getElementById('btn-cast');

// Control elements
const btnPlay     = document.getElementById('btn-play');
const iconPlay    = document.getElementById('icon-play');
const iconPause   = document.getElementById('icon-pause');
const btnPrev     = document.getElementById('btn-prev');
const btnNext     = document.getElementById('btn-next');
const seekEl      = document.getElementById('player-seek');
const currentEl   = document.getElementById('player-current');
const durationEl  = document.getElementById('player-duration');
const volumeEl    = document.getElementById('player-volume');
const btnFullscreen = document.getElementById('btn-fullscreen');
const seekLeft    = document.getElementById('seek-left');
const seekRight   = document.getElementById('seek-right');

let _hideTimer    = null;
let _tapTimer     = null;
let _tapCount     = 0;
let _castSession  = null;

// ── Play ──────────────────────────────────────────────────

export function play(film) {
  if (!film?.stream_url) return;
  videoEl.src    = film.stream_url;
  videoEl.poster = film.poster_url || '';
  videoEl.addEventListener('canplay', () => videoEl.play().catch(() => {}), { once: true });
  videoTitle.textContent = film.title || '';
  document.title = `${film.title} — movies`;
  overlay.classList.add('active');
  _showControls();
  _saveRecent(film);
  _saveSession(film);
  document.dispatchEvent(new CustomEvent('filmchange', { detail: { film_id: film.film_id } }));
}

export function playQueue(films, startIndex = 0) {
  Queue.setQueue(films, startIndex);
  play(Queue.getCurrentFilm());
}

export function playAt(film, positionSec) {
  if (positionSec > 0) {
    videoEl.addEventListener('canplay', () => { videoEl.currentTime = positionSec; }, { once: true });
  }
  play(film);
}

export function togglePlay() {
  if (videoEl.paused) videoEl.play();
  else videoEl.pause();
}

// ── Controls visibility ───────────────────────────────────

function _showControls() {
  overlay.classList.remove('controls-hidden');
  clearTimeout(_hideTimer);
  _hideTimer = setTimeout(_hideControls, 3500);
}

function _hideControls() {
  if (!videoEl.paused) overlay.classList.add('controls-hidden');
}

overlay.addEventListener('click', e => {
  if (e.target === seekEl || e.target === volumeEl) return;
  // Let button clicks inside top bar and controls fire normally
  if (e.target.closest('button')) { _showControls(); return; }
  if (e.target.closest('#video-controls') || e.target.closest('#video-top-bar')) {
    _showControls();
    return;
  }
  // Tap on video area — show controls or handle double-tap seek
  _tapCount++;
  if (_tapCount === 1) {
    _tapTimer = setTimeout(() => {
      _tapCount = 0;
      // Single tap — toggle controls
      overlay.classList.contains('controls-hidden') ? _showControls() : _hideControls();
    }, 250);
  } else if (_tapCount === 2) {
    clearTimeout(_tapTimer);
    _tapCount = 0;
    // Double tap — seek ±10s based on side
    const x = e.clientX / window.innerWidth;
    if (x < 0.35) {
      videoEl.currentTime = Math.max(0, videoEl.currentTime - 10);
      _flashZone(seekLeft, '-10s');
    } else if (x > 0.65) {
      videoEl.currentTime = Math.min(videoEl.duration || 0, videoEl.currentTime + 10);
      _flashZone(seekRight, '+10s');
    }
    _showControls();
  }
});

function _flashZone(el, label) {
  el.textContent = label;
  el.classList.add('flash');
  setTimeout(() => el.classList.remove('flash'), 600);
}

// ── Video events ──────────────────────────────────────────

videoEl.addEventListener('play',  () => { _setPlaying(true);  _showControls(); });
videoEl.addEventListener('pause', () => { _setPlaying(false); _showControls(); });
videoEl.addEventListener('ended', () => _onNext());
videoEl.addEventListener('error', () => { console.warn('Video error — skipping'); _onNext(); });

videoEl.addEventListener('timeupdate', () => {
  if (!videoEl.duration) return;
  const pct = (videoEl.currentTime / videoEl.duration) * 100;
  seekEl.value = pct;
  currentEl.textContent  = _fmt(videoEl.currentTime);
  durationEl.textContent = _fmt(videoEl.duration);
});

// Position persistence every 10s
setInterval(() => {
  if (!videoEl.paused && videoEl.currentTime > 0) Queue.savePosition(videoEl.currentTime);
}, 10000);

function _setPlaying(playing) {
  iconPlay.classList.toggle('hidden', playing);
  iconPause.classList.toggle('hidden', !playing);
}

// ── Controls wiring ───────────────────────────────────────

btnPlay.addEventListener('click', () => { togglePlay(); _showControls(); });
btnNext.addEventListener('click', _onNext);
btnPrev.addEventListener('click', _onPrev);

seekEl.addEventListener('input', () => {
  if (videoEl.duration) videoEl.currentTime = (seekEl.value / 100) * videoEl.duration;
  _showControls();
});

volumeEl.addEventListener('input', () => { videoEl.volume = volumeEl.value; });

btnClose.addEventListener('click', () => {
  videoEl.pause();
  videoEl.src = '';
  overlay.classList.remove('active');
  document.title = 'Movies';
});

btnFullscreen.addEventListener('click', () => {
  if (!document.fullscreenElement) {
    overlay.requestFullscreen?.() || overlay.webkitRequestFullscreen?.();
  } else {
    document.exitFullscreen?.() || document.webkitExitFullscreen?.();
  }
});

// ── Next / Prev ───────────────────────────────────────────

function _onNext() {
  const film = Queue.next();
  if (film) play(film);
}

function _onPrev() {
  if (videoEl.currentTime > 3) { videoEl.currentTime = 0; return; }
  const film = Queue.prev();
  if (film) play(film);
}

// ── Google Cast ───────────────────────────────────────────
// Cast SDK loads async via script tag in index.html.
// When available, window.__onGCastApiAvailable fires and we init here.
// REPLACE_WITH_CAST_APP_ID: register at https://cast.google.com/publish

window['__onGCastApiAvailable'] = function(isAvailable) {
  if (!isAvailable) return;
  cast.framework.CastContext.getInstance().setOptions({
    receiverApplicationId: '20706015',
    autoJoinPolicy: chrome.cast.AutoJoinPolicy.ORIGIN_SCOPED,
  });
  btnCast.classList.remove('hidden');
};

btnCast.addEventListener('click', async () => {
  const ctx = cast.framework.CastContext.getInstance();
  const state = ctx.getCastState();
  if (state === cast.framework.CastState.NO_DEVICES_AVAILABLE) return;

  if (_castSession) {
    _castSession.endSession(true);
    _castSession = null;
    btnCast.classList.remove('text-accent');
    return;
  }

  try {
    await ctx.requestSession();
    _castSession = ctx.getCurrentSession();
    const film = Queue.getCurrentFilm();
    if (!film) return;

    const mediaInfo = new chrome.cast.media.MediaInfo(film.stream_url, 'video/mp4');
    mediaInfo.metadata = new chrome.cast.media.MovieMediaMetadata();
    mediaInfo.metadata.title  = film.title || '';
    mediaInfo.metadata.images = film.poster_url
      ? [new chrome.cast.Image(film.poster_url)]
      : [];

    const request = new chrome.cast.media.LoadRequest(mediaInfo);
    request.currentTime = videoEl.currentTime;
    await _castSession.loadMedia(request);

    videoEl.pause();
    btnCast.classList.add('text-accent');
  } catch (e) {
    console.warn('Cast error:', e);
  }
});

// ── Keyboard shortcuts ────────────────────────────────────

document.addEventListener('keydown', e => {
  if (!overlay.classList.contains('active')) return;
  if (e.target.tagName === 'INPUT') return;
  switch (e.key) {
    case ' ':          e.preventDefault(); togglePlay(); break;
    case 'ArrowRight': e.preventDefault(); videoEl.currentTime = Math.min((videoEl.currentTime + 10), videoEl.duration || 0); break;
    case 'ArrowLeft':  e.preventDefault(); videoEl.currentTime = Math.max(videoEl.currentTime - 10, 0); break;
    case 'ArrowUp':    e.preventDefault(); videoEl.volume = Math.min(videoEl.volume + 0.1, 1); break;
    case 'ArrowDown':  e.preventDefault(); videoEl.volume = Math.max(videoEl.volume - 0.1, 0); break;
    case 'f': case 'F': btnFullscreen.click(); break;
    case 'Escape':     btnClose.click(); break;
  }
  _showControls();
});

// ── Media Session API ─────────────────────────────────────

function _updateMediaSession(film) {
  if (!('mediaSession' in navigator)) return;
  navigator.mediaSession.metadata = new MediaMetadata({
    title:  film.title || '',
    artist: film.director || '',
    artwork: film.poster_url ? [{ src: film.poster_url, sizes: '512x512', type: 'image/jpeg' }] : [],
  });
  navigator.mediaSession.setActionHandler('play',  () => videoEl.play());
  navigator.mediaSession.setActionHandler('pause', () => videoEl.pause());
  navigator.mediaSession.setActionHandler('nexttrack', _onNext);
  navigator.mediaSession.setActionHandler('previoustrack', _onPrev);
  navigator.mediaSession.setActionHandler('seekto', d => { videoEl.currentTime = d.seekTime; });
}

// ── Helpers ───────────────────────────────────────────────

function _fmt(sec) {
  if (!sec || isNaN(sec)) return '0:00';
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = Math.floor(sec % 60).toString().padStart(2, '0');
  return h > 0 ? `${h}:${m.toString().padStart(2,'0')}:${s}` : `${m}:${s}`;
}

function _saveRecent(film) {
  try {
    const KEY = 'movies_recent';
    let list = JSON.parse(localStorage.getItem(KEY)) || [];
    list = list.filter(f => f.film_id !== film.film_id);
    list.unshift(film);
    localStorage.setItem(KEY, JSON.stringify(list.slice(0, 20)));
  } catch { /* storage full */ }
}

function _saveSession(film) {
  Queue.savePosition(0);
}
