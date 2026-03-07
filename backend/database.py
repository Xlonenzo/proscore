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

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)
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

    # clientes - columns that may be missing
    _add_col("clientes", "cidade", "VARCHAR(100) DEFAULT 'Sao Paulo'")
    _add_col("clientes", "bairro", "VARCHAR(100) DEFAULT ''")
    _add_col("clientes", "cep", "VARCHAR(10) DEFAULT ''")
    _add_col("clientes", "stripe_customer_id", "VARCHAR(255)")
    _add_col("clientes", "criado_em", "TIMESTAMP")

    # solicitacoes
    _add_col("solicitacoes", "payment_intent_id", "VARCHAR(255)")
    _add_col("solicitacoes", "pago", "BOOLEAN DEFAULT FALSE")
    _add_col("solicitacoes", "categoria", "VARCHAR(50) DEFAULT 'outros'")
    _add_col("solicitacoes", "endereco", "VARCHAR(255) DEFAULT ''")
    _add_col("solicitacoes", "bairro", "VARCHAR(100) DEFAULT ''")
    _add_col("solicitacoes", "preco_sugerido_min", "FLOAT DEFAULT 0.0")
    _add_col("solicitacoes", "preco_sugerido_max", "FLOAT DEFAULT 0.0")
    _add_col("solicitacoes", "preco_final", "FLOAT DEFAULT 0.0")
    _add_col("solicitacoes", "tempo_estimado_min", "INTEGER DEFAULT 0")
    _add_col("solicitacoes", "finalizado_em", "TIMESTAMP")

    # usuarios - additional columns
    _add_col("usuarios", "ativo", "BOOLEAN DEFAULT TRUE")
    _add_col("usuarios", "criado_em", "TIMESTAMP")
    _add_col("usuarios", "cliente_id", "INTEGER")
    _add_col("usuarios", "profissional_id", "INTEGER")
