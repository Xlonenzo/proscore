"""Sistema de Score do Profissional PASSA.

Score de 0 a 1000 baseado em:
- Pontualidade (20%)
- Avaliação média (25%)
- Reclamações (20%)
- Frequência de uso (10%)
- Recorrência (15%)
- Compliance (10%)
"""


def calcular_score(
    pontualidade: float = 100.0,
    avaliacao_media: float = 5.0,
    taxa_reclamacao: float = 0.0,
    frequencia_uso: float = 50.0,
    recorrencia: float = 50.0,
    compliance: float = 100.0,
) -> dict:
    """Calcula o score do profissional (0-1000).

    Args:
        pontualidade: % de serviços pontuais (0-100)
        avaliacao_media: Nota média de avaliação (0-5)
        taxa_reclamacao: % de serviços com reclamação (0-100)
        frequencia_uso: Frequência de uso da plataforma (0-100)
        recorrencia: % de clientes que voltam (0-100)
        compliance: % de conformidade com regras (0-100)

    Returns:
        dict com score, nivel, detalhamento
    """
    # Normalizar cada componente para 0-1000
    s_pontualidade = (pontualidade / 100.0) * 1000
    s_avaliacao = (avaliacao_media / 5.0) * 1000
    s_reclamacao = ((100.0 - taxa_reclamacao) / 100.0) * 1000
    s_frequencia = (frequencia_uso / 100.0) * 1000
    s_recorrencia = (recorrencia / 100.0) * 1000
    s_compliance = (compliance / 100.0) * 1000

    # Pesos
    score = (
        s_pontualidade * 0.20
        + s_avaliacao * 0.25
        + s_reclamacao * 0.20
        + s_frequencia * 0.10
        + s_recorrencia * 0.15
        + s_compliance * 0.10
    )

    score = round(max(0, min(1000, score)), 1)

    # Classificação
    if score >= 850:
        nivel = "ELITE"
        descricao = "Profissional excepcional. Prioridade máxima."
        cor = "#00C853"
    elif score >= 700:
        nivel = "OURO"
        descricao = "Profissional excelente. Alta visibilidade."
        cor = "#FFD600"
    elif score >= 500:
        nivel = "PRATA"
        descricao = "Profissional bom. Visibilidade normal."
        cor = "#90A4AE"
    elif score >= 300:
        nivel = "BRONZE"
        descricao = "Profissional em desenvolvimento. Baixa visibilidade."
        cor = "#BF360C"
    else:
        nivel = "INICIANTE"
        descricao = "Novo na plataforma ou com baixo desempenho."
        cor = "#757575"

    return {
        "score": score,
        "nivel": nivel,
        "descricao": descricao,
        "cor": cor,
        "detalhamento": {
            "pontualidade": {"valor": pontualidade, "peso": "20%", "pontos": round(s_pontualidade * 0.20, 1)},
            "avaliacao": {"valor": avaliacao_media, "peso": "25%", "pontos": round(s_avaliacao * 0.25, 1)},
            "reclamacoes": {"valor": taxa_reclamacao, "peso": "20%", "pontos": round(s_reclamacao * 0.20, 1)},
            "frequencia": {"valor": frequencia_uso, "peso": "10%", "pontos": round(s_frequencia * 0.10, 1)},
            "recorrencia": {"valor": recorrencia, "peso": "15%", "pontos": round(s_recorrencia * 0.15, 1)},
            "compliance": {"valor": compliance, "peso": "10%", "pontos": round(s_compliance * 0.10, 1)},
        },
    }


def atualizar_score_profissional(profissional) -> dict:
    """Recalcula o score de um profissional baseado nos dados do banco."""
    taxa_reclamacao = 0.0
    if profissional.total_servicos > 0:
        taxa_reclamacao = (
            profissional.total_reclamacoes / profissional.total_servicos
        ) * 100

    resultado = calcular_score(
        pontualidade=profissional.pontualidade,
        avaliacao_media=profissional.avaliacao_media,
        taxa_reclamacao=taxa_reclamacao,
        frequencia_uso=profissional.frequencia_uso,
        recorrencia=profissional.recorrencia,
        compliance=profissional.compliance,
    )

    profissional.score = resultado["score"]
    return resultado
