document.addEventListener("DOMContentLoaded", () => {
  const filterForm = document.getElementById("filter-bar");
  const queueBody = document.getElementById("queue-body");
  const queueEmpty = document.getElementById("queue-empty");
  const statsBox = document.getElementById("dash-stats");
  if (!filterForm) return;

  function currentFilters() {
    const data = new FormData(filterForm);
    return {
      ward: data.get("ward") || undefined,
      category: data.get("category") || undefined,
      status: data.get("status") || undefined,
      urgency_level: data.get("urgency_level") || undefined,
      q: data.get("q") || undefined,
      cluster: filterForm.cluster.checked ? "true" : "false",
    };
  }

  async function refreshStats() {
    const stats = await Api.get("/api/stats", { ward: filterForm.ward.value || undefined });
    statsBox.querySelector('[data-field="total_open"]').textContent = stats.total_open;
    statsBox.querySelector('[data-field="total_resolved"]').textContent = stats.total_resolved;
    statsBox.querySelector('[data-field="critical"]').textContent = stats.by_urgency_level.critical || 0;
    statsBox.querySelector('[data-field="avg_resolution_hours"]').textContent =
      stats.avg_resolution_hours != null ? stats.avg_resolution_hours : "–";
  }

  function rowHtml(g) {
    const clusterChip =
      g.member_count > 1
        ? `<button type="button" class="cluster-chip" data-ticket="${g.ticket_id}" data-action="open-modal">🔁 ${g.member_count} similar reports</button>`
        : "";
    return `
      <tr class="queue-row urgency-${g.urgency_level}" data-ticket="${g.ticket_id}" data-action="open-modal" data-reasons-target>
        <td>
          <span class="ticket-id">${escapeHtml(g.ticket_id)}</span>
          <div class="summary">${escapeHtml(g.summary || g.raw_text)}</div>
          <span class="text-muted">${escapeHtml(g.ward)} · ${escapeHtml(g.category_label)} · ${timeAgo(g.created_at)}${g.photo_path ? " · 📷" : ""}</span>
          ${clusterChip}
        </td>
        <td>
          ${urgencyBadgeHtml(g.urgency_level, g.urgency_score)}
          <div class="urgency-reasons"><ul>${(g.urgency_reasons || [])
            .map((r) => `<li>${escapeHtml(r)}</li>`)
            .join("")}</ul></div>
        </td>
        <td><span class="text-muted">${escapeHtml(g.status.replace("_", " "))}</span></td>
      </tr>
    `;
  }

  async function refreshQueue() {
    const result = await Api.get("/api/grievances", { ...currentFilters(), page_size: 100 });
    if (!result.results.length) {
      queueBody.innerHTML = "";
      queueEmpty.hidden = false;
      return;
    }
    queueEmpty.hidden = true;
    queueBody.innerHTML = result.results.map(rowHtml).join("");
  }

  queueBody.addEventListener("click", (e) => {
    if (e.target.closest("[data-action='toggle-reasons']")) return;
    const trigger = e.target.closest("[data-action='open-modal']");
    if (!trigger) return;
    GrievanceModal.open(trigger.dataset.ticket);
  });

  filterForm.addEventListener("change", () => {
    refreshQueue();
    refreshStats();
  });
  filterForm.addEventListener("submit", (e) => e.preventDefault());
  document.addEventListener("grievance-updated", () => {
    refreshQueue();
    refreshStats();
  });

  pollEndpoint(refreshQueue, 5000);
  pollEndpoint(refreshStats, 8000);
});
