import os
import requests
from datetime import datetime

BASE_URL = "https://v3.football.api-sports.io"

API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")
if not API_FOOTBALL_KEY:
    raise RuntimeError("API_FOOTBALL_KEY não definida no ambiente")

HEADERS = {
    "x-apisports-key": API_FOOTBALL_KEY
}


COUNTRIES_ALLOWED = {
    "Brazil", "England", "Spain", "Italy", "Germany", "France", "Portugal"
}

BRAZIL_LEAGUES = {
    "Serie A", "Serie B", "Paulista", "Carioca", "Mineiro", "Gaúcho"
}

BLACKLIST_KEYWORDS = [
    "U20", "U21", "U23", "U17",
    "Women", "Feminino",
    "Youth", "Primavera",
    "Friendly", "Friendlies",
    "Reserve"
]


def is_blacklisted(text: str) -> bool:
    return any(word.lower() in text.lower() for word in BLACKLIST_KEYWORDS)


def buscar_jogos_do_dia():
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
    jogos = []

    # =========================
    # FILTRO PRINCIPAL
    # =========================
    for f in fixtures:
        league = f["league"]["name"]
        country = f["league"]["country"]

        if is_blacklisted(league):
            continue

        if country == "Brazil":
            if not any(l in league for l in BRAZIL_LEAGUES):
                continue
        elif country not in COUNTRIES_ALLOWED:
            continue

        gols_casa = f["goals"]["home"]
        gols_fora = f["goals"]["away"]

        placar = None
        if gols_casa is not None and gols_fora is not None:
            placar = f"{gols_casa} × {gols_fora}"

        jogos.append({
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

        if len(jogos) == 6:
            break

    # =========================
    # FALLBACK (SEM FILTRO)
    # =========================
    if len(jogos) < 6:
        for f in fixtures:
            gols_casa = f["goals"]["home"]
            gols_fora = f["goals"]["away"]

            placar = None
            if gols_casa is not None and gols_fora is not None:
                placar = f"{gols_casa} × {gols_fora}"

            jogos.append({
                "liga": f["league"]["name"],
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

            if len(jogos) == 6:
                break

    return jogos

def buscar_classificacao_brasileirao():
    url = "https://v3.football.api-sports.io/standings"

    # tenta temporadas mais recentes primeiro
    for season in [2026, 2025, 2024, 2023]:
        params = {
            "league": 71,  # Brasileirão Série A
            "season": season
        }

        try:
            response = requests.get(url, headers=HEADERS, params=params, timeout=10)
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

        # retorna a tabela COMPLETA (20 times)
        return tabela

    # fallback absoluto (não quebra a home nem a classificação)
    return []
