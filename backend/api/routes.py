"""Rotas da API PASSA."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.database import get_db
from backend.models.models import (
    Profissional,
    Cliente,
    Servico,
    SolicitacaoServico,
    Avaliacao,
    StatusServico,
)
from backend.services.precificacao import precificar
from backend.services.score import calcular_score, atualizar_score_profissional
import datetime

router = APIRouter(prefix="/api", tags=["PASSA"])


# ======== Schemas ========


class PrecificacaoRequest(BaseModel):
    descricao: str
    regiao: str = ""
    urgente: bool = False


class SolicitacaoRequest(BaseModel):
    nome_cliente: str
    email_cliente: str
    telefone_cliente: str
    endereco: str = ""
    bairro: str = ""
    descricao: str
    urgente: bool = False


class ProfissionalCreate(BaseModel):
    nome: str
    email: str
    telefone: str
    cpf: str
    categoria: str
    especialidades: str = ""
    regiao: str = "São Paulo"


class AvaliacaoCreate(BaseModel):
    solicitacao_id: int
    profissional_id: int
    nota: float
    pontualidade: bool = True
    comentario: str = ""
    reclamacao: bool = False


class AceitarServicoRequest(BaseModel):
    profissional_id: int


# ======== Precificação ========


@router.post("/precificar")
def api_precificar(req: PrecificacaoRequest):
    """Precifica um serviço usando IA."""
    resultado = precificar(req.descricao, req.regiao, req.urgente)
    return {
        "sucesso": True,
        "descricao_original": req.descricao,
        "precificacao": resultado,
    }


# ======== Solicitações ========


@router.post("/solicitar")
def criar_solicitacao(req: SolicitacaoRequest, db: Session = Depends(get_db)):
    """Cria uma nova solicitação de serviço."""
    # Busca ou cria cliente
    cliente = db.query(Cliente).filter(Cliente.email == req.email_cliente).first()
    if not cliente:
        cliente = Cliente(
            nome=req.nome_cliente,
            email=req.email_cliente,
            telefone=req.telefone_cliente,
            endereco=req.endereco,
            bairro=req.bairro,
        )
        db.add(cliente)
        db.flush()

    # Precifica
    preco = precificar(req.descricao, req.bairro, req.urgente)

    # Cria solicitação
    solicitacao = SolicitacaoServico(
        cliente_id=cliente.id,
        descricao=req.descricao,
        categoria=preco["categoria"],
        endereco=req.endereco,
        bairro=req.bairro,
        urgente=req.urgente,
        preco_sugerido_min=preco["preco_min"],
        preco_sugerido_max=preco["preco_max"],
        tempo_estimado_min=preco["tempo_estimado_min"],
        status=StatusServico.PENDENTE.value,
    )
    db.add(solicitacao)
    db.commit()
    db.refresh(solicitacao)

    # Busca profissionais compatíveis
    profissionais = (
        db.query(Profissional)
        .filter(
            Profissional.ativo == True,
            Profissional.categoria == preco["categoria"],
        )
        .order_by(Profissional.score.desc())
        .limit(5)
        .all()
    )

    return {
        "sucesso": True,
        "solicitacao_id": solicitacao.id,
        "precificacao": preco,
        "profissionais_disponiveis": [
            {
                "id": p.id,
                "nome": p.nome,
                "score": p.score,
                "avaliacao_media": p.avaliacao_media,
                "total_servicos": p.total_servicos,
                "documento_verificado": p.documento_verificado,
            }
            for p in profissionais
        ],
    }


@router.get("/solicitacoes")
def listar_solicitacoes(
    status: str = None, limit: int = 20, db: Session = Depends(get_db)
):
    """Lista solicitações de serviço."""
    query = db.query(SolicitacaoServico).order_by(
        SolicitacaoServico.criado_em.desc()
    )
    if status:
        query = query.filter(SolicitacaoServico.status == status)
    solicitacoes = query.limit(limit).all()

    return {
        "total": len(solicitacoes),
        "solicitacoes": [
            {
                "id": s.id,
                "descricao": s.descricao,
                "categoria": s.categoria,
                "status": s.status,
                "preco_min": s.preco_sugerido_min,
                "preco_max": s.preco_sugerido_max,
                "tempo_estimado": s.tempo_estimado_min,
                "urgente": s.urgente,
                "criado_em": s.criado_em.isoformat() if s.criado_em else None,
                "profissional_id": s.profissional_id,
            }
            for s in solicitacoes
        ],
    }


@router.post("/solicitacoes/{solicitacao_id}/aceitar")
def aceitar_servico(
    solicitacao_id: int,
    req: AceitarServicoRequest,
    db: Session = Depends(get_db),
):
    """Profissional aceita um serviço."""
    solicitacao = db.query(SolicitacaoServico).get(solicitacao_id)
    if not solicitacao:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
    if solicitacao.status != StatusServico.PENDENTE.value:
        raise HTTPException(status_code=400, detail="Solicitação não está pendente")

    profissional = db.query(Profissional).get(req.profissional_id)
    if not profissional:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")

    solicitacao.profissional_id = profissional.id
    solicitacao.status = StatusServico.ACEITO.value
    db.commit()

    return {"sucesso": True, "status": "aceito"}


@router.post("/solicitacoes/{solicitacao_id}/concluir")
def concluir_servico(solicitacao_id: int, db: Session = Depends(get_db)):
    """Marca serviço como concluído."""
    solicitacao = db.query(SolicitacaoServico).get(solicitacao_id)
    if not solicitacao:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")

    solicitacao.status = StatusServico.CONCLUIDO.value
    solicitacao.finalizado_em = datetime.datetime.utcnow()

    if solicitacao.profissional_id:
        prof = db.query(Profissional).get(solicitacao.profissional_id)
        if prof:
            prof.total_servicos += 1

    db.commit()
    return {"sucesso": True, "status": "concluido"}


# ======== Profissionais ========


@router.post("/profissionais")
def cadastrar_profissional(req: ProfissionalCreate, db: Session = Depends(get_db)):
    """Cadastra um novo profissional."""
    existente = (
        db.query(Profissional)
        .filter(
            (Profissional.email == req.email) | (Profissional.cpf == req.cpf)
        )
        .first()
    )
    if existente:
        raise HTTPException(status_code=400, detail="Email ou CPF já cadastrado")

    profissional = Profissional(
        nome=req.nome,
        email=req.email,
        telefone=req.telefone,
        cpf=req.cpf,
        categoria=req.categoria,
        especialidades=req.especialidades,
        regiao=req.regiao,
        score=500.0,
    )
    db.add(profissional)
    db.commit()
    db.refresh(profissional)

    return {
        "sucesso": True,
        "profissional": {
            "id": profissional.id,
            "nome": profissional.nome,
            "score": profissional.score,
        },
    }


@router.get("/profissionais")
def listar_profissionais(
    categoria: str = None,
    regiao: str = None,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """Lista profissionais ordenados por score."""
    query = (
        db.query(Profissional)
        .filter(Profissional.ativo == True)
        .order_by(Profissional.score.desc())
    )
    if categoria:
        query = query.filter(Profissional.categoria == categoria)
    if regiao:
        query = query.filter(Profissional.regiao.contains(regiao))

    profissionais = query.limit(limit).all()

    return {
        "total": len(profissionais),
        "profissionais": [
            {
                "id": p.id,
                "nome": p.nome,
                "categoria": p.categoria,
                "regiao": p.regiao,
                "score": p.score,
                "avaliacao_media": p.avaliacao_media,
                "total_servicos": p.total_servicos,
                "taxa_conclusao": p.taxa_conclusao,
                "documento_verificado": p.documento_verificado,
                "antecedentes_ok": p.antecedentes_ok,
            }
            for p in profissionais
        ],
    }


@router.get("/profissionais/{profissional_id}")
def detalhe_profissional(profissional_id: int, db: Session = Depends(get_db)):
    """Detalhes completos de um profissional com score."""
    prof = db.query(Profissional).get(profissional_id)
    if not prof:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")

    score_info = atualizar_score_profissional(prof)
    db.commit()

    return {
        "id": prof.id,
        "nome": prof.nome,
        "email": prof.email,
        "telefone": prof.telefone,
        "categoria": prof.categoria,
        "especialidades": prof.especialidades,
        "regiao": prof.regiao,
        "documento_verificado": prof.documento_verificado,
        "antecedentes_ok": prof.antecedentes_ok,
        "certificacoes": prof.certificacoes,
        "total_servicos": prof.total_servicos,
        "taxa_conclusao": prof.taxa_conclusao,
        "tempo_medio_min": prof.tempo_medio_min,
        "score_info": score_info,
    }


# ======== Avaliações ========


@router.post("/avaliacoes")
def criar_avaliacao(req: AvaliacaoCreate, db: Session = Depends(get_db)):
    """Cria avaliação de um serviço e atualiza score."""
    solicitacao = db.query(SolicitacaoServico).get(req.solicitacao_id)
    if not solicitacao:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")

    profissional = db.query(Profissional).get(req.profissional_id)
    if not profissional:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")

    avaliacao = Avaliacao(
        solicitacao_id=req.solicitacao_id,
        profissional_id=req.profissional_id,
        cliente_id=solicitacao.cliente_id,
        nota=req.nota,
        pontualidade=req.pontualidade,
        comentario=req.comentario,
        reclamacao=req.reclamacao,
    )
    db.add(avaliacao)

    # Atualizar métricas do profissional
    todas_avaliacoes = (
        db.query(Avaliacao)
        .filter(Avaliacao.profissional_id == req.profissional_id)
        .all()
    )
    todas_avaliacoes_list = list(todas_avaliacoes) + [avaliacao]

    total = len(todas_avaliacoes_list)
    profissional.avaliacao_media = round(
        sum(a.nota for a in todas_avaliacoes_list) / total, 2
    )
    pontuais = sum(1 for a in todas_avaliacoes_list if a.pontualidade)
    profissional.pontualidade = round((pontuais / total) * 100, 1)
    reclamacoes = sum(1 for a in todas_avaliacoes_list if a.reclamacao)
    profissional.total_reclamacoes = reclamacoes

    # Recalcula score
    score_info = atualizar_score_profissional(profissional)
    db.commit()

    return {
        "sucesso": True,
        "avaliacao_id": avaliacao.id,
        "novo_score": score_info,
    }


# ======== Score ========


@router.get("/score/simular")
def simular_score(
    pontualidade: float = 100,
    avaliacao: float = 5,
    reclamacoes: float = 0,
    frequencia: float = 50,
    recorrencia: float = 50,
    compliance: float = 100,
):
    """Simula um score sem salvar."""
    return calcular_score(
        pontualidade=pontualidade,
        avaliacao_media=avaliacao,
        taxa_reclamacao=reclamacoes,
        frequencia_uso=frequencia,
        recorrencia=recorrencia,
        compliance=compliance,
    )


# ======== Dashboard Stats ========


@router.get("/dashboard/stats")
def dashboard_stats(db: Session = Depends(get_db)):
    """Estatísticas gerais da plataforma."""
    total_profissionais = db.query(Profissional).filter(Profissional.ativo == True).count()
    total_clientes = db.query(Cliente).count()
    total_solicitacoes = db.query(SolicitacaoServico).count()
    total_concluidos = (
        db.query(SolicitacaoServico)
        .filter(SolicitacaoServico.status == StatusServico.CONCLUIDO.value)
        .count()
    )
    total_pendentes = (
        db.query(SolicitacaoServico)
        .filter(SolicitacaoServico.status == StatusServico.PENDENTE.value)
        .count()
    )

    # Top profissionais
    top_profissionais = (
        db.query(Profissional)
        .filter(Profissional.ativo == True)
        .order_by(Profissional.score.desc())
        .limit(5)
        .all()
    )

    return {
        "total_profissionais": total_profissionais,
        "total_clientes": total_clientes,
        "total_solicitacoes": total_solicitacoes,
        "total_concluidos": total_concluidos,
        "total_pendentes": total_pendentes,
        "top_profissionais": [
            {"id": p.id, "nome": p.nome, "score": p.score, "categoria": p.categoria}
            for p in top_profissionais
        ],
    }
