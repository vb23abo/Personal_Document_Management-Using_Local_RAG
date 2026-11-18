import logging
import os
import time

import streamlit as st

from src.constants import (
    MIN_EXTRACTED_CHARS,
    OPENSEARCH_INDEX,
    TEXT_CHUNK_OVERLAP,
    TEXT_CHUNK_SIZE,
)
from src.embeddings import generate_embeddings, get_embedding_model
from src.extract import SUPPORTED_EXTENSIONS, extract_text
from src.ingestion import (
    bulk_index_documents,
    clear_all_documents,
    create_index,
    delete_documents_by_document_name,
    recreate_index,
)
from src.opensearch import get_opensearch_client
from src.ui import (
    PRODUCT_NAME,
    apply_theme,
    page_header,
    render_sidebar_footer,
    render_sidebar_header,
    require_local_access,
)
from src.utils import chunk_text, sanitize_filename, setup_logging

setup_logging()
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title=f"{PRODUCT_NAME} - Upload Documents",
    page_icon="📂",
    layout="wide",
    initial_sidebar_state="expanded",
)

UPLOAD_DIR = "uploaded_files"


def save_uploaded_file(uploaded_file, safe_name: str) -> str:  # type: ignore
    """Saves an uploaded file to the local file system using a sanitized name."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, safe_name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    logger.info("File '%s' saved to '%s'.", safe_name, file_path)
    return file_path


def delete_local_uploads() -> None:
    """Remove files saved under the upload folder."""
    if not os.path.isdir(UPLOAD_DIR):
        return
    for name in os.listdir(UPLOAD_DIR):
        path = os.path.join(UPLOAD_DIR, name)
        if os.path.isfile(path):
            try:
                os.remove(path)
            except OSError as e:
                logger.warning("Could not remove '%s': %s", path, e)


def discard_uploaded_file(file_path: str) -> None:
    """Remove a file that was saved but will not stay in the index."""
    try:
        os.remove(file_path)
        logger.info("Removed unindexed file '%s'.", file_path)
    except OSError as e:
        logger.warning("Could not remove unindexed file '%s': %s", file_path, e)


def render_upload_page() -> None:
    """Renders the document upload page for users to upload and manage PDFs."""
    apply_theme()
    require_local_access()
    render_sidebar_header(tagline="Upload and index documents")
    render_sidebar_footer()

    page_header(
        "Upload Documents",
        "Add PDF, DOCX, TXT, or Markdown files. They are chunked, embedded, and stored in OpenSearch.",
    )
    model_loading_placeholder = st.empty()

    if "embedding_model_ready" not in st.session_state:
        with model_loading_placeholder:
            with st.spinner("Loading models for document processing..."):
                get_embedding_model()
                st.session_state["embedding_model_ready"] = True
        logger.info("Embedding model loaded.")
        model_loading_placeholder.empty()

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    try:
        with st.spinner("Connecting to OpenSearch..."):
            client = get_opensearch_client()
        create_index(client)
    except Exception as e:
        st.error(f"Could not connect to OpenSearch: {e}")
        return

    index_name = OPENSEARCH_INDEX

    query = {
        "size": 0,
        "aggs": {"unique_docs": {"terms": {"field": "document_name", "size": 10000}}},
    }
    try:
        response = client.search(index=index_name, body=query)
        buckets = response["aggregations"]["unique_docs"]["buckets"]
    except Exception as e:
        st.error(f"Failed to list indexed documents: {e}")
        return

    document_names = [bucket["key"] for bucket in buckets]
    chunk_counts = {bucket["key"]: bucket["doc_count"] for bucket in buckets}
    total_chunks = sum(chunk_counts.values())
    logger.info("Retrieved document names from OpenSearch.")
    st.caption(
        f"{len(document_names)} document(s), {total_chunks} chunk(s) in the index."
    )

    admin_col1, admin_col2 = st.columns(2)
    with admin_col1:
        if st.button("Clear index"):
            clear_all_documents()
            st.session_state["deleted_file"] = "all indexed documents"
            time.sleep(0.5)
            st.rerun()
    with admin_col2:
        if st.button("Recreate index"):
            recreate_index()
            delete_local_uploads()
            st.session_state["deleted_file"] = "the index and local uploads"
            time.sleep(0.5)
            st.rerun()

    documents = []
    for document_name in document_names:
        file_path = os.path.join(UPLOAD_DIR, document_name)
        local_present = os.path.exists(file_path)
        documents.append(
            {
                "filename": document_name,
                "chunk_count": chunk_counts.get(document_name, 0),
                "file_path": file_path if local_present else None,
                "local_file_present": local_present,
            }
        )
        if not local_present:
            logger.warning("File '%s' does not exist locally.", document_name)
    st.session_state["documents"] = documents

    if "deleted_file" in st.session_state:
        st.success(
            f"The file '{st.session_state['deleted_file']}' was successfully deleted."
        )
        del st.session_state["deleted_file"]

    uploaded_files = st.file_uploader(
        "Upload documents",
        type=list(SUPPORTED_EXTENSIONS),
        accept_multiple_files=True,
    )

    if uploaded_files and st.button("Index uploaded files", type="primary"):
        indexed_count = 0
        with st.spinner("Uploading and processing documents. Please wait..."):
            for uploaded_file in uploaded_files:
                try:
                    safe_name = sanitize_filename(uploaded_file.name)
                except ValueError as e:
                    st.error(f"Skipped an upload: {e}")
                    continue
                if safe_name in document_names:
                    st.warning(
                        f"The file '{safe_name}' already exists in the index."
                    )
                    continue

                file_path = save_uploaded_file(uploaded_file, safe_name)
                try:
                    text = extract_text(file_path)
                except ValueError as e:
                    discard_uploaded_file(file_path)
                    st.error(f"Skipped '{safe_name}': {e}")
                    continue
                if len(text.strip()) < MIN_EXTRACTED_CHARS:
                    discard_uploaded_file(file_path)
                    st.warning(
                        f"Skipped '{safe_name}': extracted text too short "
                        f"({len(text.strip())} chars). Check OCR/Tesseract."
                    )
                    logger.warning("Skipped empty/short extraction for %s.", safe_name)
                    continue

                try:
                    chunks = chunk_text(
                        text,
                        chunk_size=TEXT_CHUNK_SIZE,
                        overlap=TEXT_CHUNK_OVERLAP,
                    )
                except ValueError as e:
                    discard_uploaded_file(file_path)
                    st.error(f"Chunking failed for '{safe_name}': {e}")
                    continue

                if not chunks:
                    discard_uploaded_file(file_path)
                    st.warning(f"Skipped '{safe_name}': no chunks produced.")
                    continue

                embeddings = generate_embeddings(chunks)
                documents_to_index = [
                    {
                        "doc_id": f"{safe_name}_{i}",
                        "text": chunk,
                        "embedding": embedding,
                        "document_name": safe_name,
                    }
                    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
                ]
                success, errors = bulk_index_documents(documents_to_index)
                if success == 0:
                    discard_uploaded_file(file_path)
                    st.error(
                        f"Could not index '{safe_name}'"
                        + (f" ({len(errors)} bulk error(s))." if errors else ".")
                    )
                    continue
                if errors:
                    st.warning(
                        f"Indexed '{safe_name}' with {len(errors)} bulk error(s)."
                    )
                document_names.append(safe_name)
                indexed_count += 1
                logger.info(
                    "File '%s' uploaded and indexed (%s docs).", safe_name, success
                )

        if indexed_count:
            st.success(f"Indexed {indexed_count} file(s) successfully!")
            time.sleep(0.5)
            st.rerun()
        else:
            st.info("No new files were indexed.")

    if st.session_state["documents"]:
        st.markdown("### Uploaded Documents")
        with st.expander("Manage Uploaded Documents", expanded=True):
            for idx, doc in enumerate(st.session_state["documents"], 1):
                col1, col2 = st.columns([4, 1])
                with col1:
                    local_note = (
                        "" if doc["local_file_present"] else " (local file missing)"
                    )
                    st.write(
                        f"{idx}. {doc['filename']} — {doc['chunk_count']} chunk(s)"
                        f"{local_note}"
                    )
                with col2:
                    delete_button = st.button(
                        "Delete",
                        key=f"delete_{doc['filename']}_{idx}",
                        help=f"Delete {doc['filename']}",
                    )
                    if delete_button:
                        if doc["file_path"] and os.path.exists(doc["file_path"]):
                            try:
                                os.remove(doc["file_path"])
                                logger.info(
                                    "Deleted file '%s' from filesystem.",
                                    doc["filename"],
                                )
                            except FileNotFoundError:
                                st.error(
                                    f"File '{doc['filename']}' not found in filesystem."
                                )
                                logger.error(
                                    "File '%s' not found during deletion.",
                                    doc["filename"],
                                )
                        delete_documents_by_document_name(doc["filename"])
                        st.session_state["deleted_file"] = doc["filename"]
                        time.sleep(0.5)
                        st.rerun()


if __name__ == "__main__":
    if "documents" not in st.session_state:
        st.session_state["documents"] = []
    render_upload_page()
