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
    # PRIORIDADE EDITORIAL
    # =========================
    PRIORIDADE_LIGAS = [
        "Brazil",                    # Brasil (geral)
        "Brasileirao",
        "Copa do Brasil",
        "UEFA Champions League",
        "UEFA Europa League",
        "Premier League",
        "La Liga",
        "Serie A",
        "Bundesliga",
        "Ligue 1",
    ]

    def score_prioridade(fixture):
        liga = fixture["league"]["name"]
        pais = fixture["league"]["country"]

        texto = f"{pais} {liga}".lower()

        for idx, nome in enumerate(PRIORIDADE_LIGAS):
            if nome.lower() in texto:
                return idx
        return 999  # joga ligas irrelevantes para o fim

    # =========================
    # COLETA DOS JOGOS
    # =========================
    jogos_raw = []

    # 1️⃣ Próximos jogos
    try:
        jogos_raw.extend(fetch({
            "next": 10,
            "timezone": "America/Sao_Paulo"
        }))
    except Exception as e:
        print("ERRO NEXT:", e)

    # 2️⃣ Últimos jogos (fallback)
    try:
        jogos_raw.extend(fetch({
            "last": 10,
            "timezone": "America/Sao_Paulo"
        }))
    except Exception as e:
        print("ERRO LAST:", e)

    # =========================
    # LIMPEZA + ORDENAÇÃO
    # =========================
    vistos = set()
    jogos_filtrados = []

    for f in jogos_raw:
        fid = f["fixture"]["id"]
        if fid in vistos:
            continue
        vistos.add(fid)

        home = f["teams"]["home"]
        away = f["teams"]["away"]

        # garante escudos válidos
        if not home.get("logo") or not away.get("logo"):
            continue

        jogos_filtrados.append(f)

    # ordena por prioridade editorial
    jogos_filtrados.sort(key=score_prioridade)

    # =========================
    # NORMALIZAÇÃO FINAL
    # =========================
    jogos = []

    for f in jogos_filtrados[:6]:
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

    return jogos

