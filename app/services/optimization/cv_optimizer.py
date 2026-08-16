from app.schemas.candidate import CandidateProfile
from app.schemas.job import JobMatch, JobProfile
from app.schemas.optimization import CustomizedCV, OptimizationPlan


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


def build_customized_cv(
    profile: CandidateProfile,
    job: JobProfile,
    plan: OptimizationPlan,
    customized_id: str,
) -> CustomizedCV:
    matched = set(plan.emphasize)
    experience_lines: list[str] = []
    for item in profile.experience:
        title = " · ".join(
            part for part in [item.position, item.company] if part
        )
        relevant = [skill for skill in item.skills if skill in matched]
        line = title
        if item.description:
            line = f"{title}: {item.description}"
        if relevant:
            line = f"{line} ({', '.join(relevant)})"
        experience_lines.append(line)

    if profile.summary:
        summary = profile.summary
        if plan.emphasize:
            summary = (
                f"{profile.summary} En esta postulación se enfatizan "
                f"competencias ya presentes: {', '.join(plan.emphasize[:5])}."
            )
    else:
        summary = None

    skills = [skill for skill in profile.skills if skill in matched] or list(
        profile.skills
    )

    return CustomizedCV(
        id=customized_id,
        candidate_id=profile.id,
        job_id=job.id,
        headline=profile.headline,
        summary=summary,
        emphasize=plan.emphasize,
        experience=experience_lines,
        skills=skills,
        notes=(
            "CV adaptado sin inventar información. "
            "El CV maestro no fue modificado."
        ),
        invented=False,
    )
