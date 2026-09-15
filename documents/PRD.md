# Product Requirements Document (PRD)

**Product:** Personal Document Management - using local RAG  
**Owner:** vb23abo  
**Status:** Active  
**Last updated:** 2026-09-15

---

## 1. Overview

### 1.1 Problem

People need to search and ask questions over personal PDFs without uploading sensitive content to cloud AI services. Existing cloud RAG tools trade convenience for privacy and vendor lock-in.

### 1.2 Solution

A desktop-local web app that:

1. Ingests personal PDF documents
2. Indexes them for hybrid keyword + semantic search
3. Answers natural-language questions with a local LLM, grounded in retrieved chunks
4. Shows citations so users can verify answers

### 1.3 Goals

| Goal | Success indicator |
|------|-------------------|
| Privacy-first document Q&A | No document content sent to third-party APIs |
| Useful retrieval | Hybrid search returns relevant chunks; citations visible |
| Low friction local setup | Runnable with OpenSearch + Ollama + one Streamlit command |
| Trustworthy answers | Users can open Sources and see document names / snippets |

### 1.4 Non-goals (current release)

- Multi-user auth, roles, or cloud SaaS hosting
- Collaborative editing or document versioning
- Supported formats beyond PDF (DOCX/TXT/MD are future)
- Fine-tuning or training custom LLMs
- Mobile-native clients

---

## 2. Users and use cases

### 2.1 Primary user

Individual who keeps personal or work PDFs on their own machine and wants private Q&A (students, researchers, knowledge workers).

### 2.2 Core use cases

| ID | Use case | Priority |
|----|----------|----------|
| UC-1 | Upload one or more PDFs and index them | P0 |
| UC-2 | List and delete indexed documents | P0 |
| UC-3 | Ask a question with RAG enabled and receive a streamed answer | P0 |
| UC-4 | View source citations for an answer | P0 |
| UC-5 | Disable RAG and chat with the LLM only | P1 |
| UC-6 | See OpenSearch / Ollama health on the welcome page | P1 |
| UC-7 | Clear conversation history | P1 |
| UC-8 | Configure models/hosts without code changes (`.env`) | P1 |

---

## 3. Functional requirements

### 3.1 Document management

| ID | Requirement |
|----|-------------|
| FR-DM-1 | User can upload PDF files via the Upload page |
| FR-DM-2 | Indexing runs only when the user clicks **Index uploaded files** |
| FR-DM-3 | Duplicate filenames already in the index are skipped with a warning |
| FR-DM-4 | Files with too little extracted text are skipped (configurable minimum) |
| FR-DM-5 | User can delete a document from the index and local upload folder |
| FR-DM-6 | Document list shows chunk counts without re-OCR on every page refresh |

### 3.2 Retrieval and chat

| ID | Requirement |
|----|-------------|
| FR-CH-1 | User can enable/disable RAG mode |
| FR-CH-2 | When RAG is on, queries use hybrid search (BM25 + vector) |
| FR-CH-3 | Answers stream from the local Ollama model |
| FR-CH-4 | When RAG is on, the UI shows a Sources panel (document name + snippet) |
| FR-CH-5 | Empty or failed generations show an error and are not saved as answers |
| FR-CH-6 | User can clear the conversation |
| FR-CH-7 | User can adjust temperature and (when RAG is on) number of retrieved chunks |

### 3.3 Platform / ops

| ID | Requirement |
|----|-------------|
| FR-OP-1 | App creates the OpenSearch index if missing |
| FR-OP-2 | App creates the hybrid search pipeline if missing |
| FR-OP-3 | Welcome page reports OpenSearch and Ollama reachability |
| FR-OP-4 | Configuration is overridable via environment variables / `.env` |

---

## 4. Non-functional requirements

| ID | Category | Requirement |
|----|----------|-------------|
| NFR-1 | Privacy | Document text and embeddings stay on the local machine under normal use |
| NFR-2 | Security | Uploaded filenames are sanitized (basename only); no cloud auth secrets required for default local mode |
| NFR-3 | Usability | Primary flows completable from Streamlit sidebar navigation |
| NFR-4 | Reliability | OpenSearch/Ollama failures surface as UI errors, not silent empty answers |
| NFR-5 | Maintainability | Core RAG logic is importable without Streamlit UI (embeddings use process cache) |
| NFR-6 | Performance | Embeddings are batched; listing documents does not re-run OCR |

---

## 5. User experience

- **Brand:** Personal Document Management; subtitle “using local RAG”
- **Theme:** Teal and black Streamlit chrome; optional `images/logo.png`
- **Pages:** Welcome → Upload Documents → Chatbot
- **Tone:** Direct, privacy-focused, technical enough for self-hosters

---

## 6. Constraints and assumptions

- User can install and run OpenSearch and Ollama locally
- Default embedding model is downloadable from Hugging Face (or provided locally)
- Single-user / trusted-local-network deployment assumed
- GPU optional; CPU-only is acceptable for small models

---

## 7. Future roadmap (out of current PRD scope)

1. Additional file types (DOCX, TXT, Markdown)
2. Index management UI (recreate index, clear all, chunk stats)
3. Stop-generation control during streaming
4. Stronger OCR (full-page render for scans)
5. Optional basic auth for LAN exposure
6. Automated tests for chunking, retrieval mocks, and smoke UI checks

---

## 8. Acceptance criteria (MVP)

- [ ] Fresh clone + dependencies + OpenSearch + Ollama can run `streamlit run Welcome.py`
- [ ] User can index a PDF and see it in the document list with chunk count
- [ ] User can ask a RAG question and see a streamed answer plus Sources
- [ ] Deleting a document removes it from search results
- [ ] With Ollama stopped, Welcome health check shows failure and Chatbot errors clearly
