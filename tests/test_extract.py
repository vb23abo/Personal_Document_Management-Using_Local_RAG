from pathlib import Path

from src.extract import extract_text


def test_extract_text_reads_txt_and_markdown(tmp_path: Path) -> None:
    note = tmp_path / "note.txt"
    note.write_text("hello   world\n", encoding="utf-8")
    assert extract_text(str(note)) == "hello world"

    doc = tmp_path / "note.md"
    doc.write_text("alpha\n\nbeta", encoding="utf-8")
    assert "alpha" in extract_text(str(doc))
    assert "beta" in extract_text(str(doc))


def test_extract_text_rejects_unknown_suffix(tmp_path: Path) -> None:
    other = tmp_path / "data.csv"
    other.write_text("a,b", encoding="utf-8")
    try:
        extract_text(str(other))
    except ValueError as exc:
        assert "Unsupported" in str(exc)
    else:
        raise AssertionError("csv should be rejected")
