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
                    conteudo_editorial TEXT,
                    criada_em TIMESTAMP DEFAULT NOW()
                );
            """)
        conn.commit()
    finally:
        conn.close()


def salvar_noticia(
    titulo: str,
    resumo: str,
    url: str,
    fonte: str,
    categoria: str,
    slug: str
):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO noticias (titulo, resumo, url, fonte, categoria, slug)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (url) DO NOTHING;
            """, (titulo, resumo, url, fonte, categoria, slug))
        conn.commit()
    finally:
        conn.close()
