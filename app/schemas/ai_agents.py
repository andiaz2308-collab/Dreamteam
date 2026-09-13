from pydantic import BaseModel, Field

from app.schemas.job import MatchItem


class ExtractedMatch(BaseModel):
    score: int = Field(ge=0, le=100)
    matched: list[MatchItem] = Field(default_factory=list)
    missing: list[MatchItem] = Field(default_factory=list)
    partial: list[MatchItem] = Field(default_factory=list)
    summary: str


class ExtractedCustomization(BaseModel):
    headline: str | None = None
    summary: str | None = None
    emphasize: list[str] = Field(default_factory=list)
    experience: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    notes: str = (
        "CV adaptado sin inventar información. El CV maestro no fue modificado."
    )
