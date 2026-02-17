from core.database import atualizar_jogador, buscar_jogador_por_slug
from core.futebol_api import fetch_player_from_api

def sync_jogador(slug: str):
    jogador = buscar_jogador_por_slug(slug)
    if not jogador:
        return None

    # evita chamar API toda hora
    if jogador.get("ultima_sync"):
        ...

    dados_api = fetch_player_from_api(jogador["nome"])
    if not dados_api:
        return jogador

    return atualizar_jogador(
        jogador["id"],
        foto = dados_api.get("player", {}).get("photo"),
        time_atual = dados_api.get("team", {}).get("name"),
        ...
    )
