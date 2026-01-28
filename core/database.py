import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv("DATABASE_URL")


# ======================================================
# CONEXÃO
# ======================================================
def get_conn():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL não definida")
    return psycopg2.connect(DATABASE_URL)


# ======================================================
# TABELA (SEM QUEBRAR BANCO EXISTENTE)
# ======================================================
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
                    slug TEXT UNIQUE,
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


# ======================================================
# HOME / LISTAGEM
# ======================================================
def listar_noticias(limit: int = 30, categoria: str | None = None):
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:

            if categoria:
                cur.execute("""
                    SELECT
                        id,
                        titulo,
                        slug,
                        fonte,
                        categoria,
                        imagem,
                        criada_em
                    FROM noticias
                    WHERE categoria = %s
                    ORDER BY criada_em DESC
                    LIMIT %s;
                """, (categoria, limit))
            else:
                cur.execute("""
                    SELECT
                        id,
                        titulo,
                        slug,
                        fonte,
                        categoria,
                        imagem,
                        criada_em
                    FROM noticias
                    ORDER BY criada_em DESC
                    LIMIT %s;
                """, (limit,))

            return cur.fetchall()
    finally:
        conn.close()


# ======================================================
# HOT NEWS
# ======================================================
def listar_hot_news(limit: int = 24):
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    id,
                    titulo,
                    slug,
                    fonte,
                    categoria,
                    imagem,
                    criada_em
                FROM noticias
                ORDER BY criada_em DESC
                LIMIT %s;
            """, (limit,))
            return cur.fetchall()
    finally:
        conn.close()


# ======================================================
# NOTÍCIA INDIVIDUAL (EDITORIAL AQUI SIM)
# ======================================================
def buscar_noticia_por_slug(slug: str):
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    id,
                    titulo,
                    resumo,
                    conteudo_editorial,
                    imagem,
                    imagem_credito,
                    fonte,
                    categoria,
                    tags,
                    criada_em
                FROM noticias
                WHERE slug = %s
                LIMIT 1;
            """, (slug,))
            return cur.fetchone()
    finally:
        conn.close()


# ======================================================
# CATEGORIAS
# ======================================================
def listar_categorias():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT categoria
                FROM noticias
                WHERE categoria IS NOT NULL
                ORDER BY categoria ASC;
            """)
            return [row[0] for row in cur.fetchall()]
    finally:
        conn.close()


# ======================================================
# INSERT / UPDATE (CRAWLER)
# ======================================================
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
                ON CONFLICT (url) DO UPDATE
                SET
                    imagem = COALESCE(noticias.imagem, EXCLUDED.imagem),
                    imagem_credito = COALESCE(noticias.imagem_credito, EXCLUDED.imagem_credito);
            """, (
                titulo, resumo, url, fonte,
                categoria, slug, imagem, imagem_credito
            ))
        conn.commit()
    finally:
        conn.close()
# ======================================================
# HOME – BLOCOS EDITORIAIS
# ======================================================

def listar_ultima_hora(limit: int = 8):
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                  id,
                  COALESCE(titulo_editorial, titulo) AS titulo,
                  slug,
                  fonte,
                  categoria,
                  criada_em
                FROM noticias
                WHERE categoria = 'Futebol'
                ORDER BY criada_em DESC
                LIMIT %s;
            """, (limit,))
            return cur.fetchall()
    finally:
        conn.close()


def listar_brasileirao(limit: int = 10):
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                  id,
                  COALESCE(titulo_editorial, titulo) AS titulo,
                  slug,
                  fonte,
                  criada_em
                FROM noticias
                WHERE
                  categoria = 'Campeonato Brasileiro'
                  OR tags && ARRAY['Brasileirão','Série A','Série B']
                ORDER BY criada_em DESC
                LIMIT %s;
            """, (limit,))
            return cur.fetchall()
    finally:
        conn.close()


def listar_mercado_bola(limit: int = 10):
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                  id,
                  COALESCE(titulo_editorial, titulo) AS titulo,
                  slug,
                  fonte,
                  criada_em
                FROM noticias
                WHERE
                  categoria = 'Mercado da Bola'
                  OR tags && ARRAY[
                    'Contratação','Transferência','Renovação','Mercado'
                  ]
                ORDER BY criada_em DESC
                LIMIT %s;
            """, (limit,))
            return cur.fetchall()
    finally:
        conn.close()


def listar_analises(limit: int = 6):
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                  id,
                  titulo_editorial AS titulo,
                  slug,
                  fonte,
                  criada_em
                FROM noticias
                WHERE
                  conteudo_editorial IS NOT NULL
                  AND categoria IN ('Análise','Opinião')
                ORDER BY criada_em DESC
                LIMIT %s;
            """, (limit,))
            return cur.fetchall()
    finally:
        conn.close()


def listar_bastidores(limit: int = 6):
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                  id,
                  COALESCE(titulo_editorial, titulo) AS titulo,
                  slug,
                  fonte,
                  criada_em
                FROM noticias
                WHERE
                  categoria IN ('Gestão','Bastidores')
                  OR tags && ARRAY['Gestão','Finanças','CBF','Bastidores']
                ORDER BY criada_em DESC
                LIMIT %s;
            """, (limit,))
            return cur.fetchall()
    finally:
        conn.close()
