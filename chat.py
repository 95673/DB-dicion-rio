"""
Chat de dúvidas Vodacom.
Procura a pergunta do cliente no ficheiro faq_vodacom.json, pelas palavras-chave.
Não usa IA: só responde com o que está nas FAQs, por isso nunca inventa.
"""

import json
import re
from typing import Optional

import codigos
import config
from texto import normalizar_pergunta, para_gsm


def _carregar_faqs() -> list:
    try:
        with open(config.FAQ_PATH, encoding="utf-8") as f:
            faqs = json.load(f)["faqs"]
    except (OSError, ValueError, KeyError):
        print("AVISO: nao foi possivel ler", config.FAQ_PATH)
        return []
    # Prepara uma vez: troca os {CODIGOS} pelos valores e normaliza as palavras-chave
    for faq in faqs:
        faq["resposta"] = codigos.preencher(faq["resposta"])
        if faq.get("resposta_continuacao"):
            faq["resposta_continuacao"] = codigos.preencher(faq["resposta_continuacao"])
        unicas = {frozenset(normalizar_pergunta(k).split()) for k in faq.get("palavras_chave", [])}
        faq["_chaves"] = [set(chave) for chave in unicas if chave]  # sem repetidas ("mpesa" e "m-pesa")
    return faqs


FAQS = _carregar_faqs()


def buscar_resposta(pergunta: str) -> Optional[dict]:
    """
    Uma palavra-chave "acerta" se todas as suas palavras aparecem na pergunta.
    Cada acerto vale tantos pontos quantas palavras tem a chave
    (assim "ser agente" ganha a "agente"). Em empate, ganha a FAQ que vem primeiro.
    """
    palavras = set(normalizar_pergunta(pergunta).split())
    melhor, melhor_pontos = None, 0
    for faq in FAQS:
        pontos = sum(len(chave) for chave in faq["_chaves"] if chave and chave <= palavras)
        if pontos > melhor_pontos:
            melhor, melhor_pontos = faq, pontos
    return melhor


def tem_continuacao(faq: dict) -> bool:
    return bool(faq.get("resposta_continuacao"))


def resposta_simples(faq: dict) -> str:
    return para_gsm(faq["resposta"])


def primeira_parte(faq: dict) -> str:
    """Primeira parte de uma resposta em duas partes, com a opção '1. Mais'."""
    texto = re.sub(r"\s*\(1/2\)\s*$", "", faq["resposta"])
    return para_gsm(texto) + "\n1. Mais"


def segunda_parte(faq: dict) -> str:
    return para_gsm(faq["resposta_continuacao"])
