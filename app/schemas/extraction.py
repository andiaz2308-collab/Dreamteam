from pydantic import BaseModel, Field

from app.schemas.candidate import (
    CertificationItem,
    EducationItem,
    ExperienceItem,
    LanguageItem,
    ProjectItem,
)


class ExtractedProfile(BaseModel):
    name: str
    headline: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    summary: str | None = None
    experience: list[ExperienceItem] = Field(default_factory=list)
    education: list[EducationItem] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)
    languages: list[LanguageItem] = Field(default_factory=list)
    certifications: list[CertificationItem] = Field(default_factory=list)
    projects: list[ProjectItem] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)


class ExtractedJob(BaseModel):
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
