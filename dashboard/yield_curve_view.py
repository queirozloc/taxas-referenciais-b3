from __future__ import annotations

from datetime import timedelta

import pandas as pd
import streamlit as st

from dashboard.charts import plot_yield_curve_overlay
from dashboard.data import get_available_dates, load_cupom, load_di


def _closest(dates: list, target) -> object | None:
    if not dates:
        return None
    ts = pd.Timestamp(target)
    return min(dates, key=lambda d: abs(pd.Timestamp(d) - ts))


def render() -> None:
    st.header("Yield Curve")

    curve_type = st.radio("Curva", ["DI", "Cupom Cambial Limpo"], horizontal=True)
    is_di = curve_type == "DI"
    df = load_di() if is_di else load_cupom()
    year_basis = 252 if is_di else 360
    title = "DI Curve (dias úteis, base 252)" if is_di else "Cupom Cambial Limpo (dias corridos, base 360)"

    if df.empty:
        st.warning("Nenhum dado disponível. Execute `python main.py --store` para popular os dados.")
        return

    dates = get_available_dates(df)
    latest = dates[0]

    col_ctrl, col_chart = st.columns([1, 3])
    selected: dict[str, pd.DataFrame] = {}

    with col_ctrl:
        st.markdown("**Selecionar datas**")

        def _add(label: str, target):
            d = _closest(dates, target)
            if d is not None:
                day_df = df[df["date"] == pd.Timestamp(d)][["tenor", "rate"]]
                if not day_df.empty:
                    selected[label.format(date=pd.Timestamp(d).strftime("%d/%m/%Y"))] = day_df

        if st.checkbox("Última data", value=True):
            _add("Última ({date})", latest)

        if st.checkbox("1 semana atrás"):
            _add("1 semana ({date})", pd.Timestamp(latest) - timedelta(weeks=1))

        if st.checkbox("1 mês atrás"):
            _add("1 mês ({date})", pd.Timestamp(latest) - timedelta(days=30))

        if st.checkbox("1 ano atrás"):
            _add("1 ano ({date})", pd.Timestamp(latest) - timedelta(days=365))

        custom = st.date_input("Data customizada", value=None)
        if custom:
            _add("Custom ({date})", custom)

    with col_chart:
        if selected:
            st.plotly_chart(
                plot_yield_curve_overlay(selected, title=title, year_basis=year_basis),
                use_container_width=True,
            )
        else:
            st.info("Selecione pelo menos uma data à esquerda.")

    if selected:
        st.subheader("Tabela")
        tabs = st.tabs(list(selected.keys()))
        for tab, (label, day_df) in zip(tabs, selected.items()):
            with tab:
                display = day_df.copy()
                display["tenor_anos"] = (display["tenor"] / year_basis).round(3)
                st.dataframe(
                    display[["tenor", "tenor_anos", "rate"]]
                    .rename(columns={"tenor": "Tenor (dias)", "tenor_anos": "Tenor (anos)", "rate": "Taxa (%)"}),
                    hide_index=True,
                )
