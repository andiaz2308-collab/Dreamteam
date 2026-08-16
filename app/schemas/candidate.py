from pydantic import BaseModel, EmailStr, Field


class ExperienceItem(BaseModel):
    company: str | None = None
    position: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    current: bool = False
    description: str | None = None
    skills: list[str] = Field(default_factory=list)


class EducationItem(BaseModel):
    institution: str | None = None
    degree: str | None = None
    field: str | None = None
    start_date: str | None = None
    end_date: str | None = None


class LanguageItem(BaseModel):
    language: str
    level: str | None = None


class CertificationItem(BaseModel):
    name: str
    institution: str | None = None
    date: str | None = None


class ProjectItem(BaseModel):
    name: str
    description: str | None = None
    technologies: list[str] = Field(default_factory=list)


class CandidateProfile(BaseModel):
    id: str = "candidate_andreina"
    name: str
    headline: str | None = None
    email: EmailStr | None = None
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
    source: str = "demo"
