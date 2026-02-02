import os
import requests

API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://v3.football.api-sports.io"

if not API_KEY:
    raise RuntimeError("API_FOOTBALL_KEY não definida no ambiente")

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
import os

API_KEY = os.getenv("API_FOOTBALL_KEY")  # use variável de ambiente
BASE_URL = "https://v3.football.api-sports.io"

HEADERS = {
    "x-apisports-key": API_KEY
}

from datetime import datetime, timedelta

def buscar_jogos_do_dia():
    url = "https://v3.football.api-sports.io/fixtures"

    headers = {
        "x-apisports-key": os.getenv("API_FOOTBALL_KEY")
    }

    params = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "timezone": "America/Sao_Paulo"
    }

    r = requests.get(url, headers=headers, params=params, timeout=10)
    r.raise_for_status()

    data = r.json().get("response", [])

    jogos = []

    for f in data:
        jogos.append({
            "liga": f["league"]["name"],
            "data": "Hoje",
            "hora": f["fixture"]["date"][11:16],
            "casa": f["teams"]["home"]["name"],
            "fora": f["teams"]["away"]["name"],
            "casa_logo": f["teams"]["home"]["logo"],
            "fora_logo": f["teams"]["away"]["logo"],
            "gols_casa": f["goals"]["home"],
            "gols_fora": f["goals"]["away"],
            "status": f["fixture"]["status"]["short"],
            "link": "#"
        })

        if len(jogos) == 6:
            break

    return jogos

