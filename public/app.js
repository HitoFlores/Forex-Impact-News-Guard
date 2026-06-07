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
  },
  status: {
    generated_at: null,
    next_event_at: null,
    next_alert_at: null,
    latest_event_stored_at: null,
    last_dispatch_at: null,
    keepalive_updated_at: null,
  },
  dispatch_breakdown: [],
  next_alerts: [],
  recent_events: [],
  recent_dispatches: [],
};

async function loadJson(path) {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Failed to load ${path}: ${response.status}`);
  }
  return response.json();
}

async function loadState() {
  try {
    return await loadJson("state.json");
  } catch {
    try {
      return await loadJson("state.example.json");
    } catch {
      return DEFAULT_STATE;
    }
  }
}

function formatStamp(value) {
  if (!value) return "Sin timestamp";
  return new Date(value).toLocaleString("es-ES", {
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

function render() {
  loadState()
    .then((state) => {
      const counts = state.counts ?? DEFAULT_STATE.counts;
      const policy = state.policy_summary ?? DEFAULT_STATE.policy_summary;
      const status = state.status ?? DEFAULT_STATE.status;
      const breakdown = Array.isArray(state.dispatch_breakdown)
        ? state.dispatch_breakdown
        : DEFAULT_STATE.dispatch_breakdown;
      const nextAlerts = Array.isArray(state.next_alerts) ? state.next_alerts : DEFAULT_STATE.next_alerts;
      const recentEvents = Array.isArray(state.recent_events) ? state.recent_events : DEFAULT_STATE.recent_events;
      const recentDispatches = Array.isArray(state.recent_dispatches)
        ? state.recent_dispatches
        : DEFAULT_STATE.recent_dispatches;
      const freshness = freshnessMeta(state.generated_at);
      const currencies = policy.monitored_currencies?.length ? policy.monitored_currencies.join(", ") : "Todas";

      document.getElementById("count-events").textContent = counts.relevant_events;
      document.getElementById("count-schedules").textContent = counts.schedules;
      document.getElementById("count-dispatches").textContent = counts.dispatches;
      document.getElementById("count-currencies").textContent = counts.tracked_currencies || "ALL";
      document.getElementById("currencies-copy").textContent = `Monitoreo: ${currencies}`;
      document.getElementById("generated-at").textContent = `Actualizado ${formatStamp(state.generated_at)}`;
      document.getElementById("freshness-pill").textContent = freshness.label;
      document.getElementById("freshness-pill").className = `status-pill ${freshness.tone}`;

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
      ].join("");

      renderList(
        document.getElementById("next-alerts"),
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
                <div class="meta">Evento ${formatStamp(item.scheduled_at)} · ventana ${formatStamp(item.risk_window_starts_at)} a ${formatStamp(item.risk_window_ends_at)}</div>
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
        document.getElementById("policy-summary"),
        [
          `Calendario ${policy.calendar_enabled ? "activo" : "pausado"}`,
          `Breaking ${policy.breaking_enabled ? "activo" : "pausado"}`,
          policy.high_impact_only ? "Solo alto impacto" : "Impacto configurable",
          `Precheck ${policy.revalidate_minutes_before_alert}m antes`,
          `Result check inicial ${policy.result_check_delay_minutes}m despues`,
          `Retries de resultado: ${(policy.result_retry_minutes ?? []).join(", ") || "ninguno"}m`,
          `Monedas: ${currencies}`,
        ],
        (item) => `
          <article class="card compact-card">
            <h3>${escapeHtml(item)}</h3>
          </article>
        `,
        "Sin policy"
      );

      renderList(
        document.getElementById("dispatch-breakdown"),
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
        document.getElementById("recent-events"),
        recentEvents,
        (item) => `
          <article class="card">
            <div class="card-top">
              <div>
                <h3>${escapeHtml(item.title)}</h3>
                <div class="meta">${escapeHtml(item.event_id)} · ${escapeHtml(item.currency)} · ${formatImpact(item.impact)} · ${formatStamp(item.scheduled_at)}</div>
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
        document.getElementById("recent-dispatches"),
        recentDispatches,
        (item) => `
          <article class="card">
            <div class="card-top">
              <div>
                <h3>${formatKind(item.kind)} · ${escapeHtml(item.event_id)}</h3>
                <div class="meta">${formatStamp(item.sent_at)} · canal ${escapeHtml(item.channel)}</div>
              </div>
              <span class="mini-pill tone-muted">#${escapeHtml(item.attempt ?? 1)}</span>
            </div>
          </article>
        `,
        "Sin dispatches"
      );
    })
    .catch((error) => {
      document.body.insertAdjacentHTML(
        "beforeend",
        `<pre style="padding:24px;color:#ffccaa;background:#1b1111">${error.message}</pre>`
      );
    });
}

render();
