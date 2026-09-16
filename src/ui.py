"""Shared Streamlit UI: dark teal theme, branding, and sidebar chrome."""

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

# Dark + teal palette
COLOR_BG = "#05080A"
COLOR_SURFACE = "#0C1418"
COLOR_SURFACE_2 = "#122028"
COLOR_BORDER = "#1E333C"
COLOR_TEXT = "#E8F1F2"
COLOR_MUTED = "#8AA3AB"
COLOR_TEAL = "#2DD4BF"
COLOR_TEAL_DIM = "#14B8A6"
COLOR_TEAL_DEEP = "#0F766E"
COLOR_SIDEBAR = "#020405"
COLOR_DANGER = "#F87171"
COLOR_OK = "#34D399"


def apply_theme() -> None:
    """Applies a full-page dark teal theme over Streamlit defaults."""
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=Space+Grotesk:wght@500;600;700&display=swap');

        :root {{
            --pdm-bg: {COLOR_BG};
            --pdm-surface: {COLOR_SURFACE};
            --pdm-surface-2: {COLOR_SURFACE_2};
            --pdm-border: {COLOR_BORDER};
            --pdm-text: {COLOR_TEXT};
            --pdm-muted: {COLOR_MUTED};
            --pdm-teal: {COLOR_TEAL};
            --pdm-teal-dim: {COLOR_TEAL_DIM};
            --pdm-teal-deep: {COLOR_TEAL_DEEP};
        }}

        html, body, [class*="css"] {{
            font-family: "DM Sans", sans-serif;
            color: var(--pdm-text);
        }}

        .stApp {{
            background:
                radial-gradient(1200px 600px at 10% -10%, rgba(45, 212, 191, 0.12), transparent 55%),
                radial-gradient(900px 500px at 100% 0%, rgba(15, 118, 110, 0.18), transparent 50%),
                var(--pdm-bg);
            color: var(--pdm-text);
        }}

        /* Hide Streamlit chrome */
        #MainMenu {{ visibility: hidden; }}
        header[data-testid="stHeader"] {{
            background: transparent;
        }}
        [data-testid="stToolbar"] {{
            visibility: hidden;
            height: 0;
        }}
        footer {{ visibility: hidden; }}
        [data-testid="stDecoration"] {{ display: none; }}

        .block-container {{
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 980px;
        }}

        /* Sidebar */
        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #020405 0%, #071116 100%);
            border-right: 1px solid var(--pdm-border);
        }}
        [data-testid="stSidebar"] > div:first-child {{
            background: transparent;
        }}
        [data-testid="stSidebar"] * {{
            color: var(--pdm-text);
        }}
        [data-testid="stSidebarNav"] a {{
            border-radius: 10px;
            margin: 2px 0;
        }}
        [data-testid="stSidebarNav"] a:hover {{
            background: rgba(45, 212, 191, 0.08);
        }}
        [data-testid="stSidebarNav"] [aria-current="page"] {{
            background: rgba(45, 212, 191, 0.14);
            border: 1px solid rgba(45, 212, 191, 0.35);
        }}

        /* Branding blocks */
        .pdm-brand {{
            text-align: center;
            margin: 0.5rem 0 1.25rem 0;
        }}
        .pdm-brand-title {{
            font-family: "Space Grotesk", sans-serif;
            font-size: 1.15rem;
            font-weight: 700;
            letter-spacing: -0.02em;
            color: var(--pdm-teal);
            margin: 0.35rem 0 0.15rem 0;
            line-height: 1.25;
        }}
        .pdm-brand-tag {{
            color: var(--pdm-muted);
            font-size: 0.85rem;
            margin: 0;
        }}
        .pdm-footer {{
            margin-top: 1.5rem;
            padding-top: 1rem;
            border-top: 1px solid var(--pdm-border);
            text-align: center;
            color: var(--pdm-teal-dim);
            font-size: 0.8rem;
            font-weight: 600;
        }}

        /* Typography */
        h1, h2, h3 {{
            font-family: "Space Grotesk", sans-serif !important;
            color: var(--pdm-teal) !important;
            letter-spacing: -0.03em;
            font-weight: 700 !important;
        }}
        h1 {{
            font-size: 2.1rem !important;
            margin-bottom: 0.4rem !important;
        }}
        p, li, label, span, .stMarkdown {{
            color: var(--pdm-text);
        }}
        .pdm-lead {{
            color: var(--pdm-muted);
            font-size: 1.05rem;
            line-height: 1.55;
            margin-bottom: 1.5rem;
        }}

        /* Cards / panels */
        .pdm-card {{
            background: linear-gradient(180deg, var(--pdm-surface-2), var(--pdm-surface));
            border: 1px solid var(--pdm-border);
            border-radius: 16px;
            padding: 1.1rem 1.2rem;
            margin-bottom: 0.85rem;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
        }}
        .pdm-card h3 {{
            margin: 0 0 0.35rem 0 !important;
            font-size: 1rem !important;
            color: var(--pdm-text) !important;
        }}
        .pdm-status-ok {{
            color: {COLOR_OK};
            font-weight: 600;
        }}
        .pdm-status-bad {{
            color: {COLOR_DANGER};
            font-weight: 600;
        }}
        .pdm-pill {{
            display: inline-block;
            padding: 0.2rem 0.65rem;
            border-radius: 999px;
            border: 1px solid rgba(45, 212, 191, 0.35);
            background: rgba(45, 212, 191, 0.1);
            color: var(--pdm-teal);
            font-size: 0.75rem;
            font-weight: 600;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            margin-bottom: 0.75rem;
        }}

        /* Buttons */
        .stButton > button,
        .stDownloadButton > button {{
            background: linear-gradient(180deg, var(--pdm-teal), var(--pdm-teal-dim)) !important;
            color: #042f2e !important;
            border: none !important;
            border-radius: 12px !important;
            font-weight: 700 !important;
            padding: 0.55rem 1.1rem !important;
            box-shadow: 0 8px 20px rgba(20, 184, 166, 0.22);
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }}
        .stButton > button:hover {{
            background: linear-gradient(180deg, #5EEAD4, var(--pdm-teal)) !important;
            color: #022c22 !important;
            transform: translateY(-1px);
            box-shadow: 0 10px 24px rgba(20, 184, 166, 0.3);
        }}
        .stButton > button:focus {{
            outline: 2px solid rgba(45, 212, 191, 0.45) !important;
            box-shadow: none !important;
        }}

        /* Inputs */
        [data-testid="stTextInput"] input,
        [data-testid="stNumberInput"] input,
        [data-testid="stTextArea"] textarea,
        [data-baseweb="select"] > div,
        [data-testid="stFileUploader"] section {{
            background-color: var(--pdm-surface) !important;
            color: var(--pdm-text) !important;
            border: 1px solid var(--pdm-border) !important;
            border-radius: 12px !important;
        }}
        [data-testid="stChatInput"] {{
            background: transparent;
        }}
        [data-testid="stChatInput"] textarea {{
            background: var(--pdm-surface) !important;
            color: var(--pdm-text) !important;
            border: 1px solid var(--pdm-border) !important;
            border-radius: 16px !important;
        }}

        /* Checkbox / slider */
        [data-testid="stCheckbox"] label span {{
            color: var(--pdm-text) !important;
        }}
        [data-testid="stSlider"] [role="slider"] {{
            background-color: var(--pdm-teal) !important;
        }}

        /* Alerts */
        [data-testid="stAlert"] {{
            border-radius: 12px;
            border: 1px solid var(--pdm-border);
            background: var(--pdm-surface-2);
        }}

        /* Expander / file uploader */
        [data-testid="stExpander"] {{
            background: var(--pdm-surface);
            border: 1px solid var(--pdm-border);
            border-radius: 14px;
        }}
        [data-testid="stFileUploaderDropzone"] {{
            background: var(--pdm-surface) !important;
            border: 1px dashed rgba(45, 212, 191, 0.45) !important;
            border-radius: 14px !important;
        }}

        /* Chat bubbles */
        [data-testid="stChatMessage"] {{
            background: var(--pdm-surface) !important;
            border: 1px solid var(--pdm-border);
            border-radius: 16px;
            padding: 0.85rem 1rem;
            margin-bottom: 0.65rem;
        }}
        [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {{
            background: linear-gradient(135deg, rgba(45, 212, 191, 0.22), rgba(15, 118, 110, 0.18)) !important;
            border-color: rgba(45, 212, 191, 0.4);
        }}

        /* Page links */
        [data-testid="stPageLink-NavLink"] {{
            background: var(--pdm-surface);
            border: 1px solid var(--pdm-border);
            border-radius: 14px;
            padding: 0.7rem 0.9rem;
        }}
        [data-testid="stPageLink-NavLink"]:hover {{
            border-color: rgba(45, 212, 191, 0.55);
            background: rgba(45, 212, 191, 0.08);
        }}

        /* Dividers */
        hr {{
            border-color: var(--pdm-border);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    logger.info("Applied dark teal theme.")


def display_logo(logo_path: str = LOGO_PATH) -> None:
    """Displays the logo in the sidebar, or a short-name placeholder if missing."""
    if os.path.exists(logo_path):
        st.sidebar.image(logo_path, use_container_width=True)
        logger.info("Logo displayed from %s.", logo_path)
    else:
        st.sidebar.markdown(
            f'<div class="pdm-brand-title">{PRODUCT_NAME}</div>',
            unsafe_allow_html=True,
        )
        logger.warning("Logo not found at %s; showing name placeholder.", logo_path)


def render_sidebar_header(tagline: str = "using local RAG") -> None:
    """Renders logo, product name, and tagline (call before page-specific controls)."""
    display_logo()
    st.sidebar.markdown(
        f"""
        <div class="pdm-brand">
            <p class="pdm-brand-title">{PRODUCT_NAME}</p>
            <p class="pdm-brand-tag">{tagline}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    logger.info("Sidebar header rendered.")


def render_sidebar_footer() -> None:
    """Renders the copyright footer (call after page-specific controls)."""
    st.sidebar.markdown(
        f'<div class="pdm-footer">{COPYRIGHT}</div>',
        unsafe_allow_html=True,
    )


def render_sidebar(
    tagline: str = "using local RAG", *, show_footer: bool = True
) -> None:
    """Renders shared sidebar branding."""
    render_sidebar_header(tagline=tagline)
    if show_footer:
        render_sidebar_footer()


def page_header(title: str, subtitle: str = "") -> None:
    """Renders a consistent page title block."""
    st.markdown('<div class="pdm-pill">Local RAG</div>', unsafe_allow_html=True)
    st.title(title)
    if subtitle:
        st.markdown(f'<p class="pdm-lead">{subtitle}</p>', unsafe_allow_html=True)


def status_card(title: str, ok: bool, detail: str) -> None:
    """Renders a compact service status card."""
    status_class = "pdm-status-ok" if ok else "pdm-status-bad"
    status_label = "Online" if ok else "Offline"
    st.markdown(
        f"""
        <div class="pdm-card">
            <h3>{title}</h3>
            <p class="{status_class}">{status_label}</p>
            <p style="color:{COLOR_MUTED}; margin:0; font-size:0.9rem;">{detail}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
