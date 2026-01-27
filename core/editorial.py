from google import genai
import os

client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"]
)

def gerar_artigo_editorial(conteudo_original: str) -> str:
    prompt = f"""
Você é o Editorial do site "O Giro da Bola".

Reescreva a notícia abaixo com:
- Tom jornalístico profissional
- Linguagem popular e acessível
- Foco em futebol brasileiro
- Texto médio para longo (SEO-friendly)
- Análise breve do contexto
- Zero plágio do texto original

Estrutura:
- Título chamativo
- Subtítulos
- Parágrafos claros
- Análise final curta

Notícia original:
{conteudo_original}
"""

    response = client.models.generate_content(
        model="models/gemini-flash-latest",
        contents=prompt
    )

    return response.text.strip()
