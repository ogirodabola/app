# crawler/utils.py

import json

PLACEHOLDER_PADRAO = "/static/img/placeholder.png"


def extrair_imagem_artigo(soup):
    """
    Estratégia unificada de imagem:
    1) JSON-LD
    2) og:image
    3) og:image:secure_url
    4) <article> img
    5) placeholder
    """

    imagem = None

    # 1️⃣ JSON-LD
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)

            if isinstance(data, list):
                for item in data:
                    img = item.get("image") if isinstance(item, dict) else None
                    if img:
                        imagem = img[0] if isinstance(img, list) else img
                        break

            elif isinstance(data, dict):
                img = data.get("image")
                if img:
                    imagem = img[0] if isinstance(img, list) else img

        except Exception:
            continue

        if imagem:
            break

    # 2️⃣ Open Graph
    if not imagem:
        og = soup.find("meta", property="og:image")
        if og and og.get("content"):
            imagem = og["content"]

    # 3️⃣ Open Graph Secure
    if not imagem:
        ogs = soup.find("meta", property="og:image:secure_url")
        if ogs and ogs.get("content"):
            imagem = ogs["content"]

    # 4️⃣ IMG do artigo
    if not imagem:
        img = soup.select_one("article img")
        if img:
            imagem = (
                img.get("data-src")
                or img.get("data-original")
                or img.get("src")
            )

    # 5️⃣ Filtro de lixo
    if imagem:
        invalidos = ["logo", "sprite", "placeholder", "default"]
        if any(p in imagem.lower() for p in invalidos):
            imagem = None

    return imagem or PLACEHOLDER_PADRAO
