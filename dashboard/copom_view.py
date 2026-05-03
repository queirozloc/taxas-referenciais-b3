from __future__ import annotations

import io

import pandas as pd
import streamlit as st

from dashboard.charts import plot_copom_evolution, plot_copom_snapshot
from dashboard.data import get_available_dates, load_di_raw
from src.copom import COPOM_MEETINGS, build_copom_evolution, build_copom_snapshot


def _add_delta_bps(snapshot: pd.DataFrame, overnight_rate: float) -> pd.DataFrame:
    """Add 'delta_bps' column: change vs previous meeting (first meeting vs overnight Selic)."""
    prev_rates = [overnight_rate] + snapshot["implied_rate"].tolist()[:-1]
    snapshot = snapshot.copy()
    snapshot["delta_bps"] = (
        (snapshot["implied_rate"].values - prev_rates) * 100
    ).round(0).astype(int)
    return snapshot


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
        selected_date = st.selectbox(
            "Data de referência", dates,
            format_func=lambda d: pd.Timestamp(d).strftime("%d/%m/%Y"),
            key="copom_snap_date",
        )

        if selected_date is not None:
            day_data = di_raw[di_raw["date"] == pd.Timestamp(selected_date)]
            snapshot = build_copom_snapshot(day_data, selected_date)

            if snapshot.empty:
                st.info("Nenhuma reunião COPOM futura dentro do range da curva nesta data.")
            else:
                # overnight rate (DI1 = melhor proxy do Selic atual)
                overnight = day_data[day_data["tenor_bd"] == 1]["rate"].values
                anchor = float(overnight[0]) if len(overnight) > 0 else snapshot["implied_rate"].iloc[0]
                snapshot = _add_delta_bps(snapshot, anchor)

                st.plotly_chart(plot_copom_snapshot(snapshot, selected_date), use_container_width=True)

                display = snapshot.copy()
                display["meeting_date"] = display["meeting_date"].apply(
                    lambda d: pd.Timestamp(d).strftime("%d/%m/%Y")
                )
                display["implied_rate"] = display["implied_rate"].round(4)
                st.dataframe(
                    display.rename(columns={
                        "meeting_date": "Reunião",
                        "implied_rate": "Taxa Implícita (% a.a.)",
                        "delta_bps": "Variação (bps)",
                    }),
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

                col1, col2 = st.columns([1, 4])
                with col1:
                    csv = evolution.copy()
                    csv["curve_date"] = pd.to_datetime(csv["curve_date"]).dt.strftime("%Y-%m-%d")
                    st.download_button(
                        "⬇ Baixar CSV",
                        data=csv.to_csv(index=False),
                        file_name=f"copom_evolution_{selected_meeting}.csv",
                        mime="text/csv",
                    )
                with col2:
                    xlsx_buf = io.BytesIO()
                    with pd.ExcelWriter(xlsx_buf, engine="openpyxl") as writer:
                        evolution.to_excel(writer, index=False, sheet_name="Evolução COPOM")
                    xlsx_buf.seek(0)
                    st.download_button(
                        "⬇ Baixar Excel",
                        data=xlsx_buf,
                        file_name=f"copom_evolution_{selected_meeting}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
