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

def classificar_editorial(
    titulo: str,
    resumo: str,
    conteudo_original: str | None = None
) -> Tuple[str, List[str]]:

    texto_base = f"{titulo} {resumo} {conteudo_original or ''}".lower()

    # ======================================================
    # BLOQUEIO INTERNACIONAL (PRIORIDADE MÁXIMA)
    # ======================================================

    if any(p in texto_base for p in [
        "premier league",
        "tottenham",
        "liverpool",
        "manchester",
        "arsenal",
        "chelsea",
        "la liga",
        "real madrid",
        "barcelona",
        "bundesliga",
        "bayern",
        "ligue 1",
        "psg",
        "serie a italiana",
        "juventus",
        "inter de milao",
        "milan"
    ]):
        return "Última Hora", ["futebol_internacional"]

    # ======================================================
    # FORÇA BRASILEIRÃO APENAS SE FOR BRASIL
    # ======================================================

    if any(p in texto_base for p in [
        "brasileirão",
        "campeonato brasileiro",
        "corinthians",
        "palmeiras",
        "flamengo",
        "são paulo",
        "vasco",
        "grêmio",
        "internacional",
        "atlético-mg",
        "fluminense",
        "botafogo",
        "cruzeiro",
        "bahia"
    ]):
        return "Brasileirão", ["brasileirao"]

    # ======================================================
    # SE NÃO CAIU NAS REGRAS DURAS → IA DECIDE
    # ======================================================

    if USE_MOCK or not _client:
        return "Última Hora", ["futebol"]

    prompt = f"""
Você é o editor-chefe de um portal esportivo brasileiro - Giro Desportivo.

Escolha EXATAMENTE UMA categoria da lista:
Última Hora, Brasileirão, Mercado da Bola, Onde Assistir, Análises, Bastidores, Agenda

Regras:
- Mercado ou transferência → Mercado da Bola
- Jogo do Brasileirão → Brasileirão
- Análise técnica → Análises
- Bastidor/polêmica → Bastidores
- Dúvida real → Última Hora

Retorne apenas JSON:

{{
  "categoria": "Categoria",
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

        return categoria, tags[:6]

    except Exception:
        return "Última Hora", ["futebol"]


# ======================================================
# CONTEÚDO EDITORIAL INTELIGENTE
# ======================================================

def gerar_conteudo_editorial(
    titulo: str,
    resumo: str,
    categoria: str,
    conteudo_original: str | None = None
) -> str:

    if USE_MOCK or not _client:
        return f"<p>{resumo}</p>"

    conteudo_base = conteudo_original or resumo
    # ------------------------------------------------------
    # EXTRAÇÃO AUTOMÁTICA DE VÍDEOS
    # ------------------------------------------------------
    
    video_embed_html = ""
    
    if conteudo_original:
    
        # YouTube padrão
        yt_match = re.search(
            r"(https?://(?:www\.)?(?:youtube\.com/watch\?v=[\w\-]+|youtu\.be/[\w\-]+))",
            conteudo_original
        )
    
        # Vimeo
        vimeo_match = re.search(
            r"(https?://(?:www\.)?vimeo\.com/\d+)",
            conteudo_original
        )
    
        if yt_match:
            url = yt_match.group(1)
    
            video_id = None
            if "watch?v=" in url:
                video_id = url.split("watch?v=")[-1].split("&")[0]
            elif "youtu.be/" in url:
                video_id = url.split("youtu.be/")[-1]
    
            if video_id:
                video_embed_html = f"""
    <h2>Assista ao vídeo</h2>
    <p>
    <iframe width="100%" height="400"
    src="https://www.youtube.com/embed/{video_id}"
    title="YouTube video player"
    frameborder="0"
    allowfullscreen></iframe>
    </p>
    """
    
        elif vimeo_match:
            url = vimeo_match.group(1)
            video_id = url.split("/")[-1]
    
            video_embed_html = f"""
    <h2>Assista ao vídeo</h2>
    <p>
    <iframe src="https://player.vimeo.com/video/{video_id}"
    width="100%" height="400"
    frameborder="0"
    allowfullscreen></iframe>
    </p>
    """

    # ------------------------------------------------------
    # EXTRAÇÃO DE IMAGENS DO CONTEÚDO ORIGINAL
    # ------------------------------------------------------
    
    imagens_extraidas = []
    
    if conteudo_original:
        imagens = re.findall(
            r'<img[^>]+src="([^">]+)"',
            conteudo_original
        )
    
        for img in imagens:
            img_lower = img.lower()
    
            # ❌ BLOQUEIOS
            if any(p in img_lower for p in [
                "logo",
                "sponsor",
                "banner",
                "ads",
                "esportesdasorte",
                "assets.goal.com/images/v3/blt"
            ]):
                continue
    
            imagens_extraidas.append(
                f'<p><img src="{img}" style="width:100%;height:auto;" loading="lazy"></p>'
            )
    
            if len(imagens_extraidas) >= 3:
                break

    # 🔎 DETECÇÃO AUTOMÁTICA DE TIPO
    texto_base = f"{titulo} {resumo}".lower()

    if any(p in texto_base for p in [
        "vence", "empat", "derrota", "classifica",
        "goleia", "após jogo", "apos jogo"
    ]):
        tipo_materia = "pos_jogo"
    elif any(p in texto_base for p in [
        "onde assistir", "horário", "horario",
        "antes do jogo", "provável escalação"
    ]):
        tipo_materia = "pre_jogo"
    else:
        tipo_materia = "geral"

    prompt = f"""
Você é editor-chefe de um portal esportivo profissional brasileiro.

TIPO DA MATÉRIA: {tipo_materia}

REGRAS ABSOLUTAS:

- Use apenas informações do conteúdo original.
- Nunca invente horário, transmissão, escalação ou estádio.
- Use apenas HTML válido.
- Use SOMENTE <p> e <h2>.
- Nunca use Markdown.
- Comece com <p> (lead forte).
- Produza entre 600 e 900 palavras.
- Nunca inclua o título dentro do conteúdo.

ESTRUTURA POR TIPO:

Se for pos_jogo:
- Foque no resultado.
- Destaque desempenho.
- Contextualize impacto na competição.
- Pode usar <h2>Análise da partida</h2>.
- NÃO use:
  Onde será o jogo
  Horário da partida
  Onde assistir
  Prováveis escalações

Se for pre_jogo:
- Pode usar:
  <h2>Onde será o jogo</h2>
  <h2>Horário da partida</h2>
  <h2>Onde assistir</h2> (somente se confirmado)
  <h2>Prováveis escalações</h2> (somente se confirmado)

Se for geral:
- Estrutura editorial livre.
- Nunca use seções de serviço.

TÍTULO:
{titulo}

RESUMO:
{resumo}

CONTEÚDO ORIGINAL:
{conteudo_base}
"""

    resp = _client.responses.create(
        model=MODEL_NAME,
        input=prompt,
        max_output_tokens=1500,
    )

    texto = resp.output_text.strip()
    
    # 🔎 LIMPEZA DEFENSIVA
    texto = texto.replace("```html", "").replace("```", "").strip()
    
    # 🚨 Blindagem pós-jogo
    if tipo_materia == "pos_jogo":
        texto = re.sub(r"<h2>Horário.*?</p>", "", texto, flags=re.DOTALL)
        texto = re.sub(r"<h2>Onde assistir.*?</p>", "", texto, flags=re.DOTALL)
        texto = re.sub(r"<h2>Onde será.*?</p>", "", texto, flags=re.DOTALL)
    
    # ------------------------------------------------------
    # INSERIR VÍDEO APÓS PRIMEIRO BLOCO
    # ------------------------------------------------------
    if video_embed_html:
        primeiro_paragrafo = re.search(r"<p>.*?</p>", texto, flags=re.DOTALL)
        if primeiro_paragrafo:
            texto = texto.replace(
                primeiro_paragrafo.group(0),
                primeiro_paragrafo.group(0) + video_embed_html,
                1
            )
    
    # ------------------------------------------------------
    # INSERIR IMAGENS COM SEGURANÇA
    # ------------------------------------------------------
    if imagens_extraidas:
        paragrafos = re.findall(r"<p>.*?</p>", texto, flags=re.DOTALL)

        for i, img_html in enumerate(imagens_extraidas):
            if i < len(paragrafos):
                texto = texto.replace(
                    paragrafos[i],
                    paragrafos[i] + img_html,
                    1
                )

    if len(texto) < 400:
        raise ValueError("Conteúdo editorial muito curto")

    texto = aplicar_links_internos(texto)

    return texto

# ======================================================
# UTILIDADES
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
- Máx 90 caracteres
- Claro
- Jornalístico
- Sem clickbait exagerado

Retorne apenas o título final.

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

def aplicar_links_internos(texto: str) -> str:
    from datetime import datetime

    ano_atual = datetime.now().year

    # Detecta ano específico no texto
    ano_match = re.search(r"(20\d{2})", texto)
    ano = ano_match.group(1) if ano_match else str(ano_atual)

    url = f"https://girodesportivo.com/brasileirao-{ano}"

    # Divide o texto evitando mexer em links já existentes
    partes = re.split(r"(<a.*?>.*?</a>)", texto, flags=re.DOTALL)

    link_aplicado = False

    for i in range(len(partes)):
        # Se já é um link, não mexe
        if partes[i].startswith("<a"):
            continue

        if not link_aplicado:
            partes[i], substituicoes = re.subn(
                r"\b(Campeonato Brasileiro\s?20\d{2}|Brasileirão\s?20\d{2}|Campeonato Brasileiro|Brasileirão)\b",
                lambda m: f'<a href="{url}" class="internal-link">{m.group(0)}</a>',
                partes[i],
                count=1
            )

            if substituicoes > 0:
                link_aplicado = True

    return "".join(partes)
