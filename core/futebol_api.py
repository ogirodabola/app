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

def buscar_jogos_do_dia():
    import requests

    API_KEY = "SUA_API_KEY_AQUI"
    BASE_URL = "https://v3.football.api-sports.io"

    headers = {
        "x-apisports-key": API_KEY
    }

    def fetch(params):
        r = requests.get(
            f"{BASE_URL}/fixtures",
            headers=headers,
            params=params,
            timeout=10
        )
        r.raise_for_status()
        return r.json().get("response", [])

    jogos = []
    jogos.extend(fetch({"live": "all"}))
    jogos.extend(fetch({"next": 6, "timezone": "America/Sao_Paulo"}))
    jogos.extend(fetch({"last": 6, "timezone": "America/Sao_Paulo"}))

    vistos = set()
    resultado = []

    for f in jogos:
        fid = f["fixture"]["id"]
        if fid in vistos:
            continue
        vistos.add(fid)

        home_logo = f["teams"]["home"].get("logo")
        away_logo = f["teams"]["away"].get("logo")

        # LOG DE VERDADE (vai aparecer no Render)
        print("LOGOS:", home_logo, away_logo)

        if not home_logo or not away_logo:
            continue  # NÃO renderiza jogo sem escudo válido

        resultado.append({
            "liga": f["league"]["name"],
            "data": "Hoje",
            "hora": f["fixture"]["date"][11:16],
            "casa": f["teams"]["home"]["name"],
            "fora": f["teams"]["away"]["name"],
            "casa_logo": home_logo,
            "fora_logo": away_logo,
            "gols_casa": f["goals"]["home"],
            "gols_fora": f["goals"]["away"],
            "status": f["fixture"]["status"]["short"],
            "link": "#"
        })

        if len(resultado) == 6:
            break

    return resultado

