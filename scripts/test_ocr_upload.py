"""Genera un PDF escaneado de prueba y valida extracción OCR."""

from io import BytesIO

import pymupdf

from app.services.document.pdf_parser import extract_pdf


def build_scanned_pdf() -> bytes:
    source = pymupdf.open()
    page = source.new_page(width=500, height=180)
    page.insert_text(
        (40, 70),
        "Andreina Diaz Duran",
        fontsize=16,
    )
    page.insert_text(
        (40, 100),
        "Biologa marina · Investigacion ambiental",
        fontsize=12,
    )
    pixmap = page.get_pixmap(dpi=200)

    scanned = pymupdf.open()
    scan_page = scanned.new_page(width=pixmap.width, height=pixmap.height)
    scan_page.insert_image(scan_page.rect, pixmap=pixmap)
    payload = scanned.tobytes()
    scanned.close()
    source.close()
    return payload


def main() -> None:
    pdf_bytes = build_scanned_pdf()
    result = extract_pdf(
        pdf_bytes,
        filename="cv_escaneado_prueba.pdf",
        content_type="application/pdf",
    )

    print("extraction_method:", result.extraction_method)
    print("has_text:", result.has_text)
    print("characters:", result.characters)
    print("--- text ---")
    print(result.text)
    print("---")

    assert result.has_text, "No se extrajo texto"
    assert "ocr" in result.extraction_method, "No se uso OCR"
    assert "Andreina" in result.text or "Diaz" in result.text or "Biolog" in result.text, (
        "El OCR no reconocio el contenido esperado"
    )
    print("OK: OCR funcionando")


if __name__ == "__main__":
    main()
