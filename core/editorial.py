from google import genai
import os

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

MODEL = "models/gemini-2.5-flash"  # rápido e barato

def gerar_conteudo_editorial(titulo, resumo, categoria):
    prompt = f"""
Você é o Editorial Giro da Bola, um portal brasileiro de futebol.

Reescreva a notícia abaixo com:
- linguagem jornalística + popular
- texto 100% original (sem plágio)
- mínimo de 5 parágrafos
- subtítulos (H2) quando fizer sentido
- análise do contexto esportivo
- NÃO cite o site de origem
- NÃO use emojis
- NÃO inclua datas no título

Título base: {titulo}
Resumo base: {resumo}
Categoria: {categoria}
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    return response.text.strip()
