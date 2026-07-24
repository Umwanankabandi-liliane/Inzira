/* Inzira Web App — SPA matching Android screens */

const APP_BUILD = '131';
const NOTIFY_DOMAINS_KEY = 'inzira_notify_domains';
const ALERT_CHECK_MS = 30 * 60 * 1000;
const ALERT_LAST_KEY = 'inzira_last_alert_check';
let deadlineWatchTimer = null;
let authBootstrapPromise = null;
let authBootstrapped = false;

const APP_TABS = new Set(['home', 'search', 'matches', 'matches-list', 'opportunities', 'assistant', 'followed', 'settings', 'admin', 'sites', 'results', 'detail', 'radar', 'mifotra', 'dashboard']);
const APP_SHELL_ROUTES = APP_TABS;

const DISTRICTS = [
  'Gasabo', 'Kicukiro', 'Nyarugenge', 'Bugesera', 'Gatsibo', 'Kayonza', 'Kirehe',
  'Ngoma', 'Nyagatare', 'Rwamagana', 'Huye', 'Gisagara', 'Nyamagabe', 'Nyanza',
  'Nyaruguru', 'Ruhango', 'Kamonyi', 'Muhanga', 'Karongi', 'Ngororero', 'Nyabihu',
  'Rubavu', 'Rusizi', 'Rutsiro', 'Burera', 'Gakenke', 'Gicumbi', 'Musanze', 'Rulindo',
];

const MATCH_SKILL_FIELDS = [
  'ICT and software',
  'Business',
  'Health',
  'Agriculture',
  'Education',
  'Engineering',
  'Finance',
  'Law',
  'Tourism and hospitality',
  'Creative arts and media',
];

const MATCH_LOOKING_OPTIONS = [
  { id: 'jobs', value: 'job', labelKey: 'cat_job' },
  { id: 'scholarships', value: 'scholarship', labelKey: 'cat_scholarship' },
  { id: 'internships', value: 'internship', labelKey: 'cat_internship' },
  { id: 'trainings', value: 'training', labelKey: 'cat_training' },
  { id: 'programs', value: 'program', labelKey: 'cat_program' },
  { id: 'free_courses', value: 'free_course', labelKey: 'cat_free_course' },
  { id: 'competitions', value: 'competition', labelKey: 'cat_competition' },
];

const OPPORTUNITY_CATEGORIES = [
  { id: 'job', tone: 'green', labelKey: 'cat_job' },
  { id: 'scholarship', tone: 'amber', labelKey: 'cat_scholarship' },
  { id: 'program', tone: 'blue', labelKey: 'cat_program' },
  { id: 'training', tone: 'green', labelKey: 'cat_training' },
  { id: 'internship', tone: 'amber', labelKey: 'cat_internship' },
  { id: 'free_course', tone: 'green', labelKey: 'cat_free_course' },
  { id: 'competition', tone: 'blue', labelKey: 'cat_competition' },
];

function renderCategoryFilterPills(dataAttr, activeValue = '') {
  const chips = [{ id: '', tone: 'blue', labelKey: 'cat_all' }, ...OPPORTUNITY_CATEGORIES];
  return chips.map((c) => `
    <button type="button" class="filter-pill filter-pill--${c.tone}${activeValue === c.id ? ' active' : ''}" data-${dataAttr}="${c.id}">${t(c.labelKey)}</button>
  `).join('');
}

const BAR_COLORS = {
  job: '#1A3A6B',
  free_course: '#2E5FA3',
  competition: '#2E5FA3',
  internship: '#1A3A6B',
  program: '#2E5FA3',
  training: '#1A3A6B',
  scholarship: '#2E5FA3',
};

function ico(name) {
  const icons = {
    bell: '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>',
    user: '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
    search: '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>',
    mail: '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>',
    phone: '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.8 19.8 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.08 4.18 2 2 0 0 1 4.06 2h3a2 2 0 0 1 2 1.72c.12.86.32 1.7.58 2.5a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.58-1.1a2 2 0 0 1 2.11-.45c.8.26 1.64.46 2.5.58A2 2 0 0 1 22 16.92z"/></svg>',
    lock: '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>',
    eye: '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>',
    home: '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
    bookmark: '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m19 21-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>',
    settings: '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>',
    chat: '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4z"/></svg>',
    bot: '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="10" rx="2"/><circle cx="12" cy="5" r="2"/><path d="M12 7v4"/><line x1="8" y1="16" x2="8" y2="16"/><line x1="16" y1="16" x2="16" y2="16"/></svg>',
    send: '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>',
    arrow: '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>',
    back: '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>',
    check: '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>',
    external: '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>',
    share: '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>',
    calendar: '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>',
    trash: '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>',
    logo: '<svg class="ico ico--logo" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="5" y="2" width="14" height="20" rx="2"/><line x1="12" y1="18" x2="12" y2="18.01"/></svg>',
    google: '<svg class="ico" viewBox="0 0 24 24"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>',
    spark: '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3l1.5 5.5L19 10l-5.5 1.5L12 17l-1.5-5.5L5 10l5.5-1.5z"/></svg>',
    shield: '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
    logout: '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>',
    world: '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>',
    download: '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>',
    menu: '<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>',
  };
  return icons[name] || '';
}

function defaultRoute() {
  if (!localStorage.getItem('inzira_onboarded')) return 'language';
  // Web-first: allow guest search without login (login needed for Saved/Alerts/Matches).
  return 'home';
}

function profilePayload() {
  const u = state.user || {};
  const parseList = (val) => {
    if (Array.isArray(val)) return val.map((s) => String(s).trim()).filter(Boolean);
    const raw = String(val || '').trim();
    if (!raw) return [];
    if (raw.startsWith('[')) {
      try {
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed)) return parsed.map((s) => String(s).trim()).filter(Boolean);
      } catch (_) {}
    }
    return raw.split(/[,;|]+/).map((s) => s.trim()).filter(Boolean);
  };
  return {
    name: u.name || '',
    district: u.district || '',
    age: u.age || '',
    education: u.education || '',
    skills: parseList(u.skills),
    interests: parseList(u.interests),
  };
}

function emptyCategoryMessage(category) {
  const c = String(category || '').toLowerCase().trim();
  const map = {
    training: 'empty_cat_training',
    scholarship: 'empty_cat_scholarship',
    program: 'empty_cat_program',
    internship: 'empty_cat_internship',
    free_course: 'empty_cat_free_course',
    job: 'empty_cat_job',
    competition: 'empty_cat_competition',
  };
  return t(map[c] || 'empty_cat_generic');
}

function districtFallbackBanner(districtName) {
  const name = districtName || t('rwanda');
  return `<div class="info-banner info-banner--amber" role="status">${esc(t('district_fallback_msg', { district: name }))}</div>`;
}

function formatTrustDisplay(score) {
  return `${trustPercent(score)}%`;
}

function isMatchProfileReady(user = state.user) {
  const u = user || {};
  return !!(u.district && u.education && u.skills);
}

function normalizeMatchEducation(value) {
  const v = String(value || '').trim();
  const opts = ['High school', 'Diploma', "Bachelor's degree", "Master's degree"];
  if (opts.includes(v)) return v;
  return '';
}

function normalizeMatchSkill(value) {
  const v = String(value || '').trim();
  if (MATCH_SKILL_FIELDS.includes(v)) return v;
  const s = v.toLowerCase();
  if (s.includes('ict') || s.includes('software') || s.includes('tech')) return 'ICT and software';
  if (s.includes('business')) return 'Business';
  if (s.includes('health') || s.includes('medic')) return 'Health';
  if (s.includes('agri')) return 'Agriculture';
  if (s.includes('educ') || s.includes('teach')) return 'Education';
  if (s.includes('engineer')) return 'Engineering';
  if (s.includes('financ') || s.includes('account')) return 'Finance';
  if (s.includes('law') || s.includes('legal')) return 'Law';
  if (s.includes('tour') || s.includes('hospitality')) return 'Tourism and hospitality';
  if (s.includes('art') || s.includes('media') || s.includes('creative')) return 'Creative arts and media';
  return MATCH_SKILL_FIELDS.find((o) => o.toLowerCase() === s) || '';
}

function resolveLookingPick(interests) {
  const s = String(interests || '').toLowerCase();
  const hit = MATCH_LOOKING_OPTIONS.find((o) => s.includes(o.value) || s.includes(o.id));
  return hit?.id || 'jobs';
}

function mapLookingInterest(pillId) {
  const opt = MATCH_LOOKING_OPTIONS.find((o) => o.id === pillId);
  return opt?.value || 'job';
}

function normalizeLookingInterest(value) {
  return resolveLookingPick(value);
}

function profileCompletenessPct() {
  return state.profileCompleteness ?? 0;
}

function competitionLabel(level) {
  if (level === 'low') return t('competition_low');
  if (level === 'high') return t('competition_high');
  return t('competition_medium');
}

function competitionClass(level) {
  if (level === 'low') return 'match-tag--comp-low';
  if (level === 'high') return 'match-tag--comp-high';
  return 'match-tag--comp-medium';
}

function shellNavKey(path) {
  if (path === 'search' || path === 'radar') return 'home';
  if (path === 'matches-list') return 'matches';
  if (path === 'sites' || path === 'results' || path === 'detail' || path === 'opportunities') return 'home';
  if (path === 'mifotra' || path === 'dashboard') return state.mifotraToken ? 'dashboard' : 'mifotra';
  return path;
}

function renderAppHeader(active) {
  const savedN = (state.followed || []).length;
  const navItems = [
    { id: 'home', label: t('nav_dashboard') },
    { id: 'matches', label: t('nav_matches') },
    { id: 'assistant', label: t('nav_assistant') },
    { id: 'followed', label: t('nav_saved'), badge: savedN || null },
  ];
  const navLinks = navItems.map((item) => `
    <button type="button" class="inzira-topnav__link${active === item.id ? ' active' : ''}" data-go="${item.id}">
      <span>${esc(item.label)}</span>${item.badge ? `<span class="inzira-topnav__badge">${item.badge}</span>` : ''}
    </button>`).join('');

  return `
    <header class="inzira-topheader inzira-topheader--nav">
      <div class="inzira-topheader__inner">
        <button type="button" class="inzira-topheader__brand" data-go="home" aria-label="INZIRA home">
          <span class="inzira-topheader__logo">I</span>
          <span class="inzira-topheader__wordmark">INZIRA</span>
        </button>
        <nav class="inzira-topnav" aria-label="Main navigation">${navLinks}</nav>
        <div class="inzira-topheader__actions">
          <button type="button" class="inzira-topheader__icon" data-go="settings" aria-label="${esc(t('nav_settings'))}">${ico('user')}</button>
          <button type="button" class="inzira-topheader__menu" id="btnMobileNavToggle" aria-label="Menu">${ico('menu')}</button>
        </div>
      </div>
      <nav class="inzira-topnav inzira-topnav--drawer" id="mobileTopNav" aria-label="Mobile navigation" hidden>${navLinks}</nav>
    </header>`;
}

function renderSidebar(active) {
  return '';
}

function handleDownloadApp(e) {
  e?.preventDefault();
  const url = window.INZIRA_APK_URL;
  if (!url) {
    toast(t('download_app_soon'));
    return;
  }
  try {
    const resolved = new URL(url, window.location.origin);
    if (resolved.origin === window.location.origin) {
      const a = document.createElement('a');
      a.href = resolved.href;
      a.download = 'inzira.apk';
      a.rel = 'noopener';
      document.body.appendChild(a);
      a.click();
      a.remove();
      toast(t('download_app_started'));
      return;
    }
  } catch (_) {}
  window.open(url, '_blank', 'noopener');
  toast(t('download_app_started'));
}

async function loadAppConfig() {
  try {
    const cfg = await InziraApi.appConfig();
    if (cfg?.apk_url) window.INZIRA_APK_URL = cfg.apk_url;
  } catch (_) {}
}

function bindSidebarUI() {
  const drawer = document.getElementById('mobileTopNav');
  const toggle = () => {
    if (!drawer) return;
    const open = drawer.hasAttribute('hidden');
    if (open) drawer.removeAttribute('hidden');
    else drawer.setAttribute('hidden', '');
  };
  const close = () => drawer?.setAttribute('hidden', '');
  document.getElementById('btnMobileNavToggle')?.addEventListener('click', toggle);
  drawer?.querySelectorAll('[data-go]').forEach((el) => {
    el.addEventListener('click', () => close());
  });
}

function renderMobileNav(active) {
  return '';
}

function renderInziraShell(content, active) {
  return `
    <div class="inzira-layout inzira-layout--topnav">
      <div class="inzira-layout__main">
        ${renderAppHeader(active)}
        <main class="inzira-main">
          <div class="inzira-main__content">${content}</div>
        </main>
      </div>
    </div>`;
}

function renderAppTopbar({ title, sub, backTo, actionsHtml = '' }) {
  const back = backTo
    ? `<button type="button" class="icon-btn app-topbar-back" data-go="${backTo}" aria-label="Back">${ico('back')}</button>`
    : '';
  return `
    <div class="inzira-topbar inzira-topbar--app">
      <div class="inzira-topbar__left">
        ${back}
        <div>
          <h1>${typeof title === 'string' ? esc(title) : title}</h1>
          ${sub ? `<p class="inzira-topbar__sub">${typeof sub === 'string' ? esc(sub) : sub}</p>` : ''}
        </div>
      </div>
      ${actionsHtml ? `<div class="inzira-topbar__actions">${actionsHtml}</div>` : ''}
    </div>`;
}

function renderAuthShell(content, active) {
  const cardClass = active ? ` app-auth-card--${active}` : '';
  return `
    <div class="app-auth-screen">
      <div class="app-auth-card${cardClass}">
        <div class="app-auth-brand app-auth-brand--compact">
          <span class="app-auth-logo" aria-hidden="true">I</span>
          <div>
            <h1>INZIRA</h1>
            <p>${t('platform_tagline_short')}</p>
          </div>
        </div>
        ${renderAuthNav(active)}
        ${content}
      </div>
    </div>`;
}

function renderInsightsPanel() {
  const insights = state.insights || [];
  return `
    <div class="dash-card dash-card--insights">
      <div class="dash-card__head"><h2>${t('ai_insights')}</h2></div>
      <div class="insights-list" id="insightsList">
        ${insights.length ? insights.map((line) => `<div class="insight-item">${ico('spark')}<span>${esc(line)}</span></div>`).join('') : `<div class="insight-item">${ico('spark')}<span>${t('brand_tip_ai2')}</span></div>`}
      </div>
    </div>`;
}

function renderHowItWorksBanner() {
  if (localStorage.getItem('inzira_how_seen') === '1') return '';
  const steps = [
    [t('step_collect'), t('step_collect_d')],
    [t('step_understand'), t('step_understand_d')],
    [t('step_match'), t('step_match_d')],
    [t('step_alert'), t('step_alert_d')],
    [t('step_succeed'), t('step_succeed_d')],
  ];
  return `
    <section class="dash-card how-banner" id="howBanner" style="margin-top:16px">
      <div class="dash-card__head">
        <h2>${t('how_inzira_works')}</h2>
        <button type="button" class="text-link" id="btnDismissHow">${t('dismiss_how')}</button>
      </div>
      <div class="how-strip how-strip--compact">
        ${steps.map(([title, desc], i) => `
          <div class="how-step"><div class="how-step__num">${i + 1}</div><strong>${esc(title)}</strong><p>${esc(desc)}</p></div>`).join('')}
      </div>
    </section>`;
}

function renderCompactTopMatch(top) {
  if (!top) {
    return `<div class="dash-card top-match-compact top-match-compact--present"><p class="empty">${t('loading_results')}</p></div>`;
  }
  const reasons = (top.match_reasons || []).slice(0, 2);
  return `
    <div class="dash-card top-match-compact top-match-compact--present">
      <p class="top-match-card__eyebrow">${t('top_match')}</p>
      <div class="top-match-present">
        <div class="match-score-ring match-score-ring--present" style="--score:${top.match_score || 0}"><span>${top.match_score || 0}%</span></div>
        <div class="top-match-present__body">
          <h3>${esc(opportunityTitle(top))}</h3>
          <p class="top-match-card__org">${esc(opportunityEmployer(top))}</p>
          <div class="match-tags">
            <span class="match-tag match-tag--cat">${esc(categoryLabel(top.category))}</span>
            <span class="match-tag ${competitionClass(top.competition)}">${esc(competitionLabel(top.competition))}</span>
          </div>
          ${reasons.length ? `<ul class="match-reasons match-reasons--compact">${reasons.map((r) => `<li>${esc(r)}</li>`).join('')}</ul>` : ''}
          <div class="top-match-compact__actions">
            <button type="button" class="btn btn-primary" id="btnTopMatch">${t('apply_now')} ${ico('arrow')}</button>
            <button type="button" class="text-link" data-go="matches">${t('view_all_matches')}</button>
          </div>
        </div>
      </div>
    </div>`;
}

function renderQuickActions() {
  const actions = [
    { go: 'matches', icon: 'spark', label: t('quick_matches'), sub: t('nav_matches') },
    { go: 'assistant', icon: 'bot', label: t('quick_assistant'), sub: t('assistant_title_short') },
    { go: 'followed', icon: 'bookmark', label: t('nav_saved'), sub: t('nav_alerts') },
  ];
  return `
    <div class="dash-card quick-actions-card">
      <div class="dash-card__head"><h2>${t('quick_actions')}</h2></div>
      <div class="quick-actions-grid">
        ${actions.map((a) => `
          <button type="button" class="quick-action-btn" data-go="${a.go}">
            <span class="quick-action-btn__icon">${ico(a.icon)}</span>
            <strong>${esc(a.label)}</strong>
            <span>${esc(a.sub)}</span>
          </button>`).join('')}
      </div>
    </div>`;
}

function densityLabel(level) {
  if (level === 'very_high' || level === 'high') return t('density_high');
  if (level === 'medium') return t('density_medium');
  if (level === 'very_low' || level === 'low') return t('density_low');
  return t('density_medium');
}

function renderRadarPreviewCard() {
  const u = state.user || {};
  const district = u.district || 'Gasabo';
  const radar = state.radarDistricts || [];
  const data = radar.find((d) => d.district === district);
  const total = data?.total;
  const level = data?.level || 'low';
  const bd = data?.breakdown || {};
  const countLabel = total != null
    ? t('radar_preview_count', { n: total })
    : t('loading_results');

  const chips = [
    { key: 'job', label: t('cat_job'), val: bd.job },
    { key: 'scholarship', label: t('cat_scholarship'), val: bd.scholarship },
    { key: 'internship', label: t('cat_internship'), val: bd.internship },
  ].filter((c) => c.val != null);

  const heatPct = level === 'very_high' ? 95 : level === 'high' ? 78 : level === 'medium' ? 52 : level === 'low' ? 28 : 12;

  return `
    <div class="dash-card radar-preview-card">
      <div class="radar-preview-card__body">
        <div class="radar-preview-card__icon">${ico('world')}</div>
        <div class="radar-preview-card__copy">
          <p class="radar-preview-card__eyebrow">${t('your_district')}</p>
          <h3>${esc(district)}</h3>
          <p class="radar-preview-card__count">${esc(countLabel)}</p>
          ${chips.length ? `<div class="radar-preview-chips">${chips.map((c) => `
            <span class="radar-preview-chip radar-preview-chip--${c.key}">${esc(c.label)}: <strong>${c.val}</strong></span>`).join('')}</div>` : ''}
        </div>
        <div class="radar-preview-heat" aria-hidden="true">
          <div class="radar-preview-heat__track">
            <div class="radar-preview-heat__fill radar-preview-heat__fill--${level}" style="width:${heatPct}%"></div>
          </div>
          <span class="radar-preview-heat__label">${esc(densityLabel(level))}</span>
        </div>
      </div>
      <button type="button" class="btn btn-primary radar-preview-card__cta" data-go="home">
        ${t('search_btn')} ${ico('arrow')}
      </button>
    </div>`;
}

function renderRadarMapCard(opts = {}) {
  const compact = opts.compact || opts.mode === 'home';
  if (compact) {
    const district = state.selectedDashboardDistrict || state.user?.district || '';
    return `
      <div class="dash-map-block" id="radarMap">
        <div class="rwanda-map-widget rwanda-map-widget--dashboard">
          <div class="rwanda-map-svg-host" id="rwandaMapHost" data-map-mode="home"></div>
        </div>
        <p class="map-hint-line map-hint-line--pulse">${district ? esc(district) + ' · ' : ''}${t('radar_tap_hint')}</p>
      </div>`;
  }

  const u = state.user || {};
  const radar = state.radarDistricts || [];
  const selected = state.selectedRadarDistrict || state.selectedDashboardDistrict || u.district || 'Gasabo';
  const selData = radar.find((d) => d.district === selected) || radar[0];
  const registryN = registryOpportunityCount() || '—';
  const tall = opts.tall ? ' rwanda-map-widget--page' : '';

  return `
    <div class="dash-card dash-card--compact" id="radarMap">
      <div class="dash-card__head">
        <h2>${t('opportunity_radar')}</h2>
        <span class="live-pill"><span class="live-dot"></span> Live</span>
      </div>
      <div class="radar-filters radar-filters--compact" id="radarCategoryFilters">
        <button type="button" class="radar-filter active" data-cat="">${t('cat_all')}</button>
        <button type="button" class="radar-filter" data-cat="job">${t('cat_job')}</button>
        <button type="button" class="radar-filter" data-cat="scholarship">${t('cat_scholarship')}</button>
        <button type="button" class="radar-filter" data-cat="internship">${t('cat_internship')}</button>
        <button type="button" class="radar-filter" data-cat="training">${t('cat_training')}</button>
      </div>
      <div class="rwanda-map-widget${tall}">
        <div class="rwanda-map-caption">${t('rwanda')} · ${registryN}+ ${t('brand_stat_jobs').toLowerCase()}</div>
        <div class="rwanda-map-svg-host" id="rwandaMapHost" data-map-mode="${opts.mode || 'radar'}"></div>
        ${selData ? `<div class="radar-popup radar-popup--compact" id="radarPopup">
          <strong>${esc(selData.district)}</strong>
          <div class="radar-popup__row"><span>${t('cat_job')}</span><span>${selData.breakdown?.job ?? 0}</span></div>
          <div class="radar-popup__row"><span>${t('cat_scholarship')}</span><span>${selData.breakdown?.scholarship ?? 0}</span></div>
          <div class="radar-popup__row"><span>${t('cat_internship')}</span><span>${selData.breakdown?.internship ?? 0}</span></div>
          <div class="radar-popup__row"><span>Total</span><span>${selData.total ?? 0}</span></div>
        </div>` : ''}
        <div class="radar-legend radar-legend--compact">
          <span><i class="leg-very-high"></i>${t('density_very_high')}</span>
          <span><i class="leg-medium"></i>${t('density_medium')}</span>
          <span><i class="leg-low"></i>${t('density_low')}</span>
        </div>
      </div>
    </div>`;
}

async function mountRwandaMap(mode) {
  const host = document.getElementById('rwandaMapHost');
  if (!host || typeof RwandaMap === 'undefined') return;
  const u = state.user || {};
  const selected = state.selectedDashboardDistrict || state.selectedRadarDistrict || u.district || 'Gasabo';
  await RwandaMap.mount(host, {
    radar: state.radarDistricts || [],
    selected,
    gapMode: !!state.mapGapMode,
    onSelect: (district) => {
      state.selectedRadarDistrict = district;
      state.selectedDashboardDistrict = district;
      loadDashboardDistrictOpportunities(district, { scroll: true, force: true });
    },
  });
}

function renderRecentOppsRow(opps, loading) {
  const items = opps || [];
  if (loading) {
    return `
      <section class="recent-opp-section" style="margin-top:22px">
        <h2>${t('recent_near_you')}</h2>
        <div class="loading loading--compact"><div class="spinner"></div><p>${t('loading_results')}</p></div>
      </section>`;
  }
  if (!items.length) return '';
  return `
    <section class="recent-opp-section" style="margin-top:22px">
      <h2>${t('recent_near_you')}</h2>
      <div class="opp-scroll">
        ${items.slice(0, 8).map((r, i) => {
          const cat = (r.category || r.categories?.[0] || 'program').toLowerCase();
          const tagCls = cat.includes('job') ? 'job' : cat.includes('scholar') ? 'scholarship' : cat.includes('intern') ? 'internship' : 'training';
          return `
          <button type="button" class="opp-card-mini" data-open-idx="${i}">
            <span class="opp-card-mini__tag opp-card-mini__tag--${tagCls}">${esc(categoryLabel(cat))}</span>
            <h4>${esc(opportunityTitle(r))}</h4>
            <p>${esc(opportunityEmployer(r))}</p>
            <p style="margin-top:6px;font-size:11px;color:var(--text-muted)">${t('trust')} ${trustPercent(r.trust_score)}%</p>
          </button>`;
        }).join('')}
      </div>
    </section>`;
}

function renderDashSearchBar() {
  const chips = [
    { q: 'scholarships Rwanda', label: t('cat_scholarship') },
    { q: 'jobs Rwanda', label: t('cat_job') },
    { q: 'internships', label: t('cat_internship') },
    { q: 'training programs', label: t('cat_training') },
  ];
  const chipBtns = chips.map((c) =>
    `<button type="button" class="filter-pill filter-pill--blue" data-suggest="${esc(c.q)}">${esc(c.label)}</button>`
  ).join('');
  const pct = state.profileCompleteness || profileCompletenessPct();
  const profileHint = pct < 100 ? `
    <div class="dash-profile-inline">
      <span class="profile-match-ring profile-match-ring--sm" style="--pct:${pct}"><span>${pct}%</span></span>
      <span>${t('profile_match_hint')}</span>
      <button type="button" class="btn btn-outline btn-sm" data-go="matches">${t('update_profile')}</button>
    </div>` : '';
  return `
    <section class="dash-search-section">
      <form class="dash-search-bar" id="dashSearchForm" onsubmit="return false">
        <span class="dash-search-bar__icon" aria-hidden="true">${ico('search')}</span>
        <input id="dashSearchInput" type="search" placeholder="${t('search_placeholder_long')}" autocomplete="off" aria-label="${t('search_btn')}">
        <button type="submit" class="btn btn-primary dash-search-bar__btn" id="btnDashSearch">${t('search_btn')}</button>
      </form>
      <div class="motion-scroll-wrap dash-search-chips">
        <div class="motion-scroll-track">${chipBtns}${chipBtns}</div>
      </div>
      ${profileHint}
    </section>`;
}

function renderYouthDashboard() {
  const u = state.user || {};
  const district = state.selectedDashboardDistrict || u.district || '';
  const opps = (state.dashboardOpps || []).slice(0, 8);
  const nationalOpps = (state.dashboardNationalOpps || []).slice(0, 4);
  const loading = !!state.dashboardOppsLoading;
  const name = esc(u.name?.split(' ')[0] || 'there');
  const hour = new Date().getHours();
  const greet = hour < 12 ? t('good_morning') : hour < 17 ? t('good_afternoon') : t('good_evening');

  return `
    <div class="dash-welcome dash-welcome--compact">
      <h1>${greet}, ${name}</h1>
      <p>${t('dashboard_subtitle')}</p>
    </div>

    ${renderDashSearchBar()}

    ${renderImpactCounter()}

    <div class="dash-map-viewport dash-map-viewport--hero">
      ${renderRadarMapCard({ mode: 'home', compact: true })}
      ${renderGapMapControls()}
      ${state.mapGapMode ? `
        <div class="map-legend-bar map-legend-bar--gap">
          <span><i class="leg-gap-critical"></i> ${t('map_gap_hint')}</span>
        </div>` : renderMapLegend()}
    </div>

    ${renderMotionHighlights(true)}

    <div class="dash-card dash-card--below-fold" id="dashboardOppCard">
      <div class="dash-card__head">
        <h2>${t('jobs_in_district')}</h2>
        <span class="tag tag-blue">${t('verified')}</span>
      </div>
      <div class="filter-pills filter-pills--light dashboard-opp-filters" id="dashboardOppFilters" style="margin:8px 0 12px">
        ${renderCategoryFilterPills('dash-cat', state.dashboardCategoryFilter || '')}
      </div>
      <p class="sheet-desc" style="margin-top:0">${district ? t('dashboard_jobs_in', { district }) : t('dashboard_select_district')}</p>
      ${!loading && state.districtFallback ? districtFallbackBanner(district) : ''}
      <div class="results-list" id="dashboardOppList">
        ${loading ? `<div class="loading loading--compact"><div class="spinner"></div><p>${t('loading_results')}</p></div>` : ''}
        ${!loading && !opps.length && !(district && nationalOpps.length) ? `<div class="empty-state empty-state--compact">${district ? emptyCategoryMessage(state.dashboardCategoryFilter) : t('dashboard_select_district')}</div>` : ''}
        ${!loading && opps.length ? opps.map((r, i) => {
          const trust = formatTrustDisplay(r.trust_score);
          const cats = resultCategories(r);
          return `
          <div class="result-card result-card--row result-card--enriched">
            <div class="result-main">
              <div class="result-title">${esc(opportunityTitle(r))}</div>
              <div class="result-url">${esc(opportunityEmployer(r))}${r.location ? ` · ${esc(r.location)}` : ''}</div>
              <div class="tag-row" style="margin-top:8px">
                ${cats.map((c) => `<span class="tag ${categoryTagClass(c)}">${esc(categoryLabel(c))}</span>`).join('')}
                ${r.scope === 'international' ? `<span class="tag tag-muted">${esc(t('tag_international_open_to_rwandans'))}</span>` : ''}
                ${renderDeadlineGuardianBadge(r)}
              </div>
              ${renderOpportunityWowBlock(r, i, 'opp', { compact: true })}
            </div>
            <div class="result-actions">
              <span class="tag tag-green">${t('trust')} ${trust}</span>
              <button type="button" class="btn btn-outline btn-sm follow-btn${isFollowedUrl(r.url) ? ' btn-follow--active' : ''}" data-save-idx="${i}" aria-label="${t('follow')}">${ico('bookmark')}</button>
              <button type="button" class="btn btn-outline btn-sm notify-btn${isNotifyOn(r.url) ? ' notify-btn--active' : ''}" data-notify-idx="${i}" aria-label="${t('notify_me')}">${ico('bell')}</button>
              <button type="button" class="btn btn-outline btn-sm" data-open-idx="${i}">${t('apply_now')} ↗</button>
            </div>
          </div>`;
        }).join('') : ''}
      </div>
      ${district && nationalOpps.length && !state.districtFallback ? `
      <div class="dash-card__head" style="margin-top:20px">
        <h2>${t('national_opportunities') || 'National opportunities'}</h2>
        <span class="tag tag-muted">${t('rwanda')}</span>
      </div>
      <p class="sheet-desc">${t('national_opportunities_hint') || 'Rwanda-wide programs — not limited to your district.'}</p>
      <div class="results-list">
        ${nationalOpps.map((r, i) => {
          const trust = formatTrustDisplay(r.trust_score);
          const cats = resultCategories(r);
          return `
          <div class="result-card result-card--row result-card--enriched">
            <div class="result-main">
              <div class="result-title">${esc(opportunityTitle(r))}</div>
              <div class="result-url">${esc(opportunityEmployer(r))}${r.location ? ` · ${esc(r.location)}` : ''}</div>
              <div class="tag-row" style="margin-top:8px">
                ${cats.map((c) => `<span class="tag ${categoryTagClass(c)}">${esc(categoryLabel(c))}</span>`).join('')}
                ${r.scope === 'international' ? `<span class="tag tag-muted">${esc(t('tag_international_open_to_rwandans'))}</span>` : ''}
                ${renderDeadlineGuardianBadge(r)}
              </div>
            </div>
            <div class="result-actions">
              <span class="tag tag-green">${t('trust')} ${trust}</span>
              <button type="button" class="btn btn-outline btn-sm" data-open-national-idx="${i}">${t('apply_now')} ↗</button>
            </div>
          </div>`;
        }).join('')}
      </div>` : ''}
    </div>`;
}

function renderRadarPage() {
  return `
    <div class="inzira-topbar inzira-topbar--compact">
      <div>
        <h1>${t('opportunity_radar')}</h1>
        <p class="inzira-topbar__sub">${t('brand_stat_districts')} · ${t('rwanda')}</p>
      </div>
    </div>
    ${renderRadarMapCard({ tall: true, mode: 'radar' })}`;
}

function renderMatchesPage() {
  const u = state.user || {};
  const districtOpts = DISTRICTS.map((d) => `<option value="${d}"${u.district === d ? ' selected' : ''}>${d}</option>`).join('');
  const edu = normalizeMatchEducation(u.education);
  const skill = normalizeMatchSkill(u.skills);
  const pick = resolveLookingPick(u.interests);
  const eduOpts = ['High school', 'Diploma', "Bachelor's degree", "Master's degree"].map((e) =>
    `<option value="${e}"${edu === e ? ' selected' : ''}>${e}</option>`).join('');
  const skillOpts = MATCH_SKILL_FIELDS.map((s) =>
    `<option value="${s}"${skill === s ? ' selected' : ''}>${s}</option>`).join('');
  const lookingPills = MATCH_LOOKING_OPTIONS.map((o) =>
    `<button type="button" class="filter-pill filter-pill--blue${pick === o.id ? ' active' : ''}" data-looking="${o.id}">${t(o.labelKey)}</button>`).join('');

  return `
    <div class="inzira-topbar">
      <div>
        <h1>${t('nav_matches')}</h1>
        <p class="inzira-topbar__sub">${t('matches_page_sub')}</p>
      </div>
    </div>
    ${renderProfileCompletenessCard()}
    <div class="dash-card app-form-card" style="margin-top:8px">
      <div class="dash-card__head" style="margin-bottom:10px">
        <h2>Find your matches</h2>
      </div>
      <p class="sheet-desc">A short form — 30 seconds. INZIRA scores every live opportunity against your answers.</p>
      <form id="matchProfileForm" style="margin-top:14px">
        <div class="field-row">
          <div class="select-wrap">
            <label class="select-label">Education level</label>
            <select name="education" required>
              <option value="" disabled${edu ? '' : ' selected'}>Select education level</option>
              ${eduOpts}
            </select>
          </div>
          <div class="select-wrap">
            <label class="select-label">Field of interest</label>
            <select name="skills" required>
              <option value="" disabled${skill ? '' : ' selected'}>Select your field</option>
              ${skillOpts}
            </select>
          </div>
          <div class="select-wrap">
            <label class="select-label">Preferred district</label>
            <select name="district" required>
              <option value="" disabled${u.district ? '' : ' selected'}>Select district</option>
              ${districtOpts}
            </select>
          </div>
        </div>

        <div style="margin-top:10px">
          <div class="select-label" style="margin-bottom:8px">I am looking for</div>
          <div class="filter-pills filter-pills--light" id="lookingPills">
            ${lookingPills}
          </div>
          <input type="hidden" id="lookingHidden" name="interests" value="${esc(pick)}">
        </div>

        <button type="submit" class="btn btn-primary btn-primary--block" id="btnFindMatches" style="margin-top:14px;background:var(--amber);border-color:transparent">${t('view_all_matches')}</button>
      </form>
    </div>
    ${renderFeatureGrid()}`;
}

function filterMatchesByCategory(matches, cat) {
  if (!cat) return matches || [];
  const want = String(cat).toLowerCase();
  return (matches || []).filter((r) => {
    const primary = String(r.category || '').toLowerCase();
    if (primary === want) return true;
    return resultCategories(r).some((c) => String(c || '').toLowerCase() === want);
  });
}

async function loadMatchesList(category = null) {
  const cat = category || state.matchesCategoryFilter || null;
  state.matchesLoading = true;
  const { path } = parseRoute();
  if (path === 'matches-list') render();
  try {
    const data = await InziraApi.youthMatches(profilePayload(), 30, cat);
    state.matchesAll = data.matches || [];
    state.matches = state.matchesAll;
    state.matchesProfileFallback = !!data.profile_fallback;
    state.insights = data.insights || [];
    state.profileCompleteness = data.profile_completeness || 0;
    state.youthDataLoaded = true;
  } catch (err) {
    toast(err?.body?.detail || err?.message || 'Failed to load matches', { error: true });
  } finally {
    state.matchesLoading = false;
    if (parseRoute().path === 'matches-list') render();
  }
}

function renderMatchesCategoryFilters() {
  return `<div class="filter-pills filter-pills--light" id="matchesCategoryFilters" style="margin:8px 0 12px">
    ${renderCategoryFilterPills('match-cat', state.matchesCategoryFilter || '')}
  </div>`;
}

function displayedMatches() {
  const all = state.matchesAll?.length ? state.matchesAll : (state.matches || []);
  return filterMatchesByCategory(all, state.matchesCategoryFilter);
}

function renderMatchesList() {
  const allMatches = state.matchesAll?.length ? state.matchesAll : (state.matches || []);
  const matches = filterMatchesByCategory(allMatches, state.matchesCategoryFilter);
  if (state.matchesLoading) {
    return `
      <div class="inzira-topbar">
        <div><h1>${t('nav_matches')}</h1><p class="inzira-topbar__sub">${t('searching')}</p></div>
      </div>
      <div class="dash-card"><div class="loading loading--compact"><div class="spinner"></div><p>${t('loading_results')}</p></div></div>`;
  }
  if (!allMatches.length) {
    return `
      <div class="inzira-topbar">
        <div><h1>${t('nav_matches')}</h1><p class="inzira-topbar__sub">${t('matches_empty_sub')}</p></div>
        <div class="inzira-topbar__actions">
          <button type="button" class="btn btn-outline btn-sm" data-go="matches">${t('update_profile')}</button>
        </div>
      </div>
      <div class="dash-card">${emptyStateHtml(t('matches_empty_title'), t('matches_empty_sub'), t('update_profile'), 'matches')}</div>
      ${renderFeatureGrid()}
      ${renderQuickExplore()}`;
  }
  if (!matches.length) {
    return `
      <div class="inzira-topbar">
        <div><h1>${t('nav_matches')}</h1><p class="inzira-topbar__sub">${emptyCategoryMessage(state.matchesCategoryFilter)}</p></div>
        <div class="inzira-topbar__actions">
          <button type="button" class="btn btn-outline btn-sm" data-go="matches">${t('update_profile')}</button>
        </div>
      </div>
      ${renderProfileCompletenessCard()}
      ${renderMatchesCategoryFilters()}
      <div class="dash-card">${emptyStateHtml(emptyCategoryMessage(state.matchesCategoryFilter), t('try_different'), t('update_profile'), 'matches')}</div>`;
  }

  return `
    <div class="inzira-topbar">
      <div><h1>${t('nav_matches')}</h1><p class="inzira-topbar__sub">${matches.length} ${t('results_found', { n: matches.length }).replace(/^\d+\s*/, '')}</p></div>
      <div class="inzira-topbar__actions">
        <button type="button" class="btn btn-outline btn-sm" data-go="matches">${t('update_profile')}</button>
      </div>
    </div>
    ${renderProfileCompletenessCard()}
    ${state.matchesProfileFallback ? `<div class="info-banner info-banner--amber" role="status">${esc(t('matches_fallback_msg'))}</div>` : ''}
    ${renderMatchesCategoryFilters()}
    <div class="matches-grid" id="matchesList" style="margin-top:12px">
      ${matches.slice(0, 30).map((r, i) => {
        const score = Number(r.match_score || 0);
        const trust = formatTrustDisplay(r.trust_score);
        const cat = categoryLabel(r.category);
        const title = opportunityTitle(r);
        const company = opportunityEmployer(r);
        const districtLabel = r.district || r.location || state.user?.district || 'Rwanda';
        const deadline = r.deadline || 'rolling deadline';
        return `
          <div class="pro-match-card" data-match-idx="${i}">
            <div class="pro-match-card__body" style="flex:1;min-width:0">
              <h3 style="margin:0 0 6px">${esc(title)}</h3>
              <p style="margin:0;color:var(--text-secondary)">${esc(company)} · ${esc(districtLabel)} · ${esc(deadline)}</p>
              <div class="pro-tags" style="margin-top:10px">
                <span class="tag tag-${cat === 'training' ? 'green' : cat === 'scholarship' ? 'amber' : 'blue'}">${esc(cat || 'opportunity')}</span>
                <span class="tag tag-green">${t('trust')} ${trust}</span>
                ${renderDeadlineGuardianBadge(r)}
              </div>
              ${renderOpportunityWowBlock(r, i, 'match', { compact: true })}
            </div>
            <div style="display:flex;align-items:center;gap:12px">
              <div class="match-score-ring" style="--score:${Math.max(0, Math.min(100, score))}"><span>${score}%</span></div>
              <button type="button" class="btn btn-outline btn-sm follow-btn${isFollowedUrl(r.url) ? ' btn-follow--active' : ''}" data-save-idx="${i}" aria-label="${t('follow')}">${ico('bookmark')}</button>
              <button type="button" class="btn btn-outline btn-sm notify-btn${isNotifyOn(r.url) ? ' notify-btn--active' : ''}" data-notify-idx="${i}" aria-label="${t('notify_me')}">${ico('bell')}</button>
              <button type="button" class="btn btn-outline btn-sm" data-open-match="${i}">Visit</button>
            </div>
          </div>`;
      }).join('')}
    </div>
    ${renderQuickExplore()}`;
}

function renderOpportunitiesPage() {
  const n = registryOpportunityCount();
  return `
    <div class="inzira-topbar">
      <div><h1>${t('nav_opportunities')}</h1><p class="inzira-topbar__sub">${t('all_sites_sub')}</p></div>
      <div class="inzira-topbar__actions">
        <form class="inzira-search-pill" id="oppSearchForm" onsubmit="return false">
          ${ico('search')}
          <input id="oppSearchInput" type="text" placeholder="${t('search_placeholder')}" autocomplete="off">
        </form>
      </div>
    </div>
    <div class="filter-pills filter-pills--light" id="sitesCategoryFilter" style="margin-bottom:16px">
      <button type="button" class="filter-pill filter-pill--blue active" data-filter="">${t('cat_all')}</button>
      <button type="button" class="filter-pill filter-pill--green" data-filter="scholarship">${t('cat_scholarship')}</button>
      <button type="button" class="filter-pill filter-pill--amber" data-filter="job">${t('cat_job')}</button>
      <button type="button" class="filter-pill filter-pill--blue" data-filter="internship">${t('cat_internship')}</button>
      <button type="button" class="filter-pill filter-pill--green" data-filter="training">${t('cat_training')}</button>
    </div>
    <div id="sitesList" class="matches-grid">${t('all_sites_loading')}</div>
    <p class="hero-hint" style="margin-top:12px">${t('all_sites_count', { n })}</p>`;
}

function logoMark(sm) {
  return `<div class="inzira-logo${sm ? ' inzira-logo--sm' : ''}" aria-hidden="true"><span>I</span></div>`;
}

function renderStatsStrip(items, opts = {}) {
  const opps = registryOpportunityCount();
  const portals = verifiedPortalCount();
  const districts = Number(state.impactStats?.districts_covered ?? state.registryStats?.districts_with_listings ?? 0);
  const rows = items || [
    { value: String(portals || 0), label: t('brand_stat_sites'), tone: 'blue' },
    { value: 'AI', label: t('brand_stat_verify'), tone: 'green' },
    { value: String(districts || 0), label: t('brand_stat_districts'), tone: 'amber' },
  ];
  if (!items && opps) {
    rows[0] = { value: String(opps), label: t('impact_opportunities'), tone: 'blue' };
  }
  const heroCls = opts.hero ? ' stats-strip--hero' : '';
  const presentCls = opts.present ? ' stats-strip--present' : '';
  const animCls = opts.animate ? ' stats-strip--animate' : '';
  return `<div class="stats-strip${heroCls}${presentCls}${animCls}">${rows.map((s, i) => `
    <div class="stat-card stat-card--${s.tone}" style="--i:${i}">
      <strong>${esc(s.value)}</strong><span>${esc(s.label)}</span>
    </div>`).join('')}</div>`;
}

function renderMotionHighlights(compact = false) {
  const n = registryOpportunityCount() || 0;
  const items = [
    { icon: 'spark', text: `${n} ${t('brand_stat_jobs')}` },
    { icon: 'shield', text: t('brand_point2') },
    { icon: 'search', text: t('brand_point1') },
    { icon: 'bell', text: t('step_alert') },
    { icon: 'world', text: t('brand_point3') },
    { icon: 'bookmark', text: t('map_legend_hint') },
  ];
  const doubled = [...items, ...items];
  const chips = doubled.map((item, i) => `
    <span class="motion-highlights__chip" style="--i:${i % items.length}">
      <span class="motion-highlights__icon">${ico(item.icon)}</span>
      ${esc(item.text)}
    </span>`).join('');
  return `
    <div class="motion-highlights${compact ? ' motion-highlights--compact' : ''}">
      <div class="motion-highlights__track">${chips}</div>
    </div>`;
}

function renderAnimatedFlowDiagram() {
  const steps = [
    { icon: 'search', label: t('step_collect'), i: 0 },
    { icon: 'spark', label: t('step_match'), i: 1 },
    { icon: 'bell', label: t('step_alert'), i: 2 },
    { icon: 'shield', label: t('step_succeed'), i: 3 },
  ];
  const nodes = steps.map((s, idx) => {
    const node = `<div class="motion-flow__node" style="--i:${s.i}"><span class="motion-flow__icon">${ico(s.icon)}</span><span>${esc(s.label)}</span></div>`;
    return idx < steps.length - 1 ? `${node}<span class="motion-flow__arrow" style="--i:${idx}">→</span>` : node;
  }).join('');
  return `<div class="motion-flow motion-flow--inline">${nodes}</div>`;
}

function renderPageMotionBlock() {
  return `
    <section class="page-motion-block">
      ${renderMotionHighlights()}
      ${renderAnimatedFlowDiagram()}
    </section>`;
}

function renderLiveStatsStrip() {
  const n = registryOpportunityCount() || 0;
  const saved = (state.followed || []).length;
  const matches = (state.matches || []).length;
  const districts = state.impactStats?.districts_covered ?? 0;
  return renderStatsStrip([
    { value: String(n), label: t('stat_verified_opportunities'), tone: 'amber' },
    { value: String(districts), label: t('brand_stat_districts'), tone: 'blue' },
    { value: String(saved), label: t('stat_saved_bookmarks'), tone: 'green' },
    ...(matches ? [{ value: String(matches), label: t('nav_matches'), tone: 'blue' }] : []),
  ], { present: true, animate: true });
}

function renderMapLegend() {
  return `
    <div class="map-legend-bar">
      <span><i class="leg-very-high"></i> ${t('density_high')}</span>
      <span><i class="leg-medium"></i> ${t('density_medium')}</span>
      <span><i class="leg-low"></i> ${t('density_low')}</span>
      <span class="map-legend-bar__hint">${t('map_legend_hint')}</span>
    </div>`;
}

function renderQuickExplore() {
  const chips = [
    { q: 'scholarships Rwanda', label: t('cat_scholarship') },
    { q: 'jobs Kigali', label: t('cat_job') },
    { q: 'internships youth', label: t('cat_internship') },
    { q: 'training programs', label: t('cat_training') },
    { q: 'youth programs', label: t('cat_program') },
    { q: 'free courses', label: t('cat_free_course') || 'Free courses' },
  ];
  const chipHtml = chips.map((c) => `<button type="button" class="filter-pill filter-pill--blue" data-quick-search="${esc(c.q)}">${esc(c.label)}</button>`).join('');
  return `
    <section class="page-enrich-section">
      <h3 class="section-heading">${t('search_by_category')}</h3>
      <div class="voice-search-bar">
        <input type="text" id="dashVoiceInput" placeholder="${t('voice_search_hint')}" autocomplete="off" aria-label="${t('voice_search')}">
        <button type="button" class="voice-btn" id="btnVoiceDashSearch" aria-label="${t('voice_search')}">${ico('search')}</button>
      </div>
      <div class="motion-scroll-wrap">
        <div class="motion-scroll-track quick-explore-pills">${chipHtml}${chipHtml}</div>
      </div>
    </section>`;
}

function renderProfileCompletenessCard() {
  const pct = state.profileCompleteness || profileCompletenessPct();
  return `
    <div class="dash-card profile-complete-card">
      <div class="profile-complete-card__row">
        <div class="profile-match-ring" style="--pct:${pct}"><span>${pct}%</span></div>
        <div style="flex:1;min-width:0">
          <strong>${t('profile_match')}</strong>
          <p class="sheet-desc">${t('profile_match_hint')}</p>
        </div>
        ${pct < 100 ? `<button type="button" class="btn btn-outline btn-sm" data-go="matches">${t('update_profile')}</button>` : ''}
      </div>
    </div>`;
}

function renderAssistantHelpPanel() {
  const tips = [
    { title: t('assistant_tip1_title'), text: t('assistant_tip1') },
    { title: t('assistant_tip2_title'), text: t('assistant_tip2') },
    { title: t('assistant_tip3_title'), text: t('assistant_tip3') },
  ];
  return `
    <div class="dash-card">
      <div class="dash-card__head"><h2>${t('assistant_help_title')}</h2></div>
      <div class="assistant-help-grid">
        ${tips.map((tip, i) => `
          <div class="assistant-help-card" style="--i:${i}">
            <strong>${esc(tip.title)}</strong>
            <p>${esc(tip.text)}</p>
          </div>`).join('')}
      </div>
      ${renderFeatureGrid()}
    </div>`;
}

function renderSavedTipsCard() {
  return `
    <div class="dash-card saved-tips-card">
      <div class="dash-card__head"><h2>${t('saved_tips_title')}</h2></div>
      <ul>
        <li>${t('saved_tip1')}</li>
        <li>${t('saved_tip2')}</li>
        <li>${t('saved_tip3')}</li>
      </ul>
      ${renderQuickExplore()}
    </div>`;
}

function renderSavedShortcut() {
  const n = (state.followed || []).length;
  if (!n) return '';
  return `
    <div class="saved-shortcut-bar">
      <button type="button" class="btn btn-outline btn-sm saved-shortcut-btn" data-go="followed">
        ${ico('bookmark')} ${t('view_saved_sites', { n })}
      </button>
    </div>`;
}

function renderPresentationHero(u, topScore) {
  const name = esc(u.name?.split(' ')[0] || 'there');
  return `
    <section class="present-hero">
      <div class="present-hero__copy">
        <span class="present-hero__eyebrow">${ico('shield')} ${t('brand_eyebrow')}</span>
        <h1 class="present-hero__title">${t('hello')} ${name}</h1>
        <p class="present-hero__tagline">${t('platform_tagline')}</p>
        <form class="present-hero__search" id="dashSearchForm" onsubmit="return false">
          ${ico('search')}
          <input id="dashSearchInput" type="text" placeholder="${t('search_placeholder_long')}" autocomplete="off">
          <button type="button" class="btn btn-primary btn-sm" id="btnHeroSearch">${t('search_btn')}</button>
        </form>
        ${renderSavedShortcut()}
      </div>
    </section>`;
}

function renderFeatureGrid() {
  const items = [
    { tone: 'blue', text: t('brand_point1'), icon: 'search' },
    { tone: 'green', text: t('brand_point2'), icon: 'shield' },
    { tone: 'amber', text: t('brand_point3'), icon: 'spark' },
  ];
  return `<div class="feature-grid feature-grid--motion">${items.map((f, i) => `
    <div class="feature-card feature-card--${f.tone}" style="--i:${i}">
      <span class="feature-card__icon">${ico(f.icon)}</span>
      <p>${esc(f.text)}</p>
    </div>`).join('')}</div>`;
}

function renderAuthNav(active) {
  const links = [
    { id: 'language', label: t('choose_lang') },
    { id: 'register', label: t('create_account') },
    { id: 'login', label: t('sign_in') },
  ];
  return `<nav class="auth-nav">${links.map((l) => `
    <button type="button" class="auth-nav__link${active === l.id ? ' active' : ''}" data-go="${l.id}">${esc(l.label)}</button>`).join('')}</nav>`;
}

function renderAppToolbar() {
  return `<div class="app-toolbar">
    <div class="app-toolbar__inner page-wrap">
      <div class="app-toolbar__chips">
        <button type="button" class="toolbar-chip toolbar-chip--blue" data-go="language">${t('language')}</button>
        <button type="button" class="toolbar-chip toolbar-chip--amber" data-go="register">${t('create_account')}</button>
        <span class="build-badge" title="App version">v${APP_BUILD}</span>
      </div>
      <button type="button" class="btn btn-signout" id="btnTopSignOut">${ico('logout')} ${t('sign_out')}</button>
    </div>
  </div>`;
}

function renderTrustBanner() {
  return `<div class="trust-banner">
    <span class="trust-banner__icon">${ico('shield')}</span>
    <div>
      <strong>${t('trust_what')}</strong>
      <p>${t('trust_explain_short')}</p>
    </div>
    <button type="button" class="btn btn-outline btn-sm" id="btnTrustInfo">${t('learn_more')}</button>
  </div>`;
}

function renderCategoryGrid() {
  const cats = [
    { id: 'scholarship', label: t('cat_scholarship'), tone: 'blue', icon: 'spark' },
    { id: 'job', label: t('cat_job'), tone: 'green', icon: 'user' },
    { id: 'internship', label: t('cat_internship'), tone: 'amber', icon: 'calendar' },
    { id: 'program', label: t('cat_program'), tone: 'blue', icon: 'shield' },
  ];
  return `<div class="category-grid" id="categoryChips">
    <button type="button" class="category-card category-card--all active" data-cat="">
      <span class="category-card__icon">${ico('search')}</span>
      <span>${t('cat_all')}</span>
    </button>
    ${cats.map((c) => `
    <button type="button" class="category-card category-card--${c.tone}" data-cat="${c.id}">
      <span class="category-card__icon">${ico(c.icon)}</span>
      <span>${esc(c.label)}</span>
    </button>`).join('')}
  </div>`;
}

function renderPopularSection() {
  const recent = getRecentSearches();
  const popular = getPopularQueries();
  const district = state.user?.district;
  const chips = recent.length ? recent : popular.slice(0, 6);
  const label = recent.length ? t('recent') : (district ? `${t('popular_in')} ${district}` : t('popular'));
  return `
    <section class="content-section">
      <h3 class="section-heading section-heading--green">${label}</h3>
      <div class="query-chips" id="popularQueries">
        ${chips.map((q) => `<button type="button" class="query-chip query-chip--${recent.length ? 'blue' : 'amber'}" data-q="${esc(q)}">${esc(recent.length ? capitalize(q) : popularChipLabel(q))}</button>`).join('')}
      </div>
    </section>`;
}

function renderWelcomeBanner(displayName, district) {
  const d = district || t('rwanda');
  return `
    <div class="welcome-banner">
      <div class="welcome-banner__left">
        <span class="welcome-banner__eyebrow">${ico('shield')} ${t('brand_eyebrow')}</span>
        <h2 class="welcome-banner__title">${t('hello')} ${esc(displayName)} · ${t('muraho')}</h2>
        <p class="welcome-banner__sub">${t('welcome_banner_sub', { district: d })}</p>
        <div class="welcome-banner__tags">
          <span class="welcome-tag welcome-tag--blue">${ico('shield')} ${t('welcome_tag_verify')}</span>
          <span class="welcome-tag welcome-tag--green">${ico('spark')} ${t('welcome_tag_youth')}</span>
          <span class="welcome-tag welcome-tag--amber">${ico('check')} ${t('welcome_tag_free')}</span>
        </div>
      </div>
      <div class="welcome-banner__flag" aria-hidden="true">
        <span class="rw-flag-stripe rw-flag-stripe--blue"></span>
        <span class="rw-flag-stripe rw-flag-stripe--yellow"></span>
        <span class="rw-flag-stripe rw-flag-stripe--green"></span>
      </div>
    </div>`;
}

function renderRwandaSpotlight() {
  const items = [
    { tone: 'blue', label: 'MIFOTRA', sub: t('spotlight_mifotra'), go: 'mifotra' },
    { tone: 'green', label: 'MINEDUC', sub: t('spotlight_mineduc') },
    { tone: 'amber', label: 'RDB / WDA', sub: t('spotlight_rdb') },
    { tone: 'blue', label: 'HEC', sub: t('spotlight_hec') },
  ];
  return `
    <section class="content-section">
      <h3 class="section-heading section-heading--green">${t('spotlight_title')}</h3>
      <div class="spotlight-grid">${items.map((i) => {
        const cls = `spotlight-card spotlight-card--${i.tone}${i.go ? ' spotlight-card--clickable' : ''}`;
        const inner = `<strong>${esc(i.label)}</strong><span>${esc(i.sub)}</span>`;
        if (i.go) {
          return `<button type="button" class="${cls}" data-go="${i.go}">${inner}</button>`;
        }
        return `<div class="${cls}">${inner}</div>`;
      }).join('')}
      </div>
    </section>`;
}

function renderRwandaGlance() {
  const districts = Number(state.impactStats?.districts_covered ?? 0);
  const opps = Number(state.impactStats?.opportunities_live ?? registryOpportunityCount() ?? 0);
  const facts = [
    {
      tone: 'blue',
      text: districts > 0
        ? t('rwanda_fact1_live', { n: districts })
        : t('rwanda_fact1_geo'),
    },
    { tone: 'green', text: t('rwanda_fact2') },
    {
      tone: 'amber',
      text: opps > 0 ? t('rwanda_fact3_live', { n: opps }) : t('rwanda_fact3'),
    },
  ];
  return `
    <section class="content-section rwanda-glance">
      <h3 class="section-heading section-heading--amber">${t('rwanda_glance')}</h3>
      <div class="glance-pills">${facts.map((f) => `
        <span class="glance-pill glance-pill--${f.tone}">${ico('check')} ${esc(f.text)}</span>`).join('')}
      </div>
    </section>`;
}

const state = {
  // user is loaded from backend via Firebase ID token
  user: JSON.parse(localStorage.getItem('inzira_user_cache') || 'null'),
  idToken: sessionStorage.getItem('inzira_id_token') || '',
  followed: JSON.parse(localStorage.getItem('inzira_saved_cache') || '[]'),
  savedLoaded: false,
  mifotraToken: sessionStorage.getItem('inzira_mifotra_token') || '',
  detail: null,
  results: [],
  resultsQuery: '',
  resultsCategory: null,
  resultsSort: localStorage.getItem('inzira_sort') || 'trust',
  lang: localStorage.getItem('inzira_lang') || 'en',
  registryStats: null,
  allSites: [],
  matches: [],
  radarDistricts: [],
  insights: [],
  profileCompleteness: 0,
  selectedRadarDistrict: null,
  selectedDashboardDistrict: null,
  dashboardOpps: [],
  dashboardNationalOpps: [],
  dashboardOppsLoading: false,
  dashboardCategoryFilter: null,
  matchesCategoryFilter: null,
  matchesAll: [],
  matchesProfileFallback: false,
  districtFallback: false,
  youthDataLoaded: false,
  youthDataLoading: false,
};

const $modalRoot = () => document.getElementById('modalRoot');
const $modalPanel = () => document.getElementById('modalPanel');
const $previewRoot = () => document.getElementById('previewRoot');

const $app = document.getElementById('app');
const $nav = document.getElementById('bottomNav');
const $toast = document.getElementById('toast');
let toastHideTimer = null;
let toastSticky = false;
let toastDismissOnClick = true;

// ── Router ───────────────────────────────────────────────────
function navigate(route, params = {}) {
  if (params) {
    Object.assign(state, params);
  }
  dismissToast();
  const clean = String(route).replace(/^#\/?/, '');
  const target = `#/${clean}`;
  if (location.hash === target) {
    render();
  } else {
    location.hash = target;
  }
}

function parseRoute() {
  const hash = location.hash.replace(/^#\/?/, '') || defaultRoute();
  const [path, qs] = hash.split('?');
  const query = Object.fromEntries(new URLSearchParams(qs || ''));
  return { path, query };
}

const STAFF_ROUTES = new Set(['mifotra', 'dashboard']);

function guard(path) {
  const publicRoutes = ['language', 'login', 'register', 'forgot-password', 'home', 'results', 'detail', 'assistant', 'privacy-policy'];
  if (STAFF_ROUTES.has(path)) {
    if (path === 'dashboard' && !state.mifotraToken) {
      navigate('mifotra');
      return false;
    }
    return true;
  }
  if (!publicRoutes.includes(path) && !state.user) {
    navigate(defaultRoute());
    return false;
  }
  if (path === 'admin' && state.user?.role !== 'admin') {
    navigate('home');
    return false;
  }
  return true;
}

function renderGuestHome() {
  // Guest landing page: search + map + trust explainer (no profile/matches calls).
  return `
    ${renderPresentationHero({ name: '', district: '' }, 0)}
    ${renderTrustBanner()}
    <div class="dash-map-viewport dash-map-viewport--hero">
      ${renderRadarMapCard({ mode: 'home', compact: true })}
      ${renderGapMapControls()}
      ${state.mapGapMode ? `
        <div class="map-legend-bar map-legend-bar--gap">
          <span><i class="leg-gap-critical"></i> ${t('map_gap_hint')}</span>
        </div>` : renderMapLegend()}
    </div>
    ${renderMotionHighlights(true)}
    ${renderFeatureGrid()}
  `;
}

function setLanguage(lang) {
  if (lang !== 'en' && lang !== 'rw') return;
  state.lang = lang;
  localStorage.setItem('inzira_lang', lang);
  document.documentElement.lang = lang === 'rw' ? 'rw' : 'en';
}

function render() {
  // State is synced from Firebase → backend (/me)
  document.documentElement.lang = state.lang === 'rw' ? 'rw' : 'en';
  const { path, query } = parseRoute();
  if (!guard(path)) return;

  const isPublic = ['language', 'login', 'register', 'forgot-password'].includes(path);
  document.body.classList.toggle('inzira-shell', !!state.user && !isPublic);
  document.body.classList.toggle('page-auth', isPublic);
  document.body.classList.remove('inzira-dark');

  $nav.classList.add('hidden');
  $app.classList.remove('has-bottom-nav');

  const routes = {
    language: renderLanguage,
    login: renderLogin,
    'forgot-password': renderForgotPassword,
    register: renderRegister,
    home: () => (state.user ? renderYouthDashboard() : renderGuestHome()),
    search: () => (state.user ? renderYouthDashboard() : renderGuestHome()),
    radar: () => { navigate('home'); return ''; },
    matches: renderMatchesPage,
    'matches-list': renderMatchesList,
    opportunities: () => { navigate('home'); return ''; },
    results: () => renderResults(query),
    detail: renderDetail,
    assistant: renderAssistant,
    followed: renderFollowed,
    settings: renderSettings,
    'privacy-policy': renderPrivacyPolicy,
    admin: renderAdmin,
    sites: () => { navigate('home'); return ''; },
    mifotra: renderMifotra,
    dashboard: renderDashboard,
  };

  const fn = routes[path] || (state.user ? renderYouthDashboard : renderLogin);
  let html = fn(query);
  const useShell = state.user && APP_SHELL_ROUTES.has(path) && !STAFF_ROUTES.has(path);
  if (useShell) {
    html = renderInziraShell(html, shellNavKey(path));
  } else {
    const staffFrame = STAFF_ROUTES.has(path) ? ' app-frame--staff' : '';
    html = `<div class="app-frame${isPublic ? ' app-frame--auth' : ''}${staffFrame}">${html}</div>`;
  }
  $app.innerHTML = html;
  $nav.innerHTML = '';
  bindRouteEvents(path, query);
  bindGlobalUI();
  if (useShell) bindSidebarUI();
}

function renderBlueBar(title, backTo) {
  const back = backTo
    ? `<button type="button" class="icon-btn icon-btn--light" data-go="${backTo}" aria-label="Back">←</button>`
    : '';
  return `
    <div class="mobile-hero mobile-hero--bar">
      ${back}
      <h1>${esc(title)}</h1>
    </div>`;
}

// ── Auth & onboarding ──────────────────────────────────────
function renderLanguage() {
  const sel = state.lang || 'en';
  return renderAuthShell(`
    <h2 class="sheet-title">${t('choose_lang')}</h2>
    <p class="sheet-desc">${t('choose_lang_sub')}</p>
    <div class="lang-cards" id="langCards">
      <button type="button" class="lang-card ${sel === 'en' ? 'active' : ''}" data-lang="en">
        <span class="lang-flag">GB</span>
        <span class="lang-card-text"><strong>${t('lang_en_name')}</strong><span>${t('lang_en_sub')}</span></span>
        <span class="lang-radio" aria-hidden="true"></span>
      </button>
      <button type="button" class="lang-card ${sel === 'rw' ? 'active' : ''}" data-lang="rw">
        <span class="lang-flag">RW</span>
        <span class="lang-card-text"><strong>${t('lang_rw_name')}</strong><span>${t('lang_rw_sub')}</span></span>
        <span class="lang-radio" aria-hidden="true"></span>
      </button>
    </div>
    <button type="button" class="btn btn-primary btn-primary--block btn-continue" id="btnLangContinue">
      ${t('continue')} ${ico('arrow')}
    </button>
  `, 'language');
}

function renderRegister() {
  return renderAuthShell(`
    <h2 class="sheet-title">${t('create_account')}</h2>
    <p class="sheet-desc sheet-desc--tight">${t('register_sub')}</p>
    <form id="registerForm">
      <div class="input-icon-wrap">
        <span class="input-icon">${ico('user')}</span>
        <input type="text" id="registerName" name="name" required placeholder="${t('full_name_placeholder')}" autocomplete="name">
      </div>
      <div class="input-icon-wrap">
        <span class="input-icon">${ico('mail')}</span>
        <input type="email" name="email" required placeholder="${t('email_placeholder')}" autocomplete="email">
      </div>
      <div class="input-icon-wrap">
        <span class="input-icon">${ico('lock')}</span>
        <input type="password" name="password" id="registerPassword" minlength="6" required placeholder="${t('register_password_hint')}" autocomplete="new-password">
        <button type="button" class="input-icon-btn" id="btnToggleRegPwd" aria-label="Show password">${ico('eye')}</button>
      </div>
      <p class="field-hint">${t('register_password_hint')}</p>
      <button type="submit" class="btn btn-primary btn-primary--block">${t('create_account')}</button>
    </form>
    <p class="link-row">${t('already_registered')} <a href="#/login">${t('sign_in')}</a></p>
  `, 'register');
}

function renderLogin() {
  return renderAuthShell(`
    <h2 class="sheet-title">${t('welcome_back')}</h2>
    <p class="sheet-desc">${t('welcome_back_sub')}</p>
    <form id="loginForm">
      <div class="input-icon-wrap">
        <span class="input-icon">${ico('mail')}</span>
        <input type="email" name="email" id="loginEmail" placeholder="${t('login_email_placeholder')}" required autocomplete="email">
      </div>
      <div class="input-icon-wrap">
        <span class="input-icon">${ico('lock')}</span>
        <input type="password" name="password" id="loginPassword" placeholder="••••••••" required autocomplete="current-password" minlength="6">
        <button type="button" class="input-icon-btn" id="btnTogglePwd" aria-label="Show password">${ico('eye')}</button>
      </div>
      <div class="forgot-row"><button type="button" class="text-link text-link--accent" id="btnForgotPassword">${t('forgot_password')}</button></div>
      <button type="submit" class="btn btn-primary btn-primary--block">${t('sign_in')}</button>
    </form>
    <p class="link-row link-row--prominent" style="margin-top:16px">${t('new_to_inzira')} <a href="#/register" class="link-register">${t('create_account')}</a></p>
    <p class="link-row" style="margin-top:10px">
      <button type="button" class="text-link text-link--accent" data-go="mifotra">${ico('shield')} MIFOTRA Staff Portal</button>
    </p>
  `, 'login');
}

function renderForgotPassword() {
  return renderAuthShell(`
    <h2 class="sheet-title">${t('forgot_password')}</h2>
    <p class="sheet-desc">${t('forgot_password_sub')}</p>
    <form id="forgotForm">
      <div class="input-icon-wrap">
        <span class="input-icon">${ico('mail')}</span>
        <input type="email" name="email" id="forgotEmail" placeholder="${t('login_email_placeholder')}" required autocomplete="email">
      </div>
      <button type="submit" class="btn btn-primary btn-primary--block">${t('send_reset_link')}</button>
    </form>
    <p class="link-row" style="margin-top:16px"><a href="#/login" class="link-register">${t('back_to_sign_in')}</a></p>
  `, 'login');
}

function renderRegistryBanner() {
  const n = state.registryStats?.verified_opportunities ?? state.registryStats?.verified_open;
  const newN = state.registryStats?.new_verified_last_days;
  const countLabel = n != null ? t('all_sites_count', { n }) : t('brand_stat_sites');
  const newBadge = newN > 0 ? `<span class="registry-banner__new">${t('all_sites_new', { n: newN })}</span>` : '';
  return `
    <section class="registry-banner" id="registryBanner">
      <div class="registry-banner__icon">${ico('world')}</div>
      <div class="registry-banner__body">
        <strong>${t('registry_live')}</strong>
        <p>${t('all_sites_sub')}</p>
        <div class="registry-banner__meta">
          <span class="registry-banner__count">${countLabel}</span>
          ${newBadge}
        </div>
      </div>
      <button type="button" class="btn btn-primary btn-sm" data-go="sites">${t('all_sites_browse')}</button>
    </section>`;
}

function renderAllSites() {
  const n = registryOpportunityCount();
  return `
    <div class="page page--rich page--sites">
      ${renderAppToolbar()}
      <div class="page-hero-band page-hero-band--compact">
        <div class="page-wrap">
          <button type="button" class="back-link-light" data-go="search">${ico('back')} ${t('nav_search')}</button>
          <h2 class="hero-name hero-name--lg">${t('all_sites_title')}</h2>
          <p class="hero-hint">${t('all_sites_sub')}</p>
        </div>
      </div>
      <div class="page-wrap page-body-rich">
        ${renderStatsStrip([
          { value: String(n), label: t('brand_stat_sites'), tone: 'green' },
          { value: String(state.registryStats?.new_verified_last_days || 0), label: t('new_this_week'), tone: 'amber' },
          { value: 'AI', label: t('brand_stat_verify'), tone: 'blue' },
        ], { hero: true })}
        <div class="filter-pills filter-pills--light" id="sitesCategoryFilter">
          <button type="button" class="filter-pill filter-pill--blue active" data-cat="">${t('cat_all')}</button>
          <button type="button" class="filter-pill filter-pill--green" data-cat="scholarship">${t('cat_scholarship')}</button>
          <button type="button" class="filter-pill filter-pill--amber" data-cat="job">${t('cat_job')}</button>
          <button type="button" class="filter-pill filter-pill--blue" data-cat="internship">${t('cat_internship')}</button>
          <button type="button" class="filter-pill filter-pill--green" data-cat="program">${t('cat_program')}</button>
        </div>
        <div id="allSitesContainer" class="sites-directory">
          <div class="loading"><div class="spinner"></div><p>${t('all_sites_loading')}</p></div>
        </div>
      </div>
    </div>`;
}

function siteDirectoryCard(site) {
  const isPortal = Boolean(site.domain && !site.source_domain);
  const cats = site.categories || [site.category];
  const name = isPortal ? (site.title || site.domain) : opportunityTitle(site);
  const initial = (name || 'O').charAt(0).toUpperCase();
  const trust = formatTrustDisplay(site.trust_score);
  const applyUrl = site.apply_link || site.url;
  const subline = isPortal
    ? `${site.domain || ''}${site.opportunity_count ? ` · ${site.opportunity_count} ${t('listings_label')}` : ''}`
    : `${opportunityEmployer(site)}${site.district ? ` · ${site.district}` : ''}`;
  const snippet = isPortal
    ? (site.snippet || t('portal_browse_hint', { domain: site.domain || '' }))
    : (site.snippet || '');
  return `
    <div class="site-dir-card" data-cats="${esc(cats.join(','))}" data-domain="${esc(site.domain || '')}">
      <div class="site-dir-card__icon site-dir-card__icon--${['blue', 'green', 'amber'][cats.length % 3]}">${esc(initial)}</div>
      <div class="site-dir-card__body">
        <div class="site-dir-card__top">
          <strong>${esc(name)}</strong>
          ${site.is_new ? `<span class="tag tag-green">${t('all_sites_new', { n: 1 }).replace('1 ', '')}</span>` : ''}
        </div>
        <div class="site-dir-card__domain">${esc(subline)}</div>
        <div class="tag-row">
          ${cats.map((c, i) => `<span class="tag tag-${['blue', 'green', 'amber'][i % 3]}">${esc(categoryLabel(c))}</span>`).join('')}
          <span class="tag tag-muted">${t('trust')}: ${trust}</span>
        </div>
        <p class="site-dir-card__snippet">${esc(snippet)}</p>
      </div>
      <a class="btn btn-outline btn-sm" href="${esc(applyUrl)}" target="_blank" rel="noopener">${isPortal ? t('visit_website') : t('apply_now')}</a>
    </div>`;
}

function renderSearch() {
  const displayName = state.user?.email?.split('@')[0] || state.user?.name?.split(' ')[0] || 'there';
  const district = state.user?.district || t('rwanda');
  const saved = state.followed.length;
  const registryN = registryOpportunityCount() || 0;
  return `
    <div class="page page--rich page--search">
      ${renderAppToolbar()}
      <div class="page-hero-band page-hero-band--search">
        <div class="page-wrap">
          <div class="search-top-row">
            <div>
              <p class="hero-eyebrow">${t('hello')}</p>
              <h2 class="hero-name">${esc(displayName)}</h2>
              <p class="hero-hint">${t('platform_tagline')}</p>
            </div>
            <div class="search-top-actions">
              <button type="button" class="icon-btn icon-btn--light" id="btnNotifications" aria-label="Notifications">${ico('bell')}</button>
              <button type="button" class="icon-btn icon-btn--light" id="btnProfile" aria-label="Profile">${ico('user')}</button>
            </div>
          </div>
          <form class="search-bar-mobile search-bar-mobile--wide" id="searchForm" onsubmit="return false">
            <span class="search-icon" aria-hidden="true">${ico('search')}</span>
            <input id="searchInput" type="text" placeholder="${t('search_placeholder_long')}" autocomplete="off">
            <button type="button" class="search-go search-go--amber" id="btnSearch" aria-label="${t('search_btn')}">${ico('search')}</button>
          </form>
        </div>
      </div>
      <div class="page-wrap page-body-rich">
        ${renderWelcomeBanner(displayName, district)}
        ${renderRegistryBanner()}
        ${renderStatsStrip([
          { value: String(saved), label: t('nav_saved'), tone: 'green' },
          { value: esc(district), label: t('district'), tone: 'blue' },
          { value: String(registryN), label: t('brand_stat_sites'), tone: 'amber' },
        ], { hero: true })}
        <section class="content-section">
          <h3 class="section-heading section-heading--blue">${t('search_by_category')}</h3>
          ${renderCategoryGrid()}
        </section>
        ${renderPopularSection()}
        ${renderRwandaSpotlight()}
        <div class="page-columns">
          <div class="page-col-main">
            <h3 class="section-heading section-heading--blue">${t('how_works')}</h3>
            <div class="how-card how-card--rich">
              <div class="steps-list">
                ${[t('step1'), t('step2'), t('step3'), t('step4')].map((desc, i) => `
                  <div class="step-item">
                    <span class="step-num step-num--${['blue', 'green', 'amber', 'blue'][i]}">${i + 1}</span>
                    <p>${desc}</p>
                  </div>`).join('')}
              </div>
            </div>
          </div>
          <div class="page-col-side">
            ${renderTrustBanner()}
            ${renderFeatureGrid()}
          </div>
        </div>
      </div>
    </div>`;
}

function renderResults(query) {
  const q = query.q || state.resultsQuery || '';
  const activeCat = query.category || state.resultsCategory || '';
  const title = (q ? capitalize(q) : t('nav_search')) + (q ? ' Rwanda' : '');
  return `
    ${renderAppTopbar({ title, sub: t('searching'), backTo: 'home' })}
    ${renderLiveStatsStrip()}
    <div class="filter-pills filter-pills--light" id="filterChips" style="margin-bottom:16px">
      ${renderCategoryFilterPills('filter', activeCat)}
    </div>
    <p class="hero-hint" id="resultsSubtitle" style="margin-bottom:12px">${t('searching')}</p>
    <p class="sheet-desc" id="resultsDistrictNote" style="margin-top:6px;color:#666"></p>
    <p class="sheet-desc" id="resultsDeepSearchNote" style="margin-top:6px;color:#0b5cab;font-weight:600"></p>
    <div class="search-progress" id="searchProgress" aria-live="polite">
      <div class="search-progress__track"><span class="search-progress__fill" id="searchProgressFill" style="width:8%"></span></div>
      <p class="search-progress__msg" id="searchProgressMsg">${t('search_phase_registry')}</p>
    </div>
    <div id="resultsContainer" class="matches-grid">${skeletonHtml(4)}</div>`;
}

function renderDetail() {
  const r = state.detail;
  if (!r) {
    return `${renderAppTopbar({ title: t('details'), backTo: 'home' })}
      <div class="dash-card empty"><p>${t('no_results')}</p></div>`;
  }
  const trust = formatTrustDisplay(r.trust_score);
  const trustRatio = trustDecimal(r.trust_score);
  const initial = websiteName(r).charAt(0).toUpperCase() || 'W';
  return `
    ${renderAppTopbar({
      title: websiteName(r),
      sub: `${domain(r.url)} · ${t('trust')}: ${trust}`,
      backTo: 'results',
    })}
    <div class="detail-hero-app">
      <div class="result-icon result-icon--hero result-icon--${trustRatio >= 0.7 ? 'green' : trustRatio >= 0.4 ? 'amber' : 'blue'}">${esc(initial)}</div>
      <div class="detail-hero-badges">
        <span class="badge-pill badge-pill--green">${ico('shield')} ${t('verified')}</span>
        <span class="badge-pill badge-pill--amber">${esc(categoryLabel(r.category))}</span>
      </div>
    </div>
    <div class="dash-grid dash-grid--detail">
      <div class="dash-card">
        <div class="section-label section-label--caps section-label--blue">${t('opportunity_details')}</div>
        ${detailFactRow(t('label_category'), categoryLabel(r.category))}
        ${detailFactRow(t('label_deadline'), r.deadline || t('deadline_check'), 'calendar')}
        ${detailFactRow(t('label_eligibility'), r.eligibility || t('label_see_website'), 'user')}
        ${detailFactRow(t('label_benefit'), benefitLine(r), 'spark')}
      </div>
      <div class="dash-card">
        <div class="section-label section-label--caps section-label--green">${t('ai_summary')}</div>
        <p class="summary-text">${esc(aiSummary(r))}</p>
      </div>
    </div>
    ${r.needs_manual_search || r.apply_label === 'search_on_site' ? `
    <div class="info-banner info-banner--amber" role="status" style="margin-top:12px">${esc(t('apply_manual_hint'))}</div>` : ''}
    <div class="detail-actions detail-actions--rich" style="margin-top:16px">
      <a class="btn btn-primary btn-visit-main" id="btnVisitPrimary" href="${esc(r.url)}" target="_blank" rel="noopener">${applyButtonLabel(r)} ${ico('external')}</a>
      <button type="button" class="btn btn-outline btn-icon-action" id="btnShareWa" aria-label="Share">${ico('share')}</button>
      <button type="button" class="btn btn-outline btn-icon-action btn-outline--amber ${isFollowedUrl(r.url) ? 'btn-outline--active' : ''}" id="btnFollowDetail" aria-label="Save">${ico('bookmark')}</button>
      <button type="button" class="btn btn-outline btn-icon-action ${isNotifyOn(r.url) ? 'btn-outline--active notify-btn--active' : ''}" id="btnNotifyDetail" aria-label="${t('notify_me')}">${ico('bell')}</button>
    </div>`;
}

function detailFactRow(label, value, iconName) {
  return `
    <div class="detail-fact-row">
      <span class="detail-fact-icon">${ico(iconName || 'spark')}</span>
      <div><span class="detail-fact-label">${esc(label)}</span><span class="detail-fact-value">${esc(value)}</span></div>
    </div>`;
}

function chatBubbleHtml(m) {
  if (m.role === 'bot') {
    return `<div class="chat-row bot"><div class="chat-avatar">${ico('bot')}</div><div class="bubble bot">${formatAssistantText(m.text)}</div></div>`;
  }
  return `<div class="chat-row user"><div class="bubble user">${esc(m.text)}</div></div>`;
}

function renderAssistant() {
  const history = JSON.parse(sessionStorage.getItem('inzira_chat') || '[]');
  const welcome = history.length ? '' : `<div class="chat-row bot"><div class="chat-avatar chat-avatar--green">${ico('bot')}</div><div class="bubble bot">${esc(t('assistant_welcome'))}</div></div>`;
  const msgs = history.map((m) => chatBubbleHtml(m)).join('');
  const suggestions = [
    { q: 'scholarships Rwanda 2025', label: t('pop_scholarships') },
    { q: 'MIFOTRA jobs youth', label: t('pop_jobs') },
    { q: 'WDA free skills training', label: t('pop_wda') },
    { q: 'HEC university scholarships', label: t('pop_hec') },
  ].map((s) =>
    `<button type="button" class="query-chip query-chip--blue suggestion-chip" data-suggest="${esc(s.q)}">${esc(s.label)}</button>`
  ).join('');
  return `
    <div class="inzira-topbar">
      <div>
        <h1>${t('assistant_title_short')}</h1>
        <p class="inzira-topbar__sub">${t('assistant_sub_short')}</p>
      </div>
      <div class="inzira-topbar__actions">
        <button type="button" class="icon-btn" id="btnClearChat" aria-label="Clear">${ico('trash')}</button>
      </div>
    </div>
    <div class="dash-grid dash-grid--assistant">
      <div class="dash-card chat-panel-card">
        <div class="chat-messages chat-messages--shell" id="chatMessages">${welcome}${msgs}</div>
        <div class="chat-compose chat-compose--rich">
          <div class="suggestions suggestions--rich" id="chatSuggestions">${suggestions}</div>
          <div class="chat-input-row">
            <button type="button" class="voice-btn voice-btn--chat" id="btnVoiceSearch" aria-label="${t('voice_search')}">🎤</button>
            <input id="chatInput" type="text" placeholder="${t('ask_placeholder')}" autocomplete="off">
            <button type="button" class="chat-send chat-send--amber" id="chatSend" aria-label="Send">${ico('send')}</button>
          </div>
        </div>
      </div>
      ${renderPageMotionBlock()}
      ${renderAssistantHelpPanel()}
    </div>`;
}

function renderFollowed() {
  const items = state.followed;
  const alertN = items.filter((s) => isNotifyOn(s.url)).length;
  return `
    <div class="inzira-topbar">
      <div>
        <h1>${t('followed_title')}</h1>
        <p class="inzira-topbar__sub">${t('followed_notify_sub', { n: items.length, a: alertN })}</p>
        <p class="sheet-desc" style="margin-top:6px">${t('notify_saved_hint')}</p>
      </div>
    </div>
    ${renderStatsStrip([
      { value: String(items.length), label: t('nav_saved'), tone: 'green' },
      { value: String(alertN), label: t('notifications'), tone: 'amber' },
      { value: String(registryOpportunityCount() || 0), label: t('brand_stat_sites'), tone: 'blue' },
    ], { present: true })}
    ${renderPageMotionBlock()}
    <div class="followed-list" id="followedList" style="margin-top:16px">
    ${items.length === 0
      ? emptyStateHtml(t('no_followed'), t('no_followed_sub'), t('search_now'), 'home')
      : items.map((s, i) => `
        <div class="followed-card followed-card--rich dash-card" style="margin-bottom:12px" data-followed-idx="${i}">
          <button type="button" class="followed-card__open btn-open-followed" data-url="${encodeURIComponent(s.url)}" data-title="${esc(s.title || domain(s.url))}">
            <div class="followed-top">
              <div class="followed-card__icon followed-card__icon--${['blue', 'green', 'amber'][i % 3]}">${ico('bookmark')}</div>
              <div class="followed-card__copy">
                <div class="result-title">${esc(s.title || domain(s.url))}</div>
                <div class="result-url">${esc(domain(s.url))}</div>
                <span class="tag tag-${['blue', 'green', 'amber'][i % 3]}">${esc(categoryLabel(s.category || ''))}</span>
              </div>
            </div>
          </button>
          <div class="followed-card__actions">
            <button type="button" class="btn btn-ghost btn-sm btn-unfollow" data-idx="${i}">${t('unfollow')}</button>
            <button type="button" class="btn btn-outline btn-sm notify-btn${isNotifyOn(s.url) ? ' notify-btn--active' : ''}" data-notify-idx="${i}" aria-label="${t('notify_me')}">${ico('bell')} ${isNotifyOn(s.url) ? t('notify_on') : t('notify_me')}</button>
            <button type="button" class="btn btn-outline btn-sm btn-preview-followed" data-url="${encodeURIComponent(s.url)}" data-title="${esc(s.title || domain(s.url))}">${t('preview')}</button>
            <a class="btn btn-primary btn-sm btn-visit-followed" href="${esc(s.url)}" target="_blank" rel="noopener">${t('visit_website')}</a>
          </div>
        </div>`).join('')}
    </div>
    ${renderSavedTipsCard()}`;
}

function renderAdmin() {
  return `
    <div class="inzira-topbar">
      <div>
        <h1>Admin</h1>
        <p class="inzira-topbar__sub">Platform overview</p>
      </div>
      <div class="inzira-topbar__actions">
        <button type="button" class="btn btn-outline btn-sm" data-go="settings">Settings</button>
      </div>
    </div>
    <div id="adminPanel" class="dash-grid dash-grid--settings">
      <div class="dash-card"><p class="empty">${t('loading_results')}</p></div>
    </div>`;
}

function notificationStatus() {
  if (!('Notification' in window)) {
    return { label: t('notif_unsupported_short'), mode: 'unsupported' };
  }
  if (Notification.permission === 'granted' && localStorage.getItem('inzira_notif') === '1') {
    return { label: t('on'), mode: 'on' };
  }
  if (Notification.permission === 'denied') {
    return { label: t('notif_blocked_short'), mode: 'blocked' };
  }
  return { label: t('notif_off'), mode: 'off' };
}

function openNotificationHelpModal() {
  openModal(t('notifications'), `
    <p>${t('notify_blocked_help')}</p>
    <ol style="margin:12px 0 0 18px;line-height:1.6">
      <li>${t('notify_blocked_step1')}</li>
      <li>${t('notify_blocked_step2')}</li>
      <li>${t('notify_blocked_step3')}</li>
    </ol>
    <p style="margin-top:14px;color:var(--text-secondary)">${t('notify_blocked_note')}</p>
  `);
}

function renderSettings() {
  const u = state.user || {};
  const notif = notificationStatus();
  const rows = [
    { id: 'rowBackend', label: t('backend'), value: `${esc(InziraApi.baseUrl())} ›`, icon: 'search', tone: 'blue' },
    { label: t('district'), value: `${esc(u.district || t('not_set'))} ›`, icon: 'user', tone: 'green' },
    { label: t('language'), value: `${state.lang === 'rw' ? t('lang_rw_name') : t('lang_en_name')} ›`, icon: 'world', tone: 'amber' },
    { id: 'rowNotifications', label: t('notifications'), value: `${notif.label} ›`, icon: 'bell', tone: notif.mode === 'blocked' ? 'amber' : 'blue' },
    { id: 'rowShowHow', label: t('how_inzira_works'), value: '›', icon: 'spark', tone: 'green' },
  ];
  const adminSection = u.role === 'admin' ? `
        <p class="settings-section-label settings-section-label--blue">Administration</p>
        <div class="settings-group settings-group--rich">
          <div class="settings-row settings-row--rich settings-row--highlight" data-go="admin">
            <span class="settings-row__icon settings-row__icon--blue">${ico('shield')}</span>
            <span>Admin dashboard</span><span class="settings-value">›</span>
          </div>
        </div>` : '';
  return `
    <div class="inzira-topbar">
      <div>
        <h1>${t('settings_title')}</h1>
        <p class="inzira-topbar__sub">${t('platform_tagline')}</p>
      </div>
    </div>
    <div class="dash-grid dash-grid--settings">
      <div class="dash-card">
        <div class="profile-card-rich">
          <div class="avatar avatar--green">${initials(u.name)}</div>
          <div>
            <div class="profile-name">${esc(u.name || 'User')}</div>
            <div class="profile-email">${esc(u.email || '')}</div>
          </div>
          <button type="button" class="btn btn-signout btn-signout--inline" id="btnSignOutSettings">${ico('logout')} ${t('sign_out')}</button>
        </div>
        <p class="settings-section-label settings-section-label--blue">${t('preferences')}</p>
        <div class="settings-group settings-group--rich">
          ${rows.map((r) => `
          <div class="settings-row settings-row--rich" ${r.id ? `id="${r.id}"` : ''}>
            <span class="settings-row__icon settings-row__icon--${r.tone}">${ico(r.icon)}</span>
            <span>${r.label}</span>
            <span class="settings-value">${r.value}</span>
          </div>`).join('')}
        </div>
        <p class="sheet-desc" style="margin:8px 4px 0">${t('notify_when')}</p>
        ${adminSection}
        <p class="settings-section-label settings-section-label--green">${t('institution_access')}</p>
        <div class="settings-group settings-group--rich">
          <button type="button" class="settings-row settings-row--rich settings-row--highlight" id="rowMifotra" data-go="mifotra">
            <span class="settings-row__icon settings-row__icon--amber">${ico('shield')}</span>
            <span>${t('mifotra')}</span><span class="settings-value">›</span>
          </button>
        </div>
        <p class="settings-section-label settings-section-label--amber">${t('account_section')}</p>
        <div class="settings-group settings-group--rich">
          <button type="button" class="settings-row settings-row--rich" data-go="privacy-policy">
            <span class="settings-row__icon settings-row__icon--blue">${ico('shield')}</span>
            <span>${t('privacy_policy_link')}</span><span class="settings-value">›</span>
          </button>
          <div class="settings-row settings-row--rich danger" id="btnDeleteAccount">
            <span class="settings-row__icon settings-row__icon--red">${ico('trash')}</span>
            <span>${t('delete_account')}</span><span class="settings-value">›</span>
          </div>
        </div>
        <div class="lang-row settings-lang">
          <button type="button" class="lang-chip ${state.lang === 'en' ? 'active' : ''}" data-lang="en">${t('lang_en_name')}</button>
          <button type="button" class="lang-chip ${state.lang === 'rw' ? 'active' : ''}" data-lang="rw">${t('lang_rw_name')}</button>
        </div>
      </div>
      <div class="dash-card">
        ${renderStatsStrip(null, { hero: true })}
        ${renderRwandaGlance()}
      </div>
    </div>`;
}

function renderLegalSection(titleKey, itemKeys) {
  return `
    <section class="legal-section">
      <h2>${t(titleKey)}</h2>
      <ul class="legal-list">
        ${itemKeys.map((key) => `<li>${t(key)}</li>`).join('')}
      </ul>
    </section>`;
}

function renderPrivacyPolicy() {
  const backTo = state.user ? 'settings' : (localStorage.getItem('inzira_onboarded') === '1' ? 'login' : 'language');
  return `
    ${renderAppTopbar({ title: t('privacy_policy_title'), sub: t('privacy_policy_sub'), backTo })}
    <div class="info-page info-page--legal dash-card">
      <p class="legal-intro">${t('privacy_policy_intro')}</p>
      ${renderLegalSection('privacy_sec_collect_title', [
        'privacy_sec_collect_1',
        'privacy_sec_collect_2',
        'privacy_sec_collect_3',
        'privacy_sec_collect_4',
      ])}
      ${renderLegalSection('privacy_sec_use_title', [
        'privacy_sec_use_1',
        'privacy_sec_use_2',
        'privacy_sec_use_3',
        'privacy_sec_use_4',
      ])}
      ${renderLegalSection('privacy_sec_rights_title', [
        'privacy_sec_rights_1',
        'privacy_sec_rights_2',
        'privacy_sec_rights_3',
        'privacy_sec_rights_4',
      ])}
      ${renderLegalSection('privacy_sec_security_title', [
        'privacy_sec_security_1',
        'privacy_sec_security_2',
        'privacy_sec_security_3',
      ])}
      <section class="legal-section">
        <h2>${t('privacy_sec_contact_title')}</h2>
        <p class="legal-contact">${t('privacy_sec_contact_body')} <a href="mailto:inzira.app@gmail.com">inzira.app@gmail.com</a></p>
      </section>
    </div>`;
}

function renderMifotra() {
  return `
    ${renderAppTopbar({ title: t('mifotra_login_title'), sub: '@mifotra.gov.rw', backTo: state.user ? 'settings' : 'login' })}
    <div class="dash-card app-form-card">
      <p class="sheet-desc" style="margin-bottom:16px">${t('mifotra_sign_in')}</p>
      <form id="mifotraForm">
        <div class="input-icon-wrap">
          <span class="input-icon">${ico('mail')}</span>
          <input type="email" name="email" placeholder="name@mifotra.gov.rw" required autocomplete="email">
        </div>
        <div class="input-icon-wrap">
          <span class="input-icon">${ico('lock')}</span>
          <input type="password" name="password" required autocomplete="current-password">
        </div>
        <button type="submit" class="btn btn-primary btn-primary--block">${t('mifotra_sign_in')}</button>
      </form>
    </div>`;
}

function renderDashboard() {
  return `
    <section class="dashboard-present-banner">
      <button type="button" class="dashboard-present-banner__back icon-btn" data-go="home" aria-label="Back">${ico('back')}</button>
      <div class="dashboard-present-banner__icon">${ico('shield')}</div>
      <div class="dashboard-present-banner__copy">
        <span class="dashboard-present-banner__eyebrow">MIFOTRA · ${t('rwanda')}</span>
        <h1>${t('nav_mifotra_analytics')}</h1>
        <p>${t('present_dashboard_sub')}</p>
      </div>
      <span class="live-pill live-pill--green"><span class="live-dot"></span> Live</span>
    </section>
    <div id="dashboardContent" class="dashboard-present-body">
      <div class="loading"><div class="spinner"></div><p>${t('loading_results')}</p></div>
    </div>`;
}

window.addEventListener('hashchange', render);
window.addEventListener('load', () => {
  // Paint login/home immediately — HF Space iframe can block Firebase until timeout.
  render();
  purgeStaleAppCache().then(async () => {
    try { await loadAppConfig(); } catch (_) {}
    try {
      await Promise.race([
        initFirebaseAuth(),
        new Promise((resolve) => setTimeout(resolve, 5000)),
      ]);
    } catch (_) {}
    render();
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register(`/sw.js?v=${APP_BUILD}`).then((reg) => reg.update()).catch(() => {});
    }
  });
});

async function purgeStaleAppCache() {
  const key = 'inzira_build';
  if (localStorage.getItem(key) === APP_BUILD) return;
  localStorage.setItem(key, APP_BUILD);
  if ('serviceWorker' in navigator) {
    const regs = await navigator.serviceWorker.getRegistrations();
    await Promise.all(regs.map((r) => r.unregister()));
  }
  if (typeof caches !== 'undefined') {
    const keys = await caches.keys();
    await Promise.all(keys.map((k) => caches.delete(k)));
  }
}

// ── Modals & preview ─────────────────────────────────────────
function openModal(title, bodyHtml) {
  const root = $modalRoot();
  const panel = $modalPanel();
  if (!root || !panel) return;
  panel.innerHTML = `
    <button type="button" class="modal-close" id="modalCloseBtn" aria-label="${t('close')}">×</button>
    <h2>${esc(title)}</h2>
    ${bodyHtml}`;
  root.classList.remove('hidden');
  root.setAttribute('aria-hidden', 'false');
  document.getElementById('modalCloseBtn')?.addEventListener('click', closeModal);
  document.getElementById('modalBackdrop')?.addEventListener('click', closeModal);
}

function closeModal() {
  const root = $modalRoot();
  if (!root) return;
  root.classList.add('hidden');
  root.setAttribute('aria-hidden', 'true');
}

function openConfirmModal(title, message, confirmLabel, onConfirm) {
  openModal(title, `
    <p>${esc(message)}</p>
    <div class="modal-actions">
      <button type="button" class="btn btn-outline" id="modalCancelBtn">${t('cancel')}</button>
      <button type="button" class="btn btn-primary btn-danger" id="modalConfirmBtn">${esc(confirmLabel)}</button>
    </div>`);
  document.getElementById('modalCancelBtn')?.addEventListener('click', closeModal);
  document.getElementById('modalConfirmBtn')?.addEventListener('click', async () => {
    closeModal();
    await onConfirm();
  });
}

function openTrustModal() {
  openModal(t('trust_what'), `<p>${esc(t('trust_explain'))}</p>`);
}

function openPreview(url, title) {
  const root = $previewRoot();
  const frame = document.getElementById('previewFrame');
  const ext = document.getElementById('previewOpenExternal');
  if (!root || !frame) {
    window.open(url, '_blank', 'noopener');
    return;
  }
  document.getElementById('previewTitle').textContent = title || domain(url);
  frame.src = url;
  if (ext) ext.href = url;
  root.classList.remove('hidden');
  root.setAttribute('aria-hidden', 'false');
}

function closePreview() {
  const root = $previewRoot();
  const frame = document.getElementById('previewFrame');
  if (root) {
    root.classList.add('hidden');
    root.setAttribute('aria-hidden', 'true');
  }
  if (frame) frame.src = 'about:blank';
}

function invalidateYouthData() {
  state.youthDataLoaded = false;
  state.youthDataLoading = false;
  state.matches = [];
  state.radarDistricts = [];
  state.insights = [];
}

function bindGlobalUI() {
  if (!window._inziraNavBound) {
    window._inziraNavBound = true;
    document.addEventListener('click', (e) => {
      const scrollBtn = e.target.closest('[data-scroll]');
      if (scrollBtn?.dataset.scroll) {
        e.preventDefault();
        const targetId = scrollBtn.dataset.scroll;
        const { path } = parseRoute();
        if (path !== 'home' && path !== 'search') {
          navigate('home');
          setTimeout(() => document.getElementById(targetId)?.scrollIntoView({ behavior: 'smooth' }), 300);
        } else {
          document.getElementById(targetId)?.scrollIntoView({ behavior: 'smooth' });
        }
        return;
      }
      const go = e.target.closest('[data-go]');
      if (go?.dataset.go) {
        e.preventDefault();
        navigate(go.dataset.go);
        return;
      }
      const quick = e.target.closest('[data-quick-search]');
      if (quick?.dataset.quickSearch) {
        e.preventDefault();
        const q = quick.dataset.quickSearch;
        saveRecentSearch(q);
        navigate(`results?q=${encodeURIComponent(q)}`);
      }
    });
  }
  document.getElementById('previewClose')?.addEventListener('click', closePreview);
  document.getElementById('previewBackdrop')?.addEventListener('click', closePreview);
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      dismissToast();
      closeModal();
      closePreview();
    }
  });

  if (!window._inziraToastBound) {
    window._inziraToastBound = true;
    document.addEventListener('click', () => {
      if ($toast?.classList.contains('show') && toastDismissOnClick) dismissToast();
    });
    $toast?.addEventListener('click', (e) => {
      e.stopPropagation();
      dismissToast();
    });
  }
}

function shareWhatsApp(text, url) {
  const msg = encodeURIComponent(`${text}\n${url}`);
  window.open(`https://wa.me/?text=${msg}`, '_blank', 'noopener');
}

function shareCopyLink(url) {
  navigator.clipboard?.writeText(url).then(() => toast(t('link_copied'))).catch(() => toast(url));
}

function saveRecentSearch(q) {
  const key = 'inzira_recent_searches';
  let list = JSON.parse(localStorage.getItem(key) || '[]');
  list = [q, ...list.filter((x) => x !== q)].slice(0, 6);
  localStorage.setItem(key, JSON.stringify(list));
}

function getRecentSearches() {
  return JSON.parse(localStorage.getItem('inzira_recent_searches') || '[]');
}

function getPopularQueries() {
  const d = state.user?.district;
  return (d && POPULAR_QUERIES[d]) ? POPULAR_QUERIES[d] : POPULAR_QUERIES.default;
}

function skeletonHtml(n = 6) {
  return `<div class="skeleton-grid">${Array.from({ length: n }, () => `
    <div class="skeleton-card">
      <div class="skeleton-line h20 w60"></div>
      <div class="skeleton-line w40"></div>
      <div class="skeleton-line w80"></div>
      <div class="skeleton-line w60"></div>
    </div>`).join('')}</div>`;
}

function emptyStateHtml(title, desc, btnLabel, btnAction) {
  return `
    <div class="empty-state">
      <div class="empty-icon">I</div>
      <h3>${esc(title)}</h3>
      <p>${esc(desc)}</p>
      ${btnLabel ? `<button type="button" class="btn btn-primary" data-go="${btnAction || 'search'}">${esc(btnLabel)}</button>` : ''}
    </div>`;
}

function sortResults(results, sortBy) {
  const list = [...results];
  if (sortBy === 'deadline') {
    list.sort((a, b) => {
      const da = a.deadline || 'zzz';
      const db = b.deadline || 'zzz';
      return da.localeCompare(db);
    });
  } else {
    list.sort((a, b) => b.trust_score - a.trust_score);
  }
  return list;
}

async function enableNotifications() {
  if (!('Notification' in window)) {
    toast(t('notify_unsupported'), { error: true });
    return false;
  }
  const perm = await Notification.requestPermission();
  localStorage.setItem('inzira_notif', perm === 'granted' ? '1' : '0');
  if (perm === 'granted') {
    const pushOk = await registerBackgroundPush();
    toast(t('notif_on'));
    new Notification('Inzira', {
      body: pushOk ? t('notif_on_push_body') : t('notif_on_foreground_body'),
      icon: '/assets/icons/icon-192.svg',
    });
    startDeadlineWatch();
    return true;
  }
  toast(perm === 'denied' ? t('notify_blocked') : t('notif_off'), { error: perm === 'denied' });
  return false;
}

function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const raw = atob(base64);
  const arr = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; ++i) arr[i] = raw.charCodeAt(i);
  return arr;
}

async function registerBackgroundPush() {
  if (!state.idToken) return false;
  if (!('serviceWorker' in navigator) || !('PushManager' in window)) return false;
  try {
    await ensureFreshToken();
    const cfg = await InziraApi.vapidPublicKey();
    if (!cfg?.configured || !cfg.publicKey) return false;
    const reg = await navigator.serviceWorker.ready;
    let sub = await reg.pushManager.getSubscription();
    if (!sub) {
      sub = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(cfg.publicKey),
      });
    }
    const json = sub.toJSON();
    await InziraApi.pushSubscribe({
      endpoint: json.endpoint,
      keys: {
        p256dh: json.keys?.p256dh,
        auth: json.keys?.auth,
      },
    });
    localStorage.setItem('inzira_push_registered', '1');
    return true;
  } catch (err) {
    console.warn('Background push registration failed:', err);
    return false;
  }
}

function loadNotifyDomains() {
  try {
    return new Set(JSON.parse(localStorage.getItem(NOTIFY_DOMAINS_KEY) || '[]'));
  } catch (_) {
    return new Set();
  }
}

function saveNotifyDomains(domains) {
  localStorage.setItem(NOTIFY_DOMAINS_KEY, JSON.stringify([...domains]));
}

function isNotifyOn(url) {
  const dom = domain(url);
  if (!dom) return false;
  const saved = state.followed?.find((s) => (s.domain || domain(s.url)) === dom);
  if (saved && typeof saved.notify_enabled === 'boolean') return saved.notify_enabled;
  return loadNotifyDomains().has(dom);
}

function syncNotifyDomainsFromFollowed() {
  const domains = new Set(
    (state.followed || [])
      .filter((s) => s.notify_enabled)
      .map((s) => s.domain || domain(s.url))
      .filter(Boolean)
  );
  saveNotifyDomains(domains);
}

function removeNotifyDomain(url) {
  const dom = domain(url);
  if (!dom) return;
  const domains = loadNotifyDomains();
  if (!domains.delete(dom)) return;
  saveNotifyDomains(domains);
  syncNotifyButtons(dom, false);
}

async function ensureNotificationPermission() {
  if (!('Notification' in window)) {
    toast(t('notify_unsupported'), { error: true });
    return false;
  }
  if (Notification.permission === 'granted') {
    localStorage.setItem('inzira_notif', '1');
    return true;
  }
  if (Notification.permission === 'denied') {
    toast(t('notify_blocked'), { error: true, sticky: true });
    return false;
  }
  return enableNotifications();
}

function syncNotifyButtons(dom, active) {
  document.querySelectorAll('.notify-btn').forEach((btn) => {
    const idx = btn.dataset.notifyIdx;
    const url = btn.dataset.notifyUrl;
    let match = false;
    if (idx != null) {
      const item = getNotifyItemByIdx(Number(idx));
      match = item && domain(item.url) === dom;
    } else if (url) {
      match = domain(url) === dom;
    }
    if (!match) return;
    btn.classList.toggle('notify-btn--active', active);
    if (btn.id === 'btnNotifyDetail') {
      btn.classList.toggle('btn-outline--active', active);
    }
    if (btn.textContent && btn.textContent.includes(t('notify_me'))) {
      btn.innerHTML = `${ico('bell')} ${active ? t('notify_on') : t('notify_me')}`;
    }
  });
}

function getNotifyItemByIdx(idx) {
  const pools = [state.dashboardOpps, state.matches, state.results, state.followed];
  for (const pool of pools) {
    if (pool?.[idx]) return pool[idx];
  }
  return null;
}

function notifyFollowSaved(title, deadline) {
  if (localStorage.getItem('inzira_notif') !== '1' || Notification.permission !== 'granted') return;
  const body = deadline
    ? `${title}: deadline found — ${deadline}. We will alert you if it changes or gets close.`
    : `${title} is on your watch list. Inzira scans saved sites for deadlines while you use the app.`;
  new Notification('Inzira — alerts on', {
    body,
    icon: '/assets/icons/icon-192.svg',
  });
}

async function runDeadlineWatch(force = false) {
  if (!state.idToken || Notification.permission !== 'granted') return;
  if (localStorage.getItem('inzira_notif') !== '1') return;
  const hasAlerts = (state.followed || []).some((s) => s.notify_enabled);
  if (!hasAlerts) return;
  const last = Number(localStorage.getItem(ALERT_LAST_KEY) || 0);
  if (!force && Date.now() - last < ALERT_CHECK_MS) return;
  try {
    await ensureFreshToken();
    const data = await InziraApi.alertCheck();
    localStorage.setItem(ALERT_LAST_KEY, String(Date.now()));
    (data.alerts || []).forEach((a) => {
      const days = a.days_left != null ? ` (${a.days_left} days left)` : '';
      new Notification('Inzira — deadline alert', {
        body: `${a.title}: ${a.deadline}${days}`,
        icon: '/assets/icons/icon-192.svg',
      });
    });
    if (data.scanned) await refreshSavedFromServer(true);
  } catch (_) {}
}

function startDeadlineWatch() {
  runDeadlineWatch(true);
  if (deadlineWatchTimer) clearInterval(deadlineWatchTimer);
  deadlineWatchTimer = setInterval(() => runDeadlineWatch(false), ALERT_CHECK_MS);
}

async function toggleNotifyForSite(r, btn) {
  const dom = domain(r.url);
  if (!dom) return;
  const domains = loadNotifyDomains();
  const turningOn = !domains.has(dom);

  if (turningOn) {
    const ok = await ensureNotificationPermission();
    if (!ok) return;
    if (!isFollowedUrl(r.url)) {
      await toggleFollowSite(r, null);
      if (!isFollowedUrl(r.url)) return;
    }
    domains.add(dom);
    saveNotifyDomains(domains);
    if (state.idToken) {
      try {
        await ensureFreshToken();
        await InziraApi.savedNotify(dom, true);
        const item = state.followed.find((s) => (s.domain || domain(s.url)) === dom);
        if (item) item.notify_enabled = true;
      } catch (err) {
        toast(err?.body?.detail || err?.message || t('request_failed'), { error: true });
        return;
      }
    }
    notifyFollowSaved(websiteName(r), r.deadline || '');
    toast(t('notify_enabled_toast'));
    syncNotifyButtons(dom, true);
    startDeadlineWatch();
    registerBackgroundPush();
  } else {
    domains.delete(dom);
    saveNotifyDomains(domains);
    if (state.idToken) {
      try {
        await ensureFreshToken();
        await InziraApi.savedNotify(dom, false);
        const item = state.followed.find((s) => (s.domain || domain(s.url)) === dom);
        if (item) item.notify_enabled = false;
      } catch (_) {}
    }
    toast(t('notify_disabled_toast'));
    syncNotifyButtons(dom, false);
  }
}

function bindNotifyButtons(getItemByIdx, getItemByUrl) {
  document.querySelectorAll('.notify-btn[data-notify-idx]').forEach((btn) => {
    btn.onclick = async (e) => {
      e.preventDefault();
      e.stopPropagation();
      const idx = Number(btn.dataset.notifyIdx);
      const item = getItemByIdx?.(idx) || getNotifyItemByIdx(idx);
      if (!item) return;
      await toggleNotifyForSite(item, btn);
    };
  });
  document.querySelectorAll('.notify-btn[data-notify-url]').forEach((btn) => {
    btn.onclick = async (e) => {
      e.preventDefault();
      e.stopPropagation();
      const item = getItemByUrl?.(btn.dataset.notifyUrl) || state.results?.find((r) => r.url === btn.dataset.notifyUrl);
      if (!item) return;
      await toggleNotifyForSite(item, btn);
    };
  });
}

// ── Auth ─────────────────────────────────────────────────────
function firebaseConfigured() {
  const c = window.INZIRA_FIREBASE_CONFIG || {};
  return !!(window.firebase && c && c.apiKey && c.apiKey !== 'YOUR_API_KEY');
}

function firebaseInit() {
  if (!firebaseConfigured()) return false;
  if (firebase.apps && firebase.apps.length) return true;
  firebase.initializeApp(window.INZIRA_FIREBASE_CONFIG);
  return true;
}

function setIdToken(token) {
  state.idToken = (token || '').trim();
  if (state.idToken) sessionStorage.setItem('inzira_id_token', state.idToken);
  else sessionStorage.removeItem('inzira_id_token');
  window.__inziraAuthToken = state.idToken;
}
window.__inziraSetAuthToken = (token) => setIdToken(token);

function clearLocalSession(clearProfile = true) {
  setIdToken('');
  state.followed = [];
  state.savedLoaded = false;
  if (clearProfile) {
    state.user = null;
    localStorage.removeItem('inzira_user_cache');
    localStorage.removeItem('inzira_saved_cache');
  }
}

async function waitForFirebaseUser(maxMs = 5000) {
  if (!firebaseInit()) return null;
  if (authBootstrapPromise) {
    try { await authBootstrapPromise; } catch (_) {}
  }
  if (firebase.auth().currentUser) return firebase.auth().currentUser;
  const start = Date.now();
  while (Date.now() - start < maxMs) {
    await new Promise((r) => setTimeout(r, 120));
    if (firebase.auth().currentUser) return firebase.auth().currentUser;
  }
  return firebase.auth().currentUser;
}

async function repairAuthSession() {
  const user = await waitForFirebaseUser(4000);
  if (!user) return '';
  return ensureFreshToken();
}

async function refreshSavedFromServer(force = false) {
  if (!state.idToken) return;
  if (state.savedLoaded && !force) return;
  const cached = JSON.parse(localStorage.getItem('inzira_saved_cache') || '[]');
  if (cached.length && !state.followed.length) {
    state.followed = cached;
  }
  try {
    const data = await InziraApi.savedList();
    const items = data.items || [];
    if (items.length) {
      state.followed = items;
    } else if (!state.followed.length && cached.length) {
      state.followed = cached;
    }
    localStorage.setItem('inzira_saved_cache', JSON.stringify(state.followed));
    syncNotifyDomainsFromFollowed();
    state.savedLoaded = true;
  } catch (_) {
    if (!state.followed.length && cached.length) {
      state.followed = cached;
    }
  }
}

function getRegisterName() {
  return (document.getElementById('registerName')?.value || '').trim();
}

function validateRegisterName() {
  if (!getRegisterName()) {
    toast(t('register_name_required'));
    return false;
  }
  return true;
}

async function persistRegisterName() {
  const name = getRegisterName();
  if (!name) return;
  const fbUser = firebase.auth().currentUser;
  if (!fbUser) return;
  await fbUser.updateProfile({ displayName: name });
  const token = await fbUser.getIdToken(true);
  setIdToken(token);
  await InziraApi.updateProfile({ name });
}

async function ensureFreshToken() {
  if (!firebaseInit()) {
    setIdToken('');
    return '';
  }
  const fbUser = firebase.auth().currentUser || await waitForFirebaseUser(3000);
  if (!fbUser) {
    setIdToken('');
    return '';
  }
  try {
    const token = await fbUser.getIdToken(true);
    setIdToken(token);
    return token;
  } catch (_) {
    setIdToken('');
    return '';
  }
}

async function handleAuthFailure(err, context = 'action') {
  const repaired = await repairAuthSession();
  if (repaired) return repaired;

  if (err?.status === 401) {
    clearLocalSession(true);
    toast(t('session_expired'), { error: true, sticky: true });
    sessionStorage.setItem('inzira_post_login_route', location.hash || '#/home');
    navigate('login');
    return '';
  }

  const detail = err?.body?.detail;
  const msg = typeof detail === 'string'
    ? detail
    : (err?.message || (context === 'save' ? t('saved_failed') : t('request_failed')));
  toast(msg, { error: true, sticky: true });
  return '';
}

function handleAuthExpired() {
  clearLocalSession(true);
  toast(t('session_expired'), { error: true, sticky: true });
  sessionStorage.setItem('inzira_post_login_route', location.hash || '#/home');
  navigate('login');
}

async function trySaveMatchProfile(profileBody) {
  if (!firebaseInit() || !firebase.auth().currentUser) return;
  try {
    await ensureFreshToken();
    await InziraApi.updateProfile(profileBody);
  } catch (err) {
    console.warn('Profile save skipped:', err?.body?.detail || err.message);
  }
}

async function hydrateUserFromFirebase(fbUser) {
  if (!fbUser) return false;
  const token = await fbUser.getIdToken(true);
  setIdToken(token);
  try {
    const me = await InziraApi.me();
    const displayName = me.name || fbUser.displayName || me.email || me.phone || 'User';
    state.user = {
      name: displayName,
      email: me.email || fbUser.email || '',
      phone: me.phone || fbUser.phoneNumber || '',
      role: me.role || 'youth',
      district: me.profile?.district || '',
      age: me.profile?.age || '',
      education: me.profile?.education || '',
      skills: (me.profile?.skills || []).join(', '),
      interests: (me.profile?.interests || []).join(', '),
    };
  } catch (e) {
    if (e?.status === 401) {
      const repaired = await repairAuthSession();
      if (repaired) {
        try {
          const me = await InziraApi.me();
          state.user = {
            name: me.name || fbUser.displayName || me.email || 'User',
            email: me.email || fbUser.email || '',
            phone: me.phone || fbUser.phoneNumber || '',
            role: me.role || 'youth',
            district: me.profile?.district || '',
            age: me.profile?.age || '',
            education: me.profile?.education || '',
            skills: (me.profile?.skills || []).join(', '),
            interests: (me.profile?.interests || []).join(', '),
          };
        } catch (e2) {
          console.warn('Backend /me failed after token refresh', e2);
          clearLocalSession(true);
          toast(t('session_expired'), { error: true, sticky: true });
          navigate('login');
          return false;
        }
      } else {
        clearLocalSession(true);
        toast(t('session_expired'), { error: true, sticky: true });
        navigate('login');
        return false;
      }
    } else {
      console.warn('Backend /me unavailable; using Firebase profile', e);
      state.user = {
        name: fbUser.displayName || fbUser.email || 'User',
        email: fbUser.email || '',
        phone: fbUser.phoneNumber || '',
        role: 'youth',
        district: '',
        age: '',
        education: '',
        skills: '',
        interests: '',
      };
    }
  }
  state.savedLoaded = false;
  localStorage.setItem('inzira_user_cache', JSON.stringify(state.user));
  await refreshSavedFromServer();
  startDeadlineWatch();
  if (localStorage.getItem('inzira_notif') === '1' && Notification.permission === 'granted') {
    registerBackgroundPush();
  }
  return true;
}

function isAuthRoute(path) {
  return ['login', 'register', 'forgot-password'].includes(path);
}

async function initFirebaseAuth() {
  if (!firebaseInit()) return;
  if (authBootstrapPromise) return authBootstrapPromise;

  authBootstrapPromise = (async () => {
    try {
      await firebase.auth().setPersistence(firebase.auth.Auth.Persistence.LOCAL);
    } catch (_) {}

    if (typeof firebase.auth().authStateReady === 'function') {
      await firebase.auth().authStateReady();
    } else {
      await new Promise((resolve) => {
        const unsub = firebase.auth().onAuthStateChanged(() => {
          unsub();
          resolve();
        });
      });
    }

    const fbUser = firebase.auth().currentUser;
    if (fbUser) {
      await hydrateUserFromFirebase(fbUser);
    } else {
      clearLocalSession(true);
    }
    authBootstrapped = true;
  })();

  await authBootstrapPromise;

  firebase.auth().onAuthStateChanged(async (fbUser) => {
    if (!authBootstrapped) return;
    try {
      if (!fbUser) {
        clearLocalSession(true);
        const { path } = parseRoute();
        if (!isAuthRoute(path) && path !== 'language') navigate('login');
        else render();
        return;
      }
      await hydrateUserFromFirebase(fbUser);
      const { path } = parseRoute();
      if (isAuthRoute(path)) navigate('home');
      else render();
    } catch (e) {
      console.error(e);
      render();
    }
  });
}

async function syncFirebaseSession() {
  return initFirebaseAuth();
}

function renderNoAccountBanner() {
  return `<div class="auth-notice auth-notice--amber">
    <strong>${t('no_account_yet')}</strong>
    <p>${t('no_account_yet_sub')}</p>
    <button type="button" class="btn btn-primary btn-sm" data-go="register">${t('create_account')}</button>
  </div>`;
}

function saveUser(user, opts = {}) {
  state.user = user;
  localStorage.setItem('inzira_user_cache', JSON.stringify(user));
  if (opts.invalidate !== false) invalidateYouthData();
}

function logout() {
  if (firebaseInit()) {
    firebase.auth().signOut().catch(() => {});
  }
  setIdToken('');
  state.user = null;
  state.followed = [];
  state.savedLoaded = false;
  localStorage.removeItem('inzira_user_cache');
  localStorage.removeItem('inzira_saved_cache');
  invalidateYouthData();
  navigate('login');
}

async function deleteAccount() {
  if (!state.idToken) {
    toast(t('sign_in') + ' required');
    return;
  }
  openConfirmModal(
    t('delete_account'),
    t('delete_account_confirm'),
    t('delete_account'),
    async () => {
      try {
        const result = await InziraApi.deleteAccount();
        if (firebaseInit()) {
          await firebase.auth().signOut().catch(() => {});
        }
        setIdToken('');
        state.user = null;
        state.followed = [];
        state.savedLoaded = false;
        localStorage.removeItem('inzira_user_cache');
        localStorage.removeItem('inzira_saved_cache');
        invalidateYouthData();
        if (result.firebase_deleted === false) {
          toast(t('account_deleted_partial'));
        } else {
          toast(t('account_deleted'));
        }
        navigate('login');
      } catch (err) {
        toast(err?.body?.detail || err?.message || 'Delete failed');
      }
    }
  );
}

function initials(name) {
  return (name || 'U').split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();
}

// ── Bottom navigation (app layout) ───────────────────────────
function renderBottomNav(active) {
  const items = [
    { id: 'home', label: t('nav_home'), icon: 'home' },
    { id: 'search', label: t('nav_search'), icon: 'search' },
    { id: 'assistant', label: t('nav_assistant'), icon: 'bot' },
    { id: 'followed', label: t('nav_saved'), icon: 'bookmark' },
    { id: 'settings', label: t('nav_settings'), icon: 'settings' },
  ];
  const tabActive = active === 'home' ? 'home' : active;
  return items.map((i) => `
    <button type="button" class="bottom-nav-item${tabActive === i.id ? ' active' : ''}" data-go="${i.id}" aria-label="${esc(i.label)}" aria-current="${tabActive === i.id ? 'page' : 'false'}">
      <span class="bottom-nav-icon" aria-hidden="true">${ico(i.icon)}</span>
      <span class="bottom-nav-label">${esc(i.label)}</span>
    </button>`).join('');
}

// ── Event binding ────────────────────────────────────────────
function bindRouteEvents(path, query) {
  if (path === 'language') bindLanguage();
  if (path === 'login') bindLogin();
  if (path === 'forgot-password') bindForgotPassword();
  if (path === 'register') bindRegister();
  if (path === 'home' || path === 'search') {
    if (state.user) bindYouthHome();
    else bindGuestHome();
  }
  if (path === 'radar') bindRadarPage();
  if (path === 'matches') bindMatchesPage();
  if (path === 'matches-list') bindMatchesPage();
  if (path === 'opportunities' || path === 'sites') bindOpportunitiesPage();
  if (path === 'results') loadResults(query);
  if (path === 'detail') bindDetail();
  if (path === 'assistant') bindAssistant();
  if (path === 'followed') bindFollowed();
  if (path === 'settings') bindSettings();
  if (path === 'admin') bindAdmin();
  if (path === 'mifotra') bindMifotra();
  if (path === 'dashboard') loadDashboard();

  document.querySelectorAll('[data-lang]').forEach(btn => {
    btn.onclick = () => {
      setLanguage(btn.dataset.lang);
      render();
    };
  });

  document.getElementById('btnTopSignOut')?.addEventListener('click', logout);
  if (typeof bindWowFeatureUI === 'function') bindWowFeatureUI();
}

function bindDashSearchControls() {
  const form = document.getElementById('dashSearchForm');
  if (form) form.onsubmit = (e) => { e.preventDefault(); runDashSearch(); };
  const input = document.getElementById('dashSearchInput');
  if (input) {
    input.onkeydown = (e) => {
      if (e.key === 'Enter') { e.preventDefault(); runDashSearch(); }
    };
  }
  const heroBtn = document.getElementById('btnHeroSearch');
  if (heroBtn) heroBtn.onclick = (e) => { e.preventDefault(); runDashSearch(); };
  const dashBtn = document.getElementById('btnDashSearch');
  if (dashBtn) dashBtn.onclick = (e) => { e.preventDefault(); runDashSearch(); };
  document.querySelectorAll('[data-suggest]').forEach((btn) => {
    btn.onclick = (e) => {
      e.preventDefault();
      const q = btn.dataset.suggest || '';
      const inp = document.getElementById('dashSearchInput');
      if (inp) inp.value = q;
      runDashSearch();
    };
  });
}

/** Load home stats once — never call render() in a loop after every bind. */
function hydrateHomeStatsOnce() {
  if (state._homeStatsHydrated || state._homeStatsLoading) return;
  state._homeStatsLoading = true;
  Promise.all([loadRegistryStats(), loadImpactAndPathways()])
    .catch(() => {
      state.impactStats = state.impactStats || {
        opportunities_live: 0,
        verified_portals: 0,
        districts_covered: 0,
        youth_searches_month: 0,
      };
    })
    .finally(() => {
      state._homeStatsLoading = false;
      state._homeStatsHydrated = true;
      const { path } = parseRoute();
      if (path === 'home' || path === 'search') {
        mountRwandaMap('home');
        render();
      }
    });
}

function bindGuestHome() {
  bindDashSearchControls();
  mountRwandaMap('home');
  hydrateHomeStatsOnce();
}

function bindLanguage() {
  document.querySelectorAll('#langCards .lang-card').forEach((card) => {
    card.onclick = () => {
      setLanguage(card.dataset.lang);
      render();
    };
  });
  document.getElementById('btnLangContinue')?.addEventListener('click', () => {
    localStorage.setItem('inzira_lang', state.lang);
    localStorage.setItem('inzira_onboarded', '1');
    navigate('login');
  });
}

function bindLogin() {
  document.getElementById('btnTogglePwd')?.addEventListener('click', () => {
    const inp = document.getElementById('loginPassword');
    if (!inp) return;
    inp.type = inp.type === 'password' ? 'text' : 'password';
  });

  document.getElementById('btnForgotPassword')?.addEventListener('click', () => {
    const email = document.getElementById('loginEmail')?.value?.trim();
    if (email) sessionStorage.setItem('inzira_forgot_email', email);
    navigate('forgot-password');
  });

  document.getElementById('loginForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!firebaseInit()) {
      toast('Firebase is not configured yet');
      return;
    }
    const form = e.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const fd = new FormData(form);
    const email = String(fd.get('email') || '').trim().toLowerCase();
    const password = String(fd.get('password') || '');
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.dataset.label = submitBtn.textContent;
      submitBtn.textContent = 'Signing in…';
    }
    try {
      const cred = await firebase.auth().signInWithEmailAndPassword(email, password);
      await hydrateUserFromFirebase(cred.user);
      toast(t('welcome_back'));
      const returnRoute = sessionStorage.getItem('inzira_post_login_route');
      sessionStorage.removeItem('inzira_post_login_route');
      navigate(returnRoute ? returnRoute.replace(/^#\/?/, '') : 'home');
    } catch (err) {
      toast(formatAuthError(err), { error: true, sticky: true });
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = submitBtn.dataset.label || t('sign_in');
      }
    }
  });
}

function bindForgotPassword() {
  const forgotInput = document.getElementById('forgotEmail');
  const saved = sessionStorage.getItem('inzira_forgot_email');
  if (forgotInput && saved) {
    forgotInput.value = saved;
    sessionStorage.removeItem('inzira_forgot_email');
  }

  document.getElementById('forgotForm')?.addEventListener('submit', (e) => {
    e.preventDefault();
    if (!firebaseInit()) {
      toast('Firebase is not configured yet');
      return;
    }
    const email = String(new FormData(e.target).get('email') || '').trim().toLowerCase();
    if (!email) return;
    firebase.auth().sendPasswordResetEmail(email)
      .then(() => {
        toast(t('reset_link_sent'));
        navigate('login');
      })
      .catch((err) => {
        toast(err?.message || 'Could not send reset email');
      });
  });
}

function bindRegister() {
  document.getElementById('btnToggleRegPwd')?.addEventListener('click', () => {
    const inp = document.getElementById('registerPassword');
    if (!inp) return;
    inp.type = inp.type === 'password' ? 'text' : 'password';
  });

  document.getElementById('registerForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!firebaseInit()) {
      toast('Firebase is not configured yet');
      return;
    }
    if (!validateRegisterName()) return;
    const form = e.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const fd = new FormData(form);
    const email = fd.get('email').trim().toLowerCase();
    const password = fd.get('password');
    if (!password || password.length < 6) {
      toast(t('register_password_short'));
      return;
    }
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.dataset.label = submitBtn.textContent;
      submitBtn.textContent = 'Creating account…';
    }
    try {
      const cred = await firebase.auth().createUserWithEmailAndPassword(email, password);
      try {
        await persistRegisterName();
      } catch (_) {}
      await hydrateUserFromFirebase(cred.user);
      toast(t('account_created'));
      navigate('home');
    } catch (err) {
      toast(formatAuthError(err), { error: true, sticky: true });
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = submitBtn.dataset.label || t('create_account');
      }
    }
  });
}

async function bindAdmin() {
  const panel = document.getElementById('adminPanel');
  if (!panel) return;
  try {
    const [stats, users] = await Promise.all([
      InziraApi.adminStats(),
      InziraApi.adminUsers(30),
    ]);
    const items = users.items || [];
    panel.innerHTML = `
      ${renderStatsStrip([
        { value: String(stats.users || 0), label: 'Users', tone: 'blue' },
        { value: String(stats.profiles || 0), label: 'Profiles', tone: 'green' },
        { value: String(stats.saved_sites || 0), label: 'Saved sites', tone: 'amber' },
      ], { hero: true })}
      <div class="dash-card">
        <div class="dash-card__head"><h2>Recent users</h2></div>
        <div class="admin-user-list">
          ${items.length ? items.map((u) => `
            <div class="admin-user-row">
              <div>
                <strong>${esc(u.name || u.email || u.phone || `User #${u.id}`)}</strong>
                <span class="admin-user-meta">${esc(u.email || u.phone || '—')}</span>
              </div>
              <span class="admin-user-role">${esc(u.role || 'youth')}</span>
            </div>`).join('') : `<p class="empty">No users yet</p>`}
        </div>
      </div>`;
  } catch (err) {
    panel.innerHTML = `<div class="dash-card"><p class="empty">${esc(err?.body?.detail || err.message || 'Admin access failed')}</p></div>`;
  }
}

async function loadYouthData() {
  if (state.youthDataLoading) return;
  state.youthDataLoading = true;
  try {
    const [matchData, radarData] = await Promise.all([
      InziraApi.youthMatches(profilePayload(), 30, state.matchesCategoryFilter || null),
      InziraApi.youthRadar(),
    ]);
    state.matchesAll = matchData.matches || [];
    state.matches = state.matchesAll;
    state.matchesProfileFallback = !!matchData.profile_fallback;
    // Show ALL interest categories by default (do not pin to first interest only).
    state.matchesCategoryFilter = null;
    state.insights = matchData.insights || [];
    state.profileCompleteness = matchData.profile_completeness || 0;
    state.radarDistricts = radarData.districts || [];
    state.gapMap = radarData.gap_map || [];
    state.youthDataLoaded = true;
    await loadRegistryStats();
    await loadImpactAndPathways();
  } catch (_) {
    state.matches = state.matches || [];
  } finally {
    state.youthDataLoading = false;
  }
}

function openMatchAtIndex(idx) {
  const item = displayedMatches()[idx];
  if (!item) return;
  state.detail = item;
  navigate('detail');
}

function runDashSearch() {
  const q = document.getElementById('dashSearchInput')?.value?.trim();
  if (!q) { toast(t('enter_search')); return; }
  saveRecentSearch(q);
  navigate(`results?q=${encodeURIComponent(q)}`);
}

async function loadDashboardDistrictOpportunities(district, opts = {}) {
  if (!district || state.dashboardOppsLoading) return;
  const cat = state.dashboardCategoryFilter || null;
  const cacheKey = `${district}|${cat || ''}`;
  if (!opts.force && state._dashboardOppCacheKey === cacheKey && state.dashboardOpps?.length) return;
  const scroll = opts.scroll === true;
  state.selectedDashboardDistrict = district;
  state.dashboardOppsLoading = true;
  state.dashboardOpps = [];
  state.dashboardNationalOpps = [];
  state.districtFallback = false;
  state._dashboardOppCacheKey = cacheKey;
  render();
  try {
    const data = await InziraApi.registryOpportunities(200, cat, district);
    let districtItems = data.district_opportunities || [];
    let national = data.national_opportunities || [];
    if (cat) {
      const matchCat = (r, c) => {
        if (!c) return false;
        const cats = (r.categories && r.categories.length) ? r.categories : [(r.category || '')];
        return cats.some(x => String(x || '').toLowerCase() === String(c || '').toLowerCase());
      };
      districtItems = districtItems.filter((r) => matchCat(r, cat));
      national = national.filter((r) => matchCat(r, cat));
    }
    const fallback = !!(data.district_fallback) || (districtItems.length === 0 && national.length > 0);
    state.districtFallback = fallback;
    if (fallback) {
      // Never show empty — promote national results into the main list.
      state.dashboardOpps = national.slice(0, 16);
      state.dashboardNationalOpps = [];
    } else {
      state.dashboardOpps = districtItems.slice(0, 12);
      state.dashboardNationalOpps = national.slice(0, 8);
    }
  } catch (err) {
    state.dashboardOpps = [];
    state.districtFallback = false;
    toast(t('backend_down') + (err?.message ? ` ${err.message}` : ''), { error: true });
  } finally {
    state.dashboardOppsLoading = false;
    render();
    if (scroll) {
      setTimeout(() => {
        document.getElementById('dashboardOppCard')?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }, 80);
    }
  }
}

function bindYouthHome() {
  bindDashSearchControls();
  mountRwandaMap('home');

  document.querySelectorAll('#dashboardOppFilters [data-dash-cat]').forEach((btn) => {
    btn.onclick = () => {
      const cat = btn.dataset.dashCat || null;
      state.dashboardCategoryFilter = cat || null;
      document.querySelectorAll('#dashboardOppFilters [data-dash-cat]').forEach((b) => {
        b.classList.toggle('active', (b.dataset.dashCat || '') === (cat || ''));
      });
      const d = state.selectedDashboardDistrict || state.user?.district;
      if (d) loadDashboardDistrictOpportunities(d, { force: true });
    };
  });

  document.querySelectorAll('[data-open-idx]').forEach((btn) => {
    btn.onclick = (e) => {
      e.preventDefault();
      e.stopPropagation();
      const idx = Number(btn.dataset.openIdx);
      const item = state.dashboardOpps?.[idx];
      if (!item) return;
      window.open(item.apply_link || item.url, '_blank', 'noopener');
    };
  });

  document.querySelectorAll('[data-open-national-idx]').forEach((btn) => {
    btn.onclick = (e) => {
      e.preventDefault();
      e.stopPropagation();
      const idx = Number(btn.dataset.openNationalIdx);
      const item = state.dashboardNationalOpps?.[idx];
      if (!item) return;
      window.open(item.apply_link || item.url, '_blank', 'noopener');
    };
  });

  bindSaveButtons((idx) => state.dashboardOpps?.[idx]);
  bindNotifyButtons((idx) => state.dashboardOpps?.[idx]);

  hydrateHomeStatsOnce();

  if (!state.youthDataLoaded && !state.youthDataLoading) {
    loadYouthData().then(() => {
      const { path } = parseRoute();
      if (path === 'home' || path === 'search') {
        mountRwandaMap('home');
        render();
      }
    });
  }
  if (!state.selectedDashboardDistrict && state.user?.district && !state.dashboardOpps?.length && !state.dashboardOppsLoading) {
    loadDashboardDistrictOpportunities(state.user.district);
  }
}

function bindRadarPage() {
  navigate('home');
}

function bindMatchesPage() {
  document.querySelectorAll('#matchesCategoryFilters [data-match-cat]').forEach((btn) => {
    btn.onclick = async () => {
      const cat = btn.dataset.matchCat || '';
      state.matchesCategoryFilter = cat || null;
      await loadMatchesList(cat || null);
    };
  });

  document.querySelectorAll('[data-match-idx]').forEach((el) => {
    el.onclick = () => openMatchAtIndex(Number(el.dataset.matchIdx));
  });

  document.querySelectorAll('[data-open-match]').forEach((btn) => {
    btn.onclick = (e) => {
      e.preventDefault();
      e.stopPropagation();
      const idx = Number(btn.dataset.openMatch);
      const item = displayedMatches()[idx];
      if (!item?.url) return;
      window.open(item.url, '_blank', 'noopener');
    };
  });

  bindSaveButtons((idx) => displayedMatches()[idx]);
  bindNotifyButtons((idx) => displayedMatches()[idx]);

  document.querySelectorAll('#lookingPills [data-looking]').forEach((pill) => {
    pill.onclick = (e) => {
      e.preventDefault();
      document.querySelectorAll('#lookingPills [data-looking]').forEach((p) => p.classList.remove('active'));
      pill.classList.add('active');
      const v = pill.dataset.looking || '';
      const hidden = document.getElementById('lookingHidden');
      if (hidden) hidden.value = v;
    };
  });

  const form = document.getElementById('matchProfileForm');
  if (form) {
    form.onsubmit = async (e) => {
      e.preventDefault();
      const fd = new FormData(form);
      const lookingPill = fd.get('interests') || '';
      const mappedInterest = mapLookingInterest(lookingPill);
      // Keep existing multi-interests from profile; add looking pill if selected.
      const existing = profilePayload().interests || [];
      const merged = [...existing];
      if (mappedInterest && !merged.map((x) => String(x).toLowerCase()).includes(mappedInterest)) {
        merged.push(mappedInterest);
      }
      state.matchesCategoryFilter = null;
      const skill = String(fd.get('skills') || '').trim();
      const payload = {
        district: fd.get('district'),
        age: state.user?.age || '18 - 25',
        education: fd.get('education'),
        skills: skill ? [skill] : [],
        interests: merged.length ? merged : (mappedInterest ? [mappedInterest] : []),
      };
      const submitBtn = document.getElementById('btnFindMatches');
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = t('searching');
      }
      try {
        await trySaveMatchProfile({
          district: payload.district,
          age: payload.age,
          education: payload.education,
          skills: payload.skills,
          interests: payload.interests,
        });
        const data = await InziraApi.youthMatches(payload, 30, null);
        state.matches = data.matches || [];
        state.matchesAll = state.matches;
        state.matchesProfileFallback = !!data.profile_fallback;
        state.matchesCategoryFilter = null;
        state.insights = data.insights || [];
        state.profileCompleteness = data.profile_completeness || 0;
        state.youthDataLoaded = true;
        saveUser({
          ...state.user,
          district: payload.district,
          education: payload.education,
          skills: skill,
          interests: payload.interests,
        }, { invalidate: false });
        navigate('matches-list');
      } catch (err) {
        toast(err.body?.detail || err.message || 'Failed to load matches', { error: true, sticky: true });
      } finally {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.textContent = t('view_all_matches');
        }
      }
    };
  }

  if (!state.youthDataLoaded && !state.youthDataLoading) {
    loadYouthData().then(() => {
      const path = parseRoute().path;
      if (path === 'matches' || path === 'matches-list') render();
    });
  }
}

function bindOpportunitiesPage() {
  const container = document.getElementById('sitesList');
  if (!container) return;

  const renderList = (sites, catFilter) => {
    const filtered = catFilter
      ? sites.filter((s) => (s.categories || [s.category]).map((c) => c.toLowerCase()).includes(catFilter))
      : sites;
    if (!filtered.length) {
      container.innerHTML = emptyStateHtml(t('all_sites_empty'), t('all_sites_empty_sub'), t('nav_search'), 'home');
      return;
    }
    container.innerHTML = filtered.map((s) => siteDirectoryCard(s)).join('');
    container.querySelectorAll('.site-dir-card[data-domain]').forEach((card) => {
      card.style.cursor = 'pointer';
      card.addEventListener('click', (e) => {
        if (e.target.closest('a')) return;
        const dom = card.dataset.domain;
        const cat = catFilter || (card.dataset.cats || '').split(',')[0] || '';
        navigate(`results?q=${encodeURIComponent(`site:${dom}`)}${cat ? `&category=${encodeURIComponent(cat)}` : ''}`);
      });
    });
  };

  const runOppSearch = () => {
    const q = document.getElementById('oppSearchInput')?.value?.trim();
    if (!q) return;
    navigate(`results?q=${encodeURIComponent(q)}`);
  };
  document.getElementById('oppSearchForm')?.addEventListener('submit', (e) => { e.preventDefault(); runOppSearch(); });
  document.getElementById('oppSearchInput')?.addEventListener('keydown', (e) => { if (e.key === 'Enter') runOppSearch(); });

  (async () => {
    try {
      await loadRegistryStats();
      const data = await InziraApi.registryWebsites(500);
      state.allSites = data.websites || [];
      renderList(state.allSites, '');
      document.querySelectorAll('#sitesCategoryFilter .filter-pill').forEach((pill) => {
        pill.onclick = () => {
          document.querySelectorAll('#sitesCategoryFilter .filter-pill').forEach((p) => p.classList.remove('active'));
          pill.classList.add('active');
          renderList(state.allSites, pill.dataset.filter || '');
        };
      });
    } catch (err) {
      container.innerHTML = emptyStateHtml(t('backend_down'), err.message, t('nav_search'), 'home');
    }
  })();
}

function bindSearch() {
  loadRegistryStats().then(() => {
    const el = document.getElementById('registryBanner');
    if (el && state.registryStats) {
      const n = state.registryStats.verified_opportunities ?? state.registryStats.verified_open;
      const countEl = el.querySelector('.registry-banner__count');
      if (countEl) countEl.textContent = t('all_sites_count', { n });
    }
  });
  let selectedCat = '';
  document.getElementById('btnProfile')?.addEventListener('click', () => navigate('settings'));
  document.getElementById('btnNotifications')?.addEventListener('click', () => navigate('settings'));
  document.querySelectorAll('#categoryChips .category-card').forEach(chip => {
    chip.onclick = () => {
      document.querySelectorAll('#categoryChips .category-card').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      selectedCat = chip.dataset.cat;
    };
  });
  const runSearch = (q) => {
    const query = (q || document.getElementById('searchInput').value).trim();
    if (!query) { toast(t('enter_search')); return; }
    saveRecentSearch(query);
    const cat = selectedCat || '';
    state.resultsCategory = cat || null;
    navigate(`results?q=${encodeURIComponent(query)}${cat ? `&category=${encodeURIComponent(cat)}` : ''}`);
  };
  document.getElementById('btnSearch').onclick = () => runSearch();
  document.getElementById('searchInput').onkeydown = (e) => { if (e.key === 'Enter') runSearch(); };
  document.querySelectorAll('.query-chip').forEach((chip) => {
    chip.onclick = () => {
      document.getElementById('searchInput').value = chip.dataset.q;
      runSearch(chip.dataset.q);
    };
  });
  document.getElementById('btnTrustInfo')?.addEventListener('click', openTrustModal);
}

async function loadRegistryStats() {
  try {
    const [stats, newData] = await Promise.all([
      InziraApi.registryStats(),
      InziraApi.registryNew(7).catch(() => ({ websites: [] })),
    ]);
    state.registryStats = {
      ...stats,
      new_verified_last_days: (newData.websites || []).length,
    };
  } catch (_) {
    state.registryStats = state.registryStats || null;
  }
}

function bindAllSites() {
  const container = document.getElementById('allSitesContainer');
  if (!container) return;

  const renderList = (sites, catFilter) => {
    const filtered = catFilter
      ? sites.filter((s) => (s.categories || [s.category]).includes(catFilter))
      : sites;
    if (!filtered.length) {
      container.innerHTML = emptyStateHtml(t('all_sites_empty'), t('all_sites_empty_sub'), t('nav_search'), 'search');
      return;
    }
    container.innerHTML = filtered.map((s) => siteDirectoryCard(s)).join('');
    container.querySelectorAll('.site-dir-card[data-domain]').forEach((card) => {
      card.style.cursor = 'pointer';
      card.addEventListener('click', (e) => {
        if (e.target.closest('a')) return;
        const dom = card.dataset.domain;
        const cat = catFilter || (card.dataset.cats || '').split(',')[0] || '';
        const q = dom ? `site:${dom}` : cat;
        navigate(`results?q=${encodeURIComponent(q)}${cat ? `&category=${encodeURIComponent(cat)}` : ''}`);
      });
    });
  };

  (async () => {
    try {
      await loadRegistryStats();
      const data = await InziraApi.registryWebsites(500);
      state.allSites = data.websites || [];
      renderList(state.allSites, '');
      document.querySelectorAll('#sitesCategoryFilter .filter-pill').forEach((pill) => {
        pill.onclick = () => {
          document.querySelectorAll('#sitesCategoryFilter .filter-pill').forEach((p) => p.classList.remove('active'));
          pill.classList.add('active');
          renderList(state.allSites, pill.dataset.cat || '');
        };
      });
    } catch (err) {
      container.innerHTML = emptyStateHtml(t('backend_down'), err.message, t('nav_search'), 'search');
    }
  })();
}

function updateSearchProgress(status) {
  const fill = document.getElementById('searchProgressFill');
  const msg = document.getElementById('searchProgressMsg');
  const subtitle = document.getElementById('resultsSubtitle');
  const pct = Math.max(5, Math.min(100, Number(status?.progress) || 8));
  const message = status?.message || t('searching');
  if (fill) fill.style.width = `${pct}%`;
  if (msg) msg.textContent = message;
  if (subtitle) subtitle.textContent = message;
}

function hideSearchProgress() {
  document.getElementById('searchProgress')?.classList.add('search-progress--hidden');
}

function showDeepSearchNote(data) {
  const noteEl = document.getElementById('resultsDeepSearchNote');
  if (!noteEl) return;
  noteEl.textContent = data?.deep_search_note || '';
}

function applySearchResults(data, container, subtitle, countEl, activeCategory) {
  let results = data.results || [];
  const catFilter = activeCategory || data.category || null;
  if (catFilter) {
    const matchCat = (r, c) => {
      if (!c) return false;
      const cats = (r.categories && r.categories.length) ? r.categories : [(r.category || '')];
      return cats.some((x) => String(x || '').toLowerCase() === String(c || '').toLowerCase());
    };
    results = results.filter((r) => matchCat(r, catFilter));
  }
  state.results = sortResults(results, state.resultsSort);
  renderResultsList(state.results, container, subtitle, countEl, activeCategory);
  try {
    const noteEl = document.getElementById('resultsDistrictNote');
    if (noteEl) {
      if (data.district_fallback && data.district_name) {
        noteEl.innerHTML = districtFallbackBanner(data.district_name);
      } else {
        noteEl.textContent = data.district_note || '';
      }
    }
  } catch (e) {}
  showDeepSearchNote(data);
}

async function loadResults(query) {
  const q = (query.q ?? state.resultsQuery ?? '').trim();
  state.resultsQuery = q;
  saveRecentSearch(q);
  state.resultsCategory = query.category || null;

  const container = document.getElementById('resultsContainer');
  const subtitle = document.getElementById('resultsSubtitle');
  const countEl = document.getElementById('resultsCount');
  container.innerHTML = skeletonHtml(6);
  if (subtitle) subtitle.textContent = t('searching');
  updateSearchProgress({ progress: 8, message: t('search_phase_registry') });
  showDeepSearchNote(null);

  await loadRegistryStats();
  const statsStrip = document.querySelector('.stats-strip');
  if (statsStrip) {
    statsStrip.outerHTML = renderLiveStatsStrip();
  }

  document.querySelectorAll('#filterChips .filter-pill').forEach(chip => {
    chip.onclick = () => {
      document.querySelectorAll('#filterChips .filter-pill').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      const cat = chip.dataset.filter || '';
      navigate(`results?q=${encodeURIComponent(q)}${cat ? `&category=${encodeURIComponent(cat)}` : ''}`);
    };
  });

  document.getElementById('sortSelect')?.addEventListener('change', (e) => {
    state.resultsSort = e.target.value;
    localStorage.setItem('inzira_sort', state.resultsSort);
    state.results = sortResults(state.results, state.resultsSort);
    renderResultsList(state.results, container, subtitle, countEl);
  });

  try {
    const activeCategory = state.resultsCategory || null;
    const searchQ = activeCategory && !q ? activeCategory : q;
    const data = await InziraApi.searchWithProgress(
      searchQ,
      activeCategory,
      state.user?.district,
      100,
      updateSearchProgress,
      (partial) => {
        applySearchResults(partial, container, subtitle, countEl, activeCategory);
        if ((partial.registry_count || partial.total_found || 0) > 0) {
          updateSearchProgress({
            progress: 45,
            message: t('results_found', { n: partial.registry_count || partial.total_found }),
          });
        }
      },
    );
    hideSearchProgress();
    if (data.category && !state.resultsCategory) {
      state.resultsCategory = data.category;
    }
    applySearchResults(data, container, subtitle, countEl, activeCategory || data.category);
  } catch (err) {
    hideSearchProgress();
    subtitle.textContent = t('backend_down');
    container.innerHTML = emptyStateHtml(t('backend_down'), err.message, t('back_search'), 'home');
  }
}

function renderResultsList(results, container, subtitle, countEl, activeCategory = null) {
  const displayCount = results.filter((r) => !isUrAdmissionRow(r)).length
    + (results.some(isUrAdmissionRow) ? 1 : 0);
  subtitle.textContent = t('results_found', { n: results.length });
  if (countEl) countEl.textContent = `${results.length} results`;

  if (results.length === 0) {
    const cat = activeCategory || state.resultsCategory || null;
    container.innerHTML = emptyStateHtml(emptyCategoryMessage(cat), t('try_different'), t('back_search'), 'home');
    return;
  }

  const grouped = groupResultsForDisplay(results);
  container.className = 'results-grid';
  container.innerHTML = grouped.map((r, i) => {
    if (r._group) return admissionGroupCardHtml(r, i);
    const flatIdx = results.indexOf(r);
    return resultCardHtml(r, flatIdx >= 0 ? flatIdx : i);
  }).join('');
  bindResultGroups(container, results);
  container.querySelectorAll('.result-card').forEach((card, i) => {
    card.onclick = (e) => {
      if (e.target.closest('.visit-btn')) return;
      state.detail = results[i];
      navigate('detail');
    };
  });
  container.querySelectorAll('.visit-btn').forEach(btn => {
    btn.onclick = (e) => e.stopPropagation();
  });
  bindSaveButtons((idx) => results[idx], (url) => results.find((r) => r.url === url));
  bindNotifyButtons((idx) => results[idx], (url) => results.find((r) => r.url === url));
}

function applyButtonLabel(r) {
  if (r?.apply_label === 'application_form_download') return t('application_form_download');
  if (r?.apply_label === 'search_on_site') return t('search_on_site');
  if (r?.apply_label === 'visit_listing') return t('visit_listing');
  return t('visit_site');
}

function isUrAdmissionRow(r) {
  return Boolean(r?.is_admission || r?.subtype === 'admission' || String(r?.source_domain || '').includes('efiling.ur.ac.rw'));
}

function groupResultsForDisplay(results) {
  const admissions = [];
  const other = [];
  for (const r of results) {
    if (isUrAdmissionRow(r)) admissions.push(r);
    else other.push(r);
  }
  if (admissions.length < 2) return results;
  return [
    { _group: 'ur-admissions', title: t('ur_admissions_group', { n: admissions.length }), items: admissions },
    ...other,
  ];
}

function admissionGroupCardHtml(group, groupIdx) {
  const expanded = state.expandedGroups?.has(groupIdx);
  const preview = (group.items || []).slice(0, expanded ? group.items.length : 0);
  return `
    <div class="result-card result-card--group" data-group-idx="${groupIdx}">
      <div class="result-top">
        <div class="result-icon">UR</div>
        <div class="result-info">
          <div class="result-title">${esc(group.title)}</div>
          <div class="result-url">efiling.ur.ac.rw · ${esc(t('cat_program'))}</div>
        </div>
      </div>
      <div class="result-divider"></div>
      <button type="button" class="btn btn-outline btn-sm" data-toggle-group="${groupIdx}">
        ${expanded ? t('hide_programs') : t('show_programs')} (${group.items.length})
      </button>
      ${expanded ? `<div class="admission-group-list" style="margin-top:12px;display:grid;gap:10px">
        ${preview.map((r, i) => `<div class="admission-group-item" data-group-item="${groupIdx}-${i}">
          <strong>${esc(opportunityTitle(r))}</strong>
          <a class="btn btn-visit-site btn-sm" href="${esc(r.apply_link || r.url)}" target="_blank" rel="noopener">${esc(applyButtonLabel(r))}</a>
        </div>`).join('')}
      </div>` : ''}
    </div>`;
}

function bindResultGroups(container, flatResults) {
  container.querySelectorAll('[data-toggle-group]').forEach((btn) => {
    btn.onclick = (e) => {
      e.stopPropagation();
      const idx = Number(btn.dataset.toggleGroup);
      if (!state.expandedGroups) state.expandedGroups = new Set();
      if (state.expandedGroups.has(idx)) state.expandedGroups.delete(idx);
      else state.expandedGroups.add(idx);
      const subtitle = document.getElementById('resultsSubtitle');
      const countEl = document.getElementById('resultsCount');
      renderResultsList(flatResults, container, subtitle, countEl);
    };
  });
}

function resultCardHtml(r, idx = 0) {
  const trust = formatTrustDisplay(r.trust_score);
  const funding = fundingTag(r);
  const elig = eligibilityTag(r);
  const initial = opportunityTitle(r).charAt(0).toUpperCase() || 'O';
  const link = r.apply_link || r.url;
  return `
    <div class="result-card result-card--mockup">
      <div class="result-top">
        <div class="result-icon">${esc(initial)}</div>
        <div class="result-info">
          <div class="result-title">${esc(opportunityTitle(r))}</div>
          <div class="result-url">${esc(opportunityEmployer(r))}${r.district ? ` · ${esc(r.district)}` : ''}</div>
        </div>
        <div class="trust-col">
          <div class="trust-val">${trust}</div>
          <div class="trust-label">${t('trust')}</div>
        </div>
      </div>
      <div class="result-divider"></div>
      <div class="tag-row">
        <span class="tag tag-blue">${esc(categoryLabel(r.category))}</span>
          ${r.snippet && String(r.snippet).startsWith('[portal]') ? `<span class="tag tag-muted">${t('portal_badge')}</span>` : ''}
        ${funding ? `<span class="tag tag-green">${esc(funding)}</span>` : ''}
        ${elig ? `<span class="tag tag-muted">${esc(elig)}</span>` : ''}
        ${renderDeadlineGuardianBadge(r)}
      </div>
      ${renderTrustExplainCard(r)}
      ${renderReadinessPanel(r)}
      <div style="margin-top:8px">
        <button type="button" class="btn btn-outline btn-sm wow-eligibility-btn" data-eligibility-idx="${idx}" data-eligibility-prefix="result">${t('eligibility_btn')}</button>
      </div>
      <div class="result-bottom">
        <span class="deadline-pill">${ico('calendar')} ${esc(deadlineLabel(r))}</span>
        <div class="result-bottom__actions">
          <button type="button" class="btn btn-outline btn-sm follow-btn${isFollowedUrl(link) ? ' btn-follow--active' : ''}" data-url="${esc(link)}" aria-label="${t('follow')}">${ico('bookmark')}</button>
          <button type="button" class="btn btn-outline btn-sm notify-btn${isNotifyOn(link) ? ' notify-btn--active' : ''}" data-notify-url="${esc(link)}" aria-label="${t('notify_me')}">${ico('bell')}</button>
          <a class="btn btn-visit-site visit-btn" href="${esc(link)}" target="_blank" rel="noopener">${esc(applyButtonLabel(r))}</a>
        </div>
      </div>
    </div>`;
}

function bindDetail() {
  const r = state.detail;
  if (!r) return;
  const title = websiteName(r);
  document.getElementById('btnShareWa')?.addEventListener('click', () => shareWhatsApp(title, r.url));
  document.getElementById('btnFollowDetail')?.addEventListener('click', () => toggleFollowSite(r, document.getElementById('btnFollowDetail')));
  document.getElementById('btnNotifyDetail')?.addEventListener('click', () => toggleNotifyForSite(r, document.getElementById('btnNotifyDetail')));
}

function isFollowedUrl(url) {
  return state.followed.some((s) => s.url === url);
}

function bindSaveButtons(getItemByIdx, getItemByUrl) {
  document.querySelectorAll('.follow-btn[data-save-idx]').forEach((btn) => {
    btn.onclick = async (e) => {
      e.preventDefault();
      e.stopPropagation();
      const idx = Number(btn.dataset.saveIdx);
      const item = getItemByIdx?.(idx);
      if (!item) return;
      await toggleFollowSite(item, btn);
    };
  });
  document.querySelectorAll('.follow-btn[data-url]:not([data-save-idx])').forEach((btn) => {
    btn.onclick = async (e) => {
      e.preventDefault();
      e.stopPropagation();
      const item = getItemByUrl?.(btn.dataset.url) || state.results?.find((r) => r.url === btn.dataset.url);
      if (!item) return;
      await toggleFollowSite(item, btn);
    };
  });
}

async function toggleFollowSite(r, btn) {
  if (!firebaseInit()) {
    toast(t('saved_sign_in'), { error: true });
    navigate('login');
    return;
  }

  const fbUser = await waitForFirebaseUser(5000);
  if (!fbUser) {
    toast(t('saved_sign_in'), { error: true });
    sessionStorage.setItem('inzira_post_login_route', location.hash || '#/home');
    navigate('login');
    return;
  }

  let token = await ensureFreshToken();
  if (!token) {
    await handleAuthFailure({ status: 401 }, 'save');
    return;
  }

  const url = r.url;
  const title = websiteName(r);

  async function applySave() {
    const idx = state.followed.findIndex((s) => s.url === url);
    if (idx >= 0) {
      const dom = domain(url);
      await InziraApi.savedRemove(dom);
      state.followed.splice(idx, 1);
      removeNotifyDomain(url);
      toast(t('removed'));
      if (btn) {
        btn.classList.remove('btn-follow--active', 'btn-icon-outline--active');
        if (!btn.classList.contains('btn-icon-outline')) btn.textContent = t('follow');
      }
    } else {
      await InziraApi.savedAdd({ url, title, category: r.category || null });
      state.followed.push({ url, title, category: r.category || null, domain: domain(url) });
      toast(`${t('saved')} ${t('saved_view_hint')}`, { duration: 5200 });
      if (btn) {
        btn.classList.add('btn-follow--active', 'btn-icon-outline--active');
        if (!btn.classList.contains('btn-icon-outline')) btn.textContent = t('following');
      }
    }
  }

  try {
    await applySave();
  } catch (err) {
    if (err?.status === 401) {
      token = await repairAuthSession();
      if (!token) {
        await handleAuthFailure(err, 'save');
        return;
      }
      try {
        await applySave();
      } catch (retryErr) {
        await handleAuthFailure(retryErr, 'save');
        return;
      }
    } else {
      toast(err?.body?.detail || err?.message || t('saved_failed'), { error: true, sticky: true });
      return;
    }
  }

  localStorage.setItem('inzira_saved_cache', JSON.stringify(state.followed));
  state.savedLoaded = true;
  render();
  document.querySelectorAll('.follow-btn').forEach((b) => {
    if (b.dataset.url === url || (b.dataset.saveIdx != null && getSaveItemUrl(b) === url)) {
      const on = isFollowedUrl(url);
      b.classList.toggle('btn-follow--active', on);
      if (!b.classList.contains('btn-icon-outline')) b.textContent = on ? t('following') : t('follow');
    }
  });
}

function getSaveItemUrl(btn) {
  const idx = Number(btn.dataset.saveIdx);
  if (Number.isNaN(idx)) return '';
  const pools = [state.dashboardOpps, state.matches, state.results];
  for (const pool of pools) {
    if (pool?.[idx]?.url) return pool[idx].url;
  }
  return '';
}

function saveChatMessage(role, text) {
  const history = JSON.parse(sessionStorage.getItem('inzira_chat') || '[]');
  history.push({ role, text });
  sessionStorage.setItem('inzira_chat', JSON.stringify(history.slice(-40)));
}

function formatAssistantText(text) {
  const safe = esc(text);
  return safe.replace(
    /(https?:\/\/[^\s<]+)/g,
    '<a href="$1" target="_blank" rel="noopener">$1</a>'
  );
}

function bindAssistant() {
  const input = document.getElementById('chatInput');
  const messages = document.getElementById('chatMessages');
  if (messages) messages.scrollTop = messages.scrollHeight;
  if (!input || !messages) return;

  const send = async () => {
    const msg = input.value.trim();
    if (!msg) return;
    input.value = '';
    appendBubble(messages, msg, 'user');
    saveChatMessage('user', msg);

    const typing = document.createElement('div');
    typing.className = 'chat-row bot';
    typing.id = 'typing';
    typing.innerHTML = `<div class="chat-avatar">${ico('bot')}</div><div class="bubble bot typing"><span class="typing-label">${esc(t('assistant_thinking'))}</span><span></span><span></span><span></span></div>`;
    messages.appendChild(typing);
    messages.scrollTop = messages.scrollHeight;

    try {
      const data = await InziraApi.assistant(msg, state.lang === 'rw' ? 'kinyarwanda' : 'english');
      typing.remove();
      const reply = data.response || data.message || t('assistant_no_response');
      appendBubble(messages, reply, 'bot', true);
      saveChatMessage('bot', reply);
    } catch (err) {
      typing.remove();
      const detail = err.body?.detail;
      const errMsg = detail
        ? `Assistant error: ${typeof detail === 'string' ? detail : JSON.stringify(detail)}`
        : t('assistant_error');
      appendBubble(messages, errMsg, 'bot');
      saveChatMessage('bot', errMsg);
    }
  };
  document.getElementById('chatSend').onclick = send;
  input.onkeydown = (e) => { if (e.key === 'Enter') send(); };
  document.querySelectorAll('.suggestion-chip').forEach(btn => {
    btn.onclick = () => { input.value = btn.dataset.suggest; send(); };
  });
  document.getElementById('btnClearChat')?.addEventListener('click', () => {
    sessionStorage.removeItem('inzira_chat');
    render();
  });
  if (!state.youthDataLoaded && !state.youthDataLoading) {
    loadYouthData().then(() => {
      if (parseRoute().path === 'assistant') render();
    });
  }
}

function appendBubble(container, text, role, linkify = false) {
  const wrap = document.createElement('div');
  wrap.className = `chat-row ${role}`;
  if (role === 'bot') {
    const av = document.createElement('div');
    av.className = 'chat-avatar';
    av.innerHTML = ico('bot');
    wrap.appendChild(av);
  }
  const el = document.createElement('div');
  el.className = `bubble ${role}`;
  if (role === 'bot' && linkify) {
    el.innerHTML = formatAssistantText(text);
  } else {
    el.textContent = text;
  }
  wrap.appendChild(el);
  container.appendChild(wrap);
  container.scrollTop = container.scrollHeight;
}

function bindFollowed() {
  const cached = JSON.parse(localStorage.getItem('inzira_saved_cache') || '[]');
  if (cached.length && !state.followed.length) {
    state.followed = cached;
    if (parseRoute().path === 'followed') render();
  }
  refreshSavedFromServer(true).then(() => {
    if (parseRoute().path === 'followed') render();
  });
  document.querySelectorAll('.btn-unfollow').forEach(btn => {
    btn.onclick = (e) => {
      e.stopPropagation();
      const idx = parseInt(btn.dataset.idx, 10);
      const item = state.followed[idx];
      if (!item) return;
      InziraApi.savedRemove(item.domain || domain(item.url)).then(() => {
        removeNotifyDomain(item.url);
        state.followed.splice(idx, 1);
        localStorage.setItem('inzira_saved_cache', JSON.stringify(state.followed));
        render();
      }).catch((err) => toast(err?.body?.detail || err?.message || 'Remove failed'));
    };
  });
  document.querySelectorAll('.btn-open-followed').forEach((btn) => {
    btn.onclick = () => {
      const url = decodeURIComponent(btn.dataset.url || '');
      const title = btn.dataset.title || '';
      if (url) openPreview(url, title);
    };
  });
  document.querySelectorAll('.btn-preview-followed').forEach((btn) => {
    btn.onclick = (e) => {
      e.stopPropagation();
      openPreview(decodeURIComponent(btn.dataset.url || ''), btn.dataset.title || '');
    };
  });
  document.querySelectorAll('.btn-visit-followed').forEach((link) => {
    link.onclick = (e) => e.stopPropagation();
  });
  bindNotifyButtons((idx) => state.followed?.[idx]);
}

function bindSettings() {
  document.getElementById('btnSignOutSettings').onclick = logout;
  document.getElementById('btnDeleteAccount')?.addEventListener('click', deleteAccount);
  document.getElementById('rowBackend')?.addEventListener('click', () => {
    const current = InziraApi.baseUrl();
    const next = window.prompt(
      'API server URL (leave empty for this site):',
      current === window.location.origin ? '' : current
    );
    if (next === null) return;
    const trimmed = (next || window.location.origin).replace(/\/$/, '');
    InziraApi.setBaseUrl(trimmed);
    toast(`API: ${trimmed}`);
    render();
  });
  document.getElementById('rowNotifications')?.addEventListener('click', async () => {
    if (Notification?.permission === 'denied') {
      openNotificationHelpModal();
      return;
    }
    await enableNotifications();
    render();
  });
  document.getElementById('rowMifotra')?.addEventListener('click', () => navigate('mifotra'));
}

function bindMifotra() {
  const form = document.getElementById('mifotraForm');
  if (!form) return;
  form.onsubmit = async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    try {
      const data = await InziraApi.mifotraLogin(fd.get('email').trim(), fd.get('password'));
      state.mifotraToken = data.token || data.session_token || '';
      sessionStorage.setItem('inzira_mifotra_token', state.mifotraToken);
      navigate('dashboard');
    } catch (err) {
      toast(err.body?.detail || 'MIFOTRA login failed');
    }
  };
}

async function loadDashboard() {
  const el = document.getElementById('dashboardContent');
  try {
    const data = await InziraApi.mifotraDashboard(state.mifotraToken);
    el.innerHTML = dashboardHtml(data);
  } catch (err) {
    if (err.status === 401) {
      state.mifotraToken = '';
      sessionStorage.removeItem('inzira_mifotra_token');
      toast('Session expired');
      navigate('mifotra');
      return;
    }
    el.innerHTML = `<div class="empty"><p>Dashboard unavailable.</p><p style="font-size:12px">${esc(err.message)}</p></div>`;
  }
}

function renderTrendBadge(comparison, label) {
  if (!comparison || comparison.previous == null || comparison.previous <= 0) return '';
  if (comparison.change_pct == null || Number.isNaN(comparison.change_pct)) return '';
  const sign = comparison.change_pct > 0 ? '+' : '';
  const cls = comparison.change_pct >= 0 ? 'trend-up' : 'trend-down';
  return `<div class="trend ${cls}">${sign}${comparison.change_pct}% ${esc(label)}</div>`;
}

function dashboardHtml(data) {
  const reg = data.registry || {};
  const opps = data.opportunities || {};
  const youth = data.youth_analytics || {};
  const oppByCat = reg.opportunities_by_category || {};
  const totalListings = Number(opps.listings_total ?? 0);
  const scholarships = Number(oppByCat.scholarship ?? 0);
  const internships = Number(oppByCat.internship ?? 0);
  const searchesMonth = Number(youth.summary?.total_searches ?? 0);
  const searchesWeek = Number(youth.comparisons?.searches_week?.current ?? 0);
  const verifiedSites = Number(reg.verified_total ?? 0);
  const districtCoverage = reg.district_coverage || [];
  const topQueries = (youth.top_search_queries || []).slice(0, 6);
  const actions = buildRecommendations(oppByCat, youth, scholarships, districtCoverage);

  const catEntries = Object.entries(oppByCat)
    .filter(([, v]) => Number(v) > 0)
    .sort((a, b) => b[1] - a[1]);
  const maxCat = Math.max(1, ...catEntries.map(([, v]) => Number(v)));

  const districtGapHtml = districtCoverage.length < 5
    ? '<p class="empty">Insufficient district data for gap analysis</p>'
    : districtCoverage.slice(0, 8).map((d) => `
        <div class="district-card">
          <h4>${esc(d.district)}</h4>
          <div class="meta"><span>${Number(d.listings || 0)} tagged listings</span></div>
        </div>`).join('');

  const topSearchHtml = topQueries.length
    ? topQueries.map((q) => `
        <div class="top-search-row">
          <span>${esc(capitalize(q.query || 'general'))}</span>
          <strong>${q.share_pct ?? 0}%</strong>
        </div>`).join('')
    : '<p class="empty">No search data recorded yet</p>';

  return `
    <div class="metrics-grid metrics-grid--dash metrics-grid--present">
      <div class="metric-card metric-card--dash">
        <div class="label">Live opportunities</div>
        <div class="value value--blue">${fmt(totalListings)}</div>
      </div>
      <div class="metric-card metric-card--dash">
        <div class="label">Scholarships</div>
        <div class="value value--warn">${fmt(scholarships)}</div>
        ${scholarships < 15 ? '<div class="trend trend-warn">Below 15 listings</div>' : ''}
      </div>
      <div class="metric-card metric-card--dash">
        <div class="label">Internships</div>
        <div class="value value--accent">${fmt(internships)}</div>
      </div>
      <div class="metric-card metric-card--dash">
        <div class="label">Youth searches this month</div>
        <div class="value value--accent">${fmt(searchesMonth)}</div>
        ${renderTrendBadge(youth.comparisons?.searches_month, 'vs prior 30 days')}
      </div>
      <div class="metric-card metric-card--dash">
        <div class="label">Youth searches this week</div>
        <div class="value">${fmt(searchesWeek)}</div>
        ${renderTrendBadge(youth.comparisons?.searches_week, 'vs prior 7 days')}
      </div>
      <div class="metric-card metric-card--dash">
        <div class="label">Trusted websites found</div>
        <div class="value">${fmt(verifiedSites)}</div>
        ${renderTrendBadge(reg.new_websites_compare, 'vs prior 30 days')}
      </div>
    </div>
    <div class="chart-card chart-card--dash">
      <div class="chart-card-inner">
        <div class="chart-head">
          <h3>Opportunities by category</h3>
        </div>
        ${catEntries.length ? catEntries.map(([k, v]) => barRow(categoryLabel(k), v, maxCat, BAR_COLORS[k] || '#1A3A6B')).join('') : '<p class="empty">No category data yet</p>'}
      </div>
    </div>
    <div class="dash-split">
      <div class="chart-card chart-card--dash">
        <div class="chart-card-inner">
          <div class="chart-head"><h3>${t('district_gap')}</h3></div>
          <div class="district-grid">${districtGapHtml}</div>
        </div>
      </div>
      <div class="chart-card chart-card--dash">
        <div class="chart-card-inner">
          <div class="chart-head"><h3>Top searches</h3></div>
          <div class="top-search-list">${topSearchHtml}</div>
        </div>
      </div>
    </div>
    ${actions.length ? `
    <div class="actions-box actions-box--dash">
      <h3>Recommended government actions</h3>
      ${actions.map((a) => `<p>${ico('spark')} ${esc(a)}</p>`).join('')}
    </div>` : ''}`;
}

function barRow(label, value, max, color) {
  const pct = Math.max(8, Math.round((value / max) * 100));
  return `
    <div class="bar-row">
      <span class="name">${esc(label)}</span>
      <div class="bar-track"><div class="bar-fill" style="width:${pct}%;background:${color}"></div></div>
      <span class="count">${value}</span>
    </div>`;
}

function computeRisk(d) {
  const rate = d.searches > 0 ? d.zero_result_searches / d.searches : 1;
  if (d.searches < 10 || rate >= 0.5) return { label: 'High risk', cls: 'high' };
  if (rate >= 0.25 || d.searches < 30) return { label: 'Medium', cls: 'medium' };
  return { label: 'Low risk', cls: 'low' };
}

function buildRecommendations(oppByCat, youth, scholarships, districtCoverage) {
  const actions = [];
  const totalSearches = Number(youth.summary?.total_searches ?? 0);
  if (scholarships > 0 && scholarships < 15) {
    actions.push(`Scholarships low (${scholarships} live listings). Prioritize new scholarship intake sources for 2026.`);
  }
  if (totalSearches > 0) {
    (youth.top_districts || []).forEach((d) => {
      if (computeRisk(d).cls === 'high' && Number(d.searches) >= 10) {
        actions.push(`${d.district}: ${d.zero_result_searches} of ${d.searches} searches returned zero results.`);
      }
    });
  }
  const jobs = Number(oppByCat.job ?? 0);
  const freeCourses = Number(oppByCat.free_course ?? 0);
  if (jobs > 0 && freeCourses > jobs) {
    actions.push(`Free courses (${freeCourses}) outnumber jobs (${jobs}) in the live registry.`);
  }
  if (districtCoverage.length > 0 && districtCoverage.length < 5) {
    actions.push(`Only ${districtCoverage.length} districts have tagged listings — expand district tagging in harvest.`);
  }
  return actions.slice(0, 3);
}

// ── Helpers ──────────────────────────────────────────────────
function esc(s) {
  return String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;');
}

function domain(url) {
  try { return new URL(url).hostname.replace('www.', ''); } catch { return url || ''; }
}

function registryOpportunityCount() {
  const stats = state.registryStats;
  if (stats?.verified_opportunities != null) return stats.verified_opportunities;
  if (state.impactStats?.opportunities_live != null) return state.impactStats.opportunities_live;
  return 0;
}

function verifiedPortalCount() {
  return Number(
    state.impactStats?.verified_portals
    ?? state.registryStats?.verified_websites
    ?? state.registryStats?.verified_open
    ?? 0,
  );
}

function websiteName(r) {
  return opportunityTitle(r);
}

function opportunityTitle(r) {
  if (!r) return t('label_opportunity');
  let title = (r.title || '').trim();
  title = title
    .replace(/^post\s*\d*\s*/i, '')
    .replace(/(\d{4})([A-Za-z])/g, '$1 $2')
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .replace(/\b(Program|Fellowship)(By|Apply|The)\b/gi, '$1 $2')
    .split(/\b(By initiating|Applications are|Read more)\b/i)[0]
    .trim();
  if (/^application\s*link$/i.test(title) || /^apply\s*here$/i.test(title)) title = '';
  const org = (r.organization || '').trim();
  const cat = categoryLabel((r.category || (r.categories && r.categories[0]) || 'job'));
  if (title && title.length > 4 && !/^https?:/i.test(title)) {
    return title.length > 72 ? `${title.slice(0, 69)}…` : title;
  }
  if (org) return `${cat} — ${org}`;
  const host = domain(r.url);
  return host ? `${cat} — ${host}` : cat;
}

function opportunityEmployer(r) {
  if (!r) return '';
  return (r.organization || r.location || domain(r.url) || '').trim();
}

function trustDecimal(score) {
  // Legacy helper — keep 0–1 for comparisons that expect decimals.
  const n = score > 1 ? score / 100 : score;
  return Number(n);
}

function trustPercent(score) {
  const n = Number(score);
  if (!Number.isFinite(n)) return 0;
  // Backend usually returns 0–100; some paths may still send 0–1.
  return Math.round(n > 1 ? n : n * 100);
}

function resultCategories(r) {
  const cats = [];
  const primary = String(r.category || '').toLowerCase().trim();
  if (primary) cats.push(primary);
  if (Array.isArray(r.categories)) {
    for (const c of r.categories) {
      const lc = String(c || '').toLowerCase().trim();
      if (lc && !cats.includes(lc)) cats.push(lc);
    }
  }
  return cats.length ? cats : ['program'];
}

function categoryTagClass(cat) {
  const c = String(cat || '').toLowerCase();
  if (c === 'scholarship') return 'tag-amber';
  if (c === 'training' || c === 'free_course') return 'tag-green';
  return 'tag-blue';
}

function categoryLabel(cat) {
  if (!cat) return t('label_general');
  const key = {
    scholarship: 'cat_scholarship', job: 'cat_job', internship: 'cat_internship',
    training: 'cat_training', program: 'cat_program', free_course: 'cat_free_course',
    competition: 'cat_competition',
  }[cat.toLowerCase()];
  return key ? t(key) : cat.replace(/_/g, ' ');
}

function capitalize(s) {
  return s.replace(/\b\w/g, c => c.toUpperCase());
}

function fundingTag(r) {
  const text = `${r.snippet || ''} ${r.eligibility || ''}`.toLowerCase();
  if (text.includes('full tuition') || text.includes('full funding')) return t('funding_full');
  if (text.includes('partial') || text.includes('stipend')) return t('funding_partial');
  return null;
}

function eligibilityTag(r) {
  if (r.eligibility) return r.eligibility.length > 24 ? r.eligibility.slice(0, 21) + '...' : r.eligibility;
  return null;
}

function deadlineLabel(r) {
  if (r.deadline) {
    return r.deadline.startsWith('Deadline') || r.deadline.startsWith(t('deadline_prefix'))
      ? r.deadline
      : `${t('deadline_prefix')}: ${r.deadline}`;
  }
  return `${t('deadline_prefix')}: ${t('deadline_check')}`;
}

function aiSummary(r) {
  return r.snippet || t('ai_summary_default');
}

function benefitLine(r) {
  const s = (r.snippet || '').trim();
  if (!s) return t('benefit_check');
  const dot = s.indexOf('.');
  return dot > 0 && dot < 80 ? s.slice(0, dot + 1) : s.slice(0, 80);
}

function factRow(label, value) {
  return `
    <div class="fact-row">
      <span class="fact-dot"></span>
      <span class="fact-label">${esc(label)}</span>
      <span class="fact-value">${esc(value)}</span>
    </div>`;
}

function fmt(n) {
  return Number(n).toLocaleString('en-US');
}

function formatAuthError(err) {
  const code = err?.code || '';
  const msg = String(err?.message || err || '');
  const appId = window.INZIRA_FIREBASE_CONFIG?.appId || '';
  const needsWebApp = !appId || /:web:in[z]?ira$/i.test(appId);

  if (code === 'auth/too-many-requests') {
    return 'Too many SMS attempts. Free Firebase allows about 10 texts per day. Try Email sign-in or wait until tomorrow.';
  }
  if (code === 'auth/invalid-app-credential' || code === 'auth/captcha-check-failed') {
    return 'reCAPTCHA check failed. Hard refresh the page (Ctrl+Shift+R) and try again.';
  }
  if (code === 'auth/operation-not-allowed') {
    if (needsWebApp) {
      return 'Add a Web app in Firebase: Project settings → Your apps → Web (</>) → copy appId into web/index.html → hard refresh.';
    }
    if (/region|sms unable/i.test(msg)) {
      return 'Allow Rwanda: Firebase → Authentication → Settings → SMS region policy → Allow → add Rwanda (RW).';
    }
    return 'Phone SMS needs Blaze plan (Spark cannot send texts). Upgrade: bottom-left Upgrade button. Dev workaround: Authentication → Phone → Phone numbers for testing → add +250781633117 code 123456. Or use Email tab.';
  }
  if (msg.includes('sign-in provider is disabled')) {
    return 'Phone SMS needs Blaze plan, or add Rwanda in SMS region policy (Authentication → Settings). For free dev: add a test phone number under Phone sign-in method. Or use Email.';
  }
  if (msg.startsWith('Firebase:')) {
    const cleaned = msg
      .replace(/^Firebase:\s*/, '')
      .replace(/\s*\(auth\/[^)]+\)\.?$/, '')
      .trim();
    return cleaned || msg;
  }
  return msg || 'Something went wrong';
}

function dismissToast() {
  if (toastHideTimer) {
    clearTimeout(toastHideTimer);
    toastHideTimer = null;
  }
  toastSticky = false;
  toastDismissOnClick = true;
  if (!$toast) return;
  $toast.classList.remove('show', 'toast--error', 'toast--sticky');
  $toast.removeAttribute('role');
  $toast.removeAttribute('aria-live');
}

function toast(msg, opts = {}) {
  if (!$toast) return;
  const isError = opts.error === true || opts.type === 'error';
  const sticky = opts.sticky === true || isError;
  dismissToast();
  $toast.textContent = msg;
  $toast.classList.toggle('toast--error', isError);
  $toast.classList.toggle('toast--sticky', sticky);
  $toast.classList.add('show');
  $toast.setAttribute('role', 'alert');
  $toast.setAttribute('aria-live', sticky ? 'assertive' : 'polite');
  toastSticky = sticky;
  if (sticky) {
    toastDismissOnClick = false;
    setTimeout(() => { toastDismissOnClick = true; }, 400);
    return;
  }
  const duration = opts.duration ?? 2800;
  toastHideTimer = setTimeout(dismissToast, duration);
}

// Default route — never send users to old #/home landing
if (!location.hash) {
  location.hash = '#/' + defaultRoute();
}
