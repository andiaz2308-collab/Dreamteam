from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.ai.structured import StructuredOutputError
from app.services.cv_format import render_cleaned_cv
from app.services.document.pdf_parser import (
    PDFParserError,
    extract_pdf,
)
from app.services.workspace import workspace


router = APIRouter()


def _is_pdf(file: UploadFile, file_bytes: bytes) -> bool:
    filename = (file.filename or "").lower()
    content_type = (file.content_type or "").lower()
    if content_type in {"application/pdf", "application/x-pdf"}:
        return True
    if filename.endswith(".pdf"):
        return True
    return file_bytes.startswith(b"%PDF")


@router.post("/cv/upload")
async def upload_cv(file: UploadFile = File(...)):
    file_bytes = await file.read()

    if not _is_pdf(file, file_bytes):
        raise HTTPException(
            status_code=400,
            detail="Solo se permiten archivos PDF."
        )

    try:
        document = extract_pdf(
            file_bytes=file_bytes,
            filename=file.filename or "upload.pdf",
            content_type=file.content_type or "application/pdf",
        )
    except PDFParserError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        ) from exc

    if not document.has_text:
        raise HTTPException(
            status_code=400,
            detail="El PDF no contiene texto utilizable."
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
        "document": {
            "filename": document.filename,
            "content_type": document.content_type,
            "extension": document.extension,
            "pages": document.pages,
            "characters": document.characters,
            "extraction_method": document.extraction_method,
            "has_text": document.has_text,
        },
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
