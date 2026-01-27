from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI()

# STATIC
app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static"
)

# TEMPLATES
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# TESTE ABSOLUTO (SEM JINJA)
@app.get("/ping", response_class=PlainTextResponse)
def ping():
    return "pong"

# HOME
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )
