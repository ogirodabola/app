import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get("DATABASE_URL")


def get_db():
    return psycopg2.connect(
        DATABASE_URL,
        cursor_factory=RealDictCursor
    )


def criar_tabelas():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS noticias (
        id SERIAL PRIMARY KEY,
        titulo TEXT NOT NULL,
        resumo TEXT,
        url TEXT UNIQUE NOT NULL,
        fonte TEXT,
        categoria TEXT,
        slug TEXT,
        imagem TEXT,
        criada_em TIMESTAMP DEFAULT NOW()
    );
    """)

    conn.commit()
    cur.close()
    conn.close()


def salvar_noticia(titulo, resumo, url, fonte, categoria=None, slug=None, imagem=None):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO noticias (titulo, resumo, url, fonte, categoria, slug, imagem)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (url) DO NOTHING
    """, (titulo, resumo, url, fonte, categoria, slug, imagem))

    conn.commit()
    cur.close()
    conn.close()


def listar_noticias(limit=30, categoria=None):
    conn = get_db()
    cur = conn.cursor()

    if categoria:
        cur.execute("""
        SELECT * FROM noticias
        WHERE categoria = %s
        ORDER BY criada_em DESC
        LIMIT %s
        """, (categoria, limit))
    else:
        cur.execute("""
        SELECT * FROM noticias
        ORDER BY criada_em DESC
        LIMIT %s
        """, (limit,))

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def listar_categorias():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT DISTINCT categoria
    FROM noticias
    WHERE categoria IS NOT NULL
    ORDER BY categoria
    """)

    rows = [r["categoria"] for r in cur.fetchall()]
    cur.close()
    conn.close()
    return rows

def listar_hot_news(horas=3, limit=24):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM noticias
        WHERE criada_em >= NOW() - INTERVAL %s
        ORDER BY criada_em DESC
        LIMIT %s
    """, (f'{horas} hours', limit))

    rows = cursor.fetchall()
    conn.close()

    return rows
