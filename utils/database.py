"""
database.py — SQLAlchemy models and DB engine setup.
Designed to work with SQLite out of the box; swap DB_URL for PostgreSQL.
"""

import os
from datetime import datetime, date

from sqlalchemy import (
    create_engine, Column, Integer, String, Float,
    Date, DateTime, Text, Enum, ForeignKey, event
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.pool import StaticPool

# ── Connection ──────────────────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "inventory.db")
DB_URL  = f"sqlite:///{os.path.abspath(DB_PATH)}"
# For PostgreSQL, replace with:
# DB_URL = "postgresql+psycopg2://user:password@host:5432/dbname"

engine = create_engine(
    DB_URL,
    connect_args={"check_same_thread": False},   # SQLite-only; remove for PG
    poolclass=StaticPool,                          # SQLite-only; remove for PG
    echo=False,
)

# Enable WAL mode for better concurrent reads (SQLite-only)
@event.listens_for(engine, "connect")
def set_wal_mode(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


# ── Models ───────────────────────────────────────────────────────────────────

class Toy(Base):
    """Master toy catalogue."""
    __tablename__ = "toys"

    toy_id             = Column(Integer, primary_key=True, autoincrement=True)
    toy_name           = Column(String(200), nullable=False)
    category           = Column(String(100), nullable=False)
    total_stock        = Column(Integer, default=0, nullable=False)   # lifetime manufactured
    current_stock      = Column(Integer, default=0, nullable=False)   # on-hand
    manufacturing_date = Column(Date, default=date.today)
    description        = Column(Text, default="")
    created_at         = Column(DateTime, default=datetime.utcnow)
    updated_at         = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    transactions = relationship("Transaction", back_populates="toy", cascade="all, delete-orphan")


class Transaction(Base):
    """All stock movements — both inbound (STOCK_IN) and outbound (ISSUE)."""
    __tablename__ = "transactions"

    transaction_id   = Column(Integer, primary_key=True, autoincrement=True)
    toy_id           = Column(Integer, ForeignKey("toys.toy_id", ondelete="CASCADE"), nullable=False)
    transaction_type = Column(Enum("STOCK_IN", "ISSUE", name="tx_type"), nullable=False)
    quantity         = Column(Integer, nullable=False)
    transaction_date = Column(Date, default=date.today, nullable=False)
    batch_number     = Column(String(100), default="")    # STOCK_IN only
    issued_to        = Column(String(200), default="")    # ISSUE only
    remarks          = Column(Text, default="")
    created_at       = Column(DateTime, default=datetime.utcnow)

    toy = relationship("Toy", back_populates="transactions")


def init_db():
    """Create all tables if they don't exist yet."""
    Base.metadata.create_all(bind=engine)


def get_session():
    """Return a fresh DB session. Caller must close it."""
    return SessionLocal()
