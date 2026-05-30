# db.py — Conexao central com PostgreSQL
import asyncpg
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:yRCYpHCAuysDSzhLQfHjYauoznvOgnCa@postgres.railway.internal:5432/railway")

_pool = None

async def get_pool():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
    return _pool

async def init_db():
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS personagens (
                user_id     BIGINT PRIMARY KEY,
                nome        TEXT,
                classe_id   TEXT,
                raridade    TEXT,
                poder_id    TEXT,
                poder_valor INTEGER,
                destino_id  TEXT,
                skill_id    TEXT,
                nivel       INTEGER DEFAULT 1,
                xp          INTEGER DEFAULT 0,
                hp_max      INTEGER DEFAULT 100,
                hp_atual    INTEGER DEFAULT 100,
                ataque      INTEGER DEFAULT 10,
                defesa      INTEGER DEFAULT 10,
                mana_max    INTEGER DEFAULT 100,
                mana_atual  INTEGER DEFAULT 100,
                moedas      INTEGER DEFAULT 50,
                vitorias    INTEGER DEFAULT 0,
                derrotas    INTEGER DEFAULT 0,
                raca_id     TEXT DEFAULT 'humano',
                criado_em   TIMESTAMP DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS inventario (
                id          SERIAL PRIMARY KEY,
                user_id     BIGINT,
                item_id     TEXT,
                nome        TEXT,
                tipo        TEXT,
                raridade    TEXT,
                emoji       TEXT,
                descricao   TEXT,
                equipado    INTEGER DEFAULT 0,
                quantidade  INTEGER DEFAULT 1
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS skills_desbloqueadas (
                user_id  BIGINT,
                skill_id TEXT,
                PRIMARY KEY (user_id, skill_id)
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS skills_equipadas (
                user_id  BIGINT,
                skill_id TEXT,
                slot     INTEGER,
                PRIMARY KEY (user_id, slot)
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS giros (
                user_id    BIGINT,
                roleta_id  TEXT,
                raridade   TEXT,
                quantidade INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, roleta_id, raridade)
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS missoes_diarias (
                user_id    BIGINT,
                data       TEXT,
                missao_id  TEXT,
                descricao  TEXT,
                tipo       TEXT,
                meta       INTEGER,
                progresso  INTEGER DEFAULT 0,
                concluida  INTEGER DEFAULT 0,
                xp         INTEGER,
                moedas     INTEGER,
                ficha      TEXT,
                PRIMARY KEY (user_id, data, missao_id)
            )
        """)
    # Migration — adiciona raca_id se nao existir
    async with pool.acquire() as conn:
        try:
            await conn.execute("ALTER TABLE personagens ADD COLUMN IF NOT EXISTS raca_id TEXT DEFAULT 'humano'")
        except Exception:
            pass
    print("DB PostgreSQL OK")
