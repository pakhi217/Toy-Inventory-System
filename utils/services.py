"""
services.py — All business logic. UI pages import from here; never touch the DB directly.
"""

from datetime import date, datetime, timedelta
from typing import Optional

import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from utils.database import get_session, Toy, Transaction, init_db


# ── Toy CRUD ─────────────────────────────────────────────────────────────────

def add_toy(
    toy_name: str,
    category: str,
    initial_stock: int = 0,
    manufacturing_date: Optional[date] = None,
    description: str = "",
) -> Toy:
    db: Session = get_session()
    try:
        toy = Toy(
            toy_name=toy_name.strip(),
            category=category.strip(),
            total_stock=initial_stock,
            current_stock=initial_stock,
            manufacturing_date=manufacturing_date or date.today(),
            description=description.strip(),
        )
        db.add(toy)
        db.commit()
        db.refresh(toy)
        return toy
    finally:
        db.close()


def update_toy(
    toy_id: int,
    toy_name: Optional[str] = None,
    category: Optional[str] = None,
    manufacturing_date: Optional[date] = None,
    description: Optional[str] = None,
) -> Optional[Toy]:
    db: Session = get_session()
    try:
        toy = db.query(Toy).filter(Toy.toy_id == toy_id).first()
        if not toy:
            return None
        if toy_name is not None:
            toy.toy_name = toy_name.strip()
        if category is not None:
            toy.category = category.strip()
        if manufacturing_date is not None:
            toy.manufacturing_date = manufacturing_date
        if description is not None:
            toy.description = description.strip()
        toy.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(toy)
        return toy
    finally:
        db.close()


def delete_toy(toy_id: int) -> bool:
    db: Session = get_session()
    try:
        toy = db.query(Toy).filter(Toy.toy_id == toy_id).first()
        if not toy:
            return False
        db.delete(toy)
        db.commit()
        return True
    finally:
        db.close()


def get_all_toys() -> pd.DataFrame:
    db: Session = get_session()
    try:
        rows = db.query(Toy).order_by(Toy.toy_id).all()
        if not rows:
            return pd.DataFrame(columns=[
                "toy_id", "toy_name", "category",
                "total_stock", "current_stock",
                "manufacturing_date", "description", "created_at",
            ])
        return pd.DataFrame([{
            "toy_id":             r.toy_id,
            "toy_name":           r.toy_name,
            "category":           r.category,
            "total_stock":        r.total_stock,
            "current_stock":      r.current_stock,
            "manufacturing_date": r.manufacturing_date,
            "description":        r.description,
            "created_at":         r.created_at,
        } for r in rows])
    finally:
        db.close()


def get_toy_by_id(toy_id: int) -> Optional[Toy]:
    db: Session = get_session()
    try:
        return db.query(Toy).filter(Toy.toy_id == toy_id).first()
    finally:
        db.close()


def search_toys(query: str, field: str = "all") -> pd.DataFrame:
    """Search toys by name, category, or ID."""
    df = get_all_toys()
    if df.empty or not query.strip():
        return df
    q = query.strip().lower()
    if field == "name":
        mask = df["toy_name"].str.lower().str.contains(q, na=False)
    elif field == "category":
        mask = df["category"].str.lower().str.contains(q, na=False)
    elif field == "id":
        try:
            mask = df["toy_id"] == int(q)
        except ValueError:
            return df.iloc[0:0]
    else:  # "all"
        mask = (
            df["toy_name"].str.lower().str.contains(q, na=False)
            | df["category"].str.lower().str.contains(q, na=False)
            | df["toy_id"].astype(str).str.contains(q, na=False)
        )
    return df[mask].reset_index(drop=True)


# ── Stock In ─────────────────────────────────────────────────────────────────

def stock_in(
    toy_id: int,
    quantity: int,
    transaction_date: Optional[date] = None,
    batch_number: str = "",
    remarks: str = "",
) -> tuple[bool, str]:
    """Add stock. Returns (success, message)."""
    if quantity <= 0:
        return False, "Quantity must be greater than zero."
    db: Session = get_session()
    try:
        toy = db.query(Toy).filter(Toy.toy_id == toy_id).with_for_update().first()
        if not toy:
            return False, f"Toy ID {toy_id} not found."
        toy.current_stock += quantity
        toy.total_stock   += quantity
        toy.updated_at     = datetime.utcnow()
        tx = Transaction(
            toy_id=toy_id,
            transaction_type="STOCK_IN",
            quantity=quantity,
            transaction_date=transaction_date or date.today(),
            batch_number=batch_number.strip(),
            remarks=remarks.strip(),
        )
        db.add(tx)
        db.commit()
        return True, f"✅ {quantity} units added to '{toy.toy_name}'. Current stock: {toy.current_stock}."
    except Exception as e:
        db.rollback()
        return False, f"Error: {e}"
    finally:
        db.close()


# ── Issue / Dispatch ──────────────────────────────────────────────────────────

def issue_toys(
    toy_id: int,
    quantity: int,
    issued_to: str,
    issue_date: Optional[date] = None,
    remarks: str = "",
) -> tuple[bool, str]:
    """Issue (dispatch) toys. Returns (success, message)."""
    if quantity <= 0:
        return False, "Quantity must be greater than zero."
    if not issued_to.strip():
        return False, "Please specify who the toys are issued to."
    db: Session = get_session()
    try:
        toy = db.query(Toy).filter(Toy.toy_id == toy_id).with_for_update().first()
        if not toy:
            return False, f"Toy ID {toy_id} not found."
        if toy.current_stock < quantity:
            return False, (
                f"Insufficient stock. Requested: {quantity}, Available: {toy.current_stock}."
            )
        toy.current_stock -= quantity
        toy.updated_at     = datetime.utcnow()
        tx = Transaction(
            toy_id=toy_id,
            transaction_type="ISSUE",
            quantity=quantity,
            transaction_date=issue_date or date.today(),
            issued_to=issued_to.strip(),
            remarks=remarks.strip(),
        )
        db.add(tx)
        db.commit()
        return True, f"✅ {quantity} units of '{toy.toy_name}' issued to '{issued_to}'. Remaining: {toy.current_stock}."
    except Exception as e:
        db.rollback()
        return False, f"Error: {e}"
    finally:
        db.close()


# ── Transaction history ───────────────────────────────────────────────────────

def get_transactions(
    tx_type: Optional[str] = None,
    toy_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> pd.DataFrame:
    db: Session = get_session()
    try:
        q = db.query(Transaction, Toy.toy_name, Toy.category)\
              .join(Toy, Transaction.toy_id == Toy.toy_id)
        if tx_type:
            q = q.filter(Transaction.transaction_type == tx_type)
        if toy_id:
            q = q.filter(Transaction.toy_id == toy_id)
        if start_date:
            q = q.filter(Transaction.transaction_date >= start_date)
        if end_date:
            q = q.filter(Transaction.transaction_date <= end_date)
        rows = q.order_by(Transaction.transaction_date.desc(), Transaction.transaction_id.desc()).all()
        if not rows:
            return pd.DataFrame()
        records = []
        for tx, toy_name, category in rows:
            records.append({
                "transaction_id":   tx.transaction_id,
                "toy_id":           tx.toy_id,
                "toy_name":         toy_name,
                "category":         category,
                "type":             tx.transaction_type,
                "quantity":         tx.quantity,
                "date":             tx.transaction_date,
                "batch_number":     tx.batch_number,
                "issued_to":        tx.issued_to,
                "remarks":          tx.remarks,
                "recorded_at":      tx.created_at,
            })
        return pd.DataFrame(records)
    finally:
        db.close()


# ── Dashboard KPIs ───────────────────────────────────────────────────────────

LOW_STOCK_THRESHOLD = 20   # alert when current_stock <= this

def get_dashboard_kpis() -> dict:
    db: Session = get_session()
    try:
        total_toy_types = db.query(func.count(Toy.toy_id)).scalar() or 0
        total_stock     = db.query(func.sum(Toy.current_stock)).scalar() or 0
        low_stock_count = db.query(func.count(Toy.toy_id))\
                            .filter(Toy.current_stock <= LOW_STOCK_THRESHOLD)\
                            .scalar() or 0

        today_issued = db.query(func.sum(Transaction.quantity))\
                         .filter(
                             Transaction.transaction_type == "ISSUE",
                             Transaction.transaction_date == date.today(),
                         ).scalar() or 0

        today_in = db.query(func.sum(Transaction.quantity))\
                     .filter(
                         Transaction.transaction_type == "STOCK_IN",
                         Transaction.transaction_date == date.today(),
                     ).scalar() or 0

        return {
            "total_toy_types": total_toy_types,
            "total_stock":     int(total_stock),
            "low_stock_count": low_stock_count,
            "today_issued":    int(today_issued),
            "today_stock_in":  int(today_in),
        }
    finally:
        db.close()


def get_low_stock_toys() -> pd.DataFrame:
    db: Session = get_session()
    try:
        rows = db.query(Toy)\
                 .filter(Toy.current_stock <= LOW_STOCK_THRESHOLD)\
                 .order_by(Toy.current_stock)\
                 .all()
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame([{
            "toy_id":        r.toy_id,
            "toy_name":      r.toy_name,
            "category":      r.category,
            "current_stock": r.current_stock,
        } for r in rows])
    finally:
        db.close()


def get_monthly_summary(months: int = 6) -> pd.DataFrame:
    """Returns month-level aggregates of STOCK_IN and ISSUE quantities."""
    db: Session = get_session()
    try:
        start = date.today().replace(day=1) - timedelta(days=30 * (months - 1))
        rows = db.query(
            extract("year",  Transaction.transaction_date).label("year"),
            extract("month", Transaction.transaction_date).label("month"),
            Transaction.transaction_type,
            func.sum(Transaction.quantity).label("qty"),
        ).filter(Transaction.transaction_date >= start)\
         .group_by("year", "month", Transaction.transaction_type)\
         .order_by("year", "month")\
         .all()
        if not rows:
            return pd.DataFrame()
        records = []
        for r in rows:
            records.append({
                "month_label": f"{int(r.year)}-{int(r.month):02d}",
                "type":        r.transaction_type,
                "qty":         int(r.qty),
            })
        return pd.DataFrame(records)
    finally:
        db.close()


def get_category_stock() -> pd.DataFrame:
    db: Session = get_session()
    try:
        rows = db.query(
            Toy.category,
            func.sum(Toy.current_stock).label("stock"),
        ).group_by(Toy.category).all()
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame([{"category": r.category, "stock": int(r.stock)} for r in rows])
    finally:
        db.close()


def get_toy_names_map() -> dict:
    """Returns {toy_id: toy_name} for dropdowns."""
    db: Session = get_session()
    try:
        rows = db.query(Toy.toy_id, Toy.toy_name).order_by(Toy.toy_name).all()
        return {r.toy_id: r.toy_name for r in rows}
    finally:
        db.close()
