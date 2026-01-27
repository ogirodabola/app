import re
from unidecode import unidecode

# =========================
# CATEGORIAS / COMPETIÇÕES
# =========================

COMPETICOES = {
    "Campeonato Brasileiro Série A": [
        "brasileirão", "serie a", "série a"
    ],
    "Campeonato Brasileiro Série B": [
        "serie b", "série b"
    ],
    "Copa do Brasil": [
        "copa do brasil"
    ],
    "Libertadores da América": [
        "libertadores"
    ],
    "Copa Sul-Americana": [
        "sul-americana"
    ],
    "Champions League": [
        "champions", "liga dos campeões"
    ],
    "Liga Europa": [
        "liga europa"
    ],
    "Premier League": [
        "premier league", "campeonato inglês"
    ],
    "La Liga": [
        "la liga", "campeonato espanhol"
    ],
    "Serie A Italiana": [
        "campeonato italiano", "serie a italiana"
    ],
    "Bundesliga": [
        "bundesliga", "campeonato alemão"
    ],
    "Campeonato Português": [
        "campeonato português"
    ],
    "Copa do Mundo": [
        "copa do mundo"
    ],
    "Copa América": [
        "copa america"
    ],
    "Amistosos de Seleções": [
        "amistoso", "seleção"
    ]
}

CATEGORIA_PAI = {
    "Campeonato Brasileiro Série A": "Futebol Brasileiro",
    "Campeonato Brasileiro Série B": "Futebol Brasileiro",
    "Copa do Brasil": "Futebol Brasileiro",

    "Libertadores da América": "Futebol Sul-Americano",
    "Copa Sul-Americana": "Futebol Sul-Americano",

    "Champions League": "Futebol Europeu",
    "Liga Europa": "Futebol Europeu",
    "Premier League": "Futebol Europeu",
    "La Liga": "Futebol Europeu",
    "Serie A Italiana": "Futebol Europeu",
    "Bundesliga": "Futebol Europeu",
    "Campeonato Português": "Futebol Europeu",

    "Copa do Mundo": "Seleções",
    "Copa América": "Seleções",
    "Amistosos de Seleções": "Seleções"
}

# =========================
# TAGS (TIMES + CONTEXTO)
# =========================

TIMES = [
    "flamengo", "palmeiras", "corinthians", "são paulo",
    "vasco", "botafogo", "grêmio", "internacional",
    "real madrid", "barcelona", "manchester city",
    "liverpool", "arsenal", "psg", "bayern",
    "juventus", "milan", "inter"
]


def gerar_slug(texto: str) -> str:
    texto = unidecode(texto.lower())
    texto = re.sub(r"[^a-z0-9]+", "-", texto)
    return texto.strip("-")


def classificar_noticia(texto: str) -> str:
    texto = texto.lower()

    if "brasileirão" in texto:
        return "Campeonato Brasileiro"
    if "libertadores" in texto:
        return "Libertadores"
    if "sul-americana" in texto:
        return "Sul-Americana"
    if "champions" in texto:
        return "Champions League"
    if "copa do mundo" in texto:
        return "Copa do Mundo"
    if "copa américa" in texto:
        return "Copa América"

    return "Futebol"

def extrair_tags(titulo: str):
    tags = []
    titulo_norm = unidecode(titulo.lower())

    for time in TIMES:
        if time in titulo_norm:
            tags.append(time.title())

    if "lesão" in titulo_norm:
        tags.append("Lesão")

    if "contrata" in titulo_norm or "reforço" in titulo_norm:
        tags.append("Mercado da Bola")

    if "final" in titulo_norm:
        tags.append("Final")

    return tags
