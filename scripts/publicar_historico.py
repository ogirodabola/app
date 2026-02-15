import os
import psycopg2
from dotenv import load_dotenv
from slugify import slugify
import re

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DATABASE_URL)

def gerar_slug_simples(titulo):
    slug = slugify(titulo)
    slug = re.sub(r"-+", "-", slug)
    return slug[:80]

def slug_existe(conn, slug):
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM noticias WHERE slug = %s LIMIT 1;", (slug,))
        return cur.fetchone() is not None

def gerar_slug_unico(conn, titulo):
    base = gerar_slug_simples(titulo)
    slug = base
    contador = 1

    while slug_existe(conn, slug):
        slug = f"{base}-{contador}"
        contador += 1

    return slug

def publicar_historico():
    conn = get_conn()

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, titulo_editorial
                FROM noticias
                WHERE conteudo_editorial IS NOT NULL
                AND editorial_status <> 'publicado';
            """)

            noticias = cur.fetchall()

        print(f"{len(noticias)} notícias para publicar...")

        for noticia_id, titulo_editorial in noticias:
            slug = gerar_slug_unico(conn, titulo_editorial)

            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE noticias
                    SET slug = %s,
                        editorial_status = 'publicado'
                    WHERE id = %s;
                """, (slug, noticia_id))

            conn.commit()

        print("✔ Histórico publicado com sucesso.")

    finally:
        conn.close()


if __name__ == "__main__":
    publicar_historico()
