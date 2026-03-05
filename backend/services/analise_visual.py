"""Analise visual de fotos do local usando IA com visao.

Usa Groq Vision API para extrair parametros do local (area, estado,
complexidade, materiais) que sao usados para precificacao mais precisa.
"""
import json
import os

import httpx

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_VISION_MODEL = "llama-3.2-90b-vision-preview"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def analisar_foto_local(foto_base64: str, descricao_servico: str = "") -> dict:
    """Analisa foto do local e extrai parametros para precificacao.

    Args:
        foto_base64: Imagem em base64 (JPEG/PNG)
        descricao_servico: Descricao do que o cliente precisa (contexto)

    Returns:
        Dict com parametros extraidos da imagem
    """
    try:
        return _analisar_groq_vision(foto_base64, descricao_servico)
    except Exception as e:
        print(f"[ANALISE VISUAL FALLBACK] Erro: {e}")
        return _analise_fallback()


def _analisar_groq_vision(foto_base64: str, descricao_servico: str) -> dict:
    """Analise via Groq Vision API."""
    contexto = f'\nO cliente descreveu o servico como: "{descricao_servico}"' if descricao_servico else ""

    prompt = (
        "Voce e um especialista em avaliacao de ambientes para servicos residenciais. "
        "Analise esta foto do local onde o servico sera realizado e extraia os parametros abaixo. "
        f"{contexto}\n\n"
        "Retorne APENAS um JSON valido, sem markdown, sem explicacao:\n"
        "{\n"
        '  "area_m2": <numero estimado de metros quadrados da area visivel, ou null se impossivel estimar>,\n'
        '  "estado_conservacao": "<bom | regular | ruim | critico>",\n'
        '  "complexidade": "<baixa | media | alta | muito alta>",\n'
        '  "materiais_visiveis": "<lista breve dos materiais visiveis: azulejo, madeira, concreto, gesso, etc>",\n'
        '  "acessibilidade": "<facil | moderada | dificil> - facilidade de acesso ao local de trabalho",\n'
        '  "necessita_preparacao": <true ou false - se precisa limpar/mover coisas antes do servico>,\n'
        '  "pontos_de_trabalho": <numero estimado de pontos/areas de intervencao>,\n'
        '  "risco_identificado": "<nenhum | baixo | medio | alto> - riscos visiveis (fiacao exposta, umidade, estrutural)",\n'
        '  "iluminacao": "<boa | razoavel | ruim>",\n'
        '  "observacoes": "<observacoes relevantes para o prestador, max 2 frases>",\n'
        '  "fator_ajuste_preco": <numero entre 0.8 e 2.0 - multiplicador sugerido para o preco base. '
        '1.0 = normal, <1.0 = mais simples que o esperado, >1.0 = mais complexo>\n'
        "}"
    )

    resp = httpx.post(
        GROQ_URL,
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": GROQ_VISION_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{foto_base64}",
                            },
                        },
                    ],
                }
            ],
            "temperature": 0.3,
            "max_tokens": 800,
        },
        timeout=25.0,
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
            if stripped.startswith("{"):
                json_str = stripped
                break

    data = json.loads(json_str)

    # Valida e normaliza
    fator = float(data.get("fator_ajuste_preco", 1.0))
    fator = max(0.8, min(2.0, fator))

    return {
        "area_m2": data.get("area_m2"),
        "estado_conservacao": str(data.get("estado_conservacao", "regular")),
        "complexidade": str(data.get("complexidade", "media")),
        "materiais_visiveis": str(data.get("materiais_visiveis", "")),
        "acessibilidade": str(data.get("acessibilidade", "moderada")),
        "necessita_preparacao": bool(data.get("necessita_preparacao", False)),
        "pontos_de_trabalho": int(data.get("pontos_de_trabalho", 1)),
        "risco_identificado": str(data.get("risco_identificado", "nenhum")),
        "iluminacao": str(data.get("iluminacao", "boa")),
        "observacoes": str(data.get("observacoes", "")),
        "fator_ajuste_preco": fator,
    }


def _analise_fallback() -> dict:
    """Retorna valores padrao quando a analise visual falha."""
    return {
        "area_m2": None,
        "estado_conservacao": "nao analisado",
        "complexidade": "nao analisado",
        "materiais_visiveis": "",
        "acessibilidade": "nao analisado",
        "necessita_preparacao": False,
        "pontos_de_trabalho": 1,
        "risco_identificado": "nao analisado",
        "iluminacao": "nao analisado",
        "observacoes": "Nao foi possivel analisar a foto. Preco baseado apenas na descricao.",
        "fator_ajuste_preco": 1.0,
    }
