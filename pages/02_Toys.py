"""
pages/02_Toys.py — Full toy catalogue CRUD.
"""

import streamlit as st
from datetime import date

from utils.services import (
    add_toy, update_toy, delete_toy,
    get_all_toys, get_toy_by_id, search_toys,
)
from utils.ui_helpers import inject_css, section_header, show_df, download_buttons

CATEGORIES = [
    "Action Figures", "Board Games", "Building Blocks", "Dolls",
    "Educational", "Electronic Toys", "Outdoor Toys", "Plush / Soft Toys",
    "Puzzles", "Remote Control", "Vehicles", "Other",
]


def render():
    inject_css()
    st.title("🧸 Toy Catalogue")

    tab_view, tab_add, tab_edit, tab_delete = st.tabs([
        "📋 View & Search", "➕ Add Toy", "✏️ Edit Toy", "🗑️ Delete Toy"
    ])

    # ── View & Search ─────────────────────────────────────────────────────────
    with tab_view:
        section_header("🔍", "Search Toys")
        c1, c2 = st.columns([3, 1])
        with c1:
            query = st.text_input("Search", placeholder="Type name, category, or ID…", label_visibility="collapsed")
        with c2:
            field = st.selectbox("Search by", ["all", "name", "category", "id"], label_visibility="collapsed")

        df = search_toys(query, field) if query else get_all_toys()
        st.caption(f"{len(df)} record(s) found")

        # Colour current_stock column
        if not df.empty:
            def style_stock(val):
                if val <= 0:
                    return "color: #E74C3C; font-weight: bold"
                if val <= 20:
                    return "color: #F39C12; font-weight: bold"
                return "color: #2ECC71"

            styled = df.style.map(style_stock, subset=["current_stock"])
            st.dataframe(styled, use_container_width=True, height=420)
        else:
            st.info("No toys found.")

        download_buttons(df, "toy_inventory", "Toys")

    # ── Add Toy ───────────────────────────────────────────────────────────────
    with tab_add:
        section_header("➕", "Register New Toy")
        with st.form("add_toy_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            name     = c1.text_input("Toy Name *")
            category = c2.selectbox("Category *", CATEGORIES)
            c3, c4   = st.columns(2)
            init_qty = c3.number_input("Initial Stock (units)", min_value=0, value=0)
            mfg_date = c4.date_input("Manufacturing Date", value=date.today())
            desc     = st.text_area("Description (optional)", height=80)
            submitted = st.form_submit_button("Register Toy")

        if submitted:
            if not name.strip():
                st.error("Toy Name is required.")
            else:
                toy = add_toy(name, category, init_qty, mfg_date, desc)
                st.success(f"✅ '{toy.toy_name}' registered with ID #{toy.toy_id}.")
                st.balloons()

    # ── Edit Toy ──────────────────────────────────────────────────────────────
    with tab_edit:
        section_header("✏️", "Update Toy Details")
        all_toys = get_all_toys()
        if all_toys.empty:
            st.info("No toys registered yet.")
        else:
            options = {f"#{r.toy_id} — {r.toy_name}": r.toy_id for r in all_toys.itertuples()}
            choice  = st.selectbox("Select toy to edit", list(options.keys()))
            sel_id  = options[choice]
            toy_obj = get_toy_by_id(sel_id)

            if toy_obj:
                with st.form("edit_toy_form"):
                    c1, c2 = st.columns(2)
                    new_name = c1.text_input("Toy Name", value=toy_obj.toy_name)
                    new_cat  = c2.selectbox(
                        "Category", CATEGORIES,
                        index=CATEGORIES.index(toy_obj.category) if toy_obj.category in CATEGORIES else 0,
                    )
                    c3, c4   = st.columns(2)
                    new_date = c3.date_input("Manufacturing Date", value=toy_obj.manufacturing_date)
                    new_desc = st.text_area("Description", value=toy_obj.description or "", height=80)
                    save     = st.form_submit_button("Save Changes")

                if save:
                    update_toy(sel_id, new_name, new_cat, new_date, new_desc)
                    st.success("✅ Toy updated successfully.")

    # ── Delete Toy ────────────────────────────────────────────────────────────
    with tab_delete:
        section_header("🗑️", "Remove Toy from Catalogue")
        all_toys = get_all_toys()
        if all_toys.empty:
            st.info("Nothing to delete.")
        else:
            options = {f"#{r.toy_id} — {r.toy_name}": r.toy_id for r in all_toys.itertuples()}
            choice  = st.selectbox("Select toy to delete", list(options.keys()), key="del_sel")
            sel_id  = options[choice]

            st.warning(
                "⚠️ Deleting a toy will also remove all its transaction history. This cannot be undone.",
                icon="⚠️",
            )
            confirm = st.checkbox("I understand and want to delete this toy.")
            if confirm:
                if st.button("Delete Toy", type="primary"):
                    delete_toy(sel_id)
                    st.success("✅ Toy deleted.")
                    st.rerun()


render()
