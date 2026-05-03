import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

st.set_page_config(
    page_title="Taxas Referenciais B3",
    page_icon="📈",
    layout="wide",
)

st.sidebar.title("Taxas Referenciais B3")
section = st.sidebar.radio(
    "Navegação",
    ["Yield Curve", "Download", "COPOM", "FRA"],
    label_visibility="collapsed",
)
st.sidebar.markdown("---")
st.sidebar.caption("Fonte: B3 — Taxas Referenciais  \nDI Curve · Cupom Cambial Limpo")

if section == "Yield Curve":
    from dashboard.yield_curve_view import render
    render()
elif section == "Download":
    from dashboard.download_view import render
    render()
elif section == "COPOM":
    from dashboard.copom_view import render
    render()
elif section == "FRA":
    from dashboard.fra_view import render
    render()
