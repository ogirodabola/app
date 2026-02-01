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
# TABELAS
# ======================================================
def criar_tabelas():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS noticias (
                    id SERIAL PRIMARY KEY,
                    titulo TEXT NOT NULL,
                    titulo_editorial TEXT,
                    resumo TEXT,
                    url TEXT UNIQUE NOT NULL,
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
# HOME – ÚLTIMA HORA
# ======================================================
def listar_ultima_hora(limit=12):
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                  id,
                  CASE
                    WHEN editorial_status IN ('rapido', 'pronto')
                      THEN titulo_editorial
                    ELSE titulo
                  END AS titulo,
                  slug,
                  fonte,
                  categoria,
                  imagem,
                  criada_em,
                  editorial_status
                FROM noticias
                ORDER BY criada_em DESC
                LIMIT %s;
                """,
                (limit,)
            )
            return cur.fetchall()
    finally:
        conn.close()

def listar_ultimas_editoriais(limit=5):
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    id,
                    slug,
                    titulo,
                    titulo_editorial,
                    categoria,
                    imagem,
                    fonte
                FROM noticias
                ORDER BY criada_em DESC
                LIMIT %s
            """, (limit,))
            return cur.fetchall()
    finally:
        conn.close()


# ======================================================
# HOME – POR CATEGORIA (GENÉRICO)
# ======================================================
def listar_por_categoria(categoria: str, limit: int = 10):
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
                  imagem,
                  criada_em
                FROM noticias

                WHERE categoria = %s
                ORDER BY criada_em DESC
                LIMIT %s;
            """, (categoria, limit))
            return cur.fetchall()
    finally:
        conn.close()


# ======================================================
# HOME – BRASILEIRÃO (ALIAS EDITORIAL)
# ======================================================
def listar_brasileirao(limit: int = 10):
    """
    Wrapper semântico para o bloco editorial 'Brasileirão'.
    NÃO duplica query.
    Mantém contrato com main.py.
    """
    return listar_por_categoria("Brasileirão", limit)


# ======================================================
# LISTAGEM GENÉRICA (fallback / admin)
# ======================================================
def listar_noticias(limit: int = 30):
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
# NOTÍCIA INDIVIDUAL
# ======================================================
def buscar_noticia_por_slug(slug: str):
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    id,
                    COALESCE(titulo_editorial, titulo) AS titulo,
                    titulo AS titulo_original,
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
# CATEGORIAS DISPONÍVEIS
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
# INSERIR / ATUALIZAR NOTÍCIA (crawler)
# ======================================================
def salvar_noticia(
    titulo,
    resumo,
    url,
    fonte,
    categoria,
    slug,
    imagem=None,
    imagem_credito=None
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
                titulo,
                resumo,
                url,
                fonte,
                categoria,
                slug,
                imagem,
                imagem_credito
            ))
        conn.commit()
    finally:
        conn.close()


# ======================================================
# ATUALIZA EDITORIAL (worker IA)
# ======================================================
def atualizar_editorial(
    noticia_id: int,
    titulo_editorial: str,
    conteudo_editorial: str,
    tags: list[str] | None = None,
    categoria: str | None = None
):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE noticias
                SET
                    titulo_editorial = %s,
                    conteudo_editorial = %s,
                    tags = %s,
                    categoria = COALESCE(%s, categoria)
                WHERE id = %s;
            """, (
                titulo_editorial,
                conteudo_editorial,
                tags,
                categoria,
                noticia_id
            ))
        conn.commit()
    finally:
        conn.close()


# ======================================================
# BUSCAR NOTÍCIAS SEM EDITORIAL (worker IA)
# ======================================================
def listar_pendentes_editorial(limit: int = 10):
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    id,
                    titulo,
                    resumo,
                    categoria
                FROM noticias
                WHERE conteudo_editorial IS NULL
                ORDER BY criada_em ASC
                LIMIT %s;
            """, (limit,))
            return cur.fetchall()
    finally:
        conn.close()

def listar_recomendadas_por_slug(slug: str, limit: int = 5):
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                  n2.id,
                  COALESCE(n2.titulo_editorial, n2.titulo) AS titulo,
                  n2.slug,
                  n2.categoria,
                  n2.criada_em,
                  array_length(
                    ARRAY(
                      SELECT UNNEST(n2.tags)
                      INTERSECT
                      SELECT UNNEST(n1.tags)
                    ),
                    1
                  ) AS score
                FROM noticias n1
                JOIN noticias n2
                  ON n2.id != n1.id
                WHERE
                  n1.slug = %s
                  AND n2.categoria = n1.categoria
                  AND n2.tags && n1.tags
                ORDER BY
                  score DESC NULLS LAST,
                  n2.criada_em DESC
                LIMIT %s;
                """,
                (slug, limit)
            )
            return cur.fetchall()
    finally:
        conn.close()

def listar_recomendadas_por_slug(slug_atual, limit=5):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, titulo, titulo_editorial, slug, categoria, imagem, fonte
                FROM noticias
                WHERE slug != %s
                ORDER BY criada_em DESC
                LIMIT %s
                """,
                (slug_atual, limit)
            )
            return cur.fetchall()
def tabela_brasileirao_mock():
    return [
        {
            "posicao": 1,
            "nome": "Flamengo",
            "escudo": "https://media.api-sports.io/football/teams/127.png",
            "jogos": 10,
            "vitorias": 7,
        },
        {
            "posicao": 2,
            "nome": "Palmeiras",
            "escudo": "https://media.api-sports.io/football/teams/121.png",
            "jogos": 10,
            "vitorias": 6,
        },
        {
            "posicao": 3,
            "nome": "Atlético-MG",
            "escudo": "https://media.api-sports.io/football/teams/106.png",
            "jogos": 10,
            "vitorias": 6,
        },
        {
            "posicao": 4,
            "nome": "Grêmio",
            "escudo": "https://media.api-sports.io/football/teams/131.png",
            "jogos": 10,
            "vitorias": 5,
        },
        {
            "posicao": 5,
            "nome": "São Paulo",
            "escudo": "https://media.api-sports.io/football/teams/126.png",
            "jogos": 10,
            "vitorias": 5,
        },
    ]
