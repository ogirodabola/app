import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

from crawler.fontes import FONTES
from core.database import criar_tabelas, salvar_noticia
from core.classificacao import classificar_noticia, gerar_slug

HEADERS = {
    "User-Agent": "O Giro da Bola"
}

MAX_POR_FONTE = 20

criar_tabelas()

PALAVRAS_PROIBIDAS = [
    "privacy", "policy", "cookies", "termos", "login",
    "cadastro", "assine", "newsletter", "sobre",
    "contato", "institucional", "legislacao"
]

def link_valido(url: str, dominio: str) -> bool:
    if not url:
        return False

    url = url.lower()

    if dominio not in url:
        return False

    for p in PALAVRAS_PROIBIDAS:
        if p in url:
            return False

    if len(url) < 30:
        return False

    return True


def extrair_noticias_fonte(fonte):
    print(f"[INFO] Coletando: {fonte['nome']}")

    response = requests.get(
        fonte["url"],
        headers=HEADERS,
        timeout=15
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")

    dominio = urlparse(fonte["url"]).netloc
    noticias = []

    for a in soup.select("a"):
        if len(noticias) >= MAX_POR_FONTE:
            break

        titulo = a.get_text(strip=True)
        url = a.get("href")

        if not titulo or len(titulo) < 40:
            continue

        if not link_valido(url, dominio):
            continue

        categoria = classificar_noticia(titulo)
        slug = gerar_slug(titulo)
        resumo = titulo[:160]

        noticias.append({
            "titulo": titulo,
            "url": url,
            "fonte": fonte["nome"],
            "categoria": categoria,
            "slug": slug,
            "resumo": resumo
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
