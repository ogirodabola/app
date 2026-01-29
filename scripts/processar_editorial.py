import os
import time
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

from core.editorial import (
    gerar_conteudo_editorial,
    classificar_editorial,
    gerar_titulo_editorial
)

DATABASE_URL = os.getenv("DATABASE_URL")

LIMITE_POR_EXECUCAO = int(os.getenv("EDITORIAL_BATCH_LIMIT", 10))
PAUSA_ENTRE_ITENS = int(os.getenv("EDITORIAL_SLEEP", 2))


# ======================================================
# CONEXÃO
# ======================================================
def get_conn():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL não definida")
    return psycopg2.connect(DATABASE_URL)


# ======================================================
# BUSCAR NOTÍCIAS PENDENTES
# ======================================================
def buscar_pendentes(conn):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT id, titulo, resumo
            FROM noticias
            WHERE editorial_status = 'rapido'
            ORDER BY criada_em ASC
            LIMIT %s
            FOR UPDATE SKIP LOCKED;
            """,
            (LIMITE_POR_EXECUCAO,)
        )
        return cur.fetchall()


# ======================================================
# ATUALIZAR STATUS
# ======================================================
def atualizar_status(conn, noticia_id, status):
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE noticias
            SET editorial_status = %s
            WHERE id = %s;
            """,
            (status, noticia_id)
        )
    conn.commit()


# ======================================================
# SALVAR RESULTADO EDITORIAL
# ======================================================
def salvar_editorial(
    conn,
    noticia_id,
    conteudo_editorial
):
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE noticias
            SET
              conteudo_editorial = %s,
              editorial_status = 'pronto'
            WHERE id = %s;
            """,
            (
                conteudo_editorial,
                noticia_id
            )
        )
    conn.commit()


# ======================================================
# PROCESSAMENTO PRINCIPAL
# ======================================================
def processar():
    print("🧠 Iniciando worker editorial...")

    conn = get_conn()

    try:
        noticias = buscar_pendentes(conn)

        if not noticias:
            print("✅ Nenhuma notícia pendente.")
            return

        print(f"🔍 {len(noticias)} notícias pendentes encontradas.\n")

        for idx, noticia in enumerate(noticias, start=1):
            noticia_id = noticia["id"]
            titulo = noticia["titulo"]
            resumo = noticia["resumo"] or ""

            print(f"➡️ [{idx}/{len(noticias)}] ID {noticia_id}")
            print(f"   Título original: {titulo}")

            try:
                atualizar_status(conn, noticia_id, "processando")

                # Classificação + tags
                categoria, tags = classificar_editorial(titulo, resumo)

                # Título editorial (rápido)
                titulo_editorial = gerar_titulo_editorial(titulo)

                # Conteúdo editorial
                conteudo = gerar_conteudo_editorial(
                    titulo=titulo,
                    resumo=resumo,
                    categoria=categoria
                )

                salvar_editorial(
                    conn,
                    noticia_id,
                    titulo_editorial=titulo_editorial,
                    conteudo_editorial=conteudo,
                    categoria=categoria,
                    tags=tags
                )

                print("   ✅ Editorial pronto.\n")
                time.sleep(PAUSA_ENTRE_ITENS)

            except Exception as e:
                print(f"   ❌ Erro no ID {noticia_id}: {e}")
                atualizar_status(conn, noticia_id, "erro")

    finally:
        conn.close()
        print("🔒 Worker encerrado.")


# ======================================================
# ENTRYPOINT
# ======================================================
if __name__ == "__main__":
    processar()
