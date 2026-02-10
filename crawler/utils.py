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

import requests
from bs4 import BeautifulSoup
import json

PLACEHOLDER_PADRAO = "/static/img/placeholder.png"

def extrair_imagem_e_credito_por_url(url, fonte_nome):
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")

        imagem = None
        credito = None

        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    img = data.get("image")
                    if isinstance(img, list):
                        imagem = img[0]
                    elif isinstance(img, str):
                        imagem = img
                if imagem:
                    break
            except Exception:
                pass

        if not imagem:
            imagem = PLACEHOLDER_PADRAO

        return imagem, credito

    except Exception:
        return PLACEHOLDER_PADRAO, None
