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
import os

API_KEY = os.getenv("API_FOOTBALL_KEY")  # use variável de ambiente
BASE_URL = "https://v3.football.api-sports.io"

HEADERS = {
    "x-apisports-key": API_KEY
}

def buscar_jogos_do_dia():
    import requests

    def fetch(params):
        r = requests.get(
            f"{BASE_URL}/fixtures",
            headers=HEADERS,
            params=params,
            timeout=10
        )
        r.raise_for_status()
        return r.json().get("response", [])

    # =========================
    # PAÍSES PERMITIDOS
    # =========================
    PAISES_BRASIL = ["Brazil"]

    PAISES_EUROPA = [
        "England", "Spain", "Italy", "Germany", "France",
        "Portugal", "Netherlands", "Belgium", "Scotland",
        "Turkey", "Greece", "Austria", "Switzerland"
    ]

    # =========================
    # PALAVRAS BLOQUEADAS
    # =========================
    BLOQUEIOS = [
        "women", "feminino", "friendly",
        "youth", "u17", "u20", "u23"
    ]

    def permitido(f):
        liga = f["league"]["name"].lower()
        pais = (f["league"]["country"] or "").lower()

        # bloqueio por palavra
        for b in BLOQUEIOS:
            if b in liga:
                return False

        # permite Brasil
        if pais in [p.lower() for p in PAISES_BRASIL]:
            return True

        # permite Europa
        if pais in [p.lower() for p in PAISES_EUROPA]:
            return True

        return False

    # =========================
    # COLETA
    # =========================
    jogos_raw = []
    jogos_raw.extend(fetch({"next": 20, "timezone": "America/Sao_Paulo"}))
    jogos_raw.extend(fetch({"last": 20, "timezone": "America/Sao_Paulo"}))

    vistos = set()
    jogos = []

    for f in jogos_raw:
        fid = f["fixture"]["id"]
        if fid in vistos:
            continue
        vistos.add(fid)

        if not permitido(f):
            continue

        home = f["teams"]["home"]
        away = f["teams"]["away"]

        if not home.get("logo") or not away.get("logo"):
            continue

        jogos.append({
            "liga": f["league"]["name"],
            "data": "Hoje",
            "hora": f["fixture"]["date"][11:16],
            "casa": home["name"],
            "fora": away["name"],
            "casa_logo": home["logo"],
            "fora_logo": away["logo"],
            "gols_casa": f["goals"]["home"],
            "gols_fora": f["goals"]["away"],
            "status": f["fixture"]["status"]["short"],
            "link": "#"
        })

        if len(jogos) == 6:
            break

    return jogos
