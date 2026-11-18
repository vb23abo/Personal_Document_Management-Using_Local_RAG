"""Live checks against OpenSearch and Ollama.

Skipped unless LIVE_SMOKE=1. These are the acceptance checks that need the
local services from ``docker compose up -d`` and a running Ollama daemon.
"""

import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("LIVE_SMOKE") != "1",
    reason="Set LIVE_SMOKE=1 to run against local OpenSearch and Ollama",
)

TOKEN = "milu-rag-alpha"


def _write_pdf(path: Path, sentence: str) -> None:
    stream = f"BT /F1 12 Tf 72 720 Td ({sentence}) Tj ET".encode("latin-1")
    objects = [
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        (
            b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
        ),
        (
            f"4 0 obj\n<< /Length {len(stream)} >>\nstream\n".encode("latin-1")
            + stream
            + b"\nendstream\nendobj\n"
        ),
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
    ]
    header = b"%PDF-1.4\n"
    body = b""
    offsets = [0]
    for obj in objects:
        offsets.append(len(header) + len(body))
        body += obj
    xref_at = len(header) + len(body)
    xref = [f"xref\n0 {len(offsets)}\n", "0000000000 65535 f \n"]
    xref.extend(f"{offset:010d} 00000 n \n" for offset in offsets[1:])
    trailer = (
        f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\n"
        f"startxref\n{xref_at}\n%%EOF\n"
    )
    path.write_bytes(header + body + "".join(xref).encode("ascii") + trailer.encode("ascii"))


def test_index_search_answer_and_delete(tmp_path: Path) -> None:
    from src.chat import check_ollama_healthy, generate_response_streaming, ollama_chunk_text
    from src.constants import TEXT_CHUNK_OVERLAP, TEXT_CHUNK_SIZE
    from src.embeddings import generate_embeddings
    from src.extract import extract_text
    from src.ingestion import (
        bulk_index_documents,
        create_index,
        delete_documents_by_document_name,
    )
    from src.opensearch import get_opensearch_client, get_opensearch_status
    from src.utils import chunk_text

    reachable, _index_ready = get_opensearch_status()
    assert reachable, "OpenSearch is not reachable on localhost:9200"
    assert check_ollama_healthy(), "Ollama is not reachable"

    client = get_opensearch_client()
    create_index(client)

    pdf_path = tmp_path / "milu-note.pdf"
    sentence = (
        f"The secret token is {TOKEN}. "
        "It appears only in this personal note about local document search."
    )
    _write_pdf(pdf_path, sentence)

    text = extract_text(str(pdf_path))
    assert TOKEN in text
    chunks = chunk_text(text, chunk_size=TEXT_CHUNK_SIZE, overlap=TEXT_CHUNK_OVERLAP)
    assert chunks
    vectors = generate_embeddings(chunks)
    name = pdf_path.name
    success, errors = bulk_index_documents(
        [
            {
                "doc_id": f"{name}_{i}",
                "text": chunk,
                "embedding": vector,
                "document_name": name,
            }
            for i, (chunk, vector) in enumerate(zip(chunks, vectors))
        ]
    )
    assert success >= 1 and not errors

    listed = client.search(
        index="documents",
        body={
            "size": 0,
            "aggs": {"unique_docs": {"terms": {"field": "document_name", "size": 100}}},
        },
    )
    buckets = {
        bucket["key"]: bucket["doc_count"]
        for bucket in listed["aggregations"]["unique_docs"]["buckets"]
    }
    assert buckets.get(name, 0) >= 1

    result = generate_response_streaming(
        f"What is the secret token? Reply with {TOKEN} if the note says so.",
        use_hybrid_search=True,
        num_results=3,
        temperature=0.0,
        chat_history=[],
    )
    assert result.stream is not None
    assert any(cite["document_name"] == name for cite in result.citations)
    answer = ""
    for chunk in result.stream:
        answer += ollama_chunk_text(chunk)
    assert answer.strip()

    delete_documents_by_document_name(name)
    after = client.search(
        index="documents",
        body={"query": {"term": {"document_name": name}}},
    )
    assert after["hits"]["total"]["value"] == 0
