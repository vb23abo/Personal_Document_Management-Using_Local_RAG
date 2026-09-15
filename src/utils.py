# src/utils.py

import logging
import re
from pathlib import Path
from typing import List

from src.constants import LOG_FILE_PATH


def setup_logging() -> None:
    """
    Configures logging settings for the application, specifying log file, format, and level.
    """
    Path(LOG_FILE_PATH).parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=LOG_FILE_PATH,
        filemode="a",
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )


def sanitize_filename(filename: str) -> str:
    """Return a safe basename (no path components) for uploaded files."""
    return Path(filename).name


def clean_text(text: str) -> str:
    """
    Cleans OCR-extracted text by removing unnecessary newlines, hyphens, and correcting common OCR errors.

    Args:
        text (str): The text to clean.

    Returns:
        str: The cleaned text.
    """
    # Remove hyphens at line breaks (e.g., 'exam-\nple' -> 'example')
    text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)

    # Replace newlines within sentences with spaces
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)

    # Replace multiple newlines with a single newline
    text = re.sub(r"\n+", "\n", text)

    # Remove excessive whitespace
    text = re.sub(r"[ \t]+", " ", text)

    cleaned_text = text.strip()
    logging.info("Text cleaned.")
    return cleaned_text


def chunk_text(text: str, chunk_size: int, overlap: int = 100) -> List[str]:
    """
    Splits text into word-based chunks with a specified overlap.

    Args:
        text (str): The text to split.
        chunk_size (int): The number of words in each chunk.
        overlap (int): The number of words to overlap between chunks.

    Returns:
        List[str]: A list of text chunks.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must satisfy 0 <= overlap < chunk_size")

    text = clean_text(text)
    logging.info("Text prepared for chunking.")

    tokens = text.split(" ")
    if not tokens or tokens == [""]:
        return []

    chunks = []
    start = 0
    while start < len(tokens):
        end = start + chunk_size
        chunk_tokens = tokens[start:end]
        chunks.append(" ".join(chunk_tokens))
        if end >= len(tokens):
            break
        start = end - overlap

    logging.info(
        "Text split into %s chunks with chunk size %s and overlap %s.",
        len(chunks),
        chunk_size,
        overlap,
    )
    return chunks
