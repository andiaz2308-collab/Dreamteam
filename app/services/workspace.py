from uuid import uuid4

from app.schemas.candidate import CandidateProfile
from app.schemas.job import JobMatch, JobProfile
from app.schemas.optimization import CustomizedCV, OptimizationPlan
from app.services.document.document_types import DocumentContent


class Workspace:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.candidate_id = str(uuid4())
        self.profile: CandidateProfile | None = None
        self.master_document: DocumentContent | None = None
        self.master_document_id: str | None = None
        self.jobs: dict[str, JobProfile] = {}
        self.matches: dict[str, JobMatch] = {}
        self.plans: dict[str, OptimizationPlan] = {}
        self.customized: dict[str, CustomizedCV] = {}
        self.apply_mode = "manual_review"

    def has_profile(self) -> bool:
        return self.profile is not None

    def save_master_document(self, document: DocumentContent) -> str:
        self.master_document = document
        self.master_document_id = str(uuid4())
        return self.master_document_id

    def set_profile(self, profile: CandidateProfile) -> CandidateProfile:
        profile.id = self.candidate_id
        self.profile = profile
        return profile

    def require_profile(self) -> CandidateProfile:
        if self.profile is None:
            raise ValueError(
                "Primero sube y organiza tu CV. No hay perfil de candidato todavía."
            )
        return self.profile


workspace = Workspace()
