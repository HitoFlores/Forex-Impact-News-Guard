const DEFAULT_STATE = {
  generated_at: null,
  counts: {
    relevant_events: 0,
    schedules: 0,
    dispatches: 0,
    tracked_currencies: 0,
  },
  policy_summary: {
    timezone: "America/Chihuahua",
    lead_minutes: 15,
    revalidate_minutes_before_alert: 2,
    result_check_delay_minutes: 1,
    result_retry_minutes: [3, 5],
    daily_summary_enabled: true,
    include_results: true,
    high_impact_only: true,
    breaking_enabled: true,
    calendar_enabled: true,
    monitored_currencies: [],
    risk_window_before_minutes: 15,
    risk_window_after_minutes: 15,
  },
  status: {
    generated_at: null,
    next_event_at: null,
    next_alert_at: null,
    latest_event_stored_at: null,
    last_dispatch_at: null,
    keepalive_updated_at: null,
  },
  observability: {
    cards: [],
    diagnostics: [],
  },
  dispatch_breakdown: [],
  impact_breakdown: [],
  currency_breakdown: [],
  next_alerts: [],
  recent_events: [],
  recent_dispatches: [],
};

const LIVE_STATE_PATH = "state.json";
const DEMO_STATE_PATH = "state.example.json";
const MODE_STORAGE_KEY = "fing-dashboard-mode";
const GITHUB_STORAGE_KEY = "fing-dashboard-github";
const GITHUB_TOKEN_SESSION_KEY = "fing-dashboard-github-token";

function $(id) {
  return document.getElementById(id);
}

async function loadJson(path) {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Failed to load ${path}: ${response.status}`);
  }
  return response.json();
}

function detectMode() {
  const urlMode = new URLSearchParams(window.location.search).get("mode");
  if (urlMode === "demo" || urlMode === "live") return urlMode;
  const savedMode = window.localStorage.getItem(MODE_STORAGE_KEY);
  return savedMode === "demo" ? "demo" : "live";
}

function setMode(mode) {
  window.localStorage.setItem(MODE_STORAGE_KEY, mode);
  $("mode-live").classList.toggle("is-active", mode === "live");
  $("mode-demo").classList.toggle("is-active", mode === "demo");
  $("mode-copy").textContent =
    mode === "demo"
      ? "Demo visual activo. Telegram real sigue dependiendo de workflows."
      : "Modo live leyendo ultimo estado publicado por GitHub Actions.";
}

function shiftIso(value, deltaMs) {
  if (!value) return value;
  return new Date(new Date(value).getTime() + deltaMs).toISOString();
}

function buildDemoState(sample) {
  if (!sample?.generated_at) return sample;
  const deltaMs = Date.now() - new Date(sample.generated_at).getTime();
  return {
    ...sample,
    generated_at: shiftIso(sample.generated_at, deltaMs),
    status: {
      ...sample.status,
      generated_at: shiftIso(sample.status?.generated_at, deltaMs),
      next_event_at: shiftIso(sample.status?.next_event_at, deltaMs),
      next_alert_at: shiftIso(sample.status?.next_alert_at, deltaMs),
      latest_event_stored_at: shiftIso(sample.status?.latest_event_stored_at, deltaMs),
      last_dispatch_at: shiftIso(sample.status?.last_dispatch_at, deltaMs),
      keepalive_updated_at: shiftIso(sample.status?.keepalive_updated_at, deltaMs),
    },
    observability: {
      cards: (sample.observability?.cards ?? []).map((item) => ({
        ...item,
        last_attempt_at: shiftIso(item.last_attempt_at, deltaMs),
        last_success_at: shiftIso(item.last_success_at, deltaMs),
        last_error_at: shiftIso(item.last_error_at, deltaMs),
      })),
      diagnostics: (sample.observability?.diagnostics ?? []).map((item) => ({
        ...item,
        last_attempt_at: shiftIso(item.last_attempt_at, deltaMs),
        last_success_at: shiftIso(item.last_success_at, deltaMs),
        last_error_at: shiftIso(item.last_error_at, deltaMs),
      })),
    },
    next_alerts: (sample.next_alerts ?? []).map((item) => ({
      ...item,
      alert_at: shiftIso(item.alert_at, deltaMs),
      scheduled_at: shiftIso(item.scheduled_at, deltaMs),
      risk_window_starts_at: shiftIso(item.risk_window_starts_at, deltaMs),
      risk_window_ends_at: shiftIso(item.risk_window_ends_at, deltaMs),
    })),
    recent_events: (sample.recent_events ?? []).map((item) => ({
      ...item,
      scheduled_at: shiftIso(item.scheduled_at, deltaMs),
      stored_at: shiftIso(item.stored_at, deltaMs),
    })),
    recent_dispatches: (sample.recent_dispatches ?? []).map((item) => ({
      ...item,
      scheduled_for: shiftIso(item.scheduled_for, deltaMs),
      sent_at: shiftIso(item.sent_at, deltaMs),
    })),
  };
}

async function loadStateForMode(mode) {
  if (mode === "demo") {
    try {
      return buildDemoState(await loadJson(DEMO_STATE_PATH));
    } catch {
      return DEFAULT_STATE;
    }
  }

  try {
    return await loadJson(LIVE_STATE_PATH);
  } catch {
    try {
      return buildDemoState(await loadJson(DEMO_STATE_PATH));
    } catch {
      return DEFAULT_STATE;
    }
  }
}

function formatStamp(value) {
  if (!value) return "Sin timestamp";
  return new Date(value).toLocaleString("es-MX", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function formatRelative(value) {
  if (!value) return "Sin dato";
  const diffMs = new Date(value).getTime() - Date.now();
  const diffMinutes = Math.round(diffMs / 60000);
  if (Math.abs(diffMinutes) < 1) return "ahora";
  if (Math.abs(diffMinutes) < 60) {
    return diffMinutes > 0 ? `en ${diffMinutes} min` : `hace ${Math.abs(diffMinutes)} min`;
  }
  const diffHours = Math.round(diffMinutes / 60);
  if (Math.abs(diffHours) < 24) {
    return diffHours > 0 ? `en ${diffHours} h` : `hace ${Math.abs(diffHours)} h`;
  }
  const diffDays = Math.round(diffHours / 24);
  return diffDays > 0 ? `en ${diffDays} d` : `hace ${Math.abs(diffDays)} d`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function formatImpact(value) {
  const normalized = String(value ?? "").toLowerCase();
  if (normalized === "high") return "Alta";
  if (normalized === "medium") return "Media";
  if (normalized === "low") return "Baja";
  return value ?? "N/D";
}

function formatKind(value) {
  const normalized = String(value ?? "").toLowerCase();
  if (normalized === "daily_summary") return "Daily";
  if (normalized === "precheck") return "Precheck";
  if (normalized === "alert") return "Alert";
  if (normalized === "result") return "Result";
  return value ?? "N/D";
}

function formatObservabilityLabel(value) {
  const normalized = String(value ?? "").toLowerCase();
  if (normalized === "scraping") return "Scraping";
  if (normalized === "telegram") return "Telegram";
  if (normalized === "precheck") return "Precheck";
  return value ?? "N/D";
}

function formatObservabilityStatus(value) {
  const normalized = String(value ?? "").toLowerCase();
  if (normalized === "ok") return "OK";
  if (normalized === "warn") return "Warn";
  if (normalized === "error") return "Error";
  if (normalized === "idle") return "Idle";
  return value ?? "N/D";
}

function freshnessMeta(value) {
  if (!value) return { label: "Sin sync", tone: "stale" };
  const ageMinutes = Math.round((Date.now() - new Date(value).getTime()) / 60000);
  if (ageMinutes <= 10) return { label: "Cron fresco", tone: "fresh" };
  if (ageMinutes <= 30) return { label: "Cron vigilado", tone: "warm" };
  return { label: "Cron atrasado", tone: "stale" };
}

function renderList(target, items, renderItem, emptyText) {
  if (!items.length) {
    target.innerHTML = `<article class="card empty"><h3>${emptyText}</h3></article>`;
    return;
  }
  target.innerHTML = items.map(renderItem).join("");
}

function loadGithubPrefs() {
  try {
    return JSON.parse(window.localStorage.getItem(GITHUB_STORAGE_KEY) ?? "{}");
  } catch {
    return {};
  }
}

function saveGithubPrefs(rememberToken) {
  const prefs = {
    owner: $("gh-owner").value.trim(),
    repo: $("gh-repo").value.trim(),
    branch: $("gh-branch").value.trim(),
  };
  window.localStorage.setItem(GITHUB_STORAGE_KEY, JSON.stringify(prefs));
  if (rememberToken) {
    window.sessionStorage.setItem(GITHUB_TOKEN_SESSION_KEY, $("gh-token").value);
  } else {
    window.sessionStorage.removeItem(GITHUB_TOKEN_SESSION_KEY);
  }
}

function fillGithubPrefs() {
  const prefs = loadGithubPrefs();
  if (prefs.owner) $("gh-owner").value = prefs.owner;
  if (prefs.repo) $("gh-repo").value = prefs.repo;
  if (prefs.branch) $("gh-branch").value = prefs.branch;
  const token = window.sessionStorage.getItem(GITHUB_TOKEN_SESSION_KEY);
  if (token) {
    $("gh-token").value = token;
    $("gh-remember").checked = true;
  }
}

function setFeedback(id, message, tone = "idle") {
  const el = $(id);
  el.textContent = message;
  el.className = `feedback ${tone}`;
}

function updateControlLock() {
  const hasToken = Boolean($("gh-token").value.trim());
  $("run-smoke").disabled = !hasToken;
  $("run-sync").disabled = !hasToken;
  $("apply-settings").disabled = !hasToken;
  if (!hasToken) {
    setFeedback("workflow-feedback", "Controles bloqueados hasta pegar un GitHub token valido.", "idle");
  }
}

function fillSettingsForm(policy) {
  $("lead-minutes").value = policy.lead_minutes ?? 15;
  $("revalidate-minutes").value = policy.revalidate_minutes_before_alert ?? 2;
  $("result-delay").value = policy.result_check_delay_minutes ?? 1;
  $("timezone").value = policy.timezone ?? "America/Chihuahua";
  $("currencies").value = (policy.monitored_currencies ?? []).join(",");
  $("risk-before").value = policy.risk_window_before_minutes ?? 15;
  $("risk-after").value = policy.risk_window_after_minutes ?? 15;
  $("calendar-enabled").checked = Boolean(policy.calendar_enabled);
  $("breaking-enabled").checked = Boolean(policy.breaking_enabled);
  $("daily-summary-enabled").checked = Boolean(policy.daily_summary_enabled);
  $("include-results").checked = Boolean(policy.include_results);
  $("high-impact-only").checked = Boolean(policy.high_impact_only);

  const allowedImpacts = policy.high_impact_only
    ? "high"
    : Array.isArray(policy.allowed_impacts) && policy.allowed_impacts.length
      ? policy.allowed_impacts.join(",")
      : "low,medium,high";
  if ([...$("allowed-impacts").options].some((option) => option.value === allowedImpacts)) {
    $("allowed-impacts").value = allowedImpacts;
  } else {
    $("allowed-impacts").value = "medium,high";
  }
}

function collectSettingsInputs() {
  const allowedImpacts = $("high-impact-only").checked ? "high" : $("allowed-impacts").value;
  return {
    calendar_enabled: String($("calendar-enabled").checked),
    breaking_enabled: String($("breaking-enabled").checked),
    high_impact_only: String($("high-impact-only").checked),
    allowed_impacts: allowedImpacts,
    currencies: $("currencies").value.trim(),
    lead_minutes: String($("lead-minutes").value || 15),
    revalidate_minutes_before_alert: String($("revalidate-minutes").value || 2),
    result_check_delay_minutes: String($("result-delay").value || 1),
    include_results: String($("include-results").checked),
    daily_summary_enabled: String($("daily-summary-enabled").checked),
    risk_window_before_minutes: String($("risk-before").value || 15),
    risk_window_after_minutes: String($("risk-after").value || 15),
    timezone: $("timezone").value.trim() || "America/Chihuahua",
  };
}

function settingsNeedSyncNotice(inputs) {
  const riskyKeys = [
    "calendar_enabled",
    "breaking_enabled",
    "high_impact_only",
    "allowed_impacts",
    "currencies",
  ];
  return riskyKeys.some((key) => String(inputs[key] ?? "").trim() !== "");
}

async function dispatchWorkflow(workflowId, inputs = {}) {
  const owner = $("gh-owner").value.trim();
  const repo = $("gh-repo").value.trim();
  const branch = $("gh-branch").value.trim() || "main";
  const token = $("gh-token").value.trim();

  if (!owner || !repo || !token) {
    throw new Error("Falta owner, repo o token.");
  }

  saveGithubPrefs($("gh-remember").checked);

  const response = await fetch(
    `https://api.github.com/repos/${encodeURIComponent(owner)}/${encodeURIComponent(repo)}/actions/workflows/${encodeURIComponent(workflowId)}/dispatches`,
    {
      method: "POST",
      headers: {
        Accept: "application/vnd.github+json",
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        ref: branch,
        inputs,
      }),
    }
  );

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`GitHub API ${response.status}: ${errorText}`);
  }
}

async function copySettingsPayload() {
  const payload = collectSettingsInputs();
  const text = JSON.stringify(payload, null, 2);
  await navigator.clipboard.writeText(text);
  setFeedback("settings-feedback", "Payload copiado al clipboard.", "ok");
}

function bindActions(state) {
  $("gh-token").oninput = () => updateControlLock();
  $("gh-remember").onchange = () => saveGithubPrefs($("gh-remember").checked);
  $("mode-live").onclick = () => render("live");
  $("mode-demo").onclick = () => render("demo");

  $("run-smoke").onclick = async () => {
    try {
      setFeedback("workflow-feedback", "Disparando telegram-smoke-test...", "busy");
      await dispatchWorkflow("telegram-smoke-test.yml");
      setFeedback("workflow-feedback", "Workflow telegram-smoke-test lanzado.", "ok");
    } catch (error) {
      setFeedback("workflow-feedback", error.message, "error");
    }
  };

  $("run-sync").onclick = async () => {
    try {
      setFeedback("workflow-feedback", "Disparando sync-and-publish...", "busy");
      await dispatchWorkflow("cron.yml");
      setFeedback("workflow-feedback", "Workflow sync-and-publish lanzado.", "ok");
    } catch (error) {
      setFeedback("workflow-feedback", error.message, "error");
    }
  };

  $("settings-form").onsubmit = async (event) => {
    event.preventDefault();
    try {
      const inputs = collectSettingsInputs();
      setFeedback("settings-feedback", "Aplicando settings via dashboard-control...", "busy");
      await dispatchWorkflow("dashboard-control.yml", inputs);
      setFeedback(
        "settings-feedback",
        settingsNeedSyncNotice(inputs)
          ? "Settings aplicados. Pages se actualizara al terminar, pero cambios de filtros/eventos se veran en Live hasta el siguiente Sync + Publish."
          : "Workflow dashboard-control lanzado. Pages se actualizara al terminar.",
        "ok"
      );
    } catch (error) {
      setFeedback("settings-feedback", error.message, "error");
    }
  };

  $("copy-settings").onclick = async () => {
    try {
      await copySettingsPayload();
    } catch (error) {
      setFeedback("settings-feedback", error.message, "error");
    }
  };

  $("high-impact-only").onchange = () => {
    $("allowed-impacts").disabled = $("high-impact-only").checked;
  };

  fillSettingsForm(state.policy_summary ?? DEFAULT_STATE.policy_summary);
  $("allowed-impacts").disabled = $("high-impact-only").checked;
  updateControlLock();
}

async function render(mode = detectMode()) {
  setMode(mode);
  const state = await loadStateForMode(mode);
  const counts = state.counts ?? DEFAULT_STATE.counts;
  const policy = state.policy_summary ?? DEFAULT_STATE.policy_summary;
  const status = state.status ?? DEFAULT_STATE.status;
  const breakdown = Array.isArray(state.dispatch_breakdown) ? state.dispatch_breakdown : [];
  const impactBreakdown = Array.isArray(state.impact_breakdown) ? state.impact_breakdown : [];
  const currencyBreakdown = Array.isArray(state.currency_breakdown) ? state.currency_breakdown : [];
  const observabilityCards = Array.isArray(state.observability?.cards) ? state.observability.cards : [];
  const observabilityDiagnostics = Array.isArray(state.observability?.diagnostics) ? state.observability.diagnostics : [];
  const nextAlerts = Array.isArray(state.next_alerts) ? state.next_alerts : [];
  const recentEvents = Array.isArray(state.recent_events) ? state.recent_events : [];
  const recentDispatches = Array.isArray(state.recent_dispatches) ? state.recent_dispatches : [];
  const freshness = freshnessMeta(state.generated_at);
  const currencies = policy.monitored_currencies?.length ? policy.monitored_currencies.join(", ") : "Todas";

  document.getElementById("count-events").textContent = counts.relevant_events;
  document.getElementById("count-schedules").textContent = counts.schedules;
  document.getElementById("count-dispatches").textContent = counts.dispatches;
  document.getElementById("count-currencies").textContent = counts.tracked_currencies || "ALL";
  document.getElementById("currencies-copy").textContent = `Monitoreo: ${currencies}`;
  document.getElementById("generated-at").textContent = `Actualizado ${formatStamp(state.generated_at)}`;
  document.getElementById("freshness-pill").textContent = mode === "demo" ? "Demo listo" : freshness.label;
  document.getElementById("freshness-pill").className = `status-pill ${mode === "demo" ? "fresh" : freshness.tone}`;

  document.getElementById("status-next-alert").textContent = formatStamp(status.next_alert_at);
  document.getElementById("status-next-alert-rel").textContent = formatRelative(status.next_alert_at);
  document.getElementById("status-next-event").textContent = formatStamp(status.next_event_at);
  document.getElementById("status-next-event-rel").textContent = formatRelative(status.next_event_at);
  document.getElementById("status-last-dispatch").textContent = formatStamp(status.last_dispatch_at);
  document.getElementById("status-last-dispatch-rel").textContent = formatRelative(status.last_dispatch_at);
  document.getElementById("status-keepalive").textContent = formatStamp(status.keepalive_updated_at);
  document.getElementById("status-keepalive-rel").textContent = formatRelative(status.keepalive_updated_at);

  document.getElementById("policy-chips").innerHTML = [
    `<span class="chip">${escapeHtml(policy.timezone)}</span>`,
    `<span class="chip">${policy.lead_minutes}m lead</span>`,
    `<span class="chip">${policy.include_results ? "Resultados on" : "Resultados off"}</span>`,
    `<span class="chip">${policy.daily_summary_enabled ? "Daily on" : "Daily off"}</span>`,
    `<span class="chip">${mode === "demo" ? "Visual demo" : "Estado live"}</span>`,
  ].join("");

  renderList(
    $("observability-cards"),
    observabilityCards,
    (item) => `
      <article class="card observability-card">
        <div class="card-top">
          <div>
            <h3>${formatObservabilityLabel(item.key)}</h3>
            <div class="meta">${escapeHtml(item.note ?? "Sin nota")}</div>
          </div>
          <span class="pill obs-pill ${escapeHtml(item.status)}">${escapeHtml(formatObservabilityStatus(item.status))}</span>
        </div>
        <div class="detail-row">
          <span>Intento ${formatRelative(item.last_attempt_at)}</span>
          <span>Exito ${formatRelative(item.last_success_at)}</span>
          <span>Fallos ${escapeHtml(item.consecutive_failures ?? 0)}</span>
        </div>
      </article>
    `,
    "Sin observabilidad"
  );

  renderList(
    $("observability-diagnostics"),
    observabilityDiagnostics,
    (item) => `
      <article class="card">
        <div class="card-top">
          <div>
            <h3>${formatObservabilityLabel(item.key)}</h3>
            <div class="meta">Ultimo intento ${formatStamp(item.last_attempt_at)} · Ultimo exito ${formatStamp(item.last_success_at)}</div>
          </div>
          <span class="mini-pill obs-badge ${escapeHtml(item.status)}">${escapeHtml(formatObservabilityStatus(item.status))}</span>
        </div>
        <div class="detail-row">
          <span>Error ${formatStamp(item.last_error_at)}</span>
          <span>Racha ${escapeHtml(item.consecutive_failures ?? 0)}</span>
          <span>${escapeHtml(item.last_error_message ?? "Sin error registrado")}</span>
        </div>
      </article>
    `,
    "Sin diagnosticos"
  );

  renderList(
    $("next-alerts"),
    nextAlerts,
    (item) => `
      <article class="alert-card">
        <div class="alert-card-top">
          <div class="alert-copy">
            <div class="inline-meta">
              <span class="mini-pill">${escapeHtml(item.currency)}</span>
              <span class="mini-pill tone-impact">${formatImpact(item.impact)}</span>
              <span class="mini-pill tone-muted">${formatKind(item.alert_kind)}</span>
            </div>
            <h3>${escapeHtml(item.title)}</h3>
            <div class="meta">Evento ${formatStamp(item.scheduled_at)} - ventana ${formatStamp(item.risk_window_starts_at)} a ${formatStamp(item.risk_window_ends_at)}</div>
          </div>
          <div class="alert-timing">
            <span class="pill">${formatRelative(item.alert_at)}</span>
            <small>${formatStamp(item.alert_at)}</small>
          </div>
        </div>
      </article>
    `,
    "Sin alertas proximas"
  );

  renderList(
    $("policy-summary"),
    [
      `Calendario ${policy.calendar_enabled ? "activo" : "pausado"}`,
      `Breaking ${policy.breaking_enabled ? "activo" : "pausado"}`,
      policy.high_impact_only ? "Solo alto impacto" : "Impacto flexible",
      `Precheck ${policy.revalidate_minutes_before_alert}m antes`,
      `Result check ${policy.result_check_delay_minutes}m despues`,
      `Riesgo ${policy.risk_window_before_minutes ?? 15}m antes / ${policy.risk_window_after_minutes ?? 15}m despues`,
      `Monedas: ${currencies}`,
    ],
    (item) => `<article class="card compact-card"><h3>${escapeHtml(item)}</h3></article>`,
    "Sin policy"
  );

  renderList(
    $("impact-breakdown"),
    impactBreakdown,
    (item) => `
      <article class="card compact-card">
        <div class="card-top">
          <h3>Impacto ${formatImpact(item.impact)}</h3>
          <span class="pill good">${escapeHtml(item.count)}</span>
        </div>
      </article>
    `,
    "Sin impacto registrado"
  );

  renderList(
    $("currency-breakdown"),
    currencyBreakdown,
    (item) => `
      <article class="card compact-card">
        <div class="card-top">
          <h3>${escapeHtml(item.currency)}</h3>
          <span class="pill">${escapeHtml(item.count)}</span>
        </div>
      </article>
    `,
    "Sin monedas activas"
  );

  renderList(
    $("dispatch-breakdown"),
    breakdown,
    (item) => `
      <article class="card compact-card">
        <div class="card-top">
          <h3>${formatKind(item.kind)}</h3>
          <span class="pill good">${escapeHtml(item.count)}</span>
        </div>
      </article>
    `,
    "Sin dispatches registrados"
  );

  renderList(
    $("recent-events"),
    recentEvents,
    (item) => `
      <article class="card">
        <div class="card-top">
          <div>
            <h3>${escapeHtml(item.title)}</h3>
            <div class="meta">${escapeHtml(item.event_id)} - ${escapeHtml(item.currency)} - ${formatImpact(item.impact)} - ${formatStamp(item.scheduled_at)}</div>
          </div>
          ${item.is_breaking ? '<span class="mini-pill tone-alert">Breaking</span>' : ""}
        </div>
        <div class="detail-row">
          <span>Actual ${escapeHtml(item.actual ?? "N/D")}</span>
          <span>Forecast ${escapeHtml(item.forecast ?? "N/D")}</span>
          <span>Previous ${escapeHtml(item.previous ?? "N/D")}</span>
        </div>
      </article>
    `,
    "Sin eventos recientes"
  );

  renderList(
    $("recent-dispatches"),
    recentDispatches,
    (item) => `
      <article class="card">
        <div class="card-top">
          <div>
            <h3>${formatKind(item.kind)} - ${escapeHtml(item.event_id)}</h3>
            <div class="meta">${formatStamp(item.sent_at)} - canal ${escapeHtml(item.channel)}</div>
          </div>
          <span class="mini-pill tone-muted">#${escapeHtml(item.attempt ?? 1)}</span>
        </div>
      </article>
    `,
    "Sin dispatches"
  );

  bindActions(state);
}

fillGithubPrefs();
render().catch((error) => {
  document.body.insertAdjacentHTML(
    "beforeend",
    `<pre style="padding:24px;color:#ffccaa;background:#1b1111">${escapeHtml(error.message)}</pre>`
  );
});
