# Personal Document Management - using local RAG

Private, offline document search and Q&A for your own PDFs. Upload documents, index them in OpenSearch with hybrid (keyword + semantic) search, and chat with a local LLM via Ollama — no cloud upload of your files.

## Features

- **Local RAG chatbot** — answers grounded in your indexed documents, with source citations
- **Hybrid search** — BM25 text matching plus vector (kNN) retrieval in OpenSearch
- **PDF upload & OCR** — extract text from digital and scanned PDFs
- **Configurable models** — Sentence Transformers embeddings + Ollama chat model (via `.env`)

## Requirements

- Python 3.10+
- [OpenSearch](https://opensearch.org/) running locally (default `localhost:9200`) with hybrid search support
- [Ollama](https://ollama.com/) with a pulled chat model (default `llama3.2:1b`)
- Optional: [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) for scanned PDFs

## Setup

1. Clone the repo:

```bash
git clone https://github.com/vb23abo/Personal_Document_Management-Using_Local_RAG.git
cd Personal_Document_Management-Using_Local_RAG
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Optional: copy [`.env.example`](.env.example) to `.env` and set `EMBEDDING_MODEL_PATH`, `OLLAMA_MODEL_NAME`, OpenSearch host/port/index, etc. Defaults in [`src/constants.py`](src/constants.py) work for a local setup.

4. Optional: place your logo at `images/logo.png` (sidebar shows the product name if missing).

5. Run the app:

```bash
streamlit run Welcome.py
```

On startup the app creates the OpenSearch `documents` index (if missing) and the `nlp-search-pipeline` hybrid search pipeline automatically.

**Index mapping note:** vectors use cosine similarity (`cosinesimil`) with normalized embeddings. If you already have an older `documents` index built with L2, delete that index (or change `OPENSEARCH_INDEX`) so it can be recreated with the new mapping, then re-upload your PDFs.

## Project layout

| Path | Role |
|------|------|
| `Welcome.py` | Landing page, health checks, navigation |
| `pages/` | Chatbot and document upload UIs |
| `src/ui.py` | Shared teal/black theme and branding |
| `src/chat.py` | RAG prompt, citations, Ollama streaming |
| `src/ingestion.py` / `src/opensearch.py` | Indexing and hybrid search |
| `src/embeddings.py` / `src/ocr.py` / `src/utils.py` | Embeddings, PDF/OCR, chunking |
| `.env.example` | Sample environment overrides |
| `notebooks/` | Optional walkthrough notebooks |
