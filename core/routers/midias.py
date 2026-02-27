from fastapi import APIRouter, Request, UploadFile, Form
from fastapi.responses import RedirectResponse
from pathlib import Path
import shutil
from core.database import buscar_midia_por_id

router = APIRouter()

UPLOAD_ROOT = Path("static/uploads")


from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from core.database import listar_midias, listar_pastas

router = APIRouter()

@router.get("/admin/midias", response_class=HTMLResponse)
def admin_midias(request: Request, pasta: str = ""):
    from main import login_required, templates

    auth = login_required(request)
    if auth:
        return auth

    midias = listar_midias(pasta)
    pastas = listar_pastas()

    return templates.TemplateResponse(
        "admin/midias_v2.html",
        {
            "request": request,
            "midias": midias,
            "pastas": pastas,
            "pasta_atual": pasta
        }
    )


from fastapi import UploadFile, Form, Request
from fastapi.responses import RedirectResponse
from core.services.r2 import upload_to_r2
from core.database import inserir_midia
import mimetypes

@router.post("/admin/midias/upload")
async def upload_midia(
    request: Request,
    arquivo: UploadFile,
    pasta_atual: str = Form("")
):
    from main import login_required

    auth = login_required(request)
    if auth:
        return auth

    # 🔥 pegar tamanho do arquivo
    conteudo = await arquivo.read()
    tamanho = len(conteudo)

    # resetar ponteiro do arquivo (IMPORTANTE)
    arquivo.file.seek(0)

    # 🚀 Upload para R2
    folder = pasta_atual.strip("/") if pasta_atual else ""
    url = upload_to_r2(arquivo, folder=folder)

    # 🎯 Detectar tipo
    if arquivo.content_type and "video" in arquivo.content_type:
        tipo = "video"
    elif arquivo.content_type and "image" in arquivo.content_type:
        tipo = "imagem"
    else:
        tipo = "arquivo"

    # 💾 Salvar no banco
    inserir_midia({
        "nome": arquivo.filename,  # 👈 AQUI É O CERTO
        "url": url,
        "pasta": pasta_atual or "",
        "tipo": "imagem",  # ou detectar tipo depois
        "tamanho": 0
    })

    return RedirectResponse(
        url=f"/admin/midias?pasta={pasta_atual}",
        status_code=302
    )

@router.post("/admin/midias/criar-pasta")
async def criar_pasta(
    request: Request,
    nome_pasta: str = Form(...),
    pasta_atual: str = Form("")
):
    from main import login_required
    auth = login_required(request)
    if auth:
        return auth

    nome_pasta = nome_pasta.strip().replace(" ", "-").lower()

    inserir_midia({
        "nome": nome_pasta,           # nome da pasta
        "url": "",                    # nunca null
        "pasta": pasta_atual or "",   # pasta pai
        "tipo": "pasta",
        "tamanho": 0
    })

    return RedirectResponse(
        url=f"/admin/midias?pasta={pasta_atual}",
        status_code=302
    )

from core.database import (
    buscar_midia_por_id,
    deletar_midia,
    listar_midias_por_pasta,
    deletar_pasta_e_conteudo
)
from core.services.r2 import delete_from_r2

@router.post("/admin/midias/delete/{midia_id}")
async def deletar_midia_admin(midia_id: int, request: Request):
    from main import login_required
    auth = login_required(request)
    if auth:
        return auth

    midia = buscar_midia_por_id(midia_id)

    if not midia:
        return RedirectResponse("/admin/midias", status_code=302)

    # 🔥 Se for pasta
    if midia["tipo"] == "pasta":

        arquivos = listar_midias_por_pasta(midia["nome"])

        # apagar arquivos do R2
        for arquivo in arquivos:
            if arquivo["url"]:
                delete_from_r2(arquivo["url"])

        # apagar tudo do banco
        deletar_pasta_e_conteudo(midia["nome"])

    else:
        # arquivo normal
        if midia["url"]:
            delete_from_r2(midia["url"])

        deletar_midia(midia_id)

    return RedirectResponse("/admin/midias", status_code=302)
