"""Database configuration and session management."""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./passa.db")

# Render uses postgres:// but SQLAlchemy needs postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from backend.models.models import (
        Profissional,
        Cliente,
        Servico,
        Avaliacao,
        SolicitacaoServico,
        Usuario,
        Pagamento,
    )
    Base.metadata.create_all(bind=engine)
    _migrate(engine)


def _migrate(eng):
    """Add columns that may be missing in existing databases."""
    from sqlalchemy import inspect, text
    insp = inspect(eng)
    if "usuarios" in insp.get_table_names():
        cols = [c["name"] for c in insp.get_columns("usuarios")]
        if "is_admin" not in cols:
            with eng.begin() as conn:
                conn.execute(text(
                    "ALTER TABLE usuarios ADD COLUMN is_admin BOOLEAN DEFAULT FALSE"
                ))
            print("[MIGRATE] Added is_admin column to usuarios")
