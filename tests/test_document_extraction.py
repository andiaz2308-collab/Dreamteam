from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from app.services.document.docx_parser import DOCXParserError, extract_docx
from app.services.document.document_extractor import (
    DocumentExtractorError,
    extract_document,
)
from app.services.document.pdf_parser import PDFParserError, extract_pdf


def _minimal_docx(paragraphs: list[str]) -> bytes:
    from docx import Document

    document = Document()
    for text in paragraphs:
        document.add_paragraph(text)

    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def test_extract_docx_reads_paragraphs():
    payload = _minimal_docx(
        [
            "Maria Lopez",
            "Ingeniera de software",
            "Python · FastAPI · PostgreSQL",
        ]
    )

    result = extract_docx(
        payload,
        filename="cv.docx",
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

    assert result.has_text is True
    assert result.extension == ".docx"
    assert result.extraction_method == "python-docx"
    assert "Maria Lopez" in result.text
    assert "FastAPI" in result.text


def test_extract_docx_rejects_empty_file():
    with pytest.raises(DOCXParserError, match="vacio"):
        extract_docx(b"", filename="cv.docx", content_type="application/octet-stream")


def test_extract_document_rejects_legacy_doc():
    upload = MagicMock()
    upload.filename = "cv.doc"
    upload.content_type = "application/msword"

    with pytest.raises(DocumentExtractorError, match="\\.doc antiguos"):
        extract_document(upload, b"not-a-real-doc")


def test_extract_document_rejects_unknown_format():
    upload = MagicMock()
    upload.filename = "cv.txt"
    upload.content_type = "text/plain"

    with pytest.raises(DocumentExtractorError, match="Formato no soportado"):
        extract_document(upload, b"hola mundo")


def test_extract_pdf_rejects_invalid_magic():
    with pytest.raises(PDFParserError, match="PDF valido"):
        extract_pdf(b"not-pdf", filename="cv.pdf", content_type="application/pdf")


@patch("app.services.document.pdf_parser.ocr_available", return_value=False)
def test_extract_pdf_scanned_without_tesseract_raises(_mock_ocr):
    import pymupdf

    document = pymupdf.open()
    document.new_page(width=300, height=300)
    payload = document.tobytes()
    document.close()

    with pytest.raises(PDFParserError, match="escaneado"):
        extract_pdf(payload, filename="scan.pdf", content_type="application/pdf")
