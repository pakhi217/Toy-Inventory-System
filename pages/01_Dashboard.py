"""
pages/01_Dashboard.py — Factory dashboard with KPIs and Plotly charts.
"""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.services import (
    get_dashboard_kpis,
    get_low_stock_toys,
    get_monthly_summary,
    get_category_stock,
    get_transactions,
    LOW_STOCK_THRESHOLD,
)
from utils.ui_helpers import (
    inject_css, render_kpi_grid, section_header, show_df
)

CHART_THEME = {
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor":  "rgba(0,0,0,0)",
    "font_color":    "#E8EAF0",
    "gridcolor":     "#2E3450",
    
}


def render():
    inject_css()
    st.title("🏭 Factory Inventory Dashboard")
    st.caption("Real-time overview — refreshes on every interaction")

    kpis = get_dashboard_kpis()

    # ── KPI row ──────────────────────────────────────────────────────────────
    render_kpi_grid([
        {"value": kpis["total_toy_types"], "label": "Toy Types",        "color": "var(--accent)"},
        {"value": f"{kpis['total_stock']:,}", "label": "Units in Stock", "color": "var(--accent2)"},
        {"value": kpis["today_issued"],    "label": "Issued Today",      "color": "#E74C3C"},
        {"value": kpis["today_stock_in"],  "label": "Received Today",    "color": "#2ECC71"},
        {
            "value": kpis["low_stock_count"],
            "label": "Low Stock Alerts",
            "color": "#F39C12" if kpis["low_stock_count"] > 0 else "#2ECC71",
            "sub":   f"≤ {LOW_STOCK_THRESHOLD} units",
        },
    ])

    # ── Charts ───────────────────────────────────────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        section_header("📊", "Monthly Production vs Dispatch")
        monthly = get_monthly_summary(months=6)
        if not monthly.empty:
            pivot = monthly.pivot_table(
                index="month_label", columns="type", values="qty", fill_value=0
            ).reset_index()
            fig = go.Figure()
            if "STOCK_IN" in pivot.columns:
                fig.add_bar(
                    x=pivot["month_label"], y=pivot["STOCK_IN"],
                    name="Stock In", marker_color="#4ECDC4",
                )
            if "ISSUE" in pivot.columns:
                fig.add_bar(
                    x=pivot["month_label"], y=pivot["ISSUE"],
                    name="Issued", marker_color="#FF6B35",
                )
            fig.update_layout(
                        barmode="group",
                        height=320,
                         margin=dict(t=10, b=30, l=0, r=0),
                        font=dict(
        color=CHART_THEME["font_color"]
    )
)
            fig.update_xaxes(gridcolor=CHART_THEME["gridcolor"])
            fig.update_yaxes(gridcolor=CHART_THEME["gridcolor"])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No transaction data yet.")

    with col_right:
        section_header("🗂️", "Stock by Category")
        cat_stock = get_category_stock()
        if not cat_stock.empty:
            fig2 = px.pie(
                cat_stock, values="stock", names="category",
                color_discrete_sequence=px.colors.qualitative.Bold,
                hole=0.45,
            )
            fig2.update_layout(
                height=320, margin=dict(t=10, b=10, l=0, r=0),
                paper_bgcolor=CHART_THEME["paper_bgcolor"],
                font_color=CHART_THEME["font_color"],
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2),
            )
            fig2.update_traces(textinfo="percent+label")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Add toys to see the category chart.")

    # ── Stock movement sparkline ──────────────────────────────────────────────
    section_header("📈", "Last 14-Day Stock Movement")
    import pandas as pd
    from datetime import date, timedelta

    df_tx = get_transactions()
    if not df_tx.empty:
        last14 = date.today() - timedelta(days=13)
        df_tx["date"] = pd.to_datetime(df_tx["date"])
        df_recent = df_tx[df_tx["date"] >= pd.Timestamp(last14)].copy()
        if not df_recent.empty:
            daily = (
                df_recent.groupby(["date", "type"])["quantity"]
                .sum().reset_index()
            )
            fig3 = px.line(
                daily, x="date", y="quantity", color="type",
                markers=True,
                color_discrete_map={"STOCK_IN": "#4ECDC4", "ISSUE": "#FF6B35"},
            )
            fig3.update_layout(
                height=260, margin=dict(t=10, b=30, l=0, r=0),
                paper_bgcolor=CHART_THEME["paper_bgcolor"],
                plot_bgcolor=CHART_THEME["plot_bgcolor"],
                font_color=CHART_THEME["font_color"],
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
            )
            fig3.update_xaxes(gridcolor=CHART_THEME["gridcolor"])
            fig3.update_yaxes(gridcolor=CHART_THEME["gridcolor"])
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("No transactions in the last 14 days.")
    else:
        st.info("No transaction history yet.")

    # ── Low stock alerts ──────────────────────────────────────────────────────
    section_header("⚠️", f"Low Stock Alerts  (≤ {LOW_STOCK_THRESHOLD} units)")
    low_df = get_low_stock_toys()
    if low_df.empty:
        st.success("All toys are adequately stocked.")
    else:
        st.warning(f"{len(low_df)} toy(s) need restocking.")
        show_df(low_df, height=200)


render()
