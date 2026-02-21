import os
import requests
from core.database import listar_para_facebook, marcar_como_postado_facebook

PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")
PAGE_ACCESS_TOKEN = os.getenv("FACEBOOK_PAGE_TOKEN")
BASE_URL = "https://girodesportivo.com"

def gerar_texto_post(titulo, categoria, slug):
    return f"""{categoria}
{titulo}

Leia completo 👇
🔗 {BASE_URL}/noticia/{slug}"""

def publicar_facebook(imagem_url, texto):
    endpoint = f"https://graph.facebook.com/v19.0/{PAGE_ID}/photos"

    payload = {
        "url": imagem_url,
        "caption": texto,
        "access_token": PAGE_ACCESS_TOKEN
    }

    response = requests.post(endpoint, data=payload)

    if response.status_code != 200:
        raise Exception(response.text)

    return response.json()

def processar():
    noticias = listar_para_facebook(limit=4)  # publica 4 por execução

    if not noticias:
        print("Nenhuma notícia para postar.")
        return

    for n in noticias:
        try:
            texto = gerar_texto_post(
                n["titulo_editorial"],
                n["categoria"],
                n["slug"]
            )

            publicar_facebook(n["imagem"], texto)

            marcar_como_postado_facebook(n["id"])

            print(f"Publicado: {n['titulo_editorial']}")

        except Exception as e:
            print(f"Erro ao publicar ID {n['id']}: {e}")

if __name__ == "__main__":
    processar()
