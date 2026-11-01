"""
Simulador de terminal para o DB-Dicionario.

Usa exactamente o mesmo fluxo do /ussd do app.py (incluindo o chat de duvidas Vodacom),
por isso mostra o que o cliente veria no telemovel. Nao precisa de servidor, de internet
nem de API, e nao grava nada nos logs.

Como correr:
    pip install flask
    python3 simulador.py
"""

import os

os.environ["MODO_SIMULADOR"] = "1"  # tem de vir antes de importar o app

from app import app  # noqa: E402

TELEFONE_TESTE = "+258840000000"


def chamar_ussd(text: str) -> str:
    resposta = app.test_client().post(
        "/ussd", data={"phoneNumber": TELEFONE_TESTE, "text": text}
    )
    return resposta.get_data(as_text=True)


def main():
    print("=== Simulador USSD: DB-Dicionario ===")
    print("(Digite como faria no telemovel. 'sair' encerra.)\n")

    text = ""
    while True:
        resposta = chamar_ussd(text)
        tipo, _, corpo = resposta.partition(" ")  # tipo = CON (continua) ou END (termina)

        print("-" * 40)
        print(corpo)
        print("-" * 40)
        print(f"({len(resposta)} caracteres)\n")

        if tipo == "END":
            input("[Enter para voltar ao menu]\n")
            text = ""
            continue

        entrada = input("> ").strip()
        if entrada.lower() == "sair":
            break
        text = entrada if text == "" else text + "*" + entrada
        print()


if __name__ == "__main__":
    main()
