from src.ingestion import bulk_index_documents
from src.opensearch import SEARCH_PIPELINE_NAME, hybrid_search


def test_bulk_index_reports_soft_failures(monkeypatch) -> None:
    captured = {}

    def fake_bulk(client, actions, raise_on_error=True, refresh=False):
        captured["client"] = client
        captured["actions"] = actions
        captured["raise_on_error"] = raise_on_error
        captured["refresh"] = refresh
        return 0, [{"index": {"error": "rejected"}}]

    monkeypatch.setattr("src.ingestion.get_opensearch_client", lambda: "client")
    monkeypatch.setattr("src.ingestion.helpers.bulk", fake_bulk)

    success, errors = bulk_index_documents(
        [
            {
                "doc_id": "a.pdf_0",
                "text": "hello",
                "embedding": [0.1, 0.2],
                "document_name": "a.pdf",
            }
        ]
    )

    assert success == 0
    assert errors == [{"index": {"error": "rejected"}}]
    assert captured["raise_on_error"] is False
    assert captured["refresh"] == "wait_for"
    assert captured["actions"][0]["_id"] == "a.pdf_0"
    assert captured["actions"][0]["_source"]["text"] == "hello"


def test_hybrid_search_uses_pipeline_and_returns_hits(monkeypatch) -> None:
    captured = {}

    class Client:
        def search(self, index, body, search_pipeline):
            captured["index"] = index
            captured["body"] = body
            captured["pipeline"] = search_pipeline
            return {
                "hits": {
                    "hits": [
                        {
                            "_score": 0.5,
                            "_source": {"text": "sea level", "document_name": "a.pdf"},
                        }
                    ]
                }
            }

    monkeypatch.setattr("src.opensearch.get_opensearch_client", lambda: Client())
    hits = hybrid_search("sea level", [0.1, 0.2], top_k=3)

    assert hits[0]["_score"] == 0.5
    assert captured["pipeline"] == SEARCH_PIPELINE_NAME
    assert captured["body"]["size"] == 3
    queries = captured["body"]["query"]["hybrid"]["queries"]
    assert queries[0]["match"]["text"]["query"] == "sea level"
    assert queries[1]["knn"]["embedding"]["k"] == 3
