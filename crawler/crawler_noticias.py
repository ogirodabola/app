import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import json
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
        credito = f"Foto: {fonte_nome}"

        # ======================================================
        # 1️⃣ JSON-LD (UOL, GE, ESPN — padrão Google News)
        # ======================================================
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)

                # Alguns sites retornam lista
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

        # ======================================================
        # 2️⃣ Open Graph
        # ======================================================
        if not imagem_url:
            og = soup.find("meta", property="og:image")
            if og and og.get("content"):
                imagem_url = og["content"]

        if not imagem_url:
            ogs = soup.find("meta", property="og:image:secure_url")
            if ogs and ogs.get("content"):
                imagem_url = ogs["content"]

        # ======================================================
        # 3️⃣ IMG do artigo (lazy-load)
        # ======================================================
        if not imagem_url:
            img = soup.select_one("article img")
            if img:
                imagem_url = (
                    img.get("data-src")
                    or img.get("data-original")
                    or img.get("src")
                )

        # ======================================================
        # 4️⃣ FILTRO — imagens genéricas / lixo editorial
        # ======================================================
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

        # ======================================================
        # 5️⃣ CRÉDITO (quando existir)
        # ======================================================
        figcaption = soup.find("figcaption")
        if figcaption:
            texto = figcaption.get_text(strip=True)
            if len(texto) > 5:
                credito = texto

        return imagem_url, credito

    except Exception as e:
        print(f"[IMG ERRO] {fonte_nome}: {e}")
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
