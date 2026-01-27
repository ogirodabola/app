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
            slug TEXT,
            url TEXT UNIQUE NOT NULL,
            fonte TEXT,
            categoria TEXT,
            subcategoria TEXT,
            tags TEXT,
            criada_em TEXT
        )
    """)

    conn.commit()
    conn.close()


def salvar_noticia(
    titulo: str,
    url: str,
    fonte: str,
    categoria: str = None,
    subcategoria: str = None,
    tags: list[str] | None = None,
    slug: str | None = None
):
    conn = get_db()
    cursor = conn.cursor()

    tags_str = ",".join(tags) if tags else None

    try:
        cursor.execute("""
            INSERT INTO noticias (
                titulo, slug, url, fonte,
                categoria, subcategoria, tags, criada_em
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            titulo,
            slug,
            url,
            fonte,
            categoria,
            subcategoria,
            tags_str,
            datetime.utcnow().isoformat()
        ))

        conn.commit()
        print(f"[OK] Notícia salva: {titulo}")

    except sqlite3.IntegrityError:
        print(f"[SKIP] Notícia já existe: {url}")

    finally:
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

    categorias = [row["categoria"] for row in cursor.fetchall()]
    conn.close()
    return categorias
