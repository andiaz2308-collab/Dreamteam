from app.schemas.candidate import CandidateProfile
from app.schemas.job import JobMatch, JobProfile
from app.schemas.optimization import CustomizedCV, OptimizationPlan
from app.services.cv_format import render_customized_cv


def build_plan(
    profile: CandidateProfile,
    job: JobProfile,
    match: JobMatch,
) -> OptimizationPlan:
    emphasize = [item.label for item in match.matched]
    missing = [item.label for item in match.missing]
    deemphasize = [
        skill
        for skill in profile.skills
        if skill not in emphasize and skill not in job.preferred_skills
    ]
    changes = [
        "Conservar el CV maestro intacto.",
        "Reordenar experiencia para destacar evidencia real alineada a la oferta.",
        "No agregar habilidades, cargos ni logros que no estén en el perfil.",
    ]
    if missing:
        changes.append(
            "Dejar visibles las brechas; no inventar requisitos faltantes."
        )
    return OptimizationPlan(
        job_id=job.id,
        emphasize=emphasize,
        deemphasize=deemphasize[:8],
        missing=missing,
        recommended_keywords=emphasize,
        changes=changes,
    )


def _experience_relevance(item, matched: set[str], emphasize: list[str]) -> int:
    score = 0
    score += sum(1 for skill in item.skills if skill in matched)
    blob = " ".join(
        part
        for part in [item.position, item.company, item.description or ""]
        if part
    ).lower()
    for label in emphasize:
        if label.lower() in blob:
            score += 2
    return score


def build_customized_cv(
    profile: CandidateProfile,
    job: JobProfile,
    plan: OptimizationPlan,
    customized_id: str,
) -> CustomizedCV:
    matched = set(plan.emphasize)

    ranked = sorted(
        profile.experience,
        key=lambda item: _experience_relevance(item, matched, plan.emphasize),
        reverse=True,
    )

    experience_lines: list[str] = []
    for item in ranked:
        title = " · ".join(
            part for part in [item.position, item.company] if part
        )
        dates = " – ".join(
            part
            for part in [
                item.start_date,
                item.end_date or ("Actual" if item.current else None),
            ]
            if part
        )
        relevant = [skill for skill in item.skills if skill in matched]
        line = title
        if dates:
            line = f"{title} ({dates})" if title else dates
        if item.description:
            line = f"{line}: {item.description}" if line else item.description
        if relevant:
            line = f"{line} [{', '.join(relevant)}]"
        if line:
            experience_lines.append(line)

    if profile.summary:
        summary = profile.summary
        if plan.emphasize:
            summary = (
                f"{profile.summary} Enfoque para esta oferta: "
                f"{', '.join(plan.emphasize[:5])}."
            )
    else:
        summary = None

    matched_skills = [skill for skill in profile.skills if skill in matched]
    other_skills = [skill for skill in profile.skills if skill not in matched]
    skills = matched_skills + other_skills

    headline = profile.headline
    if job.title and profile.headline:
        headline = f"{profile.headline} · Orientación: {job.title}"
    elif job.title:
        headline = job.title

    customized = CustomizedCV(
        id=customized_id,
        candidate_id=profile.id,
        job_id=job.id,
        headline=headline,
        summary=summary,
        emphasize=plan.emphasize,
        experience=experience_lines,
        skills=skills,
        notes=(
            "CV adaptado sin inventar información. "
            "El CV maestro no fue modificado."
        ),
        invented=False,
        target_role=job.title,
        target_company=job.company,
    )
    customized.rendered_text = render_customized_cv(profile, customized, job)
    return customized
