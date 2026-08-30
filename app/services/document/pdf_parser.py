import pymupdf

from app.services.document.document_types import DocumentContent
from app.services.document.limits import (
    MAX_FILE_SIZE,
    MAX_PAGES,
    MAX_TEXT_LENGTH,
    MIN_PAGE_CHARS,
)
from app.services.document.ocr import ocr_available, ocr_page_text
from app.services.document.text_cleaner import clean_text


class PDFParserError(Exception):
    pass


def _extract_page_text(page: pymupdf.Page) -> tuple[str, str]:
    native_text = page.get_text("text").strip()
    if len(native_text) >= MIN_PAGE_CHARS:
        return native_text, "pymupdf"

    if not ocr_available():
        if native_text:
            return native_text, "pymupdf"
        raise PDFParserError(
            "El PDF parece escaneado y no tiene texto seleccionable. "
            "Instala Tesseract OCR (idiomas spa+eng) o sube un PDF con texto."
        )

    ocr_text = ocr_page_text(page)
    if ocr_text:
        return ocr_text, "pymupdf+ocr"

    if native_text:
        return native_text, "pymupdf"

    return "", "pymupdf+ocr"


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

        raw_pages: list[str] = []
        methods: set[str] = set()

        for page in document:
            text, method = _extract_page_text(page)
            methods.add(method)
            if text:
                raw_pages.append(text)

        raw_text = "\n\n".join(raw_pages)
        cleaned_text = clean_text(raw_text)

        if len(cleaned_text) > MAX_TEXT_LENGTH:
            raise PDFParserError(
                "El texto extraido supera el limite permitido."
            )

        if "pymupdf+ocr" in methods:
            extraction_method = "pymupdf+ocr" if methods == {"pymupdf+ocr"} else "pymupdf+ocr-mixed"
        else:
            extraction_method = "pymupdf"

        return DocumentContent(
            filename=filename,
            content_type=content_type,
            extension=".pdf",
            text=cleaned_text,
            pages=document.page_count,
            characters=len(cleaned_text),
            extraction_method=extraction_method,
            has_text=bool(cleaned_text),
        )

    finally:
        document.close()
