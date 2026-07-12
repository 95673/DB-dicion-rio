import re
import csv
import sqlite3

INPUT = "raw_words.txt"
CSV_OUT = "dicionario.csv"
DB_OUT = "dicionario.db"

# Exceções conhecidas onde a pronúncia tem 2 formas (contém vírgula antes da tradução)
# formato: id -> (pron_completa, traducao)
EXCECOES = {
    109: ("lêv, laiv", "viver, vivo"),
}

rows = []
with open(INPUT, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        m = re.match(r"^(\d+)\s+(\S+)\s+(.+)$", line)
        if not m:
            print("LINHA IGNORADA:", line)
            continue
        idx = int(m.group(1))
        word = m.group(2)
        rest = m.group(3)

        if idx in EXCECOES:
            pron, trad = EXCECOES[idx]
        else:
            # pron = primeiro token do resto, tradução = o restante
            partes = rest.split(" ", 1)
            pron = partes[0]
            trad = partes[1] if len(partes) > 1 else ""

        rows.append({
            "id": idx,
            "word_en": word,
            "pron": pron,
            "trad_pt": trad,
        })

print(f"Total de palavras parseadas: {len(rows)}")

# Salvar CSV
with open(CSV_OUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["id", "word_en", "pron", "trad_pt"])
    writer.writeheader()
    writer.writerows(rows)

# Criar banco SQLite com índices para busca rápida EN->PT e PT->EN
conn = sqlite3.connect(DB_OUT)
cur = conn.cursor()
cur.execute("DROP TABLE IF EXISTS words")
cur.execute("""
CREATE TABLE words (
    id INTEGER PRIMARY KEY,
    word_en TEXT NOT NULL,
    pron TEXT NOT NULL,
    trad_pt TEXT NOT NULL
)
""")
cur.executemany(
    "INSERT INTO words (id, word_en, pron, trad_pt) VALUES (:id, :word_en, :pron, :trad_pt)",
    rows,
)
cur.execute("CREATE INDEX idx_word_en ON words (word_en)")
conn.commit()
conn.close()

print(f"CSV gerado: {CSV_OUT}")
print(f"Banco SQLite gerado: {DB_OUT}")
