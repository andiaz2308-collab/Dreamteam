from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.routes.applications import service as application_service
from app.schemas.application import ApplicationCreate
from app.services.ai.cv_customizer_ai import customize_cv_with_ai
from app.services.ai.job_matcher_ai import match_profile_to_job_ai
from app.services.ai.structured import StructuredOutputError
from app.services.optimization.cv_optimizer import build_plan
from app.services.workspace import workspace


router = APIRouter(prefix="/api/jobs", tags=["jobs"])


class JobTextPayload(BaseModel):
    text: str
    url: str | None = None


def _job_or_404(job_id: str):
    job = workspace.jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="La oferta no existe.")
    return job


def _require_profile():
    try:
        return workspace.require_profile()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _ensure_match_and_customized(job_id: str):
    profile = _require_profile()
    job = _job_or_404(job_id)
    match = workspace.matches.get(job.id)
    if match is None:
        match = match_profile_to_job_ai(profile, job)
        workspace.matches[job.id] = match

    customized = next(
        (cv for cv in workspace.customized.values() if cv.job_id == job.id),
        None,
    )
    if customized is None:
        plan = build_plan(profile, job, match)
        customized = customize_cv_with_ai(
            profile,
            job,
            match,
            customized_id=str(uuid4()),
        )
        workspace.plans[job.id] = plan
        workspace.customized[customized.id] = customized

    return profile, job, match, customized


def _application_package(application, job, match, customized) -> dict:
    checklist = [
        "CV maestro intacto (no se modificó el original).",
        "CV adaptado listo para copiar o descargar.",
        "Postulación en cola de revisión manual.",
        "No se envió nada a portales externos.",
    ]
    if match.missing:
        checklist.append(
            "Requisitos faltantes visibles: "
            + ", ".join(item.label for item in match.missing[:6])
        )
    return {
        "application_id": application.id,
        "status": application.status.value
        if hasattr(application.status, "value")
        else application.status,
        "company": job.company,
        "position": job.title,
        "job_url": job.url,
        "match_percent": match.score,
        "customized_cv_id": customized.id,
        "adapted_cv_text": customized.rendered_text,
        "checklist": checklist,
        "next_step": (
            "Revisa el CV adaptado, descárgalo y postula manualmente "
            "en la URL de la oferta si aplica."
        ),
    }


@router.get("")
def list_jobs():
    profile = workspace.profile
    items = []
    for job in workspace.jobs.values():
        match = workspace.matches.get(job.id)
        customized = next(
            (cv for cv in workspace.customized.values() if cv.job_id == job.id),
            None,
        )
        items.append(
            {
                **job.model_dump(mode="json"),
                "match": match.model_dump(mode="json") if match else None,
                "customized_cv_id": customized.id if customized else None,
                "has_adapted_cv": customized is not None,
            }
        )
    return {
        "status": "success",
        "has_profile": workspace.has_profile(),
        "candidate": (
            {
                "id": profile.id,
                "name": profile.name,
                "headline": profile.headline,
            }
            if profile is not None
            else None
        ),
        "jobs": items,
    }


@router.post("")
def create_job_from_text(payload: JobTextPayload):
    if not payload.text or len(payload.text.strip()) < 20:
        raise HTTPException(
            status_code=400,
            detail="Pega el texto de la oferta para analizarla.",
        )
    from app.services.ai.job_analyzer import analyze_job_text

    try:
        job = analyze_job_text(payload.text.strip())
    except StructuredOutputError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if payload.url:
        job.url = payload.url
    workspace.jobs[job.id] = job
    return {"status": "success", "job": job.model_dump(mode="json")}


@router.post("/{job_id}/match")
def match_job(job_id: str):
    profile = _require_profile()
    job = _job_or_404(job_id)
    match = match_profile_to_job_ai(profile, job)
    workspace.matches[job.id] = match
    return {
        "status": "success",
        "match": match.model_dump(mode="json"),
        "agent": "openai",
    }


@router.post("/{job_id}/customize")
def customize_cv(job_id: str):
    profile, job, match, customized = _ensure_match_and_customized(job_id)
    plan = build_plan(profile, job, match)
    customized = customize_cv_with_ai(
        profile,
        job,
        match,
        customized_id=customized.id,
    )
    workspace.plans[job.id] = plan
    workspace.customized[customized.id] = customized
    return {
        "status": "success",
        "plan": plan.model_dump(mode="json"),
        "customized_cv": customized.model_dump(mode="json"),
        "adapted_cv_text": customized.rendered_text,
        "download_name": f"CV_{job.company}_{job.title}.txt".replace(" ", "_"),
        "agent": "openai",
    }


@router.get("/{job_id}/adapted-cv")
def get_adapted_cv(job_id: str):
    _require_profile()
    job = _job_or_404(job_id)
    customized = next(
        (cv for cv in workspace.customized.values() if cv.job_id == job.id),
        None,
    )
    if customized is None:
        raise HTTPException(
            status_code=404,
            detail="Todavía no hay CV adaptado para esta oferta. Pulsa Adaptar CV.",
        )
    return {
        "status": "success",
        "job_id": job.id,
        "customized_cv_id": customized.id,
        "adapted_cv_text": customized.rendered_text,
        "download_name": f"CV_{job.company}_{job.title}.txt".replace(" ", "_"),
    }


@router.post("/{job_id}/apply")
def apply_to_job(job_id: str):
    _profile, job, match, customized = _ensure_match_and_customized(job_id)

    application = application_service.create_and_queue(
        ApplicationCreate(
            candidate_id=_profile.id,
            job_id=job.id,
            customized_cv_id=customized.id,
            company=job.company,
            position=job.title,
            job_url=job.url,
            match_percent=match.score,
            notes=(
                "Paquete de postulación listo para revisión manual. "
                "Sin envío automático a portales."
            ),
        )
    )
    package = _application_package(application, job, match, customized)
    return {
        "status": "success",
        "application": application.model_dump(mode="json"),
        "package": package,
        "adapted_cv_text": customized.rendered_text,
    }
