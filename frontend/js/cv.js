import { getCandidateProfile, initShell, uploadCv } from "./api.js";

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

function renderList(items) {
  if (!items.length) {
    return `<p class="mt-3 text-sm text-zinc-500">No aparece en el CV.</p>`;
  }
  return `<ul class="mt-3 space-y-2 text-sm text-zinc-700">${items
    .map((item) => `<li>${escapeHtml(item)}</li>`)
    .join("")}</ul>`;
}

function showProfile(profile, cleanedCv) {
  const nameEl = document.getElementById("profile-name");
  const titleEl = document.getElementById("profile-title");
  const sectionsEl = document.getElementById("profile-sections");
  const statusEl = document.getElementById("profile-status");
  const cleanedEl = document.getElementById("cleaned-cv");

  if (!sectionsEl) {
    return;
  }

  nameEl.textContent = profile.name;
  titleEl.textContent = profile.headline || "";
  if (statusEl) {
    statusEl.textContent = profile.source === "demo" ? "Demo" : "CV organizado";
  }
  if (cleanedEl) {
    cleanedEl.textContent = cleanedCv || "";
  }

  const experience = (profile.experience || []).map((item) => {
    const heading = [item.position, item.company].filter(Boolean).join(" · ");
    return item.description ? `${heading}: ${item.description}` : heading;
  });
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
}

function initUploadPage() {
  const fileInput = document.getElementById("cv-file");
  const uploadButton = document.getElementById("upload-button");
  const fileLabel = document.getElementById("file-label");
  const status = document.getElementById("upload-status");

  if (!fileInput || !uploadButton) {
    return;
  }

  uploadButton.addEventListener("click", () => fileInput.click());

  fileInput.addEventListener("change", async () => {
    const file = fileInput.files?.[0];
    if (!file) {
      return;
    }

    if (fileLabel) fileLabel.textContent = file.name;
    uploadButton.disabled = true;
    if (status) {
      renderStatus(
        status,
        "loading",
        "Leyendo y organizando tu CV",
        "Extraemos el texto (incluye OCR en PDF escaneado) y armamos el perfil. El archivo original no se modifica."
      );
    }

    try {
      const result = await uploadCv(file);
      if (status) {
        const method = result.document?.extraction_method;
        const methodLabel =
          method === "pymupdf+ocr" || method === "pymupdf+ocr-mixed"
            ? " · lectura OCR"
            : method === "python-docx"
              ? " · DOCX"
              : "";
        const pages =
          result.document?.pages != null
            ? `${result.document.pages} páginas`
            : `${result.document?.characters ?? 0} caracteres`;
        renderStatus(
          status,
          "success",
          "CV organizado",
          `${escapeHtml(result.profile?.name || file.name)} · ${escapeHtml(pages)}${escapeHtml(methodLabel)}. El original sigue intacto.`
        );
      }
      if (result.profile && document.getElementById("profile-sections")) {
        showProfile(result.profile, result.cleaned_cv);
      } else {
        window.location.href = "/cv";
      }
    } catch (error) {
      if (status) {
        renderStatus(
          status,
          "error",
          "No se pudo organizar el CV",
          escapeHtml(error.message || "Error inesperado.")
        );
      }
    } finally {
      uploadButton.disabled = false;
      fileInput.value = "";
    }
  });
}

function initProfilePage() {
  if (!document.getElementById("profile-sections")) {
    return;
  }

  getCandidateProfile()
    .then((payload) => showProfile(payload.profile, payload.cleaned_cv))
    .catch((error) => {
      const sectionsEl = document.getElementById("profile-sections");
      if (sectionsEl) {
        sectionsEl.innerHTML = `<p class="text-sm text-red-700">${escapeHtml(error.message)}</p>`;
      }
    });
}

initShell();
initUploadPage();
initProfilePage();
