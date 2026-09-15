import logging
from functools import lru_cache
from typing import Any, List

import numpy as np
from sentence_transformers import SentenceTransformer

from src.constants import ASYMMETRIC_EMBEDDING, EMBEDDING_MODEL_PATH
from src.utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """
    Loads and caches the embedding model (no Streamlit dependency).

    Returns:
        SentenceTransformer: The loaded embedding model.
    """
    logger.info("Loading embedding model from path: %s", EMBEDDING_MODEL_PATH)
    return SentenceTransformer(EMBEDDING_MODEL_PATH)


def generate_embeddings(chunks: List[str]) -> List[np.ndarray[Any, Any]]:
    """
    Generates embeddings for a list of text chunks (batched).

    When ASYMMETRIC_EMBEDDING is enabled, encodes with a 'passage:' prefix
    (query side should use 'query:'). Vectors are L2-normalized for cosine search.

    Args:
        chunks (List[str]): List of text chunks (raw text, no prefix).

    Returns:
        List[np.ndarray[Any, Any]]: List of embeddings as numpy arrays for each chunk.
    """
    if not chunks:
        return []

    model = get_embedding_model()
    to_encode = (
        [f"passage: {chunk}" for chunk in chunks]
        if ASYMMETRIC_EMBEDDING
        else list(chunks)
    )
    vectors = model.encode(
        to_encode,
        batch_size=32,
        show_progress_bar=False,
        normalize_embeddings=True,
    )
    embeddings = [np.array(vector) for vector in vectors]
    logger.info("Generated embeddings for %s text chunks.", len(chunks))
    return embeddings
