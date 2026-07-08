let map;
let markers = [];
let heatmap;
let heatmapVisible = false;

const URGENCY_COLORS = { low: "#16a34a", medium: "#d97706", high: "#ea580c", critical: "#dc2626" };

// Classic teardrop pin, tip anchored at (0,0).
const PIN_PATH = "M 0,0 C -2.2,-7 -9,-9.5 -9,-16.5 A 9,9 0 1,1 9,-16.5 C 9,-9.5 2.2,-7 0,0 Z";

// Called by the Maps JS API when the key is rejected (bad referrer, billing,
// etc.) — degrade to the same list view used when no key is configured,
// instead of leaving a blank grey rectangle.
window.gm_authFailure = () => {
  const canvas = document.getElementById("map-canvas");
  if (canvas) canvas.style.display = "none";
  const errEl = document.getElementById("map-auth-error");
  if (errEl) errEl.hidden = false;
  window.MAPS_ENABLED = false;
  renderFallbackList();
};

function initGoogleMap() {
  map = new google.maps.Map(document.getElementById("map-canvas"), {
    center: { lat: 22.5726, lng: 88.3639 },
    zoom: 11,
  });
  loadAndRenderMarkers();
  pollEndpoint(loadAndRenderMarkers, 6000, false);
}

async function loadAndRenderMarkers() {
  const ward = document.getElementById("map-ward-filter")?.value;
  const result = await Api.get("/api/grievances", { ward: ward || undefined, page_size: 200, cluster: "true" });
  const items = result.results.filter((g) => g.status !== "resolved" && g.status !== "rejected" && g.latitude && g.longitude);

  markers.forEach((m) => m.setMap(null));
  markers = items.map((g) => {
    const marker = new google.maps.Marker({
      position: { lat: g.latitude, lng: g.longitude },
      map,
      title: g.summary || g.raw_text,
      icon: {
        path: PIN_PATH,
        scale: 1.6,
        fillColor: URGENCY_COLORS[g.urgency_level] || "#64748b",
        fillOpacity: 0.95,
        strokeWeight: 1.5,
        strokeColor: "#fff",
        anchor: new google.maps.Point(0, 0),
      },
    });
    marker.addListener("click", () => GrievanceModal.open(g.ticket_id));
    return marker;
  });

  if (window.google?.maps?.visualization) {
    if (heatmap) heatmap.setMap(null);
    heatmap = new google.maps.visualization.HeatmapLayer({
      data: items.map((g) => ({ location: new google.maps.LatLng(g.latitude, g.longitude), weight: g.urgency_score })),
    });
    heatmap.setMap(heatmapVisible ? map : null);
  }
}

function renderFallbackList() {
  const listEl = document.getElementById("map-fallback-list");
  if (!listEl) return;

  pollEndpoint(async () => {
    const ward = document.getElementById("map-ward-filter")?.value;
    const result = await Api.get("/api/grievances", { ward: ward || undefined, page_size: 100, cluster: "true" });
    const items = result.results.filter((g) => g.status !== "resolved" && g.status !== "rejected");
    listEl.innerHTML = items
      .map(
        (g) => `
      <div class="queue-row" style="padding:0.8rem;" data-ticket="${g.ticket_id}">
        ${urgencyBadgeHtml(g.urgency_level, g.urgency_score)}
        <strong>${escapeHtml(g.ward)}</strong> — ${escapeHtml(g.summary || g.raw_text)}
      </div>`
      )
      .join("");
  }, 6000);

  listEl.addEventListener("click", (e) => {
    const row = e.target.closest("[data-ticket]");
    if (row) GrievanceModal.open(row.dataset.ticket);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("map-ward-filter")?.addEventListener("change", () => {
    if (window.MAPS_ENABLED && map) loadAndRenderMarkers();
  });
  document.getElementById("heatmap-toggle")?.addEventListener("click", () => {
    heatmapVisible = !heatmapVisible;
    if (heatmap) heatmap.setMap(heatmapVisible ? map : null);
  });

  if (!window.MAPS_ENABLED) {
    renderFallbackList();
  }

  document.addEventListener("grievance-updated", () => {
    if (window.MAPS_ENABLED && map) loadAndRenderMarkers();
  });
});
