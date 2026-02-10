from passlib.context import CryptContext
from fastapi import Request
from core.database import get_conn
from psycopg2.extras import RealDictCursor

pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto"
)

def gerar_hash(senha: str) -> str:
    return pwd_context.hash(senha)


def verificar_senha(senha: str, senha_hash: str) -> bool:
    return pwd_context.verify(senha, senha_hash)


def autenticar_usuario(email: str, senha: str):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, email, senha_hash, ativo
                FROM admin_users
                WHERE email = %s
                LIMIT 1
            """, (email,))
            user = cur.fetchone()

    if not user or not user["ativo"]:
        return None

    if not verificar_senha(senha, user["senha_hash"]):
        return None

    return user


def usuario_logado(request: Request):
    return request.session.get("admin_user")
