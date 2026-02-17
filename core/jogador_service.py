from core.database import (
    buscar_jogador_por_slug,
    inserir_jogador,
    atualizar_jogador
)

from core.futebol_api import buscar_jogador_api_por_nome


def buscar_ou_sincronizar_jogador(slug: str):

    # 1️⃣ Busca no banco primeiro
    jogador = buscar_jogador_por_slug(slug)

    # Se já existe e tem dados completos → retorna
    if jogador and jogador.get("foto"):
        return jogador

    # 2️⃣ Se não existe ou está incompleto → buscar na API
    nome = slug.replace("-", " ")

    api_data = buscar_jogador_api_por_nome(nome)

    if not api_data:
        return jogador  # Retorna o que tiver no banco (ou None)

    # Estrutura defensiva (evita quebrar se vier campo faltando)
    player = api_data.get("player", {})
    statistics = api_data.get("statistics", [{}])
    stats = statistics[0] if statistics else {}

    birth = player.get("birth", {})

    dados = {
        "nome": player.get("name"),
        "slug": slug,
        "foto": player.get("photo"),
        "posicao": stats.get("games", {}).get("position"),
        "time_atual": stats.get("team", {}).get("name"),
        "escudo_time": stats.get("team", {}).get("logo"),
        "data_nascimento": birth.get("date"),
        "altura": player.get("height"),
    }

    # 3️⃣ Atualiza ou insere
    if jogador:
        atualizar_jogador(jogador["id"], dados)
    else:
        inserir_jogador(dados)

    # 4️⃣ Retorna versão atualizada do banco
    return buscar_jogador_por_slug(slug)
