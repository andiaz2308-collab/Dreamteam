import unicodedata

from app.schemas.candidate import CandidateProfile
from app.schemas.job import JobMatch, JobProfile, MatchItem


def _normalize(value: str) -> str:
    text = unicodedata.normalize("NFKC", value or "").strip().lower()
    return " ".join(text.split())


def _profile_terms(profile: CandidateProfile) -> list[str]:
    terms: list[str] = []
    terms.extend(profile.skills)
    terms.extend(profile.soft_skills)
    terms.extend(item.language for item in profile.languages)
    for experience in profile.experience:
        terms.extend(experience.skills)
        if experience.position:
            terms.append(experience.position)
        if experience.description:
            terms.append(experience.description)
    if profile.headline:
        terms.append(profile.headline)
    if profile.summary:
        terms.append(profile.summary)
    for education in profile.education:
        if education.degree:
            terms.append(education.degree)
        if education.field:
            terms.append(education.field)
    return [_normalize(term) for term in terms if term]


def _contains(term: str, haystack: list[str]) -> str:
    needle = _normalize(term)
    if not needle:
        return "missing"
    if any(needle == item for item in haystack):
        return "matched"
    if len(needle) >= 4 and any(needle in item for item in haystack if item):
        return "matched"
    if len(needle) >= 4 and any(
        len(item) >= 4 and item in needle for item in haystack if item
    ):
        return "partial"
    return "missing"


def match_profile_to_job(
    profile: CandidateProfile,
    job: JobProfile,
) -> JobMatch:
    haystack = _profile_terms(profile)
    required = job.required_skills or job.keywords
    matched: list[MatchItem] = []
    missing: list[MatchItem] = []
    partial: list[MatchItem] = []

    for skill in required:
        status = _contains(skill, haystack)
        item = MatchItem(label=skill, status=status)
        if status == "matched":
            matched.append(item)
        elif status == "partial":
            partial.append(item)
        else:
            missing.append(item)

    total = max(len(required), 1)
    score = int(round(((len(matched) + 0.5 * len(partial)) / total) * 100))
    score = min(score, 100)

    summary = (
        f"Tu perfil coincide con {len(matched)} de {len(required)} requisitos."
        if required
        else "La oferta no declara requisitos comparables."
    )

    return JobMatch(
        job_id=job.id,
        candidate_id=profile.id,
        score=score,
        matched=matched,
        missing=missing,
        partial=partial,
        summary=summary,
    )
