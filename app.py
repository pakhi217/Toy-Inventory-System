"""
app.py — Entry point. Initialises DB and renders the landing dashboard.
Run with:  streamlit run app.py --server.address 0.0.0.0 --server.port 8501
"""

import streamlit as st
from utils.database import init_db
from utils.ui_helpers import inject_css

# ── One-time DB bootstrap ─────────────────────────────────────────────────────
init_db()

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ToyFactory IMS",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

# ── Sidebar branding ──────────────────────────────────────────────────────────
st.sidebar.markdown(
    """
    <div style="text-align:center;padding:16px 0 24px">
      <div style="font-size:2.5rem">🏭</div>
      <div style="font-size:1.1rem;font-weight:700;color:#FF6B35;letter-spacing:0.05em">ToyFactory IMS</div>
      <div style="font-size:0.7rem;color:#8892A4;margin-top:4px">Inventory Management System</div>
    </div>
    <hr style="border-color:#2E3450;margin:0 0 16px">
    """,
    unsafe_allow_html=True,
)

# ── Landing / redirect hint ───────────────────────────────────────────────────
st.title("🏭 Welcome to ToyFactory IMS")
st.markdown(
    """
    Use the **sidebar navigation** to access each module:

    | Page | Purpose |
    |------|---------|
    | 📊 **Dashboard** | Live KPIs, charts, low-stock alerts |
    | 🧸 **Toys** | Add, edit, delete and search your toy catalogue |
    | 📦 **Stock In** | Record newly manufactured inventory |
    | 🚚 **Issue** | Dispatch toys to departments / retail |
    | 📑 **Reports** | Export inventory & movement reports |
    """,
    unsafe_allow_html=False,
)

st.info("👈 Click **Dashboard** in the sidebar to begin.", icon="ℹ️")
