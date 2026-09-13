from fastapi import APIRouter

from app.schemas.candidate import CandidateProfile
from app.services.cv_format import render_cleaned_cv
from app.services.workspace import workspace


router = APIRouter()


@router.post("/candidate")
def create_candidate(candidate: CandidateProfile):
    profile = workspace.set_profile(candidate)
    return {
        "status": "success",
        "candidate": profile.model_dump(mode="json"),
    }


@router.get("/api/candidate/profile")
def get_candidate_profile():
    if not workspace.has_profile():
        return {
            "status": "empty",
            "has_profile": False,
            "profile": None,
            "cleaned_cv": None,
            "message": "Sube tu CV para ver el perfil organizado.",
        }

    profile = workspace.profile
    return {
        "status": "success",
        "has_profile": True,
        "profile": profile.model_dump(mode="json"),
        "cleaned_cv": render_cleaned_cv(profile),
    }
