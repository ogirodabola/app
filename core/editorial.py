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
Você é o editor-chefe de um grande portal esportivo brasileiro.

Sua tarefa é classificar a notícia com precisão editorial.

REGRAS OBRIGATÓRIAS:

1) Escolha EXATAMENTE UMA categoria da lista permitida.
2) Nunca invente novas categorias.
3) A decisão deve seguir hierarquia estratégica:

PRIORIDADE DE CLASSIFICAÇÃO:

- Se envolver contratação, transferência, sondagem, renovação ou mercado:
  -> "Mercado da Bola"

- Se envolver jogo, rodada, tabela, desempenho ou posição no campeonato brasileiro:
  -> "Brasileirão"

- Se for análise técnica, avaliação tática ou opinião estruturada:
  -> "Análises"

- Se tratar de bastidores, clima interno, polêmica ou comportamento:
  -> "Bastidores"

- Se for internacional e não envolver Brasileirão:
  -> "Internacional"

- Se nenhuma regra for claramente atendida:
  -> "Última Hora"

IMPORTANTE:
- Não classifique como "Última Hora" se existir categoria mais específica.
- Evite usar categoria genérica quando houver específica.

CATEGORIAS PERMITIDAS:
{", ".join(CATEGORIAS_VALIDAS)}

TAGS:
- Gere entre 3 e 6 tags relevantes.
- Use nomes próprios quando possível (clubes, jogadores, técnicos).
- Não repita palavras da categoria.
- Não use tags genéricas como "futebol".

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
Você é editor-chefe de um portal esportivo profissional brasileiro.

A matéria trata de um confronto de futebol.

LEIA atentamente o conteúdo original.
Extraia apenas informações reais presentes no texto.
NÃO invente dados.

REGRAS OBRIGATÓRIAS:

- Use apenas HTML válido
- Use SOMENTE <p> e <h2>
- Nunca use Markdown
- Nunca use negrito
- Nunca use listas
- Sempre comece com um <p> (lead direto e informativo)
- Estruture entre 5 e 8 blocos
- Produza entre 600 e 900 palavras
- SEO otimizado
- Nunca inclua o título dentro do conteúdo
- Não invente horário, transmissão ou escalações
- Se o texto não mencionar canal específico, não invente
- Se não houver nomes de jogadores, não invente escalação

ESTRUTURA OBRIGATÓRIA:

<p>Lead forte resumindo o confronto e sua importância</p>

<h2>Onde será o jogo</h2>
<p>Informar estádio e contexto</p>

<h2>Horário da partida</h2>
<p>Informar data e horário confirmados</p>

<h2>Onde assistir</h2>
<p>Informar transmissão apenas se citada</p>

<h2>Prováveis escalações</h2>
<p>Somente se houver informação concreta no texto</p>

<h2>Momento das equipes</h2>
<p>Análise baseada exclusivamente no conteúdo original</p>

TÍTULO:
{titulo}

CATEGORIA:
{categoria}

CONTEÚDO ORIGINAL:
{conteudo_original}
"""

    resp = _client.responses.create(
        model=MODEL_NAME,
        input=prompt,
        max_output_tokens=1200,
    )

    texto = resp.output_text.strip()

    # limpeza defensiva
    texto = texto.replace("```html", "").replace("```", "")
    texto = re.sub(r"^##\s*(.*)", r"<h2>\1</h2>", texto, flags=re.MULTILINE)
    texto = re.sub(r"^###\s*(.*)", r"<h2>\1</h2>", texto, flags=re.MULTILINE)

    texto = texto.strip()

    if len(texto) < 400:
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
Você é editor de títulos de um grande portal esportivo brasileiro.

Reescreva o título abaixo seguindo padrão profissional de portal.

REGRAS OBRIGATÓRIAS:

- Máximo 90 caracteres
- Linguagem jornalística objetiva
- Priorize clareza e impacto informativo
- Inclua nome de clube ou jogador se relevante
- Inclua competição quando aplicável (Brasileirão, Libertadores, etc.)
- Evite termos vagos como "veja", "confira", "surpreende"
- Não use emojis
- Não use clickbait exagerado
- Não invente informações

ESTRATÉGIA:
- Se for Mercado → destaque negociação ou valor
- Se for jogo → destaque resultado + consequência
- Se for bastidor → destaque fato central
- Se for internacional → inclua país ou competição

Retorne APENAS o título final.

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

def gerar_slug_seo(titulo: str) -> str:
    if USE_MOCK or not _client:
        from slugify import slugify
        return slugify(titulo)

    prompt = f"""
Reescreva o título abaixo em formato de slug SEO.

Regras:
- Apenas minúsculas
- Separado por hífen
- Sem palavras desnecessárias
- Máximo 8 palavras
- Não use números aleatórios

Título:
{titulo}

Retorne APENAS o slug.
"""

    resp = _client.responses.create(
        model=MODEL_NAME,
        input=prompt,
        max_output_tokens=50,
    )

    slug = resp.output_text.strip().replace(" ", "-")
    slug = re.sub(r"[^a-z0-9-]", "", slug.lower())

    return slug

def gerar_guia_transmissao(dados_partida: dict) -> str:
        return ""

def gerar_editorial_com_extracao(titulo, resumo, conteudo_original, categoria):
    prompt = f"..."
    
    resp = _client.responses.create(
        model=MODEL_NAME,
        input=prompt,
        max_output_tokens=1400,
    )

    texto = resp.output_text.strip()
    return texto

def gerar_editorial_com_extracao(
    titulo: str,
    resumo: str,
    conteudo_original: str,
    categoria: str
) -> str:
    
    prompt = f"""
    ...
    CONTEÚDO ORIGINAL:
    {conteudo_original}
    """

    resp = _client.responses.create(
        model=MODEL_NAME,
        input=prompt,
        max_output_tokens=1400,
    )

    return resp.output_text.strip()
