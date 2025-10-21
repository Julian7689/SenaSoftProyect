
(function () {
  const CREDENTIALS = [
    { username: 'admin', password: 'admin123', role: 'admin', redirect: '/admin' },
    { username: 'usuario', password: 'usuario123', role: 'usuario', redirect: '/' },
  ];

  const STORAGE_KEY = 'boti_auth';

  function getStorage(remember) {
    return remember ? window.localStorage : window.sessionStorage;
  }

  function getExistingAuth() {
    try {
      const ls = localStorage.getItem(STORAGE_KEY);
      const ss = sessionStorage.getItem(STORAGE_KEY);
      const raw = ls || ss;
      return raw ? JSON.parse(raw) : null;
    } catch (e) {
      return null;
    }
  }

  function setAuth(data, remember) {
    // Clear both to avoid conflicts
    try { localStorage.removeItem(STORAGE_KEY); } catch {}
    try { sessionStorage.removeItem(STORAGE_KEY); } catch {}

    const storage = getStorage(remember);
    storage.setItem(STORAGE_KEY, JSON.stringify({
      ...data,
      ts: new Date().toISOString(),
    }));
  }

  function showError(msg) {
    const el = document.getElementById('auth-error');
    if (!el) return;
    el.textContent = msg;
    el.style.display = 'block';
    el.classList.add('visible');
  }

  function hideError() {
    const el = document.getElementById('auth-error');
    if (!el) return;
    el.textContent = '';
    el.style.display = 'none';
    el.classList.remove('visible');
  }

  function matchCredentials(username, password) {
    return CREDENTIALS.find(c => c.username === username && c.password === password) || null;
  }

  function redirectTo(path) {
    // Use location.replace to avoid going back to login with back button
    window.location.replace(path);
  }

  // If already authenticated, redirect to the appropriate view right away
  document.addEventListener('DOMContentLoaded', () => {
    const existing = getExistingAuth();
    if (existing && existing.redirect) {
      // Optional: only auto-redirect if we're on the login page path
      if (window.location.pathname.toLowerCase().includes('login')) {
        redirectTo(existing.redirect);
        return;
      }
    }

    const form = document.getElementById('login-form');
    if (!form) return;

    form.addEventListener('submit', (e) => {
      e.preventDefault();
      hideError();

      const usernameEl = document.getElementById('username');
      const passwordEl = document.getElementById('password');
      const rememberEl = document.getElementById('remember');

      const username = (usernameEl?.value || '').trim();
      const password = passwordEl?.value || '';
      const remember = !!rememberEl?.checked;

      const match = matchCredentials(username, password);
      if (!match) {
        showError('Credenciales inválidas. Intenta con: admin/admin123 o usuario/usuario123');
        return;
      }

      setAuth({ username: match.username, role: match.role, redirect: match.redirect }, remember);
      redirectTo(match.redirect);
    });
  });
})();
