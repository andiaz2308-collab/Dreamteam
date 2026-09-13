from uuid import uuid4

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from app.api.routes.applications import service as application_service
from app.schemas.application import ApplicationCreate
from app.services.ai.cv_customizer_ai import customize_cv_with_ai
from app.services.ai.job_matcher_ai import match_profile_to_job_ai
from app.services.ai.structured import StructuredOutputError
from app.services.cv_docx import build_customized_cv_docx, docx_download_name
from app.services.optimization.cv_optimizer import build_plan
from app.services.persistence import (
    ensure_agent_user_id,
    persistence_enabled,
    save_customized_cv,
    save_job,
    save_match,
)
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


def _get_customized_for_job(job_id: str):
    return next(
        (cv for cv in workspace.customized.values() if cv.job_id == job_id),
        None,
    )


def _try_persist_job(job) -> None:
    if not persistence_enabled():
        return
    user_id = ensure_agent_user_id()
    if not user_id:
        return
    try:
        old_id = job.id
        new_id = save_job(user_id=user_id, job=job)
        if old_id != new_id and old_id in workspace.jobs:
            workspace.jobs.pop(old_id, None)
        workspace.jobs[new_id] = job
    except Exception:
        return


def _try_persist_match(match) -> None:
    if not persistence_enabled() or not workspace.profile:
        return
    user_id = ensure_agent_user_id()
    if not user_id:
        return
    try:
        save_match(
            user_id=user_id,
            candidate_id=workspace.profile.id,
            match=match,
        )
    except Exception:
        return


def _try_persist_customized(customized) -> None:
    if not persistence_enabled() or not workspace.profile:
        return
    user_id = ensure_agent_user_id()
    if not user_id:
        return
    try:
        old_id = customized.id
        new_id = save_customized_cv(
            user_id=user_id,
            candidate_id=workspace.profile.id,
            customized=customized,
        )
        if old_id != new_id and old_id in workspace.customized:
            workspace.customized.pop(old_id, None)
        workspace.customized[new_id] = customized
    except Exception:
        return


def _ensure_match_and_customized(job_id: str):
    profile = _require_profile()
    job = _job_or_404(job_id)
    match = workspace.matches.get(job.id)
    if match is None:
        match = match_profile_to_job_ai(profile, job)
        workspace.matches[job.id] = match
        _try_persist_match(match)

    customized = _get_customized_for_job(job.id)
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
        _try_persist_customized(customized)

    return profile, job, match, customized


def _download_names(job, profile) -> dict:
    base = docx_download_name(job, profile).removesuffix(".docx")
    return {
        "download_name_txt": f"{base}.txt",
        "download_name_docx": f"{base}.docx",
        "docx_url": f"/api/jobs/{job.id}/adapted-cv.docx",
    }


def _application_package(application, profile, job, match, customized) -> dict:
    downloads = _download_names(job, profile)
    checklist = [
        "CV maestro intacto (no se modificó el original).",
        "CV adaptado generado con IA (sin inventar datos).",
        "Archivo DOCX listo para adjuntar en el portal.",
        "Postulación en cola de revisión manual.",
        "No se envió nada a portales externos.",
    ]
    if match.missing:
        checklist.append(
            "Requisitos faltantes a tener en cuenta: "
            + ", ".join(item.label for item in match.missing[:6])
        )

    steps = [
        "Descarga el CV en DOCX.",
        "Abre la oferta en el portal.",
        "Adjunta el DOCX y completa el formulario.",
        "Vuelve a Postulaciones si quieres revisar el paquete otra vez.",
    ]

    return {
        "application_id": application.id,
        "status": application.status.value
        if hasattr(application.status, "value")
        else application.status,
        "candidate_name": profile.name,
        "company": job.company,
        "position": job.title,
        "job_url": job.url,
        "match_percent": match.score,
        "match_summary": match.summary,
        "matched": [item.label for item in match.matched],
        "missing": [item.label for item in match.missing],
        "partial": [item.label for item in match.partial],
        "customized_cv_id": customized.id,
        "adapted_cv_text": customized.rendered_text,
        "emphasize": list(customized.emphasize),
        "checklist": checklist,
        "steps": steps,
        "attachments": [
            {
                "type": "docx",
                "label": "CV adaptado (Word)",
                "url": downloads["docx_url"],
                "filename": downloads["download_name_docx"],
            },
            {
                "type": "txt",
                "label": "CV adaptado (texto)",
                "filename": downloads["download_name_txt"],
            },
        ],
        **downloads,
        "next_step": (
            "Descarga el DOCX, revisa el paquete y postula manualmente "
            "en la URL de la oferta."
        ),
    }


@router.get("")
def list_jobs():
    profile = workspace.profile
    items = []
    for job in workspace.jobs.values():
        match = workspace.matches.get(job.id)
        customized = _get_customized_for_job(job.id)
        items.append(
            {
                **job.model_dump(mode="json"),
                "match": match.model_dump(mode="json") if match else None,
                "customized_cv_id": customized.id if customized else None,
                "has_adapted_cv": customized is not None,
                "docx_url": f"/api/jobs/{job.id}/adapted-cv.docx"
                if customized
                else None,
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
    _try_persist_job(job)
    return {"status": "success", "job": job.model_dump(mode="json")}


@router.post("/{job_id}/match")
def match_job(job_id: str):
    profile = _require_profile()
    job = _job_or_404(job_id)
    match = match_profile_to_job_ai(profile, job)
    workspace.matches[job.id] = match
    _try_persist_match(match)
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
    _try_persist_match(match)
    _try_persist_customized(customized)
    downloads = _download_names(job, profile)
    return {
        "status": "success",
        "plan": plan.model_dump(mode="json"),
        "customized_cv": customized.model_dump(mode="json"),
        "adapted_cv_text": customized.rendered_text,
        "download_name": downloads["download_name_txt"],
        **downloads,
        "agent": "openai",
    }


@router.get("/{job_id}/adapted-cv")
def get_adapted_cv(job_id: str):
    profile = _require_profile()
    job = _job_or_404(job_id)
    customized = _get_customized_for_job(job.id)
    if customized is None:
        raise HTTPException(
            status_code=404,
            detail="Todavía no hay CV adaptado para esta oferta. Pulsa Adaptar CV.",
        )
    downloads = _download_names(job, profile)
    return {
        "status": "success",
        "job_id": job.id,
        "customized_cv_id": customized.id,
        "adapted_cv_text": customized.rendered_text,
        "download_name": downloads["download_name_txt"],
        **downloads,
    }


@router.get("/{job_id}/adapted-cv.docx")
def download_adapted_cv_docx(job_id: str):
    profile = _require_profile()
    job = _job_or_404(job_id)
    customized = _get_customized_for_job(job.id)
    if customized is None:
        raise HTTPException(
            status_code=404,
            detail="Todavía no hay CV adaptado para esta oferta. Pulsa Adaptar CV.",
        )

    payload = build_customized_cv_docx(profile, customized, job)
    filename = docx_download_name(job, profile)
    return Response(
        content=payload,
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        ),
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.post("/{job_id}/apply")
def apply_to_job(job_id: str):
    profile, job, match, customized = _ensure_match_and_customized(job_id)

    application = application_service.create_and_queue(
        ApplicationCreate(
            candidate_id=profile.id,
            job_id=job.id,
            customized_cv_id=customized.id,
            company=job.company,
            position=job.title,
            job_url=job.url,
            match_percent=match.score,
            notes=(
                "Paquete de postulación listo para revisión manual. "
                "CV disponible en DOCX. Sin envío automático a portales."
            ),
        )
    )
    package = _application_package(application, profile, job, match, customized)
    return {
        "status": "success",
        "application": application.model_dump(mode="json"),
        "package": package,
        "adapted_cv_text": customized.rendered_text,
        **_download_names(job, profile),
    }
