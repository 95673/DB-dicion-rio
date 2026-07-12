"""
Simulador de terminal para o DB-Dicionário.
Roda o mesmo fluxo do app.py, mas direto no console — sem precisar
subir servidor Flask nem contratar API. Ideal para testar rapidamente.
"""

from app import (
    buscar_en_pt,
    buscar_pt_en,
    palavra_do_dia,
    truncar,
)


def linha(char="-", n=40):
    print(char * n)


def main():
    text = ""
    print("=== Simulador USSD: DB-Dicionário ===")
    print("(Digite os números como faria no celular. 'sair' encerra.)\n")

    while True:
        partes = text.split("*") if text else []
        nivel = len(partes) if text else 0

        if text == "":
            tela = (
                "Bem-vindo ao DB-Dicionario!\n"
                "1. Ingles > Portugues\n"
                "2. Portugues > Ingles\n"
                "3. Palavra do dia"
            )
            print(tela)
            entrada = input("\n> Digite opcao: ").strip()
            if entrada.lower() == "sair":
                break
            text = entrada
            continue

        elif nivel == 1:
            escolha = partes[0]
            if escolha == "3":
                row = palavra_do_dia()
                resp = truncar(f"{row['word_en']} ({row['pron']}) = {row['trad_pt']}")
                linha()
                print("RESPOSTA (%d caracteres):" % len(resp))
                print(resp)
                linha()
                text = ""
                input("\n[Enter para voltar ao menu]")
                continue
            elif escolha in ("1", "2"):
                label = "ingles" if escolha == "1" else "portugues"
                entrada = input(f"\n> Digite a palavra em {label}: ").strip()
                text = text + "*" + entrada
                continue
            else:
                print("Opção inválida.\n")
                text = ""
                continue

        elif nivel == 2:
            escolha, termo = partes[0], partes[1]
            if escolha == "1":
                row = buscar_en_pt(termo)
                if row:
                    resp = truncar(f"{row['word_en']} ({row['pron']}) = {row['trad_pt']}")
                else:
                    resp = f"'{termo}' nao encontrada."
            else:
                row = buscar_pt_en(termo)
                if row:
                    resp = truncar(f"{row['trad_pt']} = {row['word_en']} ({row['pron']})")
                else:
                    resp = f"'{termo}' nao encontrada."

            linha()
            print("RESPOSTA (%d caracteres):" % len(resp))
            print(resp)
            linha()
            text = ""
            input("\n[Enter para voltar ao menu]")
            continue


if __name__ == "__main__":
    main()
