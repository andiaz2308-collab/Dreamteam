from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.ai.structured import StructuredOutputError
from app.services.cv_format import render_cleaned_cv
from app.services.document.document_extractor import (
    DocumentExtractorError,
    extract_document,
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

    return {
        "status": "success",
        "document_id": document_id,
        "document": _document_payload(document),
        "profile": profile.model_dump(mode="json"),
        "cleaned_cv": render_cleaned_cv(profile),
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
    return {
        "status": "success",
        "profile": profile.model_dump(mode="json"),
        "cleaned_cv": render_cleaned_cv(profile),
    }
