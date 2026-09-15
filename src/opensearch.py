import logging
from typing import Any, Dict, List

from opensearchpy import OpenSearch

from src.constants import OPENSEARCH_HOST, OPENSEARCH_INDEX, OPENSEARCH_PORT
from src.utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

SEARCH_PIPELINE_NAME = "nlp-search-pipeline"

SEARCH_PIPELINE_BODY: Dict[str, Any] = {
    "description": "Post processor for hybrid search",
    "phase_results_processors": [
        {
            "normalization-processor": {
                "normalization": {"technique": "min_max"},
                "combination": {
                    "technique": "arithmetic_mean",
                    "parameters": {"weights": [0.3, 0.7]},
                },
            }
        }
    ],
}


def get_opensearch_client() -> OpenSearch:
    """Initializes and returns an OpenSearch client."""
    client = OpenSearch(
        hosts=[{"host": OPENSEARCH_HOST, "port": OPENSEARCH_PORT}],
        http_compress=True,
        timeout=30,
        max_retries=3,
        retry_on_timeout=True,
    )
    logger.info("OpenSearch client initialized.")
    return client


def check_opensearch_healthy() -> bool:
    """Returns True if OpenSearch responds to ping."""
    try:
        client = get_opensearch_client()
        return bool(client.ping())
    except Exception as e:
        logger.warning("OpenSearch health check failed: %s", e)
        return False


def ensure_search_pipeline(client: OpenSearch) -> None:
    """Creates the hybrid search pipeline if it does not already exist."""
    pipeline_path = f"/_search/pipeline/{SEARCH_PIPELINE_NAME}"
    try:
        client.transport.perform_request("GET", pipeline_path)
        logger.info("Search pipeline '%s' already exists.", SEARCH_PIPELINE_NAME)
        return
    except Exception:
        logger.info(
            "Search pipeline '%s' not found; creating it.", SEARCH_PIPELINE_NAME
        )

    client.transport.perform_request("PUT", pipeline_path, body=SEARCH_PIPELINE_BODY)
    logger.info("Created search pipeline '%s'.", SEARCH_PIPELINE_NAME)


def hybrid_search(
    query_text: str, query_embedding: List[float], top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Performs a hybrid search combining text-based and vector-based queries.
    """
    client = get_opensearch_client()

    query_body = {
        "_source": {"exclude": ["embedding"]},
        "query": {
            "hybrid": {
                "queries": [
                    {"match": {"text": {"query": query_text}}},
                    {
                        "knn": {
                            "embedding": {
                                "vector": query_embedding,
                                "k": top_k,
                            }
                        }
                    },
                ]
            }
        },
        "size": top_k,
    }

    try:
        response = client.search(
            index=OPENSEARCH_INDEX,
            body=query_body,
            search_pipeline=SEARCH_PIPELINE_NAME,
        )
        logger.info(
            "Hybrid search completed for query '%s' with top_k=%s.",
            query_text,
            top_k,
        )
        hits: List[Dict[str, Any]] = response["hits"]["hits"]
        return hits
    except Exception as e:
        logger.error("Hybrid search failed: %s", e)
        raise
