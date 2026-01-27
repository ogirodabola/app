from core.editorial import gerar_artigo_editorial
from crawler.utils import extrair_conteudo_noticia

for noticia in noticias_extraidas:
    conteudo_original = extrair_conteudo_noticia(noticia["url"])

    if len(conteudo_original) < 300:
        print("[SKIP] Conteúdo fraco")
        continue

    try:
        conteudo_editorial = gerar_artigo_editorial(conteudo_original)
    except Exception as e:
        print(f"[IA ERRO] {e}")
        continue

    salvar_noticia(
        titulo=noticia["titulo"],
        slug=noticia["slug"],
        fonte=noticia["fonte"],
        categoria=noticia["categoria"],
        url_original=noticia["url"],
        conteudo_original=conteudo_original,
        conteudo_editorial=conteudo_editorial
    )
