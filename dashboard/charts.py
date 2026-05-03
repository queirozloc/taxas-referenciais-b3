from __future__ import annotations

from datetime import date

import pandas as pd
import plotly.graph_objects as go


def plot_yield_curve_overlay(
    curves: dict[str, pd.DataFrame],
    title: str = "Yield Curve",
    year_basis: int = 252,
) -> go.Figure:
    fig = go.Figure()
    for label, df in curves.items():
        fig.add_trace(go.Scatter(
            x=df["tenor"] / year_basis,
            y=df["rate"],
            mode="lines+markers",
            name=label,
            line=dict(shape="spline", smoothing=1.3),
            marker=dict(size=5),
            hovertemplate="%{x:.2f} anos: %{y:.4f}%<extra></extra>",
        ))
    fig.update_layout(
        title=title,
        xaxis_title="Tenor (anos)",
        yaxis_title="Taxa (% a.a.)",
        hovermode="x unified",
        template="plotly_white",
        legend=dict(orientation="h", y=-0.15),
    )
    return fig


def plot_copom_snapshot(snapshot_df: pd.DataFrame, reference_date) -> go.Figure:
    labels = [pd.Timestamp(d).strftime("%d/%m/%Y") for d in snapshot_df["meeting_date"]]
    fig = go.Figure(go.Bar(
        x=labels,
        y=snapshot_df["implied_rate"],
        text=snapshot_df["implied_rate"].round(2).astype(str) + "%",
        textposition="outside",
        marker_color="#1F4E79",
    ))
    fig.update_layout(
        title=f"Taxas Implícitas COPOM — {pd.Timestamp(reference_date).strftime('%d/%m/%Y')}",
        xaxis_title="Reunião COPOM",
        yaxis_title="Taxa Implícita (% a.a.)",
        template="plotly_white",
        yaxis=dict(range=[
            snapshot_df["implied_rate"].min() * 0.98,
            snapshot_df["implied_rate"].max() * 1.02,
        ]),
    )
    return fig


def plot_copom_evolution(evolution_df: pd.DataFrame, meeting_date) -> go.Figure:
    fig = go.Figure(go.Scatter(
        x=evolution_df["curve_date"],
        y=evolution_df["implied_rate"],
        mode="lines",
        line=dict(color="#1F4E79", width=2),
        hovertemplate="%{x|%d/%m/%Y}: %{y:.4f}%<extra></extra>",
    ))
    fig.update_layout(
        title=f"Evolução da Taxa Implícita — COPOM {pd.Timestamp(meeting_date).strftime('%d/%m/%Y')}",
        xaxis_title="Data",
        yaxis_title="Taxa Implícita (% a.a.)",
        template="plotly_white",
    )
    return fig


def plot_fra(fra_1y1y: pd.DataFrame, fra_5y5y: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=fra_1y1y["date"], y=fra_1y1y["rate"],
        mode="lines", name="FRA 1y1y",
        line=dict(color="#1F4E79", width=2),
        hovertemplate="%{x|%d/%m/%Y}: %{y:.4f}%<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=fra_5y5y["date"], y=fra_5y5y["rate"],
        mode="lines", name="FRA 5y5y",
        line=dict(color="#E74C3C", width=2),
        hovertemplate="%{x|%d/%m/%Y}: %{y:.4f}%<extra></extra>",
    ))
    fig.update_layout(
        title="Forward Rate Agreements — DI Curve",
        xaxis_title="Data",
        yaxis_title="Taxa (% a.a.)",
        hovermode="x unified",
        template="plotly_white",
        legend=dict(orientation="h", y=-0.15),
    )
    return fig
