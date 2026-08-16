import fitz


MAX_FILE_SIZE = 5 * 1024 * 1024
MAX_PAGES = 10
MAX_TEXT_LENGTH = 50_000


class PDFParserError(Exception):
    pass


def extract_text_from_pdf(file_bytes: bytes) -> dict:
    if not file_bytes:
        raise PDFParserError("El archivo esta vacio.")

    if len(file_bytes) > MAX_FILE_SIZE:
        raise PDFParserError("El PDF supera el limite de 5 MB.")

    if not file_bytes.startswith(b"%PDF"):
        raise PDFParserError("El archivo no parece ser un PDF valido.")

    try:
        document = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as exc:
        raise PDFParserError("No se pudo abrir el PDF.") from exc

    try:
        if document.page_count > MAX_PAGES:
            raise PDFParserError(
                f"El PDF supera el limite de {MAX_PAGES} paginas."
            )

        pages = []
        total_chars = 0

        for page_number, page in enumerate(document):
            text = page.get_text("text")

            if text:
                text = text.strip()
                pages.append({
                    "page": page_number + 1,
                    "text": text,
                })
                total_chars += len(text)

            if total_chars > MAX_TEXT_LENGTH:
                raise PDFParserError(
                    "El texto extraido supera el limite permitido."
                )

        full_text = "\n\n".join(
            page["text"] for page in pages
        )

        return {
            "pages": document.page_count,
            "text": full_text,
            "characters": len(full_text),
            "has_text": bool(full_text.strip()),
        }

    finally:
        document.close()
