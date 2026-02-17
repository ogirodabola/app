import os
import requests
from datetime import datetime
from core.cache import get_cache, set_cache

BASE_URL = "https://v3.football.api-sports.io"

API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")
if not API_FOOTBALL_KEY:
    raise RuntimeError("API_FOOTBALL_KEY não definida no ambiente")

HEADERS = {
    "x-apisports-key": API_FOOTBALL_KEY
}

# =========================
# FILTROS EDITORIAIS
# =========================

TIMES_BRASILEIROS = {
    # =========================
    # CAMPEONATO PAULISTA (A1)
    # =========================
    "Botafogo-SP",
    "Capivariano",
    "Corinthians",
    "Guarani",
    "Mirassol",
    "Noroeste",
    "Novorizontino",
    "Palmeiras",
    "Ponte Preta",
    "Portuguesa",
    "Primavera",
    "Red Bull Bragantino",
    "RB Bragantino",
    "Santos",
    "São Bernardo",
    "São Paulo",
    "Velo Clube",

    # =========================
    # CAMPEONATO CARIOCA
    # =========================
    "Bangu",
    "Boavista-RJ",
    "Boavista",
    "Botafogo",
    "Flamengo",
    "Fluminense",
    "Madureira",
    "Maricá",
    "Nova Iguaçu",
    "Portuguesa-RJ",
    "Portuguesa",
    "Sampaio Corrêa-RJ",
    "Sampaio Corrêa",
    "Vasco da Gama",
    "Vasco",
    "Volta Redonda",

    # =========================
    # CAMPEONATO MINEIRO
    # =========================
    "América-MG",
    "América Mineiro",
    "Athletic Club",
    "Atlético Mineiro",
    "Atlético-MG",
    "Betim Futebol",
    "Cruzeiro",
    "Democrata GV",
    "Itabirito FC",
    "North EC",
    "Pouso Alegre FC",
    "Tombense FC",
    "Uberlândia EC",
    "URT",

    # =========================
    # CAMPEONATO GAÚCHO
    # =========================
    "Avenida",
    "Caxias",
    "Grêmio",
    "Guarany Bagé",
    "Internacional",
    "Inter",
    "Inter-SM",
    "Juventude",
    "Monsoon FC",
    "Novo Hamburgo",
    "São José-RS",
    "São José",
    "São Luiz",
    "Ypiranga-RS",
}


PRIORIDADE_COMPETICOES = [
    "Serie A",
    "Paulista",
    "Carioca",
    "Mineiro",
    "Gaúcho",
    "CONMEBOL Libertadores",
    "CONMEBOL Sudamericana",
]

BLACKLIST_KEYWORDS = [
    "U20", "U21", "U23", "U17",
    "Women", "Feminino",
    "Youth", "Primavera",
    "Friendly", "Friendlies",
    "Reserve"
]

def is_blacklisted(text: str) -> bool:
    if not text:
        return False

    return any(
        word.lower() in text.lower()
        for word in BLACKLIST_KEYWORDS
    )

# ======================================================
# JOGADOR – BUSCA COMPLETA NA API
# ======================================================

def buscar_jogador_api_por_nome(nome: str):
    url = f"{BASE_URL}/players"

    params = {
        "search": nome
    }

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            params=params,
            timeout=10
        )

        if response.status_code != 200:
            return None

        data = response.json()

        if not data.get("response"):
            return None

        # Escolhe jogador mais relevante (primeiro retorno)
        jogador = data["response"][0]

        player = jogador.get("player", {})
        statistics = jogador.get("statistics", [])

        stats = statistics[0] if statistics else {}

        birth = player.get("birth", {})
        team = stats.get("team", {})
        games = stats.get("games", {})

        return {
            "nome": player.get("name"),
            "foto": player.get("photo"),
            "posicao": games.get("position"),
            "time_atual": team.get("name"),
            "escudo_time": team.get("logo"),
            "nacionalidade": player.get("nationality"),
            "data_nascimento": birth.get("date"),
            "altura": player.get("height"),
        }

    except Exception:
        return None



def normalizar_nome(nome: str) -> str:
    return (
        nome.lower()
        .replace("á", "a")
        .replace("ã", "a")
        .replace("â", "a")
        .replace("é", "e")
        .replace("ê", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ô", "o")
        .replace("ú", "u")
        .replace("-", "")
        .strip()
    )

def tem_time_brasileiro(fixture) -> bool:
    home = fixture.get("teams", {}).get("home", {}).get("name", "")
    away = fixture.get("teams", {}).get("away", {}).get("name", "")

    home_norm = normalizar_nome(home)
    away_norm = normalizar_nome(away)

    for time in TIMES_BRASILEIROS:
        t_norm = normalizar_nome(time)
        if home_norm == t_norm or away_norm == t_norm:
            return True

    return False



def peso_competicao(league_name: str) -> int:
    for idx, nome in enumerate(PRIORIDADE_COMPETICOES):
        if nome.lower() in league_name.lower():
            return idx
    return 99

from datetime import timedelta


def buscar_fixtures_por_data(data_str: str):
    params = {
        "date": data_str,
        "timezone": "America/Sao_Paulo"
    }

    r = requests.get(
        f"{BASE_URL}/fixtures",
        headers=HEADERS,
        params=params,
        timeout=10
    )
    r.raise_for_status()

    return r.json().get("response", [])


# =========================
# JOGOS DO DIA (EDITORIAL)
# =========================

def buscar_jogos_do_dia():
    cache_key = "jogos_do_dia"

    cached = get_cache(cache_key)
    if cached is not None:
        return cached

    jogos_priorizados = []
    datas_consultadas = []

    # hoje + próximos 2 dias
    for offset in range(0, 3):
        data = datetime.now() + timedelta(days=offset)
        data_str = data.strftime("%Y-%m-%d")
        datas_consultadas.append(data_str)

        fixtures = buscar_fixtures_por_data(data_str)

        for f in fixtures:
            league = f.get("league", {}).get("name", "")
            country = f.get("league", {}).get("country", "")

            if not league or is_blacklisted(league):
                continue

            # competições nacionais
            if country == "Brazil":
                peso = peso_competicao(league)
                if peso == 99:
                    continue

            # libertadores / sula
            elif "CONMEBOL" in league:
                if not tem_time_brasileiro(f):
                    continue
                peso = peso_competicao(league)

            else:
                continue

            gols_casa = f.get("goals", {}).get("home")
            gols_fora = f.get("goals", {}).get("away")

            placar = None
            if gols_casa is not None and gols_fora is not None:
                placar = f"{gols_casa} × {gols_fora}"

            jogos_priorizados.append({
                "peso": peso,
                "liga": league,
                "data": data.strftime("%d/%m"),
                "hora": f.get("fixture", {}).get("date", "")[11:16],
                "casa": f.get("teams", {}).get("home", {}).get("name", ""),
                "fora": f.get("teams", {}).get("away", {}).get("name", ""),
                "casa_logo": f.get("teams", {}).get("home", {}).get("logo", ""),
                "fora_logo": f.get("teams", {}).get("away", {}).get("logo", ""),
                "placar": placar,
                "status": f.get("fixture", {}).get("status", {}).get("short", ""),
                "link": "#"
            })

        # já dá pra parar?
        if len(jogos_priorizados) >= 6:
            break

    # ordena por prioridade editorial
    jogos_priorizados.sort(key=lambda x: x["peso"])

    jogos = jogos_priorizados[:6]

    # cache maior porque envolve datas futuras
    set_cache(cache_key, jogos, ttl=900)  # 15 min

    return jogos

# =========================
# CLASSIFICAÇÃO BRASILEIRÃO
# =========================

def buscar_classificacao_brasileirao():
    url = "https://v3.football.api-sports.io/standings"

    for season in [2026, 2025, 2024, 2023]:
        params = {
            "league": 71,  # Brasileirão Série A
            "season": season
        }

        try:
            response = requests.get(
                url,
                headers=HEADERS,
                params=params,
                timeout=10
            )
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
                "posicao": time.get("rank"),
                "nome": time.get("team", {}).get("name"),
                "escudo": time.get("team", {}).get("logo"),
                "pontos": time.get("points"),
                "jogos": time.get("all", {}).get("played"),
                "vitorias": time.get("all", {}).get("win"),
                "saldo_gols": time.get("goalsDiff"),
                "gols_pro": time.get("all", {}).get("goals", {}).get("for"),
                "gols_contra": time.get("all", {}).get("goals", {}).get("against"),
            })

        return tabela

    return []

import requests
import logging

def buscar_artilharia_brasileirao():
    BASE_URL = "https://v3.football.api-sports.io"
    HEADERS = {
        "x-apisports-key": os.getenv("API_FOOTBALL_KEY")
    }

    url = f"{BASE_URL}/players/topscorers"

    # Tenta temporadas recentes primeiro
    for season in [2026, 2025, 2024, 2023]:

        params = {
            "league": 71,  # Brasileirão Série A
            "season": season
        }

        try:
            response = requests.get(
                url,
                headers=HEADERS,
                params=params,
                timeout=10
            )

            # Se API devolver erro HTTP, pula temporada
            if response.status_code != 200:
                logging.warning(f"API status {response.status_code} temporada {season}")
                continue

            data = response.json()

        except Exception as e:
            logging.error(f"Erro ao buscar artilharia {season}: {e}")
            continue

        # Se não vier resposta válida, tenta próxima temporada
        if not data.get("response"):
            continue

        artilheiros = []

        for item in data["response"]:

            player = item.get("player", {})
            statistics = item.get("statistics", [{}])[0]

            artilheiros.append({
            "nome": player.get("name"),
            "foto": player.get("photo"),
            "time": statistics.get("team", {}).get("name"),
            "escudo": statistics.get("team", {}).get("logo"),
            "gols": statistics.get("goals", {}).get("total"),
            "jogos": statistics.get("games", {}).get("appearences"),
        })


        # Ordena por gols desc
        artilheiros.sort(key=lambda x: x["gols"], reverse=True)

        return artilheiros

    # Se nenhuma temporada retornar dados
    return []

def fetch_player_from_api(nome: str):
    BASE_URL = "https://v3.football.api-sports.io"
    HEADERS = {
        "x-apisports-key": os.getenv("API_FOOTBALL_KEY")
    }

    try:
        response = requests.get(
            f"{BASE_URL}/players?search={nome}",
            headers=HEADERS,
            timeout=10
        )

        if response.status_code != 200:
            return None

        data = response.json()

        if not data.get("response"):
            return None

        return data["response"][0]

    except Exception as e:
        logging.error(f"Erro ao buscar jogador {nome}: {e}")
        return None
