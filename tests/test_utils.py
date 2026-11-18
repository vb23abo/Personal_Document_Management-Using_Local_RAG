import pytest

from src.utils import chunk_text, clean_text, sanitize_filename


def test_clean_text_joins_hyphenated_line_breaks() -> None:
    assert clean_text("exam-\nple  text") == "example text"


def test_chunk_text_overlap() -> None:
    words = [f"w{i}" for i in range(10)]
    chunks = chunk_text(" ".join(words), chunk_size=4, overlap=1)
    assert chunks == [
        "w0 w1 w2 w3",
        "w3 w4 w5 w6",
        "w6 w7 w8 w9",
    ]


def test_chunk_text_rejects_bad_sizes() -> None:
    with pytest.raises(ValueError):
        chunk_text("one two", chunk_size=0, overlap=0)
    with pytest.raises(ValueError):
        chunk_text("one two three", chunk_size=2, overlap=2)
    with pytest.raises(ValueError):
        chunk_text("one two three", chunk_size=2, overlap=-1)


def test_sanitize_filename_keeps_basename() -> None:
    assert sanitize_filename("../notes/report.pdf") == "report.pdf"
    assert sanitize_filename("report.pdf") == "report.pdf"


@pytest.mark.parametrize("name", ["", ".", "..", "folder/.."])
def test_sanitize_filename_rejects_empty_and_dot_names(name: str) -> None:
    with pytest.raises(ValueError):
        sanitize_filename(name)
