# Deploy AgenteCV (Docker)

AgenteCV corre como un contenedor FastAPI + Tesseract (OCR spa/eng).
Puerto por defecto: **7860** (Hugging Face Spaces).

## Probar en local con Docker

```powershell
cd C:\Users\luxia\OneDrive\Escritorio\agentecv
docker compose up --build
```

Abre: http://127.0.0.1:7860

Variables (desde `.env`, no las subas a GitHub):

- `OPENAI_API_KEY` (obligatoria para analizar CV)
- `OPENAI_MODEL` (opcional, default `gpt-4o-mini`)
- `SUPABASE_URL` / `SUPABASE_ANON_KEY` / `SUPABASE_SERVICE_ROLE_KEY` (cuando conectemos persistencia)

## Opción C — Render free (sin Docker)

Render free suele fallar en `pushing layers` con la imagen Docker + Tesseract
(muy pesada). Usa **Python nativo**:

1. New Web Service → repo Dreamteam
2. Runtime: **Python** (no Docker)
3. Build: `pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt`
4. Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Env **obligatoria**: `PYTHON_VERSION` = `3.12.8`
   (si no, Render usa 3.14 y `pydantic` falla al compilar)
6. Env app: `OPENAI_API_KEY`, `OPENAI_MODEL`, Supabase, `AGENT_USER_ID`

También hay `.python-version` y `runtime.txt` en el repo apuntando a 3.12.8.

Limitación: **sin OCR** de PDF escaneado en este host.
PDF con texto y DOCX sí funcionan. OCR queda en local / Docker completo.

`render.yaml` ya está configurado así.

## Opción A — Hugging Face Spaces (recomendada, gratis)

1. Entra a https://huggingface.co/new-space
2. Nombre: `agentecv`
3. SDK: **Docker**
4. Espacio: Public o Private
5. Create Space
6. En el Space: **Settings → Repository** → conecta el GitHub `andiaz2308-collab/Dreamteam`
   - o haz push del repo al Space
7. **Settings → Variables and secrets**:
   - Secret: `OPENAI_API_KEY`
   - Variable: `OPENAI_MODEL` = `gpt-4o-mini`
   - (luego) secrets de Supabase
8. Espera el build. URL típica: `https://TU_USER-agentecv.hf.space`

El `Dockerfile` ya usa `PORT=7860`, que es lo que espera Spaces.

## Opción B — Koyeb (gratis)

1. https://app.koyeb.com → Sign up con GitHub
2. **Create App** → **GitHub** → repo Dreamteam
3. Builder: **Dockerfile**
4. Puerto: `7860` (o el que exponga el servicio; el CMD usa `$PORT`)
5. **Environment variables**:
   - `OPENAI_API_KEY`
   - `OPENAI_MODEL=gpt-4o-mini`
6. Deploy

Si Koyeb inyecta `PORT` distinto, el contenedor ya lo respeta.

## Qué no usar para este backend

- Vercel / Netlify / GitHub Pages: no corren bien este FastAPI + OCR.

## Seguridad

- Nunca pongas `OPENAI_API_KEY` ni `SUPABASE_SERVICE_ROLE_KEY` en el frontend.
- `.env` está en `.gitignore`.
- En el host, marca las keys como **Secret**, no como variables públicas.
