"""
Verifica se os dados (FAQs e códigos) estão certos, antes de os clientes os verem.

Pode usar-se de três formas:
  python3 verificar.py            no terminal
  /verificar?chave=SENHA          no navegador (a senha é a STATS_PASSWORD)
  ao arrancar, o resumo aparece nos logs do Render
"""

import json
import re
import sys
from collections import defaultdict

import codigos
import config
from texto import normalizar_pergunta

_DATA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_NOME = re.compile(r"^[A-Z0-9_]+$")


def _ler_json(caminho: str, problemas: list):
    nome = caminho.replace("\\", "/").split("/")[-1]
    try:
        with open(caminho, encoding="utf-8") as f:
            return json.load(f)
    except OSError:
        problemas.append(f"{nome}: ficheiro nao encontrado")
    except ValueError as erro:
        problemas.append(f"{nome}: JSON invalido ({erro})")
    return {}


def _verificar_codigos(dados: dict, problemas: list, avisos: list) -> dict:
    vistos = {}
    for seccao in ("contactos", "codigos"):
        if not isinstance(dados.get(seccao), dict):
            problemas.append(f"codigos_vodacom.json: falta a seccao '{seccao}'")
            continue
        for nome, valor in dados[seccao].items():
            if not _NOME.match(nome):
                problemas.append(f"codigos_vodacom.json: nome invalido '{nome}' (use MAIUSCULAS, numeros e _)")
            if nome in vistos:
                problemas.append(f"codigos_vodacom.json: nome repetido '{nome}'")
            vistos[nome] = seccao
            if not isinstance(valor, str) or not valor.strip():
                problemas.append(f"codigos_vodacom.json: '{nome}' esta vazio")
            elif seccao == "codigos" and not (valor.startswith("*") and valor.endswith("#")):
                avisos.append(f"codigo '{nome}' ({valor}) nao comeca com * e nao termina com #")
    return vistos


def analisar() -> dict:
    problemas, avisos = [], []

    # Códigos e contactos
    dados_codigos = _ler_json(config.CODIGOS_PATH, problemas)
    nomes = _verificar_codigos(dados_codigos, problemas, avisos)

    # FAQs
    dados_faq = _ler_json(config.FAQ_PATH, problemas)
    faqs = dados_faq.get("faqs", [])
    if not isinstance(faqs, list) or not faqs:
        problemas.append("faq_vodacom.json: nao tem a lista 'faqs'")
        faqs = []

    ids, usados, palavras = set(), set(), defaultdict(list)
    por_verificar, com_nota = [], []
    for faq in faqs:
        fid = faq.get("id")
        etiqueta = f"FAQ {fid}"
        if not isinstance(fid, int) or fid in ids:
            problemas.append(f"{etiqueta}: id em falta ou repetido")
        ids.add(fid)
        if not faq.get("pergunta"):
            problemas.append(f"{etiqueta}: falta a pergunta")
        chaves = faq.get("palavras_chave")
        if not isinstance(chaves, list) or not chaves:
            problemas.append(f"{etiqueta}: faltam as palavras-chave")
        else:
            normalizadas = [normalizar_pergunta(chave) for chave in chaves]
            if len(set(normalizadas)) < len(normalizadas):
                avisos.append(f"{etiqueta}: tem palavras-chave iguais depois de normalizar (ex.: mpesa e m-pesa)")
            for chave in set(normalizadas):
                palavras[chave].append(fid)

        verificado = faq.get("verificado")
        if verificado is None:
            por_verificar.append(fid)
        elif not (isinstance(verificado, str) and _DATA.match(verificado)):
            problemas.append(f"{etiqueta}: 'verificado' deve ser null ou AAAA-MM-DD")
        if faq.get("nota"):
            com_nota.append(fid)

        resposta = faq.get("resposta")
        if not isinstance(resposta, str) or not resposta.strip():
            problemas.append(f"{etiqueta}: falta a resposta")
            continue
        continuacao = faq.get("resposta_continuacao")
        for campo, texto in (("resposta", resposta), ("resposta_continuacao", continuacao)):
            if not texto:
                continue
            for nome in codigos.chaves_em(texto):
                usados.add(nome)
                if nome not in nomes:
                    problemas.append(f"{etiqueta}: {{{nome}}} nao existe em codigos_vodacom.json")
            final = codigos.preencher(texto)
            limite = config.MAX_LEN
            if campo == "resposta" and continuacao:
                final = re.sub(r"\s*\(1/2\)\s*$", "", final) + "\n1. Mais"
            if len(final) > limite:
                problemas.append(f"{etiqueta}: {campo} tem {len(final)} caracteres (maximo {limite})")
        if continuacao and not resposta.rstrip().endswith("(1/2)"):
            avisos.append(f"{etiqueta}: tem continuacao, mas a resposta nao termina com (1/2)")

    for nome, seccao in nomes.items():
        if seccao == "codigos" and nome not in usados:
            avisos.append(f"codigo {{{nome}}} nao e usado em nenhuma FAQ")

    repetidas = [(k, v) for k, v in palavras.items() if k and len(set(v)) > 1]
    for chave, lista in sorted(repetidas)[:10]:
        avisos.append(f"palavra-chave '{chave}' repetida nas FAQs {sorted(set(lista))} (ganha a primeira)")

    return {
        "total": len(faqs),
        "verificadas": len(faqs) - len(por_verificar),
        "por_verificar": por_verificar,
        "com_nota": com_nota,
        "n_codigos": sum(1 for s in nomes.values() if s == "codigos"),
        "n_contactos": sum(1 for s in nomes.values() if s == "contactos"),
        "problemas": problemas,
        "avisos": avisos,
    }


def relatorio() -> str:
    r = analisar()
    linhas = [
        "=== Verificacao dos dados ===",
        f"FAQs: {r['total']} ({r['verificadas']} verificadas, {len(r['por_verificar'])} por verificar)",
        f"Codigos USSD: {r['n_codigos']} | Contactos: {r['n_contactos']}",
        "",
        f"PROBLEMAS ({len(r['problemas'])}) - corrigir antes de publicar:",
    ]
    linhas += [f"  - {p}" for p in r["problemas"]] or ["  nenhum"]
    linhas += ["", f"AVISOS ({len(r['avisos'])}):"]
    linhas += [f"  - {a}" for a in r["avisos"]] or ["  nenhum"]
    if r["com_nota"]:
        linhas += ["", "FAQs com nota (algo por confirmar): " + ", ".join(str(i) for i in r["com_nota"])]
    if r["por_verificar"]:
        linhas += ["", "FAQs por verificar: " + ", ".join(str(i) for i in r["por_verificar"])]
    return "\n".join(linhas)


def mostrar_no_arranque():
    """Escreve nos logs um resumo curto (no Render: separador Logs)."""
    r = analisar()
    print(f"[dados] {r['total']} FAQs ({len(r['por_verificar'])} por verificar), "
          f"{r['n_codigos']} codigos, {len(r['problemas'])} problemas, {len(r['avisos'])} avisos")
    for problema in r["problemas"]:
        print("[dados] PROBLEMA:", problema)


if __name__ == "__main__":
    print(relatorio())
    sys.exit(1 if analisar()["problemas"] else 0)
