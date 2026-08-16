import pymupdf

from app.services.document.document_types import DocumentContent
from app.services.document.text_cleaner import clean_text


MAX_FILE_SIZE = 5 * 1024 * 1024
MAX_PAGES = 10
MAX_TEXT_LENGTH = 50_000


class PDFParserError(Exception):
    pass


def extract_pdf(
    file_bytes: bytes,
    filename: str,
    content_type: str,
) -> DocumentContent:

    if not file_bytes:
        raise PDFParserError("El archivo esta vacio.")

    if len(file_bytes) > MAX_FILE_SIZE:
        raise PDFParserError("El PDF supera el limite de 5 MB.")

    if not file_bytes.startswith(b"%PDF"):
        raise PDFParserError("El archivo no parece ser un PDF valido.")

    try:
        document = pymupdf.open(
            stream=file_bytes,
            filetype="pdf",
        )
    except Exception as exc:
        raise PDFParserError("No se pudo abrir el PDF.") from exc

    try:
        if document.page_count > MAX_PAGES:
            raise PDFParserError(
                f"El PDF supera el limite de {MAX_PAGES} paginas."
            )

        raw_pages = []

        for page in document:
            text = page.get_text("text")

            if text:
                raw_pages.append(text)

        raw_text = "\n\n".join(raw_pages)

        cleaned_text = clean_text(raw_text)

        if len(cleaned_text) > MAX_TEXT_LENGTH:
            raise PDFParserError(
                "El texto extraido supera el limite permitido."
            )

        return DocumentContent(
            filename=filename,
            content_type=content_type,
            extension=".pdf",
            text=cleaned_text,
            pages=document.page_count,
            characters=len(cleaned_text),
            extraction_method="pymupdf",
            has_text=bool(cleaned_text),
        )

    finally:
        document.close()
