"""Dados iniciais para popular o banco PASSA."""
from backend.database import SessionLocal
from backend.models.models import Profissional, Servico


def seed_profissionais():
    """Cria profissionais de exemplo."""
    db = SessionLocal()

    if db.query(Profissional).count() > 0:
        db.close()
        return

    profissionais = [
        Profissional(
            nome="Carlos Eletricista",
            email="carlos@passa.com",
            telefone="(11) 99999-1001",
            cpf="111.111.111-01",
            categoria="eletrica",
            especialidades="Instalações, chuveiros, ar condicionado",
            regiao="São Paulo - Zona Sul",
            documento_verificado=True,
            antecedentes_ok=True,
            certificacoes="NR10, NR35",
            score=870,
            total_servicos=145,
            taxa_conclusao=98.5,
            tempo_medio_min=55,
            avaliacao_media=4.8,
            total_reclamacoes=3,
            pontualidade=95.0,
            frequencia_uso=85.0,
            recorrencia=72.0,
            compliance=98.0,
        ),
        Profissional(
            nome="Ana Pintora",
            email="ana@passa.com",
            telefone="(11) 99999-1002",
            cpf="222.222.222-02",
            categoria="pintura",
            especialidades="Residencial, textura, grafiato",
            regiao="São Paulo - Zona Oeste",
            documento_verificado=True,
            antecedentes_ok=True,
            certificacoes="Curso Suvinil Pro",
            score=920,
            total_servicos=210,
            taxa_conclusao=99.0,
            tempo_medio_min=180,
            avaliacao_media=4.9,
            total_reclamacoes=2,
            pontualidade=97.0,
            frequencia_uso=90.0,
            recorrencia=80.0,
            compliance=100.0,
        ),
        Profissional(
            nome="Roberto Encanador",
            email="roberto@passa.com",
            telefone="(11) 99999-1003",
            cpf="333.333.333-03",
            categoria="hidraulica",
            especialidades="Vazamentos, desentupimento, encanamento geral",
            regiao="São Paulo - Centro",
            documento_verificado=True,
            antecedentes_ok=True,
            score=750,
            total_servicos=89,
            taxa_conclusao=95.0,
            tempo_medio_min=70,
            avaliacao_media=4.5,
            total_reclamacoes=5,
            pontualidade=88.0,
            frequencia_uso=70.0,
            recorrencia=60.0,
            compliance=95.0,
        ),
        Profissional(
            nome="Marcos Montador",
            email="marcos@passa.com",
            telefone="(11) 99999-1004",
            cpf="444.444.444-04",
            categoria="montagem",
            especialidades="Móveis planejados, cozinhas, guarda-roupas",
            regiao="São Paulo - Zona Norte",
            documento_verificado=True,
            antecedentes_ok=False,
            score=680,
            total_servicos=62,
            taxa_conclusao=93.0,
            tempo_medio_min=120,
            avaliacao_media=4.3,
            total_reclamacoes=4,
            pontualidade=82.0,
            frequencia_uso=55.0,
            recorrencia=45.0,
            compliance=90.0,
        ),
        Profissional(
            nome="Luciana Limpeza",
            email="luciana@passa.com",
            telefone="(11) 99999-1005",
            cpf="555.555.555-05",
            categoria="limpeza",
            especialidades="Residencial, pós-obra, comercial",
            regiao="São Paulo - Zona Leste",
            documento_verificado=True,
            antecedentes_ok=True,
            score=810,
            total_servicos=180,
            taxa_conclusao=97.0,
            tempo_medio_min=200,
            avaliacao_media=4.7,
            total_reclamacoes=4,
            pontualidade=93.0,
            frequencia_uso=80.0,
            recorrencia=68.0,
            compliance=97.0,
        ),
        Profissional(
            nome="Pedro Reformas",
            email="pedro@passa.com",
            telefone="(11) 99999-1006",
            cpf="666.666.666-06",
            categoria="reforma",
            especialidades="Pisos, revestimentos, gesso, drywall",
            regiao="São Paulo - Zona Sul",
            documento_verificado=True,
            antecedentes_ok=True,
            certificacoes="CREA Técnico",
            score=780,
            total_servicos=95,
            taxa_conclusao=96.0,
            tempo_medio_min=300,
            avaliacao_media=4.6,
            total_reclamacoes=3,
            pontualidade=90.0,
            frequencia_uso=75.0,
            recorrencia=55.0,
            compliance=96.0,
        ),
        Profissional(
            nome="Jorge Jardineiro",
            email="jorge@passa.com",
            telefone="(11) 99999-1007",
            cpf="777.777.777-07",
            categoria="jardinagem",
            especialidades="Poda, paisagismo, manutenção",
            regiao="São Paulo - Zona Oeste",
            documento_verificado=False,
            antecedentes_ok=False,
            score=520,
            total_servicos=30,
            taxa_conclusao=90.0,
            tempo_medio_min=100,
            avaliacao_media=4.0,
            total_reclamacoes=3,
            pontualidade=78.0,
            frequencia_uso=40.0,
            recorrencia=35.0,
            compliance=85.0,
        ),
        Profissional(
            nome="Fernando Eletricista Jr",
            email="fernando@passa.com",
            telefone="(11) 99999-1008",
            cpf="888.888.888-08",
            categoria="eletrica",
            especialidades="Residencial, tomadas, iluminação",
            regiao="São Paulo - Zona Leste",
            documento_verificado=True,
            antecedentes_ok=True,
            score=620,
            total_servicos=25,
            taxa_conclusao=92.0,
            tempo_medio_min=65,
            avaliacao_media=4.1,
            total_reclamacoes=2,
            pontualidade=85.0,
            frequencia_uso=45.0,
            recorrencia=30.0,
            compliance=92.0,
        ),
    ]

    for p in profissionais:
        db.add(p)

    db.commit()
    db.close()
    print(f"[OK] {len(profissionais)} profissionais criados com sucesso!")


def seed_servicos():
    """Cria catálogo base de serviços."""
    db = SessionLocal()

    if db.query(Servico).count() > 0:
        db.close()
        return

    servicos = [
        Servico(nome="Trocar resistência do chuveiro", categoria="eletrica", preco_base=150, preco_min=100, preco_max=200, tempo_estimado_min=45, complexidade=2, palavras_chave="chuveiro, resistência, 220v, 127v"),
        Servico(nome="Instalar ventilador de teto", categoria="eletrica", preco_base=160, preco_min=100, preco_max=220, tempo_estimado_min=50, complexidade=3, palavras_chave="ventilador, teto, instalação"),
        Servico(nome="Instalar ar condicionado", categoria="eletrica", preco_base=450, preco_min=300, preco_max=600, tempo_estimado_min=180, complexidade=4, palavras_chave="ar condicionado, split, instalação"),
        Servico(nome="Consertar vazamento", categoria="hidraulica", preco_base=200, preco_min=120, preco_max=350, tempo_estimado_min=60, complexidade=3, palavras_chave="vazamento, cano, água"),
        Servico(nome="Desentupir pia/vaso", categoria="hidraulica", preco_base=180, preco_min=100, preco_max=300, tempo_estimado_min=60, complexidade=3, palavras_chave="entupido, desentupir, pia, vaso"),
        Servico(nome="Pintar parede", categoria="pintura", preco_base=200, preco_min=120, preco_max=400, tempo_estimado_min=120, complexidade=2, palavras_chave="pintura, parede, pintar"),
        Servico(nome="Pintar quarto completo", categoria="pintura", preco_base=500, preco_min=350, preco_max=800, tempo_estimado_min=360, complexidade=3, palavras_chave="pintar quarto, quarto"),
        Servico(nome="Montar móvel", categoria="montagem", preco_base=150, preco_min=80, preco_max=250, tempo_estimado_min=90, complexidade=2, palavras_chave="montar, móvel, montagem"),
        Servico(nome="Montar guarda-roupa", categoria="montagem", preco_base=250, preco_min=150, preco_max=400, tempo_estimado_min=180, complexidade=3, palavras_chave="guarda-roupa, armário, montar"),
        Servico(nome="Limpeza residencial", categoria="limpeza", preco_base=200, preco_min=120, preco_max=350, tempo_estimado_min=240, complexidade=2, palavras_chave="limpeza, faxina, casa"),
        Servico(nome="Trocar piso", categoria="reforma", preco_base=800, preco_min=500, preco_max=1500, tempo_estimado_min=480, complexidade=4, palavras_chave="piso, trocar, assentar"),
        Servico(nome="Aplicar gesso", categoria="reforma", preco_base=400, preco_min=250, preco_max=700, tempo_estimado_min=240, complexidade=3, palavras_chave="gesso, forro, moldura"),
    ]

    for s in servicos:
        db.add(s)

    db.commit()
    db.close()
    print(f"[OK] {len(servicos)} servicos criados com sucesso!")


def seed_all():
    seed_profissionais()
    seed_servicos()


if __name__ == "__main__":
    seed_all()
