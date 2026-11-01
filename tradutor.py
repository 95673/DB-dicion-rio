"""
Tradutor: procura palavras na base de dados do dicionário.

A busca é tolerante:
  - aceita formas diferentes da palavra (plural, -ing, -ed, artigos como "to" e "the"...);
  - quando não encontra, sugere a palavra mais parecida (para gralhas).
A tabela é lida uma só vez; para recarregar depois de mudar o dicionário, reinicia o serviço.
"""

import difflib
import re
from functools import lru_cache

from base_dados import get_conn
from texto import normalizar

ARTIGOS_EN = ("to ", "the ", "a ", "an ")
ARTIGOS_PT = ("o ", "a ", "os ", "as ", "um ", "uma ", "uns ", "umas ")

# (terminação, substituição): formas a tentar, pela ordem
REGRAS_EN = (
    ("ies", "y"), ("ied", "y"), ("ves", "f"), ("ves", "fe"),
    ("s", ""), ("es", ""),
    ("ing", ""), ("ing", "e"), ("ed", ""), ("ed", "e"), ("ly", ""),
)
REGRAS_PT = (
    ("oes", "ao"), ("aes", "ae"), ("aes", "ao"), ("ais", "al"), ("eis", "el"), ("ois", "ol"),
    ("ns", "m"), ("s", ""), ("es", ""),
    ("ando", "ar"), ("endo", "er"), ("indo", "ir"),
    ("ado", "ar"), ("ido", "er"), ("ido", "ir"),
)


def _chave(texto: str) -> str:
    """Forma normalizada usada nas comparações: sem acentos, minúsculas, espaços simples."""
    return " ".join(normalizar(texto).split())


def _chave_pt(glosa: str) -> str:
    """Como _chave, mas tira o que está entre parênteses e os hífenes."""
    glosa = re.sub(r"\(.*?\)", "", glosa).replace("-", " ")
    return _chave(glosa)


@lru_cache(maxsize=1)
def _indices() -> dict:
    """Lê a tabela uma vez e prepara os índices de busca."""
    conn = get_conn()
    linhas = [dict(r) for r in conn.execute("SELECT * FROM words").fetchall()]
    conn.close()

    en, pt = {}, {}
    for linha in linhas:
        en.setdefault(_chave(linha["word_en"]), linha)
        for glosa in linha["trad_pt"].split(","):
            chave = _chave_pt(glosa)
            if chave:
                pt.setdefault(chave, (linha, glosa.strip()))
    return {"en": en, "pt": pt, "chaves_en": list(en), "chaves_pt": list(pt)}


def _formas(palavra: str, regras) -> list:
    """Formas prováveis da palavra de base (singular, infinitivo...)."""
    formas = []
    for sufixo, troca in regras:
        minimo = 1 if sufixo == "aes" else 2  # "paes" -> "pao" tem só 1 letra de raiz
        if palavra.endswith(sufixo) and len(palavra) - len(sufixo) >= minimo:
            if sufixo == "s" and len(palavra) < 4:
                continue  # evita "his" -> "hi"
            raiz = palavra[: len(palavra) - len(sufixo)] + troca
            formas.append(raiz)
            # running -> runn -> run
            if sufixo in ("ing", "ed") and troca == "" and len(raiz) >= 3 and raiz[-1] == raiz[-2]:
                formas.append(raiz[:-1])
    return formas


def _candidatos(termo: str, artigos, regras) -> list:
    """O que vale a pena procurar, da forma exacta para a menos provável."""
    base = termo
    for artigo in artigos:
        if base.startswith(artigo) and len(base) > len(artigo):
            base = base[len(artigo):].strip()
            break
    candidatos = [termo]
    if base != termo:
        candidatos.append(base)
    if " " not in base:  # expressões: só a forma exacta
        candidatos += _formas(base, regras)
    return candidatos


def buscar_en_pt(palavra: str):
    """Devolve a linha do dicionário (dict) ou None."""
    en = _indices()["en"]
    for candidato in _candidatos(_chave(palavra), ARTIGOS_EN, REGRAS_EN):
        if candidato in en:
            return en[candidato]
    return None


def buscar_pt_en(palavra: str):
    """Procura nas glosas de trad_pt (várias, separadas por vírgula). Devolve a linha ou None."""
    pt = _indices()["pt"]
    for candidato in _candidatos(_chave(palavra.replace("-", " ")), ARTIGOS_PT, REGRAS_PT):
        if candidato in pt:
            return pt[candidato][0]
    return None


def _parecida(termo: str, chaves: list):
    if len(termo) < 4:
        return None
    perto = difflib.get_close_matches(termo, chaves, n=1, cutoff=0.8)
    return perto[0] if perto else None


def sugerir_en_pt(palavra: str):
    """Para gralhas: devolve a palavra inglesa mais parecida, ou None."""
    ind = _indices()
    chave = _parecida(_chave(palavra), ind["chaves_en"])
    return ind["en"][chave]["word_en"] if chave else None


def sugerir_pt_en(palavra: str):
    """Para gralhas: devolve a palavra portuguesa mais parecida, ou None."""
    ind = _indices()
    chave = _parecida(_chave(palavra.replace("-", " ")), ind["chaves_pt"])
    return ind["pt"][chave][1] if chave else None


def palavra_do_dia():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM words ORDER BY RANDOM() LIMIT 1")
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None
