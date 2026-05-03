from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.charts import plot_copom_evolution, plot_copom_snapshot
from dashboard.data import get_available_dates, load_di_raw
from src.copom import COPOM_MEETINGS, build_copom_evolution, build_copom_snapshot


def render() -> None:
    st.header("Estudo COPOM — Flat-Forward Copom (FFC)")

    di_raw = load_di_raw()
    if di_raw.empty:
        st.warning("Nenhum dado disponível. Execute `python main.py --store` para popular os dados.")
        return

    tab_snap, tab_evol = st.tabs(["Snapshot", "Evolução"])

    with tab_snap:
        st.markdown(
            "Taxas implícitas de cada reunião COPOM futura, calculadas via interpolação "
            "flat-forward nos pontos brutos da curva DI."
        )
        dates = get_available_dates(di_raw)
        selected_date = st.selectbox("Data de referência", dates,
                                     format_func=lambda d: pd.Timestamp(d).strftime("%d/%m/%Y"),
                                     key="copom_snap_date")
        if selected_date is not None:
            day_data = di_raw[di_raw["date"] == pd.Timestamp(selected_date)]
            snapshot = build_copom_snapshot(day_data, selected_date)
            if snapshot.empty:
                st.info("Nenhuma reunião COPOM futura dentro do range da curva nesta data.")
            else:
                st.plotly_chart(plot_copom_snapshot(snapshot, selected_date), use_container_width=True)
                display = snapshot.copy()
                display["meeting_date"] = display["meeting_date"].apply(
                    lambda d: pd.Timestamp(d).strftime("%d/%m/%Y")
                )
                st.dataframe(
                    display.rename(columns={"meeting_date": "Reunião", "implied_rate": "Taxa Implícita (%)"}),
                    hide_index=True,
                )

    with tab_evol:
        st.markdown(
            "Como o mercado foi precificando uma determinada reunião ao longo do tempo."
        )
        min_date = pd.Timestamp(di_raw["date"].min()).date()
        relevant = [m for m in COPOM_MEETINGS if m >= min_date]
        if not relevant:
            st.info("Nenhuma reunião disponível no período dos dados.")
            return

        selected_meeting = st.selectbox(
            "Reunião COPOM",
            relevant,
            format_func=lambda d: d.strftime("%d/%m/%Y"),
            key="copom_evol_meeting",
        )
        if selected_meeting is not None:
            with st.spinner("Calculando evolução..."):
                evolution = build_copom_evolution(di_raw, selected_meeting)
            if evolution.empty:
                st.info("Dados insuficientes para calcular a evolução desta reunião.")
            else:
                st.plotly_chart(plot_copom_evolution(evolution, selected_meeting), use_container_width=True)
