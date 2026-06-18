"""
pages/04_Issue.py — Dispatch / issue toys to departments.
"""

import streamlit as st
from datetime import date

from utils.services import (
    get_toy_names_map, get_toy_by_id,
    issue_toys, get_transactions,
)
from utils.ui_helpers import inject_css, section_header, show_df, download_buttons

DEPARTMENTS = [
    "Retail Dispatch", "Wholesale", "Quality Control",
    "Showroom", "Export", "Gifting / CSR", "Internal Use", "Other",
]


def render():
    inject_css()
    st.title("🚚 Toy Dispatch  —  Issue Management")

    toys_map = get_toy_names_map()
    if not toys_map:
        st.warning("No toys registered yet. Go to **Toy Catalogue** to add toys first.")
        return

    toy_options = {f"#{tid} — {name}": tid for tid, name in toys_map.items()}

    # ── Live stock preview ────────────────────────────────────────────────────
    section_header("👁️", "Check Current Stock")
    preview_choice = st.selectbox("Select toy to preview stock", list(toy_options.keys()), key="preview")
    preview_toy    = get_toy_by_id(toy_options[preview_choice])
    if preview_toy:
        avail = preview_toy.current_stock
        color = "#2ECC71" if avail > 20 else ("#F39C12" if avail > 0 else "#E74C3C")
        st.markdown(
            f'<div style="background:#1C1F2E;border:1px solid #2E3450;border-radius:10px;'
            f'padding:14px 20px;margin-bottom:16px;">'
            f'<span style="color:#8892A4;font-size:0.8rem">AVAILABLE STOCK</span><br>'
            f'<span style="font-size:2rem;font-weight:700;color:{color}">{avail:,}</span>'
            f' <span style="color:#8892A4">units</span></div>',
            unsafe_allow_html=True,
        )

    # ── Issue form ────────────────────────────────────────────────────────────
    section_header("📤", "Issue Toys")
    with st.form("issue_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        toy_choice  = c1.selectbox("Toy *", list(toy_options.keys()))
        qty         = c2.number_input("Quantity to Issue *", min_value=1, step=1, value=1)
        c3, c4      = st.columns(2)
        issue_date  = c3.date_input("Issue Date", value=date.today())
        issued_to   = c4.text_input("Issued To / Department *", placeholder="e.g. Retail Dispatch")
        dept_quick  = st.selectbox("Quick-select Department", ["— type above —"] + DEPARTMENTS)
        remarks     = st.text_area("Remarks (optional)", height=70)
        submitted   = st.form_submit_button("Issue Toys")

    if submitted:
        final_dept = issued_to.strip() or (dept_quick if dept_quick != "— type above —" else "")
        toy_id     = toy_options[toy_choice]
        ok, msg    = issue_toys(toy_id, qty, final_dept, issue_date, remarks)
        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)

    # ── History ───────────────────────────────────────────────────────────────
    section_header("📋", "Issue History")
    fc1, fc2, _ = st.columns([1, 1, 3])
    start = fc1.date_input("From", value=date.today().replace(month=1, day=1))
    end   = fc2.date_input("To",   value=date.today())

    df = get_transactions(tx_type="ISSUE", start_date=start, end_date=end)
    if df.empty:
        st.info("No issue records for the selected period.")
    else:
        st.caption(f"{len(df)} dispatch(es) | Total units issued: **{df['quantity'].sum():,}**")
        show_df(
            df[["transaction_id", "toy_name", "category", "quantity",
                "date", "issued_to", "remarks", "recorded_at"]],
            height=400,
        )
        download_buttons(df, "issue_history", "Issues")


render()
