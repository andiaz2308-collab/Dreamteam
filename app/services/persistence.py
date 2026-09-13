"""Persistencia AgenteCV → Supabase (perfil, docs, jobs, CVs, applications)."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID, uuid4

from app.core.config import (
    AGENT_BOOTSTRAP_EMAIL,
    AGENT_BOOTSTRAP_PASSWORD,
    AGENT_USER_ID,
    SUPABASE_CV_BUCKET,
    supabase_configured,
)
from app.schemas.application import Application, ApplicationStatus
from app.schemas.candidate import CandidateProfile
from app.schemas.job import JobMatch, JobProfile
from app.schemas.optimization import CustomizedCV
from app.services.cv_format import render_cleaned_cv
from app.services.document.document_types import DocumentContent
from app.services.supabase_client import (
    SupabaseNotConfiguredError,
    get_supabase,
)
from app.services.workspace import workspace

logger = logging.getLogger(__name__)


def persistence_enabled() -> bool:
    return supabase_configured()


def _is_uuid(value: str | None) -> bool:
    if not value:
        return False
    try:
        UUID(str(value))
        return True
    except ValueError:
        return False


_RESOLVED_USER_ID: str | None = None


def ensure_agent_user_id() -> str | None:
    """Resuelve el user_id de Auth (AGENT_USER_ID o bootstrap)."""
    global _RESOLVED_USER_ID
    if _RESOLVED_USER_ID:
        return _RESOLVED_USER_ID

    if not persistence_enabled():
        return None

    if AGENT_USER_ID and _is_uuid(AGENT_USER_ID):
        _RESOLVED_USER_ID = AGENT_USER_ID
        return _RESOLVED_USER_ID

    if not AGENT_BOOTSTRAP_EMAIL or not AGENT_BOOTSTRAP_PASSWORD:
        logger.warning(
            "Supabase configurado pero falta AGENT_USER_ID (UUID) "
            "o AGENT_BOOTSTRAP_EMAIL/PASSWORD."
        )
        return None

    client = get_supabase()
    try:
        listed = client.auth.admin.list_users()
        users = getattr(listed, "users", None) or listed or []
        for user in users:
            email = getattr(user, "email", None) or (
                user.get("email") if isinstance(user, dict) else None
            )
            user_id = getattr(user, "id", None) or (
                user.get("id") if isinstance(user, dict) else None
            )
            if email and email.lower() == AGENT_BOOTSTRAP_EMAIL.lower() and user_id:
                _RESOLVED_USER_ID = str(user_id)
                return _RESOLVED_USER_ID
    except Exception as exc:
        logger.warning("No se pudo listar usuarios Auth: %s", exc)

    try:
        created = client.auth.admin.create_user(
            {
                "email": AGENT_BOOTSTRAP_EMAIL,
                "password": AGENT_BOOTSTRAP_PASSWORD,
                "email_confirm": True,
            }
        )
        user = getattr(created, "user", None) or created
        user_id = getattr(user, "id", None) or (
            user.get("id") if isinstance(user, dict) else None
        )
        if user_id:
            _ensure_profile_row(str(user_id))
            _RESOLVED_USER_ID = str(user_id)
            return _RESOLVED_USER_ID
    except Exception as exc:
        logger.error("No se pudo crear usuario bootstrap: %s", exc)
    return None


def _ensure_profile_row(user_id: str, full_name: str | None = None) -> None:
    client = get_supabase()
    payload = {"id": user_id}
    if full_name:
        payload["full_name"] = full_name
    client.table("profiles").upsert(payload).execute()


def _as_uuid_or_new(value: str | None) -> str:
    return str(value) if _is_uuid(value) else str(uuid4())


def save_master_cv(
    *,
    user_id: str,
    document: DocumentContent,
    file_bytes: bytes | None,
    document_id: str | None = None,
) -> str:
    client = get_supabase()
    doc_id = _as_uuid_or_new(document_id)
    storage_path = None

    if file_bytes:
        storage_path = f"{user_id}/master/{doc_id}{document.extension}"
        try:
            client.storage.from_(SUPABASE_CV_BUCKET).upload(
                storage_path,
                file_bytes,
                file_options={
                    "content-type": document.content_type,
                    "upsert": "true",
                },
            )
        except Exception as exc:
            logger.error("Error subiendo CV a Storage: %s", exc)
            storage_path = None

    row = {
        "id": doc_id,
        "user_id": user_id,
        "filename": document.filename,
        "content_type": document.content_type,
        "extension": document.extension,
        "extraction_method": document.extraction_method,
        "pages": document.pages,
        "characters": document.characters,
        "extracted_text": document.text,
        "storage_path": storage_path,
    }
    client.table("master_documents").upsert(row).execute()
    return doc_id


def save_candidate_profile(
    *,
    user_id: str,
    profile: CandidateProfile,
    master_document_id: str | None,
) -> str:
    client = get_supabase()
    profile_id = _as_uuid_or_new(profile.id if _is_uuid(profile.id) else None)
    profile.id = profile_id
    _ensure_profile_row(user_id, profile.name)

    # Keep a single active profile per user: upsert by id; also delete older? 
    # Simpler: upsert this id and store as canonical.
    data = profile.model_dump(mode="json")
    row = {
        "id": profile_id,
        "user_id": user_id,
        "master_document_id": master_document_id if _is_uuid(master_document_id) else None,
        "name": profile.name,
        "headline": profile.headline,
        "email": str(profile.email) if profile.email else None,
        "phone": profile.phone,
        "location": profile.location,
        "summary": profile.summary,
        "cleaned_cv": render_cleaned_cv(profile),
        "data": data,
        "source": profile.source or "llm",
    }
    client.table("candidate_profiles").upsert(row).execute()
    return profile_id


def save_job(*, user_id: str, job: JobProfile) -> str:
    client = get_supabase()
    job_id = _as_uuid_or_new(job.id if _is_uuid(job.id) else None)
    # Keep original string id inside data if it wasn't UUID
    payload = job.model_dump(mode="json")
    payload["local_id"] = job.id
    job.id = job_id
    row = {
        "id": job_id,
        "user_id": user_id,
        "title": job.title,
        "company": job.company,
        "url": job.url,
        "data": payload,
        "source": job.source or "manual",
    }
    client.table("job_profiles").upsert(row).execute()
    return job_id


def save_match(*, user_id: str, candidate_id: str, match: JobMatch) -> None:
    if not (_is_uuid(candidate_id) and _is_uuid(match.job_id)):
        return
    client = get_supabase()
    row = {
        "user_id": user_id,
        "candidate_id": candidate_id,
        "job_id": match.job_id,
        "score": match.score,
        "data": match.model_dump(mode="json"),
    }
    # delete previous for same pair then insert
    client.table("job_matches").delete().eq("user_id", user_id).eq(
        "job_id", match.job_id
    ).eq("candidate_id", candidate_id).execute()
    client.table("job_matches").insert(row).execute()


def save_customized_cv(
    *,
    user_id: str,
    candidate_id: str,
    customized: CustomizedCV,
) -> str:
    client = get_supabase()
    cv_id = _as_uuid_or_new(customized.id if _is_uuid(customized.id) else None)
    customized.id = cv_id
    if not (_is_uuid(candidate_id) and _is_uuid(customized.job_id)):
        return cv_id
    row = {
        "id": cv_id,
        "user_id": user_id,
        "candidate_id": candidate_id,
        "job_id": customized.job_id,
        "data": customized.model_dump(mode="json"),
        "invented": bool(customized.invented),
    }
    client.table("customized_cvs").upsert(row).execute()
    return cv_id


def save_application(*, user_id: str, application: Application) -> str:
    client = get_supabase()
    app_id = _as_uuid_or_new(application.id if _is_uuid(application.id) else None)
    application.id = app_id
    if not all(
        _is_uuid(x)
        for x in [
            application.candidate_id,
            application.job_id,
            application.customized_cv_id,
        ]
    ):
        logger.warning("Application omitida: IDs no UUID compatibles con Supabase.")
        return app_id

    status = (
        application.status.value
        if hasattr(application.status, "value")
        else str(application.status)
    )
    row = {
        "id": app_id,
        "user_id": user_id,
        "candidate_id": application.candidate_id,
        "job_id": application.job_id,
        "customized_cv_id": application.customized_cv_id,
        "provider": (
            application.provider.value
            if application.provider and hasattr(application.provider, "value")
            else application.provider
        ),
        "status": status,
        "company": application.company,
        "position": application.position,
        "job_url": application.job_url,
        "match_percent": application.match_percent,
        "error_message": application.error_message,
        "notes": application.notes,
        "submitted_at": application.submitted_at.isoformat()
        if application.submitted_at
        else None,
    }
    client.table("applications").upsert(row).execute()
    return app_id


def load_workspace(user_id: str) -> dict[str, Any]:
    """Carga estado del usuario en el workspace en memoria."""
    client = get_supabase()
    summary: dict[str, Any] = {
        "profile": False,
        "jobs": 0,
        "matches": 0,
        "customized": 0,
        "applications": 0,
    }

    profiles = (
        client.table("candidate_profiles")
        .select("*")
        .eq("user_id", user_id)
        .order("updated_at", desc=True)
        .limit(1)
        .execute()
    )
    profile_row = (profiles.data or [None])[0]
    if profile_row:
        data = profile_row.get("data") or {}
        data["id"] = profile_row["id"]
        data["source"] = profile_row.get("source") or data.get("source") or "llm"
        profile = CandidateProfile.model_validate(data)
        workspace.candidate_id = profile.id
        workspace.profile = profile
        summary["profile"] = True

        master_id = profile_row.get("master_document_id")
        if master_id:
            docs = (
                client.table("master_documents")
                .select("*")
                .eq("id", master_id)
                .limit(1)
                .execute()
            )
            doc_row = (docs.data or [None])[0]
            if doc_row:
                workspace.master_document_id = doc_row["id"]
                workspace.master_document = DocumentContent(
                    filename=doc_row["filename"],
                    content_type=doc_row["content_type"],
                    extension=doc_row["extension"],
                    text=doc_row.get("extracted_text") or "",
                    pages=doc_row.get("pages"),
                    characters=doc_row.get("characters") or 0,
                    extraction_method=doc_row.get("extraction_method") or "unknown",
                    has_text=bool(doc_row.get("extracted_text")),
                )

    jobs = (
        client.table("job_profiles")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=False)
        .execute()
    )
    for row in jobs.data or []:
        data = row.get("data") or {}
        data["id"] = row["id"]
        data["title"] = row.get("title") or data.get("title")
        data["company"] = row.get("company") or data.get("company")
        data["url"] = row.get("url") or data.get("url")
        data["source"] = row.get("source") or data.get("source") or "manual"
        job = JobProfile.model_validate(data)
        workspace.jobs[job.id] = job
        summary["jobs"] += 1

    if workspace.profile:
        matches = (
            client.table("job_matches")
            .select("*")
            .eq("user_id", user_id)
            .eq("candidate_id", workspace.profile.id)
            .execute()
        )
        for row in matches.data or []:
            data = row.get("data") or {}
            data["job_id"] = row["job_id"]
            data["candidate_id"] = row["candidate_id"]
            data["score"] = row.get("score", data.get("score", 0))
            match = JobMatch.model_validate(data)
            workspace.matches[match.job_id] = match
            summary["matches"] += 1

        customs = (
            client.table("customized_cvs")
            .select("*")
            .eq("user_id", user_id)
            .eq("candidate_id", workspace.profile.id)
            .execute()
        )
        for row in customs.data or []:
            data = row.get("data") or {}
            data["id"] = row["id"]
            data["job_id"] = row["job_id"]
            data["candidate_id"] = row["candidate_id"]
            customized = CustomizedCV.model_validate(data)
            workspace.customized[customized.id] = customized
            summary["customized"] += 1

    apps = (
        client.table("applications")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=False)
        .execute()
    )
    from datetime import datetime, timezone

    from app.api.routes import applications as applications_route
    from app.schemas.application import ApplicationProviderName

    for row in apps.data or []:
        try:
            status = ApplicationStatus(row["status"])
        except Exception:
            status = ApplicationStatus.REVIEW_REQUIRED
        provider = None
        if row.get("provider"):
            try:
                provider = ApplicationProviderName(row["provider"])
            except Exception:
                provider = None
        created = row.get("created_at")
        updated = row.get("updated_at")
        submitted = row.get("submitted_at")

        def _parse_dt(value):
            if not value:
                return None
            if isinstance(value, str):
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            return value

        application = Application(
            id=row["id"],
            candidate_id=row["candidate_id"],
            job_id=row["job_id"],
            customized_cv_id=row["customized_cv_id"],
            company=row["company"],
            position=row["position"],
            job_url=row.get("job_url"),
            match_percent=row.get("match_percent"),
            status=status,
            provider=provider,
            notes=row.get("notes"),
            error_message=row.get("error_message"),
            created_at=_parse_dt(created) or datetime.now(timezone.utc),
            updated_at=_parse_dt(updated) or datetime.now(timezone.utc),
            submitted_at=_parse_dt(submitted),
        )
        applications_route.service.store.upsert(application)
        summary["applications"] += 1

    return summary


def bootstrap_persistence() -> dict[str, Any]:
    if not persistence_enabled():
        return {"enabled": False, "reason": "missing_env"}

    try:
        get_supabase()
    except SupabaseNotConfiguredError as exc:
        return {"enabled": False, "reason": str(exc)}

    user_id = ensure_agent_user_id()
    if not user_id:
        return {
            "enabled": False,
            "reason": "missing_AGENT_USER_ID_or_bootstrap",
        }

    try:
        summary = load_workspace(user_id)
        return {"enabled": True, "user_id": user_id, "loaded": summary}
    except Exception as exc:
        logger.exception("Error cargando workspace desde Supabase")
        return {"enabled": True, "user_id": user_id, "error": str(exc)}
