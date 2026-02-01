import requests
import os

API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")

BASE_URL = "https://v3.football.api-sports.io"

HEADERS = {
    "x-apisports-key": API_FOOTBALL_KEY
}


def buscar_classificacao_brasileirao():
    """
    Retorna TOP 6 do Brasileirão
    """
    url = f"{BASE_URL}/standings"

    params = {
        "league": 71,      # Brasileirão Série A
        "season": 2026
    }

    response = requests.get(url, headers=HEADERS, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()

    tabela = data["response"][0]["league"]["standings"][0]

    resultado = []

    for time in tabela[:6]:
        resultado.append({
            "posicao": time["rank"],
            "nome": time["team"]["name"],
            "escudo": time["team"]["logo"],
            "jogos": time["all"]["played"],
            "vitorias": time["all"]["win"]
        })

    return resultado
