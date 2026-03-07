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
    tables = insp.get_table_names()

    def _add_col(table, column, col_type):
        if table not in tables:
            return
        cols = [c["name"] for c in insp.get_columns(table)]
        if column not in cols:
            with eng.begin() as conn:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
            print(f"[MIGRATE] Added {column} to {table}")

    # usuarios
    _add_col("usuarios", "is_admin", "BOOLEAN DEFAULT FALSE")

    # profissionais - columns that may be missing
    _add_col("profissionais", "online", "BOOLEAN DEFAULT FALSE")
    _add_col("profissionais", "stripe_connect_id", "VARCHAR(255)")
    _add_col("profissionais", "descricao_servicos", "TEXT DEFAULT ''")
    _add_col("profissionais", "foto_url", "VARCHAR(255) DEFAULT ''")
    _add_col("profissionais", "total_reclamacoes", "INTEGER DEFAULT 0")
    _add_col("profissionais", "pontualidade", "FLOAT DEFAULT 100.0")
    _add_col("profissionais", "frequencia_uso", "FLOAT DEFAULT 0.0")
    _add_col("profissionais", "recorrencia", "FLOAT DEFAULT 0.0")
    _add_col("profissionais", "compliance", "FLOAT DEFAULT 100.0")
    _add_col("profissionais", "avaliacao_media", "FLOAT DEFAULT 0.0")

    # solicitacoes_servico
    _add_col("solicitacoes_servico", "payment_intent_id", "VARCHAR(255)")
    _add_col("solicitacoes_servico", "pago", "BOOLEAN DEFAULT FALSE")
