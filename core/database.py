import sqlite3
from pathlib import Path

# Caminho absoluto do banco (seguro no Render)
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "girodabola.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def criar_tabela_noticias():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS noticias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            url TEXT NOT NULL UNIQUE,
            fonte TEXT NOT NULL,

            categoria TEXT NOT NULL,
            subcategoria TEXT NOT NULL,
            tags TEXT,

            criada_em DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

def salvar_noticia(titulo, url, fonte, categoria, subcategoria, tags, slug):
    criar_tabela_noticias()

    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO noticias
            (titulo, slug, url, fonte, categoria, subcategoria, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            titulo,
            slug,
            url,
            fonte,
            categoria,
            subcategoria,
            ",".join(tags)
        ))
        conn.commit()
        print(f"[OK] Notícia salva: {titulo}")

    except sqlite3.IntegrityError:
        print(f"[SKIP] Já existe: {url}")

    finally:
        conn.close()
