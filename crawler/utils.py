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
