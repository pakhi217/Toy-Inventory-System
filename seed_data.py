"""
seed_data.py — Populate the DB with realistic demo data.
Run once:  python seed_data.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import date, timedelta
import random

from utils.database import init_db
from utils.services import add_toy, stock_in, issue_toys

init_db()

TOYS = [
    ("Race Car Red",      "Vehicles",        date(2024,  1, 10)),
    ("Dino Rex",          "Action Figures",  date(2024,  2, 15)),
    ("Castle Builder",    "Building Blocks", date(2024,  3,  5)),
    ("Princess Ella",     "Dolls",           date(2024,  3, 20)),
    ("Math Wizard Board", "Educational",     date(2024,  4,  1)),
    ("Robot Rumble",      "Electronic Toys", date(2024,  4, 25)),
    ("Fluffy Bear",       "Plush / Soft Toys",date(2024, 5,  8)),
    ("Mega Puzzle 500",   "Puzzles",         date(2024,  5, 30)),
    ("Speed Drone X",     "Remote Control",  date(2024,  6, 12)),
    ("Jungle Swing Set",  "Outdoor Toys",    date(2024,  7,  3)),
    ("Knight Shield",     "Action Figures",  date(2024,  7, 18)),
    ("Space Lego Kit",    "Building Blocks", date(2024,  8,  2)),
    ("Baby Doll Sarah",   "Dolls",           date(2024,  8, 20)),
    ("Word Scramble",     "Educational",     date(2024,  9,  5)),
    ("Tiny RC Truck",     "Remote Control",  date(2024,  9, 22)),
]

DEPARTMENTS = [
    "Retail Dispatch", "Wholesale", "Export", "Showroom", "Gifting / CSR"
]

print("🌱 Seeding toys...")
for name, cat, mfg in TOYS:
    toy = add_toy(name, cat, 0, mfg, f"Demo entry for {name}")
    print(f"   Added #{toy.toy_id}: {name}")

print("\n📦 Seeding stock-in transactions...")
from utils.services import get_all_toys
all_toys = get_all_toys()

random.seed(42)
today = date.today()

for _, row in all_toys.iterrows():
    # 3–6 stock-in events over past 6 months
    for i in range(random.randint(3, 6)):
        tx_date = today - timedelta(days=random.randint(1, 180))
        qty     = random.randint(50, 300)
        batch   = f"BATCH-{tx_date.strftime('%Y%m')}-{random.randint(1,99):02d}"
        ok, msg = stock_in(int(row["toy_id"]), qty, tx_date, batch)
        if ok:
            print(f"   +{qty} → {row['toy_name']} on {tx_date}")

print("\n🚚 Seeding issue transactions...")
all_toys = get_all_toys()

for _, row in all_toys.iterrows():
    avail = int(row["current_stock"])
    for _ in range(random.randint(2, 5)):
        if avail < 5:
            break
        qty     = random.randint(1, min(avail // 2, 50))
        tx_date = today - timedelta(days=random.randint(0, 90))
        dept    = random.choice(DEPARTMENTS)
        ok, msg = issue_toys(int(row["toy_id"]), qty, dept, tx_date)
        if ok:
            avail -= qty
            print(f"   -{qty} from {row['toy_name']} → {dept} on {tx_date}")

print("\n✅ Seed complete. Run: streamlit run app.py --server.address 0.0.0.0")
