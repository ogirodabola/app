# crawler/crawler_noticias.py

from urllib.parse import urlparse

from core.database import criar_tabelas, salvar_noticia
from core.classificacao import classificar_noticia, gerar_slug

from crawler.fontes.gazeta import coletar_noticias_gazeta
from crawler.fontes.goal import coletar_noticias_goal
from crawler.fontes.torcedores import coletar_noticias_torcedores


# ======================================================
# CONFIGURAÇÃO INICIAL
# ======================================================

criar_tabelas()


# ======================================================
# BLINDAGEM INSTITUCIONAL — UOL
# ======================================================

def bloquear_uol(url: str) -> bool:
    if not url:
        return True

    dominio = urlparse(url).netloc.lower()
    return "uol.com.br" in dominio


# ======================================================
# VALIDAÇÃO FINAL DA NOTÍCIA
# ======================================================

def noticia_valida(n: dict) -> bool:
    campos_obrigatorios = [
        "titulo",
        "url",
        "fonte",
        "imagem"
    ]

    for campo in campos_obrigatorios:
        if campo not in n or not n[campo]:
            return False

    if bloquear_uol(n["url"]):
        return False

    if len(n["titulo"]) < 15:
        return False

    return True


# ======================================================
# RUNNER (ORQUESTRADOR PURO)
# ======================================================

def rodar_crawler():
    total_coletadas = 0
    total_salvas = 0

    fontes = [
        coletar_noticias_gazeta,
        coletar_noticias_goal,
        coletar_noticias_torcedores,
    ]

    for crawler in fontes:
        try:
            noticias = crawler()
            total_coletadas += len(noticias)

            for n in noticias:
                if not noticia_valida(n):
                    continue

                sucesso = salvar_noticia(
                    titulo=n["titulo"],
                    resumo=n.get("subtitulo") or n["titulo"][:160],
                    url=n["url"],
                    fonte=n["fonte"],
                    categoria=classificar_noticia(n["titulo"]),
                    slug=gerar_slug(n["titulo"]),
                    imagem=n["imagem"],
                    imagem_credito=n.get("imagem_credito"),
                    conteudo_original=n.get("conteudo_html")
                )

                if sucesso:
                    total_salvas += 1

                except Exception as e:
                    import traceback
                    print(f"\n[RUNNER] erro no crawler {crawler.__name__}")
                    traceback.print_exc()
        
            print(
                f"[RUNNER] Finalizado | coletadas: {total_coletadas} | salvas: {total_salvas}"
            )


# ======================================================
# ENTRYPOINT
# ======================================================

if __name__ == "__main__":
    rodar_crawler()
