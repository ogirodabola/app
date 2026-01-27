import os
import google.generativeai as genai

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)

MODEL = "gemini-2.0-flash"


def gerar_conteudo_editorial(titulo: str, resumo: str, categoria: str) -> str:
    prompt = f"""
Você é o editorial do site O Giro da Bola.

Reescreva a notícia abaixo:
- Linguagem jornalística popular
- SEO-friendly
- Não cite a fonte original
- Não copie frases
- Crie uma análise final

Título:
{titulo}

Resumo:
{resumo}

Categoria:
{categoria}
"""

    try:
        model = genai.GenerativeModel(MODEL)
        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        print(f"[ERRO GEMINI] {e}")
        return resumo
