from fastapi import APIRouter

from app.core.config import OPENAI_API_KEY, OPENAI_MODEL
from app.services.ai.usage import ai_status


router = APIRouter()


@router.get("/health")
def health():
    return {
        "status": "healthy",
        "openai_configured": bool(OPENAI_API_KEY),
        "openai_model": OPENAI_MODEL,
        "ai_agents": [
            "cv_analyze",
            "job_analyze",
            "match",
            "customize",
        ],
        "ai_usage": ai_status(),
    }
