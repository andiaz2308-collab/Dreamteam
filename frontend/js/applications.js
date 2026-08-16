import {
  createApplication,
  initShell,
  listApplications,
  reviewApplication,
  retryApplication,
} from "./api.js";

const STATUS_LABELS = {
  DISCOVERED: "Encontrada",
  ANALYZING: "Analizando",
  MATCHED: "Match encontrado",
  CV_READY: "CV preparado",
  READY_TO_APPLY: "Lista para enviar",
  SUBMITTED: "Enviada",
  REVIEW_REQUIRED: "Requiere revisión",
  FAILED: "Error",
};

const STATUS_BADGES = {
  DISCOVERED: "badge-neutral",
  ANALYZING: "badge-warning",
  MATCHED: "badge-primary",
  CV_READY: "badge-primary",
  READY_TO_APPLY: "badge-success",
  SUBMITTED: "badge-success",
  REVIEW_REQUIRED: "badge-warning",
  FAILED: "badge-error",
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleDateString("es-CO", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function actionCell(item) {
  if (item.status === "REVIEW_REQUIRED") {
    return `<button type="button" class="text-sm font-medium text-primary" data-review="${item.id}">Revisar postulación</button>`;
  }
  if (item.status === "SUBMITTED") {
    return `<span class="text-sm text-zinc-500">Enviada</span>`;
  }
  if (item.status === "FAILED") {
    return `<button type="button" class="text-sm font-medium text-primary" data-retry="${item.id}">Reintentar</button>`;
  }
  return `<span class="text-sm text-zinc-400">—</span>`;
}

function renderApplications(items) {
  if (!items.length) {
    return `
      <div class="px-4 py-10 text-center">
        <p class="text-sm font-medium">Aún no hay postulaciones</p>
        <p class="mt-1 text-sm text-zinc-500">Crea una de demostración para ver el Application Engine.</p>
      </div>
    `;
  }

  const rows = items
    .map(
      (item) => `
        <tr class="border-t border-zinc-100">
          <td class="px-4 py-3">${escapeHtml(item.company)}</td>
          <td class="px-4 py-3">${escapeHtml(item.position)}</td>
          <td class="px-4 py-3">${item.match_percent != null ? `${item.match_percent}%` : "—"}</td>
          <td class="px-4 py-3"><span class="badge ${STATUS_BADGES[item.status] || "badge-neutral"}">${STATUS_LABELS[item.status] || item.status}</span></td>
          <td class="px-4 py-3 text-zinc-500">${formatDate(item.created_at)}</td>
          <td class="px-4 py-3">${actionCell(item)}</td>
        </tr>
      `
    )
    .join("");

  const cards = items
    .map(
      (item) => `
        <article class="border-t border-zinc-100 px-4 py-4 md:hidden">
          <div class="flex items-start justify-between gap-3">
            <div>
              <p class="font-medium">${escapeHtml(item.company)}</p>
              <p class="text-sm text-zinc-500">${escapeHtml(item.position)}</p>
            </div>
            <span class="badge ${STATUS_BADGES[item.status] || "badge-neutral"}">${STATUS_LABELS[item.status] || item.status}</span>
          </div>
          <p class="mt-2 text-sm text-zinc-500">${item.match_percent != null ? `${item.match_percent}%` : "—"} · ${formatDate(item.created_at)}</p>
          <div class="mt-3">${actionCell(item)}</div>
        </article>
      `
    )
    .join("");

  return `
    <div class="hidden overflow-x-auto md:block">
      <table class="min-w-full text-left text-sm">
        <thead class="bg-canvas text-zinc-500">
          <tr>
            <th class="px-4 py-3 font-medium">Empresa</th>
            <th class="px-4 py-3 font-medium">Cargo</th>
            <th class="px-4 py-3 font-medium">Match</th>
            <th class="px-4 py-3 font-medium">Estado</th>
            <th class="px-4 py-3 font-medium">Fecha</th>
            <th class="px-4 py-3 font-medium">Acción</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
    ${cards}
  `;
}

function showReview(review) {
  const modal = document.getElementById("review-modal");
  const body = document.getElementById("review-body");
  if (!modal || !body) return;

  body.innerHTML = `
    <p class="text-sm font-medium">${escapeHtml(review.message)}</p>
    <dl class="mt-4 grid gap-3 text-sm sm:grid-cols-2">
      <div><dt class="text-zinc-500">Empresa</dt><dd>${escapeHtml(review.company)}</dd></div>
      <div><dt class="text-zinc-500">Cargo</dt><dd>${escapeHtml(review.position)}</dd></div>
      <div><dt class="text-zinc-500">URL</dt><dd>${escapeHtml(review.job_url || "—")}</dd></div>
      <div><dt class="text-zinc-500">CV adaptado</dt><dd>${escapeHtml(review.customized_cv_id)}</dd></div>
      <div><dt class="text-zinc-500">Carta</dt><dd>${escapeHtml(review.cover_letter_id || "No hay")}</dd></div>
      <div><dt class="text-zinc-500">Notas</dt><dd>${escapeHtml(review.notes || "—")}</dd></div>
    </dl>
  `;
  modal.classList.remove("hidden");
}

async function loadApplications() {
  const table = document.getElementById("applications-table");
  const status = document.getElementById("applications-status");
  if (!table) return;

  table.innerHTML = `<p class="px-4 py-8 text-sm text-zinc-500">Cargando postulaciones...</p>`;

  try {
    const payload = await listApplications();
    table.innerHTML = renderApplications(payload.applications || []);
    if (status) status.textContent = "";
  } catch (error) {
    table.innerHTML = `<p class="px-4 py-8 text-sm text-red-700">${escapeHtml(error.message)}</p>`;
  }
}

initShell();

const table = document.getElementById("applications-table");
const modal = document.getElementById("review-modal");

table?.addEventListener("click", async (event) => {
  const reviewId = event.target.closest("[data-review]")?.getAttribute("data-review");
  const retryId = event.target.closest("[data-retry]")?.getAttribute("data-retry");

  try {
    if (reviewId) {
      const payload = await reviewApplication(reviewId);
      showReview(payload.review);
    }
    if (retryId) {
      await retryApplication(retryId);
      await loadApplications();
    }
  } catch (error) {
    const status = document.getElementById("applications-status");
    if (status) status.textContent = error.message;
  }
});

document.getElementById("close-review")?.addEventListener("click", () => {
  modal?.classList.add("hidden");
});

document.getElementById("close-review-backdrop")?.addEventListener("click", () => {
  modal?.classList.add("hidden");
});

document.getElementById("create-demo")?.addEventListener("click", async (event) => {
  const button = event.currentTarget;
  button.disabled = true;
  try {
    await createApplication({
      candidate_id: "candidate_andreina",
      job_id: "job_demo_nueva",
      customized_cv_id: "cv_custom_demo_nueva",
      company: "Reserva Costa Azul",
      position: "Bióloga de campo",
      job_url: "https://example.com/jobs/biologa-campo",
      match_percent: 84,
    });
    await loadApplications();
  } catch (error) {
    const status = document.getElementById("applications-status");
    if (status) status.textContent = error.message;
  } finally {
    button.disabled = false;
  }
});

loadApplications();
