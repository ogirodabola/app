import sqlite3
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "girodabola.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def criar_tabelas():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS noticias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            slug TEXT UNIQUE,
            url TEXT UNIQUE,
            fonte TEXT,
            categoria TEXT,
            criada_em TEXT
        )
    """)

    conn.commit()
    conn.close()


def salvar_noticia(titulo, url, fonte, categoria, slug):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO noticias
        (titulo, url, fonte, categoria, slug, criada_em)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        titulo,
        url,
        fonte,
        categoria,
        slug,
        datetime.utcnow()
    ))

    conn.commit()
    conn.close()

def listar_noticias(limit=30, categoria=None):
    conn = get_db()
    cursor = conn.cursor()

    if categoria:
        cursor.execute("""
            SELECT * FROM noticias
            WHERE categoria = ?
            ORDER BY criada_em DESC
            LIMIT ?
        """, (categoria, limit))
    else:
        cursor.execute("""
            SELECT * FROM noticias
            ORDER BY criada_em DESC
            LIMIT ?
        """, (limit,))

    rows = cursor.fetchall()
    conn.close()
    return rows


def listar_categorias():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT categoria
        FROM noticias
        WHERE categoria IS NOT NULL
        ORDER BY categoria
    """)

    rows = cursor.fetchall()
    conn.close()
    return [r["categoria"] for r in rows]
