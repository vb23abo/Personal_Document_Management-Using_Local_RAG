"""Read uploaded files into plain text."""

from pathlib import Path

from src.utils import clean_text

SUPPORTED_EXTENSIONS = ("pdf", "docx", "txt", "md", "markdown")


def extract_text(file_path: str) -> str:
    """Extract text from a PDF, DOCX, TXT, or Markdown file."""
    suffix = Path(file_path).suffix.lower()
    if suffix == ".pdf":
        from src.ocr import extract_text_from_pdf

        return extract_text_from_pdf(file_path)
    if suffix == ".docx":
        return _extract_docx(file_path)
    if suffix in {".txt", ".md", ".markdown"}:
        raw = Path(file_path).read_text(encoding="utf-8", errors="replace")
        return clean_text(raw)
    raise ValueError(f"Unsupported file type: {suffix or 'unknown'}")


def _extract_docx(file_path: str) -> str:
    from docx import Document

    document = Document(file_path)
    parts = []
    for paragraph in document.paragraphs:
        if paragraph.text and paragraph.text.strip():
            parts.append(paragraph.text)
    for table in document.tables:
        for row in table.rows:
            cells = [
                cell.text.strip()
                for cell in row.cells
                if cell.text and cell.text.strip()
            ]
            if cells:
                parts.append(" ".join(cells))
    return clean_text("\n".join(parts))
