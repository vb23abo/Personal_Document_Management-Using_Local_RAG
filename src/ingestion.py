import json
import logging
from typing import Any, Dict, List, Tuple

from opensearchpy import OpenSearch, helpers

from src.constants import EMBEDDING_DIMENSION, INDEX_CONFIG_PATH, OPENSEARCH_INDEX
from src.opensearch import ensure_search_pipeline, get_opensearch_client
from src.utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


def load_index_config() -> Dict[str, Any]:
    """
    Loads the index configuration from a JSON file next to this module.
    """
    with open(INDEX_CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

    config["mappings"]["properties"]["embedding"]["dimension"] = EMBEDDING_DIMENSION
    logger.info("Index configuration loaded from %s.", INDEX_CONFIG_PATH)
    return config if isinstance(config, dict) else {}


def create_index(client: OpenSearch) -> None:
    """
    Creates an index in OpenSearch using settings and mappings from the configuration file.
    Also ensures the hybrid search pipeline exists.
    """
    index_body = load_index_config()
    if not client.indices.exists(index=OPENSEARCH_INDEX):
        response = client.indices.create(index=OPENSEARCH_INDEX, body=index_body)
        logger.info("Created index %s: %s", OPENSEARCH_INDEX, response)
    else:
        logger.info("Index %s already exists.", OPENSEARCH_INDEX)
    ensure_search_pipeline(client)


def delete_index(client: OpenSearch) -> None:
    """Deletes the index in OpenSearch if it exists."""
    if client.indices.exists(index=OPENSEARCH_INDEX):
        response = client.indices.delete(index=OPENSEARCH_INDEX)
        logger.info("Deleted index %s: %s", OPENSEARCH_INDEX, response)
    else:
        logger.info("Index %s does not exist.", OPENSEARCH_INDEX)


def bulk_index_documents(documents: List[Dict[str, Any]]) -> Tuple[int, List[Any]]:
    """
    Indexes multiple documents into OpenSearch in bulk.

    Stores raw (unprefixed) text for BM25. Embeddings should already be computed
    with the correct passage/query convention by the caller.
    """
    if not documents:
        return 0, []

    actions = []
    client = get_opensearch_client()

    for doc in documents:
        embedding = doc["embedding"]
        embedding_list = (
            embedding.tolist() if hasattr(embedding, "tolist") else list(embedding)
        )
        action = {
            "_index": OPENSEARCH_INDEX,
            "_id": doc["doc_id"],
            "_source": {
                "text": doc["text"],
                "embedding": embedding_list,
                "document_name": doc["document_name"],
            },
        }
        actions.append(action)

    success, errors = helpers.bulk(client, actions, raise_on_error=False)
    error_list: List[Any] = errors if isinstance(errors, list) else []
    logger.info(
        "Bulk indexed %s documents into index %s with %s errors.",
        len(documents),
        OPENSEARCH_INDEX,
        len(error_list),
    )
    return success, error_list


def delete_documents_by_document_name(document_name: str) -> Dict[str, Any]:
    """Deletes documents from OpenSearch where 'document_name' matches."""
    client = get_opensearch_client()
    query = {"query": {"term": {"document_name": document_name}}}
    response: Dict[str, Any] = client.delete_by_query(
        index=OPENSEARCH_INDEX, body=query
    )
    logger.info(
        "Deleted documents with name '%s' from index %s.",
        document_name,
        OPENSEARCH_INDEX,
    )
    return response
