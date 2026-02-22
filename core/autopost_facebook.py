import os
import requests
from core.database import listar_publicadas_nao_postadas_x, marcar_postado_x

PAGE_ID = "993344013868127"
PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_TOKEN")

BASE_URL = "https://girodesportivo.com/noticia/"

def postar_facebook(noticia):
    titulo = noticia["titulo_editorial"]
    slug = noticia["slug"]

    link = f"{BASE_URL}{slug}"

    mensagem = f"{titulo}\n\nLeia mais:\n{link}\n\nvia Giro Desportivo"

    url = f"https://graph.facebook.com/v25.0/{PAGE_ID}/feed"

    response = requests.post(
        url,
        data={
            "message": mensagem,
            "access_token": PAGE_ACCESS_TOKEN
        }
    )

    return response.json()


def rodar_autopost_facebook():
    noticias = listar_publicadas_nao_postadas_x()

    for n in noticias:
        try:
            resp = postar_facebook(n)
            print("Facebook post:", resp)
        except Exception as e:
            print("Erro Facebook:", e)


if __name__ == "__main__":
    rodar_autopost_facebook()
