from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.routes.applications import service as application_service
from app.schemas.application import ApplicationCreate
from app.services.ai.structured import StructuredOutputError
from app.services.matching.job_matcher import match_profile_to_job
from app.services.optimization.cv_optimizer import (
    build_customized_cv,
    build_plan,
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


@router.get("")
def list_jobs():
    profile = workspace.profile
    items = []
    for job in workspace.jobs.values():
        match = workspace.matches.get(job.id)
        items.append(
            {
                **job.model_dump(mode="json"),
                "match": match.model_dump(mode="json") if match else None,
                "customized_cv_id": next(
                    (
                        cv.id
                        for cv in workspace.customized.values()
                        if cv.job_id == job.id
                    ),
                    None,
                ),
            }
        )
    return {
        "status": "success",
        "candidate": {
            "id": profile.id,
            "name": profile.name,
            "headline": profile.headline,
        },
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
    job = _job_or_404(job_id)
    match = match_profile_to_job(workspace.profile, job)
    workspace.matches[job.id] = match
    return {"status": "success", "match": match.model_dump(mode="json")}


@router.post("/{job_id}/customize")
def customize_cv(job_id: str):
    job = _job_or_404(job_id)
    match = workspace.matches.get(job.id) or match_profile_to_job(
        workspace.profile, job
    )
    workspace.matches[job.id] = match
    plan = build_plan(workspace.profile, job, match)
    customized = build_customized_cv(
        workspace.profile,
        job,
        plan,
        customized_id=str(uuid4()),
    )
    workspace.plans[job.id] = plan
    workspace.customized[customized.id] = customized
    return {
        "status": "success",
        "plan": plan.model_dump(mode="json"),
        "customized_cv": customized.model_dump(mode="json"),
    }


@router.post("/{job_id}/apply")
def apply_to_job(job_id: str):
    job = _job_or_404(job_id)
    match = workspace.matches.get(job.id)
    customized = next(
        (cv for cv in workspace.customized.values() if cv.job_id == job.id),
        None,
    )
    if match is None or customized is None:
        raise HTTPException(
            status_code=400,
            detail="Primero analiza la oferta y adapta el CV.",
        )

    application = application_service.create_and_queue(
        ApplicationCreate(
            candidate_id=workspace.profile.id,
            job_id=job.id,
            customized_cv_id=customized.id,
            company=job.company,
            position=job.title,
            job_url=job.url,
            match_percent=match.score,
            notes="Listo para revisión manual. Sin envío automático.",
        )
    )
    return {
        "status": "success",
        "application": application.model_dump(mode="json"),
    }
