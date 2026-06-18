"""Custom CSS injected on top of config.toml's base dark theme."""

CUSTOM_CSS: str = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* Mac / Retina font smoothing */
* {
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

.stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', sans-serif !important;
}

/* Hide default Streamlit chrome */
#MainMenu { visibility: hidden !important; }
footer { visibility: hidden !important; }
[data-testid="stHeader"] { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }

/* Main content padding */
.main .block-container {
    padding-top: 1.25rem !important;
    padding-bottom: 2.5rem !important;
    max-width: 1440px !important;
}

/* ── Sidebar ─────────────────────────────────── */
[data-testid="stSidebar"] {
    border-right: 1px solid #1e2d3d !important;
}
[data-testid="stSidebar"] > div:first-child {
    padding: 1.25rem 1rem 1.5rem 1rem !important;
}

/* Sidebar section headers */
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    font-size: 0.6875rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    color: #475569 !important;
    margin-top: 1.5rem !important;
    margin-bottom: 0.5rem !important;
}

[data-testid="stSidebar"] hr {
    border-color: #1e2d3d !important;
    margin: 1rem 0 !important;
}

[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stMarkdown p {
    color: #94a3b8 !important;
    font-size: 0.8125rem !important;
}

/* ── Buttons ─────────────────────────────────── */
.stButton > button {
    border: 1px solid #1e2d3d !important;
    border-radius: 7px !important;
    font-family: 'Inter', -apple-system, sans-serif !important;
    font-size: 0.8125rem !important;
    font-weight: 500 !important;
    transition: border-color 0.15s ease, background-color 0.15s ease !important;
}
.stButton > button:hover {
    border-color: #3b82f6 !important;
    background-color: rgba(59, 130, 246, 0.1) !important;
}

.stDownloadButton > button {
    background: #1d4ed8 !important;
    border: none !important;
    border-radius: 7px !important;
    color: #fff !important;
    font-weight: 500 !important;
    transition: background-color 0.15s ease !important;
}
.stDownloadButton > button:hover {
    background: #2563eb !important;
}

/* ── Section headings ────────────────────────── */
h2, h3 {
    font-family: 'Inter', -apple-system, sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: -0.025em !important;
    color: #e2e8f0 !important;
}

/* ── DataFrames ──────────────────────────────── */
[data-testid="stDataFrame"] {
    border: 1px solid #1e2d3d;
    border-radius: 8px;
    overflow: hidden;
}

/* ── Alert boxes ─────────────────────────────── */
[data-testid="stAlert"] {
    border-radius: 8px !important;
}

/* ── Expander ────────────────────────────────── */
[data-testid="stExpander"] {
    border: 1px solid #1e2d3d !important;
    border-radius: 8px !important;
}
[data-testid="stExpander"] summary {
    font-size: 0.875rem !important;
    font-weight: 500 !important;
    color: #94a3b8 !important;
}

/* ── File uploader ───────────────────────────── */
[data-testid="stFileUploaderDropzone"] {
    border-color: #1e2d3d !important;
    border-radius: 8px !important;
}

/* ── Checkbox labels ─────────────────────────── */
[data-testid="stCheckbox"] label {
    font-size: 0.8125rem !important;
    color: #94a3b8 !important;
}

/* ── Scrollbar (WebKit / macOS Chrome/Safari) ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #1e2d3d; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #2d4060; }

/* ── macOS dark mode signal ──────────────────── */
@media (prefers-color-scheme: dark) {
    :root { color-scheme: dark; }
}
</style>
"""


def inject_styles() -> None:
    """Inject custom CSS overrides into the Streamlit page."""
    import streamlit as st
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
