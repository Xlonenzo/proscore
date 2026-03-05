"""Motor de precificacao inteligente do PASSA.

Usa tabela de referencia de precos do mercado brasileiro + Groq Vision API
para precificar com base na descricao E na foto do local.
"""
import json
import os

import httpx

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_VISION_MODEL = "llama-3.2-90b-vision-preview"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

CATEGORIAS_VALIDAS = [
    "eletrica", "hidraulica", "pintura", "montagem",
    "limpeza", "jardinagem", "reforma", "manutencao", "outros",
]

# ===== Tabela de referencia de precos — mercado brasileiro 2025 =====
# Fontes: GetNinjas, Triider, Trice Brasil, Cronoshare, SOS Reformas, ReparosRMC,
#         Engehall, Habitissimo, SINAPI/Caixa, mercado real SP/RJ 2024/2025
# Formato: descricao, preco_min, preco_base, preco_max, tempo_min, categoria, complexidade

TABELA_PRECOS = [
    # ELETRICA
    {"servico": "Trocar tomada simples", "min": 30, "base": 50, "max": 70, "tempo": 20, "cat": "eletrica", "cx": 1},
    {"servico": "Instalar 10 tomadas", "min": 300, "base": 500, "max": 700, "tempo": 120, "cat": "eletrica", "cx": 3},
    {"servico": "Trocar interruptor simples", "min": 25, "base": 45, "max": 60, "tempo": 20, "cat": "eletrica", "cx": 1},
    {"servico": "Instalar interruptor three-way/four-way", "min": 60, "base": 75, "max": 85, "tempo": 30, "cat": "eletrica", "cx": 2},
    {"servico": "Instalar luminaria simples", "min": 70, "base": 120, "max": 300, "tempo": 40, "cat": "eletrica", "cx": 2},
    {"servico": "Instalar spot LED embutido", "min": 60, "base": 75, "max": 90, "tempo": 30, "cat": "eletrica", "cx": 2},
    {"servico": "Instalar luminaria com furo em gesso/laje", "min": 150, "base": 200, "max": 300, "tempo": 60, "cat": "eletrica", "cx": 3},
    {"servico": "Trocar resistencia de chuveiro", "min": 80, "base": 130, "max": 180, "tempo": 30, "cat": "eletrica", "cx": 2},
    {"servico": "Instalar chuveiro eletrico completo", "min": 80, "base": 130, "max": 180, "tempo": 60, "cat": "eletrica", "cx": 3},
    {"servico": "Instalar ventilador de teto", "min": 100, "base": 200, "max": 350, "tempo": 50, "cat": "eletrica", "cx": 3},
    {"servico": "Trocar disjuntor", "min": 50, "base": 90, "max": 130, "tempo": 30, "cat": "eletrica", "cx": 2},
    {"servico": "Instalar disjuntor individual (chuveiro)", "min": 90, "base": 150, "max": 200, "tempo": 40, "cat": "eletrica", "cx": 2},
    {"servico": "Instalar quadro de distribuicao", "min": 1200, "base": 1450, "max": 1700, "tempo": 180, "cat": "eletrica", "cx": 4},
    {"servico": "Passar fiacao (por ponto)", "min": 35, "base": 45, "max": 50, "tempo": 60, "cat": "eletrica", "cx": 3},
    {"servico": "Instalar ar condicionado split (12000 BTU)", "min": 450, "base": 650, "max": 900, "tempo": 180, "cat": "eletrica", "cx": 4},
    {"servico": "Instalar ar condicionado split (complexo, fachada)", "min": 900, "base": 1050, "max": 1200, "tempo": 240, "cat": "eletrica", "cx": 5},
    {"servico": "Tubulacao extra ar condicionado (por metro)", "min": 25, "base": 35, "max": 45, "tempo": 15, "cat": "eletrica", "cx": 2},
    {"servico": "Instalar interfone / video porteiro", "min": 150, "base": 225, "max": 300, "tempo": 120, "cat": "eletrica", "cx": 3},
    {"servico": "Instalar campainha", "min": 150, "base": 175, "max": 200, "tempo": 40, "cat": "eletrica", "cx": 2},
    {"servico": "Instalar fotocélula/sensor de presenca", "min": 80, "base": 100, "max": 120, "tempo": 30, "cat": "eletrica", "cx": 2},
    {"servico": "Cabeamento de rede (por ponto)", "min": 100, "base": 150, "max": 250, "tempo": 60, "cat": "eletrica", "cx": 3},
    {"servico": "Reparo fiacao eletrica", "min": 250, "base": 325, "max": 400, "tempo": 90, "cat": "eletrica", "cx": 3},
    {"servico": "Visita tecnica eletricista", "min": 80, "base": 115, "max": 150, "tempo": 30, "cat": "eletrica", "cx": 1},

    # HIDRAULICA
    {"servico": "Trocar torneira simples", "min": 50, "base": 90, "max": 125, "tempo": 30, "cat": "hidraulica", "cx": 1},
    {"servico": "Instalar torneira com filtro/purificador", "min": 120, "base": 185, "max": 250, "tempo": 40, "cat": "hidraulica", "cx": 2},
    {"servico": "Desentupir pia/ralo", "min": 180, "base": 215, "max": 250, "tempo": 45, "cat": "hidraulica", "cx": 2},
    {"servico": "Desentupir vaso sanitario", "min": 120, "base": 350, "max": 600, "tempo": 60, "cat": "hidraulica", "cx": 3},
    {"servico": "Consertar vazamento simples", "min": 150, "base": 190, "max": 228, "tempo": 45, "cat": "hidraulica", "cx": 2},
    {"servico": "Caca vazamento (deteccao)", "min": 400, "base": 500, "max": 600, "tempo": 120, "cat": "hidraulica", "cx": 3},
    {"servico": "Consertar vazamento embutido (quebrar parede)", "min": 250, "base": 400, "max": 700, "tempo": 180, "cat": "hidraulica", "cx": 4},
    {"servico": "Trocar vaso sanitario", "min": 120, "base": 280, "max": 450, "tempo": 90, "cat": "hidraulica", "cx": 3},
    {"servico": "Trocar mecanismo caixa descarga completo", "min": 58, "base": 75, "max": 90, "tempo": 30, "cat": "hidraulica", "cx": 2},
    {"servico": "Trocar sifao", "min": 50, "base": 60, "max": 80, "tempo": 20, "cat": "hidraulica", "cx": 1},
    {"servico": "Trocar registro de agua", "min": 150, "base": 220, "max": 300, "tempo": 40, "cat": "hidraulica", "cx": 2},
    {"servico": "Instalar caixa dagua", "min": 200, "base": 350, "max": 600, "tempo": 120, "cat": "hidraulica", "cx": 4},
    {"servico": "Trocar boia caixa dagua", "min": 80, "base": 100, "max": 120, "tempo": 30, "cat": "hidraulica", "cx": 2},
    {"servico": "Instalar aquecedor a gas", "min": 300, "base": 500, "max": 800, "tempo": 180, "cat": "hidraulica", "cx": 4},
    {"servico": "Instalar aquecedor instantaneo", "min": 80, "base": 100, "max": 120, "tempo": 60, "cat": "hidraulica", "cx": 3},
    {"servico": "Instalar maquina de lavar", "min": 80, "base": 115, "max": 150, "tempo": 30, "cat": "hidraulica", "cx": 2},
    {"servico": "Instalar lava-loucas", "min": 60, "base": 80, "max": 100, "tempo": 30, "cat": "hidraulica", "cx": 2},
    {"servico": "Limpeza caixa de gordura", "min": 130, "base": 260, "max": 390, "tempo": 60, "cat": "hidraulica", "cx": 2},
    {"servico": "Ponto adicional agua externo", "min": 70, "base": 90, "max": 110, "tempo": 40, "cat": "hidraulica", "cx": 2},
    {"servico": "Ponto adicional agua interno", "min": 100, "base": 130, "max": 160, "tempo": 50, "cat": "hidraulica", "cx": 3},

    # PINTURA
    {"servico": "Pintar parede simples (ate 10m2)", "min": 180, "base": 280, "max": 400, "tempo": 120, "cat": "pintura", "cx": 2},
    {"servico": "Pintar parede interna (por m2, mao de obra)", "min": 18, "base": 27, "max": 35, "tempo": 15, "cat": "pintura", "cx": 2},
    {"servico": "Pintar quarto completo (paredes + teto)", "min": 400, "base": 600, "max": 900, "tempo": 360, "cat": "pintura", "cx": 3},
    {"servico": "Pintar sala (ate 20m2)", "min": 500, "base": 800, "max": 1200, "tempo": 480, "cat": "pintura", "cx": 3},
    {"servico": "Pintar apartamento completo (2 quartos)", "min": 1500, "base": 2500, "max": 4000, "tempo": 2400, "cat": "pintura", "cx": 4},
    {"servico": "Pintar casa completa (70m2)", "min": 3500, "base": 5000, "max": 7000, "tempo": 3600, "cat": "pintura", "cx": 4},
    {"servico": "Pintar fachada/muro externo (por m2)", "min": 25, "base": 30, "max": 35, "tempo": 30, "cat": "pintura", "cx": 3},
    {"servico": "Aplicar textura/grafiato (por m2)", "min": 25, "base": 35, "max": 45, "tempo": 40, "cat": "pintura", "cx": 3},
    {"servico": "Pintura decorativa/efeito especial (por m2)", "min": 50, "base": 65, "max": 80, "tempo": 50, "cat": "pintura", "cx": 4},
    {"servico": "Aplicar massa corrida (por m2)", "min": 12, "base": 18, "max": 25, "tempo": 20, "cat": "pintura", "cx": 2},
    {"servico": "Pintar portao/grade metalica", "min": 200, "base": 350, "max": 550, "tempo": 180, "cat": "pintura", "cx": 3},
    {"servico": "Pintar porta/janela", "min": 120, "base": 230, "max": 350, "tempo": 90, "cat": "pintura", "cx": 2},

    # MONTAGEM
    {"servico": "Montar movel simples (estante, mesa)", "min": 90, "base": 150, "max": 250, "tempo": 60, "cat": "montagem", "cx": 2},
    {"servico": "Montar guarda-roupa", "min": 200, "base": 300, "max": 500, "tempo": 180, "cat": "montagem", "cx": 3},
    {"servico": "Montar cozinha planejada", "min": 500, "base": 800, "max": 1500, "tempo": 480, "cat": "montagem", "cx": 4},
    {"servico": "Montar cama box", "min": 80, "base": 120, "max": 180, "tempo": 40, "cat": "montagem", "cx": 1},
    {"servico": "Montar rack/painel TV", "min": 120, "base": 180, "max": 250, "tempo": 60, "cat": "montagem", "cx": 2},
    {"servico": "Desmontar e remontar movel", "min": 180, "base": 260, "max": 350, "tempo": 120, "cat": "montagem", "cx": 3},
    {"servico": "Instalar prateleira/nicho", "min": 80, "base": 130, "max": 250, "tempo": 40, "cat": "montagem", "cx": 2},
    {"servico": "Instalar suporte TV na parede", "min": 120, "base": 200, "max": 300, "tempo": 40, "cat": "montagem", "cx": 2},
    {"servico": "Instalar cortina/varao", "min": 90, "base": 170, "max": 250, "tempo": 30, "cat": "montagem", "cx": 2},
    {"servico": "Instalar persiana", "min": 90, "base": 170, "max": 250, "tempo": 30, "cat": "montagem", "cx": 2},
    {"servico": "Instalar varal", "min": 54, "base": 72, "max": 90, "tempo": 30, "cat": "montagem", "cx": 1},
    {"servico": "Instalar quadro/espelho pequeno", "min": 40, "base": 60, "max": 80, "tempo": 20, "cat": "montagem", "cx": 1},
    {"servico": "Instalar quadro/espelho grande", "min": 60, "base": 90, "max": 120, "tempo": 30, "cat": "montagem", "cx": 2},

    # LIMPEZA
    {"servico": "Limpeza residencial (apartamento ate 70m2)", "min": 150, "base": 200, "max": 300, "tempo": 240, "cat": "limpeza", "cx": 2},
    {"servico": "Limpeza residencial (casa ate 150m2)", "min": 250, "base": 350, "max": 500, "tempo": 360, "cat": "limpeza", "cx": 3},
    {"servico": "Limpeza pos-obra (por m2)", "min": 8, "base": 15, "max": 23, "tempo": 30, "cat": "limpeza", "cx": 3},
    {"servico": "Limpeza pos-obra (apartamento medio)", "min": 600, "base": 1200, "max": 2500, "tempo": 480, "cat": "limpeza", "cx": 4},
    {"servico": "Limpeza de vidros/janelas (por unidade)", "min": 30, "base": 50, "max": 80, "tempo": 20, "cat": "limpeza", "cx": 2},
    {"servico": "Higienizacao de sofa (2-3 lugares)", "min": 120, "base": 180, "max": 280, "tempo": 60, "cat": "limpeza", "cx": 2},
    {"servico": "Limpeza de caixa dagua (ate 1000L, terreo)", "min": 200, "base": 250, "max": 300, "tempo": 90, "cat": "limpeza", "cx": 3},
    {"servico": "Limpeza de caixa dagua (ate 1000L, sobrado)", "min": 250, "base": 300, "max": 400, "tempo": 90, "cat": "limpeza", "cx": 3},

    # JARDINAGEM
    {"servico": "Cortar grama (ate 50m2)", "min": 80, "base": 130, "max": 200, "tempo": 60, "cat": "jardinagem", "cx": 2},
    {"servico": "Limpeza jardim (ate 25m2)", "min": 150, "base": 200, "max": 250, "tempo": 60, "cat": "jardinagem", "cx": 2},
    {"servico": "Limpeza jardim (ate 50m2)", "min": 250, "base": 350, "max": 450, "tempo": 120, "cat": "jardinagem", "cx": 2},
    {"servico": "Limpeza jardim (ate 100m2)", "min": 400, "base": 600, "max": 800, "tempo": 180, "cat": "jardinagem", "cx": 3},
    {"servico": "Podar arvore/arbusto", "min": 150, "base": 300, "max": 500, "tempo": 120, "cat": "jardinagem", "cx": 3},
    {"servico": "Poda de 5 arvores + remocao", "min": 400, "base": 600, "max": 800, "tempo": 240, "cat": "jardinagem", "cx": 3},
    {"servico": "Manutencao de jardim completa (mensal)", "min": 240, "base": 700, "max": 1280, "tempo": 240, "cat": "jardinagem", "cx": 3},
    {"servico": "Plantio e paisagismo basico", "min": 3000, "base": 6000, "max": 10000, "tempo": 1200, "cat": "jardinagem", "cx": 4},
    {"servico": "Remocao de toco/raiz", "min": 200, "base": 400, "max": 700, "tempo": 180, "cat": "jardinagem", "cx": 4},

    # REFORMA / PEDREIRO
    {"servico": "Trocar piso ceramico (por m2, autonomo)", "min": 45, "base": 70, "max": 100, "tempo": 60, "cat": "reforma", "cx": 3},
    {"servico": "Instalar porcelanato (por m2, autonomo)", "min": 45, "base": 75, "max": 100, "tempo": 60, "cat": "reforma", "cx": 3},
    {"servico": "Instalar porcelanato (por m2, empresa)", "min": 80, "base": 130, "max": 180, "tempo": 60, "cat": "reforma", "cx": 3},
    {"servico": "Trabalho complexo em piso (recortes, paginacao, por m2)", "min": 80, "base": 115, "max": 150, "tempo": 75, "cat": "reforma", "cx": 4},
    {"servico": "Substituir piso/revestimento (por m2)", "min": 100, "base": 150, "max": 200, "tempo": 60, "cat": "reforma", "cx": 3},
    {"servico": "Rejunte piso/azulejo", "min": 200, "base": 250, "max": 300, "tempo": 120, "cat": "reforma", "cx": 2},
    {"servico": "Assentar revestimento parede (por m2)", "min": 50, "base": 80, "max": 120, "tempo": 50, "cat": "reforma", "cx": 3},
    {"servico": "Construir parede de drywall (por m2, material + mao)", "min": 65, "base": 110, "max": 160, "tempo": 60, "cat": "reforma", "cx": 3},
    {"servico": "Reparo drywall/gesso", "min": 200, "base": 250, "max": 300, "tempo": 60, "cat": "reforma", "cx": 2},
    {"servico": "Forro de gesso (por m2, material + mao)", "min": 70, "base": 105, "max": 140, "tempo": 45, "cat": "reforma", "cx": 3},
    {"servico": "Reboco de parede (por m2)", "min": 30, "base": 50, "max": 80, "tempo": 40, "cat": "reforma", "cx": 2},
    {"servico": "Reparo parede (por m2)", "min": 20, "base": 25, "max": 30, "tempo": 30, "cat": "reforma", "cx": 2},
    {"servico": "Contrapiso (por m2)", "min": 40, "base": 65, "max": 100, "tempo": 45, "cat": "reforma", "cx": 2},
    {"servico": "Impermeabilizacao laje (por m2)", "min": 25, "base": 50, "max": 80, "tempo": 30, "cat": "reforma", "cx": 3},
    {"servico": "Reparo infiltracao", "min": 300, "base": 400, "max": 500, "tempo": 120, "cat": "reforma", "cx": 3},
    {"servico": "Reforma banheiro completo (pequeno, 3m2)", "min": 5000, "base": 8000, "max": 12000, "tempo": 4800, "cat": "reforma", "cx": 5},
    {"servico": "Reforma cozinha completa (10m2)", "min": 15000, "base": 25000, "max": 35000, "tempo": 6000, "cat": "reforma", "cx": 5},

    # MARCENARIA / SERRALHERIA
    {"servico": "Reparar porta de madeira empenada", "min": 80, "base": 140, "max": 200, "tempo": 60, "cat": "manutencao", "cx": 2},
    {"servico": "Instalar porta completa (batente + folha + alisar)", "min": 200, "base": 250, "max": 350, "tempo": 180, "cat": "montagem", "cx": 3},
    {"servico": "Instalar portao de ferro/aco", "min": 300, "base": 500, "max": 900, "tempo": 240, "cat": "manutencao", "cx": 4},
    {"servico": "Instalar janela de aluminio", "min": 200, "base": 350, "max": 600, "tempo": 120, "cat": "montagem", "cx": 3},

    # MANUTENCAO GERAL
    {"servico": "Trocar fechadura simples (horario comercial)", "min": 100, "base": 150, "max": 200, "tempo": 30, "cat": "manutencao", "cx": 2},
    {"servico": "Trocar fechadura (fora de horario)", "min": 150, "base": 200, "max": 250, "tempo": 30, "cat": "manutencao", "cx": 2},
    {"servico": "Instalar fechadura digital", "min": 190, "base": 320, "max": 450, "tempo": 60, "cat": "manutencao", "cx": 3},
    {"servico": "Consertar porta (ajuste, dobradia)", "min": 60, "base": 130, "max": 200, "tempo": 40, "cat": "manutencao", "cx": 2},
    {"servico": "Instalar/consertar macaneta", "min": 100, "base": 175, "max": 200, "tempo": 30, "cat": "manutencao", "cx": 2},
    {"servico": "Reparo telhado pequeno", "min": 300, "base": 400, "max": 500, "tempo": 120, "cat": "manutencao", "cx": 3},
    {"servico": "Trocar telha (terreo, por unidade)", "min": 20, "base": 25, "max": 30, "tempo": 15, "cat": "manutencao", "cx": 2},
    {"servico": "Trocar telha (sobrado, por unidade)", "min": 30, "base": 35, "max": 40, "tempo": 15, "cat": "manutencao", "cx": 3},
    {"servico": "Limpeza calha (terreo, por metro)", "min": 25, "base": 33, "max": 40, "tempo": 10, "cat": "manutencao", "cx": 2},
    {"servico": "Limpeza calha (sobrado, por metro)", "min": 40, "base": 50, "max": 60, "tempo": 10, "cat": "manutencao", "cx": 3},
    {"servico": "Limpeza calha geral", "min": 250, "base": 325, "max": 400, "tempo": 60, "cat": "manutencao", "cx": 2},
    {"servico": "Dedetizacao residencial (baratas, formigas, tracas)", "min": 250, "base": 375, "max": 500, "tempo": 60, "cat": "manutencao", "cx": 2},
    {"servico": "Dedetizacao residencial (5 comodos)", "min": 400, "base": 450, "max": 550, "tempo": 90, "cat": "manutencao", "cx": 3},
    {"servico": "Tratamento cupins", "min": 600, "base": 860, "max": 1200, "tempo": 120, "cat": "manutencao", "cx": 4},
    {"servico": "Tratamento escorpioes", "min": 400, "base": 550, "max": 700, "tempo": 60, "cat": "manutencao", "cx": 3},
    {"servico": "Instalar cameras de seguranca (por ponto)", "min": 300, "base": 400, "max": 500, "tempo": 60, "cat": "manutencao", "cx": 3},
    {"servico": "Instalar cerca eletrica", "min": 400, "base": 700, "max": 1200, "tempo": 240, "cat": "manutencao", "cx": 4},
    {"servico": "Instalar rede de protecao", "min": 300, "base": 400, "max": 500, "tempo": 90, "cat": "manutencao", "cx": 3},
    {"servico": "Instalar box banheiro (vidro)", "min": 350, "base": 425, "max": 500, "tempo": 90, "cat": "manutencao", "cx": 3},
    {"servico": "Trocar vidro", "min": 250, "base": 325, "max": 400, "tempo": 60, "cat": "manutencao", "cx": 3},
    {"servico": "Ajuste janela", "min": 180, "base": 215, "max": 250, "tempo": 40, "cat": "manutencao", "cx": 2},
    {"servico": "Instalar porta de correr", "min": 300, "base": 400, "max": 500, "tempo": 120, "cat": "manutencao", "cx": 3},
    {"servico": "Trocar gas (botijao)", "min": 40, "base": 60, "max": 80, "tempo": 15, "cat": "manutencao", "cx": 1},
    {"servico": "Trocar valvula/mangueira gas", "min": 50, "base": 70, "max": 90, "tempo": 20, "cat": "manutencao", "cx": 1},
    {"servico": "Marido de aluguel (hora)", "min": 60, "base": 90, "max": 130, "tempo": 60, "cat": "manutencao", "cx": 2},
]

# Monta texto da tabela para o prompt do LLM
_TABELA_TEXTO = "\n".join(
    f"- {s['servico']}: R${s['min']}-{s['max']} (base R${s['base']}) | {s['tempo']}min | {s['cat']} | complexidade {s['cx']}/5"
    for s in TABELA_PRECOS
)

# ===== Referencia SINAPI + Mercado — custos reais 2024/2025 =====
# Fontes: SINAPI/Caixa/IBGE, Trice Brasil, Triider, Engehall, ReparosRMC
# SINAPI = referencia governo (CLT com encargos), mercado = preco autonomo real

_SINAPI_REFERENCIA = """
CUSTO MAO DE OBRA POR HORA:

SINAPI (referencia governo, CLT com encargos — base para calculo):
- Ajudante geral: R$11,05/h
- Ajudante especializado: R$11,91/h
- Eletricista oficial: R$10,81-17,81/h
- Encanador/bombeiro hidraulico: R$11,09-17,81/h
- Pedreiro: R$10,57-17,81/h
- Pintor: R$17,81-26,94/h
- Azulejista/ladrilhista: R$18,30/h
- Gesseiro: R$16,09/h
- Jardineiro: R$15,46/h
- Montador: R$14,10/h
- Carpinteiro: R$17,81/h
- Serralheiro: R$17,81/h

MERCADO PRIVADO (preco real autonomo SP/RJ 2025):
- Eletricista: R$60-120/h | diaria R$200-600
- Encanador: R$50-70/h | diaria R$150-300
- Pedreiro: diaria R$200-350
- Pintor: diaria R$150-220
- Jardineiro: R$30-80/h | diaria R$120-350
- Montador de moveis: diaria R$200-350
- Marido de aluguel: R$60/h | diaria R$480
- Paisagista: R$100-250/h

NOTA: SINAPI e referencia CLT para obras publicas. Autonomos cobram 3-6x mais
porque incluem ferramentas, transporte, seguro e margem de lucro.

CUSTO MATERIAIS COMUNS (SINAPI 2023 + mercado 2025):
- Cimento CP II-32: R$0,68/kg
- Areia media: R$127/m3
- Argamassa colante ACIII: R$2,30/kg (saco 20kg: R$20-50)
- Rejunte cimenticio: R$4,39/kg (pacote: R$10-40)
- Piso ceramica PEI4 (pequeno): R$25,90/m2
- Piso ceramica PEI4 (grande): R$52,79/m2
- Piso porcelanato borda reta: R$83,11/m2
- Revestimento ceramica comercial: R$19,71/m2
- Niveladores piso (kit): R$30-100
- Tinta acrilica: R$15-22/L
- Selador acrilico: R$9,15/L
- Massa corrida PVA: R$2,50/kg
- Massa oleo: R$10,11/kg
- Placa drywall standard 12,5mm: R$50-100/m2
- Placa drywall resistente umidade: +20-30%% sobre standard
- Chuveiro plastico simples: R$10,87/un
- Interruptor 1 tecla: R$7,31/un
- Sifao PVC: R$14,77/un
- Tubo PVC soldavel 25mm: R$12-18/m
- Fio eletrico 2,5mm: R$2,50-3,50/m
- Disjuntor monopolar: R$15-25/un
- CUB nacional (ago/2025): R$1.863/m2 (materiais R$1.064 + mao de obra R$799)

REGRA DE PRECIFICACAO PARA SERVICOS RESIDENCIAIS:
O preco final ao cliente deve incluir:
1. Custo de mao de obra (horas estimadas x taxa mercado do profissional)
2. Custo de materiais basicos (quando aplicavel, usar referencias acima)
3. Deslocamento (R$30-60 fixo)
4. Margem da plataforma (~15-20%%)
Emergencia/fora de horario: +30-100%% sobre o preco normal.
Regioes SP/RJ cobram o topo da faixa; interior/nordeste cobra 20-40%% menos.
""".strip()


def precificar(descricao: str, regiao: str = "", urgente: bool = False, foto_base64: str = None) -> dict:
    """Precifica um servico com base na descricao e foto usando IA.

    Se foto_base64 for fornecida, usa Vision API para analisar o local.
    Retorna preco fechado (unico), como o Uber.
    """
    try:
        if foto_base64:
            return _precificar_com_foto(descricao, regiao, urgente, foto_base64)
        return _precificar_groq(descricao, regiao, urgente)
    except Exception as e:
        print(f"[PRECIFICACAO FALLBACK] Erro na API: {e}")
        return _precificar_fallback(descricao, regiao, urgente)


def _precificar_com_foto(descricao: str, regiao: str, urgente: bool, foto_base64: str) -> dict:
    """Precifica usando Vision API — analisa descricao + foto do local juntos."""
    prompt = (
        "Voce e um especialista em precificacao de servicos residenciais no Brasil. "
        "O cliente enviou uma descricao do que precisa E uma foto do local.\n\n"
        "USE ESTAS REFERENCIAS DE PRECOS DO MERCADO BRASILEIRO:\n"
        f"{_TABELA_TEXTO}\n\n"
        f"{_SINAPI_REFERENCIA}\n\n"
        "INSTRUCOES:\n"
        "1. Identifique na tabela o servico mais proximo do que o cliente precisa\n"
        "2. Use o preco BASE da tabela como ponto de partida\n"
        "3. Valide usando SINAPI: custo mao de obra (horas x custo/h x markup 2-3x) + materiais + deslocamento R$30-60 + margem 15-20%%\n"
        "4. ANALISE A FOTO e ajuste o preco baseado no que voce ve:\n"
        "   - Area/tamanho visivel do espaco (m2 estimado)\n"
        "   - Estado de conservacao do local (bom/regular/ruim/critico)\n"
        "   - Complexidade visivel (acessibilidade, altura, obstaculos)\n"
        "   - Materiais visiveis (tipo de parede, piso, instalacao)\n"
        "   - Quantidade de pontos de trabalho\n"
        "   - Riscos visiveis (fiacao exposta, umidade, mofo, estrutural)\n"
        "   - Se precisa preparacao previa (limpar, mover moveis, etc)\n"
        f"5. {'Acrescente 35% ao preco final por ser URGENTE' if urgente else 'Nao e urgente'}\n"
        f"6. Regiao: {regiao or 'Sao Paulo'}\n\n"
        f"DESCRICAO DO CLIENTE: {descricao}\n\n"
        "Retorne APENAS um JSON valido, sem markdown, sem explicacao:\n"
        "{\n"
        '  "preco": <numero em reais, preco unico fechado>,\n'
        '  "tempo_estimado_min": <minutos>,\n'
        '  "categoria": "<eletrica|hidraulica|pintura|montagem|limpeza|jardinagem|reforma|manutencao|outros>",\n'
        '  "complexidade": <1 a 5>,\n'
        '  "detalhes": "<o que esta incluso no preco, max 2 frases>",\n'
        '  "analise_foto": {\n'
        '    "area_m2": <numero estimado ou null>,\n'
        '    "estado_conservacao": "<bom|regular|ruim|critico>",\n'
        '    "complexidade": "<baixa|media|alta|muito alta>",\n'
        '    "materiais_visiveis": "<lista breve>",\n'
        '    "acessibilidade": "<facil|moderada|dificil>",\n'
        '    "necessita_preparacao": <true|false>,\n'
        '    "pontos_de_trabalho": <numero>,\n'
        '    "risco_identificado": "<nenhum|baixo|medio|alto>",\n'
        '    "iluminacao": "<boa|razoavel|ruim>",\n'
        '    "observacoes": "<observacoes relevantes para o prestador, max 2 frases>"\n'
        '  }\n'
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
            "max_tokens": 1000,
        },
        timeout=25.0,
    )
    resp.raise_for_status()

    content = resp.json()["choices"][0]["message"]["content"]
    data = _extrair_json(content)

    categoria = str(data.get("categoria", "outros")).lower()
    if categoria not in CATEGORIAS_VALIDAS:
        categoria = "outros"

    resultado = {
        "preco": round(float(data.get("preco", 200)), 2),
        "tempo_estimado_min": int(data.get("tempo_estimado_min", 60)),
        "categoria": categoria,
        "complexidade": max(1, min(5, int(data.get("complexidade", 2)))),
        "detalhes": str(data.get("detalhes", "Precificado por IA com analise visual")),
    }

    # Extrai analise da foto se presente
    analise = data.get("analise_foto")
    if analise and isinstance(analise, dict):
        resultado["analise_foto"] = {
            "area_m2": analise.get("area_m2"),
            "estado_conservacao": str(analise.get("estado_conservacao", "regular")),
            "complexidade": str(analise.get("complexidade", "media")),
            "materiais_visiveis": str(analise.get("materiais_visiveis", "")),
            "acessibilidade": str(analise.get("acessibilidade", "moderada")),
            "necessita_preparacao": bool(analise.get("necessita_preparacao", False)),
            "pontos_de_trabalho": int(analise.get("pontos_de_trabalho", 1)),
            "risco_identificado": str(analise.get("risco_identificado", "nenhum")),
            "iluminacao": str(analise.get("iluminacao", "boa")),
            "observacoes": str(analise.get("observacoes", "")),
        }

    return resultado


def _precificar_groq(descricao: str, regiao: str, urgente: bool) -> dict:
    """Precifica usando Groq API (sem foto). Usa tabela de referencia."""
    prompt = (
        "Voce e um especialista em precificacao de servicos residenciais no Brasil. "
        "O cliente descreveu o que precisa. Use a tabela de referencia para definir o preco.\n\n"
        "REFERENCIAS DE PRECOS DO MERCADO BRASILEIRO:\n"
        f"{_TABELA_TEXTO}\n\n"
        f"{_SINAPI_REFERENCIA}\n\n"
        "INSTRUCOES:\n"
        "1. Identifique na tabela o servico mais proximo\n"
        "2. Use o preco BASE como referencia principal\n"
        "3. Use os custos SINAPI para validar: custo mao de obra (horas x custo/h x markup 2-3x) + materiais + deslocamento R$30-60 + margem 15-20%%\n"
        "4. Ajuste para cima ou para baixo conforme a descricao indica algo mais ou menos complexo\n"
        "5. Se o servico nao esta na tabela, estime baseado nos custos SINAPI de mao de obra e materiais\n"
        f"6. {'Acrescente 35% por ser URGENTE' if urgente else 'Nao e urgente'}\n"
        f"7. Regiao: {regiao or 'Sao Paulo'}\n\n"
        f"DESCRICAO DO CLIENTE: {descricao}\n\n"
        "IMPORTANTE: Retorne um PRECO UNICO FECHADO (nao faixa). Como o Uber mostra um preco exato.\n\n"
        "Retorne APENAS um JSON valido, sem markdown:\n"
        "{\n"
        '  "preco": <numero em reais>,\n'
        '  "tempo_estimado_min": <minutos>,\n'
        '  "categoria": "<eletrica|hidraulica|pintura|montagem|limpeza|jardinagem|reforma|manutencao|outros>",\n'
        '  "complexidade": <1 a 5>,\n'
        '  "detalhes": "<o que esta incluso no preco>"\n'
        "}"
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
            "temperature": 0.3,
            "max_tokens": 500,
        },
        timeout=15.0,
    )
    resp.raise_for_status()

    content = resp.json()["choices"][0]["message"]["content"]
    data = _extrair_json(content)

    categoria = str(data.get("categoria", "outros")).lower()
    if categoria not in CATEGORIAS_VALIDAS:
        categoria = "outros"

    return {
        "preco": round(float(data.get("preco", 200)), 2),
        "tempo_estimado_min": int(data.get("tempo_estimado_min", 60)),
        "categoria": categoria,
        "complexidade": max(1, min(5, int(data.get("complexidade", 2)))),
        "detalhes": str(data.get("detalhes", "Precificado por IA")),
    }


def _extrair_json(content: str) -> dict:
    """Extrai JSON de resposta do LLM (pode ter markdown fences)."""
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
    return json.loads(json_str)


# ===== Fallback: motor keyword (usado se Groq falhar) =====

def _precificar_fallback(descricao: str, regiao: str, urgente: bool) -> dict:
    """Motor keyword como fallback. Busca na tabela de precos."""
    descricao_lower = descricao.lower()
    melhor = None
    melhor_score = 0

    for item in TABELA_PRECOS:
        palavras = item["servico"].lower().split()
        score = sum(len(p) for p in palavras if p in descricao_lower and len(p) > 3)
        if score > melhor_score:
            melhor_score = score
            melhor = item

    if not melhor:
        return {
            "preco": 200,
            "tempo_estimado_min": 60,
            "categoria": "outros",
            "complexidade": 2,
            "detalhes": "Servico nao identificado. Preco estimado generico.",
        }

    mult = 1.35 if urgente else 1.0
    return {
        "preco": round(melhor["base"] * mult, 2),
        "tempo_estimado_min": melhor["tempo"],
        "categoria": melhor["cat"],
        "complexidade": melhor["cx"],
        "detalhes": f"{melhor['servico']} | Ref: R${melhor['min']}-{melhor['max']}"
        + (" | Urgente: +35%" if urgente else ""),
    }
