"""
Contactos e códigos USSD da Vodacom.
Vêm de codigos_vodacom.json, para mudar sem mexer no código Python.
Nas FAQs escreve-se o nome entre chavetas (por exemplo {MPESA}) e este módulo troca pelo valor.
"""

import json
import re

import config

_PADRAO = re.compile(r"\{([A-Z0-9_]+)\}")


def _carregar() -> dict:
    try:
        with open(config.CODIGOS_PATH, encoding="utf-8") as f:
            dados = json.load(f)
    except (OSError, ValueError):
        print("AVISO: nao foi possivel ler", config.CODIGOS_PATH)
        return {}
    valores = {}
    for seccao in ("contactos", "codigos"):
        valores.update(dados.get(seccao, {}))
    return valores


VALORES = _carregar()


def obter(chave: str) -> str:
    """Valor de um contacto ou código (texto vazio se não existir)."""
    return VALORES.get(chave, "")


def chaves_em(texto: str) -> list:
    """Nomes entre chavetas que aparecem no texto."""
    return _PADRAO.findall(texto)


def preencher(texto: str) -> str:
    """Troca {CHAVE} pelo valor. Chaves desconhecidas ficam como estão (o verificar.py avisa)."""
    return _PADRAO.sub(lambda m: VALORES.get(m.group(1), m.group(0)), texto)
