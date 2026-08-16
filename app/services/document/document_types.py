from dataclasses import dataclass


@dataclass
class DocumentContent:
    filename: str
    content_type: str
    extension: str
    text: str
    pages: int | None
    characters: int
    extraction_method: str
    has_text: bool
