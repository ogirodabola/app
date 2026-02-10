from core.auth import gerar_hash
from core.database import get_conn

EMAIL = "fsr.tiago@gmail.com"
SENHA = "#t25rootPUkroot$25$"

senha_hash = gerar_hash(SENHA)

with get_conn() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO admin_users (email, senha_hash)
            VALUES (%s, %s)
            ON CONFLICT (email) DO NOTHING
        """, (EMAIL, senha_hash))
    conn.commit()

print("Usuário admin criado com sucesso!")
