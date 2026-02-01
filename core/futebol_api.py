import requests
import os

API_KEY = os.getenv("API_FOOTBALL_KEY")

HEADERS = {
    "x-apisports-key": API_KEY
}

def buscar_classificacao_brasileirao():
    url = "https://v3.football.api-sports.io/standings"

    for season in [2025, 2024, 2023]:
        params = {
            "league": 71,
            "season": season
        }

        response = requests.get(url, headers=HEADERS, params=params)
        data = response.json()

        if data.get("response"):
            standings = data["response"][0]["league"]["standings"][0]

            return [
                {
                    "posicao": time["rank"],
                    "nome": time["team"]["name"],
                    "escudo": time["team"]["logo"],
                    "jogos": time["all"]["played"],
                    "vitorias": time["all"]["win"],
                }
                for time in standings[:6]
            ]

    # fallback absoluto (não quebra a home)
    return []
