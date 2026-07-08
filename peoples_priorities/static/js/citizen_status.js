document.addEventListener("DOMContentLoaded", () => {
  const searchForm = document.getElementById("ticket-search");
  if (!searchForm) return;

  const ticketInput = document.getElementById("ticket-input");
  const resultBox = document.getElementById("status-result");
  const chatWindow = document.getElementById("chat-window");
  const chatForm = document.getElementById("chat-form");
  const chatInput = document.getElementById("chat-input");

  const STEPS = ["submitted", "acknowledged", "in_progress", "resolved"];
  let currentTicket = null;
  let stopPolling = null;

  const params = new URLSearchParams(window.location.search);
  const initialTicket = params.get("ticket");
  if (initialTicket) {
    ticketInput.value = initialTicket;
    loadTicket(initialTicket);
  }

  searchForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const ticket = ticketInput.value.trim().toUpperCase();
    if (ticket) loadTicket(ticket);
  });

  function loadTicket(ticket) {
    currentTicket = ticket;
    if (stopPolling) stopPolling();
    resultBox.innerHTML = '<p aria-busy="true">Loading…</p>';
    stopPolling = pollEndpoint(() => renderTicket(ticket), 5000);
  }

  async function renderTicket(ticket) {
    try {
      const g = await Api.get(`/api/grievances/${ticket}`);
      resultBox.innerHTML = renderTimeline(g);
      chatForm.hidden = false;
    } catch (err) {
      resultBox.innerHTML = `<p class="text-muted">No grievance found for ${escapeHtml(ticket)}.</p>`;
      chatForm.hidden = true;
    }
  }

  function renderTimeline(g) {
    const currentIndex = STEPS.indexOf(g.status);
    const steps = STEPS.map((step, i) => {
      const cls = g.status === "rejected" ? "" : i < currentIndex ? "done" : i === currentIndex ? "current" : "";
      const historyEntry = g.status_history.find((h) => h.status === step);
      return `<li class="${cls}"><strong>${step.replace("_", " ")}</strong>${
        historyEntry ? `<span class="ts">${timeAgo(historyEntry.changed_at)}</span>` : ""
      }</li>`;
    }).join("");

    const clusterNote =
      g.member_count > 1
        ? `<p class="text-muted">🔁 Part of a wider issue affecting an estimated ${g.affected_count} residents.</p>`
        : "";

    return `
      <article>
        <header>
          <strong>${escapeHtml(g.ticket_id)}</strong> — ${escapeHtml(g.category_label)}
          ${urgencyBadgeHtml(g.urgency_level, g.urgency_score)}
        </header>
        <p>${escapeHtml(g.summary || g.raw_text)}</p>
        ${clusterNote}
        <ul class="timeline">${steps}</ul>
      </article>
    `;
  }

  if (chatForm) {
    chatForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const message = chatInput.value.trim();
      if (!message) return;
      appendBubble(message, "user");
      chatInput.value = "";
      try {
        const res = await Api.post("/api/chatbot", { ticket_id: currentTicket, message });
        appendBubble(res.reply, "bot");
      } catch (err) {
        appendBubble("Sorry, something went wrong answering that.", "bot");
      }
    });
  }

  function appendBubble(text, role) {
    const div = document.createElement("div");
    div.className = `chat-bubble ${role}`;
    div.textContent = text;
    chatWindow.appendChild(div);
    chatWindow.scrollTop = chatWindow.scrollHeight;
  }
});
