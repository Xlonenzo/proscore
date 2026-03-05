"""Rotas da API PASSA."""
import random
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.database import get_db
from backend.models.models import (
    Profissional,
    Cliente,
    Servico,
    SolicitacaoServico,
    Avaliacao,
    Pagamento,
    StatusServico,
    Usuario,
)
from backend.services.precificacao import precificar
from backend.services.score import calcular_score, atualizar_score_profissional
from backend.services.matchmaking import matchmaking_ia
from backend.services import pagamento as pagamento_service
from backend.auth import (
    hash_senha,
    verificar_senha,
    criar_token,
    get_current_user,
    COOKIE_NAME,
)
import datetime

router = APIRouter(prefix="/api", tags=["PASSA"])


# ======== Schemas ========


class PrecificacaoRequest(BaseModel):
    descricao: str
    regiao: str = ""
    urgente: bool = False
    foto_base64: str | None = None


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


class RegistroClienteRequest(BaseModel):
    nome: str
    email: str
    senha: str
    telefone: str
    endereco: str = ""
    bairro: str = ""


class RegistroPrestadorRequest(BaseModel):
    nome: str
    email: str
    senha: str
    telefone: str
    cpf: str = ""
    categoria: str = ""
    especialidades: str = ""
    descricao_servicos: str = ""
    regiao: str = "Sao Paulo"


class LoginRequest(BaseModel):
    email: str
    senha: str


class EnderecoRequest(BaseModel):
    endereco: str = ""
    bairro: str = ""


class DescricaoServicosRequest(BaseModel):
    descricao_servicos: str = ""


class SolicitacaoLogadoRequest(BaseModel):
    descricao: str
    urgente: bool = False


class CriarIntencaoPagamentoRequest(BaseModel):
    descricao: str
    regiao: str = ""
    urgente: bool = False
    foto_base64: str | None = None


class BuscarProfissionaisRequest(BaseModel):
    solicitacao_id: int


# ======== Auth ========


@router.post("/auth/registro/cliente")
def registro_cliente(req: RegistroClienteRequest, db: Session = Depends(get_db)):
    """Cadastra um novo cliente."""
    if db.query(Usuario).filter(Usuario.email == req.email).first():
        raise HTTPException(status_code=400, detail="Email ja cadastrado")

    cliente = Cliente(
        nome=req.nome,
        email=req.email,
        telefone=req.telefone,
        endereco=req.endereco,
        bairro=req.bairro,
    )
    db.add(cliente)
    db.flush()

    usuario = Usuario(
        email=req.email,
        senha_hash=hash_senha(req.senha),
        nome=req.nome,
        tipo="cliente",
        cliente_id=cliente.id,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)

    token = criar_token({"sub": str(usuario.id)})
    response = JSONResponse(content={"sucesso": True, "token": token, "nome": usuario.nome, "tipo": usuario.tipo})
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=86400,
    )
    return response


@router.post("/auth/registro/prestador")
def registro_prestador(req: RegistroPrestadorRequest, db: Session = Depends(get_db)):
    """Cadastra um novo prestador de servico."""
    if db.query(Usuario).filter(Usuario.email == req.email).first():
        raise HTTPException(status_code=400, detail="Email ja cadastrado")
    if req.cpf and db.query(Profissional).filter(Profissional.cpf == req.cpf).first():
        raise HTTPException(status_code=400, detail="CPF ja cadastrado")

    profissional = Profissional(
        nome=req.nome,
        email=req.email,
        telefone=req.telefone,
        cpf=req.cpf or None,
        categoria=req.categoria,
        especialidades=req.especialidades,
        descricao_servicos=req.descricao_servicos,
        regiao=req.regiao,
        score=500.0,
    )
    db.add(profissional)
    db.flush()

    usuario = Usuario(
        email=req.email,
        senha_hash=hash_senha(req.senha),
        nome=req.nome,
        tipo="prestador",
        profissional_id=profissional.id,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)

    token = criar_token({"sub": str(usuario.id)})
    response = JSONResponse(content={"sucesso": True, "token": token, "nome": usuario.nome, "tipo": usuario.tipo})
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=86400,
    )
    return response


@router.post("/auth/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Autentica usuario."""
    usuario = db.query(Usuario).filter(Usuario.email == req.email).first()
    if not usuario or not verificar_senha(req.senha, usuario.senha_hash):
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")
    if not usuario.ativo:
        raise HTTPException(status_code=403, detail="Conta desativada")

    token = criar_token({"sub": str(usuario.id)})
    response = JSONResponse(content={
        "sucesso": True,
        "token": token,
        "nome": usuario.nome,
        "tipo": usuario.tipo,
    })
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=86400,
    )
    return response


@router.post("/auth/logout")
def logout():
    """Remove cookie de autenticacao."""
    response = JSONResponse(content={"sucesso": True})
    response.delete_cookie(COOKIE_NAME)
    return response


@router.get("/auth/me")
def me(usuario: Usuario = Depends(get_current_user)):
    """Retorna dados do usuario logado."""
    data = {
        "id": usuario.id,
        "nome": usuario.nome,
        "email": usuario.email,
        "tipo": usuario.tipo,
    }
    if usuario.tipo == "cliente" and usuario.cliente:
        data["endereco"] = usuario.cliente.endereco or ""
        data["bairro"] = usuario.cliente.bairro or ""
        data["telefone"] = usuario.cliente.telefone or ""
    if usuario.tipo == "prestador" and usuario.profissional:
        p = usuario.profissional
        data["categoria"] = p.categoria or ""
        data["regiao"] = p.regiao or ""
        data["descricao_servicos"] = p.descricao_servicos or ""
        data["telefone"] = p.telefone or ""
        data["score"] = p.score
        data["avaliacao_media"] = p.avaliacao_media
        data["total_servicos"] = p.total_servicos
        data["online"] = p.online
    return data


@router.put("/auth/endereco")
def atualizar_endereco(
    req: EnderecoRequest,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Salva endereco do cliente no perfil."""
    if usuario.tipo != "cliente" or not usuario.cliente:
        raise HTTPException(status_code=400, detail="Apenas clientes podem atualizar endereco")
    usuario.cliente.endereco = req.endereco
    usuario.cliente.bairro = req.bairro
    db.commit()
    return {"sucesso": True}


@router.put("/auth/descricao-servicos")
def atualizar_descricao_servicos(
    req: DescricaoServicosRequest,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Atualiza descricao de servicos do prestador."""
    if usuario.tipo != "prestador" or not usuario.profissional:
        raise HTTPException(status_code=400, detail="Apenas prestadores podem atualizar descricao de servicos")
    usuario.profissional.descricao_servicos = req.descricao_servicos
    db.commit()
    return {"sucesso": True}


# ======== Precificação ========


@router.post("/precificar")
def api_precificar(req: PrecificacaoRequest):
    """Precifica um serviço usando IA, com analise visual opcional."""
    resultado = precificar(req.descricao, req.regiao, req.urgente, req.foto_base64)

    response = {
        "sucesso": True,
        "descricao_original": req.descricao,
        "precificacao": resultado,
    }

    # Se a precificacao com foto retornou analise, inclui no response
    if "analise_foto" in resultado:
        response["analise_visual"] = resultado.pop("analise_foto")

    return response


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
        preco_final=preco["preco"],
        tempo_estimado_min=preco["tempo_estimado_min"],
        status=StatusServico.PENDENTE.value,
    )
    db.add(solicitacao)
    db.commit()
    db.refresh(solicitacao)

    # Busca profissionais compatíveis (somente online)
    profissionais = (
        db.query(Profissional)
        .filter(
            Profissional.ativo == True,
            Profissional.online == True,
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


@router.post("/solicitar-logado")
def criar_solicitacao_logado(
    req: SolicitacaoLogadoRequest,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cria solicitacao usando dados do usuario logado (fluxo Uber-like)."""
    if usuario.tipo != "cliente" or not usuario.cliente:
        raise HTTPException(status_code=400, detail="Apenas clientes podem solicitar servicos")

    cliente = usuario.cliente
    bairro = cliente.bairro or ""

    # Precifica com IA
    preco = precificar(req.descricao, bairro, req.urgente)

    # Cria solicitacao
    solicitacao = SolicitacaoServico(
        cliente_id=cliente.id,
        descricao=req.descricao,
        categoria=preco["categoria"],
        endereco=cliente.endereco or "",
        bairro=bairro,
        urgente=req.urgente,
        preco_final=preco["preco"],
        tempo_estimado_min=preco["tempo_estimado_min"],
        status=StatusServico.PENDENTE.value,
    )
    db.add(solicitacao)
    db.commit()
    db.refresh(solicitacao)

    # === Matchmaking por IA ===
    # Busca todos os profissionais ativos e online
    todos_profissionais = (
        db.query(Profissional)
        .filter(Profissional.ativo == True, Profissional.online == True)
        .all()
    )

    # Prepara dados para o matchmaking
    profs_para_match = [
        {
            "id": p.id,
            "nome": p.nome,
            "descricao_servicos": p.descricao_servicos or "",
            "categoria": p.categoria or "",
            "regiao": p.regiao or "",
            "score": p.score or 0,
            "avaliacao_media": p.avaliacao_media or 0,
            "total_servicos": p.total_servicos or 0,
            "taxa_conclusao": p.taxa_conclusao or 0,
            "documento_verificado": p.documento_verificado,
            "antecedentes_ok": p.antecedentes_ok,
        }
        for p in todos_profissionais
    ]

    # Matchmaking via IA (Groq) com fallback para keywords
    matches = matchmaking_ia(req.descricao, profs_para_match)

    # Calcula tempo estimado de chegada por regiao
    bairro_lower = (bairro or "").lower()
    resultado_profs = []
    for m in matches[:10]:
        regiao_prof = (m.get("regiao") or "").lower()
        if bairro_lower and bairro_lower in regiao_prof:
            tempo_chegada = random.randint(8, 20)
        elif any(z in regiao_prof for z in ["centro", "zona sul", "zona norte", "zona leste", "zona oeste"]
                 if z in bairro_lower or bairro_lower in z):
            tempo_chegada = random.randint(15, 30)
        else:
            tempo_chegada = random.randint(25, 50)

        resultado_profs.append({
            "id": m["id"],
            "nome": m["nome"],
            "categoria": m.get("categoria", ""),
            "regiao": m.get("regiao", ""),
            "score": m.get("score", 0),
            "avaliacao_media": m.get("avaliacao_media", 0),
            "total_servicos": m.get("total_servicos", 0),
            "taxa_conclusao": m.get("taxa_conclusao", 0),
            "documento_verificado": m.get("documento_verificado", False),
            "antecedentes_ok": m.get("antecedentes_ok", False),
            "tempo_chegada_min": tempo_chegada,
            "relevancia": m.get("relevancia", 0),
            "motivo_match": m.get("motivo_match", ""),
        })

    return {
        "sucesso": True,
        "solicitacao_id": solicitacao.id,
        "precificacao": preco,
        "profissionais_disponiveis": resultado_profs,
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
                "preco": s.preco_final,
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
    """Marca serviço como concluído e transfere pagamento ao prestador."""
    solicitacao = db.query(SolicitacaoServico).get(solicitacao_id)
    if not solicitacao:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")

    solicitacao.status = StatusServico.CONCLUIDO.value
    solicitacao.finalizado_em = datetime.datetime.utcnow()

    if solicitacao.profissional_id:
        prof = db.query(Profissional).get(solicitacao.profissional_id)
        if prof:
            prof.total_servicos += 1

    # Transfere pagamento automaticamente ao prestador
    pag = (
        db.query(Pagamento)
        .filter(
            Pagamento.solicitacao_id == solicitacao_id,
            Pagamento.status == "pago",
        )
        .first()
    )
    transfer_id = None
    if pag and solicitacao.profissional_id:
        prof = db.query(Profissional).get(solicitacao.profissional_id)
        if prof and prof.stripe_connect_id:
            try:
                transfer_id = pagamento_service.transferir_para_prestador(
                    stripe_connect_id=prof.stripe_connect_id,
                    valor_profissional=pag.valor_profissional,
                    solicitacao_id=solicitacao_id,
                    payment_intent_id=pag.stripe_payment_intent_id,
                )
                pag.stripe_transfer_id = transfer_id
                pag.status = "transferido"
                pag.transferido_em = datetime.datetime.utcnow()
            except Exception as e:
                print(f"[TRANSFER ERRO] solicitacao {solicitacao_id}: {e}")

    db.commit()
    return {
        "sucesso": True,
        "status": "concluido",
        "transferencia": transfer_id,
    }


@router.post("/solicitacoes/{solicitacao_id}/cancelar")
def cancelar_solicitacao(
    solicitacao_id: int,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancela uma solicitacao. Cliente ou prestador podem cancelar."""
    solicitacao = db.query(SolicitacaoServico).get(solicitacao_id)
    if not solicitacao:
        raise HTTPException(status_code=404, detail="Solicitacao nao encontrada")

    if solicitacao.status == StatusServico.CONCLUIDO.value:
        raise HTTPException(status_code=400, detail="Servico ja concluido, nao pode cancelar")

    if solicitacao.status == StatusServico.CANCELADO.value:
        raise HTTPException(status_code=400, detail="Solicitacao ja cancelada")

    # Verifica se o usuario tem permissao
    pode_cancelar = False
    if usuario.tipo == "cliente" and usuario.cliente:
        pode_cancelar = solicitacao.cliente_id == usuario.cliente.id
    elif usuario.tipo == "prestador" and usuario.profissional:
        pode_cancelar = solicitacao.profissional_id == usuario.profissional.id

    if not pode_cancelar:
        raise HTTPException(status_code=403, detail="Sem permissao para cancelar")

    solicitacao.status = StatusServico.CANCELADO.value
    solicitacao.finalizado_em = datetime.datetime.utcnow()

    # Reembolso: marca pagamento como reembolsado
    reembolsado = False
    pag = (
        db.query(Pagamento)
        .filter(
            Pagamento.solicitacao_id == solicitacao_id,
            Pagamento.status.in_(["pendente", "pago"]),
        )
        .first()
    )
    if pag:
        pag.status = "reembolsado"
        reembolsado = True
        # Se Stripe configurado, tenta reembolso real
        if pagamento_service.STRIPE_SECRET_KEY and not pag.stripe_payment_intent_id.startswith("mvp_"):
            try:
                import stripe
                stripe.Refund.create(payment_intent=pag.stripe_payment_intent_id)
            except Exception as e:
                print(f"[REFUND ERRO] solicitacao {solicitacao_id}: {e}")

    db.commit()
    return {
        "sucesso": True,
        "status": "cancelado",
        "reembolsado": reembolsado,
    }


# ======== Historico Cliente ========


@router.get("/cliente/historico")
def cliente_historico(
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retorna historico de servicos do cliente."""
    if usuario.tipo != "cliente" or not usuario.cliente:
        raise HTTPException(status_code=400, detail="Apenas clientes")

    solicitacoes = (
        db.query(SolicitacaoServico)
        .filter(SolicitacaoServico.cliente_id == usuario.cliente.id)
        .order_by(SolicitacaoServico.criado_em.desc())
        .limit(50)
        .all()
    )

    resultado = []
    for s in solicitacoes:
        prof = db.query(Profissional).get(s.profissional_id) if s.profissional_id else None
        pag = db.query(Pagamento).filter(Pagamento.solicitacao_id == s.id).first()
        avaliacao = (
            db.query(Avaliacao)
            .filter(Avaliacao.solicitacao_id == s.id)
            .first()
        )
        resultado.append({
            "id": s.id,
            "descricao": s.descricao,
            "categoria": s.categoria,
            "status": s.status,
            "preco_final": s.preco_final,
            "urgente": s.urgente,
            "criado_em": s.criado_em.isoformat() if s.criado_em else None,
            "finalizado_em": s.finalizado_em.isoformat() if s.finalizado_em else None,
            "profissional_nome": prof.nome if prof else None,
            "profissional_categoria": prof.categoria if prof else None,
            "profissional_score": prof.score if prof else None,
            "valor_pago": pag.valor_total if pag else None,
            "pagamento_status": pag.status if pag else None,
            "avaliacao_nota": avaliacao.nota if avaliacao else None,
        })

    return {"historico": resultado}


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


# ======== Pagamento Stripe ========


@router.get("/stripe/config")
def stripe_config():
    """Retorna a publishable key do Stripe para o mobile."""
    return {"publishable_key": pagamento_service.STRIPE_PUBLISHABLE_KEY}


@router.post("/pagamento/criar-intencao")
def criar_intencao_pagamento(
    req: CriarIntencaoPagamentoRequest,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Precifica, cria solicitacao e PaymentIntent do Stripe.

    Chamado quando o cliente aceita o preco e vai pagar.
    Retorna client_secret para o Stripe SDK no mobile confirmar.
    """
    if usuario.tipo != "cliente" or not usuario.cliente:
        raise HTTPException(status_code=400, detail="Apenas clientes podem pagar")

    cliente = usuario.cliente
    bairro = cliente.bairro or ""

    # 1. Precifica com IA
    preco_result = precificar(req.descricao, req.regiao or bairro, req.urgente, req.foto_base64)
    valor_total = float(preco_result["preco"])

    # 2. Cria solicitacao no banco
    solicitacao = SolicitacaoServico(
        cliente_id=cliente.id,
        descricao=req.descricao,
        categoria=preco_result.get("categoria", "outros"),
        endereco=cliente.endereco or "",
        bairro=bairro,
        urgente=req.urgente,
        preco_final=valor_total,
        tempo_estimado_min=int(preco_result.get("tempo_estimado_min", 60)),
        status=StatusServico.PENDENTE.value,
    )
    db.add(solicitacao)
    db.flush()

    # 3. Calcula split
    split = pagamento_service.calcular_split(valor_total)

    # 4. Tenta Stripe se configurado, senao modo MVP
    payment_intent_id = f"mvp_{solicitacao.id}_{int(datetime.datetime.utcnow().timestamp())}"
    client_secret = ""

    if pagamento_service.STRIPE_SECRET_KEY:
        try:
            if not cliente.stripe_customer_id:
                cliente.stripe_customer_id = pagamento_service.criar_customer(
                    email=cliente.email,
                    nome=cliente.nome,
                )
                db.flush()

            intent = pagamento_service.criar_payment_intent(
                valor_brl=valor_total,
                stripe_customer_id=cliente.stripe_customer_id,
                solicitacao_id=solicitacao.id,
                descricao=req.descricao,
            )
            payment_intent_id = intent["payment_intent_id"]
            client_secret = intent["client_secret"]
        except Exception:
            pass  # Segue em modo MVP

    # 5. Salva registro de pagamento
    pag = Pagamento(
        solicitacao_id=solicitacao.id,
        stripe_payment_intent_id=payment_intent_id,
        valor_total=split["valor_total"],
        valor_profissional=split["valor_profissional"],
        valor_plataforma=split["valor_plataforma"],
        status="pendente",
    )
    db.add(pag)
    db.commit()

    return {
        "sucesso": True,
        "client_secret": client_secret,
        "payment_intent_id": payment_intent_id,
        "solicitacao_id": solicitacao.id,
        "preco": valor_total,
        "split": split,
        "precificacao": preco_result,
    }


@router.post("/pagamento/buscar-profissionais")
def buscar_profissionais_apos_pagamento(
    req: BuscarProfissionaisRequest,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Busca profissionais para uma solicitacao ja paga.

    Chamado pelo BuscaMapaScreen apos confirmacao do pagamento.
    """
    if usuario.tipo != "cliente":
        raise HTTPException(status_code=400, detail="Apenas clientes")

    solicitacao = db.query(SolicitacaoServico).get(req.solicitacao_id)
    if not solicitacao:
        raise HTTPException(status_code=404, detail="Solicitacao nao encontrada")

    # Verifica se o pagamento foi confirmado
    pag = (
        db.query(Pagamento)
        .filter(
            Pagamento.solicitacao_id == req.solicitacao_id,
            Pagamento.status.in_(["pago", "pendente"]),
        )
        .first()
    )
    if not pag:
        raise HTTPException(status_code=400, detail="Pagamento nao encontrado")

    # Matchmaking por IA (somente online)
    todos_profissionais = (
        db.query(Profissional)
        .filter(Profissional.ativo == True, Profissional.online == True)
        .all()
    )

    profs_para_match = [
        {
            "id": p.id,
            "nome": p.nome,
            "descricao_servicos": p.descricao_servicos or "",
            "categoria": p.categoria or "",
            "regiao": p.regiao or "",
            "score": p.score or 0,
            "avaliacao_media": p.avaliacao_media or 0,
            "total_servicos": p.total_servicos or 0,
            "taxa_conclusao": p.taxa_conclusao or 0,
            "documento_verificado": p.documento_verificado,
            "antecedentes_ok": p.antecedentes_ok,
        }
        for p in todos_profissionais
    ]

    matches = matchmaking_ia(solicitacao.descricao, profs_para_match)

    bairro_lower = (solicitacao.bairro or "").lower()
    resultado_profs = []
    for m in matches[:10]:
        regiao_prof = (m.get("regiao") or "").lower()
        if bairro_lower and bairro_lower in regiao_prof:
            tempo_chegada = random.randint(8, 20)
        elif any(z in regiao_prof for z in ["centro", "zona sul", "zona norte", "zona leste", "zona oeste"]
                 if z in bairro_lower or bairro_lower in z):
            tempo_chegada = random.randint(15, 30)
        else:
            tempo_chegada = random.randint(25, 50)

        resultado_profs.append({
            "id": m["id"],
            "nome": m["nome"],
            "categoria": m.get("categoria", ""),
            "regiao": m.get("regiao", ""),
            "score": m.get("score", 0),
            "avaliacao_media": m.get("avaliacao_media", 0),
            "total_servicos": m.get("total_servicos", 0),
            "documento_verificado": m.get("documento_verificado", False),
            "tempo_chegada_min": tempo_chegada,
            "relevancia": m.get("relevancia", 0),
        })

    return {
        "sucesso": True,
        "solicitacao_id": solicitacao.id,
        "profissionais_disponiveis": resultado_profs,
    }


@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Webhook do Stripe para confirmar pagamentos."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        evento = pagamento_service.processar_webhook(payload, sig_header)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook invalido: {e}")

    if evento["tipo"] == "pagamento_confirmado":
        pag = (
            db.query(Pagamento)
            .filter(Pagamento.stripe_payment_intent_id == evento["payment_intent_id"])
            .first()
        )
        if pag and pag.status == "pendente":
            pag.status = "pago"
            pag.pago_em = datetime.datetime.utcnow()
            pag.metodo = evento.get("metodo", "cartao")
            db.commit()

    elif evento["tipo"] == "pagamento_falhou":
        pag = (
            db.query(Pagamento)
            .filter(Pagamento.stripe_payment_intent_id == evento["payment_intent_id"])
            .first()
        )
        if pag:
            pag.status = "falhou"
            db.commit()

    return {"received": True}


@router.post("/stripe/connect/onboarding")
def stripe_connect_onboarding(
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cria conta Stripe Connect para o prestador receber pagamentos."""
    if usuario.tipo != "prestador" or not usuario.profissional:
        raise HTTPException(status_code=400, detail="Apenas prestadores")

    if not pagamento_service.STRIPE_SECRET_KEY:
        return {
            "sucesso": False,
            "mensagem": "Stripe nao configurado. Configure STRIPE_SECRET_KEY.",
        }

    prof = usuario.profissional

    if prof.stripe_connect_id:
        import stripe
        link = stripe.AccountLink.create(
            account=prof.stripe_connect_id,
            refresh_url="https://passa.app/stripe/refresh",
            return_url="https://passa.app/stripe/return",
            type="account_onboarding",
        )
        return {
            "sucesso": True,
            "account_id": prof.stripe_connect_id,
            "onboarding_url": link.url,
        }

    result = pagamento_service.criar_conta_connect(
        email=prof.email,
        nome=prof.nome,
    )
    prof.stripe_connect_id = result["account_id"]
    db.commit()

    return {
        "sucesso": True,
        "account_id": result["account_id"],
        "onboarding_url": result["onboarding_url"],
    }


@router.get("/stripe/connect/status")
def stripe_connect_status(
    usuario: Usuario = Depends(get_current_user),
):
    """Verifica se o prestador completou onboarding do Stripe."""
    if usuario.tipo != "prestador" or not usuario.profissional:
        raise HTTPException(status_code=400, detail="Apenas prestadores")

    prof = usuario.profissional
    if not prof.stripe_connect_id:
        return {"configurado": False, "mensagem": "Conta Stripe nao criada"}

    if not pagamento_service.STRIPE_SECRET_KEY:
        return {"configurado": False, "mensagem": "Stripe nao configurado"}

    status = pagamento_service.verificar_conta_connect(prof.stripe_connect_id)
    return {
        "configurado": status["payouts_enabled"],
        "detalhes": status,
    }


# ======== Prestador Dashboard ========


@router.put("/prestador/online")
def prestador_toggle_online(
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Alterna status online/offline do prestador."""
    if usuario.tipo != "prestador" or not usuario.profissional:
        raise HTTPException(status_code=400, detail="Apenas prestadores")

    prof = usuario.profissional
    prof.online = not prof.online
    db.commit()

    return {"online": prof.online}


@router.get("/prestador/stats")
def prestador_stats(
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retorna estatisticas do prestador para o dashboard."""
    if usuario.tipo != "prestador" or not usuario.profissional:
        raise HTTPException(status_code=400, detail="Apenas prestadores")

    prof = usuario.profissional

    # Ganhos totais e do mes
    ganhos_total = 0.0
    ganhos_mes = 0.0
    agora = datetime.datetime.utcnow()
    inicio_mes = agora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    pagamentos = (
        db.query(Pagamento)
        .join(SolicitacaoServico, Pagamento.solicitacao_id == SolicitacaoServico.id)
        .filter(
            SolicitacaoServico.profissional_id == prof.id,
            Pagamento.status.in_(["pago", "transferido"]),
        )
        .all()
    )
    for p in pagamentos:
        ganhos_total += p.valor_profissional
        if p.pago_em and p.pago_em >= inicio_mes:
            ganhos_mes += p.valor_profissional

    return {
        "nome": prof.nome,
        "score": prof.score,
        "avaliacao_media": prof.avaliacao_media,
        "total_servicos": prof.total_servicos,
        "ganhos_total": round(ganhos_total, 2),
        "ganhos_mes": round(ganhos_mes, 2),
        "categoria": prof.categoria,
        "online": prof.online,
    }


@router.get("/prestador/solicitacoes/disponiveis")
def prestador_solicitacoes_disponiveis(
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retorna solicitacoes pendentes que combinam com o prestador."""
    if usuario.tipo != "prestador" or not usuario.profissional:
        raise HTTPException(status_code=400, detail="Apenas prestadores")

    prof = usuario.profissional

    # Busca solicitacoes pendentes sem profissional atribuido
    query = (
        db.query(SolicitacaoServico)
        .filter(
            SolicitacaoServico.status == StatusServico.PENDENTE.value,
            SolicitacaoServico.profissional_id == None,
        )
        .order_by(SolicitacaoServico.criado_em.desc())
        .limit(20)
    )

    solicitacoes = query.all()
    resultado = []
    for s in solicitacoes:
        cliente = db.query(Cliente).get(s.cliente_id)
        resultado.append({
            "id": s.id,
            "descricao": s.descricao,
            "categoria": s.categoria,
            "bairro": s.bairro,
            "urgente": s.urgente,
            "preco_final": s.preco_final,
            "criado_em": s.criado_em.isoformat() if s.criado_em else None,
            "cliente_nome": cliente.nome if cliente else "",
        })

    return {"solicitacoes": resultado}


@router.get("/prestador/solicitacoes")
def prestador_solicitacoes(
    status: str = "",
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retorna solicitacoes do prestador filtradas por status."""
    if usuario.tipo != "prestador" or not usuario.profissional:
        raise HTTPException(status_code=400, detail="Apenas prestadores")

    prof = usuario.profissional

    query = (
        db.query(SolicitacaoServico)
        .filter(SolicitacaoServico.profissional_id == prof.id)
    )

    if status:
        query = query.filter(SolicitacaoServico.status == status)

    solicitacoes = (
        query.order_by(SolicitacaoServico.criado_em.desc())
        .limit(50)
        .all()
    )

    resultado = []
    for s in solicitacoes:
        cliente = db.query(Cliente).get(s.cliente_id)
        pag = (
            db.query(Pagamento)
            .filter(Pagamento.solicitacao_id == s.id)
            .first()
        )
        resultado.append({
            "id": s.id,
            "descricao": s.descricao,
            "categoria": s.categoria,
            "bairro": s.bairro,
            "urgente": s.urgente,
            "preco_final": s.preco_final,
            "status": s.status,
            "criado_em": s.criado_em.isoformat() if s.criado_em else None,
            "finalizado_em": s.finalizado_em.isoformat() if s.finalizado_em else None,
            "cliente_nome": cliente.nome if cliente else "",
            "valor_profissional": pag.valor_profissional if pag else None,
            "pagamento_status": pag.status if pag else None,
        })

    return {"solicitacoes": resultado}


@router.post("/solicitacoes/{solicitacao_id}/aceitar-prestador")
def aceitar_solicitacao_prestador(
    solicitacao_id: int,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Prestador aceita uma solicitacao disponivel."""
    if usuario.tipo != "prestador" or not usuario.profissional:
        raise HTTPException(status_code=400, detail="Apenas prestadores")

    prof = usuario.profissional
    solicitacao = db.query(SolicitacaoServico).get(solicitacao_id)

    if not solicitacao:
        raise HTTPException(status_code=404, detail="Solicitacao nao encontrada")

    if solicitacao.status != StatusServico.PENDENTE.value:
        raise HTTPException(status_code=400, detail="Solicitacao nao esta pendente")

    if solicitacao.profissional_id and solicitacao.profissional_id != prof.id:
        raise HTTPException(status_code=400, detail="Solicitacao ja aceita por outro profissional")

    solicitacao.profissional_id = prof.id
    solicitacao.status = StatusServico.ACEITO.value
    db.commit()

    return {
        "sucesso": True,
        "solicitacao_id": solicitacao.id,
        "status": "aceito",
    }
