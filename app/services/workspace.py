from uuid import uuid4

from app.schemas.candidate import CandidateProfile
from app.schemas.job import JobMatch, JobProfile
from app.schemas.optimization import CustomizedCV, OptimizationPlan
from app.services.document.document_types import DocumentContent
from app.services.demo import DEMO_JOBS, DEMO_PROFILE


class Workspace:
    def __init__(self) -> None:
        self.reset_demo()

    def reset_demo(self) -> None:
        self.candidate_id = DEMO_PROFILE.id
        self.profile = DEMO_PROFILE.model_copy(deep=True)
        self.master_document: DocumentContent | None = None
        self.master_document_id: str | None = None
        self.jobs: dict[str, JobProfile] = {
            job.id: job.model_copy(deep=True) for job in DEMO_JOBS
        }
        self.matches: dict[str, JobMatch] = {}
        self.plans: dict[str, OptimizationPlan] = {}
        self.customized: dict[str, CustomizedCV] = {}
        self.apply_mode = "manual_review"

    def save_master_document(self, document: DocumentContent) -> str:
        self.master_document = document
        self.master_document_id = str(uuid4())
        return self.master_document_id

    def set_profile(self, profile: CandidateProfile) -> CandidateProfile:
        profile.id = self.candidate_id
        self.profile = profile
        return profile


workspace = Workspace()
