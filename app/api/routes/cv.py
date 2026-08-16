from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.ai.structured import StructuredOutputError
from app.services.document.pdf_parser import (
    PDFParserError,
    extract_pdf,
)
from app.services.workspace import workspace


router = APIRouter()


@router.post("/cv/upload")
async def upload_cv(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Solo se permiten archivos PDF."
        )

    file_bytes = await file.read()

    try:
        document = extract_pdf(
            file_bytes=file_bytes,
            filename=file.filename or "upload.pdf",
            content_type=file.content_type,
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
    }
