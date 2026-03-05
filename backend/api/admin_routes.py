"""Admin API routes for PASSA."""
import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case, extract
from backend.database import get_db
from backend.models.models import (
    Usuario,
    Profissional,
    Cliente,
    SolicitacaoServico,
    Avaliacao,
    Pagamento,
    StatusServico,
)
from backend.auth import get_admin_user

admin_router = APIRouter(prefix="/api/admin", tags=["Admin"])


# ======== Usuarios ========


@admin_router.get("/usuarios")
def listar_usuarios(
    busca: str = "",
    tipo: str = "",
    ativo: str = "",
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    admin: Usuario = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    q = db.query(Usuario)
    if busca:
        q = q.filter(
            (Usuario.nome.ilike(f"%{busca}%"))
            | (Usuario.email.ilike(f"%{busca}%"))
        )
    if tipo:
        q = q.filter(Usuario.tipo == tipo)
    if ativo == "true":
        q = q.filter(Usuario.ativo == True)
    elif ativo == "false":
        q = q.filter(Usuario.ativo == False)

    total = q.count()
    usuarios = (
        q.order_by(Usuario.criado_em.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return {
        "usuarios": [
            {
                "id": u.id,
                "nome": u.nome,
                "email": u.email,
                "tipo": u.tipo,
                "ativo": u.ativo,
                "is_admin": u.is_admin,
                "criado_em": u.criado_em.isoformat() if u.criado_em else None,
            }
            for u in usuarios
        ],
        "total": total,
        "page": page,
        "pages": max(1, (total + per_page - 1) // per_page),
    }


@admin_router.get("/usuarios/{user_id}")
def detalhe_usuario(
    user_id: int,
    admin: Usuario = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    u = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not u:
        raise HTTPException(404, "Usuario nao encontrado")

    data = {
        "id": u.id,
        "nome": u.nome,
        "email": u.email,
        "tipo": u.tipo,
        "ativo": u.ativo,
        "is_admin": u.is_admin,
        "criado_em": u.criado_em.isoformat() if u.criado_em else None,
    }

    if u.tipo == "prestador" and u.profissional:
        p = u.profissional
        data["profissional"] = {
            "id": p.id,
            "categoria": p.categoria,
            "score": p.score,
            "total_servicos": p.total_servicos,
            "avaliacao_media": p.avaliacao_media,
            "documento_verificado": p.documento_verificado,
            "antecedentes_ok": p.antecedentes_ok,
            "ativo": p.ativo,
        }
    elif u.tipo == "cliente" and u.cliente:
        c = u.cliente
        total_sol = (
            db.query(SolicitacaoServico)
            .filter(SolicitacaoServico.cliente_id == c.id)
            .count()
        )
        data["cliente"] = {
            "id": c.id,
            "telefone": c.telefone,
            "endereco": c.endereco,
            "total_solicitacoes": total_sol,
        }

    return data


@admin_router.post("/usuarios/{user_id}/suspender")
def suspender_usuario(
    user_id: int,
    admin: Usuario = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    u = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not u:
        raise HTTPException(404, "Usuario nao encontrado")
    if u.is_admin:
        raise HTTPException(400, "Nao e possivel suspender um admin")
    u.ativo = False
    if u.tipo == "prestador" and u.profissional:
        u.profissional.ativo = False
    db.commit()
    return {"ok": True, "message": f"Usuario {u.nome} suspenso"}


@admin_router.post("/usuarios/{user_id}/reativar")
def reativar_usuario(
    user_id: int,
    admin: Usuario = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    u = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not u:
        raise HTTPException(404, "Usuario nao encontrado")
    u.ativo = True
    if u.tipo == "prestador" and u.profissional:
        u.profissional.ativo = True
    db.commit()
    return {"ok": True, "message": f"Usuario {u.nome} reativado"}


# ======== Prestadores (todos) ========


@admin_router.get("/prestadores")
def listar_prestadores(
    busca: str = "",
    categoria: str = "",
    ativo: str = "",
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    admin: Usuario = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    q = db.query(Profissional)
    if busca:
        q = q.filter(
            (Profissional.nome.ilike(f"%{busca}%"))
            | (Profissional.email.ilike(f"%{busca}%"))
        )
    if categoria:
        q = q.filter(Profissional.categoria == categoria)
    if ativo == "true":
        q = q.filter(Profissional.ativo == True)
    elif ativo == "false":
        q = q.filter(Profissional.ativo == False)

    total = q.count()
    prestadores = (
        q.order_by(Profissional.criado_em.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return {
        "prestadores": [
            {
                "id": p.id,
                "nome": p.nome,
                "email": p.email,
                "telefone": p.telefone,
                "categoria": p.categoria,
                "regiao": p.regiao,
                "score": p.score,
                "total_servicos": p.total_servicos,
                "avaliacao_media": p.avaliacao_media,
                "documento_verificado": p.documento_verificado,
                "antecedentes_ok": p.antecedentes_ok,
                "ativo": p.ativo,
                "online": p.online,
                "criado_em": p.criado_em.isoformat() if p.criado_em else None,
            }
            for p in prestadores
        ],
        "total": total,
        "page": page,
        "pages": max(1, (total + per_page - 1) // per_page),
    }


# ======== Prestadores Pendentes ========


@admin_router.get("/prestadores/pendentes")
def prestadores_pendentes(
    admin: Usuario = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    pendentes = (
        db.query(Profissional)
        .filter(
            (Profissional.documento_verificado == False)
            | (Profissional.antecedentes_ok == False)
        )
        .order_by(Profissional.criado_em.desc())
        .all()
    )
    return {
        "pendentes": [
            {
                "id": p.id,
                "nome": p.nome,
                "email": p.email,
                "telefone": p.telefone,
                "categoria": p.categoria,
                "regiao": p.regiao,
                "documento_verificado": p.documento_verificado,
                "antecedentes_ok": p.antecedentes_ok,
                "criado_em": p.criado_em.isoformat() if p.criado_em else None,
            }
            for p in pendentes
        ],
        "total": len(pendentes),
    }


@admin_router.post("/prestadores/{prof_id}/aprovar")
def aprovar_prestador(
    prof_id: int,
    admin: Usuario = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    p = db.query(Profissional).filter(Profissional.id == prof_id).first()
    if not p:
        raise HTTPException(404, "Prestador nao encontrado")
    p.documento_verificado = True
    p.antecedentes_ok = True
    db.commit()
    return {"ok": True, "message": f"Prestador {p.nome} aprovado"}


# ======== Solicitacoes ========


@admin_router.get("/solicitacoes")
def listar_solicitacoes(
    status: str = "",
    categoria: str = "",
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    admin: Usuario = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    q = db.query(SolicitacaoServico)
    if status:
        q = q.filter(SolicitacaoServico.status == status)
    if categoria:
        q = q.filter(SolicitacaoServico.categoria == categoria)

    total = q.count()
    solicitacoes = (
        q.order_by(SolicitacaoServico.criado_em.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return {
        "solicitacoes": [
            {
                "id": s.id,
                "descricao": s.descricao[:100],
                "categoria": s.categoria,
                "status": s.status,
                "preco_final": s.preco_final,
                "urgente": s.urgente,
                "cliente_nome": s.cliente.nome if s.cliente else "—",
                "profissional_nome": s.profissional.nome if s.profissional else "—",
                "criado_em": s.criado_em.isoformat() if s.criado_em else None,
            }
            for s in solicitacoes
        ],
        "total": total,
        "page": page,
        "pages": max(1, (total + per_page - 1) // per_page),
    }


@admin_router.get("/solicitacoes/{sol_id}")
def detalhe_solicitacao(
    sol_id: int,
    admin: Usuario = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    s = db.query(SolicitacaoServico).filter(SolicitacaoServico.id == sol_id).first()
    if not s:
        raise HTTPException(404, "Solicitacao nao encontrada")
    return {
        "id": s.id,
        "descricao": s.descricao,
        "categoria": s.categoria,
        "status": s.status,
        "endereco": s.endereco,
        "bairro": s.bairro,
        "urgente": s.urgente,
        "preco_sugerido_min": s.preco_sugerido_min,
        "preco_sugerido_max": s.preco_sugerido_max,
        "preco_final": s.preco_final,
        "tempo_estimado_min": s.tempo_estimado_min,
        "cliente_nome": s.cliente.nome if s.cliente else "—",
        "profissional_nome": s.profissional.nome if s.profissional else "—",
        "criado_em": s.criado_em.isoformat() if s.criado_em else None,
        "finalizado_em": s.finalizado_em.isoformat() if s.finalizado_em else None,
    }


@admin_router.post("/solicitacoes/{sol_id}/cancelar")
def cancelar_solicitacao(
    sol_id: int,
    admin: Usuario = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    s = db.query(SolicitacaoServico).filter(SolicitacaoServico.id == sol_id).first()
    if not s:
        raise HTTPException(404, "Solicitacao nao encontrada")
    if s.status == StatusServico.CANCELADO.value:
        raise HTTPException(400, "Ja esta cancelada")
    s.status = StatusServico.CANCELADO.value
    db.commit()
    return {"ok": True, "message": "Solicitacao cancelada pelo admin"}


# ======== Analytics ========


@admin_router.get("/analytics/overview")
def analytics_overview(
    admin: Usuario = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    total_usuarios = db.query(Usuario).count()
    total_clientes = db.query(Usuario).filter(Usuario.tipo == "cliente").count()
    total_prestadores = db.query(Usuario).filter(Usuario.tipo == "prestador").count()
    total_solicitacoes = db.query(SolicitacaoServico).count()

    hoje = datetime.datetime.utcnow().date()
    inicio_mes = hoje.replace(day=1)
    sol_mes = (
        db.query(SolicitacaoServico)
        .filter(SolicitacaoServico.criado_em >= inicio_mes)
        .count()
    )

    concluidos = (
        db.query(SolicitacaoServico)
        .filter(SolicitacaoServico.status == StatusServico.CONCLUIDO.value)
        .count()
    )
    taxa_conclusao = round(concluidos / total_solicitacoes * 100, 1) if total_solicitacoes else 0

    receita_total = (
        db.query(func.coalesce(func.sum(SolicitacaoServico.preco_final), 0))
        .filter(SolicitacaoServico.status == StatusServico.CONCLUIDO.value)
        .scalar()
    )

    avaliacao_media = (
        db.query(func.coalesce(func.avg(Avaliacao.nota), 0)).scalar()
    )

    # Recent activity (last 10 solicitacoes)
    recentes = (
        db.query(SolicitacaoServico)
        .order_by(SolicitacaoServico.criado_em.desc())
        .limit(10)
        .all()
    )

    return {
        "total_usuarios": total_usuarios,
        "total_clientes": total_clientes,
        "total_prestadores": total_prestadores,
        "total_solicitacoes": total_solicitacoes,
        "solicitacoes_mes": sol_mes,
        "taxa_conclusao": taxa_conclusao,
        "receita_total": float(receita_total),
        "avaliacao_media": round(float(avaliacao_media), 1),
        "recentes": [
            {
                "id": s.id,
                "descricao": s.descricao[:60],
                "status": s.status,
                "categoria": s.categoria,
                "criado_em": s.criado_em.isoformat() if s.criado_em else None,
            }
            for s in recentes
        ],
    }


@admin_router.get("/analytics/revenue")
def analytics_revenue(
    meses: int = Query(6, ge=1, le=12),
    admin: Usuario = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    hoje = datetime.datetime.utcnow()
    resultado = []
    for i in range(meses - 1, -1, -1):
        # Calculate month
        mes = hoje.month - i
        ano = hoje.year
        while mes <= 0:
            mes += 12
            ano -= 1

        inicio = datetime.datetime(ano, mes, 1)
        if mes == 12:
            fim = datetime.datetime(ano + 1, 1, 1)
        else:
            fim = datetime.datetime(ano, mes + 1, 1)

        receita = (
            db.query(func.coalesce(func.sum(SolicitacaoServico.preco_final), 0))
            .filter(
                SolicitacaoServico.status == StatusServico.CONCLUIDO.value,
                SolicitacaoServico.criado_em >= inicio,
                SolicitacaoServico.criado_em < fim,
            )
            .scalar()
        )

        count = (
            db.query(SolicitacaoServico)
            .filter(
                SolicitacaoServico.criado_em >= inicio,
                SolicitacaoServico.criado_em < fim,
            )
            .count()
        )

        nomes_meses = [
            "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
            "Jul", "Ago", "Set", "Out", "Nov", "Dez",
        ]
        resultado.append({
            "mes": f"{nomes_meses[mes - 1]}/{ano}",
            "receita": float(receita),
            "servicos": count,
        })

    return {"meses": resultado}


@admin_router.get("/analytics/categorias")
def analytics_categorias(
    admin: Usuario = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    cats = (
        db.query(
            SolicitacaoServico.categoria,
            func.count(SolicitacaoServico.id).label("total"),
            func.coalesce(func.sum(SolicitacaoServico.preco_final), 0).label("receita"),
        )
        .group_by(SolicitacaoServico.categoria)
        .order_by(func.count(SolicitacaoServico.id).desc())
        .all()
    )

    return {
        "categorias": [
            {
                "categoria": c.categoria or "outros",
                "total": c.total,
                "receita": float(c.receita),
            }
            for c in cats
        ]
    }


@admin_router.get("/analytics/status")
def analytics_status(
    admin: Usuario = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Distribuicao de solicitacoes por status."""
    statuses = (
        db.query(
            SolicitacaoServico.status,
            func.count(SolicitacaoServico.id).label("total"),
        )
        .group_by(SolicitacaoServico.status)
        .all()
    )
    return {
        "status": [
            {"status": s.status, "total": s.total}
            for s in statuses
        ]
    }


@admin_router.get("/analytics/top-prestadores")
def analytics_top_prestadores(
    limit: int = Query(10, ge=1, le=20),
    admin: Usuario = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Top prestadores por score, servicos e avaliacao."""
    tops = (
        db.query(Profissional)
        .filter(Profissional.ativo == True)
        .order_by(Profissional.score.desc())
        .limit(limit)
        .all()
    )
    return {
        "prestadores": [
            {
                "id": p.id,
                "nome": p.nome,
                "categoria": p.categoria,
                "score": p.score,
                "total_servicos": p.total_servicos,
                "avaliacao_media": p.avaliacao_media,
                "taxa_conclusao": p.taxa_conclusao,
            }
            for p in tops
        ]
    }


@admin_router.get("/analytics/crescimento")
def analytics_crescimento(
    meses: int = Query(6, ge=1, le=12),
    admin: Usuario = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Novos usuarios por mes (clientes vs prestadores)."""
    hoje = datetime.datetime.utcnow()
    resultado = []
    for i in range(meses - 1, -1, -1):
        mes = hoje.month - i
        ano = hoje.year
        while mes <= 0:
            mes += 12
            ano -= 1

        inicio = datetime.datetime(ano, mes, 1)
        if mes == 12:
            fim = datetime.datetime(ano + 1, 1, 1)
        else:
            fim = datetime.datetime(ano, mes + 1, 1)

        novos_clientes = (
            db.query(Usuario)
            .filter(
                Usuario.tipo == "cliente",
                Usuario.is_admin == False,
                Usuario.criado_em >= inicio,
                Usuario.criado_em < fim,
            )
            .count()
        )
        novos_prestadores = (
            db.query(Usuario)
            .filter(
                Usuario.tipo == "prestador",
                Usuario.criado_em >= inicio,
                Usuario.criado_em < fim,
            )
            .count()
        )

        nomes_meses = [
            "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
            "Jul", "Ago", "Set", "Out", "Nov", "Dez",
        ]
        resultado.append({
            "mes": f"{nomes_meses[mes - 1]}/{ano}",
            "clientes": novos_clientes,
            "prestadores": novos_prestadores,
            "total": novos_clientes + novos_prestadores,
        })

    return {"meses": resultado}


@admin_router.get("/analytics/ticket-medio")
def analytics_ticket_medio(
    meses: int = Query(6, ge=1, le=12),
    admin: Usuario = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Ticket medio por mes."""
    hoje = datetime.datetime.utcnow()
    resultado = []
    for i in range(meses - 1, -1, -1):
        mes = hoje.month - i
        ano = hoje.year
        while mes <= 0:
            mes += 12
            ano -= 1

        inicio = datetime.datetime(ano, mes, 1)
        if mes == 12:
            fim = datetime.datetime(ano + 1, 1, 1)
        else:
            fim = datetime.datetime(ano, mes + 1, 1)

        avg_ticket = (
            db.query(func.coalesce(func.avg(SolicitacaoServico.preco_final), 0))
            .filter(
                SolicitacaoServico.status == StatusServico.CONCLUIDO.value,
                SolicitacaoServico.preco_final > 0,
                SolicitacaoServico.criado_em >= inicio,
                SolicitacaoServico.criado_em < fim,
            )
            .scalar()
        )

        nomes_meses = [
            "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
            "Jul", "Ago", "Set", "Out", "Nov", "Dez",
        ]
        resultado.append({
            "mes": f"{nomes_meses[mes - 1]}/{ano}",
            "ticket_medio": round(float(avg_ticket), 2),
        })

    return {"meses": resultado}
