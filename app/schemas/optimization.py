from pydantic import BaseModel, Field


class OptimizationPlan(BaseModel):
    job_id: str
    emphasize: list[str] = Field(default_factory=list)
    deemphasize: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)
    recommended_keywords: list[str] = Field(default_factory=list)
    changes: list[str] = Field(default_factory=list)


class CustomizedCV(BaseModel):
    id: str
    candidate_id: str
    job_id: str
    headline: str | None = None
    summary: str | None = None
    emphasize: list[str] = Field(default_factory=list)
    experience: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    notes: str
    invented: bool = False
    rendered_text: str = ""
    target_role: str | None = None
    target_company: str | None = None
