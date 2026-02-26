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
    url = upload_to_r2(arquivo, folder=pasta_atual or "uploads")

    # 🎯 Detectar tipo
    if arquivo.content_type and "video" in arquivo.content_type:
        tipo = "video"
    elif arquivo.content_type and "image" in arquivo.content_type:
        tipo = "imagem"
    else:
        tipo = "arquivo"

    # 💾 Salvar no banco
    inserir_midia({
        "nome": arquivo.filename,
        "url": url,
        "pasta": pasta_atual,
        "tipo": tipo,
        "tamanho": tamanho
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
