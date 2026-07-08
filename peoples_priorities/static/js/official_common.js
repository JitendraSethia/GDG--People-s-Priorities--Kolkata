const GrievanceModal = (() => {
  const dialog = document.getElementById("grievance-modal");
  const body = document.getElementById("grievance-modal-body");
  if (!dialog) return { open: async () => {} };

  dialog.addEventListener("click", (e) => {
    if (e.target === dialog) dialog.close();
  });

  const STATUS_OPTIONS = ["submitted", "acknowledged", "in_progress", "resolved", "rejected"];

  async function open(ticketId) {
    body.innerHTML = '<p aria-busy="true">Loading…</p>';
    dialog.showModal();
    try {
      const g = await Api.get(`/api/grievances/${ticketId}`);
      body.innerHTML = render(g);
      wireStatusForm(g);
    } catch (err) {
      body.innerHTML = `<p>Couldn't load ${escapeHtml(ticketId)}.</p>`;
    }
  }

  function render(g) {
    const reasons = (g.urgency_reasons || []).map((r) => `<li>${escapeHtml(r)}</li>`).join("");
    const members = (g.cluster_members || [])
      .map((m) => `<li><strong>${escapeHtml(m.ticket_id)}</strong> — ${escapeHtml(m.raw_text)}</li>`)
      .join("");
    const history = (g.status_history || [])
      .map(
        (h) =>
          `<li>${escapeHtml(h.status)} <span class="ts">${timeAgo(h.changed_at)}${
            h.note ? " — " + escapeHtml(h.note) : ""
          }</span></li>`
      )
      .join("");

    return `
      <button class="modal-close secondary" type="button" onclick="document.getElementById('grievance-modal').close()">Close</button>
      <p class="eyebrow">${escapeHtml(g.ticket_id)} · ${escapeHtml(g.ward)}</p>
      <h3>${escapeHtml(g.category_label)}</h3>
      ${urgencyBadgeHtml(g.urgency_level, g.urgency_score)}
      ${g.safety_risk ? '<span class="urgency-badge critical">Safety risk</span>' : ""}
      <p>${escapeHtml(g.summary || g.raw_text)}</p>
      ${g.photo_path ? `<img src="${escapeHtml(g.photo_path)}" alt="Citizen-submitted photo" style="max-width:100%;border-radius:10px;margin-bottom:0.75rem;">` : ""}
      <details open>
        <summary>Why this urgency score?</summary>
        <ul>${reasons}</ul>
      </details>
      ${
        g.member_count > 1
          ? `<details>
        <summary>${g.member_count} similar reports (affecting ~${g.affected_count} residents)</summary>
        <ul>${members}</ul>
      </details>`
          : ""
      }
      <details>
        <summary>Timeline</summary>
        <ul class="timeline">${history}</ul>
      </details>
      <form id="modal-status-form">
        <label for="modal-status-select">Update status</label>
        <select id="modal-status-select" name="status">
          ${STATUS_OPTIONS.map(
            (s) => `<option value="${s}" ${s === g.status ? "selected" : ""}>${s.replace("_", " ")}</option>`
          ).join("")}
        </select>
        <input type="text" id="modal-status-note" placeholder="Add a note (optional)">
        <button type="submit">Update Status</button>
      </form>
    `;
  }

  function wireStatusForm(g) {
    const form = document.getElementById("modal-status-form");
    form?.addEventListener("submit", async (e) => {
      e.preventDefault();
      const status = document.getElementById("modal-status-select").value;
      const note = document.getElementById("modal-status-note").value || null;
      try {
        await Api.patch(`/api/grievances/${g.ticket_id}/status`, { status, note });
        open(g.ticket_id);
        document.dispatchEvent(new CustomEvent("grievance-updated"));
      } catch (err) {
        alert(err.message || "Couldn't update status");
      }
    });
  }

  return { open };
})();

document.addEventListener("click", (e) => {
  const trigger = e.target.closest("[data-action='toggle-reasons']");
  if (!trigger) return;
  const row = trigger.closest("[data-reasons-target]") || trigger.parentElement;
  const box = row?.querySelector(".urgency-reasons");
  box?.classList.toggle("open");
});
