document.addEventListener("DOMContentLoaded", () => {
  const tabs = document.getElementById("ward-tabs");
  const issueCards = document.getElementById("issue-cards");
  const clusterList = document.getElementById("cluster-list");
  const canvas = document.getElementById("trend-chart");
  if (!tabs) return;

  let chart;
  const TREND_ARROWS = { rising: "▲ Rising", falling: "▼ Falling", flat: "→ Flat" };

  async function loadWard(ward) {
    issueCards.innerHTML = '<p aria-busy="true">Loading…</p>';
    clusterList.innerHTML = '<li aria-busy="true">Loading…</li>';
    const data = await Api.get(`/api/wards/${encodeURIComponent(ward)}/planning`);
    renderIssues(data.top_issues);
    renderTrend(data.trend);
    renderClusters(data.open_clusters);
  }

  function renderIssues(issues) {
    if (!issues.length) {
      issueCards.innerHTML = '<p class="text-muted">No issues recorded for this ward yet.</p>';
      return;
    }
    issueCards.innerHTML = issues
      .map(
        (issue, i) => `
      <div class="issue-card" data-rank="${i + 1}">
        <span class="rank">Top issue &middot; No. ${i + 1}</span>
        <h3>${escapeHtml(issue.label)}</h3>
        <p>${issue.count} reports &middot; avg urgency ${issue.avg_urgency}</p>
        <p class="trend-arrow ${issue.trend_direction}">${TREND_ARROWS[issue.trend_direction]}</p>
      </div>`
      )
      .join("");
  }

  function renderTrend(trend) {
    const labels = trend.map((t) => t.period);
    const counts = trend.map((t) => t.count);
    if (chart) {
      chart.data.labels = labels;
      chart.data.datasets[0].data = counts;
      chart.update();
      return;
    }
    chart = new Chart(canvas, {
      type: "line",
      data: {
        labels,
        datasets: [
          {
            label: "Grievances / week",
            data: counts,
            borderColor: "#1a56db",
            backgroundColor: "rgba(26,86,219,0.15)",
            fill: true,
            tension: 0.3,
          },
        ],
      },
      options: { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } },
    });
  }

  function renderClusters(clusters) {
    if (!clusters.length) {
      clusterList.innerHTML = '<li class="text-muted">No active duplicate clusters in this ward.</li>';
      return;
    }
    clusterList.innerHTML = clusters
      .map(
        (c) => `
      <li data-cluster="${c.cluster_id}">
        <span>${escapeHtml(c.sample_summary || c.category_label)}</span>
        <span>${urgencyBadgeHtml(c.urgency_level, c.urgency_score)} <strong>${c.affected_count}</strong> affected</span>
      </li>`
      )
      .join("");
  }

  tabs.addEventListener("click", (e) => {
    const btn = e.target.closest("button[data-ward]");
    if (!btn) return;
    tabs.querySelectorAll("button").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    loadWard(btn.dataset.ward);
  });

  const firstWard = tabs.querySelector("button.active")?.dataset.ward;
  if (firstWard) loadWard(firstWard);
});
