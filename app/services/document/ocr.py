import os
import shutil
from pathlib import Path

import pymupdf

OCR_LANGUAGES = "spa+eng"
TESSDATA_DIR = Path(__file__).resolve().parents[3] / "tessdata"
WINDOWS_TESSERACT = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
LINUX_TESSDATA_CANDIDATES = (
    Path("/usr/share/tesseract-ocr/5/tessdata"),
    Path("/usr/share/tesseract-ocr/4.00/tessdata"),
    Path("/usr/share/tessdata"),
)


def _tesseract_path() -> str | None:
    found = shutil.which("tesseract")
    if found:
        return found
    if WINDOWS_TESSERACT.exists():
        return str(WINDOWS_TESSERACT)
    return None


def _has_lang_data(directory: Path) -> bool:
    return (directory / "eng.traineddata").exists() and (
        directory / "spa.traineddata"
    ).exists()


def _tessdata_path() -> str | None:
    if _has_lang_data(TESSDATA_DIR):
        return str(TESSDATA_DIR)

    program_files = Path(r"C:\Program Files\Tesseract-OCR\tessdata")
    if (program_files / "eng.traineddata").exists():
        return str(program_files)

    for candidate in LINUX_TESSDATA_CANDIDATES:
        if _has_lang_data(candidate):
            return str(candidate)

    prefix = os.environ.get("TESSDATA_PREFIX")
    if prefix:
        prefix_path = Path(prefix)
        if _has_lang_data(prefix_path):
            return str(prefix_path)
        if prefix_path.exists() and (prefix_path / "eng.traineddata").exists():
            return str(prefix_path)

    return None


def ocr_available() -> bool:
    return _tesseract_path() is not None and _tessdata_path() is not None


def ocr_page_text(page: pymupdf.Page) -> str:
    tesseract = _tesseract_path()
    tessdata = _tessdata_path()

    if not tesseract or not tessdata:
        raise RuntimeError(
            "OCR no disponible: instala Tesseract (spa+eng) en el servidor."
        )

    tesseract_dir = str(Path(tesseract).parent)
    path_entries = os.environ.get("PATH", "").split(os.pathsep)
    if tesseract_dir not in path_entries:
        os.environ["PATH"] = tesseract_dir + os.pathsep + os.environ.get("PATH", "")

    os.environ["TESSDATA_PREFIX"] = tessdata

    try:
        textpage = page.get_textpage_ocr(
            language=OCR_LANGUAGES,
            full=True,
            tessdata=tessdata,
        )
        return page.get_text(textpage=textpage).strip()
    except Exception as exc:
        raise RuntimeError(
            "No se pudo leer el PDF escaneado con OCR."
        ) from exc
