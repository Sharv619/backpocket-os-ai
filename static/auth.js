/**
 * BackPocket Auth Helper
 * - Reads api_key from URL params or localStorage, saves it
 * - Patches window.fetch to inject ?api_key= on all /api/ and /admin/api/ calls
 * - Redirects to /login if no credential is found
 */
(function () {
  const STORAGE_KEY = 'bp_api_key';
  const TOKEN_KEY   = 'bp_token';

  // 1. Pick up key from URL param (e.g. bookmarked link with ?api_key=xxx)
  const urlParams = new URLSearchParams(window.location.search);
  const paramKey  = urlParams.get('api_key');
  if (paramKey) {
    localStorage.setItem(STORAGE_KEY, paramKey);
    // Clean the key out of the visible URL without reloading
    urlParams.delete('api_key');
    const clean = [window.location.pathname, urlParams.toString()].filter(Boolean).join('?');
    history.replaceState(null, '', clean);
  }

  const apiKey = localStorage.getItem(STORAGE_KEY);
  const token  = localStorage.getItem(TOKEN_KEY);

  // 2. Redirect to login if no credential at all
  if (!apiKey && !token) {
    const next = encodeURIComponent(window.location.pathname + window.location.search);
    window.location.href = '/login?next=' + next;
    return;
  }

  // 3. Patch fetch — inject credentials on API calls
  const _origFetch = window.fetch.bind(window);
  window.fetch = function (input, init) {
    let url = typeof input === 'string' ? input : (input instanceof Request ? input.url : String(input));

    const isApiCall = url.startsWith('/api/') || url.startsWith('/admin/api/');
    if (isApiCall) {
      if (token) {
        // JWT mode — send as Authorization header
        init = init || {};
        init.headers = Object.assign({}, init.headers || {}, {
          'Authorization': 'Bearer ' + token,
        });
      } else if (apiKey) {
        // API-key mode — append as query param
        const sep = url.includes('?') ? '&' : '?';
        url = url + sep + 'api_key=' + encodeURIComponent(apiKey);
      }
    }

    const newInput = typeof input === 'string' ? url : input;
    return _origFetch(newInput, init);
  };

  // 4. Global logout helper — call BPAuth.logout() from any page
  window.BPAuth = {
    logout() {
      localStorage.removeItem(STORAGE_KEY);
      localStorage.removeItem(TOKEN_KEY);
      window.location.href = '/login';
    },
    getKey()   { return apiKey; },
    getToken() { return token; },
  };
})();
