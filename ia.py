"""Ajudante de reserva: pergunta ao Grok quando a palavra não está na base local."""

from typing import Optional

import config


def buscar_via_grok(palavra: str, sentido: str) -> Optional[str]:
    """
    sentido = 'en-pt' ou 'pt-en'.
    Devolve None se a chave não estiver configurada ou se a chamada falhar
    (nunca derruba o app).
    """
    if not config.GROK_API_KEY:
        return None

    import requests  # só é preciso quando há chave configurada

    if sentido == "en-pt":
        prompt = (
            f"Traduza a palavra em inglês '{palavra}' para português. "
            "Responda SOMENTE no formato: pronuncia_aproximada = traducao "
            "(máximo 15 palavras, sem explicações)."
        )
    else:
        prompt = (
            f"Traduza a palavra em português '{palavra}' para inglês. "
            "Responda SOMENTE no formato: traducao (pronuncia_aproximada) "
            "(máximo 15 palavras, sem explicações)."
        )

    try:
        resp = requests.post(
            config.GROK_API_URL,
            headers={
                "Authorization": f"Bearer {config.GROK_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": config.GROK_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 40,
            },
            timeout=5,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        return None
