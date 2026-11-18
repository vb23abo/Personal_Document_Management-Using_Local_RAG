from src.chat import (
    citations_from_hits,
    commit_chat_turn,
    generate_response_streaming,
)


def test_citations_include_name_snippet_and_score() -> None:
    text = "a" * 250
    context, citations = citations_from_hits(
        [
            {
                "_source": {"text": text, "document_name": "notes.pdf"},
                "_score": 0.42,
            }
        ]
    )
    assert citations[0]["document_name"] == "notes.pdf"
    assert citations[0]["score"] == 0.42
    assert citations[0]["snippet"] == ("a" * 240) + "…"
    assert "notes.pdf" in context
    assert text in context


def test_failed_turn_is_not_stored() -> None:
    history = [{"role": "user", "content": "What is this?"}]
    assert commit_chat_turn(history, "What is this?", None, []) == []
    assert commit_chat_turn(history, "What is this?", "   ", []) == []


def test_completed_turn_keeps_answer_and_citations() -> None:
    history = [{"role": "user", "content": "What is this?"}]
    citations = [{"document_name": "a.pdf", "snippet": "hello", "score": 1.0}]
    updated = commit_chat_turn(history, "What is this?", "An answer", citations)
    assert updated[-1]["role"] == "assistant"
    assert updated[-1]["content"] == "An answer"
    assert updated[-1]["citations"] == citations


def test_rag_off_does_not_search(monkeypatch) -> None:
    def fail_search(*_args, **_kwargs):
        raise AssertionError("hybrid search should not run when RAG is off")

    monkeypatch.setattr("src.chat.hybrid_search", fail_search)
    monkeypatch.setattr(
        "src.chat.run_llama_streaming",
        lambda prompt, temperature: iter(()),
    )
    result = generate_response_streaming(
        "hello",
        use_hybrid_search=False,
        num_results=5,
        temperature=0.2,
        chat_history=[{"role": "user", "content": "hello"}],
    )
    assert result.citations == []
    assert result.stream is not None


def test_produce_chat_chunks_stops_before_text(monkeypatch) -> None:
    import queue
    import threading
    import types

    fake = types.ModuleType("ollama")

    def chat(**_kwargs):
        return [
            {"message": {"content": "Hello"}},
            {"message": {"content": " world"}},
        ]

    fake.chat = chat
    monkeypatch.setitem(__import__("sys").modules, "ollama", fake)
    stop = threading.Event()
    stop.set()
    out: queue.Queue = queue.Queue()
    from src.chat import produce_chat_chunks

    produce_chat_chunks("prompt", 0.2, stop, out)
    assert out.get(timeout=2) is None
    assert out.empty()


def test_failed_stream_does_not_become_an_assistant_message(monkeypatch) -> None:
    monkeypatch.setattr("src.chat.run_llama_streaming", lambda prompt, temperature: None)
    result = generate_response_streaming(
        "hello",
        use_hybrid_search=False,
        num_results=5,
        temperature=0.2,
        chat_history=[],
    )
    assert result.stream is None
    history = commit_chat_turn(
        [{"role": "user", "content": "hello"}],
        "hello",
        None,
        result.citations,
    )
    assert history == []
    assert all(message["role"] != "assistant" for message in history)
