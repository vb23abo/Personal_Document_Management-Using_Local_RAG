import logging
import queue
import threading
from typing import Any, Dict, List

import streamlit as st

from src.chat import (
    commit_chat_turn,
    ensure_model_pulled,
    prepare_prompt,
    produce_chat_chunks,
)
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
    require_local_access,
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


def _finalize_generation(state: Dict[str, Any]) -> None:
    """Store a finished or stopped answer, and drop the turn when it is empty."""
    if state.get("finished"):
        return
    state["finished"] = True
    user_text = state["user_text"]
    text = state.get("text") or ""
    stopped = bool(state["stop"].is_set())
    if state.get("error") or not text.strip():
        st.session_state["chat_history"] = commit_chat_turn(
            st.session_state["chat_history"], user_text, None, []
        )
        if state.get("error"):
            notice = (
                "error",
                "Failed to generate a response. Check Ollama and OpenSearch.",
            )
        elif stopped:
            notice = ("info", "Stopped before any text was generated.")
        else:
            notice = ("error", "The model returned an empty response.")
        st.session_state["gen_notice"] = notice
    else:
        citations = state["citations"] if state["use_rag"] else []
        st.session_state["chat_history"] = commit_chat_turn(
            st.session_state["chat_history"], user_text, text, citations
        )
        st.session_state["last_citations"] = citations
    st.session_state["gen_state"] = None
    st.rerun(scope="app")


@st.fragment(run_every="0.5s")
def _generation_panel() -> None:
    """Poll the background Ollama stream and offer a stop control."""
    state = st.session_state.get("gen_state")
    if not state or state.get("finished"):
        return
    try:
        while True:
            item = state["queue"].get_nowait()
            if item is None:
                state["done"] = True
            elif isinstance(item, Exception):
                state["error"] = str(item)
                state["done"] = True
            else:
                state["text"] += item
    except queue.Empty:
        pass
    worker = state.get("thread")
    if (
        not state["done"]
        and worker is not None
        and not worker.is_alive()
        and state["queue"].empty()
    ):
        state["error"] = state.get("error") or "Generation stopped unexpectedly."
        state["done"] = True
    with st.chat_message("assistant"):
        if state["text"]:
            st.markdown(state["text"] + ("" if state["done"] else "▌"))
        elif not state["done"]:
            st.caption("Generating...")
        if not state["done"] and st.button("Stop generating"):
            state["stop"].set()
    if state["done"]:
        _finalize_generation(state)


def _begin_generation(prompt: str) -> None:
    st.session_state["chat_history"].append({"role": "user", "content": prompt})
    logger.info("User input received.")
    try:
        built, citations = prepare_prompt(
            prompt,
            use_hybrid_search=st.session_state["use_hybrid_search"],
            num_results=st.session_state["num_results"],
            chat_history=st.session_state["chat_history"],
        )
    except Exception as e:
        logger.error("Failed to prepare prompt: %s", e)
        st.session_state["chat_history"] = commit_chat_turn(
            st.session_state["chat_history"], prompt, None, []
        )
        st.error("Failed to generate a response. Check Ollama and OpenSearch.")
        return
    stop_event = threading.Event()
    out_queue: queue.Queue[Any] = queue.Queue()
    worker = threading.Thread(
        target=produce_chat_chunks,
        args=(built, st.session_state["temperature"], stop_event, out_queue),
        daemon=True,
    )
    st.session_state["gen_state"] = {
        "user_text": prompt,
        "text": "",
        "citations": citations,
        "use_rag": st.session_state["use_hybrid_search"],
        "queue": out_queue,
        "stop": stop_event,
        "thread": worker,
        "done": False,
        "finished": False,
        "error": None,
    }
    worker.start()
    st.rerun()


def _render_citations(citations: List[Dict[str, Any]]) -> None:
    if not citations:
        st.caption("No retrieval hits for this answer.")
        return
    with st.expander("Sources", expanded=False):
        for i, cite in enumerate(citations, 1):
            name = cite.get("document_name", "unknown")
            snippet = cite.get("snippet", "")
            score = cite.get("score")
            score_note = (
                f" (score: {score:.4f})" if isinstance(score, (int, float)) else ""
            )
            st.markdown(f"**{i}. {name}**{score_note}")
            st.caption(snippet)


def render_chatbot_page() -> None:
    apply_theme()
    require_local_access()
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

    if st.session_state["use_hybrid_search"]:
        try:
            with st.spinner("Connecting to OpenSearch..."):
                client = get_opensearch_client()
            create_index(client)
        except Exception as e:
            st.error(f"Could not connect to OpenSearch: {e}")
            return

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

    notice = st.session_state.pop("gen_notice", None)
    if notice:
        level, message = notice
        if level == "info":
            st.info(message)
        else:
            st.error(message)

    for message in st.session_state["chat_history"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant" and message.get("citations"):
                _render_citations(message["citations"])

    if st.session_state.get("gen_state"):
        _generation_panel()
    elif prompt := st.chat_input("Type your message here..."):
        with st.chat_message("user"):
            st.markdown(prompt)
        _begin_generation(prompt)


if __name__ == "__main__":
    render_chatbot_page()
