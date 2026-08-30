# Dreamteam — AgenteCV

Agente personal de búsqueda laboral.

## Flujo

1. Subir CV maestro (PDF)
2. Extraer y organizar perfil (`CandidateProfile`)
3. Analizar ofertas y calcular match
4. Adaptar CV por oferta (sin inventar datos)
5. Crear postulación → revisión manual o provider permitido

## Local

```powershell
cd agentecv
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# Editar .env con tus claves (no subir .env)
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Abrir: http://127.0.0.1:8000

## Variables de entorno

| Variable | Dónde |
|---|---|
| `OPENAI_API_KEY` | Solo backend |
| `OPENAI_MODEL` | `gpt-4o-mini` por defecto |
| `SUPABASE_URL` | Backend (próximo bloque) |
| `SUPABASE_SERVICE_ROLE_KEY` | Solo backend, nunca frontend |

## Deploy gratuito (recomendado)

**Koyeb** o **Hugging Face Spaces** con el `Dockerfile` del repo.

Variables en el panel del host: `OPENAI_API_KEY`, `OPENAI_MODEL`.

> Render free se duerme; si tu cuenta está suspendida, usar Koyeb/HF.

## Seguridad

- `.env` está en `.gitignore`
- No commitear claves
- El CV completo no se devuelve en `/cv/upload`
