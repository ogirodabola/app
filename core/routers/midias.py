from fastapi import APIRouter, Request, UploadFile, Form
from fastapi.responses import RedirectResponse
from pathlib import Path
import shutil

router = APIRouter()

UPLOAD_ROOT = Path("static/uploads")


@router.get("/admin/midias")
def admin_midias(request: Request, pasta: str = ""):
    from main import login_required, templates

    auth = login_required(request)
    if auth:
        return auth

    base_path = UPLOAD_ROOT.resolve()
    current_path = (UPLOAD_ROOT / pasta).resolve()

    if not str(current_path).startswith(str(base_path)):
        current_path = base_path
        pasta = ""

    pastas = []
    arquivos = []

    if current_path.exists():
        for item in current_path.iterdir():
            if item.is_dir():
                pastas.append(item.name)
            elif item.is_file():
                arquivos.append(item.name)

    return templates.TemplateResponse(
        "admin/midias_v2.html",
        {
            "request": request,
            "pastas": sorted(pastas),
            "arquivos": sorted(arquivos),
            "pasta_atual": pasta
        }
    )


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

    destino = (UPLOAD_ROOT / pasta_atual).resolve()

    if not str(destino).startswith(str(UPLOAD_ROOT.resolve())):
        destino = UPLOAD_ROOT

    destino.mkdir(parents=True, exist_ok=True)

    caminho_arquivo = destino / arquivo.filename

    from core.services.r2 import upload_to_r2

    url = upload_to_r2(file, folder=pasta_atual or "uploads")
    
    inserir_midia({
        "nome": file.filename,
        "url": url,
        "pasta": pasta_atual
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

    destino = (UPLOAD_ROOT / pasta_atual / nome_pasta).resolve()

    if str(destino).startswith(str(UPLOAD_ROOT.resolve())):
        destino.mkdir(parents=True, exist_ok=True)

    return RedirectResponse(
        url=f"/admin/midias?pasta={pasta_atual}",
        status_code=302
    )
