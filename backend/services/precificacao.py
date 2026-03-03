"""Motor de precificação inteligente do PASSA.

Analisa a descrição do serviço e calcula faixa de preço
com base em: categoria, complexidade, região, urgência e horário.
"""
import re
from datetime import datetime

# Base de preços por serviço (preço base, min, max, tempo em minutos)
SERVICOS_BASE = {
    # ELÉTRICA
    "trocar resistência": {"base": 150, "min": 100, "max": 200, "tempo": 45, "cat": "eletrica", "complex": 2},
    "trocar chuveiro": {"base": 180, "min": 120, "max": 250, "tempo": 60, "cat": "eletrica", "complex": 2},
    "instalar ventilador": {"base": 160, "min": 100, "max": 220, "tempo": 50, "cat": "eletrica", "complex": 3},
    "instalar luminária": {"base": 120, "min": 80, "max": 180, "tempo": 40, "cat": "eletrica", "complex": 2},
    "trocar tomada": {"base": 80, "min": 50, "max": 120, "tempo": 20, "cat": "eletrica", "complex": 1},
    "trocar interruptor": {"base": 80, "min": 50, "max": 120, "tempo": 20, "cat": "eletrica", "complex": 1},
    "instalar ar condicionado": {"base": 450, "min": 300, "max": 600, "tempo": 180, "cat": "eletrica", "complex": 4},
    "quadro elétrico": {"base": 500, "min": 350, "max": 800, "tempo": 240, "cat": "eletrica", "complex": 5},
    "fiação": {"base": 350, "min": 200, "max": 600, "tempo": 180, "cat": "eletrica", "complex": 4},
    "curto circuito": {"base": 200, "min": 150, "max": 350, "tempo": 60, "cat": "eletrica", "complex": 3},

    # HIDRÁULICA
    "vazamento": {"base": 200, "min": 120, "max": 350, "tempo": 60, "cat": "hidraulica", "complex": 3},
    "desentupir": {"base": 180, "min": 100, "max": 300, "tempo": 60, "cat": "hidraulica", "complex": 3},
    "trocar torneira": {"base": 120, "min": 80, "max": 180, "tempo": 30, "cat": "hidraulica", "complex": 1},
    "instalar torneira": {"base": 130, "min": 80, "max": 200, "tempo": 40, "cat": "hidraulica", "complex": 2},
    "trocar sifão": {"base": 100, "min": 60, "max": 150, "tempo": 25, "cat": "hidraulica", "complex": 1},
    "vaso sanitário": {"base": 250, "min": 150, "max": 400, "tempo": 90, "cat": "hidraulica", "complex": 3},
    "caixa d'água": {"base": 300, "min": 200, "max": 500, "tempo": 120, "cat": "hidraulica", "complex": 3},
    "encanamento": {"base": 350, "min": 200, "max": 600, "tempo": 180, "cat": "hidraulica", "complex": 4},
    "aquecedor": {"base": 400, "min": 250, "max": 600, "tempo": 120, "cat": "hidraulica", "complex": 4},

    # PINTURA
    "pintar parede": {"base": 200, "min": 120, "max": 400, "tempo": 120, "cat": "pintura", "complex": 2},
    "pintar quarto": {"base": 500, "min": 350, "max": 800, "tempo": 360, "cat": "pintura", "complex": 3},
    "pintar sala": {"base": 600, "min": 400, "max": 1000, "tempo": 480, "cat": "pintura", "complex": 3},
    "pintar apartamento": {"base": 2500, "min": 1500, "max": 4000, "tempo": 2400, "cat": "pintura", "complex": 4},
    "pintar casa": {"base": 4000, "min": 2500, "max": 7000, "tempo": 4800, "cat": "pintura", "complex": 5},
    "pintar portão": {"base": 250, "min": 150, "max": 400, "tempo": 180, "cat": "pintura", "complex": 2},
    "textura": {"base": 350, "min": 200, "max": 600, "tempo": 240, "cat": "pintura", "complex": 3},
    "grafiato": {"base": 400, "min": 250, "max": 650, "tempo": 300, "cat": "pintura", "complex": 4},

    # MONTAGEM
    "montar móvel": {"base": 150, "min": 80, "max": 250, "tempo": 90, "cat": "montagem", "complex": 2},
    "montar guarda-roupa": {"base": 250, "min": 150, "max": 400, "tempo": 180, "cat": "montagem", "complex": 3},
    "montar cozinha": {"base": 400, "min": 250, "max": 600, "tempo": 300, "cat": "montagem", "complex": 4},
    "instalar prateleira": {"base": 100, "min": 60, "max": 160, "tempo": 30, "cat": "montagem", "complex": 1},
    "instalar cortina": {"base": 120, "min": 80, "max": 180, "tempo": 40, "cat": "montagem", "complex": 2},
    "instalar suporte tv": {"base": 150, "min": 100, "max": 250, "tempo": 45, "cat": "montagem", "complex": 2},

    # LIMPEZA
    "limpeza residencial": {"base": 200, "min": 120, "max": 350, "tempo": 240, "cat": "limpeza", "complex": 2},
    "limpeza pós-obra": {"base": 500, "min": 300, "max": 800, "tempo": 480, "cat": "limpeza", "complex": 3},
    "limpar caixa d'água": {"base": 250, "min": 150, "max": 400, "tempo": 120, "cat": "limpeza", "complex": 3},
    "impermeabilização": {"base": 600, "min": 350, "max": 1000, "tempo": 300, "cat": "limpeza", "complex": 4},

    # JARDINAGEM
    "podar árvore": {"base": 200, "min": 100, "max": 400, "tempo": 120, "cat": "jardinagem", "complex": 3},
    "cortar grama": {"base": 150, "min": 80, "max": 250, "tempo": 90, "cat": "jardinagem", "complex": 1},
    "jardim": {"base": 300, "min": 150, "max": 500, "tempo": 180, "cat": "jardinagem", "complex": 3},

    # REFORMA
    "trocar piso": {"base": 800, "min": 500, "max": 1500, "tempo": 480, "cat": "reforma", "complex": 4},
    "assentar piso": {"base": 900, "min": 600, "max": 1600, "tempo": 480, "cat": "reforma", "complex": 4},
    "reboco": {"base": 500, "min": 300, "max": 800, "tempo": 300, "cat": "reforma", "complex": 3},
    "gesso": {"base": 400, "min": 250, "max": 700, "tempo": 240, "cat": "reforma", "complex": 3},
    "drywall": {"base": 500, "min": 300, "max": 800, "tempo": 300, "cat": "reforma", "complex": 3},
    "contrapiso": {"base": 600, "min": 400, "max": 1000, "tempo": 360, "cat": "reforma", "complex": 4},

    # MANUTENÇÃO
    "fechadura": {"base": 150, "min": 80, "max": 250, "tempo": 40, "cat": "manutencao", "complex": 2},
    "porta": {"base": 200, "min": 120, "max": 350, "tempo": 60, "cat": "manutencao", "complex": 2},
    "janela": {"base": 200, "min": 120, "max": 350, "tempo": 60, "cat": "manutencao", "complex": 2},
    "calha": {"base": 250, "min": 150, "max": 400, "tempo": 90, "cat": "manutencao", "complex": 3},
    "telhado": {"base": 500, "min": 300, "max": 900, "tempo": 240, "cat": "manutencao", "complex": 4},
}

# Multiplicadores por região (São Paulo como base)
MULTIPLICADOR_REGIAO = {
    "centro": 1.20,
    "zona sul": 1.15,
    "zona oeste": 1.15,
    "zona norte": 1.00,
    "zona leste": 0.95,
    "jardins": 1.30,
    "pinheiros": 1.25,
    "moema": 1.25,
    "itaim": 1.30,
    "vila mariana": 1.10,
    "tatuapé": 1.05,
    "santana": 1.05,
    "default": 1.00,
}


def _normalizar(texto: str) -> str:
    """Remove acentos e normaliza texto para busca."""
    texto = texto.lower().strip()
    substituicoes = {
        "á": "a", "à": "a", "ã": "a", "â": "a",
        "é": "e", "ê": "e",
        "í": "i",
        "ó": "o", "ô": "o", "õ": "o",
        "ú": "u", "ü": "u",
        "ç": "c",
    }
    for orig, sub in substituicoes.items():
        texto = texto.replace(orig, sub)
    return texto


def _encontrar_servico(descricao: str) -> dict | None:
    """Encontra o serviço mais relevante pela descrição."""
    descricao_norm = _normalizar(descricao)
    melhor_match = None
    melhor_score = 0

    for chave, dados in SERVICOS_BASE.items():
        chave_norm = _normalizar(chave)
        palavras_chave = chave_norm.split()
        score = 0
        for palavra in palavras_chave:
            if palavra in descricao_norm:
                score += len(palavra)
        if score > melhor_score:
            melhor_score = score
            melhor_match = dados

    return melhor_match if melhor_score > 0 else None


def _extrair_dimensoes(descricao: str) -> float:
    """Extrai dimensões mencionadas (ex: 3x2m = 6m²)."""
    padrao = re.findall(r"(\d+(?:[.,]\d+)?)\s*[xX×]\s*(\d+(?:[.,]\d+)?)\s*m", descricao)
    if padrao:
        largura = float(padrao[0][0].replace(",", "."))
        altura = float(padrao[0][1].replace(",", "."))
        return largura * altura

    padrao_m2 = re.findall(r"(\d+(?:[.,]\d+)?)\s*m[²2]", descricao)
    if padrao_m2:
        return float(padrao_m2[0].replace(",", "."))

    return 0.0


def _calcular_multiplicador_urgencia(urgente: bool) -> float:
    """Serviço urgente custa mais."""
    return 1.35 if urgente else 1.0


def _calcular_multiplicador_horario() -> float:
    """Horário fora do comercial custa mais."""
    hora = datetime.now().hour
    if hora < 8 or hora > 18:
        return 1.20
    if hora > 17:
        return 1.10
    return 1.0


def precificar(descricao: str, regiao: str = "", urgente: bool = False) -> dict:
    """Precifica um serviço com base na descrição.

    Returns:
        dict com preco_min, preco_max, tempo_estimado, categoria, complexidade, confianca
    """
    servico = _encontrar_servico(descricao)

    if not servico:
        return {
            "preco_min": 100,
            "preco_max": 300,
            "preco_sugerido": 200,
            "tempo_estimado_min": 60,
            "categoria": "outros",
            "complexidade": 2,
            "confianca": 0.3,
            "detalhes": "Serviço não identificado com precisão. Faixa estimada genérica.",
        }

    base = servico["base"]
    preco_min = servico["min"]
    preco_max = servico["max"]
    tempo = servico["tempo"]
    categoria = servico["cat"]
    complexidade = servico["complex"]

    # Ajuste por dimensões
    area = _extrair_dimensoes(descricao)
    if area > 0:
        fator_area = max(0.5, min(area / 10.0, 3.0))
        base = base * fator_area
        preco_min = preco_min * fator_area
        preco_max = preco_max * fator_area
        tempo = int(tempo * fator_area)

    # Ajuste por região
    regiao_norm = _normalizar(regiao) if regiao else "default"
    mult_regiao = MULTIPLICADOR_REGIAO.get(regiao_norm, 1.0)
    base *= mult_regiao
    preco_min *= mult_regiao
    preco_max *= mult_regiao

    # Ajuste por urgência
    mult_urgencia = _calcular_multiplicador_urgencia(urgente)
    base *= mult_urgencia
    preco_min *= mult_urgencia
    preco_max *= mult_urgencia

    # Ajuste por horário
    mult_horario = _calcular_multiplicador_horario()
    base *= mult_horario
    preco_min *= mult_horario
    preco_max *= mult_horario

    # Verificação 220v / trifásico
    if "220" in descricao or "trifásico" in descricao.lower() or "trifasico" in descricao.lower():
        base *= 1.15
        preco_min *= 1.10
        preco_max *= 1.20
        complexidade = min(5, complexidade + 1)

    preco_min = round(preco_min, 2)
    preco_max = round(preco_max, 2)
    preco_sugerido = round(base, 2)

    detalhes_parts = [f"Categoria: {categoria}"]
    if area > 0:
        detalhes_parts.append(f"Área detectada: {area:.1f}m²")
    if urgente:
        detalhes_parts.append("Acréscimo urgência: +35%")
    if mult_regiao != 1.0:
        detalhes_parts.append(f"Ajuste regional: {mult_regiao:.0%}")
    detalhes_parts.append(f"Complexidade: {complexidade}/5")

    return {
        "preco_min": preco_min,
        "preco_max": preco_max,
        "preco_sugerido": preco_sugerido,
        "tempo_estimado_min": tempo,
        "categoria": categoria,
        "complexidade": complexidade,
        "confianca": 0.85,
        "detalhes": " | ".join(detalhes_parts),
    }
