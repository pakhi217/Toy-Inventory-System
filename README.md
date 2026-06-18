# 🏭 ToyFactory IMS — Inventory Management System

A professional, factory-ready inventory management web app built with **Streamlit + SQLAlchemy + Plotly**.

---

## 📁 Project Structure

```
toy_inventory/
│
├── app.py                  ← Entry point (run this)
├── requirements.txt
├── seed_data.py            ← Optional: populate demo data
├── inventory.db            ← SQLite database (auto-created on first run)
│
├── utils/
│   ├── database.py         ← SQLAlchemy models & DB engine
│   ├── services.py         ← All business logic
│   └── ui_helpers.py       ← Shared CSS, KPI cards, export helpers
│
└── pages/
    ├── 01_Dashboard.py     ← KPIs, charts, low-stock alerts
    ├── 02_Toys.py          ← Toy catalogue CRUD
    ├── 03_Stock_In.py      ← Record manufactured inventory
    ├── 04_Issue.py         ← Dispatch toys to departments
    └── 05_Reports.py       ← Reports + Excel/CSV export
```

---

## ⚙️ Installation

### Step 1 — Prerequisites
- Python 3.10 or higher
- `pip` package manager

### Step 2 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 3 — (Optional) Load demo data

```bash
python seed_data.py
```

This adds 15 toy types with 6 months of realistic stock-in and dispatch history.

---

## 🚀 Running the App

### On a single machine (localhost only):
```bash
streamlit run app.py
```
Open: **http://localhost:8501**

### On factory LAN (all computers on same Wi-Fi/network):
```bash
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

Find your machine's IP address:
- **Windows:** Open CMD → `ipconfig` → look for `IPv4 Address`
- **Linux/Mac:** Open Terminal → `ifconfig` or `ip a`

Other computers on the same network open:
```
http://<YOUR-IP-ADDRESS>:8501
```
Example: `http://192.168.1.105:8501`

> **No login required** — all factory users get full access.

---

## 🔄 Upgrading to PostgreSQL

Only one line needs to change in `utils/database.py`:

```python
# Current (SQLite)
DB_URL = f"sqlite:///{os.path.abspath(DB_PATH)}"

# Replace with (PostgreSQL)
DB_URL = "postgresql+psycopg2://user:password@host:5432/dbname"
```

Install the PostgreSQL driver:
```bash
pip install psycopg2-binary
```

Remove the SQLite-only lines in `database.py`:
- `connect_args={"check_same_thread": False}`
- `poolclass=StaticPool`
- The `@event.listens_for` WAL block

---

## 🧩 Module Overview

| Module | What it does |
|--------|-------------|
| **Dashboard** | Real-time KPIs (toy types, total stock, today's movements, low-stock count), monthly production vs dispatch chart, category pie chart, 14-day sparkline |
| **Toy Catalogue** | Add/edit/delete/search toys with colour-coded stock levels (green/amber/red) |
| **Stock In** | Record newly manufactured units; auto-increments total & current stock; batch number support |
| **Dispatch** | Issue toys to departments with real-time stock check; blocks over-issue |
| **Reports** | Current inventory, issue history, date-wise movement — all exportable to Excel & CSV |

---

## 📊 Database Schema

```
toys
  toy_id             INTEGER  PRIMARY KEY AUTOINCREMENT
  toy_name           TEXT     NOT NULL
  category           TEXT     NOT NULL
  total_stock        INTEGER  (lifetime manufactured)
  current_stock      INTEGER  (on-hand)
  manufacturing_date DATE
  description        TEXT
  created_at         DATETIME
  updated_at         DATETIME

transactions
  transaction_id     INTEGER  PRIMARY KEY AUTOINCREMENT
  toy_id             INTEGER  FK → toys.toy_id  ON DELETE CASCADE
  transaction_type   ENUM     STOCK_IN | ISSUE
  quantity           INTEGER
  transaction_date   DATE
  batch_number       TEXT     (STOCK_IN only)
  issued_to          TEXT     (ISSUE only)
  remarks            TEXT
  created_at         DATETIME
```

---

## 🎨 UI Design Notes

- **Dark factory palette** — deep navy (#0F1117) with orange (#FF6B35) accents
- **Stock colour coding** — green (OK) / amber (≤ 20 units) / red (0 units)
- **Low-stock threshold** — configurable via `LOW_STOCK_THRESHOLD` in `services.py`
- All pages work on 1024px+ screens; sidebar navigation collapses on small screens

---
## STREAMLIT URL
https://toy-inventory-system-kemfwpobuhbhxwdkyqrcoy.streamlit.app/Toys

## 🛠️ Common Issues

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| Other computers can't connect | Use `--server.address 0.0.0.0`; check Windows Firewall allows port 8501 |
| Database locked (SQLite) | SQLite WAL mode is enabled; still limit to ~10 concurrent users |
| Want more concurrent users | Migrate to PostgreSQL (see above) |

