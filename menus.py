"""Textos dos ecrãs USSD. Sem acentos, para aparecerem bem em qualquer telemóvel."""

import codigos
from texto import para_gsm

MENU_PRINCIPAL = (
    "CON Bem-vindo ao DB-Dicionario!\n"
    "1. Ingles > Portugues\n"
    "2. Portugues > Ingles\n"
    "3. Palavra do dia\n"
    "4. Duvidas Vodacom"
)

PEDE_INGLES = "CON Digite a palavra em ingles:"
PEDE_PORTUGUES = "CON Digite a palavra em portugues:"
PEDE_DUVIDA = "CON Escreva a sua duvida sobre servicos Vodacom:"

OPCAO_INVALIDA = "END Opcao invalida. Tente novamente."
SESSAO_INVALIDA = "END Sessao invalida."
SESSAO_ENCERRADA = "END Sessao encerrada."
ERRO_PALAVRA_DIA = "END Erro ao buscar palavra do dia."


def _sem_resposta() -> str:
    """Quando o chat não encontra a pergunta nas FAQs. Os números vêm de codigos_vodacom.json."""
    linha, whatsapp = codigos.obter("LINHA_APOIO"), codigos.obter("WHATSAPP")
    if linha and whatsapp:
        return f"END Nao encontrei a resposta. Ligue {linha} ou fale no WhatsApp Vodacom: {whatsapp}"
    return "END Nao encontrei a resposta. Tente mais tarde."


SEM_RESPOSTA = _sem_resposta()


def palavra_nao_encontrada(termo: str) -> str:
    return f"END '{termo}' nao encontrada. Tente outra palavra."


def quis_dizer(termo: str, sugestao: str) -> str:
    """Ecrã de sugestão para gralhas. Responder 1 mostra a tradução da palavra sugerida."""
    return f"CON '{termo[:30]}' nao encontrada. Quis dizer: {para_gsm(sugestao)[:40]}?\n1. Sim"
