"""
Teste de contrato do core.database

Objetivo:
- Garantir que todas as funções usadas pelo main.py
  existem fisicamente no core.database
- Falhar o CI antes do deploy se o contrato for quebrado
"""

import importlib


def test_database_public_contract():
    database = importlib.import_module("core.database")

    required_functions = [
        "criar_tabelas",
        "listar_ultima_hora",
        "listar_por_categoria",
        "listar_categorias",
        "buscar_noticia_por_slug",
        "salvar_noticia",
        "atualizar_editorial",
        "listar_pendentes_editorial",
    ]

    missing = [
        fn for fn in required_functions
        if not hasattr(database, fn)
    ]

    assert not missing, (
        "Funções obrigatórias ausentes em core.database: "
        + ", ".join(missing)
    )
