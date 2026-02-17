from core.database import (
    buscar_jogador_por_slug,
    inserir_jogador,
    atualizar_jogador
)
from core.futebol_api import api_football_client


def buscar_ou_sincronizar_jogador(slug: str):

    jogador = buscar_jogador_por_slug(slug)

    # Se já existe e já tem foto/time, retorna
    if jogador and jogador.get("foto"):
        return jogador

    # Se não tem ou está incompleto → busca na API
    nome = slug.replace("-", " ")

    try:
        response = api_football_client.players_search(nome=nome)
    except Exception:
        return jogador

    if not response.get("response"):
        return jogador

    data = response["response"][0]

    # Monta dicionário
    dados = {
        "nome": data["player"]["name"],
        "slug": slug,
        "foto": data["player"]["photo"],
        "posicao": data["statistics"][0]["games"]["position"],
        "time_atual": data["statistics"][0]["team"]["name"],
        "escudo_time": data["statistics"][0]["team"]["logo"],
        "data_nascimento": data["player"]["birth"]["date"],
        "altura": data["player"]["height"],
    }

    if jogador:
        atualizar_jogador(jogador["id"], dados)
    else:
        inserir_jogador(dados)

    return buscar_jogador_por_slug(slug)
