from fastapi import APIRouter

from app.core.config import OPENAI_API_KEY, OPENAI_MODEL, supabase_configured
from app.services.ai.usage import ai_status
from app.services.persistence import ensure_agent_user_id, persistence_enabled


router = APIRouter()


@router.get("/health")
def health():
    return {
        "status": "healthy",
        "openai_configured": bool(OPENAI_API_KEY),
        "openai_model": OPENAI_MODEL,
        "persistence": "supabase" if persistence_enabled() else "memory",
        "supabase_configured": supabase_configured(),
        "supabase_user_ready": bool(ensure_agent_user_id())
        if persistence_enabled()
        else False,
        "ai_agents": [
            "cv_analyze",
            "job_analyze",
            "match",
            "customize",
        ],
        "ai_usage": ai_status(),
    }
