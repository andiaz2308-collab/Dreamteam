from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.config import OPENAI_MODEL
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
            "apply_mode": workspace.apply_mode,
            "automation_enabled": False,
            "persistence": "memory",
            "auth_enabled": False,
            "candidate_demo": "Andreina Díaz Durán",
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
