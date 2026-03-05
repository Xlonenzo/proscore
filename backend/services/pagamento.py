"""Servico de pagamento Stripe com split automatico.

Integra Stripe Connect para cobrar clientes e transferir
automaticamente 85% ao prestador e reter 15% para a plataforma.
"""
import datetime
import os

import stripe

STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
COMISSAO_PLATAFORMA = 0.15  # 15%

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY


def criar_customer(email: str, nome: str) -> str:
    """Cria um Stripe Customer e retorna o ID."""
    customer = stripe.Customer.create(
        email=email,
        name=nome,
        metadata={"plataforma": "passa"},
    )
    return customer.id


def criar_payment_intent(
    valor_brl: float,
    stripe_customer_id: str,
    solicitacao_id: int,
    descricao: str = "",
) -> dict:
    """Cria PaymentIntent no Stripe.

    Args:
        valor_brl: Valor em reais (ex: 150.00)
        stripe_customer_id: ID do customer no Stripe
        solicitacao_id: ID da solicitacao no banco
        descricao: Descricao do servico

    Returns:
        Dict com payment_intent_id e client_secret
    """
    amount_centavos = int(round(valor_brl * 100))

    intent = stripe.PaymentIntent.create(
        amount=amount_centavos,
        currency="brl",
        customer=stripe_customer_id,
        payment_method_types=["card", "pix"],
        metadata={
            "solicitacao_id": str(solicitacao_id),
            "plataforma": "passa",
        },
        description=f"PASSA - {descricao[:200]}" if descricao else "PASSA - Servico residencial",
    )

    return {
        "payment_intent_id": intent.id,
        "client_secret": intent.client_secret,
    }


def transferir_para_prestador(
    stripe_connect_id: str,
    valor_profissional: float,
    solicitacao_id: int,
    payment_intent_id: str,
) -> str:
    """Transfere a parte do prestador (85%) para sua conta Connect.

    Args:
        stripe_connect_id: ID da conta Connect do prestador
        valor_profissional: Valor a transferir em reais
        solicitacao_id: ID da solicitacao
        payment_intent_id: ID do PaymentIntent original

    Returns:
        ID da Transfer no Stripe
    """
    amount_centavos = int(round(valor_profissional * 100))

    transfer = stripe.Transfer.create(
        amount=amount_centavos,
        currency="brl",
        destination=stripe_connect_id,
        metadata={
            "solicitacao_id": str(solicitacao_id),
            "payment_intent_id": payment_intent_id,
            "plataforma": "passa",
        },
        description=f"PASSA - Pagamento servico #{solicitacao_id}",
    )

    return transfer.id


def criar_conta_connect(email: str, nome: str) -> dict:
    """Cria conta Stripe Connect Express para o prestador.

    Returns:
        Dict com account_id e onboarding_url
    """
    account = stripe.Account.create(
        type="express",
        country="BR",
        email=email,
        capabilities={
            "transfers": {"requested": True},
        },
        business_type="individual",
        metadata={
            "plataforma": "passa",
            "nome": nome,
        },
    )

    # Gera link de onboarding
    link = stripe.AccountLink.create(
        account=account.id,
        refresh_url="https://passa.app/stripe/refresh",
        return_url="https://passa.app/stripe/return",
        type="account_onboarding",
    )

    return {
        "account_id": account.id,
        "onboarding_url": link.url,
    }


def verificar_conta_connect(stripe_connect_id: str) -> dict:
    """Verifica status da conta Connect do prestador."""
    account = stripe.Account.retrieve(stripe_connect_id)
    return {
        "charges_enabled": account.charges_enabled,
        "payouts_enabled": account.payouts_enabled,
        "details_submitted": account.details_submitted,
    }


def processar_webhook(payload: bytes, sig_header: str) -> dict:
    """Processa evento webhook do Stripe.

    Args:
        payload: Body cru da request
        sig_header: Header Stripe-Signature

    Returns:
        Dict com tipo do evento e dados relevantes
    """
    event = stripe.Webhook.construct_event(
        payload, sig_header, STRIPE_WEBHOOK_SECRET
    )

    if event.type == "payment_intent.succeeded":
        pi = event.data.object
        return {
            "tipo": "pagamento_confirmado",
            "payment_intent_id": pi.id,
            "solicitacao_id": int(pi.metadata.get("solicitacao_id", 0)),
            "metodo": _detectar_metodo(pi),
        }

    if event.type == "payment_intent.payment_failed":
        pi = event.data.object
        return {
            "tipo": "pagamento_falhou",
            "payment_intent_id": pi.id,
            "solicitacao_id": int(pi.metadata.get("solicitacao_id", 0)),
        }

    return {"tipo": "ignorado", "event_type": event.type}


def calcular_split(valor_total: float) -> dict:
    """Calcula os valores do split.

    Returns:
        Dict com valor_plataforma e valor_profissional
    """
    valor_plataforma = round(valor_total * COMISSAO_PLATAFORMA, 2)
    valor_profissional = round(valor_total - valor_plataforma, 2)
    return {
        "valor_total": valor_total,
        "valor_plataforma": valor_plataforma,
        "valor_profissional": valor_profissional,
    }


def _detectar_metodo(payment_intent) -> str:
    """Detecta o metodo de pagamento usado (cartao ou pix)."""
    if payment_intent.charges and payment_intent.charges.data:
        charge = payment_intent.charges.data[0]
        pm_details = charge.payment_method_details
        if pm_details and pm_details.type == "pix":
            return "pix"
    return "cartao"
