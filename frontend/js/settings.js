import { getSettings, initShell } from "./api.js";

initShell();

getSettings()
  .then((payload) => {
    const settings = payload.settings || {};
    const model = document.getElementById("settings-model");
    const mode = document.getElementById("settings-mode");
    const persistence = document.getElementById("settings-persistence");
    if (model) model.textContent = settings.openai_model || "gpt-4o-mini";
    if (mode) {
      mode.textContent =
        settings.apply_mode === "manual_review"
          ? "Revisión manual"
          : settings.apply_mode;
    }
    if (persistence) {
      const who = settings.candidate_name
        ? `Perfil activo: ${settings.candidate_name}.`
        : "Aún no hay CV subido.";
      persistence.textContent =
        `Hoy los datos viven en memoria del servidor. Auth y Supabase son el siguiente bloque. ${who}`;
    }
  })
  .catch(() => {
    const persistence = document.getElementById("settings-persistence");
    if (persistence) {
      persistence.textContent = "No se pudieron leer las configuraciones.";
    }
  });
