from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.config import OPENAI_API_KEY, OPENAI_MODEL
from app.services.ai.usage import ai_status
from app.services.workspace import workspace


router = APIRouter(prefix="/api/settings", tags=["settings"])


class SettingsUpdate(BaseModel):
    apply_mode: str = Field(default="manual_review")


@router.get("")
def get_settings():
    return {
        "status": "success",
        "settings": {
            "openai_model": OPENAI_MODEL,
            "openai_configured": bool(OPENAI_API_KEY),
            "apply_mode": workspace.apply_mode,
            "automation_enabled": False,
            "persistence": "memory",
            "auth_enabled": False,
            "has_profile": workspace.has_profile(),
            "candidate_name": (
                workspace.profile.name if workspace.has_profile() else None
            ),
            "ai_agents": {
                "cv_upload": "openai",
                "job_analyze": "openai",
                "match": "openai",
                "customize": "openai",
                "apply_queue": "local",
            },
            "ai_usage": ai_status(),
        },
    }


@router.post("")
def update_settings(payload: SettingsUpdate):
    if payload.apply_mode != "manual_review":
        raise HTTPException(
            status_code=400,
            detail=(
                "El envío automático solo se activará con una integración "
                "permitida. Hoy el modo válido es manual_review."
            ),
        )
    workspace.apply_mode = payload.apply_mode
    return get_settings()
