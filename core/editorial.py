import os
from google import genai

# usa a variável de ambiente do Render / local
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

MODEL = "models/gemini-2.0-flash"


def gerar_conteudo_editorial(titulo: str, resumo: str, categoria: str) -> str:
    """
    Reescreve a notícia em tom jornalístico popular,
    com foco em SEO e análise.
    """

    prompt = f"""
Você é o Editorial do site O Giro da Bola.

Reescreva a notícia abaixo seguindo estas regras:
- Linguagem jornalística + popular
- Texto médio para longo (SEO)
- NÃO cite a fonte original
- NÃO copie frases
- Crie uma análise final
- Tema: futebol

Título original:
{titulo}

Resumo:
{resumo}

Categoria:
{categoria}

Estruture assim:
- Título
- Parágrafos bem distribuídos
- Subtítulos quando fizer sentido
- Conclusão analítica
"""

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )

        return response.text.strip()

    except Exception as e:
        print(f"[ERRO IA] {e}")
        return resumo
