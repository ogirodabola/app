import requests
from bs4 import BeautifulSoup

def extrair_conteudo_noticia(url: str) -> str:
    try:
        resp = requests.get(url, timeout=15, headers={
            "User-Agent": "Mozilla/5.0"
        })
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")

        # remove lixo
        for tag in soup(["script", "style", "aside", "footer", "nav"]):
            tag.decompose()

        paragrafos = [
            p.get_text(strip=True)
            for p in soup.find_all("p")
            if len(p.get_text(strip=True)) > 40
        ]

        return "\n\n".join(paragrafos[:15])  # limite seguro
    except Exception as e:
        print(f"[ERRO] Conteúdo não extraído: {e}")
        return ""

PLACEHOLDER_PADRAO = "/static/img/placeholder.png"


def extrair_imagem_e_credito_lance(soup):
    imagem = None
    credito = None

    # Lance usa figure com img claro
    figure = soup.find("figure")
    if figure:
        img = figure.find("img")
        if img:
            imagem = (
                img.get("data-src")
                or img.get("src")
            )

        figcaption = figure.find("figcaption")
        if figcaption:
            texto = figcaption.get_text(strip=True)
            if texto:
                credito = texto

    if not imagem:
        imagem = PLACEHOLDER_PADRAO

    return imagem, credito
