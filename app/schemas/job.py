from pydantic import BaseModel, Field


class JobProfile(BaseModel):
    id: str
    title: str
    company: str
    location: str | None = None
    modality: str | None = None
    seniority: str | None = None
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    education: str | None = None
    experience_requirements: str | None = None
    languages: list[str] = Field(default_factory=list)
    salary: str | None = None
    keywords: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    url: str | None = None
    source: str = "demo"


class MatchItem(BaseModel):
    label: str
    status: str


class JobMatch(BaseModel):
    job_id: str
    candidate_id: str
    score: int
    matched: list[MatchItem] = Field(default_factory=list)
    missing: list[MatchItem] = Field(default_factory=list)
    partial: list[MatchItem] = Field(default_factory=list)
    summary: str
