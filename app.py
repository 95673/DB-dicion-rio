"""
DB-Dicionario — Backend USSD (compatível com o webhook da Africa's Talking)

Este ficheiro só tem as rotas e o fluxo dos ecrãs. O resto está em módulos:
  config.py      -> números, limites e segredos
  menus.py       -> textos dos ecrãs
  base_dados.py  -> SQLite e logs
  tradutor.py    -> busca de palavras (com tolerância e sugestões)
  chat.py        -> dúvidas Vodacom (faq_vodacom.json)
  codigos.py     -> códigos USSD e contactos (codigos_vodacom.json)
  verificar.py   -> verifica se os dados estão certos (rota /verificar)
  ia.py          -> Grok, como reserva do tradutor
  texto.py       -> ferramentas de texto

Fluxo:
  Raiz  -> 1. Ingles > Portugues | 2. Portugues > Ingles | 3. Palavra do dia | 4. Duvidas Vodacom
  1 ou 2 -> pede a palavra -> mostra o resultado e fecha
           (se for uma gralha, pergunta "Quis dizer: ...?" e responder 1 mostra a tradução)
  3      -> palavra aleatória e fecha
  4      -> pede a dúvida -> responde com a FAQ (ou manda ligar para a linha de apoio)

Toda resposta respeita o limite de 160 caracteres.
"""

import html
from secrets import compare_digest

from flask import Flask, request

import base_dados
import chat
import config
import ia
import menus
import tradutor
import verificar
from texto import truncar

app = Flask(__name__)
base_dados.init_logs()
verificar.mostrar_no_arranque()


# ---------- Fluxo USSD ----------

def _formatar_traducao(row, sentido: str) -> str:
    if sentido == "en-pt":
        return f"{row['word_en']} ({row['pron']}) = {row['trad_pt']}"
    return f"{row['trad_pt']} = {row['word_en']} ({row['pron']})"


def _menu_principal(escolha: str) -> str:
    if escolha == "1":
        return menus.PEDE_INGLES
    if escolha == "2":
        return menus.PEDE_PORTUGUES
    if escolha == "3":
        row = tradutor.palavra_do_dia()
        if row:
            return "END " + _formatar_traducao(row, "en-pt")
        return menus.ERRO_PALAVRA_DIA
    if escolha == "4":
        return menus.PEDE_DUVIDA
    return menus.OPCAO_INVALIDA


def _formatar_traducao(row: dict, sentido: str) -> str:
    if sentido == "en-pt":
        return f"END {row['word_en']} ({row['pron']}) = {row['trad_pt']}"
    return f"END {row['trad_pt']} = {row['word_en']} ({row['pron']})"


def _buscar(termo: str, sentido: str):
    if sentido == "en-pt":
        return tradutor.buscar_en_pt(termo)
    return tradutor.buscar_pt_en(termo)


def _sugerir(termo: str, sentido: str):
    if sentido == "en-pt":
        return tradutor.sugerir_en_pt(termo)
    return tradutor.sugerir_pt_en(termo)


def _traduzir(termo: str, phone_number: str, sentido: str) -> str:
    # 1. Busca tolerante na base local (plural, -ing, artigos...)
    row = _buscar(termo, sentido)
    if row:
        base_dados.registrar_busca(phone_number, sentido, termo, True)
        return _formatar_traducao(row, sentido)

    # 2. Reserva: pergunta ao Grok (só se houver chave configurada)
    resposta_ia = ia.buscar_via_grok(termo, sentido)
    if resposta_ia:
        base_dados.registrar_busca(phone_number, sentido, termo, True)
        return f"END {termo} = {resposta_ia}"

    # 3. Não encontrou: regista a falha e, se houver, sugere a palavra mais parecida
    base_dados.registrar_busca(phone_number, sentido, termo, False)
    sugestao = _sugerir(termo, sentido)
    if sugestao:
        return menus.quis_dizer(termo, sugestao)
    return menus.palavra_nao_encontrada(termo)


def _confirmar_sugestao(escolha: str, termo: str, phone_number: str) -> str:
    """O cliente respondeu 1 ao 'Quis dizer?': mostra a tradução da palavra sugerida."""
    sentido = "en-pt" if escolha == "1" else "pt-en"
    sugestao = _sugerir(termo, sentido)
    row = _buscar(sugestao, sentido) if sugestao else None
    if not row:
        return menus.SESSAO_ENCERRADA
    base_dados.registrar_busca(phone_number, sentido, sugestao, True)
    return _formatar_traducao(row, sentido)


def _duvida(pergunta: str, phone_number: str) -> str:
    faq = chat.buscar_resposta(pergunta)
    if not faq:
        base_dados.registrar_busca(phone_number, "duvida", pergunta, base_dados.NAO_ENCONTRADA)
        return menus.SEM_RESPOSTA
    base_dados.registrar_busca(phone_number, "duvida", pergunta, base_dados.ENCONTRADA)
    if chat.tem_continuacao(faq):
        return "CON " + chat.primeira_parte(faq)
    return "END " + chat.resposta_simples(faq)


def _continuacao_duvida(pergunta: str) -> str:
    faq = chat.buscar_resposta(pergunta)
    if faq and chat.tem_continuacao(faq):
        return "END " + chat.segunda_parte(faq)
    return menus.SESSAO_ENCERRADA


def _segundo_nivel(escolha: str, termo: str, phone_number: str) -> str:
    if escolha == "1":
        return _traduzir(termo, phone_number, "en-pt")
    if escolha == "2":
        return _traduzir(termo, phone_number, "pt-en")
    if escolha == "4":
        return _duvida(termo, phone_number)
    return menus.SESSAO_INVALIDA


@app.route("/ussd", methods=["POST"])
def ussd():
    # Parâmetros padrão enviados pela Africa's Talking
    phone_number = request.values.get("phoneNumber", "")
    text = request.values.get("text", "")

    partes = text.split("*") if text else []
    nivel = len(partes)

    if nivel == 0:
        response = menus.MENU_PRINCIPAL
    elif nivel == 1:
        response = _menu_principal(partes[0])
    elif nivel == 2:
        response = _segundo_nivel(partes[0], partes[1], phone_number)
    elif nivel == 3 and partes[0] == "4" and partes[2].strip() == "1":
        response = _continuacao_duvida(partes[1])
    elif nivel == 3 and partes[0] in ("1", "2") and partes[2].strip() == "1":
        response = _confirmar_sugestao(partes[0], partes[1], phone_number)
    else:
        response = menus.SESSAO_ENCERRADA

    return truncar(response), 200, {"Content-Type": "text/plain"}


# ---------- Rotas de apoio ----------

@app.route("/", methods=["GET"])
def health():
    """Rota simples para o Render confirmar que o serviço está de pé."""
    return "DB-Dicionario online.", 200


def _senha_certa() -> bool:
    """Confere a senha da URL (?chave=...) com a variável de ambiente STATS_PASSWORD."""
    esperada = config.STATS_PASSWORD
    recebida = request.args.get("chave", "")
    return bool(esperada) and compare_digest(recebida.encode("utf-8"), esperada.encode("utf-8"))


@app.route("/stats", methods=["GET"])
def stats():
    """
    Painel simples de estatísticas, protegido por senha na URL:
    https://seu-app.onrender.com/stats?chave=SUA_SENHA
    A senha vem da variável de ambiente STATS_PASSWORD.
    """
    if not _senha_certa():
        return "Acesso negado.", 403

    e = base_dados.obter_estatisticas()
    total = e["total"]
    falha = total - e["sucesso"]
    taxa = (e["sucesso"] / total * 100) if total > 0 else 0

    linhas = [
        "=== DB-Dicionario — Estatisticas ===",
        f"Total de buscas: {total}",
        f"Com sucesso: {e['sucesso']}",
        f"Sem sucesso: {falha}",
        f"Respondidas pelo Grok: {e['pela_ia']}",
        f"Taxa de sucesso: {taxa:.1f}%",
        f"Numeros de telefone unicos: {e['numeros_unicos']}",
        "",
        "--- Palavras mais buscadas ---",
    ]
    linhas += [f"{qtd:4d}x  {html.escape(termo)}" for termo, qtd in e["top_palavras"]]
    linhas += ["", "--- Palavras que nao estavam no dicionario (acrescentar ao CSV) ---"]
    for direcao, termo, resultado, qtd in e["palavras_em_falta"]:
        nota = "  (respondida pelo Grok)" if resultado == base_dados.RESPONDIDA_PELA_IA else ""
        linhas.append(f"{qtd:4d}x  [{direcao}] {html.escape(termo)}{nota}")
    linhas += ["", "--- Palavras nao encontradas (para acrescentar ao dicionario.csv) ---"]
    linhas += [
        f"{qtd:4d}x  [{direcao}] {html.escape(termo)}"
        for direcao, termo, qtd in e["nao_encontradas"]
    ]
    linhas += ["", "--- Duvidas Vodacom mais feitas ---"]
    linhas += [f"{qtd:4d}x  {html.escape(termo)}" for termo, qtd in e["top_duvidas"]]
    linhas += ["", "--- Duvidas sem resposta (para melhorar as FAQs) ---"]
    linhas += [f"{qtd:4d}x  {html.escape(termo)}" for termo, qtd in e["duvidas_sem_resposta"]]
    linhas += ["", "--- Buscas por dia ---"]
    linhas += [f"{data}: {qtd}" for data, qtd in e["por_dia"]]

    return "<pre>" + "\n".join(linhas) + "</pre>", 200


@app.route("/verificar", methods=["GET"])
def verificar_dados():
    """
    Mostra se as FAQs e os códigos estão certos (limite de 160 caracteres, códigos em falta...).
    Protegido pela mesma senha do /stats: https://seu-app.onrender.com/verificar?chave=SUA_SENHA
    """
    if not _senha_certa():
        return "Acesso negado.", 403
    return "<pre>" + html.escape(verificar.relatorio()) + "</pre>", 200


if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
