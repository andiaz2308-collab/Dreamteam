import { getApplicationStats, initShell } from "./api.js";

/* MOCK — fallback si /api/applications/stats no está disponible. */
const DASHBOARD_STATS_MOCK = {
  jobs_analyzed: 0,
  matches: 0,
  cvs_ready: 0,
  ready_to_apply: 0,
  submitted: 0,
  review_required: 0,
};

function greetingForNow() {
  return "Buenos días";
}

function renderStats(stats) {
  const items = [
    ["Ofertas analizadas", String(stats.jobs_analyzed)],
    ["Matches", String(stats.matches)],
    ["CV preparados", String(stats.cvs_ready)],
    ["Postulaciones listas", String(stats.ready_to_apply)],
    ["Postulaciones enviadas", String(stats.submitted)],
    ["Requieren revisión", String(stats.review_required)],
  ];

  return items
    .map(
      ([label, value]) => `
        <article class="card p-5">
          <p class="text-sm text-zinc-500">${label}</p>
          <p class="mt-2 text-2xl font-semibold tracking-tight">${value}</p>
        </article>
      `
    )
    .join("");
}

initShell();

const greeting = document.getElementById("greeting");
const stats = document.getElementById("stats");

if (greeting) {
  greeting.textContent = greetingForNow();
}

if (stats) {
  stats.innerHTML = `<p class="text-sm text-zinc-500">Cargando indicadores...</p>`;
  getApplicationStats()
    .then((payload) => {
      stats.innerHTML = renderStats(payload.stats || DASHBOARD_STATS_MOCK);
    })
    .catch(() => {
      stats.innerHTML = renderStats(DASHBOARD_STATS_MOCK);
    });
}
