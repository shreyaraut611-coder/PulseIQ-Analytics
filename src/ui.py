"""Small Streamlit helpers shared by every page."""
from __future__ import annotations

import streamlit as st

from views import AI_LABEL, CUTOFF_LABEL, freshness, months_available


def header(title: str, subtitle: str = "") -> None:
    st.set_page_config(page_title=f"PulseIQ | {title}", page_icon="📊", layout="wide")
    st.title(title)
    f = freshness()
    st.caption(f"{subtitle}  ·  Data cut-off: **{CUTOFF_LABEL}**  ·  Last refresh: {f['last_refresh']}  ·  "
               "Fictional training data (Zenith Nova Technologies)")


def month_selector(key: str, label: str = "Month") -> str:
    months = months_available()
    return st.selectbox(label, months, index=len(months) - 1, key=key)


def inr(v) -> str:
    try:
        v = float(v)
    except (TypeError, ValueError):
        return "–"
    if abs(v) >= 1e7:
        return f"₹{v / 1e7:,.2f} Cr"
    if abs(v) >= 1e5:
        return f"₹{v / 1e5:,.2f} L"
    return f"₹{v:,.0f}"


def ai_label() -> None:
    st.warning(f"🤖 **{AI_LABEL}.** These are model outputs (leads, not proof). A person must check them before acting.")


def note(text: str) -> None:
    st.info(f"💡 {text}")
