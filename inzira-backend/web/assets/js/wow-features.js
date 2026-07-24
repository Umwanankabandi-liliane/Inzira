/* Inzira wow features — trust, readiness, gap map, eligibility, voice, pathways */

function renderImpactCounter() {
  const s = state.impactStats || {};
  const liveOpps = Number(s.opportunities_live ?? registryOpportunityCount() ?? 0);
  const portals = Number(s.verified_portals ?? verifiedPortalCount() ?? 0);
  const districts = Number(s.districts_covered ?? state.registryStats?.districts_with_listings ?? 0);
  const searches = Number(s.youth_searches_month ?? 0);
  const items = [
    { value: Number.isFinite(liveOpps) ? liveOpps : 0, label: t('impact_opportunities') },
    { value: Number.isFinite(portals) ? portals : 0, label: t('impact_portals') },
    { value: Number.isFinite(districts) ? districts : 0, label: t('impact_districts') },
    { value: Number.isFinite(searches) ? searches : 0, label: t('impact_youth_guided') },
  ];
  // After hydration, paint final values immediately so counters never spin forever.
  const paintNow = !!state._homeStatsHydrated;
  return `
    <section class="impact-counter" id="impactCounter" aria-live="polite">
      ${items.map((item, i) => `
        <div class="impact-counter__item" style="--i:${i}">
          <strong class="impact-counter__value" data-count-target="${esc(String(item.value))}"${paintNow ? ' data-count-done="1"' : ''}>${paintNow ? esc(String(item.value)) : '0'}</strong>
          <span class="impact-counter__label">${esc(item.label)}</span>
        </div>`).join('')}
    </section>`;
}

function animateImpactCounters() {
  document.querySelectorAll('.impact-counter__value[data-count-target]').forEach((el) => {
    const raw = el.getAttribute('data-count-target') || '0';
    if (el.getAttribute('data-count-done') === '1') {
      el.textContent = raw;
      return;
    }
    if (el._countRaf) {
      cancelAnimationFrame(el._countRaf);
      el._countRaf = null;
    }
    const target = parseInt(String(raw).replace(/\D/g, ''), 10);
    if (!Number.isFinite(target) || target <= 0) {
      el.textContent = raw;
      el.setAttribute('data-count-done', '1');
      return;
    }
    const start = performance.now();
    const dur = 900;
    const finish = () => {
      el.textContent = raw;
      el.setAttribute('data-count-done', '1');
      el._countRaf = null;
      if (el._countTimer) {
        clearTimeout(el._countTimer);
        el._countTimer = null;
      }
    };
    // Hard stop — never leave counters animating indefinitely.
    el._countTimer = setTimeout(finish, dur + 200);
    const tick = (now) => {
      if (el.getAttribute('data-count-done') === '1') return;
      const p = Math.min(1, (now - start) / dur);
      el.textContent = String(Math.round(target * p));
      if (p < 1) el._countRaf = requestAnimationFrame(tick);
      else finish();
    };
    el._countRaf = requestAnimationFrame(tick);
  });
}

function renderTrustExplainCard(r) {
  const reasons = r.trust_reasons || [];
  if (!reasons.length) return '';
  const pct = trustPercent(r.trust_score);
  return `
    <div class="trust-explain-card">
      <div class="trust-explain-card__head">
        <span class="trust-explain-card__score">${t('trust')} ${pct}%</span>
        <span class="trust-explain-card__title">${t('trust_why')}</span>
      </div>
      <ul class="trust-explain-list">
        ${reasons.map((reason) => `
          <li class="trust-explain-list__item trust-explain-list__item--${esc(reason.tone || 'blue')}">
            ${esc(reason.text)}
          </li>`).join('')}
      </ul>
    </div>`;
}

function renderReadinessPanel(r) {
  const ready = r.readiness || {};
  const score = ready.readiness_score ?? r.match_score ?? null;
  if (score == null) return '';
  const checklist = ready.checklist || [];
  return `
    <div class="readiness-panel">
      <div class="readiness-panel__head">
        <span class="readiness-panel__label">${t('readiness_title')}</span>
        <strong class="readiness-panel__score">${score}%</strong>
      </div>
      <div class="readiness-panel__bar"><span style="width:${Math.min(100, score)}%"></span></div>
      ${checklist.length ? `<ul class="readiness-checklist">
        ${checklist.map((c) => `
          <li class="readiness-checklist__item${c.ok ? ' readiness-checklist__item--ok' : ''}">
            <span class="readiness-checklist__mark">${c.ok ? '✓' : '○'}</span>
            <span>${esc(c.label)}</span>
          </li>`).join('')}
      </ul>` : ''}
    </div>`;
}

function renderDeadlineGuardianBadge(r) {
  const st = r.deadline_status || {};
  const status = st.status || 'unknown';
  if (status === 'hidden' || !st.label) return '';
  const cls = {
    urgent: 'deadline-badge--urgent',
    soon: 'deadline-badge--soon',
    expired: 'deadline-badge--expired',
    open: 'deadline-badge--open',
  }[status] || 'deadline-badge--unknown';
  return `<span class="deadline-badge ${cls}">${ico('calendar')} ${esc(st.label || t('deadline_check'))}</span>`;
}

function renderOpportunityWowBlock(r, i, prefix = 'opp', opts = {}) {
  const compact = opts.compact === true;
  if (compact) {
    return `
    <div class="opp-wow-block opp-wow-block--compact">
      <button type="button" class="btn btn-outline btn-sm wow-eligibility-btn" data-eligibility-idx="${i}" data-eligibility-prefix="${prefix}">
        ${t('eligibility_btn')}
      </button>
    </div>`;
  }
  return `
    <div class="opp-wow-block">
      ${renderDeadlineGuardianBadge(r)}
      <button type="button" class="btn btn-outline btn-sm wow-eligibility-btn" data-eligibility-idx="${i}" data-eligibility-prefix="${prefix}">
        ${t('eligibility_btn')}
      </button>
      ${renderTrustExplainCard(r)}
      ${renderReadinessPanel(r)}
    </div>`;
}

function renderPathwaysGraph() {
  const steps = state.pathwaySteps || [
    { id: 'learn', icon: 'book', title: t('path_learn'), sub: t('path_learn_sub') },
    { id: 'train', icon: 'spark', title: t('path_train'), sub: t('path_train_sub') },
    { id: 'intern', icon: 'user', title: t('path_intern'), sub: t('path_intern_sub') },
    { id: 'work', icon: 'shield', title: t('path_work'), sub: t('path_work_sub') },
  ];
  const nodes = steps.map((s, idx) => {
    const node = `
      <div class="pathway-node pathway-node--motion" style="--i:${idx}" data-pathway="${s.id}">
        <span class="pathway-node__icon">${ico(s.icon)}</span>
        <strong>${esc(s.title)}</strong>
        <span>${esc(s.sub)}</span>
      </div>`;
    return idx < steps.length - 1 ? `${node}<span class="pathway-arrow">→</span>` : node;
  }).join('');
  return `
    <section class="pathway-graph page-enrich-section">
      <h3 class="section-heading">${t('pathway_title')}</h3>
      <p class="sheet-desc">${t('pathway_sub')}</p>
      <div class="pathway-graph__track">${nodes}</div>
    </section>`;
}

function renderGapMapControls() {
  const gapOn = !!state.mapGapMode;
  return `
    <div class="gap-map-controls">
      <button type="button" class="filter-pill filter-pill--blue${gapOn ? '' : ' active'}" id="btnMapSupply" data-map-mode="supply">
        ${t('map_mode_supply')}
      </button>
      <button type="button" class="filter-pill filter-pill--amber${gapOn ? ' active' : ''}" id="btnMapGap" data-map-mode="gap">
        ${t('map_mode_gap')}
      </button>
      <span class="gap-map-controls__hint">${gapOn ? t('map_gap_hint') : t('map_legend_hint')}</span>
    </div>`;
}

async function loadImpactAndPathways() {
  try {
    const [impact, pathways] = await Promise.all([
      InziraApi.youthImpact(),
      InziraApi.youthPathways().catch(() => ({ steps: [] })),
    ]);
    state.impactStats = impact;
    state.pathwaySteps = (pathways.steps || []).map((s) => ({
      ...s,
      title: s.title,
      sub: s.sub,
    }));
  } catch (_) {
    state.impactStats = state.impactStats || {};
  }
}

function resolveEligibilityOpportunity(idx, prefix) {
  if (prefix === 'match') return state.matches?.[idx];
  if (prefix === 'result') return state.results?.[idx];
  return state.dashboardOpps?.[idx];
}

async function showEligibilityWizard(idx, prefix) {
  const opp = resolveEligibilityOpportunity(idx, prefix);
  if (!opp) return;
  const overlay = document.createElement('div');
  overlay.className = 'wow-modal-overlay';
  overlay.innerHTML = `
    <div class="wow-modal" role="dialog" aria-labelledby="eligTitle">
      <button type="button" class="wow-modal__close" aria-label="Close">×</button>
      <h2 id="eligTitle">${t('eligibility_title')}</h2>
      <p class="sheet-desc">${esc(opportunityTitle(opp))}</p>
      <div class="loading loading--compact"><div class="spinner"></div><p>${t('searching')}</p></div>
    </div>`;
  document.body.appendChild(overlay);
  const close = () => overlay.remove();
  overlay.querySelector('.wow-modal__close').addEventListener('click', close);
  overlay.addEventListener('click', (e) => { if (e.target === overlay) close(); });
  try {
    const data = await InziraApi.youthEligibility(opp, profilePayload());
    const verdictCls = `eligibility-verdict--${data.verdict || 'maybe'}`;
    const body = overlay.querySelector('.wow-modal');
    body.innerHTML = `
      <button type="button" class="wow-modal__close" aria-label="Close">×</button>
      <h2 id="eligTitle">${t('eligibility_title')}</h2>
      <p class="sheet-desc">${esc(opportunityTitle(opp))}</p>
      <div class="eligibility-verdict ${verdictCls}">
        <strong>${t(`eligibility_${data.verdict || 'maybe'}`)}</strong>
        <p>${esc(data.summary || '')}</p>
        <span class="tag tag-blue">${t('readiness_title')}: ${data.readiness_score || 0}%</span>
      </div>
      ${renderReadinessPanel({ readiness: { readiness_score: data.readiness_score, checklist: data.checklist } })}
      <button type="button" class="btn btn-primary" style="margin-top:12px;width:100%" data-open-opp>${t('apply_now')} ↗</button>`;
    body.querySelector('.wow-modal__close').addEventListener('click', close);
    body.querySelector('[data-open-opp]')?.addEventListener('click', () => {
      close();
      openOpportunityUrl(opp);
    });
  } catch (err) {
    overlay.querySelector('.wow-modal').innerHTML = `
      <button type="button" class="wow-modal__close">×</button>
      <p class="empty">${esc(err.message || 'Failed')}</p>`;
    overlay.querySelector('.wow-modal__close').addEventListener('click', close);
  }
}

function openOpportunityUrl(opp) {
  const url = opp.apply_url || opp.apply_link || opp.url;
  if (url) window.open(url, '_blank', 'noopener');
}

function bindVoiceSearch(btnId, inputId, onResult) {
  const btn = document.getElementById(btnId);
  const input = document.getElementById(inputId);
  if (!btn) return;
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) {
    btn.hidden = true;
    return;
  }
  const rec = new SR();
  rec.lang = state.lang === 'rw' ? 'rw-RW' : 'en-RW';
  rec.interimResults = false;
  rec.maxAlternatives = 1;
  btn.addEventListener('click', () => {
    try {
      btn.classList.add('voice-btn--active');
      rec.start();
    } catch (_) {}
  });
  rec.onresult = (ev) => {
    const text = ev.results?.[0]?.[0]?.transcript || '';
    if (input) input.value = text;
    if (typeof onResult === 'function') onResult(text);
    btn.classList.remove('voice-btn--active');
  };
  rec.onerror = () => btn.classList.remove('voice-btn--active');
  rec.onend = () => btn.classList.remove('voice-btn--active');
}

function bindWowFeatureUI() {
  animateImpactCounters();
  document.querySelectorAll('.wow-eligibility-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      const idx = parseInt(btn.getAttribute('data-eligibility-idx'), 10);
      const prefix = btn.getAttribute('data-eligibility-prefix') || 'opp';
      showEligibilityWizard(idx, prefix);
    });
  });
  const btnSupply = document.getElementById('btnMapSupply');
  const btnGap = document.getElementById('btnMapGap');
  if (btnSupply) {
    btnSupply.addEventListener('click', () => {
      state.mapGapMode = false;
      render();
    });
  }
  if (btnGap) {
    btnGap.addEventListener('click', () => {
      state.mapGapMode = true;
      render();
    });
  }
  bindVoiceSearch('btnVoiceSearch', 'chatInput', (text) => {
    if (text.trim()) document.getElementById('chatSend')?.click();
  });
  bindVoiceSearch('btnVoiceDashSearch', 'dashVoiceInput', (text) => {
    if (text.trim()) {
      saveRecentSearch(text);
      navigate(`results?q=${encodeURIComponent(text.trim())}`);
    }
  });
}
