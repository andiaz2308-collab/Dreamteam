from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ApplicationStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    ANALYZING = "ANALYZING"
    MATCHED = "MATCHED"
    CV_READY = "CV_READY"
    READY_TO_APPLY = "READY_TO_APPLY"
    SUBMITTED = "SUBMITTED"
    FAILED = "FAILED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class ApplicationProviderName(str, Enum):
    MANUAL_REVIEW = "manual_review"
    DIRECT_APPLY = "direct_apply"


class JobContext(BaseModel):
    job_id: str
    company: str
    position: str
    url: str | None = None
    match_percent: int | None = None


class Application(BaseModel):
    id: str
    candidate_id: str
    job_id: str
    customized_cv_id: str
    provider: ApplicationProviderName | None = None
    status: ApplicationStatus
    created_at: datetime
    updated_at: datetime
    submitted_at: datetime | None = None
    error_message: str | None = None
    notes: str | None = None
    company: str
    position: str
    job_url: str | None = None
    match_percent: int | None = None
    cover_letter_id: str | None = None
    answers: list[str] = Field(default_factory=list)


class ApplicationCreate(BaseModel):
    candidate_id: str
    job_id: str
    customized_cv_id: str
    company: str
    position: str
    job_url: str | None = None
    match_percent: int | None = None
    cover_letter_id: str | None = None
    answers: list[str] = Field(default_factory=list)
    notes: str | None = None


class ProviderResult(BaseModel):
    status: ApplicationStatus
    provider: ApplicationProviderName
    job_url: str | None = None
    company: str | None = None
    position: str | None = None
    customized_cv_id: str | None = None
    cover_letter_id: str | None = None
    answers: list[str] = Field(default_factory=list)
    notes: str | None = None
    error_message: str | None = None


class ApplicationReview(BaseModel):
    message: str
    status: ApplicationStatus
    job_url: str | None = None
    company: str
    position: str
    customized_cv_id: str
    cover_letter_id: str | None = None
    answers: list[str] = Field(default_factory=list)
    notes: str | None = None


class ApplicationStats(BaseModel):
    jobs_analyzed: int
    matches: int
    cvs_ready: int
    ready_to_apply: int
    submitted: int
    review_required: int
