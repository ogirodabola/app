from fastapi import APIRouter, Request, HTTPException
from fastapi.templating import Jinja2Templates
from app.database import get_db

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/")
def home(request: Request):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT * FROM noticias
        ORDER BY id DESC
        LIMIT 12
    """)

    noticias = cursor.fetchall()
    db.close()

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "noticias": noticias}
    )


@router.get("/agenda")
def agenda(request: Request):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT * FROM jogos
        ORDER BY horario ASC
    """)

    jogos = cursor.fetchall()
    db.close()

    return templates.TemplateResponse(
        "agenda.html",
        {"request": request, "jogos": jogos}
    )


@router.get("/jogo/{slug}")
def jogo(slug: str, request: Request):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT * FROM jogos WHERE slug = ?
    """, (slug,))

    jogo = cursor.fetchone()
    db.close()

    if not jogo:
        raise HTTPException(status_code=404)

    return templates.TemplateResponse(
        "jogo.html",
        {"request": request, "jogo": jogo}
    )
