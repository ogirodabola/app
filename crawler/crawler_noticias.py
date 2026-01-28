import os
import hashlib
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

IMAGENS_DIR = "static/img/noticias"
os.makedirs(IMAGENS_DIR, exist_ok=True)

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

def baixar_imagem(url: str) -> str | None:
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()

        ext = url.split("?")[0].split(".")[-1].lower()
        if ext not in ["jpg", "jpeg", "png", "webp"]:
            ext = "jpg"

        nome = hashlib.md5(url.encode()).hexdigest()
        caminho = f"{IMAGENS_DIR}/{nome}.{ext}"

        with open(caminho, "wb") as f:
            f.write(r.content)

        return "/" + caminho  # caminho público

    except Exception as e:
        print(f"[IMG DOWNLOAD ERRO] {e}")
        return None

def extrair_imagem_e_credito(url_noticia: str, fonte_nome: str):
    try:
        html = requests.get(url_noticia, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(html.text, "lxml")

        # 1️⃣ Open Graph
        og = soup.find("meta", property="og:image")
        if og and og.get("content"):
            imagem_url = og["content"]
        else:
            img = soup.select_one("article img")
            imagem_url = img["src"] if img else None
            imagem, imagem_credito = extrair_imagem_e_credito(url, fonte["nome"])

        if not imagem_url:
            return None, None

        # Crédito
        figcaption = soup.find("figcaption")
        if figcaption:
            credito = figcaption.get_text(strip=True)
        else:
            credito = f"Foto: {fonte_nome}"

        imagem_local = baixar_imagem(imagem_url)
        return imagem_local, credito

    except Exception as e:
        print(f"[IMG EXTRAÇÃO ERRO] {e}")
        return None, None

def limpar_titulo(titulo: str) -> str:
    """
    Remove datas, horas e ruídos comuns vindos dos portais.
    Ex: '...clube27/01/2026 22h06'
    """
    # remove datas e horas
    titulo = re.sub(r"\d{2}/\d{2}/\d{4}\s*\d{2}h\d{2}", "", titulo)

    # remove múltiplos espaços
    titulo = re.sub(r"\s{2,}", " ", titulo)

    return titulo.strip()

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

        titulo = limpar_titulo(a.get_text(strip=True))
        url = a.get("href")

        if not titulo or len(titulo) < 40:
            continue

        if not link_valido(url, dominio):
            continue

        categoria = classificar_noticia(titulo)
        slug = gerar_slug(titulo)
        resumo = titulo if len(titulo) <= 160 else titulo[:157] + "..."

        noticias.append({
            "titulo": titulo,
            "url": url,
            "fonte": fonte["nome"],
            "categoria": categoria,
            "slug": slug,
            "resumo": resumo,
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
