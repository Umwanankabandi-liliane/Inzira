const InziraApi = (() => {
  const STORAGE_KEY = 'inzira_api_base';

  function baseUrl() {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) return saved.replace(/\/$/, '');
    return window.location.origin.replace(/\/$/, '');
  }

  function setBaseUrl(url) {
    localStorage.setItem(STORAGE_KEY, url.replace(/\/$/, ''));
  }

  function authToken() {
    return (window.__inziraAuthToken || sessionStorage.getItem('inzira_id_token') || '').trim();
  }

  async function refreshAuthToken() {
    const fb = window.firebase;
    const user = fb?.auth?.()?.currentUser;
    if (!user) return '';
    try {
      const fresh = await user.getIdToken(true);
      window.__inziraAuthToken = fresh;
      sessionStorage.setItem('inzira_id_token', fresh);
      if (typeof window.__inziraSetAuthToken === 'function') {
        window.__inziraSetAuthToken(fresh);
      }
      return fresh;
    } catch (_) {
      return authToken();
    }
  }

  async function request(path, options = {}, retried = false) {
    const url = `${baseUrl()}${path}`;
    const token = authToken();
    const res = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(options.headers || {}),
      },
      ...options,
    });
    if (res.status === 401 && !retried) {
      const fresh = await refreshAuthToken();
      if (fresh) {
        return request(path, options, true);
      }
    }
    if (!res.ok) {
      let body = null;
      try { body = await res.json(); } catch (_) {}
      const detail = typeof body?.detail === 'string'
        ? body.detail
        : (body?.detail ? JSON.stringify(body.detail) : '');
      const err = new Error(detail || `Request failed: ${res.status}`);
      err.status = res.status;
      err.body = body;
      throw err;
    }
    return res.json();
  }

  return {
    baseUrl,
    setBaseUrl,
    refreshAuthToken,
    health: () => request('/health'),
    appConfig: () => request('/app/config'),
    search: (query, category = null, district = null, maxResults = 25) =>
      request('/search', {
        method: 'POST',
        body: JSON.stringify({
          query,
          category: category || undefined,
          max_results: maxResults,
          district: district || undefined,
        }),
      }),
    searchStart: (query, category = null, district = null, maxResults = 25) =>
      request('/search/start', {
        method: 'POST',
        body: JSON.stringify({
          query,
          category: category || undefined,
          max_results: maxResults,
          district: district || undefined,
        }),
      }),
    searchJob: (jobId) => request(`/search/job/${encodeURIComponent(jobId)}`),
    async searchWithProgress(query, category = null, district = null, maxResults = 25, onProgress = null, onPartial = null) {
      const start = await this.searchStart(query, category, district, maxResults);
      const jobId = start.job_id;
      const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
      let partialShown = false;
      for (let i = 0; i < 60; i += 1) {
        const status = await this.searchJob(jobId);
        if (typeof onProgress === 'function') onProgress(status);
        if (status.partial_ready && status.partial_result && !partialShown) {
          partialShown = true;
          if (typeof onPartial === 'function') onPartial(status.partial_result);
        }
        if (status.done) {
          if (status.error) {
            const err = new Error(status.error);
            err.status = 500;
            throw err;
          }
          return status.result;
        }
        await sleep(partialShown ? 500 : 250);
      }
      throw new Error('Search timed out — try again');
    },
    assistant: (message, language = 'english') =>
      request('/assistant', {
        method: 'POST',
        body: JSON.stringify({ message, language }),
      }),
    mifotraConfig: () => request('/mifotra/staff-config'),
    mifotraLogin: (email, password) =>
      request('/mifotra/verify-staff', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      }),
    mifotraDashboard: (token, days = 30) =>
      request(`/mifotra/dashboard?days=${days}`, {
        headers: { 'X-Mifotra-Token': token },
      }),
    registryStats: () => request('/registry/stats'),
    registryOpportunities: (limit = 200, category = null, district = null, q = '') => {
      const params = new URLSearchParams({ limit: String(limit) });
      if (category) params.set('category', category);
      if (district) params.set('district', district);
      if (q) params.set('q', q);
      return request(`/registry/opportunities?${params}`);
    },
    registryWebsites: (limit = 200, category = null) => {
      const params = new URLSearchParams({ limit: String(limit) });
      if (category) params.set('category', category);
      return request(`/registry/websites?${params}`);
    },
    youthMatches: (profile, limit = 30, category = null) => {
      const params = new URLSearchParams({ limit: String(limit) });
      if (category) params.set('category', category);
      return request(`/youth/matches?${params}`, {
        method: 'POST',
        body: JSON.stringify(profile),
      });
    },
    youthRadar: () => request('/youth/radar'),
    youthPathways: () => request('/youth/pathways'),
    youthImpact: () => request('/youth/impact'),
    youthGapMap: () => request('/youth/gap-map'),
    youthEligibility: (opportunity, profile) =>
      request('/youth/eligibility', {
        method: 'POST',
        body: JSON.stringify({ opportunity, profile }),
      }),
    me: () => request('/me'),
    updateProfile: (profile) =>
      request('/me/profile', { method: 'PUT', body: JSON.stringify(profile) }),
    deleteAccount: () => request('/me', { method: 'DELETE' }),
    savedList: () => request('/me/saved'),
    savedAdd: (site) =>
      request('/me/saved', { method: 'POST', body: JSON.stringify(site) }),
    savedRemove: (domain) =>
      request(`/me/saved/${encodeURIComponent(domain)}`, { method: 'DELETE' }),
    savedNotify: (domain, enabled) =>
      request(`/me/saved/${encodeURIComponent(domain)}/notify`, {
        method: 'PUT',
        body: JSON.stringify({ enabled: !!enabled }),
      }),
    alertCheck: (limit = 6) => request(`/me/alerts/check?limit=${limit}`),
    vapidPublicKey: () => request('/push/vapid-public-key'),
    pushSubscribe: (subscription) =>
      request('/me/push/subscribe', { method: 'POST', body: JSON.stringify(subscription) }),
    pushUnsubscribe: (endpoint) =>
      request('/me/push/unsubscribe', {
        method: 'DELETE',
        body: JSON.stringify({ endpoint }),
      }),
    adminStats: () => request('/admin/stats'),
    adminUsers: (limit = 50) => request(`/admin/users?limit=${limit}`),
  };
})();
