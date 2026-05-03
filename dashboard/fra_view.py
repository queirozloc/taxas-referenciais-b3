from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.charts import plot_fra
from dashboard.data import load_di


def compute_fra(di_df: pd.DataFrame, t1_bd: int, t2_bd: int) -> pd.DataFrame:
    """
    Annualised forward rate between tenor t1_bd and t2_bd (business days, base 252).
    FRA(T1,T2) = [(1+r2/100)^(T2/252) / (1+r1/100)^(T1/252)]^(252/(T2-T1)) - 1
    """
    r1 = di_df[di_df["tenor"] == t1_bd][["date", "rate"]].rename(columns={"rate": "r1"})
    r2 = di_df[di_df["tenor"] == t2_bd][["date", "rate"]].rename(columns={"rate": "r2"})
    m = r1.merge(r2, on="date")
    m["rate"] = (
        ((1 + m["r2"] / 100) ** (t2_bd / 252) / (1 + m["r1"] / 100) ** (t1_bd / 252))
        ** (252 / (t2_bd - t1_bd))
        - 1
    ) * 100
    return m[["date", "rate"]].sort_values("date").reset_index(drop=True)


def render() -> None:
    st.header("Forward Rate Agreements (FRA)")
    st.markdown(
        "Taxas a termo calculadas diretamente dos vértices interpolados da curva DI. "
        "Indicadores de expectativas de médio/longo prazo do mercado."
    )

    di = load_di()
    if di.empty:
        st.warning("Nenhum dado disponível. Execute `python main.py --store` para popular os dados.")
        return

    fra_1y1y = compute_fra(di, 252, 504)    # taxa de 1 ano daqui a 1 ano
    fra_5y5y = compute_fra(di, 1260, 2520)  # taxa de 5 anos daqui a 5 anos

    if fra_1y1y.empty and fra_5y5y.empty:
        st.info("Dados insuficientes (verifique se os tenores 252/504/1260/2520 estão presentes).")
        return

    st.plotly_chart(plot_fra(fra_1y1y, fra_5y5y), use_container_width=True)

    st.subheader("Valores Recentes")
    n = 20
    col1, col2 = st.columns(2)
    with col1:
        if not fra_1y1y.empty:
            st.caption("FRA 1y1y (T1=252, T2=504)")
            display = fra_1y1y.tail(n).copy()
            display["date"] = pd.to_datetime(display["date"]).dt.strftime("%d/%m/%Y")
            st.dataframe(
                display.rename(columns={"date": "Data", "rate": "FRA 1y1y (%)"}).set_index("Data"),
            )
    with col2:
        if not fra_5y5y.empty:
            st.caption("FRA 5y5y (T1=1260, T2=2520)")
            display = fra_5y5y.tail(n).copy()
            display["date"] = pd.to_datetime(display["date"]).dt.strftime("%d/%m/%Y")
            st.dataframe(
                display.rename(columns={"date": "Data", "rate": "FRA 5y5y (%)"}).set_index("Data"),
            )
