from __future__ import annotations

import io

import pandas as pd
import streamlit as st

from dashboard.data import get_available_dates, load_cupom, load_di
from src.export import export_to_excel


def render() -> None:
    st.header("Download de Dados")

    di = load_di()
    cupom = load_cupom()

    if di.empty:
        st.warning("Nenhum dado disponível. Execute `python main.py --store` para popular os dados.")
        return

    dates = get_available_dates(di)
    min_date = pd.Timestamp(min(dates)).date()
    max_date = pd.Timestamp(max(dates)).date()

    col1, col2 = st.columns(2)
    with col1:
        start = st.date_input("Data inicial", value=min_date, min_value=min_date, max_value=max_date)
    with col2:
        end = st.date_input("Data final", value=max_date, min_value=min_date, max_value=max_date)

    if start > end:
        st.error("Data inicial deve ser anterior à data final.")
        return

    mask_di = (di["date"] >= pd.Timestamp(start)) & (di["date"] <= pd.Timestamp(end))
    mask_cu = (cupom["date"] >= pd.Timestamp(start)) & (cupom["date"] <= pd.Timestamp(end))
    di_filt = di[mask_di]
    cupom_filt = cupom[mask_cu]

    n_dates = di_filt["date"].nunique()
    st.caption(f"{n_dates} datas no período selecionado")

    if st.button("Gerar Excel", disabled=(n_dates == 0)):
        buf = io.BytesIO()
        export_to_excel(di_filt, cupom_filt, buf)
        buf.seek(0)
        st.download_button(
            label="⬇ Baixar Excel",
            data=buf,
            file_name=f"taxas_b3_{start}_{end}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
