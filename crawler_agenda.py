import requests
import sqlite3
import datetime
from slugify import slugify

DB_PATH = "girodabola.db"

API_KEY = "a485887708409f6abbab585db0dd87c8"
API_URL = "https://v3.football.api-sports.io/fixtures"

HEADERS = {
    "x-apisports-key": API_KEY
}


def gerar_slug(mandante, visitante, data):
    return slugify(f"{mandante} x {visitante} {data}")


def processar_agenda():
    hoje = datetime.date.today().isoformat()

    params = {
        "date": hoje,
        "timezone": "America/Sao_Paulo"
    }

    r = requests.get(API_URL, headers=HEADERS, params=params, timeout=20)

    if r.status_code != 200:
        print("❌ Falha API-Football")
        return

    dados = r.json().get("response", [])

    if not dados:
        print("⚠️ Nenhum jogo encontrado")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    salvos = 0

    for jogo in dados:
        mandante = jogo["teams"]["home"]["name"]
        visitante = jogo["teams"]["away"]["name"]
        campeonato = jogo["league"]["name"]
        horario = jogo["fixture"]["date"][11:16]
        estadio = jogo["fixture"]["venue"]["name"]
        cidade = jogo["fixture"]["venue"]["city"]

        slug = gerar_slug(mandante, visitante, hoje)

        cursor.execute("""
            INSERT OR IGNORE INTO jogos
            (data, horario, mandante, visitante, campeonato, estadio, cidade, slug)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            hoje, horario, mandante, visitante,
            campeonato, estadio, cidade, slug
        ))

        if cursor.rowcount:
            salvos += 1

    conn.commit()
    conn.close()

    print(f"✅ {salvos} jogos salvos")
