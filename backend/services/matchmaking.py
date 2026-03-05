"""Matchmaking inteligente entre clientes e prestadores usando IA.

Compara a descricao do servico solicitado pelo cliente com a descricao
de servicos de cada prestador usando Groq LLM para matching semantico.
"""
import json
import os

import httpx

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def matchmaking_ia(descricao_cliente: str, prestadores: list[dict]) -> list[dict]:
    """Faz matchmaking usando IA entre descricao do cliente e prestadores.

    Args:
        descricao_cliente: O que o cliente precisa (ex: "trocar chuveiro eletrico")
        prestadores: Lista de dicts com {id, nome, descricao_servicos, regiao, score}

    Returns:
        Lista de prestadores ordenada por relevancia, com campo 'relevancia' (0-100)
    """
    if not prestadores:
        return []

    try:
        return _matchmaking_groq(descricao_cliente, prestadores)
    except Exception as e:
        print(f"[MATCHMAKING FALLBACK] Erro na IA: {e}")
        return _matchmaking_fallback(descricao_cliente, prestadores)


def _matchmaking_groq(descricao_cliente: str, prestadores: list[dict]) -> list[dict]:
    """Matchmaking via Groq API."""
    # Monta a lista de prestadores para o prompt (max 20)
    lista = prestadores[:20]
    profs_texto = ""
    for p in lista:
        profs_texto += (
            f"ID: {p['id']} | Nome: {p['nome']} | "
            f"Servicos: {p['descricao_servicos'] or 'nao informado'} | "
            f"Regiao: {p['regiao'] or 'nao informada'}\n"
        )

    prompt = (
        "Voce e um sistema de matchmaking de servicos residenciais. "
        "O cliente descreveu o que precisa, e voce tem uma lista de prestadores "
        "com a descricao dos servicos que cada um oferece.\n\n"
        "Analise a COMPATIBILIDADE entre o que o cliente precisa e o que cada "
        "prestador sabe fazer. Considere:\n"
        "- Relevancia direta (o prestador faz exatamente o que o cliente precisa)\n"
        "- Relevancia parcial (o prestador tem habilidades relacionadas)\n"
        "- Especialidade (o prestador menciona especificamente esse tipo de trabalho)\n\n"
        f"PEDIDO DO CLIENTE: {descricao_cliente}\n\n"
        f"PRESTADORES DISPONIVEIS:\n{profs_texto}\n"
        "Retorne APENAS um JSON valido, sem markdown, sem explicacao. "
        "O JSON deve ser uma lista de objetos com os campos:\n"
        '[{"id": <id>, "relevancia": <0 a 100>, "motivo": "<frase curta>"}]\n\n'
        "REGRAS:\n"
        "- relevancia 80-100: match direto (prestador faz exatamente isso)\n"
        "- relevancia 50-79: match parcial (area relacionada)\n"
        "- relevancia 1-49: match fraco\n"
        "- relevancia 0: sem relacao nenhuma\n"
        "- NAO inclua prestadores com relevancia 0\n"
        "- Ordene do mais relevante para o menos relevante"
    )

    resp = httpx.post(
        GROQ_URL,
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 1000,
        },
        timeout=15.0,
    )
    resp.raise_for_status()

    content = resp.json()["choices"][0]["message"]["content"]

    # Extrai JSON
    json_str = content
    if "```" in content:
        parts = content.split("```")
        for part in parts:
            stripped = part.strip()
            if stripped.startswith("json"):
                stripped = stripped[4:].strip()
            if stripped.startswith("["):
                json_str = stripped
                break

    rankings = json.loads(json_str)

    # Monta mapa de prestadores por ID
    profs_map = {p["id"]: p for p in prestadores}
    resultado = []

    for r in rankings:
        prof_id = r.get("id")
        relevancia = r.get("relevancia", 0)
        motivo = r.get("motivo", "")

        if prof_id in profs_map and relevancia > 0:
            prof = profs_map[prof_id].copy()
            prof["relevancia"] = relevancia
            prof["motivo_match"] = motivo
            resultado.append(prof)

    return resultado


def _matchmaking_fallback(descricao_cliente: str, prestadores: list[dict]) -> list[dict]:
    """Fallback: matching por palavras-chave quando a IA falha."""
    import unicodedata

    def normalizar(texto):
        texto = texto.lower().strip()
        texto = unicodedata.normalize("NFD", texto)
        texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
        return texto

    desc_cliente = normalizar(descricao_cliente)
    palavras_cliente = set(desc_cliente.split())
    stopwords = {
        "de", "do", "da", "dos", "das", "em", "no", "na", "um", "uma",
        "para", "por", "com", "que", "e", "ou", "o", "a", "os", "as",
        "eu", "meu", "minha", "preciso", "quero", "servico",
    }
    palavras_cliente = {p for p in palavras_cliente if len(p) > 2 and p not in stopwords}

    resultado = []
    for prof in prestadores:
        desc_prof = normalizar(prof.get("descricao_servicos") or "")
        palavras_prof = set(desc_prof.split())

        if not palavras_cliente or not palavras_prof:
            continue

        # Match exato + substring
        matches = palavras_cliente & palavras_prof
        for pc in palavras_cliente:
            for pp in palavras_prof:
                if len(pc) >= 4 and (pc in pp or pp in pc):
                    matches.add(pc)

        if not matches:
            continue

        relevancia = int((len(matches) / len(palavras_cliente)) * 100)
        relevancia = min(relevancia, 95)  # Cap no fallback

        p = prof.copy()
        p["relevancia"] = relevancia
        p["motivo_match"] = f"Palavras em comum: {', '.join(list(matches)[:5])}"
        resultado.append(p)

    resultado.sort(key=lambda x: x["relevancia"], reverse=True)
    return resultado
