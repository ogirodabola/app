# core/editorial.py
import os
import json
from typing import Optional, List, Tuple
from openai import OpenAI
import unicodedata
import re

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = "gpt-4.1-mini"
USE_MOCK = False

_client: Optional[OpenAI] = None
if OPENAI_API_KEY:
    _client = OpenAI(api_key=OPENAI_API_KEY)

CATEGORIAS_VALIDAS = [
    "Última Hora",
    "Brasileirão",
    "Mercado da Bola",
    "Onde Assistir",
    "Análises",
    "Bastidores",
    "Agenda"
]

# ======================================================
# CLASSIFICAÇÃO + TAGS
# ======================================================
def classificar_editorial(titulo: str, resumo: str) -> Tuple[str, List[str]]:
    if USE_MOCK or not _client:
        return "Última Hora", ["Futebol"]

    prompt = f"""
Você é o editor-chefe de um portal de notícias esportivas focado em futebol.

Sua tarefa é classificar a notícia abaixo.

REGRAS OBRIGATÓRIAS:
- Escolha EXATAMENTE UMA categoria da lista abaixo
- NUNCA invente novas categorias
- Se a notícia tratar de contratações, negociações, renovações ou transferências:
  escolha "Mercado da Bola"
- Se tratar de jogo, resultado, rodada ou tabela do campeonato brasileiro:
  escolha "Brasileirão"
- Se for análise tática, técnica ou opinião aprofundada:
  escolha "Análises"
- Se for bastidor, clima interno, polêmica ou comportamento:
  escolha "Bastidores"
- Se houver dúvida real:
  escolha "Última Hora"

CATEGORIAS PERMITIDAS:
{", ".join(CATEGORIAS_VALIDAS)}

RETORNE APENAS JSON NO FORMATO:
{{
  "categoria": "Categoria escolhida",
  "tags": ["tag1", "tag2", "tag3"]
}}

TÍTULO:
{titulo}

RESUMO:
{resumo}
"""
    resp = _client.responses.create(
        model=MODEL_NAME,
        input=prompt,
        max_output_tokens=200,
    )

    try:
        data = json.loads(resp.output_text)
        categoria = data.get("categoria", "Última Hora")
        tags_raw = data.get("tags", [])
        tags = []

        for tag in tags_raw:
            t = normalizar_tag(tag)
            if t and t not in tags:
                tags.append(t)
        
        tags = tags[:8]


        if categoria not in CATEGORIAS_VALIDAS:
            categoria = "Última Hora"

        return categoria, tags[:6]

    except Exception as e:
        print("[EDITORIAL CLASSIFICAÇÃO ERRO]", e)
        return "Última Hora", ["Futebol"]


# ======================================================
# CONTEÚDO EDITORIAL
# ======================================================
def gerar_conteudo_editorial(titulo: str, resumo: str, categoria: str) -> str:
    if USE_MOCK or not _client:
        return f"<p>{resumo}</p>"

    prompt = f"""
Você é o editorial do portal O Giro da Bola.

Reescreva a notícia com:
- Linguagem jornalística popular
- SEO-friendly
- Lead + desenvolvimento + fechamento
- HTML puro usando apenas <p> e <h2>

Título: {titulo}
Resumo: {resumo}
Categoria: {categoria}
"""

    resp = _client.responses.create(
        model=MODEL_NAME,
        input=prompt,
        max_output_tokens=900,
    )

    texto = resp.output_text.strip()
    texto = texto.replace("```html", "").replace("```", "").strip()

    if len(texto) < 200:
        raise ValueError("Conteúdo editorial muito curto")

    return texto


# ======================================================
# FUNÇÃO DE COMPATIBILIDADE (NÃO REMOVER)
# ======================================================
def gerar_tags_editoriais(titulo: str, resumo: str, categoria: str) -> List[str]:
    _, tags = classificar_editorial(titulo, resumo)
    return tags

def normalizar_tag(tag: str) -> str:
    tag = unicodedata.normalize("NFKD", tag).encode("ascii", "ignore").decode("ascii")
    tag = tag.lower()
    tag = re.sub(r"[^a-z0-9]", "", tag)
    return tag

def gerar_titulo_editorial(titulo: str) -> str:
    if USE_MOCK or not _client:
        return titulo

    prompt = f"""
Reescreva o título abaixo para um portal esportivo brasileiro.

Regras:
- Curto
- Claro
- Jornalístico
- Sem clickbait exagerado
- Máx. 90 caracteres

Retorne APENAS o texto do título.

Título original:
{titulo}
"""

    resp = _client.responses.create(
        model=MODEL_NAME,
        input=prompt,
        max_output_tokens=50,
    )

    texto = resp.output_text.strip().replace('"', "")
    return texto or titulo
