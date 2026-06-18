"""
pages/05_Reports.py — Inventory, issue-history, and date-wise stock reports.
"""

import streamlit as st
import plotly.express as px
from datetime import date, timedelta
import pandas as pd

from utils.services import get_all_toys, get_transactions
from utils.ui_helpers import inject_css, section_header, show_df, download_buttons

CHART_BG = "rgba(0,0,0,0)"
FONT_COL = "#E8EAF0"
GRID_COL = "#2E3450"


def render():
    inject_css()
    st.title("📑 Reports")

    tab1, tab2, tab3 = st.tabs([
        "🗂️ Current Inventory", "📤 Issue History", "📅 Date-wise Stock"
    ])

    # ── Report 1: Current Inventory ───────────────────────────────────────────
    with tab1:
        section_header("🗂️", "Current Inventory Report")
        df = get_all_toys()
        if df.empty:
            st.info("No toys registered yet.")
        else:
            # Summary stats
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Toy Types",  len(df))
            c2.metric("Total Units",       f"{df['current_stock'].sum():,}")
            c3.metric("Zero Stock Items",  int((df["current_stock"] == 0).sum()))
            c4.metric("Categories",        df["category"].nunique())

            # Category filter
            cats = ["All"] + sorted(df["category"].unique().tolist())
            sel_cat = st.selectbox("Filter by Category", cats)
            view = df if sel_cat == "All" else df[df["category"] == sel_cat]

            show_df(view[[
                "toy_id", "toy_name", "category",
                "total_stock", "current_stock", "manufacturing_date", "description"
            ]], height=450)
            download_buttons(view, f"inventory_report_{date.today()}", "Inventory")

            # Bar chart: top 15 by stock
            section_header("📊", "Top 15 Toys by Current Stock")
            top15 = view.nlargest(15, "current_stock")
            if not top15.empty:
                fig = px.bar(
                    top15, x="current_stock", y="toy_name",
                    orientation="h",
                    color="current_stock",
                    color_continuous_scale=["#FF6B35", "#4ECDC4"],
                    labels={"current_stock": "Units", "toy_name": ""},
                )
                fig.update_layout(
                    height=400,
                    paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
                    font_color=FONT_COL,
                    yaxis=dict(autorange="reversed"),
                    margin=dict(t=10, b=30, l=0, r=0),
                    coloraxis_showscale=False,
                )
                fig.update_xaxes(gridcolor=GRID_COL)
                st.plotly_chart(fig, use_container_width=True)

    # ── Report 2: Issue History ───────────────────────────────────────────────
    with tab2:
        section_header("📤", "Issue History Report")
        c1, c2 = st.columns(2)
        start = c1.date_input("From Date", value=date.today() - timedelta(days=30))
        end   = c2.date_input("To Date",   value=date.today())

        df_issue = get_transactions(tx_type="ISSUE", start_date=start, end_date=end)
        if df_issue.empty:
            st.info("No issue records for this period.")
        else:
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Dispatches",    len(df_issue))
            m2.metric("Total Units Issued",  f"{df_issue['quantity'].sum():,}")
            m3.metric("Unique Toys Issued",  df_issue["toy_name"].nunique())

            show_df(df_issue[[
                "transaction_id", "toy_name", "category",
                "quantity", "date", "issued_to", "remarks"
            ]], height=420)
            download_buttons(df_issue, f"issue_history_{start}_{end}", "Issue History")

            # Pie: issued by department
            section_header("🏢", "Dispatch by Department")
            dept_df = df_issue.groupby("issued_to")["quantity"].sum().reset_index()
            dept_df.columns = ["department", "units"]
            fig2 = px.pie(
                dept_df, values="units", names="department", hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Vivid,
            )
            fig2.update_layout(
                height=320, paper_bgcolor=CHART_BG, font_color=FONT_COL,
                margin=dict(t=10, b=10), showlegend=True,
            )
            st.plotly_chart(fig2, use_container_width=True)

    # ── Report 3: Date-wise stock movement ────────────────────────────────────
    with tab3:
        section_header("📅", "Date-wise Stock Movement")
        c1, c2 = st.columns(2)
        start3 = c1.date_input("From", value=date.today() - timedelta(days=30), key="dw_start")
        end3   = c2.date_input("To",   value=date.today(), key="dw_end")

        df_all = get_transactions(start_date=start3, end_date=end3)
        if df_all.empty:
            st.info("No transactions for this period.")
        else:
            df_all["date"] = pd.to_datetime(df_all["date"])
            daily = df_all.groupby(["date", "type"])["quantity"].sum().reset_index()
            pivot = daily.pivot_table(
                index="date", columns="type", values="quantity", fill_value=0
            ).reset_index()
            pivot.columns.name = None

            # Net movement column
            if "STOCK_IN" not in pivot.columns:
                pivot["STOCK_IN"] = 0
            if "ISSUE" not in pivot.columns:
                pivot["ISSUE"] = 0
            pivot["net_movement"] = pivot["STOCK_IN"] - pivot["ISSUE"]

            st.caption(
                f"Period totals — "
                f"Stock In: **{pivot['STOCK_IN'].sum():,}** | "
                f"Issued: **{pivot['ISSUE'].sum():,}** | "
                f"Net: **{pivot['net_movement'].sum():,}**"
            )

            show_df(pivot.rename(columns={
                "date": "Date", "STOCK_IN": "Units In",
                "ISSUE": "Units Issued", "net_movement": "Net Movement"
            }), height=380)
            download_buttons(pivot, f"datewise_stock_{start3}_{end3}", "Datewise Stock")

            # Line chart
            fig3 = px.line(
                daily, x="date", y="quantity", color="type",
                markers=True,
                color_discrete_map={"STOCK_IN": "#4ECDC4", "ISSUE": "#FF6B35"},
                labels={"quantity": "Units", "date": ""},
            )
            fig3.update_layout(
                height=300, paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
                font_color=FONT_COL, margin=dict(t=10, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
            )
            fig3.update_xaxes(gridcolor=GRID_COL)
            fig3.update_yaxes(gridcolor=GRID_COL)
            st.plotly_chart(fig3, use_container_width=True)


render()
