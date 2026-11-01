"""Base de dados SQLite: ligação e registo de buscas (logs)."""

import hashlib
import sqlite3
from datetime import datetime

import config

# Resultado de cada busca (coluna "sucesso" dos logs)
NAO_ENCONTRADA = 0
ENCONTRADA = 1
RESPONDIDA_PELA_IA = 2  # não estava no dicionário; foi o Grok que respondeu


def get_conn():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def proteger_numero(phone_number: str) -> str:
    """
    Devolve uma versão cifrada (hash) do número.
    Assim dá para contar números únicos sem guardar o número de ninguém.
    """
    if not phone_number:
        return ""
    texto = config.HASH_SALT + phone_number
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()[:16]


def init_logs():
    """Cria a tabela de logs se não existir (não apaga dados existentes)."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            phone_number TEXT,
            direcao TEXT,
            termo_buscado TEXT,
            sucesso INTEGER
        )
    """)
    # Se o HASH_SALT estiver configurado, cifra também os números antigos (uma só vez)
    if config.HASH_SALT:
        cur.execute(
            "SELECT id, phone_number FROM logs "
            "WHERE phone_number IS NOT NULL AND phone_number != '' AND LENGTH(phone_number) != 16"
        )
        for row in cur.fetchall():
            cur.execute(
                "UPDATE logs SET phone_number = ? WHERE id = ?",
                (proteger_numero(row["phone_number"]), row["id"]),
            )
    conn.commit()
    conn.close()


def registrar_busca(phone_number: str, direcao: str, termo: str, resultado: int):
    """Grava uma linha de log: data, número cifrado, direção, termo e o resultado (0, 1 ou 2)."""
    if config.MODO_SIMULADOR:
        return
    conn = get_conn()
    cur = conn.cursor()
    data_hoje = datetime.now().strftime("%d/%m/%Y")
    termo_limpo = " ".join(termo.lower().split())[:100]  # assim "Water" e "water" contam como uma só
    cur.execute(
        "INSERT INTO logs (data, phone_number, direcao, termo_buscado, sucesso) VALUES (?, ?, ?, ?, ?)",
        (data_hoje, proteger_numero(phone_number), direcao, termo_limpo, int(resultado)),
    )
    conn.commit()
    conn.close()


def obter_estatisticas() -> dict:
    """Números para o painel /stats."""
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM logs")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM logs WHERE sucesso >= 1")
    sucesso = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM logs WHERE sucesso = 2")
    pela_ia = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT phone_number) FROM logs")
    numeros_unicos = cur.fetchone()[0]

    def top(filtro: str):
        cur.execute(
            "SELECT termo_buscado, COUNT(*) AS qtd FROM logs "
            f"WHERE {filtro} GROUP BY termo_buscado ORDER BY qtd DESC LIMIT 15"
        )
        return [(r["termo_buscado"], r["qtd"]) for r in cur.fetchall()]

    cur.execute(
        "SELECT direcao, LOWER(TRIM(termo_buscado)) AS termo, COUNT(*) AS qtd FROM logs "
        "WHERE direcao IN ('en-pt', 'pt-en') AND sucesso = 0 "
        "GROUP BY direcao, termo ORDER BY qtd DESC LIMIT 20"
    )
    nao_encontradas = [(r["direcao"], r["termo"], r["qtd"]) for r in cur.fetchall()]

    top_palavras = top("direcao IN ('en-pt', 'pt-en')")

    cur.execute(
        "SELECT direcao, termo_buscado, sucesso, COUNT(*) AS qtd FROM logs "
        "WHERE direcao IN ('en-pt', 'pt-en') AND sucesso IN (0, 2) "
        "GROUP BY direcao, termo_buscado, sucesso ORDER BY qtd DESC LIMIT 20"
    )
    palavras_em_falta = [
        (r["direcao"], r["termo_buscado"], r["sucesso"], r["qtd"]) for r in cur.fetchall()
    ]
    top_duvidas = top("direcao = 'duvida'")
    duvidas_sem_resposta = top("direcao = 'duvida' AND sucesso = 0")

    cur.execute(
        "SELECT data, COUNT(*) AS qtd FROM logs GROUP BY data ORDER BY MAX(id) DESC LIMIT 15"
    )
    por_dia = [(r["data"], r["qtd"]) for r in cur.fetchall()]

    conn.close()
    return {
        "total": total,
        "sucesso": sucesso,
        "pela_ia": pela_ia,
        "numeros_unicos": numeros_unicos,
        "top_palavras": top_palavras,
        "nao_encontradas": nao_encontradas,
        "palavras_em_falta": palavras_em_falta,
        "top_duvidas": top_duvidas,
        "duvidas_sem_resposta": duvidas_sem_resposta,
        "por_dia": por_dia,
    }
