# Personal Document Management - using local RAG

A private, fully local document Q&A application. Upload PDFs, index them with hybrid search (keyword + semantic), and chat with a local LLM. Your files never leave your machine.

| | |
|---|---|
| **UI** | Streamlit |
| **Search** | OpenSearch hybrid (BM25 + kNN) |
| **Embeddings** | Sentence Transformers |
| **LLM** | Ollama (local) |

## Quick start

**Prerequisites:** Python 3.10+, [OpenSearch](https://opensearch.org/) on `localhost:9200`, [Ollama](https://ollama.com/) with a chat model, optional [Tesseract](https://github.com/tesseract-ocr/tesseract) for scanned PDFs.

```bash
git clone https://github.com/vb23abo/Personal_Document_Management-Using_Local_RAG.git
cd Personal_Document_Management-Using_Local_RAG
pip install -r requirements.txt
# optional: cp .env.example .env
streamlit run Welcome.py
```

1. Open **Upload Documents**, select PDFs, click **Index uploaded files**.
2. Open **Chatbot**, keep **Enable RAG mode** on, and ask questions about your documents.

The app auto-creates the OpenSearch index and `nlp-search-pipeline` on startup.

## Features

- Hybrid RAG retrieval with source citations under each answer
- PDF text extraction with OCR fallback for scanned pages
- Local-only stack (OpenSearch + Ollama + local embeddings)
- Configurable models and hosts via `.env`
- Welcome-page health checks for OpenSearch and Ollama
- Teal/black branded Streamlit UI (`images/logo.png` optional)

## Configuration

Copy [`.env.example`](.env.example) to `.env` or edit defaults in [`src/constants.py`](src/constants.py).

| Variable | Default | Purpose |
|----------|---------|---------|
| `EMBEDDING_MODEL_PATH` | `sentence-transformers/all-mpnet-base-v2` | Embedding model |
| `OLLAMA_MODEL_NAME` | `llama3.2:1b` | Chat model |
| `OPENSEARCH_HOST` / `PORT` / `INDEX` | `localhost` / `9200` / `documents` | Search backend |
| `TEXT_CHUNK_SIZE` / `OVERLAP` | `300` / `100` | Word-based chunking |

Vectors use **cosine similarity** with normalized embeddings. If you previously indexed with L2, delete the old index (or change `OPENSEARCH_INDEX`) and re-upload documents.

## Project structure

```
Welcome.py                 # Landing + health checks
pages/                     # Chatbot + Upload UIs
src/                       # RAG core (chat, ingest, search, OCR, embeddings)
documents/                 # Product & technical requirements (PRD, TRD)
notebooks/                 # Optional walkthrough notebooks
.env.example               # Sample environment overrides
```

## Documentation

| Document | Description |
|----------|-------------|
| [documents/PRD.md](documents/PRD.md) | Product Requirements Document |
| [documents/TRD.md](documents/TRD.md) | Technical Requirements Document |

## License

MIT — see [LICENSE](LICENSE).
