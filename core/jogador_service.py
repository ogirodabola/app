from datetime import datetime, timedelta, timezone
from slugify import slugify

from core.database import (
    buscar_jogador_por_slug,
    inserir_jogador,
    atualizar_jogador
)

from core.futebol_api import buscar_jogador_api_por_nome


TTL_DIAS = 7


def jogador_completo(jogador: dict) -> bool:

    if not jogador:
        return False

    campos = [
        "foto",
        "time_atual",
        "escudo_time",
        "posicao",
        "data_nascimento"
    ]

    return all(jogador.get(c) for c in campos)


def precisa_sincronizar(jogador: dict) -> bool:

    if not jogador:
        return True

    ultima_sync = jogador.get("ultima_sync")

    if not ultima_sync:
        return True

    limite = datetime.now(timezone.utc) - timedelta(days=TTL_DIAS)

    # Se vier naive do banco
    if ultima_sync.tzinfo is None:
        ultima_sync = ultima_sync.replace(tzinfo=timezone.utc)

    return ultima_sync < limite


def buscar_ou_sincronizar_jogador(slug: str):

    jogador = buscar_jogador_por_slug(slug)

    if jogador and jogador_completo(jogador) and not precisa_sincronizar(jogador):
        return jogador

    nome = slug.replace("-", " ")

    api_data = buscar_jogador_api_por_nome(nome)

    if not api_data:
        return jogador

    dados = {
        "nome": api_data.get("nome"),
        "slug": slug,
        "foto": api_data.get("foto"),
        "time_atual": api_data.get("time_atual"),
        "escudo_time": api_data.get("escudo_time"),
        "posicao": api_data.get("posicao"),
        "nacionalidade": api_data.get("nacionalidade"),
        "data_nascimento": api_data.get("data_nascimento"),
        "altura": api_data.get("altura"),
    }

    if jogador:
        atualizar_jogador(jogador["id"], dados)
    else:
        inserir_jogador(dados)

    return buscar_jogador_por_slug(slug)
