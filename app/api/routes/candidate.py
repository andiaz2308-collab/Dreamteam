from fastapi import APIRouter

from app.schemas.candidate import CandidateProfile
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
    return {
        "status": "success",
        "profile": workspace.profile.model_dump(mode="json"),
    }
