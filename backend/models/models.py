"""Database models for PASSA."""
import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Boolean,
    ForeignKey,
    Text,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from backend.database import Base
import enum


class StatusServico(str, enum.Enum):
    PENDENTE = "pendente"
    ACEITO = "aceito"
    EM_ANDAMENTO = "em_andamento"
    CONCLUIDO = "concluido"
    CANCELADO = "cancelado"


class CategoriaServico(str, enum.Enum):
    ELETRICA = "eletrica"
    HIDRAULICA = "hidraulica"
    PINTURA = "pintura"
    MONTAGEM = "montagem"
    LIMPEZA = "limpeza"
    JARDINAGEM = "jardinagem"
    REFORMA = "reforma"
    MANUTENCAO = "manutencao"
    OUTROS = "outros"


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    senha_hash = Column(String(255), nullable=False)
    nome = Column(String(100), nullable=False)
    tipo = Column(String(20), nullable=False)  # "cliente" or "prestador"
    is_admin = Column(Boolean, default=False)
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.datetime.utcnow)

    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=True)
    profissional_id = Column(Integer, ForeignKey("profissionais.id"), nullable=True)

    cliente = relationship("Cliente", foreign_keys=[cliente_id])
    profissional = relationship("Profissional", foreign_keys=[profissional_id])


class Profissional(Base):
    __tablename__ = "profissionais"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    telefone = Column(String(20), nullable=False)
    cpf = Column(String(14), unique=True, nullable=True)
    categoria = Column(String(50), nullable=False)
    especialidades = Column(Text, default="")
    descricao_servicos = Column(Text, default="")
    regiao = Column(String(100), default="")
    foto_url = Column(String(255), default="")
    documento_verificado = Column(Boolean, default=False)
    antecedentes_ok = Column(Boolean, default=False)
    certificacoes = Column(Text, default="")
    score = Column(Float, default=500.0)
    total_servicos = Column(Integer, default=0)
    taxa_conclusao = Column(Float, default=100.0)
    tempo_medio_min = Column(Float, default=0.0)
    avaliacao_media = Column(Float, default=0.0)
    total_reclamacoes = Column(Integer, default=0)
    pontualidade = Column(Float, default=100.0)
    frequencia_uso = Column(Float, default=0.0)
    recorrencia = Column(Float, default=0.0)
    compliance = Column(Float, default=100.0)
    stripe_connect_id = Column(String(255), nullable=True)
    online = Column(Boolean, default=False)
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.datetime.utcnow)
    atualizado_em = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    servicos = relationship("SolicitacaoServico", back_populates="profissional")
    avaliacoes = relationship("Avaliacao", back_populates="profissional")


class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    telefone = Column(String(20), nullable=False)
    endereco = Column(String(255), nullable=False)
    cidade = Column(String(100), default="São Paulo")
    bairro = Column(String(100), default="")
    cep = Column(String(10), default="")
    stripe_customer_id = Column(String(255), nullable=True)
    criado_em = Column(DateTime, default=datetime.datetime.utcnow)

    solicitacoes = relationship("SolicitacaoServico", back_populates="cliente")
    avaliacoes = relationship("Avaliacao", back_populates="cliente")


class Servico(Base):
    __tablename__ = "servicos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    categoria = Column(String(50), nullable=False)
    descricao = Column(Text, default="")
    preco_base = Column(Float, nullable=False)
    preco_min = Column(Float, nullable=False)
    preco_max = Column(Float, nullable=False)
    tempo_estimado_min = Column(Integer, nullable=False)
    complexidade = Column(Integer, default=1)  # 1-5
    palavras_chave = Column(Text, default="")


class SolicitacaoServico(Base):
    __tablename__ = "solicitacoes"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=True)
    profissional_id = Column(
        Integer, ForeignKey("profissionais.id"), nullable=True
    )
    descricao = Column(Text, nullable=False)
    categoria = Column(String(50), default="outros")
    endereco = Column(String(255), default="")
    cidade = Column(String(100), default="São Paulo")
    bairro = Column(String(100), default="")
    urgente = Column(Boolean, default=False)
    preco_sugerido_min = Column(Float, default=0.0)
    preco_sugerido_max = Column(Float, default=0.0)
    preco_final = Column(Float, default=0.0)
    tempo_estimado_min = Column(Integer, default=0)
    status = Column(String(20), default=StatusServico.PENDENTE.value)
    criado_em = Column(DateTime, default=datetime.datetime.utcnow)
    finalizado_em = Column(DateTime, nullable=True)

    cliente = relationship("Cliente", back_populates="solicitacoes")
    profissional = relationship("Profissional", back_populates="servicos")
    avaliacao = relationship(
        "Avaliacao", back_populates="solicitacao", uselist=False
    )


class Avaliacao(Base):
    __tablename__ = "avaliacoes"

    id = Column(Integer, primary_key=True, index=True)
    solicitacao_id = Column(
        Integer, ForeignKey("solicitacoes.id"), nullable=False
    )
    profissional_id = Column(
        Integer, ForeignKey("profissionais.id"), nullable=False
    )
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    nota = Column(Float, nullable=False)  # 1-5
    pontualidade = Column(Boolean, default=True)
    comentario = Column(Text, default="")
    reclamacao = Column(Boolean, default=False)
    criado_em = Column(DateTime, default=datetime.datetime.utcnow)

    solicitacao = relationship("SolicitacaoServico", back_populates="avaliacao")
    profissional = relationship("Profissional", back_populates="avaliacoes")
    cliente = relationship("Cliente", back_populates="avaliacoes")


class Pagamento(Base):
    __tablename__ = "pagamentos"

    id = Column(Integer, primary_key=True, index=True)
    solicitacao_id = Column(Integer, ForeignKey("solicitacoes.id"), nullable=False)
    stripe_payment_intent_id = Column(String(255), unique=True, nullable=False)
    stripe_transfer_id = Column(String(255), nullable=True)
    valor_total = Column(Float, nullable=False)
    valor_profissional = Column(Float, nullable=False)
    valor_plataforma = Column(Float, nullable=False)
    metodo = Column(String(20), default="cartao")  # cartao, pix
    status = Column(String(30), default="pendente")  # pendente, pago, transferido, reembolsado, falhou
    criado_em = Column(DateTime, default=datetime.datetime.utcnow)
    pago_em = Column(DateTime, nullable=True)
    transferido_em = Column(DateTime, nullable=True)

    solicitacao = relationship("SolicitacaoServico")
