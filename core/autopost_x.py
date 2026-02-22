import os
import tweepy
import requests
from core.database import listar_publicadas_nao_postadas_x, marcar_postado_x

BASE_URL = "https://girodesportivo.com/noticia/"

client = tweepy.Client(
    consumer_key=os.getenv("X_API_KEY"),
    consumer_secret=os.getenv("X_API_SECRET"),
    access_token=os.getenv("X_ACCESS_TOKEN"),
    access_token_secret=os.getenv("X_ACCESS_SECRET"),
)

# upload de mídia ainda usa v1.1
auth = tweepy.OAuth1UserHandler(
    os.getenv("X_API_KEY"),
    os.getenv("X_API_SECRET"),
    os.getenv("X_ACCESS_TOKEN"),
    os.getenv("X_ACCESS_SECRET"),
)

api_v1 = tweepy.API(auth)

def postar_noticia(noticia):
    titulo = noticia["titulo_editorial"]
    slug = noticia["slug"]
    imagem_url = noticia["imagem"]

    link = f"{BASE_URL}{slug}"

    texto = f"{titulo}\n\n{link}\n\nvia @ogirodesportivo"

    # baixar imagem
    img_data = requests.get(imagem_url).content
    with open("temp.jpg", "wb") as f:
        f.write(img_data)

    media = api_v1.media_upload("temp.jpg")

    response = client.create_tweet(
        text=texto,
        media_ids=[media.media_id]
    )

    return response


def rodar_autopost():
    noticias = listar_publicadas_nao_postadas_x()

    for n in noticias:
        try:
            postar_noticia(n)
            marcar_postado_x(n["id"])
            print(f"Postado: {n['slug']}")
        except Exception as e:
            print("Erro:", e)


if __name__ == "__main__":
    rodar_autopost()
