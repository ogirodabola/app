from core.database import buscar_ad_por_slot

def render_ad(slot_nome: str) -> str:
    ad = buscar_ad_por_slot(slot_nome)

    # fallback silencioso (produção segura)
    if not ad:
        return ""

    if not ad["slot_ativo"] or not ad["script_ativo"]:
        return ""

    return ad["codigo"]
