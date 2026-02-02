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

from datetime import datetime

def buscar_jogos_do_dia():
    # 🇧🇷🇪🇺 Países permitidos
    PAISES_PERMITIDOS = {
        "Brazil",
        "Portugal",
        "France",
        "Italy",
        "Germany",
        "England",
        "Spain"
    }

    # ❌ Categorias proibidas
    PALAVRAS_PROIBIDAS = [
        "u17", "u18", "u19", "u20", "u21", "u23",
        "women", "feminino",
        "youth", "reserve",
        "development", "friendly"
    ]

    # 🇧🇷 Ligas brasileiras permitidas
    LIGAS_BRASIL = [
        "serie a",
        "serie b",
        "paulista",
        "carioca",
        "mineiro",
        "gaúcho"
    ]

    def liga_valida(nome_liga, pais):
        nome = nome_liga.lower()

        for palavra in PALAVRAS_PROIBIDAS:
            if palavra in nome:
                return False

        if pais == "Brazil":
            return any(liga in nome for liga in LIGAS_BRASIL)

        return pais in PAISES_PERMITIDOS

    def fetch(params):
        r = requests.get(
            f"{BASE_URL}/fixtures",
            headers=HEADERS,
            params=params,
            timeout=10
        )
        r.raise_for_status()
        return r.json().get("response", [])

    jogos_raw = []

    # 1️⃣ Jogos ao vivo
    try:
        jogos_raw.extend(fetch({
            "live": "all",
            "timezone": "America/Sao_Paulo"
        }))
    except Exception as e:
        print("ERRO LIVE:", e)

    # 2️⃣ Jogos do dia
    if len(jogos_raw) < 6:
        try:
            jogos_raw.extend(fetch({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "timezone": "America/Sao_Paulo"
            }))
        except Exception as e:
            print("ERRO DATE:", e)

    jogos = []
    vistos = set()

    for f in jogos_raw:
        fid = f["fixture"]["id"]
        if fid in vistos:
            continue
        vistos.add(fid)

        league = f["league"]
        country = league["country"]
        league_name = league["name"]

        if not liga_valida(league_name, country):
            continue

        home = f["teams"]["home"]
        away = f["teams"]["away"]

        if not home["logo"] or not away["logo"]:
            continue

        jogos.append({
            "liga": league_name,
            "pais": country,
            "hora": f["fixture"]["date"][11:16],
            "status": f["fixture"]["status"]["short"],
            "casa": home["name"],
            "fora": away["name"],
            "casa_logo": home["logo"],
            "fora_logo": away["logo"],
            "gols_casa": f["goals"]["home"],
            "gols_fora": f["goals"]["away"],
            "link": "#"
        })

        if len(jogos) == 6:
            break

    return jogos


