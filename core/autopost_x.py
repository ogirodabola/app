import os
import requests
import tweepy
from core.database import (
    listar_publicadas_nao_postadas_x,
    marcar_postado_x
)

X_API_KEY = os.getenv("X_API_KEY")
X_API_SECRET = os.getenv("X_API_SECRET")
X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
X_ACCESS_SECRET = os.getenv("X_ACCESS_SECRET")

auth = tweepy.OAuth1UserHandler(
    X_API_KEY,
    X_API_SECRET,
    X_ACCESS_TOKEN,
    X_ACCESS_SECRET
)

api = tweepy.API(auth)

BASE_URL = "https://girodesportivo.com/noticia/"


def postar_noticia(noticia):
    titulo = noticia["titulo_editorial"]
    slug = noticia["slug"]
    imagem_url = noticia["imagem"]

    link = f"{BASE_URL}{slug}"

    texto = f"{titulo}\n\n{link}\n\nvia @ogirodesportivo"

    # baixa imagem
    img_data = requests.get(imagem_url).content
    with open("temp.jpg", "wb") as f:
        f.write(img_data)

    media = api.media_upload("temp.jpg")
    api.update_status(status=texto, media_ids=[media.media_id])


def rodar_autopost():
    noticias = listar_publicadas_nao_postadas_x()

    for n in noticias:
        try:
            postar_noticia(n)
            marcar_postado_x(n["id"])
            print(f"Postado: {n['slug']}")
        except Exception as e:
            print("Erro ao postar:", e)
