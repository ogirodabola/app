import re
from slugify import slugify

def auto_link_texto(texto, entidades):
    """
    entidades = [
        {"nome": "Neymar", "url": "/jogador/neymar"},
        {"nome": "Palmeiras", "url": "/time/palmeiras"}
    ]
    """

    if not texto:
        return texto

    for entidade in entidades:
        nome = entidade["nome"]
        url = entidade["url"]

        pattern = r'\b' + re.escape(nome) + r'\b'

        texto = re.sub(
            pattern,
            f'<a href="{url}" class="auto-link">{nome}</a>',
            texto,
            count=1,  # evita spam de links
            flags=re.IGNORECASE
        )

    return texto
