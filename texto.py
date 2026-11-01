"""Ferramentas de texto: normalizar, truncar e preparar texto para o ecrã USSD."""

import re
import unicodedata

from config import MAX_LEN


def _sem_acentos(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in texto if not unicodedata.combining(c))


def normalizar(texto: str) -> str:
    """Remove acentos, espaços extras e coloca em minúsculas para comparação tolerante."""
    return _sem_acentos(texto.strip().lower())


def normalizar_pergunta(texto: str) -> str:
    """Como normalizar(), mas também tira pontuação e junta 'm-pesa' em 'mpesa'."""
    texto = normalizar(texto).replace("-", " ")
    texto = re.sub(r"[^a-z0-9 ]", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto.replace("m pesa", "mpesa")


def para_gsm(texto: str) -> str:
    """Tira acentos e aspas especiais, para o texto aparecer bem no ecrã USSD."""
    trocas = (("“", '"'), ("”", '"'), ("‘", "'"), ("’", "'"), ("–", "-"), ("—", "-"))
    for antigo, novo in trocas:
        texto = texto.replace(antigo, novo)
    return _sem_acentos(texto)


def truncar(texto: str) -> str:
    """Garante que a resposta nunca ultrapasse o limite USSD."""
    return texto if len(texto) <= MAX_LEN else texto[: MAX_LEN - 3] + "..."
