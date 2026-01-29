import os
import time
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

from core.editorial import (
    classificar_editorial,
    gerar_titulo_editorial
)

DATABASE_URL = os.getenv("DATABASE_URL")

LIMITE_POR_EXECUCAO = int(os.getenv("EDITORIAL_BATCH_LIMIT", 10))
PAUSA_ENTRE_ITENS = int(os.getenv("EDITORIAL_SLEEP", 1))


# ======================================================
# CONEXÃO
# ======================================================
def get_conn():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL não definida")
    return psycopg2.connect(DATABASE_URL)


# ======================================================
# BUSCAR NOTÍCIAS PENDENTES (EDITORIAL RÁPIDO)
# ======================================================
def buscar_pendentes(conn):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT id, titulo, resumo
            FROM noticias
            WHERE editorial_status = 'pendente'
            ORDER BY criada_em ASC
            LIMIT %s
            FOR UPDATE SKIP LOCKED;
            """,
            (LIMITE_POR_EXECUCAO,)
        )
        return cur.fetchall()


# ======================================================
# SALVAR RESULTADO DO EDITORIAL RÁPIDO
# ======================================================
def salvar_editorial_rapido(
    conn,
    noticia_id,
    titulo_editorial,
    categoria,
    tags
):
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE noticias
            SET
              titulo_editorial = %s,
              categoria = %s,
              tags = %s,
              editorial_status = 'rapido'
            WHERE id = %s;
            """,
            (
                titulo_editorial,
                categoria,
                tags,
                noticia_id
            )
        )
    conn.commit()


# ======================================================
# PROCESSAMENTO PRINCIPAL
# ======================================================
def processar():
    print("⚡ Iniciando worker editorial RÁPIDO...")

    conn = get_conn()

    try:
        noticias = buscar_pendentes(conn)

        if not noticias:
            print("✅ Nenhuma notícia pendente.")
            return

        print(f"🔍 {len(noticias)} notícias para editorial rápido.\n")

        for idx, noticia in enumerate(noticias, start=1):
            noticia_id = noticia["id"]
            titulo = noticia["titulo"]
            resumo = noticia["resumo"] or ""

            print(f"➡️ [{idx}/{len(noticias)}] ID {noticia_id}")
            print(f"   Título original: {titulo}")

            try:
                categoria, tags = classificar_editorial(titulo, resumo)
                titulo_editorial = gerar_titulo_editorial(titulo)

                salvar_editorial_rapido(
                    conn,
                    noticia_id,
                    titulo_editorial=titulo_editorial,
                    categoria=categoria,
                    tags=tags
                )

                print("   ⚡ Editorial rápido concluído.\n")
                time.sleep(PAUSA_ENTRE_ITENS)

            except Exception as e:
                print(f"   ❌ Erro no ID {noticia_id}: {e}")

    finally:
        conn.close()
        print("🔒 Worker rápido encerrado.")


# ======================================================
# ENTRYPOINT
# ======================================================
if __name__ == "__main__":
    processar()
