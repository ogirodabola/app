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

# garante banco/tabelas
criar_tabelas()


def link_valido(url, dominio):
    return (
        url.startswith("http")
        and dominio in url
        and not any(p in url.lower() for p in [
            "privacy", "ads", "cookies", "politica",
            "terms", "login", "cadastro"
        ])
    )


def extrair_noticias_fonte(fonte):
    print(f"[INFO] Coletando: {fonte['nome']}")

    response = requests.get(fonte["url"], headers=HEADERS, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")

    noticias = []
    dominio = urlparse(fonte["url"]).netloc

    # 🔥 pega apenas links com <h2> ou <h3> (padrão jornalístico)
    for a in soup.select("a:has(h2), a:has(h3)"):
        if len(noticias) >= MAX_POR_FONTE:
            break

        titulo = a.get_text(strip=True)
        url = a.get("href")

        if not titulo or len(titulo) < 30:
            continue

        if not link_valido(url, dominio):
            continue

        categoria = classificar_noticia(titulo)
        slug = gerar_slug(titulo)

        noticias.append({
            "titulo": titulo,
            "url": url,
            "fonte": fonte["nome"],
            "categoria": categoria,
            "slug": slug,
            "resumo": titulo[:140]
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
