# database/queries.py — Funções de consulta ao banco de dados

from database.db import get_pool

# ==================================================
# PERSONAGEM
# ==================================================

async def get_personagem(user_id: int):
    """Retorna o personagem do usuário"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM personagens WHERE user_id = $1", user_id)


async def update_personagem(user_id: int, **kwargs):
    """Atualiza campos do personagem"""
    if not kwargs:
        return
    pool = await get_pool()
    async with pool.acquire() as conn:
        set_clause = ", ".join([f"{k} = ${i+2}" for i, k in enumerate(kwargs.keys())])
        values = [user_id] + list(kwargs.values())
        await conn.execute(f"UPDATE personagens SET {set_clause} WHERE user_id = $1", *values)


async def add_moedas(user_id: int, quantidade: int):
    """Adiciona moedas ao personagem"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("UPDATE personagens SET moedas = moedas + $1 WHERE user_id = $2", quantidade, user_id)


async def add_xp(user_id: int, quantidade: int):
    """Adiciona XP ao personagem"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("UPDATE personagens SET xp = xp + $1 WHERE user_id = $2", quantidade, user_id)


# ==================================================
# INVENTÁRIO
# ==================================================

async def get_inventario(user_id: int):
    """Retorna todos os itens do inventário do usuário"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch("SELECT * FROM inventario WHERE user_id = $1 ORDER BY tipo, raridade", user_id)


async def add_item(user_id: int, item_id: str, nome: str, tipo: str, raridade: str, emoji: str, descricao: str, quantidade: int = 1):
    """Adiciona um item ao inventário do usuário"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        ex = await conn.fetchrow("SELECT id, quantidade FROM inventario WHERE user_id = $1 AND item_id = $2", user_id, item_id)
        if ex:
            await conn.execute("UPDATE inventario SET quantidade = quantidade + $1 WHERE id = $2", quantidade, ex["id"])
        else:
            await conn.execute("""
                INSERT INTO inventario (user_id, item_id, nome, tipo, raridade, emoji, descricao, quantidade)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, user_id, item_id, nome, tipo, raridade, emoji, descricao, quantidade)


async def remove_item(user_id: int, item_id: str, quantidade: int = 1):
    """Remove um item do inventário do usuário"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT id, quantidade FROM inventario WHERE user_id = $1 AND item_id = $2", user_id, item_id)
        if row:
            if row["quantidade"] <= quantidade:
                await conn.execute("DELETE FROM inventario WHERE id = $1", row["id"])
            else:
                await conn.execute("UPDATE inventario SET quantidade = quantidade - $1 WHERE id = $2", quantidade, row["id"])


async def equipar_item(user_id: int, item_id: int, tipo: str):
    """Equipa um item do inventário"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("UPDATE inventario SET equipado = 0 WHERE user_id = $1 AND tipo = $2", user_id, tipo)
        await conn.execute("UPDATE inventario SET equipado = 1 WHERE user_id = $1 AND id = $2", user_id, item_id)


# ==================================================
# SKILLS
# ==================================================

async def get_skills_desbloqueadas(user_id: int):
    """Retorna as skills desbloqueadas do usuário"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT skill_id FROM skills_desbloqueadas WHERE user_id = $1", user_id)
        return [r["skill_id"] for r in rows]


async def get_skills_equipadas(user_id: int):
    """Retorna as skills equipadas do usuário"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT skill_id FROM skills_equipadas WHERE user_id = $1 AND slot != 99 ORDER BY slot", user_id)
        return [r["skill_id"] for r in rows]


async def get_magia_suporte(user_id: int):
    """Retorna a magia de suporte equipada do usuário"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT skill_id FROM skills_equipadas WHERE user_id = $1 AND slot = 99", user_id)
        return row["skill_id"] if row else None


async def desbloquear_skill(user_id: int, skill_id: str):
    """Desbloqueia uma skill para o usuário"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("INSERT INTO skills_desbloqueadas (user_id, skill_id) VALUES ($1, $2) ON CONFLICT DO NOTHING", user_id, skill_id)


async def equipar_skill(user_id: int, skill_id: str, slot: int):
    """Equipa uma skill no slot especificado"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO skills_equipadas (user_id, skill_id, slot)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id, slot) DO UPDATE SET skill_id = EXCLUDED.skill_id
        """, user_id, skill_id, slot)


# ==================================================
# GIROS (FICHAS DE ROLETA)
# ==================================================

async def get_giros(user_id: int):
    """Retorna as fichas de roleta do usuário"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT roleta_id, raridade, quantidade FROM giros WHERE user_id = $1 AND quantidade > 0", user_id)
        result = {}
        for r in rows:
            key = f"{r['roleta_id']}_{r['raridade']}"
            result[key] = {"roleta_id": r["roleta_id"], "raridade": r["raridade"], "quantidade": r["quantidade"]}
        return result


async def adicionar_giro(user_id: int, roleta_id: str, raridade: str, quantidade: int = 1):
    """Adiciona fichas de roleta para o usuário"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO giros (user_id, roleta_id, raridade, quantidade)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (user_id, roleta_id, raridade)
            DO UPDATE SET quantidade = giros.quantidade + $4
        """, user_id, roleta_id, raridade, quantidade)


async def remover_giro(user_id: int, roleta_id: str, raridade: str):
    """Remove uma ficha de roleta do usuário"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE giros SET quantidade = quantidade - 1
            WHERE user_id = $1 AND roleta_id = $2 AND raridade = $3 AND quantidade > 0
        """, user_id, roleta_id, raridade)


# ==================================================
# TREINO USO (LIMITE DIÁRIO)
# ==================================================

async def get_treino_uso(user_id: int):
    """Retorna quantos treinos o usuário já fez hoje"""
    from datetime import datetime, timezone, timedelta
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT count, reset_em FROM treino_uso WHERE user_id = $1", user_id)
        if not row:
            return 0, None
        now = datetime.now(timezone.utc)
        if row["reset_em"] and now >= row["reset_em"]:
            await conn.execute("UPDATE treino_uso SET count = 0, reset_em = NULL WHERE user_id = $1", user_id)
            return 0, None
        return row["count"], row["reset_em"]


async def incrementar_treino_uso(user_id: int):
    """Incrementa o contador de treinos do usuário"""
    from datetime import datetime, timezone, timedelta
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT count FROM treino_uso WHERE user_id = $1", user_id)
        novo = (row["count"] if row else 0) + 1
        reset_em = datetime.now(timezone.utc) + timedelta(hours=2) if novo >= 20 else None
        await conn.execute("""
            INSERT INTO treino_uso (user_id, count, reset_em)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id) DO UPDATE SET count = $2, reset_em = COALESCE($3, treino_uso.reset_em)
        """, user_id, novo, reset_em)