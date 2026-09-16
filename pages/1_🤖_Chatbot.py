import logging
from typing import Any, Dict, List

import streamlit as st

from src.chat import ensure_model_pulled, generate_response_streaming
from src.constants import OLLAMA_MODEL_NAME
from src.embeddings import get_embedding_model
from src.ingestion import create_index
from src.opensearch import get_opensearch_client
from src.ui import (
    PRODUCT_NAME,
    apply_theme,
    page_header,
    render_sidebar_footer,
    render_sidebar_header,
)
from src.utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title=f"{PRODUCT_NAME} - Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _render_citations(citations: List[Dict[str, Any]]) -> None:
    if not citations:
        st.caption("No retrieval hits for this answer.")
        return
    with st.expander("Sources", expanded=False):
        for i, cite in enumerate(citations, 1):
            name = cite.get("document_name", "unknown")
            snippet = cite.get("snippet", "")
            score = cite.get("score")
            score_note = f" (score: {score:.4f})" if isinstance(score, (int, float)) else ""
            st.markdown(f"**{i}. {name}**{score_note}")
            st.caption(snippet)


def render_chatbot_page() -> None:
    apply_theme()
    render_sidebar_header(tagline="Chat with your documents")

    page_header(
        "Chatbot",
        "Ask questions about your indexed documents. Enable RAG to ground answers in your files.",
    )
    model_loading_placeholder = st.empty()

    if "use_hybrid_search" not in st.session_state:
        st.session_state["use_hybrid_search"] = True
    if "num_results" not in st.session_state:
        st.session_state["num_results"] = 5
    if "temperature" not in st.session_state:
        st.session_state["temperature"] = 0.7
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
    if "last_citations" not in st.session_state:
        st.session_state["last_citations"] = []

    try:
        with st.spinner("Connecting to OpenSearch..."):
            client = get_opensearch_client()
        create_index(client)
    except Exception as e:
        st.error(f"Could not connect to OpenSearch: {e}")
        render_sidebar_footer()
        return

    st.session_state["use_hybrid_search"] = st.sidebar.checkbox(
        "Enable RAG mode", value=st.session_state["use_hybrid_search"]
    )
    if st.session_state["use_hybrid_search"]:
        st.session_state["num_results"] = st.sidebar.number_input(
            "Number of Results in Context Window",
            min_value=1,
            max_value=10,
            value=st.session_state["num_results"],
            step=1,
        )
    else:
        st.sidebar.caption("RAG off — answers use the LLM only (no document retrieval).")

    st.session_state["temperature"] = st.sidebar.slider(
        "Response Temperature",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state["temperature"],
        step=0.1,
    )

    if st.sidebar.button("Clear conversation"):
        st.session_state["chat_history"] = []
        st.session_state["last_citations"] = []
        st.rerun()

    render_sidebar_footer()

    if "embedding_model_ready" not in st.session_state:
        with model_loading_placeholder:
            with st.spinner("Loading embedding model..."):
                get_embedding_model()
                st.session_state["embedding_model_ready"] = True
        logger.info("Embedding model loaded.")

    if "ollama_model_ready" not in st.session_state:
        with model_loading_placeholder:
            with st.spinner(
                f"Ensuring Ollama model '{OLLAMA_MODEL_NAME}' is available..."
            ):
                ok = ensure_model_pulled(OLLAMA_MODEL_NAME)
                if ok:
                    st.session_state["ollama_model_ready"] = True
                    logger.info("Ollama model ready.")
                else:
                    st.error(
                        f"Could not load Ollama model '{OLLAMA_MODEL_NAME}'. "
                        "Is Ollama running?"
                    )
                    logger.error("Ollama model failed to load.")
                    return
        model_loading_placeholder.empty()
    else:
        model_loading_placeholder.empty()

    for message in st.session_state["chat_history"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant" and message.get("citations"):
                _render_citations(message["citations"])

    if prompt := st.chat_input("Type your message here..."):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state["chat_history"].append({"role": "user", "content": prompt})
        logger.info("User input received.")

        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            response_text = ""
            citations: List[Dict[str, Any]] = []

            with st.spinner("Generating response..."):
                result = generate_response_streaming(
                    prompt,
                    use_hybrid_search=st.session_state["use_hybrid_search"],
                    num_results=st.session_state["num_results"],
                    temperature=st.session_state["temperature"],
                    chat_history=st.session_state["chat_history"],
                )
                citations = result.citations
                response_stream = result.stream

            if response_stream is None:
                st.error("Failed to generate a response. Check Ollama and OpenSearch.")
                logger.error("Response stream was None.")
                return

            for chunk in response_stream:
                content = ""
                if isinstance(chunk, dict):
                    content = (
                        chunk.get("message", {}).get("content")
                        if isinstance(chunk.get("message"), dict)
                        else ""
                    ) or ""
                else:
                    message = getattr(chunk, "message", None)
                    content = getattr(message, "content", None) or ""

                if content:
                    response_text += content
                    response_placeholder.markdown(response_text + "▌")
                else:
                    # Final stream frames often have empty content; ignore those.
                    done = (
                        chunk.get("done")
                        if isinstance(chunk, dict)
                        else getattr(chunk, "done", False)
                    )
                    if not done:
                        logger.warning("Skipping stream chunk with no content: %s", type(chunk))

            if not response_text.strip():
                st.error("The model returned an empty response.")
                logger.error("Empty assistant response.")
                return

            response_placeholder.markdown(response_text)
            if st.session_state["use_hybrid_search"]:
                _render_citations(citations)

            st.session_state["chat_history"].append(
                {
                    "role": "assistant",
                    "content": response_text,
                    "citations": citations,
                }
            )
            st.session_state["last_citations"] = citations
            logger.info("Response generated and displayed.")


if __name__ == "__main__":
    render_chatbot_page()
