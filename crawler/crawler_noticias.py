PLACEHOLDER_PADRAO = "/static/img/placeholder.png"

import re
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

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


# ======================================================
# LINK VÁLIDO — SUPORTA LINKS RELATIVOS (LANCE!)
# ======================================================
def link_valido(url: str, dominio: str) -> bool:
    if not url:
        return False

    url = url.lower()

    for p in PALAVRAS_PROIBIDAS:
        if p in url:
            return False

    # aceita links relativos
    if url.startswith("/"):
        return True

    if dominio not in url:
        return False

    return len(url) > 30


def limpar_titulo(titulo: str) -> str:
    titulo = re.sub(r"\d{2}/\d{2}/\d{4}\s*\d{2}h\d{2}", "", titulo)
    titulo = re.sub(r"\s{2,}", " ", titulo)
    return titulo.strip()


# ======================================================
# EXTRAÇÃO DE IMAGEM — ROBUSTA (LANCE / GE / ESPN)
# ======================================================
def extrair_imagem_e_credito(url_noticia: str, fonte_nome: str):
    try:
        r = requests.get(url_noticia, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")

        imagem_url = None
        credito = f"Foto: {fonte_nome}"

        # 1️⃣ JSON-LD (padrão Google News)
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)

                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            img = item.get("image")
                            if isinstance(img, list) and img:
                                imagem_url = img[0]
                            elif isinstance(img, str):
                                imagem_url = img
                elif isinstance(data, dict):
                    img = data.get("image")
                    if isinstance(img, list) and img:
                        imagem_url = img[0]
                    elif isinstance(img, str):
                        imagem_url = img

                if imagem_url:
                    break
            except Exception:
                continue

        # 2️⃣ Open Graph
        if not imagem_url:
            og = soup.find("meta", property="og:image")
            if og and og.get("content"):
                imagem_url = og["content"]

        if not imagem_url:
            ogs = soup.find("meta", property="og:image:secure_url")
            if ogs and ogs.get("content"):
                imagem_url = ogs["content"]

        # 3️⃣ IMG do artigo (lazy-load)
        if not imagem_url:
            img = soup.select_one("article img")
            if img:
                imagem_url = (
                    img.get("data-src")
                    or img.get("data-original")
                    or img.get("src")
                )

        # 4️⃣ Filtro de lixo editorial
        if imagem_url:
            imagem_url = imagem_url.strip()

            PADROES_INVALIDOS = [
                "default",
                "placeholder",
                "og-default",
                "logo",
                "sprite"
            ]

            if any(p in imagem_url.lower() for p in PADROES_INVALIDOS):
                imagem_url = None

        # 5️⃣ Crédito
        figcaption = soup.find("figcaption")
        if figcaption:
            texto = figcaption.get_text(strip=True)
            if len(texto) > 5:
                credito = texto

        # 6️⃣ Fallback final
        if not imagem_url:
            imagem_url = PLACEHOLDER_PADRAO
            credito = None

        return imagem_url, credito

    except Exception as e:
        print(f"[IMG ERRO] {fonte_nome}: {e}")
        return PLACEHOLDER_PADRAO, None


# ======================================================
# EXTRAÇÃO DE NOTÍCIAS POR FONTE
# ======================================================
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
        href = a.get("href")

        if not titulo or len(titulo) < 20:
            continue
        
        if fonte["nome"] == "Lance!" and "/futebol/" not in url:
            continue

        if not link_valido(href, dominio):
            continue

        # normaliza URL (links relativos do Lance)
        url = urljoin(fonte["url"], href)
        if "uol.com.br" in url:
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


# ======================================================
# EXECUÇÃO PRINCIPAL
# ======================================================
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
