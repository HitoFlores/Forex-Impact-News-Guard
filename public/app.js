const DEFAULT_STATE = {
  generated_at: null,
  counts: {
    relevant_events: 0,
    schedules: 0,
    dispatches: 0,
  },
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

function renderList(target, items, renderItem, emptyText) {
  if (!items.length) {
    target.innerHTML = `<article class="card"><h3>${emptyText}</h3></article>`;
    return;
  }
  target.innerHTML = items.map(renderItem).join("");
}

function render() {
  loadState()
    .then((state) => {
      const counts = state.counts ?? DEFAULT_STATE.counts;
      const nextAlerts = Array.isArray(state.next_alerts) ? state.next_alerts : DEFAULT_STATE.next_alerts;
      const recentEvents = Array.isArray(state.recent_events) ? state.recent_events : DEFAULT_STATE.recent_events;
      const recentDispatches = Array.isArray(state.recent_dispatches)
        ? state.recent_dispatches
        : DEFAULT_STATE.recent_dispatches;

      document.getElementById("count-events").textContent = counts.relevant_events;
      document.getElementById("count-schedules").textContent = counts.schedules;
      document.getElementById("count-dispatches").textContent = counts.dispatches;
      document.getElementById("generated-at").textContent = `Actualizado ${formatStamp(state.generated_at)}`;

      renderList(
        document.getElementById("next-alerts"),
        nextAlerts,
        (item) => `
          <article class="card">
            <div class="card-top">
              <div>
                <h3>${item.title}</h3>
                <div class="meta">${item.currency} - ${item.impact} - ${formatStamp(item.scheduled_at)}</div>
              </div>
              <span class="pill">${formatStamp(item.alert_at)}</span>
            </div>
          </article>
        `,
        "Sin alertas proximas"
      );

      renderList(
        document.getElementById("recent-events"),
        recentEvents,
        (item) => `
          <article class="card">
            <h3>${item.title}</h3>
            <div class="meta">${item.event_id} - ${item.currency} - ${item.impact} - ${formatStamp(item.scheduled_at)}</div>
          </article>
        `,
        "Sin eventos recientes"
      );

      renderList(
        document.getElementById("recent-dispatches"),
        recentDispatches,
        (item) => `
          <article class="card">
            <h3>${item.kind} - ${item.event_id}</h3>
            <div class="meta">${formatStamp(item.sent_at)} - ${item.channel}</div>
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
