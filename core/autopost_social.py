import os
import requests
import tweepy
import unicodedata
import random

from core.database import listar_publicadas_nao_postadas_x, marcar_postado_x

BASE_URL = "https://girodesportivo.com/noticia/"
SITE_URL = "https://girodesportivo.com"
PAGE_ID = "993344013868127"
FB_TOKEN = os.getenv("FB_PAGE_TOKEN")

# =========================
# CLIENTE X
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
    texto = texto.replace("-", "")
    return f"#{texto}"


def gerar_hashtags(noticia):
    tags = []

    if noticia.get("categoria"):
        tags.append(normalizar_hashtag(noticia["categoria"]))

    if noticia.get("tags"):
        if isinstance(noticia["tags"], list):
            for tag in noticia["tags"][:2]:
                tags.append(normalizar_hashtag(tag))

    return " ".join(tags[:3])


# =========================
# POST X (COM IMAGEM)
# =========================

def postar_x(noticia):
    titulo = (noticia.get("titulo_editorial") or "").strip()[:140]
    slug = noticia.get("slug")
    imagem = noticia.get("imagem")

    if not slug:
        return

    link = f"{BASE_URL}{slug}"
    hashtags = gerar_hashtags(noticia)

    variacao = random.choice(["", " 🔥", " ⚽", " 📢"])
    texto = f"{titulo}{variacao}\n\n{hashtags}\n\n{link}"

    if len(texto) > 270:
        texto = texto[:270]

    # Corrigir imagem relativa
    if imagem and imagem.startswith("/"):
        imagem = SITE_URL + imagem

    try:
        if imagem:
            response_img = requests.get(imagem, timeout=10)

            if "image" in response_img.headers.get("Content-Type", ""):
                with open("temp.jpg", "wb") as f:
                    f.write(response_img.content)

                media = api_v1.media_upload("temp.jpg")

                client_x.create_tweet(
                    text=texto,
                    media_ids=[media.media_id]
                )
                print(f"Post X OK (com imagem): {slug}")
                return

        # fallback sem imagem
        client_x.create_tweet(text=texto)
        print(f"Post X OK (sem imagem): {slug}")

    except Exception as e:
        print("Erro X:", e)


# =========================
# POST FACEBOOK (COM IMAGEM)
# =========================

def postar_facebook(noticia):
    titulo = noticia.get("titulo_editorial")
    slug = noticia.get("slug")
    hashtags = gerar_hashtags(noticia)

    link = f"{BASE_URL}{slug}"

    mensagem = f"{titulo}\n\n{hashtags}"

    url = f"https://graph.facebook.com/v25.0/{PAGE_ID}/feed"

    response = requests.post(
        url,
        data={
            "message": mensagem,
            "link": link,  # ISSO GERA PREVIEW COM IMAGEM
            "access_token": FB_TOKEN
        }
    )

    if response.status_code != 200:
        raise Exception(f"Facebook erro: {response.text}")

    print(f"Post Facebook OK: {slug}")


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
