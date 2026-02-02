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
    from datetime import datetime

    BASE_URL = "https://v3.football.api-sports.io"
    HEADERS = {
        "x-apisports-key": API_FOOTBALL_KEY
    }

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

    # ❌ Palavras proibidas (categorias lixo)
    PALAVRAS_PROIBIDAS = [
        "U17", "U18", "U19", "U20", "U21", "U23",
        "Women", "Feminino",
        "Youth", "Reserve",
        "Development",
        "Friendly"
    ]

    # ✅ Ligas brasileiras permitidas
    LIGAS_BRASIL = [
        "Serie A",
        "Serie B",
        "Paulista",
        "Carioca",
        "Mineiro",
        "Gaúcho"
    ]

    def liga_valida(league_name, country):
        nome = league_name.lower()

        # bloqueios diretos
        for palavra in PALAVRAS_PROIBIDAS:
            if palavra.lower() in nome:
                return False

        if country == "Brazil":
            return any(l.lower() in nome for l in LIGAS_BRASIL)

        return country in PAISES_PERMITIDOS

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

    # 1️⃣ PRIORIDADE: jogos ao vivo
    try:
        jogos_raw.extend(fetch({
            "live": "all",
            "timezone": "America/Sao_Paulo"
        }))
    except Exception as e:
        print("ERRO LIVE:", e)

    # 2️⃣ Se não tiver 6, buscar jogos do dia
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

