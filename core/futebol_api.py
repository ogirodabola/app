import os
import requests
from datetime import datetime
from core.cache import get_cache, set_cache

BASE_URL = "https://v3.football.api-sports.io"

API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")
if not API_FOOTBALL_KEY:
    raise RuntimeError("API_FOOTBALL_KEY não definida no ambiente")

HEADERS = {
    "x-apisports-key": API_FOOTBALL_KEY
}

# =========================
# FILTROS EDITORIAIS
# =========================

TIMES_BRASILEIROS = {
    "Flamengo", "Palmeiras", "São Paulo", "Corinthians", "Santos",
    "Grêmio", "Internacional", "Atlético Mineiro", "Cruzeiro",
    "Botafogo", "Fluminense", "Vasco",
    "Athletico Paranaense", "Atlético Goianiense",
    "Bahia", "Fortaleza", "Ceará", "Sport", "Vitória",
    "Coritiba", "Goiás", "Bragantino"
}


PRIORIDADE_COMPETICOES = [
    "Serie A",
    "Paulista",
    "Carioca",
    "Mineiro",
    "Gaúcho",
    "CONMEBOL Libertadores",
    "CONMEBOL Sudamericana",
]

BLACKLIST_KEYWORDS = [
    "U20", "U21", "U23", "U17",
    "Women", "Feminino",
    "Youth", "Primavera",
    "Friendly", "Friendlies",
    "Reserve"
]


def is_blacklisted(text: str) -> bool:
    return any(word.lower() in text.lower() for word in BLACKLIST_KEYWORDS)


def tem_time_brasileiro(fixture) -> bool:
    home = fixture["teams"]["home"]["name"]
    away = fixture["teams"]["away"]["name"]

    return home in TIMES_BRASILEIROS or away in TIMES_BRASILEIROS


def peso_competicao(league_name: str) -> int:
    for idx, nome in enumerate(PRIORIDADE_COMPETICOES):
        if nome.lower() in league_name.lower():
            return idx
    return 99


# =========================
# JOGOS DO DIA (EDITORIAL)
# =========================

def buscar_jogos_do_dia():
    cache_key = "jogos_do_dia"

    cached = get_cache(cache_key)
    if cached is not None:
        return cached

    params = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "timezone": "America/Sao_Paulo"
    }

    r = requests.get(
        f"{BASE_URL}/fixtures",
        headers=HEADERS,
        params=params,
        timeout=10
    )
    r.raise_for_status()

    fixtures = r.json().get("response", [])
    jogos_priorizados = []

    for f in fixtures:
        league = f["league"]["name"]
        country = f["league"]["country"]

        # remove lixo editorial
        if is_blacklisted(league):
            continue

        # competições nacionais
        if country == "Brazil":
            peso = peso_competicao(league)
            if peso == 99:
                continue

        # libertadores / sula só com brasileiro
        elif "CONMEBOL" in league:
            if not tem_time_brasileiro(f):
                continue
            peso = peso_competicao(league)

        else:
            continue

        gols_casa = f["goals"]["home"]
        gols_fora = f["goals"]["away"]

        placar = None
        if gols_casa is not None and gols_fora is not None:
            placar = f"{gols_casa} × {gols_fora}"

        jogos_priorizados.append({
            "peso": peso,
            "liga": league,
            "data": "Hoje",
            "hora": f["fixture"]["date"][11:16],
            "casa": f["teams"]["home"]["name"],
            "fora": f["teams"]["away"]["name"],
            "casa_logo": f["teams"]["home"]["logo"],
            "fora_logo": f["teams"]["away"]["logo"],
            "placar": placar,
            "status": f["fixture"]["status"]["short"],
            "link": "#"
        })

    # ordena por prioridade editorial
    jogos_priorizados.sort(key=lambda x: x["peso"])

    # limita a 6 jogos
    jogos = jogos_priorizados[:6]

    # cache por 10 minutos
    set_cache(cache_key, jogos, ttl=600)

    return jogos
def buscar_classificacao_brasileirao():
    url = "https://v3.football.api-sports.io/standings"

    for season in [2026, 2025, 2024, 2023]:
        params = {
            "league": 71,  # Brasileirão Série A
            "season": season
        }

        try:
            response = requests.get(
                url,
                headers=HEADERS,
                params=params,
                timeout=10
            )
            data = response.json()
        except Exception:
            continue

        if not data.get("response"):
            continue

        try:
            standings = data["response"][0]["league"]["standings"][0]
        except (IndexError, KeyError, TypeError):
            continue

        tabela = []

        for time in standings:
            tabela.append({
                "posicao": time["rank"],
                "nome": time["team"]["name"],
                "escudo": time["team"]["logo"],
                "pontos": time["points"],
                "jogos": time["all"]["played"],
                "vitorias": time["all"]["win"],
                "saldo_gols": time["goalsDiff"],
                "gols_pro": time["all"]["goals"]["for"],
                "gols_contra": time["all"]["goals"]["against"],
            })

        return tabela

    return []
