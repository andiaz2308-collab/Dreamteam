from fastapi import UploadFile

from app.services.document.docx_parser import DOCXParserError, extract_docx
from app.services.document.document_types import DocumentContent
from app.services.document.pdf_parser import PDFParserError, extract_pdf


class DocumentExtractorError(Exception):
    pass


def _is_pdf(file: UploadFile, file_bytes: bytes) -> bool:
    filename = (file.filename or "").lower()
    content_type = (file.content_type or "").lower()
    if content_type in {"application/pdf", "application/x-pdf"}:
        return True
    if filename.endswith(".pdf"):
        return True
    return file_bytes.startswith(b"%PDF")


def _is_docx(file: UploadFile, file_bytes: bytes) -> bool:
    filename = (file.filename or "").lower()
    content_type = (file.content_type or "").lower()
    docx_types = {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    }
    if content_type in docx_types and filename.endswith(".docx"):
        return True
    if filename.endswith(".docx"):
        return True
    if file_bytes.startswith(b"PK") and filename.endswith(".docx"):
        return True
    return False


def extract_document(file: UploadFile, file_bytes: bytes) -> DocumentContent:
    if _is_pdf(file, file_bytes):
        try:
            return extract_pdf(
                file_bytes=file_bytes,
                filename=file.filename or "upload.pdf",
                content_type=file.content_type or "application/pdf",
            )
        except PDFParserError as exc:
            raise DocumentExtractorError(str(exc)) from exc

    if _is_docx(file, file_bytes):
        try:
            return extract_docx(
                file_bytes=file_bytes,
                filename=file.filename or "upload.docx",
                content_type=file.content_type
                or "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        except DOCXParserError as exc:
            raise DocumentExtractorError(str(exc)) from exc

    filename = (file.filename or "").lower()
    if filename.endswith(".doc"):
        raise DocumentExtractorError(
            "Los archivos .doc antiguos no son compatibles. Guarda el CV como .docx o PDF."
        )

    raise DocumentExtractorError(
        "Formato no soportado. Sube un PDF o DOCX con texto legible."
    )
