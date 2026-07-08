document.addEventListener("DOMContentLoaded", () => {
  const list = document.getElementById("completed-list");
  const summary = document.getElementById("completed-summary");
  const wardFilter = document.getElementById("completed-ward-filter");
  if (!list) return;

  function formatHours(hours) {
    if (hours < 24) return `${Math.round(hours)} hours`;
    return `${Math.round(hours / 24)} days`;
  }

  async function load() {
    list.innerHTML = '<p aria-busy="true">Loading…</p>';
    const data = await Api.get("/api/completed", { ward: wardFilter.value || undefined, page_size: 30 });

    summary.textContent = data.avg_resolution_hours
      ? `${data.count} issues resolved recently — average fix time ${formatHours(data.avg_resolution_hours)}`
      : `${data.count} issues resolved recently`;

    if (!data.results.length) {
      list.innerHTML = '<p class="text-muted center">Nothing resolved here yet — check back soon.</p>';
      return;
    }

    list.innerHTML = data.results
      .map(
        (item) => `
      <article class="completed-card">
        <span class="resolved-badge">Fixed in ${formatHours(item.resolution_hours)}</span>
        <h3>${escapeHtml(item.category_label)}</h3>
        <p class="text-muted">${escapeHtml(item.ward)} · ${escapeHtml(item.ticket_id)}</p>
        <p>${escapeHtml(item.summary)}</p>
        ${item.photo_path ? `<img src="${escapeHtml(item.photo_path)}" alt="Photo of resolved issue">` : ""}
      </article>`
      )
      .join("");
  }

  wardFilter.addEventListener("change", load);
  load();
});
