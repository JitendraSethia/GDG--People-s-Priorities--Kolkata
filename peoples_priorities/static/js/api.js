const Api = {
  async get(path, params) {
    const url = new URL(path, window.location.origin);
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, v);
      });
    }
    const res = await fetch(url);
    if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`);
    return res.json();
  },

  async post(path, body) {
    const res = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {}),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw Object.assign(new Error(data.message || `POST ${path} failed`), { data, status: res.status });
    return data;
  },

  async patch(path, body) {
    const res = await fetch(path, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {}),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw Object.assign(new Error(data.message || `PATCH ${path} failed`), { data, status: res.status });
    return data;
  },
};

function pollEndpoint(fn, intervalMs, immediate = true) {
  let stopped = false;
  const tick = async () => {
    if (stopped) return;
    try {
      await fn();
    } catch (err) {
      console.warn("poll tick failed", err);
    }
    if (!stopped) setTimeout(tick, intervalMs);
  };
  if (immediate) tick();
  else setTimeout(tick, intervalMs);
  return () => { stopped = true; };
}

const URGENCY_LABELS = { low: "Low", medium: "Medium", high: "High", critical: "Critical" };

function urgencyBadgeHtml(level, score) {
  const label = URGENCY_LABELS[level] || level;
  return `<button type="button" class="urgency-badge ${level}" data-action="toggle-reasons">${label} · ${score}</button>`;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = (str === null || str === undefined) ? "" : str;
  return div.innerHTML;
}

function timeAgo(isoString) {
  if (!isoString) return "";
  const then = new Date(isoString.replace(" ", "T"));
  const diffMs = Date.now() - then.getTime();
  const mins = Math.round(diffMs / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.round(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.round(hours / 24)}d ago`;
}
