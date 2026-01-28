import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv("DATABASE_URL")


def get_conn():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL não definida")
    return psycopg2.connect(DATABASE_URL)


def criar_tabelas():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS noticias (
                    id SERIAL PRIMARY KEY,
                    titulo TEXT NOT NULL,
                    resumo TEXT,
                    url TEXT UNIQUE,
                    fonte TEXT,
                    categoria TEXT,
                    slug TEXT,
                    imagem TEXT,
                    imagem_credito TEXT,
                    conteudo_editorial TEXT,
                    tags TEXT[],
                    criada_em TIMESTAMP DEFAULT NOW()
                );
            """)
        conn.commit()
    finally:
        conn.close()


def listar_noticias(limit: int = 20):
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT *
                FROM noticias
                ORDER BY criada_em DESC
                LIMIT %s
            """, (limit,))
            return cur.fetchall()
    finally:
        conn.close()


def listar_noticias_por_categoria(categoria: str, limit: int = 20):
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT *
                FROM noticias
                WHERE categoria = %s
                ORDER BY criada_em DESC
                LIMIT %s
            """, (categoria, limit))
            return cur.fetchall()
    finally:
        conn.close()


def buscar_noticia_por_slug(slug: str):
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT *
                FROM noticias
                WHERE slug = %s
                LIMIT 1
            """, (slug,))
            return cur.fetchone()
    finally:
        conn.close()


def salvar_noticia(
    titulo, resumo, url, fonte, categoria, slug,
    imagem=None, imagem_credito=None
):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO noticias
                (titulo, resumo, url, fonte, categoria, slug, imagem, imagem_credito)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (url) DO NOTHING;
            """, (
                titulo, resumo, url, fonte, categoria,
                slug, imagem, imagem_credito
            ))
        conn.commit()
    finally:
        conn.close()
