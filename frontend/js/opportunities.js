import {
  applyToJob,
  createJobFromText,
  customizeJobCv,
  initShell,
  listJobs,
  matchJob,
} from "./api.js";

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function matchClass(score) {
  if (score >= 85) return "text-success";
  if (score >= 70) return "text-primary";
  return "text-warning";
}

function renderOpportunities(items) {
  return items
    .map((item) => {
      const score = item.match?.score;
      const summary = item.match?.summary || "Aún no se calcula el match.";
      const skills = item.required_skills || [];
      return `
        <article class="card flex flex-col p-5" data-job-id="${item.id}">
          <div class="flex items-start justify-between gap-3">
            <div>
              <h2 class="text-base font-semibold">${escapeHtml(item.title)}</h2>
              <p class="text-sm text-zinc-500">${escapeHtml(item.company)}</p>
            </div>
            <p class="text-sm font-semibold ${score == null ? "text-zinc-400" : matchClass(score)}">${score == null ? "—" : `${score}% compatible`}</p>
          </div>
          <div class="mt-4 flex flex-wrap gap-2">
            ${skills.map((skill) => `<span class="badge badge-neutral">${escapeHtml(skill)}</span>`).join("")}
          </div>
          <p class="mt-4 flex-1 text-sm leading-6 text-zinc-600">${escapeHtml(summary)}</p>
          <div class="mt-5 flex flex-wrap gap-2">
            <button type="button" class="rounded-xl border border-zinc-200 px-3 py-2 text-sm font-medium hover:bg-zinc-50" data-match="${item.id}">Analizar oportunidad</button>
            <button type="button" class="rounded-xl border border-zinc-200 px-3 py-2 text-sm font-medium hover:bg-zinc-50" data-customize="${item.id}">Adaptar CV</button>
            <button type="button" class="btn-primary rounded-xl px-3 py-2 text-sm font-medium" data-apply="${item.id}">Preparar postulación</button>
          </div>
          <p class="mt-3 text-sm text-zinc-500" data-job-status="${item.id}"></p>
        </article>
      `;
    })
    .join("");
}

async function reloadJobs() {
  const list = document.getElementById("opportunity-list");
  if (!list) return;
  const payload = await listJobs();
  list.innerHTML = renderOpportunities(payload.jobs || []);
}

initShell();
reloadJobs().catch((error) => {
  const list = document.getElementById("opportunity-list");
  if (list) list.innerHTML = `<p class="text-sm text-red-700">${escapeHtml(error.message)}</p>`;
});

document.getElementById("job-form")?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const textarea = document.getElementById("job-text");
  const status = document.getElementById("job-form-status");
  status.textContent = "Analizando oferta...";
  try {
    await createJobFromText(textarea.value);
    textarea.value = "";
    status.textContent = "Oferta agregada.";
    await reloadJobs();
  } catch (error) {
    status.textContent = error.message;
  }
});

document.getElementById("opportunity-list")?.addEventListener("click", async (event) => {
  const matchId = event.target.closest("[data-match]")?.getAttribute("data-match");
  const customizeId = event.target.closest("[data-customize]")?.getAttribute("data-customize");
  const applyId = event.target.closest("[data-apply]")?.getAttribute("data-apply");
  const jobId = matchId || customizeId || applyId;
  if (!jobId) return;
  const status = document.querySelector(`[data-job-status="${jobId}"]`);
  try {
    if (matchId) {
      status.textContent = "Calculando match...";
      const payload = await matchJob(matchId);
      status.textContent = payload.match.summary;
      await reloadJobs();
    }
    if (customizeId) {
      status.textContent = "Adaptando CV sin inventar datos...";
      const payload = await customizeJobCv(customizeId);
      status.textContent = payload.customized_cv.notes;
    }
    if (applyId) {
      status.textContent = "Enviando a la cola de revisión...";
      await applyToJob(applyId);
      window.location.href = "/applications";
    }
  } catch (error) {
    if (status) status.textContent = error.message;
  }
});
