const API_BASE = "";

function readErrorDetail(payload) {
  if (!payload) {
    return "No se pudo completar la solicitud.";
  }

  if (typeof payload.detail === "string") {
    return payload.detail;
  }

  if (Array.isArray(payload.detail)) {
    return payload.detail
      .map((item) => item.msg || item.detail || "")
      .filter(Boolean)
      .join(" ");
  }

  return "No se pudo completar la solicitud.";
}

export async function uploadCv(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/cv/upload`, {
    method: "POST",
    body: formData,
  });

  const payload = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(readErrorDetail(payload));
  }

  return {
    status: payload.status,
    document: {
      filename: payload.document?.filename,
      content_type: payload.document?.content_type,
      extension: payload.document?.extension,
      pages: payload.document?.pages,
      characters: payload.document?.characters,
      extraction_method: payload.document?.extraction_method,
      has_text: payload.document?.has_text,
    },
  };
}

async function requestJson(url, options = {}) {
  const response = await fetch(`${API_BASE}${url}`, options);
  const payload = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(readErrorDetail(payload));
  }

  return payload;
}

export function listApplications() {
  return requestJson("/api/applications");
}

export function getApplicationStats() {
  return requestJson("/api/applications/stats");
}

export function createApplication(body) {
  return requestJson("/api/applications", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function reviewApplication(applicationId) {
  return requestJson(`/api/applications/${applicationId}/review`, {
    method: "POST",
  });
}

export function retryApplication(applicationId) {
  return requestJson(`/api/applications/${applicationId}/retry`, {
    method: "POST",
  });
}

export function getCandidateProfile() {
  return requestJson("/api/candidate/profile");
}

export function analyzeCv() {
  return requestJson("/cv/analyze", { method: "POST" });
}

export function listJobs() {
  return requestJson("/api/jobs");
}

export function createJobFromText(text) {
  return requestJson("/api/jobs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
}

export function matchJob(jobId) {
  return requestJson(`/api/jobs/${jobId}/match`, { method: "POST" });
}

export function customizeJobCv(jobId) {
  return requestJson(`/api/jobs/${jobId}/customize`, { method: "POST" });
}

export function applyToJob(jobId) {
  return requestJson(`/api/jobs/${jobId}/apply`, { method: "POST" });
}

export function getSettings() {
  return requestJson("/api/settings");
}

export function initShell() {
  const toggle = document.getElementById("menu-toggle");
  const sidebar = document.getElementById("sidebar");
  const backdrop = document.getElementById("sidebar-backdrop");
  const closeButtons = document.querySelectorAll("[data-close-sidebar]");

  function openSidebar() {
    sidebar?.classList.remove("-translate-x-full");
    backdrop?.classList.remove("hidden");
    toggle?.setAttribute("aria-expanded", "true");
  }

  function closeSidebar() {
    sidebar?.classList.add("-translate-x-full");
    backdrop?.classList.add("hidden");
    toggle?.setAttribute("aria-expanded", "false");
  }

  toggle?.addEventListener("click", () => {
    const isClosed = sidebar?.classList.contains("-translate-x-full");
    if (isClosed) {
      openSidebar();
    } else {
      closeSidebar();
    }
  });

  backdrop?.addEventListener("click", closeSidebar);
  closeButtons.forEach((button) => button.addEventListener("click", closeSidebar));
}
