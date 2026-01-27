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

    # Tabela de notícias
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS noticias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            url TEXT UNIQUE NOT NULL,
            fonte TEXT,
            categoria TEXT,
            tags TEXT,
            criada_em TEXT
        )
    """)

    # Verifica se a coluna criada_em existe (migração automática)
    cursor.execute("PRAGMA table_info(noticias)")
    colunas = [col["name"] for col in cursor.fetchall()]

    if "criada_em" not in colunas:
        print("[MIGRATION] Recriando tabela noticias")

        cursor.execute("""
            CREATE TABLE noticias_nova (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                fonte TEXT,
                categoria TEXT,
                tags TEXT,
                criada_em TEXT
            )
        """)

        cursor.execute("""
            INSERT INTO noticias_nova (id, titulo, url, fonte, categoria, tags)
            SELECT id, titulo, url, fonte, categoria, tags FROM noticias
        """)

        cursor.execute("DROP TABLE noticias")
        cursor.execute("ALTER TABLE noticias_nova RENAME TO noticias")

    conn.commit()
    conn.close()


def salvar_noticia(titulo, url, fonte, categoria=None, tags=None):
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO noticias (titulo, url, fonte, categoria, tags, criada_em)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            titulo,
            url,
            fonte,
            categoria,
            tags,
            datetime.utcnow().isoformat()
        ))
        conn.commit()
        print(f"[OK] Notícia salva: {titulo}")
    except sqlite3.IntegrityError:
        print(f"[SKIP] Notícia já existe: {url}")

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
