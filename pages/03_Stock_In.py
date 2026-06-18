"""
pages/03_Stock_In.py — Record incoming manufactured stock.
"""

import streamlit as st
from datetime import date

from utils.services import get_toy_names_map, stock_in, get_transactions
from utils.ui_helpers import inject_css, section_header, show_df, download_buttons


def render():
    inject_css()
    st.title("📦 Stock In  —  Record Production")

    toys_map = get_toy_names_map()
    if not toys_map:
        st.warning("No toys registered yet. Go to **Toy Catalogue** to add toys first.")
        return

    # ── Entry form ────────────────────────────────────────────────────────────
    section_header("➕", "Add Manufactured Stock")
    toy_options = {f"#{tid} — {name}": tid for tid, name in toys_map.items()}

    with st.form("stock_in_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        toy_choice = c1.selectbox("Toy *", list(toy_options.keys()))
        qty        = c2.number_input("Quantity Added *", min_value=1, step=1, value=1)
        c3, c4     = st.columns(2)
        tx_date    = c3.date_input("Date", value=date.today())
        batch      = c4.text_input("Batch Number (optional)", placeholder="e.g. BATCH-2024-001")
        remarks    = st.text_area("Remarks (optional)", height=70)
        submitted  = st.form_submit_button("Record Stock In")

    if submitted:
        toy_id = toy_options[toy_choice]
        ok, msg = stock_in(toy_id, qty, tx_date, batch, remarks)
        if ok:
            st.success(msg)
        else:
            st.error(msg)

    # ── History ───────────────────────────────────────────────────────────────
    section_header("📋", "Stock In History")

    # Date filter
    fc1, fc2, _ = st.columns([1, 1, 3])
    start = fc1.date_input("From", value=date.today().replace(month=1, day=1))
    end   = fc2.date_input("To",   value=date.today())

    df = get_transactions(tx_type="STOCK_IN", start_date=start, end_date=end)
    if df.empty:
        st.info("No stock-in records for the selected period.")
    else:
        st.caption(f"{len(df)} record(s) | Total units received: **{df['quantity'].sum():,}**")
        show_df(
            df[["transaction_id", "toy_name", "category", "quantity",
                "date", "batch_number", "remarks", "recorded_at"]],
            height=400,
        )
        download_buttons(df, "stock_in_history", "Stock In")


render()
