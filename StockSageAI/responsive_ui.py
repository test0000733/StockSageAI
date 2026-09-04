"""
Mobile-First Responsive UI & Dynamic Component System for SP 07
Ensures responsive design across all devices and platforms
"""

import streamlit as st
from typing import Callable, Optional, Dict, Any

# ============================================================================
# RESPONSIVE CSS FRAMEWORK
# ============================================================================

MOBILE_FIRST_STYLES = """
<style>
/* CSS Variables for theming */
:root {
    --primary-color: #7c3aed;
    --primary-2: #22d3ee;
    --primary-3: #a78bfa;
    --primary-dark: #1d4ed8;
    --danger-color: #f87171;
    --success-color: #34d399;
    --warning-color: #fbbf24;
    --bg-dark: #07111f;
    --bg-darker: #020817;
    --bg-panel: rgba(15, 23, 42, 0.8);
    --bg-panel-strong: rgba(15, 23, 42, 0.92);
    --text-primary: #e2e8f0;
    --text-secondary: #cbd5e1;
    --border-color: rgba(148, 163, 184, 0.22);
    --shadow-sm: 0 8px 22px rgba(15, 23, 42, 0.14);
    --shadow-md: 0 12px 26px rgba(60, 88, 179, 0.22);
    --shadow-lg: 0 18px 40px rgba(34, 211, 238, 0.15);
    --shadow-xl: 0 30px 80px rgba(124, 58, 237, 0.18);
    --radius-sm: 14px;
    --radius-md: 18px;
    --radius-lg: 24px;
}

/* Base Mobile-First Styles */
* {
    box-sizing: border-box;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

html, body {
    margin: 0;
    padding: 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
    background:
        radial-gradient(circle at top left, rgba(124, 58, 237, 0.20), transparent 35%),
        radial-gradient(circle at top right, rgba(34, 211, 238, 0.18), transparent 30%),
        linear-gradient(180deg, #020817 0%, #07111f 100%);
    color: var(--text-primary);
}

div[data-testid="stAppViewContainer"] {
    background: transparent;
}

div[data-testid="stAppViewContainer"] > .main {
    background: transparent;
}

section[data-testid="stSidebar"] {
    background: rgba(11, 18, 32, 0.92) !important;
    border-right: 1px solid var(--border-color);
    box-shadow: var(--shadow-md);
}

div.block-container {
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
    max-width: 1500px !important;
}

/* Premium glass cards */
.responsive-card,
.metric-card,
[data-testid="stMetric"] {
    background: linear-gradient(180deg, rgba(15, 23, 42, 0.82), rgba(15, 23, 42, 0.7));
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-sm);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
}

/* Buttons */
.responsive-btn,
button[kind="primary"],
button[kind="secondary"],
button[kind="tertiary"] {
    border-radius: 12px !important;
    border: 1px solid rgba(124, 58, 237, 0.35) !important;
    background: linear-gradient(135deg, rgba(124, 58, 237, 0.92), rgba(59, 130, 246, 0.82)) !important;
    color: white !important;
    box-shadow: var(--shadow-md);
    transition: transform 0.2s ease, box-shadow 0.2s ease, filter 0.2s ease;
    font-weight: 600;
}

.responsive-btn:hover,
button[kind="primary"]:hover,
button[kind="secondary"]:hover,
button[kind="tertiary"]:hover {
    transform: translateY(-1px);
    box-shadow: var(--shadow-lg);
    filter: brightness(1.06);
}

/* Inputs */
input, textarea, select, .stTextInput input, .stNumberInput input, .stSelectbox select {
    border-radius: 12px !important;
    border: 1px solid var(--border-color) !important;
    background: rgba(15, 23, 42, 0.7) !important;
    color: var(--text-primary) !important;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.05);
}

/* Metrics */
.metric-card {
    background: linear-gradient(135deg, rgba(124, 58, 237, 0.12), rgba(34, 211, 238, 0.06));
    border: 1px solid rgba(124, 58, 237, 0.18);
    border-radius: var(--radius-md);
    padding: clamp(1rem, 3vw, 1.5rem);
    text-align: center;
}

.metric-value {
    font-size: clamp(1.4rem, 4vw, 2.3rem);
    font-weight: 700;
    color: var(--primary-2);
    margin: 0.35rem 0;
}

.metric-label {
    font-size: clamp(0.75rem, 1.8vw, 0.9rem);
    color: var(--text-secondary);
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

/* Sections and cards */
section[data-testid="stFileUploader"],
section[data-testid="stForm"],
div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: var(--radius-md) !important;
}

/* Tables */
.table-responsive {
    width: 100%;
    overflow-x: auto;
    border-radius: var(--radius-md);
    border: 1px solid var(--border-color);
    background: rgba(15, 23, 42, 0.55);
}

.table-responsive table {
    width: 100%;
    border-collapse: collapse;
}

.table-responsive th {
    background: rgba(124, 58, 237, 0.10);
    padding: 0.8rem 1rem;
    border-bottom: 1px solid var(--border-color);
    color: var(--text-primary);
}

.table-responsive td {
    padding: 0.8rem 1rem;
    border-bottom: 1px solid rgba(148, 163, 184, 0.12);
    color: var(--text-secondary);
}

/* Premium page titles */
h1 {
    background: linear-gradient(90deg, #f8fafc 0%, #7dd3fc 22%, #c4b5fd 65%, #f9a8d4 100%);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    letter-spacing: -0.04em;
}

/* Mobile: Default - Single column, full width */
.responsive-container {
    padding: 1rem;
    width: 100%;
    max-width: 100%;
}

.responsive-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 1rem;
    width: 100%;
}

.responsive-flex {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    width: 100%;
}

/* Typography Responsive */
h1, .heading-1 {
    font-size: clamp(1.5rem, 5vw, 2.8rem);
    margin: 0.5rem 0;
    line-height: 1.2;
}

h2, .heading-2 {
    font-size: clamp(1.3rem, 4vw, 2.2rem);
    margin: 0.5rem 0;
}

h3, .heading-3 {
    font-size: clamp(1.1rem, 3vw, 1.8rem);
    margin: 0.5rem 0;
}

p, .body-text {
    font-size: clamp(0.9rem, 2vw, 1rem);
    line-height: 1.6;
    margin: 0.5rem 0;
}

.body-small {
    font-size: clamp(0.75rem, 1.5vw, 0.875rem);
    color: var(--text-secondary);
}

/* Button Responsive */
.responsive-btn {
    padding: clamp(0.5rem, 2vw, 0.75rem) clamp(1rem, 4vw, 1.5rem);
    font-size: clamp(0.9rem, 2vw, 1rem);
    border: none;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s ease;
    white-space: nowrap;
    min-height: 44px;
}

.responsive-btn:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
}

.responsive-btn:active {
    transform: translateY(0);
}

/* Input Fields Responsive */
.responsive-input {
    width: 100%;
    padding: clamp(0.75rem, 2vw, 1rem);
    font-size: clamp(0.9rem, 2vw, 1rem);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    background: rgba(15, 23, 42, 0.6);
    color: var(--text-primary);
    transition: all 0.2s ease;
}

.responsive-input:focus {
    outline: none;
    border-color: var(--primary-color);
    box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.1);
}

/* Cards Responsive */
.responsive-card {
    background: rgba(30, 41, 59, 0.8);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: clamp(1rem, 4vw, 1.5rem);
    transition: all 0.3s ease;
    backdrop-filter: blur(10px);
}

.responsive-card:hover {
    border-color: var(--primary-color);
    box-shadow: var(--shadow-lg);
}

/* Metrics/Stats Responsive */
.metric-card {
    background: linear-gradient(135deg, rgba(56, 189, 248, 0.1), rgba(168, 85, 247, 0.05));
    border: 1px solid rgba(56, 189, 248, 0.2);
    border-radius: 12px;
    padding: clamp(1rem, 3vw, 1.5rem);
    text-align: center;
}

.metric-value {
    font-size: clamp(1.5rem, 6vw, 2.5rem);
    font-weight: 700;
    color: var(--primary-color);
    margin: 0.5rem 0;
}

.metric-label {
    font-size: clamp(0.8rem, 2vw, 0.95rem);
    color: var(--text-secondary);
}

/* Tables Responsive */
.table-responsive {
    width: 100%;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
}

.table-responsive table {
    width: 100%;
    font-size: clamp(0.8rem, 1.5vw, 0.95rem);
    border-collapse: collapse;
}

.table-responsive th {
    background: rgba(56, 189, 248, 0.1);
    padding: clamp(0.5rem, 2vw, 0.75rem);
    text-align: left;
    border-bottom: 2px solid var(--border-color);
}

.table-responsive td {
    padding: clamp(0.5rem, 2vw, 0.75rem);
    border-bottom: 1px solid var(--border-color);
}

/* Forms Responsive */
.form-group {
    margin-bottom: clamp(1rem, 3vw, 1.5rem);
    width: 100%;
}

.form-label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    font-size: clamp(0.9rem, 2vw, 1rem);
}

/* Navigation Responsive */
.responsive-nav {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    width: 100%;
    overflow-x: auto;
    padding: 0.5rem 0;
}

.nav-item {
    white-space: nowrap;
    padding: 0.5rem 1rem;
    border-radius: 8px;
    background: rgba(56, 189, 248, 0.1);
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: clamp(0.85rem, 2vw, 0.95rem);
}

.nav-item:hover {
    background: rgba(56, 189, 248, 0.2);
}

/* Tablet: Medium screens - 2 columns */
@media (min-width: 640px) {
    .responsive-grid {
        grid-template-columns: repeat(2, 1fr);
    }

    .responsive-flex {
        flex-direction: row;
    }

    .responsive-container {
        padding: 1.5rem;
        max-width: 100%;
    }

    .metric-card {
        padding: 1.5rem;
    }
}

/* Desktop: Large screens - 3+ columns */
@media (min-width: 1024px) {
    .responsive-grid {
        grid-template-columns: repeat(3, 1fr);
    }

    .responsive-container {
        padding: 2rem;
        max-width: 1400px;
        margin: 0 auto;
    }

    .form-group {
        display: inline-block;
        width: calc(50% - 0.5rem);
        margin-right: 1rem;
    }

    .form-group:nth-child(even) {
        margin-right: 0;
    }
}

/* Extra large screens */
@media (min-width: 1440px) {
    .responsive-grid {
        grid-template-columns: repeat(4, 1fr);
    }

    .responsive-container {
        max-width: 1600px;
    }
}

/* Touch-friendly interactions */
@media (hover: none) and (pointer: coarse) {
    .responsive-btn {
        min-height: 48px;
        padding: 0.75rem 1.5rem;
    }

    .responsive-input {
        padding: 1rem;
        font-size: 16px; /* Prevents zoom on iOS */
    }

    .nav-item {
        padding: 0.75rem 1.25rem;
        min-height: 44px;
    }
}

/* Print styles */
@media print {
    .responsive-btn, .nav-item, .form-group {
        display: none;
    }

    .responsive-card {
        page-break-inside: avoid;
    }
}

/* Animation & Transitions */
@keyframes slideInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

.animate-in {
    animation: slideInUp 0.4s ease-out;
}

.fade-in {
    animation: fadeIn 0.3s ease-out;
}
</style>
"""


# ============================================================================
# DYNAMIC COMPONENT SYSTEM
# ============================================================================

class DynamicComponents:
    """Dynamic component rendering system"""

    @staticmethod
    def render_responsive_metric(label: str, value: str, change: Optional[str] = None, trend: str = "neutral"):
        """Render responsive metric card"""
        st.markdown(MOBILE_FIRST_STYLES, unsafe_allow_html=True)

        color = "success" if trend == "up" else "danger" if trend == "down" else "neutral"
        color_map = {"success": "#10b981", "danger": "#ef4444", "neutral": "#38bdf8"}

        html = f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value" style="color: {color_map[color]}">{value}</div>
            {f'<div class="body-small" style="color: {color_map[color]}">{change}</div>' if change else ''}
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)

    @staticmethod
    def render_responsive_table(data: list, columns: list):
        """Render responsive table"""
        st.markdown(MOBILE_FIRST_STYLES, unsafe_allow_html=True)

        html = '<div class="table-responsive"><table><thead><tr>'
        for col in columns:
            html += f'<th>{col}</th>'
        html += '</tr></thead><tbody>'

        for row in data:
            html += '<tr>'
            for item in row:
                html += f'<td>{item}</td>'
            html += '</tr>'

        html += '</tbody></table></div>'
        st.markdown(html, unsafe_allow_html=True)

    @staticmethod
    def render_button_group(buttons: Dict[str, Callable]):
        """Render responsive button group"""
        cols = st.columns(len(buttons))
        for col, (label, callback) in zip(cols, buttons.items()):
            with col:
                if st.button(label, width='stretch', key=f"btn_{label}"):
                    callback()


# ============================================================================
# MOBILE-OPTIMIZED LAYOUT HELPERS
# ============================================================================

def get_responsive_columns(count: int, mobile_count: int = 1, **kwargs) -> tuple:
    """Get responsive column layout."""
    # Use the configured column count consistently so calling code that unpacks
    # multiple columns remains stable across screen sizes.
    return st.columns(count, **kwargs)


def render_mobile_navbar(nav_items: Dict[str, Callable]):
    """Render mobile-friendly navigation bar"""
    st.markdown(MOBILE_FIRST_STYLES, unsafe_allow_html=True)

    cols = st.columns(len(nav_items))
    for col, (label, callback) in zip(cols, nav_items.items()):
        with col:
            if st.button(label, width='stretch'):
                callback()


def ensure_viewport_width(default_width: int = 1024):
    """Detect viewport width in the browser and store it in session state."""
    # If session_state already has a value, do nothing.
    try:
        if 'viewport_width' in st.session_state:
            return
    except Exception:
        # session_state may not be functional outside `streamlit run`.
        return

    # Safely attempt to read query params; some Streamlit versions or
    # execution contexts may not expose experimental_get_query_params.
    query_params = {}
    try:
        if hasattr(st, 'experimental_get_query_params'):
            query_params = st.experimental_get_query_params() or {}
    except Exception:
        query_params = {}

    if 'vw' in query_params:
        try:
            st.session_state['viewport_width'] = int(float(query_params['vw'][0]))
        except Exception:
            st.session_state['viewport_width'] = default_width
        return

    # Try injecting JS to capture viewport width when running inside Streamlit.
    try:
        # Build a data URL containing the small JS snippet and render it in an iframe.
        # Using an iframe avoids the deprecated `components.html` API.
        import urllib.parse

        js = """
        <script>
        const params = new URLSearchParams(window.location.search);
        params.set('vw', window.innerWidth);
        window.location.search = params.toString();
        </script>
        """

        data_url = "data:text/html;charset=utf-8," + urllib.parse.quote(js)
        st.iframe(data_url, height=0)

        # After injecting script, request a rerun so Streamlit reloads with vw param.
        try:
            st.stop()
        except Exception:
            # If st.stop is unavailable or raises (non-Streamlit run), ignore.
            pass
    except Exception:
        # If iframe injection fails (non-Streamlit runtime), skip silently.
        return
