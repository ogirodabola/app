import requests
import feedparser

from core.classificacao import classificar_noticia, gerar_slug
from crawler.utils import extrair_imagem_e_credito_por_url


RSS_URL = "https://www.lance.com.br/rss"
MAX_NOTICIAS = 20


def coletar_noticias_lance():
    print("[LANCE] Iniciando crawler do Lance via RSS")

    feed = feedparser.parse(RSS_URL)
    noticias = []

    for entry in feed.entries[:MAX_NOTICIAS]:
        try:
            titulo = entry.title.strip()
            url = entry.link.strip()

            if len(titulo) < 15:
                continue

            imagem, credito = extrair_imagem_e_credito_por_url(
                url, fonte_nome="Lance!"
            )

            noticias.append({
                "titulo": titulo,
                "url": url,
                "fonte": "Lance!",
                "categoria": classificar_noticia(titulo),
                "slug": gerar_slug(titulo),
                "resumo": titulo[:160],
                "imagem": imagem,
                "imagem_credito": credito
            })

        except Exception as e:
            print(f"[LANCE ERRO] {entry.link}: {e}")

    print(f"[LANCE] Notícias coletadas: {len(noticias)}")
    return noticias
