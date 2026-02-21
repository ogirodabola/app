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
                    conteudo_original TEXT,   -- 🔥 NOVO
                    conteudo_editorial TEXT,
                    categoria TEXT,
                    tags TEXT[],
                    imagem TEXT,
                    imagem_credito TEXT,
                    url TEXT UNIQUE NOT NULL,
                    slug TEXT UNIQUE NOT NULL,
                    fonte TEXT,
                    editorial_status TEXT DEFAULT 'pendente',
                    criada_em TIMESTAMP DEFAULT NOW()
                );

            """)
        conn.commit()
    finally:
        conn.close()

# ======================================================
# HOME – ÚLTIMA HORA
# ======================================================

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
        {
            "posicao": 6,
            "nome": "Internacional",
            "escudo": "https://media.api-sports.io/football/teams/130.png",
            "jogos": 10,
            "vitorias": 4,
        },
    ]

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
                WHERE conteudo_editorial IS NOT NULL
                ORDER BY criada_em DESC

                LIMIT %s;
                """,
                (limit,)
            )
            return cur.fetchall()
    finally:
        conn.close()

def listar_ultimas_editoriais(limit=8):
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
                WHERE conteudo_editorial IS NOT NULL
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
                AND conteudo_editorial IS NOT NULL
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
                AND conteudo_editorial IS NOT NULL
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
    imagem_credito=None,
    conteudo_original=None
):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO noticias
                (titulo, resumo, url, fonte, categoria, slug, imagem, imagem_credito, conteudo_original)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
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
                imagem_credito,
                conteudo_original   # 🔥 AQUI ESTAVA FALTANDO
            ))
        conn.commit()
    finally:
        conn.close()

# =============================
# VINCULAR JOGADOR AUTOMATICAMENTE
# =============================

def vincular_jogador_na_noticia(noticia_id: int, jogador_nome: str):
    from core.database import buscar_ou_criar_jogador
    from core.database import salvar_relacao_noticia_jogadores

    if not jogador_nome:
        return

    try:
        jogador = buscar_ou_criar_jogador(jogador_nome)

        if jogador:
            salvar_relacao_noticia_jogadores(
                noticia_id=noticia_id,
                jogador_id=jogador["id"]
            )

    except Exception as e:
        print(f"Erro ao vincular jogador: {e}")

def salvar_relacao_noticia_jogador(noticia_id, jogador_id):
    return vincular_jogador_noticia(noticia_id, jogador_id)

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
                    categoria = COALESCE(%s, categoria),
                    editorial_status = 'publicado'  -- AUTO PUBLISH
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
            
# ======================================================
# CLASSIFICAÇÃO — BRASILEIRÃO
# ======================================================
def buscar_classificacao_brasileirao():
    """
    Fonte única da classificação.
    - Tenta API
    - Se falhar, usa mock
    - Nunca quebra o template
    """

    try:
        # import atrasado (CORRETO)
        from core.futebol_api import buscar_classificacao_brasileirao as api_call
        tabela = api_call()
        print("Classificação vinda da API:", type(tabela))
    except Exception as e:
        print("Erro ao buscar classificação na API:", e)
        tabela = None

    # ✅ fallback seguro
    if not tabela:
        print("Usando MOCK da classificação")
        tabela = tabela_brasileirao_mock()

    return [
        {
            "posicao": t.get("posicao"),
            "nome": t.get("nome"),
            "escudo": t.get("escudo"),
            "pontos": t.get("pontos", 0),
            "jogos": t.get("jogos", 0),
            "vitorias": t.get("vitorias", 0),
            "saldo_gols": t.get("saldo_gols", 0),
            "gols_pro": t.get("gols_pro", 0),
            "gols_contra": t.get("gols_contra", 0),
        }
        for t in tabela
    ]

def buscar_ad_por_slot(nome_slot: str):
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    s.nome,
                    s.ativo AS slot_ativo,
                    sc.codigo,
                    sc.ativo AS script_ativo
                FROM ads_slots s
                LEFT JOIN ads_scripts sc ON sc.slot_id = s.id
                WHERE s.nome = %s
                LIMIT 1;
            """, (nome_slot,))
            return cur.fetchone()
    finally:
        conn.close()

from psycopg2.extras import RealDictCursor

# ======================================================
# ADS — LISTAR SLOTS
# ======================================================
def listar_ads_slots():
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    s.id,
                    s.nome,
                    s.pagina,
                    s.posicao,
                    s.dispositivo,
                    s.ativo,
                    sc.codigo
                FROM ads_slots s
                LEFT JOIN ads_scripts sc ON sc.slot_id = s.id
                ORDER BY s.pagina, s.posicao;
            """)
            return cur.fetchall()


# ======================================================
# ADS — BUSCAR SLOT POR ID
# ======================================================
def buscar_ads_slot(slot_id: int):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    s.id,
                    s.nome,
                    s.pagina,
                    s.posicao,
                    s.dispositivo,
                    s.ativo,
                    sc.codigo,
                    sc.ativo AS script_ativo
                FROM ads_slots s
                LEFT JOIN ads_scripts sc ON sc.slot_id = s.id
                WHERE s.id = %s
                LIMIT 1;
            """, (slot_id,))
            return cur.fetchone()


# ======================================================
# ADS — SALVAR SCRIPT
# ======================================================
def salvar_ads_script(slot_id: int, codigo: str, ativo: bool):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO ads_scripts (slot_id, tipo, codigo, ativo)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (slot_id)
                DO UPDATE SET
                    tipo = EXCLUDED.tipo,
                    codigo = EXCLUDED.codigo,
                    ativo = EXCLUDED.ativo;
            """, (slot_id, "html", codigo, ativo))
        conn.commit()

# ======================================================
# ADS — ATIVAR / DESATIVAR SLOT
# ======================================================
def atualizar_ads_slot_status(slot_id: int, ativo: bool):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE ads_slots
                SET ativo = %s
                WHERE id = %s;
            """, (ativo, slot_id))
        conn.commit()

from psycopg2.extras import RealDictCursor
from slugify import slugify

# ======================================================
# NOTÍCIAS — LISTAR
# ======================================================
def listar_noticias():
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT n.id, n.titulo, n.status, n.criada_em, c.nome AS categoria
                FROM noticias n
                LEFT JOIN categorias c ON c.id = n.categoria_id
                ORDER BY n.criada_em DESC;
            """)
            return cur.fetchall()


# ======================================================
# NOTÍCIAS — BUSCAR POR ID
# ======================================================
from psycopg2.extras import RealDictCursor

def listar_noticias_admin(
    status: str | None = None,
    categoria: str | None = None,
    busca: str | None = None,
    fonte: str | None = None
):
    query = """
        SELECT
            id,
            COALESCE(titulo_editorial, titulo) AS titulo,
            categoria,
            editorial_status,
            criada_em
        FROM noticias
        WHERE 1=1
    """
    params = []
    
    if status:
        query += " AND editorial_status = %s"
        params.append(status)

    if categoria:
        query += " AND categoria = %s"
        params.append(categoria)

    if busca and busca.strip():
        query += " AND COALESCE(titulo_editorial, titulo) ILIKE %s"
        params.append(f"%{busca.strip()}%")

    if fonte:
        query += " AND fonte = %s"
        params.append(fonte)

    query += " ORDER BY criada_em DESC"

    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, tuple(params))
            return cur.fetchall()

# ======================================================
# NOTÍCIAS — CRIAR
# ======================================================
def criar_noticia(dados: dict):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO noticias
                (titulo_editorial, resumo, conteudo_editorial, imagem,
                 categoria, tags, editorial_status, slug)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                dados.get("titulo_editorial"),
                dados.get("resumo"),
                dados.get("conteudo_editorial"),
                dados.get("imagem"),
                dados.get("categoria"),
                dados.get("tags"),
                dados.get("editorial_status", "pendente"),
                dados.get("slug"),
            ))
        conn.commit()



# ======================================================
# NOTÍCIAS — ATUALIZAR
# ======================================================
def atualizar_noticia(noticia_id: int, dados: dict):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE noticias
                SET
                  titulo_editorial = %s,
                  resumo = %s,
                  conteudo_editorial = %s,
                  imagem = %s,
                  categoria = %s,
                  tags = %s,
                  editorial_status = %s,
                  slug = %s
                WHERE id = %s;
            """, (
                dados.get("titulo_editorial"),
                dados.get("resumo"),
                dados.get("conteudo_editorial"),
                dados.get("imagem"),
                dados.get("categoria"),
                dados.get("tags"),
                dados.get("editorial_status", "pendente"),
                dados.get("slug"),
                noticia_id
            ))
        conn.commit()


from psycopg2.extras import RealDictCursor

# ======================================================
# NOTÍCIAS — HOME (PUBLICADAS)
# ======================================================
def listar_noticias_publicadas(limit=10):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                  id,
                  slug,
                  titulo,
                  titulo_editorial,
                  resumo,
                  imagem,
                  categoria,
                  criada_em
                FROM noticias
                WHERE editorial_status = 'publicado'
                ORDER BY criada_em DESC
                LIMIT %s;
            """, (limit,))
            return cur.fetchall()

# ======================================================
# NOTÍCIA — PÁGINA INDIVIDUAL
# ======================================================
def buscar_noticia_publica(slug: str):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                  COALESCE(titulo_editorial, titulo) AS titulo,
                  resumo,
                  conteudo_editorial AS conteudo,
                  imagem,
                  imagem_credito,
                  categoria,
                  tags,
                  criada_em
                FROM noticias
                WHERE slug = %s
                  AND editorial_status = 'publicado'
                LIMIT 1;
            """, (slug,))
            return cur.fetchone()

from psycopg2.extras import RealDictCursor

# ======================================================
# ÚLTIMA HORA — PUBLICADAS
# ======================================================
def listar_ultima_hora_publicada(limit=6):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                  id,
                  slug,
                  titulo_editorial,
                  COALESCE(titulo_editorial, titulo) AS titulo,
                  resumo,
                  imagem,
                  categoria,
                  fonte,
                  criada_em
                FROM noticias
                WHERE editorial_status = 'publicado'
                  AND categoria = 'Última Hora'
                ORDER BY criada_em DESC
                LIMIT %s;
            """, (limit,))
            return cur.fetchall()

# ======================================================
# EDITORIAL — PUBLICADAS (EXCETO ÚLTIMA HORA)
# ======================================================
def listar_editorial_publicado(limit=6):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                  id,
                  slug,
                  titulo_editorial,
                  COALESCE(titulo_editorial, titulo) AS titulo,
                  resumo,
                  imagem,
                  categoria,
                  fonte,
                  criada_em
                FROM noticias
                WHERE editorial_status = 'publicado'
                  AND (categoria IS NULL OR categoria <> 'Última Hora')
                ORDER BY criada_em DESC
                LIMIT %s;
            """, (limit,))
            return cur.fetchall()

from psycopg2.extras import RealDictCursor

# ======================================================
# NOTÍCIAS — BUSCAR UMA (ADMIN / CMS)
# ======================================================
def buscar_noticia_admin(noticia_id: int):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT *
                FROM noticias
                WHERE id = %s
                LIMIT 1;
            """, (noticia_id,))
            return cur.fetchone()

def listar_ultimas_publicadas(limit=10):
    query = """
        SELECT *
        FROM noticias
        WHERE editorial_status = 'publicado'
        ORDER BY criada_em DESC
        LIMIT :limit
    """
    with engine.connect() as conn:
        return conn.execute(text(query), {"limit": limit}).fetchall()

# ======================================================
# ADS — ATUALIZAR DISPOSITIVO
# ======================================================
def atualizar_ads_slot_dispositivo(slot_id: int, dispositivo: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE ads_slots
                SET dispositivo = %s
                WHERE id = %s;
            """, (dispositivo, slot_id))
        conn.commit()

# ======================================================
# DASHBOARD — MÉTRICAS EDITORIAIS
# ======================================================
def obter_metricas_editoriais():
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:

            cur.execute("SELECT COUNT(*) FROM noticias")
            total = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*)
                FROM noticias
                WHERE editorial_status = 'publicado'
            """)
            publicadas = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*)
                FROM noticias
                WHERE conteudo_editorial IS NULL
            """)
            pendentes = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*)
                FROM noticias
                WHERE conteudo_editorial IS NOT NULL
                  AND editorial_status != 'publicado'
            """)
            prontas_ia = cur.fetchone()["count"]

            cur.execute("""
                SELECT id, COALESCE(titulo_editorial, titulo) AS titulo, criada_em
                FROM noticias
                ORDER BY criada_em DESC
                LIMIT 5
            """)
            ultimas = cur.fetchall()

            return {
                "total": total,
                "publicadas": publicadas,
                "pendentes": pendentes,
                "prontas_ia": prontas_ia,
                "ultimas": ultimas
            }

# ======================================================
# DASHBOARD — STATUS POR FONTE (CRAWLER)
# ======================================================
def dashboard_status_por_fonte():
    query = """
        SELECT
            fonte,
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE conteudo_editorial IS NULL) AS pendentes_ia,
            COUNT(*) FILTER (WHERE editorial_status = 'publicado') AS publicadas,
            COUNT(*) FILTER (
                WHERE conteudo_editorial IS NOT NULL
                AND editorial_status <> 'publicado'
            ) AS prontas_publicar
        FROM noticias
        GROUP BY fonte
        ORDER BY fonte;
    """

    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            return cur.fetchall()

def listar_home_hero():
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                  id,
                  slug,
                  COALESCE(titulo_editorial, titulo) AS titulo,
                  resumo,
                  imagem,
                  categoria,
                  fonte,
                  criada_em
                FROM noticias
                WHERE editorial_status = 'publicado'
                ORDER BY criada_em DESC
                LIMIT 5;
            """)
            return cur.fetchall()

def listar_home_feed(limit=20):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                  id,
                  slug,
                  COALESCE(titulo_editorial, titulo) AS titulo,
                  resumo,
                  imagem,
                  categoria,
                  fonte,
                  criada_em
                FROM noticias
                WHERE editorial_status = 'publicado'
                ORDER BY criada_em DESC
                LIMIT %s;
            """, (limit,))
            return cur.fetchall()

def listar_home_brasileirao(limit=6):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                  id,
                  slug,
                  COALESCE(titulo_editorial, titulo) AS titulo,
                  resumo,
                  imagem,
                  fonte,
                  criada_em
                FROM noticias
                WHERE categoria = 'Brasileirão'
                AND editorial_status = 'publicado'
                ORDER BY criada_em DESC
                LIMIT %s;
            """, (limit,))
            return cur.fetchall()

def listar_home_mercado(limit=6):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                  id,
                  slug,
                  COALESCE(titulo_editorial, titulo) AS titulo,
                  resumo,
                  imagem,
                  fonte,
                  criada_em
                FROM noticias
                WHERE categoria = 'Mercado da Bola'
                AND editorial_status = 'publicado'
                ORDER BY criada_em DESC
                LIMIT %s;
            """, (limit,))
            return cur.fetchall()

def listar_home_internacional(limit=6):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                  id,
                  slug,
                  COALESCE(titulo_editorial, titulo) AS titulo,
                  resumo,
                  imagem,
                  categoria,
                  fonte,
                  criada_em
                FROM noticias
                WHERE categoria NOT IN (
                    'Brasileirão',
                    'Mercado da Bola',
                    'Última Hora'
                )
                AND editorial_status = 'publicado'
                ORDER BY criada_em DESC
                LIMIT %s;
            """, (limit,))
            return cur.fetchall()

def listar_home_analises(limit=4):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                  id,
                  slug,
                  COALESCE(titulo_editorial, titulo) AS titulo,
                  resumo,
                  imagem,
                  criada_em
                FROM noticias
                WHERE categoria = 'Análises'
                AND editorial_status = 'publicado'
                ORDER BY criada_em DESC
                LIMIT %s;
            """, (limit,))
            return cur.fetchall()

def listar_home_bastidores(limit=4):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                  id,
                  slug,
                  COALESCE(titulo_editorial, titulo) AS titulo,
                  resumo,
                  imagem,
                  criada_em
                FROM noticias
                WHERE categoria = 'Bastidores'
                AND editorial_status = 'publicado'
                ORDER BY criada_em DESC
                LIMIT %s;
            """, (limit,))
            return cur.fetchall()

def listar_home_mais_lidas(limit=8):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                  id,
                  slug,
                  COALESCE(titulo_editorial, titulo) AS titulo,
                  categoria,
                  criada_em
                FROM noticias
                WHERE editorial_status = 'publicado'
                ORDER BY criada_em DESC
                LIMIT %s;
            """, (limit,))
            return cur.fetchall()

from slugify import slugify

def criar_ou_buscar_jogador(nome, foto=None, time_atual=None, escudo_time=None):
    slug = slugify(nome)

    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:

            cur.execute("SELECT * FROM jogadores WHERE slug = %s", (slug,))
            jogador = cur.fetchone()

            if jogador:
                return jogador

            cur.execute("""
                INSERT INTO jogadores (nome, slug, foto, time_atual, escudo_time)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING *;
            """, (nome, slug, foto, time_atual, escudo_time))

            conn.commit()
            return cur.fetchone()

# ==========================================================
# JOGADORES (SISTEMA HÍBRIDO API + CACHE LOCAL)
# ==========================================================

from datetime import datetime, timedelta
from slugify import slugify
from psycopg2.extras import RealDictCursor

# ----------------------------------------------------------
# BUSCAR JOGADOR NA API-FOOTBALL
# ----------------------------------------------------------

def buscar_jogador_na_api(nome):

    import requests
    import os

    BASE_URL = "https://v3.football.api-sports.io"
    API_KEY = os.getenv("API_FOOTBALL_KEY")

    if not API_KEY:
        return []

    headers = {"x-apisports-key": API_KEY}

    response = requests.get(
        f"{BASE_URL}/players",
        headers=headers,
        params={"search": nome},
        timeout=10
    )

    data = response.json()

    if not data.get("response"):
        return []

    jogadores = []

    for item in data["response"]:
        player = item.get("player", {})
        statistics = item.get("statistics", [{}])[0]

        jogadores.append({
            "nome": player.get("name"),
            "foto": player.get("photo"),
            "time": statistics.get("team", {}).get("name"),
            "api_id": player.get("id")
        })

    return jogadores[:5]



# ----------------------------------------------------------
# BUSCAR OU CRIAR JOGADOR (CACHE INTELIGENTE)
# ----------------------------------------------------------

def buscar_ou_criar_jogador(nome):

    from datetime import datetime
    from slugify import slugify

    slug = slugify(nome)

    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:

            # 1️⃣ Verifica se já existe
            cur.execute(
                "SELECT * FROM jogadores WHERE slug = %s",
                (slug,)
            )
            jogador = cur.fetchone()

            if jogador:
                return jogador

            # 2️⃣ Buscar dados na API
            dados_api = buscar_dados_jogador_api(nome)

            if dados_api:
                cur.execute("""
                    INSERT INTO jogadores (
                        nome,
                        slug,
                        foto,
                        time_atual,
                        escudo_time,
                        posicao,
                        nacionalidade,
                        data_nascimento,
                        altura,
                        ultima_sync
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    RETURNING *
                """, (
                    dados_api.get("nome"),
                    slug,
                    dados_api.get("foto"),
                    dados_api.get("time_atual"),
                    dados_api.get("escudo_time"),
                    dados_api.get("posicao"),
                    dados_api.get("nacionalidade"),
                    dados_api.get("data_nascimento"),
                    dados_api.get("altura"),
                    datetime.utcnow()
                ))

                novo = cur.fetchone()
                conn.commit()
                return novo

            # 3️⃣ Se API falhar, cria básico
            cur.execute("""
                INSERT INTO jogadores (nome, slug)
                VALUES (%s, %s)
                RETURNING *
            """, (
                nome.title(),
                slug
            ))

            novo = cur.fetchone()
            conn.commit()
            return novo

# ----------------------------------------------------------
# RELACIONAR NOTÍCIA ↔ JOGADOR
# ----------------------------------------------------------

def salvar_relacao_noticia_jogadores(noticia_id, jogador_id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO noticia_jogadores (noticia_id, jogador_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            """, (noticia_id, jogador_id))
            conn.commit()


# ----------------------------------------------------------
# LISTAR NOTÍCIAS POR JOGADOR
# ----------------------------------------------------------

def listar_noticias_por_jogador(jogador_id, limit=20):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT n.*
                FROM noticias n
                JOIN noticia_jogadores nj ON nj.noticia_id = n.id
                WHERE nj.jogador_id = %s
                AND n.editorial_status = 'publicado'
                ORDER BY n.criada_em DESC
                LIMIT %s
            """, (jogador_id, limit))

            return cur.fetchall()

def limpar_vinculos_jogadores_noticia(noticia_id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM noticia_jogadores WHERE noticia_id = %s",
                (noticia_id,)
            )
            conn.commit()

def criar_jogador_basico(nome):
    slug_jogador = slugify(nome)

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO jogadores (nome, slug)
                VALUES (%s, %s)
                RETURNING id
            """, (nome, slug_jogador))

            jogador_id = cur.fetchone()[0]
            conn.commit()

            return jogador_id

def vincular_jogador_noticia(noticia_id, jogador_id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO noticia_jogadores (noticia_id, jogador_id)
                VALUES (%s, %s)
                ON CONFLICT (noticia_id, jogador_id) DO NOTHING
            """, (noticia_id, jogador_id))

            conn.commit()

# ============================================
# JOGADORES RELACIONADOS À NOTÍCIA
# ============================================

def listar_jogadores_por_noticia(noticia_id: int):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:

            cur.execute("""
                SELECT j.id,
                       j.nome,
                       j.slug,
                       j.foto,
                       j.time_atual,
                       j.escudo_time,
                       j.data_nascimento
                FROM jogadores j
                JOIN noticia_jogadores nj ON nj.jogador_id = j.id
                WHERE nj.noticia_id = %s
            """, (noticia_id,))

            return cur.fetchall()

# ======================================================
# JOGADORES
# ======================================================

def buscar_jogador_por_slug(slug: str):
    try:
        with get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT *,
                    COALESCE(DATE_PART('year', AGE(data_nascimento)), 0) AS idade
                    FROM jogadores
                    WHERE slug = %s
                    LIMIT 1
                """, (slug,))
                return cur.fetchone()
    except Exception:
        return None


def inserir_jogador(dados: dict):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO jogadores (
                        nome,
                        slug,
                        foto,
                        time_atual,
                        escudo_time,
                        posicao,
                        nacionalidade,
                        data_nascimento,
                        altura,
                        ultima_sync
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
                    ON CONFLICT (slug) DO NOTHING
                """, (
                    dados.get("nome"),
                    dados.get("slug"),
                    dados.get("foto"),
                    dados.get("time_atual"),
                    dados.get("escudo_time"),
                    dados.get("posicao"),
                    dados.get("nacionalidade"),
                    dados.get("data_nascimento"),
                    dados.get("altura"),
                ))
            conn.commit()
    except Exception:
        pass


def atualizar_jogador(jogador_id: int, dados: dict):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE jogadores SET
                        foto = %s,
                        time_atual = %s,
                        escudo_time = %s,
                        posicao = %s,
                        nacionalidade = %s,
                        data_nascimento = %s,
                        altura = %s,
                        atualizado_em = NOW(),
                        ultima_sync = NOW()
                    WHERE id = %s
                """, (
                    dados.get("foto"),
                    dados.get("time_atual"),
                    dados.get("escudo_time"),
                    dados.get("posicao"),
                    dados.get("nacionalidade"),
                    dados.get("data_nascimento"),
                    dados.get("altura"),
                    jogador_id
                ))
            conn.commit()
    except Exception:
        pass

def buscar_dados_jogador_api(nome: str):

    import requests
    import os

    BASE_URL = "https://v3.football.api-sports.io"
    API_KEY = os.getenv("API_FOOTBALL_KEY")

    if not API_KEY:
        return None

    headers = {
        "x-apisports-key": API_KEY
    }

    url = f"{BASE_URL}/players"

    params = {
        "search": nome
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=10
        )

        data = response.json()

    except Exception:
        return None

    if not data.get("response"):
        return None

    item = data["response"][0]

    player = item.get("player", {})
    statistics = item.get("statistics", [{}])[0]

    return {
        "nome": player.get("name"),
        "foto": player.get("photo"),
        "time_atual": statistics.get("team", {}).get("name"),
        "escudo_time": statistics.get("team", {}).get("logo"),
        "posicao": statistics.get("games", {}).get("position"),
        "nacionalidade": player.get("nationality"),
        "data_nascimento": player.get("birth", {}).get("date"),
        "altura": player.get("height"),
    }

def buscar_jogadores_por_nome(query: str):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:

            cur.execute("""
                SELECT id, nome, foto, time_atual
                FROM jogadores
                WHERE nome ILIKE %s
                ORDER BY nome ASC
                LIMIT 5
            """, (f"%{query}%",))

            return cur.fetchall()

def garantir_coluna_facebook():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                ALTER TABLE noticias
                ADD COLUMN IF NOT EXISTS facebook_posted BOOLEAN DEFAULT FALSE;
            """)
        conn.commit()

def listar_para_facebook(limit=10):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, titulo_editorial, slug, imagem, categoria
                FROM noticias
                WHERE editorial_status = 'publicado'
                  AND facebook_posted = FALSE
                  AND categoria IN (
                      'Mercado da Bola',
                      'Brasileirão',
                      'Última Hora'
                  )
                ORDER BY criada_em DESC
                LIMIT %s;
            """, (limit,))
            return cur.fetchall()

def marcar_como_postado_facebook(noticia_id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE noticias
                SET facebook_posted = TRUE
                WHERE id = %s;
            """, (noticia_id,))
        conn.commit()
