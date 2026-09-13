import json

from app.schemas.ai_agents import ExtractedMatch
from app.schemas.candidate import CandidateProfile
from app.schemas.job import JobMatch, JobProfile
from app.services.ai.structured import StructuredOutputError, parse_structured
from app.services.ai.usage import record_ai_call
from app.services.matching.job_matcher import match_profile_to_job as heuristic_match


SYSTEM_PROMPT = """
Eres el agente de matching de AgenteCV.
Compara SOLO evidencia presente en el perfil del candidato contra la oferta.
No inventes habilidades, experiencia ni títulos.
status de cada item: matched | partial | missing.
score entero 0-100, realista y conservador.
summary en español, breve y accionable.
Devuelve solo el esquema solicitado.
""".strip()


def match_profile_to_job_ai(
    profile: CandidateProfile,
    job: JobProfile,
) -> JobMatch:
    payload = {
        "candidate": profile.model_dump(mode="json"),
        "job": job.model_dump(mode="json"),
    }
    try:
        extracted = parse_structured(
            ExtractedMatch,
            SYSTEM_PROMPT,
            "MATCH_INPUT_JSON:\n" + json.dumps(payload, ensure_ascii=False),
        )
        record_ai_call("match", True, f"score={extracted.score}")
        return JobMatch(
            job_id=job.id,
            candidate_id=profile.id,
            score=extracted.score,
            matched=extracted.matched,
            missing=extracted.missing,
            partial=extracted.partial,
            summary=extracted.summary,
        )
    except StructuredOutputError as exc:
        record_ai_call("match", False, str(exc))
        # Fallback local solo si la IA falla; el front verá summary heurístico.
        fallback = heuristic_match(profile, job)
        fallback.summary = (
            f"{fallback.summary} (match local: la IA no respondió: {exc})"
        )
        return fallback
