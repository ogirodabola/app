import re
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

    return len(url) > 30


def limpar_titulo(titulo: str) -> str:
    titulo = re.sub(r"\d{2}/\d{2}/\d{4}\s*\d{2}h\d{2}", "", titulo)
    titulo = re.sub(r"\s{2,}", " ", titulo)
    return titulo.strip()


def extrair_imagem_e_credito(url_noticia: str, fonte_nome: str):
    try:
        r = requests.get(url_noticia, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")

        imagem_url = None

        # 1️⃣ Open Graph padrão
        og = soup.find("meta", property="og:image")
        if og and og.get("content"):
            imagem_url = og["content"]

        # 2️⃣ OG secure
        if not imagem_url:
            ogs = soup.find("meta", property="og:image:secure_url")
            if ogs and ogs.get("content"):
                imagem_url = ogs["content"]

        # 3️⃣ Primeira imagem do artigo
        if not imagem_url:
            img = soup.select_one("article img")
            if img and img.get("src"):
                imagem_url = img["src"]

        # Crédito
        figcaption = soup.find("figcaption")
        credito = figcaption.get_text(strip=True) if figcaption else f"Foto: {fonte_nome}"

        return imagem_url, credito

    except Exception as e:
        print(f"[IMG ERRO] {e}")
        return None, None


def extrair_noticias_fonte(fonte):
    print(f"[INFO] Coletando: {fonte['nome']}")

    response = requests.get(fonte["url"], headers=HEADERS, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")
    dominio = urlparse(fonte["url"]).netloc
    noticias = []

    for a in soup.select("a"):
        if len(noticias) >= MAX_POR_FONTE:
            break

        titulo = limpar_titulo(a.get_text(strip=True))
        url = a.get("href")

        if not titulo or len(titulo) < 40:
            continue

        if not link_valido(url, dominio):
            continue

        imagem, imagem_credito = extrair_imagem_e_credito(url, fonte["nome"])

        noticias.append({
            "titulo": titulo,
            "url": url,
            "fonte": fonte["nome"],
            "categoria": classificar_noticia(titulo),
            "slug": gerar_slug(titulo),
            "resumo": titulo[:160],
            "imagem": imagem,
            "imagem_credito": imagem_credito
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
                    slug=n["slug"],
                    imagem=n["imagem"],
                    imagem_credito=n["imagem_credito"]
                )
                total += 1

        except Exception as e:
            print(f"[ERRO] Fonte {fonte['nome']}: {e}")

    print(f"[OK] Total de notícias processadas: {total}")


if __name__ == "__main__":
    rodar_crawler()
