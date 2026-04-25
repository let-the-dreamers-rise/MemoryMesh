from __future__ import annotations

import json
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path


@dataclass(slots=True)
class ExtractedDocument:
    title: str
    text: str
    source_type: str
    tags: list[str]


def detect_source_type(filename: str, content_type: str | None = None) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        return "pdf"
    if suffix in {".png", ".jpg", ".jpeg"}:
        return "screenshot"
    if suffix in {".json", ".html", ".htm", ".url"} or "bookmark" in filename.lower():
        return "bookmark"
    if content_type and content_type.startswith("image/"):
        return "screenshot"
    return "note"


def extract_document(filename: str, content: bytes, content_type: str | None = None) -> ExtractedDocument:
    source_type = detect_source_type(filename, content_type)
    title = Path(filename).stem.replace("_", " ").replace("-", " ").strip() or "Untitled upload"

    if source_type == "pdf":
        text = _extract_pdf(content)
    elif source_type == "screenshot":
        text = _extract_image(content)
    elif source_type == "bookmark":
        text = _extract_bookmarks(content)
    else:
        text = _decode_text(content)

    tags = [source_type]
    return ExtractedDocument(title=title, text=text, source_type=source_type, tags=tags)


def _decode_text(content: bytes) -> str:
    for encoding in ("utf-8", "utf-16", "latin-1"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="ignore")


def _extract_pdf(content: bytes) -> str:
    try:
        from pypdf import PdfReader

        reader = PdfReader(BytesIO(content))
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n\n".join(page.strip() for page in pages if page.strip())
        return text or "PDF uploaded, but no extractable text was found."
    except Exception as exc:
        return f"PDF uploaded. Text extraction was unavailable: {exc}"


def _extract_image(content: bytes) -> str:
    try:
        from PIL import Image
        import pytesseract

        image = Image.open(BytesIO(content))
        text = pytesseract.image_to_string(image)
        return text.strip() or "Screenshot uploaded, but OCR found no readable text."
    except Exception as exc:
        return (
            "Screenshot uploaded. OCR is optional for local setup and was unavailable. "
            f"Install Tesseract to extract screenshot text. Details: {exc}"
        )


def _extract_bookmarks(content: bytes) -> str:
    raw = _decode_text(content)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return raw

    rows: list[str] = []

    def walk(value: object) -> None:
        if isinstance(value, dict):
            title = str(value.get("title") or value.get("name") or "").strip()
            url = str(value.get("url") or value.get("href") or "").strip()
            note = str(value.get("description") or value.get("note") or value.get("text") or "").strip()
            if title or url or note:
                rows.append(" | ".join(part for part in (title, url, note) if part))
            for child in value.values():
                if isinstance(child, (list, dict)):
                    walk(child)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(data)
    return "\n".join(rows) if rows else raw

