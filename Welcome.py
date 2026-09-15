import logging

import streamlit as st

from src.chat import check_ollama_healthy
from src.opensearch import check_opensearch_healthy
from src.ui import PRODUCT_FULL_NAME, PRODUCT_NAME, apply_theme, render_sidebar
from src.utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title=PRODUCT_FULL_NAME,
    page_icon="📄",
)


def display_main_content() -> None:
    """Displays the main welcome content, health status, and navigation CTAs."""
    st.title(PRODUCT_NAME)
    st.markdown(
        f"""
        Welcome to **{PRODUCT_FULL_NAME}**.

        Manage and query your personal documents locally with hybrid search and a local LLM.
        Nothing leaves your machine.
        """
    )

    st.subheader("Service status")
    col1, col2 = st.columns(2)
    with col1:
        os_ok = check_opensearch_healthy()
        if os_ok:
            st.success("OpenSearch: reachable")
        else:
            st.error("OpenSearch: unreachable (is it running on the configured host/port?)")
    with col2:
        ollama_ok = check_ollama_healthy()
        if ollama_ok:
            st.success("Ollama: reachable")
        else:
            st.error("Ollama: unreachable (is the Ollama service running?)")

    st.subheader("Get started")
    cta1, cta2 = st.columns(2)
    with cta1:
        st.page_link(
            "pages/2_📄_Upload_Documents.py",
            label="Upload documents",
            icon="📄",
        )
    with cta2:
        st.page_link(
            "pages/1_🤖_Chatbot.py",
            label="Open chatbot",
            icon="🤖",
        )

    st.markdown(
        """
        **Features:**
        - **Chatbot**: Ask questions with optional RAG context from your indexed files.
        - **Document Upload**: Upload PDFs; text is chunked, embedded, and stored in OpenSearch.
        """
    )
    logger.info("Displayed main welcome content.")


if __name__ == "__main__":
    apply_theme()
    render_sidebar(tagline="using local RAG")
    display_main_content()
