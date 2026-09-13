import json

from app.schemas.ai_agents import ExtractedCustomization
from app.schemas.candidate import CandidateProfile
from app.schemas.job import JobMatch, JobProfile
from app.schemas.optimization import CustomizedCV, OptimizationPlan
from app.services.ai.structured import StructuredOutputError, parse_structured
from app.services.ai.usage import record_ai_call
from app.services.cv_format import render_customized_cv
from app.services.optimization.cv_optimizer import build_customized_cv as local_customize
from app.services.optimization.cv_optimizer import build_plan


SYSTEM_PROMPT = """
Eres el agente de adaptación de CV de AgenteCV.
Reescribes y reordenas el CV para una oferta concreta.
Reglas estrictas:
- No inventes experiencia, empresas, cargos, fechas, skills ni logros.
- Solo usa datos del perfil del candidato.
- experience: líneas basadas en la experiencia real, priorizando lo alineado.
- skills: solo skills que existan en el perfil; pon primero las relevantes.
- summary: síntesis fiel orientada a la oferta, sin aspiraciones inventadas.
- headline: puede orientar al cargo de la oferta sin mentir sobre el perfil.
- notes: recuerda que el CV maestro no se modifica.
Devuelve solo el esquema solicitado.
""".strip()


def _filter_known_skills(profile: CandidateProfile, skills: list[str]) -> list[str]:
    known = {item.lower(): item for item in profile.skills}
    known.update({item.lower(): item for item in profile.soft_skills})
    filtered: list[str] = []
    for skill in skills:
        key = (skill or "").strip().lower()
        if key in known and known[key] not in filtered:
            filtered.append(known[key])
    if not filtered:
        return list(profile.skills)
    # append remaining profile skills
    for skill in profile.skills:
        if skill not in filtered:
            filtered.append(skill)
    return filtered


def customize_cv_with_ai(
    profile: CandidateProfile,
    job: JobProfile,
    match: JobMatch,
    customized_id: str,
) -> CustomizedCV:
    plan = build_plan(profile, job, match)
    payload = {
        "candidate": profile.model_dump(mode="json"),
        "job": job.model_dump(mode="json"),
        "match": match.model_dump(mode="json"),
        "plan": plan.model_dump(mode="json"),
    }
    try:
        extracted = parse_structured(
            ExtractedCustomization,
            SYSTEM_PROMPT,
            "CUSTOMIZE_INPUT_JSON:\n" + json.dumps(payload, ensure_ascii=False),
        )
        skills = _filter_known_skills(profile, extracted.skills)
        experience = extracted.experience or []
        if not experience:
            # safety: fall back to local builder lines
            local = local_customize(profile, job, plan, customized_id)
            experience = local.experience

        customized = CustomizedCV(
            id=customized_id,
            candidate_id=profile.id,
            job_id=job.id,
            headline=extracted.headline or profile.headline,
            summary=extracted.summary or profile.summary,
            emphasize=extracted.emphasize or plan.emphasize,
            experience=experience,
            skills=skills,
            notes=extracted.notes
            or "CV adaptado sin inventar información. El CV maestro no fue modificado.",
            invented=False,
            target_role=job.title,
            target_company=job.company,
        )
        customized.rendered_text = render_customized_cv(profile, customized, job)
        record_ai_call("customize", True, f"job={job.title}")
        return customized
    except StructuredOutputError as exc:
        record_ai_call("customize", False, str(exc))
        customized = local_customize(profile, job, plan, customized_id)
        customized.notes = (
            f"{customized.notes} (adaptación local: la IA no respondió: {exc})"
        )
        return customized
