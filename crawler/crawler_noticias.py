import requests
from bs4 import BeautifulSoup

from crawler.fontes import FONTES
from core.database import criar_tabelas, salvar_noticia
from core.classificacao import classificar_noticia, gerar_slug

# =========================================
# GARANTE BANCO + TABELAS (CRON SAFE)
# =========================================
criar_tabelas()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (O Giro da Bola)"
}

MAX_POR_FONTE = 30


def extrair_noticias_fonte(fonte):
    print(f"[INFO] Coletando: {fonte['nome']}")

    response = requests.get(
        fonte["url"],
        headers=HEADERS,
        timeout=15
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")
    links = soup.find_all("a", href=True)

    noticias = []

    for link in links:
        if len(noticias) >= MAX_POR_FONTE:
            break

        titulo = link.get_text(strip=True)
        url = link["href"]

        # filtros mínimos
        if not titulo or len(titulo) < 15:
            continue

        if not url.startswith("http"):
            continue

        categoria = classificar_noticia(titulo)
        slug = gerar_slug(titulo)

        # ✅ RESUMO OBRIGATÓRIO (regra final)
        resumo = titulo[:180]

        noticias.append({
            "titulo": titulo,
            "resumo": resumo,
            "url": url,
            "fonte": fonte["nome"],
            "categoria": categoria,
            "slug": slug
        })

    return noticias


def rodar_crawler():
    total = 0

    for fonte in FONTES:
        try:
            noticias = extrair_noticias_fonte(fonte)

            for n in noticias:
                salvar_noticia(
                    titulo=n["titulo"],
                    resumo=n["resumo"],
                    url=n["url"],
                    fonte=n["fonte"],
                    categoria=n["categoria"],
                    slug=n["slug"]
                )
                total += 1

        except Exception as e:
            print(f"[ERRO] Fonte {fonte['nome']}: {e}")

    print(f"[OK] Total de notícias processadas: {total}")


if __name__ == "__main__":
    rodar_crawler()
