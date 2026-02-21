import os
import time
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from slugify import slugify
import re

load_dotenv()

from core.editorial import (
    gerar_conteudo_editorial,
    classificar_editorial,
    gerar_titulo_editorial
)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL não definida")

LIMITE_POR_EXECUCAO = int(os.getenv("EDITORIAL_BATCH_LIMIT", 35))
PAUSA_ENTRE_ITENS = int(os.getenv("EDITORIAL_SLEEP", 2))


# ======================================================
# CONEXÃO
# ======================================================

def get_conn():
    return psycopg2.connect(DATABASE_URL)


# ======================================================
# SLUG SEO SEGURO
# ======================================================

def gerar_slug_seo_simples(titulo: str) -> str:
    slug = slugify(titulo)
    slug = re.sub(r"-+", "-", slug)
    return slug[:80]


def slug_existe(conn, slug: str) -> bool:
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM noticias WHERE slug = %s LIMIT 1;", (slug,))
        return cur.fetchone() is not None


def gerar_slug_unico(conn, titulo: str) -> str:
    base_slug = gerar_slug_seo_simples(titulo)
    slug = base_slug

    for contador in range(1, 20):
        if not slug_existe(conn, slug):
            return slug
        slug = f"{base_slug}-{contador}"

    return f"{base_slug}-{int(time.time())}"


# ======================================================
# BUSCAR PENDENTES
# ======================================================

def buscar_pendentes_balanceado(conn):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT id, titulo, resumo, conteudo_original
            FROM noticias
            WHERE conteudo_editorial IS NULL
            ORDER BY criada_em ASC
            LIMIT %s;
        """, (LIMITE_POR_EXECUCAO,))
        return cur.fetchall()


# ======================================================
# MARCAR ERRO
# ======================================================

def marcar_erro(conn, noticia_id):
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE noticias
            SET editorial_status = 'erro_conteudo'
            WHERE id = %s;
        """, (noticia_id,))
    conn.commit()


def normalizar_titulo(titulo):
    return re.sub(r'\W+', '', titulo.lower())


def noticia_similar_existe(conn, titulo):
    titulo_norm = normalizar_titulo(titulo)

    with conn.cursor() as cur:
        cur.execute("""
            SELECT titulo
            FROM noticias
            WHERE editorial_status = 'publicado'
            ORDER BY criada_em DESC
            LIMIT 50;
        """)
        titulos = cur.fetchall()

    for (t,) in titulos:
        if normalizar_titulo(t)[:40] in titulo_norm:
            return True

    return False


# ======================================================
# EXTRAÇÃO E VÍNCULO AUTOMÁTICO DE JOGADORES
# ======================================================

def vincular_jogadores_automaticamente(conn, noticia_id, tags, conteudo_original):
    from core.database import buscar_ou_criar_jogador, vincular_jogador_noticia

    candidatos = set()

    # 1️⃣ Tags geradas pela IA
    for tag in tags or []:
        if len(tag) >= 4:
            candidatos.add(tag.title())

    # 2️⃣ Extração simples do conteúdo original
    if conteudo_original:
        encontrados = re.findall(
            r"\b[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+(?:\s[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+)?\b",
            conteudo_original
        )
        for nome in encontrados:
            if len(nome) > 4:
                candidatos.add(nome)

    bloqueados = {
        "Brasileirão",
        "Libertadores",
        "Flamengo",
        "Palmeiras",
        "Corinthians",
        "Vasco",
        "São Paulo",
        "Santos",
        "Grêmio",
        "Internacional",
    }

    for nome in candidatos:
        if nome in bloqueados:
            continue

        try:
            jogador = buscar_ou_criar_jogador(nome)
            if jogador:
                vincular_jogador_noticia(noticia_id, jogador["id"])
        except Exception as e:
            print(f"Erro ao vincular jogador {nome}: {e}")


# ======================================================
# SALVAR EDITORIAL
# ======================================================

def salvar_editorial(
    conn,
    noticia_id,
    titulo_editorial,
    conteudo_editorial,
    categoria,
    tags
):
    if not conteudo_editorial or len(conteudo_editorial) < 150:
        print("   ⚠️ Conteúdo muito curto. Marcado como erro.")
        marcar_erro(conn, noticia_id)
        return False

    slug = gerar_slug_unico(conn, titulo_editorial)

    with conn.cursor() as cur:
        cur.execute("""
            UPDATE noticias
            SET
              titulo_editorial = %s,
              conteudo_editorial = %s,
              categoria = %s,
              tags = %s,
              slug = %s,
              editorial_status = 'publicado'
            WHERE id = %s;
        """, (
            titulo_editorial,
            conteudo_editorial,
            categoria,
            tags,
            slug,
            noticia_id
        ))

    conn.commit()
    return True


# ======================================================
# PROCESSAMENTO PRINCIPAL
# ======================================================

def processar():
    print("🧠 Iniciando worker editorial...")

    conn = get_conn()

    try:
        noticias = buscar_pendentes_balanceado(conn)

        if not noticias:
            print("✅ Nenhuma notícia pendente.")
            return

        print(f"🔍 {len(noticias)} notícias pendentes encontradas.\n")

        for idx, noticia in enumerate(noticias, start=1):

            noticia_id = noticia["id"]
            titulo = noticia["titulo"]
            resumo = noticia["resumo"] or ""

            print(f"➡️ [{idx}/{len(noticias)}] ID {noticia_id}")

            try:
                categoria, tags = classificar_editorial(titulo, resumo)
                titulo_editorial = gerar_titulo_editorial(titulo)

                if noticia_similar_existe(conn, titulo_editorial):
                    print("   ⚠️ Notícia similar já publicada. Ignorando.")
                    marcar_erro(conn, noticia_id)
                    continue

                conteudo = gerar_conteudo_editorial(
                    titulo=titulo_editorial,
                    resumo=resumo,
                    categoria=categoria,
                    conteudo_original=noticia.get("conteudo_original")
                )

                publicado = salvar_editorial(
                    conn,
                    noticia_id,
                    titulo_editorial,
                    conteudo,
                    categoria,
                    tags
                )

                # 🔥 VINCULAR JOGADORES APENAS SE PUBLICOU
                if publicado:
                    vincular_jogadores_automaticamente(
                        conn,
                        noticia_id,
                        tags,
                        noticia.get("conteudo_original")
                    )

                print("   ✅ Publicado.\n")
                time.sleep(PAUSA_ENTRE_ITENS)

            except Exception as e:
                print(f"   ❌ Erro no ID {noticia_id}: {e}")
                marcar_erro(conn, noticia_id)

    finally:
        conn.close()
        print("🔒 Worker encerrado.")


if __name__ == "__main__":
    processar()
