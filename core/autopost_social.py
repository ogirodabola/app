import os
import requests
import tweepy
import unicodedata
from core.database import listar_publicadas_nao_postadas_x, marcar_postado_x

BASE_URL = "https://girodesportivo.com/noticia/"
PAGE_ID = "993344013868127"
FB_TOKEN = os.getenv("FB_PAGE_TOKEN")

# =========================
# CLIENTE X (v2)
# =========================

client_x = tweepy.Client(
    consumer_key=os.getenv("X_API_KEY"),
    consumer_secret=os.getenv("X_API_SECRET"),
    access_token=os.getenv("X_ACCESS_TOKEN"),
    access_token_secret=os.getenv("X_ACCESS_SECRET"),
)

auth = tweepy.OAuth1UserHandler(
    os.getenv("X_API_KEY"),
    os.getenv("X_API_SECRET"),
    os.getenv("X_ACCESS_TOKEN"),
    os.getenv("X_ACCESS_SECRET"),
)

api_v1 = tweepy.API(auth)


# =========================
# HELPERS
# =========================

def normalizar_hashtag(texto):
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    texto = texto.replace(" ", "")
    return f"#{texto}"


def gerar_hashtags(noticia):
    hashtags = []

    if noticia.get("categoria"):
        hashtags.append(normalizar_hashtag(noticia["categoria"]))

    if noticia.get("tags"):
        for tag in noticia["tags"][:2]:
            hashtags.append(normalizar_hashtag(tag))

    return " ".join(hashtags[:3])


# =========================
# POST X
# =========================

def postar_x(noticia):
    titulo = noticia["titulo_editorial"]
    slug = noticia["slug"]
    imagem = noticia["imagem"]

    link = f"{BASE_URL}{slug}"
    hashtags = gerar_hashtags(noticia)

    texto = f"{titulo}\n\n🔗 {link}\n\n{hashtags}\n\nvia @ogirodesportivo"

    img_data = requests.get(imagem).content
    with open("temp.jpg", "wb") as f:
        f.write(img_data)

    media = api_v1.media_upload("temp.jpg")

    client_x.create_tweet(
        text=texto,
        media_ids=[media.media_id]
    )


# =========================
# POST FACEBOOK
# =========================

def postar_facebook(noticia):
    titulo = noticia["titulo_editorial"]
    slug = noticia["slug"]
    hashtags = gerar_hashtags(noticia)

    link = f"{BASE_URL}{slug}"

    mensagem = f"{titulo}\n\nLeia mais:\n{link}\n\n{hashtags}"

    url = f"https://graph.facebook.com/v25.0/{PAGE_ID}/feed"

    requests.post(
        url,
        data={
            "message": mensagem,
            "access_token": FB_TOKEN
        }
    )


# =========================
# RUNNER
# =========================

def rodar_autopost_social():
    noticias = listar_publicadas_nao_postadas_x(limit=3)

    for n in noticias:
        try:
            postar_x(n)
            postar_facebook(n)
            marcar_postado_x(n["id"])
            print(f"Publicado social: {n['slug']}")
        except Exception as e:
            print("Erro social:", e)


if __name__ == "__main__":
    rodar_autopost_social()
