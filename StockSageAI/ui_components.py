import streamlit as st
import os
from typing import Optional
from StockSageAI import responsive_ui

MOBILE_STYLES = responsive_ui.MOBILE_FIRST_STYLES


def render_primary_button(label: str, key: Optional[str] = None, full_width: bool = True) -> bool:
    """Render a primary-styled button. Returns True if clicked."""
    st.markdown(MOBILE_STYLES, unsafe_allow_html=True)
    if full_width:
        return st.button(label, key=key, use_container_width=True)
    return st.button(label, key=key)


def render_metric_card(label: str, value: str, delta: Optional[str] = None, trend: str = "neutral"):
    """Render a metric card using the shared CSS."""
    st.markdown(MOBILE_STYLES, unsafe_allow_html=True)
    color_map = {"up": "#10b981", "down": "#ef4444", "neutral": "#38bdf8"}
    color = color_map.get(trend, "#38bdf8")
    html = f"""
    <div class="metric-card" style="margin-bottom: 0.75rem;">
        <div class="metric-label">{label}</div>
        <div class="metric-value" style="color: {color}">{value}</div>
        {f'<div class="body-small" style="color: {color}">{delta}</div>' if delta else ''}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def input_text(label: str, key: str, placeholder: str = "", help: Optional[str] = None) -> str:
    """Wrapper for Streamlit text input with consistent help and styling."""
    st.markdown(MOBILE_STYLES, unsafe_allow_html=True)
    return st.text_input(label, placeholder=placeholder, key=key, help=help)


def input_number(label: str, key: str, value: float = 0.0, min_value: float = 0.0, step: float = 1.0, help: Optional[str] = None) -> float:
    st.markdown(MOBILE_STYLES, unsafe_allow_html=True)
    return st.number_input(label, value=value, min_value=min_value, step=step, key=key, help=help)


def save_uploaded_csv(uploaded, target_dir: str = None) -> Optional[str]:
    """Save uploaded CSV to a tmp directory and return path, or None."""
    if not uploaded:
        return None
    if target_dir is None:
        target_dir = os.path.join(os.path.dirname(__file__), "tmp")
    os.makedirs(target_dir, exist_ok=True)
    filename = uploaded.name.replace(" ", "_")
    path = os.path.join(target_dir, f"uploaded_{filename}")
    with open(path, "wb") as f:
        f.write(uploaded.getbuffer())
    st.success(f"✅ Saved: {filename}")
    return path


def training_status_card(status_text: str, progress: Optional[int] = None, updated_at: Optional[str] = None):
    st.markdown(MOBILE_STYLES, unsafe_allow_html=True)
    status_color = {
        'running': '#3b82f6',
        'completed': '#10b981',
        'failed': '#ef4444',
        'queued': '#f59e0b'
    }.get(status_text.lower(), '#38bdf8')
    prog_html = ''
    if progress is not None:
        prog_html = f'<div style="margin-top:0.5rem;">Progress: {progress}%</div>'
    updated_html = f'<div style="margin-top:0.25rem; color: #cbd5e1; font-size:0.85rem;">Last updated: {updated_at}</div>' if updated_at else ''
    st.markdown(f"""
    <div style='background: rgba(56, 189, 248, 0.05); padding: 1rem; border-radius: 8px; border-left: 4px solid {status_color};'>
        <strong>Status:</strong> {status_text}
        {prog_html}
        {updated_html}
    </div>
    """, unsafe_allow_html=True)
