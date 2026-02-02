import requests
import os

API_KEY = os.getenv("API_FOOTBALL_KEY")

HEADERS = {
    "x-apisports-key": API_KEY
}

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
import requests
from datetime import date

import requests

API_KEY = "SUA_API_KEY_AQUI"
BASE_URL = "https://v3.football.api-sports.io"

headers = {
    "x-apisports-key": API_KEY
}


def _parse_fixture(f):
    return {
        "liga": f["league"]["name"],
        "data": "Hoje",
        "hora": f["fixture"]["date"][11:16],
        "casa": f["teams"]["home"]["name"],
        "fora": f["teams"]["away"]["name"],
        "casa_logo": f["teams"]["home"]["logo"],
        "fora_logo": f["teams"]["away"]["logo"],
        "gols_casa": f["goals"]["home"],
        "gols_fora": f["goals"]["away"],
        "status": f["fixture"]["status"]["short"],  # FT, NS, LIVE
        "link": "#"
    }


def buscar_jogos_do_dia():
    # 1️⃣ AO VIVO
    r = requests.get(
        f"{BASE_URL}/fixtures",
        headers=headers,
        params={"live": "all"}
    )
    data = r.json().get("response", [])
    if data:
        return [_parse_fixture(f) for f in data[:6]]

    # 2️⃣ PRÓXIMOS JOGOS
    r = requests.get(
        f"{BASE_URL}/fixtures",
        headers=headers,
        params={"next": 6, "timezone": "America/Sao_Paulo"}
    )
    data = r.json().get("response", [])
    if data:
        return [_parse_fixture(f) for f in data]

    # 3️⃣ ÚLTIMOS JOGOS
    r = requests.get(
        f"{BASE_URL}/fixtures",
        headers=headers,
        params={"last": 6, "timezone": "America/Sao_Paulo"}
    )
    data = r.json().get("response", [])
    return [_parse_fixture(f) for f in data]

