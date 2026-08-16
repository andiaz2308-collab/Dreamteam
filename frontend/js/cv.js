import { analyzeCv, getCandidateProfile, initShell, uploadCv } from "./api.js";

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function renderStatus(container, variant, title, body) {
  const styles = {
    loading: "border-zinc-200 bg-white",
    success: "border-zinc-200 bg-white",
    error: "border-red-200 bg-red-50",
  };

  container.innerHTML = `
    <div class="card ${styles[variant]} p-4">
      <p class="text-sm font-medium">${escapeHtml(title)}</p>
      <div class="mt-2 text-sm text-zinc-600">${body}</div>
    </div>
  `;
}

function initUploadPage() {
  const fileInput = document.getElementById("cv-file");
  const uploadButton = document.getElementById("upload-button");
  const fileLabel = document.getElementById("file-label");
  const status = document.getElementById("upload-status");

  if (!fileInput || !uploadButton || !status) {
    return;
  }

  uploadButton.addEventListener("click", () => fileInput.click());

  fileInput.addEventListener("change", async () => {
    const file = fileInput.files?.[0];
    if (!file) {
      return;
    }

    fileLabel.textContent = file.name;
    uploadButton.disabled = true;
    renderStatus(
      status,
      "loading",
      "Procesando tu CV",
      "Extrayendo texto. No guardamos el archivo en disco."
    );

    try {
      const result = await uploadCv(file);
      const doc = result.document;
      renderStatus(
        status,
        "success",
        "CV procesado",
        `
          <dl class="grid gap-2 sm:grid-cols-2">
            <div><dt class="text-zinc-500">Archivo</dt><dd>${escapeHtml(doc.filename || file.name)}</dd></div>
            <div><dt class="text-zinc-500">Páginas</dt><dd>${escapeHtml(doc.pages)}</dd></div>
            <div><dt class="text-zinc-500">Caracteres</dt><dd>${escapeHtml(doc.characters)}</dd></div>
            <div><dt class="text-zinc-500">Método</dt><dd>${escapeHtml(doc.extraction_method)}</dd></div>
          </dl>
          <button id="analyze-cv" type="button" class="btn-primary mt-4 rounded-xl px-4 py-2 text-sm font-medium">Analizar perfil</button>
        `
      );
      document.getElementById("analyze-cv")?.addEventListener("click", async (event) => {
        const button = event.currentTarget;
        button.disabled = true;
        renderStatus(status, "loading", "Analizando CV", "Una sola lectura con gpt-4o-mini. El original no se modifica.");
        try {
          await analyzeCv();
          window.location.href = "/cv";
        } catch (error) {
          renderStatus(status, "error", "No se pudo analizar el CV", escapeHtml(error.message));
        }
      });
    } catch (error) {
      renderStatus(
        status,
        "error",
        "No se pudo procesar el CV",
        escapeHtml(error.message || "Error inesperado.")
      );
    } finally {
      uploadButton.disabled = false;
      fileInput.value = "";
    }
  });
}

function renderList(items) {
  return `<ul class="mt-3 space-y-2 text-sm text-zinc-700">${items
    .map((item) => `<li>${escapeHtml(item)}</li>`)
    .join("")}</ul>`;
}

function initProfilePage() {
  const nameEl = document.getElementById("profile-name");
  const titleEl = document.getElementById("profile-title");
  const sectionsEl = document.getElementById("profile-sections");
  const statusEl = document.getElementById("profile-status");

  if (!sectionsEl) {
    return;
  }

  getCandidateProfile()
    .then((payload) => {
      const profile = payload.profile;
      nameEl.textContent = profile.name;
      titleEl.textContent = profile.headline || "";
      if (statusEl) {
        statusEl.textContent = profile.source === "demo" ? "Demo" : "CV analizado";
      }

      const experience = (profile.experience || []).map((item) =>
        [item.position, item.company].filter(Boolean).join(" · ")
      );
      const education = (profile.education || []).map((item) =>
        [item.degree, item.field, item.institution].filter(Boolean).join(" · ")
      );
      const languages = (profile.languages || []).map((item) =>
        [item.language, item.level].filter(Boolean).join(" · ")
      );
      const certifications = (profile.certifications || []).map((item) => item.name);
      const projects = (profile.projects || []).map((item) => item.name);

      const sections = [
        ["Perfil profesional", `<p class="mt-3 text-sm leading-6 text-zinc-700">${escapeHtml(profile.summary || "—")}</p>`],
        ["Experiencia", renderList(experience)],
        ["Habilidades", renderList(profile.skills || [])],
        ["Educación", renderList(education)],
        ["Idiomas", renderList(languages)],
        ["Certificaciones", renderList(certifications)],
        ["Proyectos", renderList(projects)],
      ];

      sectionsEl.innerHTML = sections
        .map(
          ([title, body]) => `
            <article class="card p-5">
              <h2 class="text-sm font-medium">${title}</h2>
              ${body}
            </article>
          `
        )
        .join("");
    })
    .catch((error) => {
      sectionsEl.innerHTML = `<p class="text-sm text-red-700">${escapeHtml(error.message)}</p>`;
    });
}

initShell();
initUploadPage();
initProfilePage();
