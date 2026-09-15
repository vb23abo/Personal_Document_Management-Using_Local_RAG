"""Application configuration. Defaults can be overridden via environment / .env."""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# Editable model / chunk settings (override with env vars)
EMBEDDING_MODEL_PATH = os.getenv(
    "EMBEDDING_MODEL_PATH", "sentence-transformers/all-mpnet-base-v2"
)
ASYMMETRIC_EMBEDDING = os.getenv("ASYMMETRIC_EMBEDDING", "false").lower() in (
    "1",
    "true",
    "yes",
)
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "768"))
# Word-based chunk size (split on whitespace), not characters
TEXT_CHUNK_SIZE = int(os.getenv("TEXT_CHUNK_SIZE", "300"))
TEXT_CHUNK_OVERLAP = int(os.getenv("TEXT_CHUNK_OVERLAP", "100"))

OLLAMA_MODEL_NAME = os.getenv("OLLAMA_MODEL_NAME", "llama3.2:1b")

# Logging
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "logs/app.log")

# OpenSearch
OPENSEARCH_HOST = os.getenv("OPENSEARCH_HOST", "localhost")
OPENSEARCH_PORT = int(os.getenv("OPENSEARCH_PORT", "9200"))
OPENSEARCH_INDEX = os.getenv("OPENSEARCH_INDEX", "documents")

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
INDEX_CONFIG_PATH = Path(__file__).resolve().parent / "index_config.json"

# Skip indexing when extracted text is shorter than this
MIN_EXTRACTED_CHARS = int(os.getenv("MIN_EXTRACTED_CHARS", "40"))
