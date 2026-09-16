import logging

import streamlit as st

from src.chat import check_ollama_healthy
from src.opensearch import check_opensearch_healthy
from src.ui import (
    PRODUCT_FULL_NAME,
    PRODUCT_NAME,
    apply_theme,
    page_header,
    render_sidebar,
    status_card,
)
from src.utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title=PRODUCT_FULL_NAME,
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)


def display_main_content() -> None:
    """Displays the main welcome content, health status, and navigation CTAs."""
    page_header(
        PRODUCT_NAME,
        "Private document search and Q&A on your machine — hybrid retrieval plus a local LLM.",
    )

    st.markdown("### Service status")
    col1, col2 = st.columns(2)
    with col1:
        os_ok = check_opensearch_healthy()
        status_card(
            "OpenSearch",
            os_ok,
            "Hybrid search index is ready."
            if os_ok
            else "Start the OpenSearch container on port 9200.",
        )
    with col2:
        ollama_ok = check_ollama_healthy()
        status_card(
            "Ollama",
            ollama_ok,
            "Local chat model service is reachable."
            if ollama_ok
            else "Launch Ollama and pull your chat model.",
        )

    st.markdown("### Get started")
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
        <div class="pdm-card" style="margin-top:1rem;">
            <h3>What you can do</h3>
            <ul style="margin:0.4rem 0 0 1rem; color:#E8F1F2;">
                <li><strong>Upload</strong> PDFs — chunked, embedded, and indexed locally</li>
                <li><strong>Chat</strong> with RAG on — answers grounded in your files with sources</li>
                <li><strong>Stay private</strong> — OpenSearch + Ollama run on your machine</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )
    logger.info("Displayed main welcome content.")


if __name__ == "__main__":
    apply_theme()
    render_sidebar(tagline="using local RAG")
    display_main_content()
