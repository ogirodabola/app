import requests
from bs4 import BeautifulSoup
from fontes import FONTES
from database import salvar_noticia

HEADERS = {
    "User-Agent": "Mozilla/5.0 (O Giro da Bola)"
}

def extrair_noticias_fonte(fonte):
    response = requests.get(fonte["url"], headers=HEADERS, timeout=10)
    soup = BeautifulSoup(response.text, "lxml")

    noticias = []

    for link in soup.select("a"):
        titulo = link.get_text(strip=True)
        url = link.get("href")

        if titulo and url and url.startswith("http"):
            noticias.append({
                "titulo": titulo,
                "url": url,
                "fonte": fonte["nome"]
            })

    return noticias


def rodar_crawler():
    total = 0

    for fonte in FONTES:
        try:
            noticias = extrair_noticias_fonte(fonte)
            for n in noticias:
                salvar_noticia(n)
                total += 1
        except Exception as e:
            print(f"[ERRO] {fonte['nome']}: {e}")

    print(f"[OK] {total} notícias processadas")


if __name__ == "__main__":
    rodar_crawler()
