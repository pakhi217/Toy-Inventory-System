"""
ui_helpers.py — Shared Streamlit styling, KPI cards, and table renderers.
"""

import io
import streamlit as st
import pandas as pd


# ── Global CSS ────────────────────────────────────────────────────────────────

GLOBAL_CSS = """
<style>
/* ---- Palette ---- */
:root {
    --bg:        #0F1117;
    --surface:   #1C1F2E;
    --surface2:  #252A3D;
    --accent:    #FF6B35;       /* factory orange */
    --accent2:   #4ECDC4;       /* teal */
    --success:   #2ECC71;
    --warning:   #F39C12;
    --danger:    #E74C3C;
    --text:      #E8EAF0;
    --muted:     #8892A4;
    --border:    #2E3450;
}

/* ---- Base ---- */
.stApp { background: var(--bg); color: var(--text); font-family: 'Inter', sans-serif; }

/* ---- Sidebar ---- */
section[data-testid="stSidebar"] {
    background: var(--surface);
    border-right: 1px solid var(--border);
}
section[data-testid="stSidebar"] .stRadio label { color: var(--text) !important; }

/* ---- KPI Cards ---- */
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 16px; margin-bottom: 24px; }
.kpi-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px 16px;
    text-align: center;
    transition: border-color 0.2s;
}
.kpi-card:hover { border-color: var(--accent); }
.kpi-value { font-size: 2rem; font-weight: 700; color: var(--accent); line-height: 1; }
.kpi-label { font-size: 0.75rem; color: var(--muted); margin-top: 6px; letter-spacing: 0.08em; text-transform: uppercase; }
.kpi-sub   { font-size: 0.7rem; color: var(--accent2); margin-top: 4px; }

/* ---- Section header ---- */
.section-header {
    display: flex; align-items: center; gap: 10px;
    border-left: 4px solid var(--accent);
    padding-left: 12px;
    margin: 24px 0 16px;
}
.section-header h3 { margin: 0; font-size: 1.1rem; font-weight: 600; color: var(--text); }

/* ---- Alert badges ---- */
.badge-danger  { background: rgba(231,76,60,0.15); border: 1px solid var(--danger); border-radius: 6px; padding: 2px 8px; color: var(--danger); font-size: 0.75rem; font-weight: 600; }
.badge-warning { background: rgba(243,156,18,0.15); border: 1px solid var(--warning); border-radius: 6px; padding: 2px 8px; color: var(--warning); font-size: 0.75rem; font-weight: 600; }
.badge-ok      { background: rgba(46,204,113,0.15); border: 1px solid var(--success); border-radius: 6px; padding: 2px 8px; color: var(--success); font-size: 0.75rem; font-weight: 600; }

/* ---- Low-stock row highlight ---- */
.low-stock-row { color: var(--danger) !important; font-weight: 600; }

/* ---- Buttons ---- */
.stButton > button {
    background: var(--accent) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: opacity 0.2s !important;
}
.stButton > button:hover { opacity: 0.85 !important; }

/* ---- Forms ---- */
.stForm { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 20px; }

/* ---- DataFrames ---- */
.stDataFrame { background: var(--surface) !important; }
.stDataFrame thead th { background: var(--surface2) !important; color: var(--accent) !important; }

/* ---- Inputs ---- */
.stTextInput input, .stNumberInput input, .stSelectbox select, .stTextArea textarea {
    background: var(--surface2) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}

/* ---- Tab strip ---- */
.stTabs [data-baseweb="tab-list"] { background: var(--surface); border-radius: 10px; padding: 4px; }
.stTabs [data-baseweb="tab"] { color: var(--muted) !important; border-radius: 8px; }
.stTabs [aria-selected="true"] { background: var(--accent) !important; color: #fff !important; }

/* ---- Divider ---- */
hr { border-color: var(--border) !important; }
</style>
"""


def inject_css():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


# ── KPI card helpers ──────────────────────────────────────────────────────────

def kpi_card(value, label, sub="", color="var(--accent)") -> str:
    return f"""
<div class="kpi-card">
  <div class="kpi-value" style="color:{color}">{value}</div>
  <div class="kpi-label">{label}</div>
  {"<div class='kpi-sub'>" + sub + "</div>" if sub else ""}
</div>"""


def render_kpi_grid(kpis: list[dict]):
    """kpis = [{"value": ..., "label": ..., "sub": ..., "color": ...}]"""
    cards = "".join([
        kpi_card(k["value"], k["label"], k.get("sub", ""), k.get("color", "var(--accent)"))
        for k in kpis
    ])
    st.markdown(f'<div class="kpi-grid">{cards}</div>', unsafe_allow_html=True)


def section_header(icon: str, title: str):
    st.markdown(
        f'<div class="section-header"><span style="font-size:1.3rem">{icon}</span>'
        f'<h3>{title}</h3></div>',
        unsafe_allow_html=True,
    )


# ── DataFrame display ─────────────────────────────────────────────────────────

def show_df(df: pd.DataFrame, height: int = 400, hide_cols: list[str] | None = None):
    """Show a styled dataframe, optionally hiding columns."""
    if df is None or df.empty:
        st.info("No records found.")
        return
    display = df.copy()
    if hide_cols:
        display = display.drop(columns=[c for c in hide_cols if c in display.columns], errors="ignore")
    st.dataframe(display, use_container_width=True, height=height)


# ── Export helpers ────────────────────────────────────────────────────────────

def df_to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Report") -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return buf.getvalue()


def download_buttons(df: pd.DataFrame, base_name: str, sheet_name: str = "Report"):
    """Render Excel + CSV download buttons side by side."""
    if df is None or df.empty:
        return
    col1, col2, _ = st.columns([1, 1, 4])
    with col1:
        st.download_button(
            "⬇ Excel",
            data=df_to_excel_bytes(df, sheet_name),
            file_name=f"{base_name}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    with col2:
        st.download_button(
            "⬇ CSV",
            data=df.to_csv(index=False).encode(),
            file_name=f"{base_name}.csv",
            mime="text/csv",
        )
