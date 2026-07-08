document.addEventListener("DOMContentLoaded", () => {
  const strip = document.getElementById("live-stats");
  if (!strip) return;

  pollEndpoint(async () => {
    const stats = await Api.get("/api/stats");
    strip.querySelector('[data-field="total_open"]').textContent = stats.total_open != null ? stats.total_open : "–";
    strip.querySelector('[data-field="total_resolved"]').textContent = stats.total_resolved != null ? stats.total_resolved : "–";
    strip.querySelector('[data-field="avg_resolution_hours"]').textContent =
      stats.avg_resolution_hours != null ? stats.avg_resolution_hours : "–";
  }, 8000);
});
