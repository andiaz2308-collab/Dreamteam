import {
  applyToJob,
  createJobFromText,
  customizeJobCv,
  initShell,
  listJobs,
  matchJob,
} from "./api.js";

let lastAdapted = {
  text: "",
  filename: "CV_adaptado.txt",
};

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

function downloadText(filename, text) {
  const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename || "CV_adaptado.txt";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

function showAdaptedCv({ text, meta, filename, packageData }) {
  const panel = document.getElementById("adapted-panel");
  const textEl = document.getElementById("adapted-cv-text");
  const metaEl = document.getElementById("adapted-meta");
  const packageBox = document.getElementById("package-box");
  const checklist = document.getElementById("package-checklist");
  const actionStatus = document.getElementById("adapted-action-status");

  if (!panel || !textEl) return;

  lastAdapted = {
    text: text || "",
    filename: filename || "CV_adaptado.txt",
  };

  panel.classList.remove("hidden");
  textEl.textContent = lastAdapted.text;
  if (metaEl) metaEl.textContent = meta || "";

  if (packageBox && checklist) {
    if (packageData) {
      packageBox.classList.remove("hidden");
      checklist.innerHTML = (packageData.checklist || [])
        .map((item) => `<li>${escapeHtml(item)}</li>`)
        .join("");
      if (actionStatus) {
        actionStatus.textContent = packageData.next_step || "Postulación preparada.";
      }
    } else {
      packageBox.classList.add("hidden");
      checklist.innerHTML = "";
      if (actionStatus) actionStatus.textContent = "";
    }
  }

  panel.scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderOpportunities(items) {
  return items
    .map((item) => {
      const score = item.match?.score;
      const summary = item.match?.summary || "Aún no se calcula el match.";
      const skills = item.required_skills || [];
      const adapted = item.has_adapted_cv
        ? `<span class="badge badge-success">CV adaptado listo</span>`
        : "";
      return `
        <article class="card flex flex-col p-5" data-job-id="${item.id}">
          <div class="flex items-start justify-between gap-3">
            <div>
              <h2 class="text-base font-semibold">${escapeHtml(item.title)}</h2>
              <p class="text-sm text-zinc-500">${escapeHtml(item.company)}</p>
            </div>
            <p class="text-sm font-semibold ${score == null ? "text-zinc-400" : matchClass(score)}">${score == null ? "—" : `${score}% compatible`}</p>
          </div>
          <div class="mt-3">${adapted}</div>
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
  const jobs = payload.jobs || [];
  if (!payload.has_profile) {
    list.innerHTML = `
      <article class="card p-5 lg:col-span-2">
        <h2 class="text-base font-semibold">Primero sube tu CV</h2>
        <p class="mt-2 text-sm text-zinc-600">Sin perfil no hay matching. Ve a <a class="text-primary underline" href="/cv">Mi CV</a>, sube tu PDF o DOCX y vuelve aquí.</p>
      </article>
    `;
    if (jobs.length) {
      list.innerHTML += renderOpportunities(jobs);
    }
    return;
  }
  if (!jobs.length) {
    list.innerHTML = `<p class="text-sm text-zinc-500">No hay ofertas todavía. Pega una oferta abajo para analizarla.</p>`;
    return;
  }
  list.innerHTML = renderOpportunities(jobs);
}

initShell();
reloadJobs().catch((error) => {
  const list = document.getElementById("opportunity-list");
  if (list) list.innerHTML = `<p class="text-sm text-red-700">${escapeHtml(error.message)}</p>`;
});

document.getElementById("adapted-copy")?.addEventListener("click", async () => {
  const status = document.getElementById("adapted-action-status");
  if (!lastAdapted.text) return;
  try {
    await navigator.clipboard.writeText(lastAdapted.text);
    if (status) status.textContent = "CV adaptado copiado al portapapeles.";
  } catch {
    if (status) status.textContent = "No se pudo copiar. Selecciona el texto manualmente.";
  }
});

document.getElementById("adapted-download")?.addEventListener("click", () => {
  if (!lastAdapted.text) return;
  downloadText(lastAdapted.filename, lastAdapted.text);
  const status = document.getElementById("adapted-action-status");
  if (status) status.textContent = `Descargado: ${lastAdapted.filename}`;
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
      status.textContent = "Calculando match con OpenAI...";
      const payload = await matchJob(matchId);
      status.textContent = payload.match.summary;
      await reloadJobs();
    }
    if (customizeId) {
      status.textContent = "Adaptando CV con OpenAI (puede tardar unos segundos)...";
      const payload = await customizeJobCv(customizeId);
      status.textContent = "CV adaptado con IA. Puedes copiarlo o descargarlo abajo.";
      showAdaptedCv({
        text: payload.adapted_cv_text || payload.customized_cv?.rendered_text,
        meta: payload.customized_cv?.notes || "CV adaptado sin inventar datos.",
        filename: payload.download_name,
      });
      await reloadJobs();
    }
    if (applyId) {
      status.textContent = "Preparando postulación (match/CV con IA si hace falta)...";
      const payload = await applyToJob(applyId);
      status.textContent = "Postulación preparada. Revisa el paquete abajo.";
      showAdaptedCv({
        text: payload.adapted_cv_text || payload.package?.adapted_cv_text,
        meta: `${payload.package?.company || ""} · ${payload.package?.position || ""} · ${payload.package?.match_percent ?? ""}%`,
        filename: `CV_${(payload.package?.company || "empresa").replaceAll(" ", "_")}.txt`,
        packageData: payload.package,
      });
      await reloadJobs();
    }
  } catch (error) {
    if (status) status.textContent = error.message;
  }
});
