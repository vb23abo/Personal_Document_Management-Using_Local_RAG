# Technical Requirements Document (TRD)

**Product:** Personal Document Management - using local RAG  
**Owner:** vb23abo  
**Status:** Active  
**Last updated:** 2026-09-15  
**Companion:** [PRD.md](PRD.md)

---

## 1. Purpose

This document specifies the technical architecture, components, interfaces, data model, configuration, and operational requirements for the Personal Document Management local RAG application.

---

## 2. System architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Streamlit UI layer                       │
│  Welcome.py │ pages/Upload │ pages/Chatbot │ src/ui.py       │
└───────────────┬─────────────────────────────┬───────────────┘
                │                             │
                ▼                             ▼
┌───────────────────────────┐   ┌─────────────────────────────┐
│     Ingestion pipeline    │   │     Query / generation      │
│  OCR → chunk → embed →    │   │  embed query → hybrid       │
│  bulk index               │   │  search → prompt → Ollama   │
│  src/ocr, utils,          │   │  stream + citations         │
│  embeddings, ingestion    │   │  src/chat, embeddings,      │
└─────────────┬─────────────┘   │  opensearch                 │
              │                 └──────────────┬──────────────┘
              ▼                                ▼
┌───────────────────────────┐   ┌─────────────────────────────┐
│  OpenSearch (local)       │   │  Ollama (local)             │
│  index: documents         │   │  chat model (configurable)  │
│  pipeline: nlp-search-    │   └─────────────────────────────┘
│  pipeline (hybrid)        │
│  knn_vector cosinesimil   │
└───────────────────────────┘
```

### 2.1 Runtime dependencies

| Component | Role | Default |
|-----------|------|---------|
| Python 3.10+ | Application runtime | — |
| Streamlit | Multipage UI | 1.39.x |
| OpenSearch | Hybrid retrieval store | `localhost:9200` |
| Sentence Transformers + PyTorch | Embeddings | `all-mpnet-base-v2` (768-d) |
| Ollama | Local LLM inference | `llama3.2:1b` |
| PyPDF2 + Pillow + Tesseract | PDF / OCR | Optional Tesseract binary |
| python-dotenv | Env configuration | Optional `.env` |

---

## 3. Repository layout

| Path | Responsibility |
|------|----------------|
| `Welcome.py` | Landing page, service health, navigation CTAs |
| `pages/1_🤖_Chatbot.py` | Chat UX, RAG controls, streaming, citations |
| `pages/2_📄_Upload_Documents.py` | Upload, index, list, delete |
| `src/constants.py` | Env-backed configuration |
| `src/ui.py` | Theme, branding, sidebar chrome |
| `src/ocr.py` | PDF text extraction + OCR fallback |
| `src/utils.py` | Logging, cleaning, chunking, filename sanitize |
| `src/embeddings.py` | Model load (`lru_cache`), batched encode |
| `src/ingestion.py` | Index create, bulk index, delete-by-name |
| `src/opensearch.py` | Client, pipeline ensure, hybrid search, health |
| `src/chat.py` | Prompting, Ollama stream, citations payload |
| `src/index_config.json` | Index settings/mappings template |
| `documents/` | PRD / TRD product docs |
| `.env.example` | Documented environment overrides |

---

## 4. Data flow

### 4.1 Ingestion

1. User selects PDFs and clicks **Index uploaded files**
2. Filename sanitized via `Path(name).name`
3. File saved under `uploaded_files/`
4. `extract_text_from_pdf` extracts text; empty pages fall back to OCR on embedded images
5. If cleaned text length `< MIN_EXTRACTED_CHARS`, skip with warning
6. `chunk_text` splits on words (`TEXT_CHUNK_SIZE`, `TEXT_CHUNK_OVERLAP`) with validation `0 ≤ overlap < chunk_size`
7. `generate_embeddings` batch-encodes chunks (`normalize_embeddings=True`; optional `passage:` prefix if asymmetric mode)
8. `bulk_index_documents` writes `{text, embedding, document_name}` with `raise_on_error=False`

### 4.2 Query (RAG on)

1. Embed query (`query:` prefix if asymmetric; otherwise raw), normalized
2. `hybrid_search` against OpenSearch using `nlp-search-pipeline`
3. Build prompt with retrieved context + prior history (current user turn not duplicated)
4. Stream Ollama chat chunks to UI
5. Return citations `{document_name, snippet, score}` for Sources UI

### 4.3 Query (RAG off)

Skip retrieval; prompt uses conversation history + general assistant instruction only.

---

## 5. Data model (OpenSearch)

**Index name:** `OPENSEARCH_INDEX` (default `documents`)

| Field | Type | Notes |
|-------|------|-------|
| `text` | `text` | Raw chunk text for BM25 (no embedding prefix stored) |
| `embedding` | `knn_vector` dim=`EMBEDDING_DIMENSION` | `lucene` / `hnsw` / `cosinesimil` |
| `document_name` | `keyword` | Source filename; used for list/delete aggregations |

**Document `_id`:** `{document_name}_{chunk_index}`

**Search pipeline:** `nlp-search-pipeline`  
- Normalization: `min_max`  
- Combination: `arithmetic_mean` with weights `[0.3, 0.7]` (BM25, kNN)

Created automatically by `ensure_search_pipeline` during `create_index`.

---

## 6. Interfaces

### 6.1 Configuration interface

All primary knobs via environment / `.env` (see `.env.example`):

- Models: `EMBEDDING_MODEL_PATH`, `ASYMMETRIC_EMBEDDING`, `EMBEDDING_DIMENSION`, `OLLAMA_MODEL_NAME`
- Chunking: `TEXT_CHUNK_SIZE`, `TEXT_CHUNK_OVERLAP`, `MIN_EXTRACTED_CHARS`
- OpenSearch: `OPENSEARCH_HOST`, `OPENSEARCH_PORT`, `OPENSEARCH_INDEX`
- Logging: `LOG_FILE_PATH`

### 6.2 Key Python APIs

| Function | Module | Contract |
|----------|--------|----------|
| `get_embedding_model()` | `embeddings` | Cached `SentenceTransformer` |
| `generate_embeddings(chunks)` | `embeddings` | `List[np.ndarray]`, batched |
| `create_index(client)` | `ingestion` | Idempotent index + pipeline |
| `bulk_index_documents(docs)` | `ingestion` | `(success_count, errors)` |
| `hybrid_search(text, vector, top_k)` | `opensearch` | OpenSearch hits |
| `generate_response_streaming(...)` | `chat` | `GenerationResult(stream, citations)` |
| `ensure_model_pulled(model)` | `chat` | `bool` |
| `check_opensearch_healthy()` / `check_ollama_healthy()` | `opensearch` / `chat` | `bool` |

### 6.3 UI contracts

- Session flags: `embedding_model_ready`, `ollama_model_ready` (separate)
- Chat history messages may include `citations` on assistant turns
- Upload listing must not call OCR on rerun; use index aggregations for chunk counts

---

## 7. Technical requirements

| ID | Requirement | Implementation notes |
|----|-------------|----------------------|
| TR-1 | Hybrid search must work on fresh OpenSearch without notebook setup | Auto-create pipeline |
| TR-2 | Embedding module must not depend on Streamlit | `functools.lru_cache` |
| TR-3 | Logging must not crash when `logs/` is missing | `Path.mkdir(parents=True)` |
| TR-4 | Index config path must be CWD-independent | `Path(__file__).parent / index_config.json` |
| TR-5 | Vector space must match encoding | `cosinesimil` + `normalize_embeddings=True` |
| TR-6 | Asymmetric mode must use consistent prefixes | docs: `passage:`, queries: `query:`; store raw text |
| TR-7 | Bulk indexing must report soft failures | `helpers.bulk(..., raise_on_error=False)` |
| TR-8 | Uploaded names must not allow path traversal | `sanitize_filename` |
| TR-9 | Sticky Streamlit uploader must not auto-reindex after delete | Explicit Index button |
| TR-10 | Failed/empty LLM responses must not pollute history | UI error + early return |

---

## 8. Security and privacy

| Topic | Requirement |
|-------|-------------|
| Data residency | Default deployment keeps PDFs, embeddings, and chat local |
| OpenSearch | Default client is unauthenticated HTTP to localhost; do not expose port publicly without auth/TLS |
| Uploads | Basename-only filenames; files under `uploaded_files/` (gitignored) |
| Secrets | `.env` gitignored; no API keys required for default local stack |
| Prompt injection | Prompt instructs model to treat document context as untrusted data |

---

## 9. Observability

- Application logs append to `LOG_FILE_PATH` (default `logs/app.log`)
- Welcome page provides interactive health probes
- Streamlit surfaces connect/index/generation errors to the user

---

## 10. Build, run, and deploy

### 10.1 Local run

```bash
pip install -r requirements.txt
streamlit run Welcome.py
```

### 10.2 External services

- OpenSearch with kNN / hybrid search support enabled
- Ollama daemon with the configured model pulled (app can pull on first chat)
- Optional system Tesseract for OCR

### 10.3 Index migration

Changing `space_type` or embedding dimension requires deleting/recreating the index and re-ingesting documents.

---

## 11. Testing requirements (target)

| Level | Scope |
|-------|-------|
| Unit | `clean_text`, `chunk_text` validation, `sanitize_filename`, citation assembly |
| Integration | Mock OpenSearch bulk/search; mock Ollama stream |
| Manual smoke | Upload → index → RAG question → citation → delete |

Automated tests are desirable but not yet shipped as a required CI gate in this revision.

---

## 12. Risks and mitigations

| Risk | Mitigation |
|------|------------|
| OCR quality on hard scans | Image OCR fallback; document min-length skip; future full-page render |
| Large PDFs / slow CPU embeds | Batching; user-triggered index; smaller models via `.env` |
| Existing L2 index after cosine change | Documented recreate/re-upload path in README |
| Ollama/OpenSearch down | Health checks + explicit UI errors |

---

## 13. Traceability

| PRD item | TRD coverage |
|----------|--------------|
| UC-1..UC-2 / FR-DM-* | §4.1, §5, TR-8, TR-9 |
| UC-3..UC-5 / FR-CH-* | §4.2–4.3, §6.2, TR-10 |
| UC-6 / FR-OP-3 | §6.2 health APIs, Welcome |
| FR-OP-1..2 | TR-1, `create_index` / `ensure_search_pipeline` |
| NFR privacy/security | §8 |
| NFR performance | TR-2, batched embeddings, no list OCR |
