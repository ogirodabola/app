import requests
import xml.etree.ElementTree as ET

from core.classificacao import classificar_noticia, gerar_slug
from crawler.utils import extrair_imagem_e_credito_por_url


RSS_URL = "https://www.lance.com.br/rss"
MAX_NOTICIAS = 20


def coletar_noticias_lance():
    print("[LANCE] Iniciando crawler do Lance via RSS (sem feedparser)")

    response = requests.get(RSS_URL, timeout=15)
    response.raise_for_status()

    root = ET.fromstring(response.content)
    noticias = []

    for item in root.findall(".//item")[:MAX_NOTICIAS]:
        try:
            titulo = item.findtext("title", "").strip()
            url = item.findtext("link", "").strip()

            if not titulo or len(titulo) < 15 or not url:
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
            print(f"[LANCE ERRO] {e}")

    print(f"[LANCE] Notícias coletadas: {len(noticias)}")
    return noticias
