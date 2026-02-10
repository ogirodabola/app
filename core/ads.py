from core.database import buscar_ad_por_slot
from fastapi import Request


def is_mobile(user_agent: str) -> bool:
    if not user_agent:
        return False

    ua = user_agent.lower()
    return any(k in ua for k in [
        "mobile", "android", "iphone", "ipad"
    ])


def render_ad(slot_nome: str, request: Request) -> str:
    ad = buscar_ad_por_slot(slot_nome)

    if not ad:
        return ""

    if not ad["slot_ativo"] or not ad["script_ativo"]:
        return ""

    dispositivo = ad.get("dispositivo", "all")

    user_agent = request.headers.get("user-agent", "")
    mobile = is_mobile(user_agent)

    # controle de dispositivo
    if dispositivo == "desktop" and mobile:
        return ""

    if dispositivo == "mobile" and not mobile:
        return ""

    return ad["codigo"]
