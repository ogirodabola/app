import requests
import os

API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")

BASE_URL = "https://v3.football.api-sports.io"

HEADERS = {
    "x-apisports-key": API_FOOTBALL_KEY
}


def buscar_classificacao_brasileirao():
    url = f"{BASE_URL}/standings"

    params = {
        "league": 71,     # Brasileirão Série A
        "season": 2025    # ⚠️ USE 2025 por enquanto
    }

    response = requests.get(url, headers=HEADERS, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()

    # 🔒 PROTEÇÃO ABSOLUTA
    if not data.get("response"):
        print("⚠️ API-Football: resposta vazia para standings")
        return []

    league = data["response"][0].get("league")
    if not league or not league.get("standings"):
        print("⚠️ API-Football: standings não encontrados")
        return []

    tabela = league["standings"][0]

    resultado = []

    for time in tabela[:6]:
        resultado.append({
            "posicao": time.get("rank"),
            "nome": time["team"].get("name"),
            "escudo": time["team"].get("logo"),
            "jogos": time["all"].get("played"),
            "vitorias": time["all"].get("win")
        })

    return resultado
    print("API-Football resposta:", data)
