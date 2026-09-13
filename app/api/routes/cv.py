from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.ai.structured import StructuredOutputError
from app.services.cv_format import render_cleaned_cv
from app.services.document.document_extractor import (
    DocumentExtractorError,
    extract_document,
)
from app.services.persistence import (
    ensure_agent_user_id,
    persistence_enabled,
    save_candidate_profile,
    save_master_cv,
)
from app.services.workspace import workspace


router = APIRouter()


def _document_payload(document) -> dict:
    return {
        "filename": document.filename,
        "content_type": document.content_type,
        "extension": document.extension,
        "pages": document.pages,
        "characters": document.characters,
        "extraction_method": document.extraction_method,
        "has_text": document.has_text,
    }


def _persist_profile(document, file_bytes: bytes | None, profile) -> str | None:
    if not persistence_enabled():
        return None
    user_id = ensure_agent_user_id()
    if not user_id:
        return "missing_user"
    try:
        doc_id = save_master_cv(
            user_id=user_id,
            document=document,
            file_bytes=file_bytes,
            document_id=workspace.master_document_id,
        )
        workspace.master_document_id = doc_id
        profile_id = save_candidate_profile(
            user_id=user_id,
            profile=profile,
            master_document_id=doc_id,
        )
        workspace.candidate_id = profile_id
        profile.id = profile_id
        workspace.profile = profile
        return "saved"
    except Exception as exc:
        return f"error:{exc}"


@router.post("/cv/upload")
async def upload_cv(file: UploadFile = File(...)):
    file_bytes = await file.read()

    try:
        document = extract_document(file, file_bytes)
    except DocumentExtractorError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    if not document.has_text:
        raise HTTPException(
            status_code=400,
            detail="El archivo no contiene texto utilizable.",
        )

    document_id = workspace.save_master_document(document)

    from app.services.ai.cv_analyzer import analyze_cv_text

    try:
        profile = analyze_cv_text(
            document.text,
            workspace.candidate_id,
        )
    except StructuredOutputError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    workspace.set_profile(profile)
    persist_status = _persist_profile(document, file_bytes, workspace.profile)

    return {
        "status": "success",
        "document_id": workspace.master_document_id or document_id,
        "document": _document_payload(document),
        "profile": workspace.profile.model_dump(mode="json"),
        "cleaned_cv": render_cleaned_cv(workspace.profile),
        "persisted": persist_status == "saved",
        "persist_status": persist_status,
    }


@router.post("/cv/analyze")
def analyze_cv():
    if workspace.master_document is None:
        raise HTTPException(
            status_code=400,
            detail="Primero debes subir un CV maestro.",
        )

    from app.services.ai.cv_analyzer import analyze_cv_text

    try:
        profile = analyze_cv_text(
            workspace.master_document.text,
            workspace.candidate_id,
        )
    except StructuredOutputError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    workspace.set_profile(profile)
    persist_status = _persist_profile(workspace.master_document, None, workspace.profile)
    return {
        "status": "success",
        "profile": workspace.profile.model_dump(mode="json"),
        "cleaned_cv": render_cleaned_cv(workspace.profile),
        "persisted": persist_status == "saved",
        "persist_status": persist_status,
    }
