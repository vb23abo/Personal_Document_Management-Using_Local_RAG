"""Shared Streamlit UI: teal/black theme, branding, and sidebar chrome."""

import logging
import os

import streamlit as st

from src.utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

PRODUCT_NAME = "Personal Document Management"
PRODUCT_FULL_NAME = "Personal Document Management - using local RAG"
LOGO_PATH = "images/logo.png"
COPYRIGHT = "© 2026 Personal Document Management"

COLOR_BG = "#0A0A0A"
COLOR_SURFACE = "#111827"
COLOR_TEXT = "#E5E7EB"
COLOR_TEAL = "#14B8A6"
COLOR_TEAL_HOVER = "#0D9488"
COLOR_SIDEBAR = "#000000"


def apply_theme() -> None:
    """Applies the shared teal-and-black theme CSS."""
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {COLOR_BG};
            color: {COLOR_TEXT};
        }}
        body {{
            background-color: {COLOR_BG};
            color: {COLOR_TEXT};
        }}
        [data-testid="stSidebar"] {{
            background-color: {COLOR_SIDEBAR};
            border-right: 2px solid {COLOR_TEAL};
        }}
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h4,
        [data-testid="stSidebar"] p {{
            color: {COLOR_TEXT};
        }}
        .block-container {{
            background-color: {COLOR_SURFACE};
            border-radius: 10px;
            padding: 20px;
            border: 1px solid #1f2937;
        }}
        .footer-text {{
            font-size: 1rem;
            font-weight: 600;
            color: {COLOR_TEAL};
            text-align: center;
            margin-top: 10px;
        }}
        .stButton button {{
            background-color: {COLOR_TEAL};
            color: {COLOR_BG};
            border-radius: 5px;
            border: none;
            padding: 10px 20px;
            font-size: 16px;
        }}
        .stButton button:hover {{
            background-color: {COLOR_TEAL_HOVER};
            color: {COLOR_TEXT};
        }}
        h1, h2, h3, h4 {{
            color: {COLOR_TEAL};
        }}
        .stChatMessage {{
            background-color: {COLOR_SURFACE};
            color: {COLOR_TEXT};
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 10px;
            border: 1px solid #1f2937;
        }}
        [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {{
            background-color: {COLOR_TEAL};
            color: {COLOR_BG};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    logger.info("Applied teal/black theme.")


def display_logo(logo_path: str = LOGO_PATH) -> None:
    """Displays the logo in the sidebar, or a short-name placeholder if missing."""
    if os.path.exists(logo_path):
        st.sidebar.image(logo_path, width=220)
        logger.info("Logo displayed from %s.", logo_path)
    else:
        st.sidebar.markdown(f"### {PRODUCT_NAME}")
        logger.warning("Logo not found at %s; showing name placeholder.", logo_path)


def render_sidebar_header(tagline: str = "using local RAG") -> None:
    """Renders logo, product name, and tagline (call before page-specific controls)."""
    display_logo()
    st.sidebar.markdown(
        f"<h2 style='text-align: center; color: {COLOR_TEAL};'>{PRODUCT_NAME}</h2>",
        unsafe_allow_html=True,
    )
    st.sidebar.markdown(
        f"<h4 style='text-align: center; color: {COLOR_TEXT};'>{tagline}</h4>",
        unsafe_allow_html=True,
    )
    logger.info("Sidebar header rendered.")


def render_sidebar_footer() -> None:
    """Renders the copyright footer (call after page-specific controls)."""
    st.sidebar.markdown(
        f'<div class="footer-text">{COPYRIGHT}</div>',
        unsafe_allow_html=True,
    )


def render_sidebar(
    tagline: str = "using local RAG", *, show_footer: bool = True
) -> None:
    """
    Renders shared sidebar branding.

    Prefer render_sidebar_header() + controls + render_sidebar_footer() when the
    page needs widgets between the tagline and the copyright.
    """
    render_sidebar_header(tagline=tagline)
    if show_footer:
        render_sidebar_footer()
