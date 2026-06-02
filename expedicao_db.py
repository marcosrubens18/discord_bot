# expedicao_db.py — Modelos do banco de dados para expedições avançadas
import json
from db import get_pool

async def init_db_expedicao_avancado():
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Tabela principal de expedições
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS expedicoes_avancadas (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                descricao TEXT DEFAULT '',
                nivel_minimo INTEGER DEFAULT 1,
                max_participantes INTEGER DEFAULT 5,
                status TEXT DEFAULT 'rascunho',
                criado_por BIGINT,
                criado_em TIMESTAMP DEFAULT NOW(),
                imagem_divulgacao TEXT DEFAULT '',
                imagem_final TEXT DEFAULT '',
                config JSONB DEFAULT '{}'
            )
        """)
        
        # Tabela de monstros personalizados
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS expedicao_monstros (
                id SERIAL PRIMARY KEY,
                expedicao_id INTEGER REFERENCES expedicoes_avancadas(id) ON DELETE CASCADE,
                nome TEXT NOT NULL,
                vida INTEGER DEFAULT 100,
                ataque INTEGER DEFAULT 50,
                defesa INTEGER DEFAULT 30,
                critico INTEGER DEFAULT 5,
                imagem TEXT DEFAULT '',
                descricao TEXT DEFAULT '',
                habilidades JSONB DEFAULT '[]',
                permanente BOOLEAN DEFAULT FALSE
            )
        """)
        
        # Tabela de capítulos
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS expedicao_capitulos (
                id SERIAL PRIMARY KEY,
                expedicao_id INTEGER REFERENCES expedicoes_avancadas(id) ON DELETE CASCADE,
                ordem INTEGER DEFAULT 0,
                titulo TEXT NOT NULL,
                texto TEXT DEFAULT '',
                imagem TEXT DEFAULT '',
                tipo TEXT DEFAULT 'narrativa',
                config JSONB DEFAULT '{}'
            )
        """)
        
        # Tabela de recompensas
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS expedicao_recompensas (
                id SERIAL PRIMARY KEY,
                expedicao_id INTEGER REFERENCES expedicoes_avancadas(id) ON DELETE CASCADE,
                tipo TEXT NOT NULL,
                item_id TEXT,
                quantidade INTEGER DEFAULT 1,
                chance INTEGER DEFAULT 100
            )
        """)
        
        # Tabela de participantes
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS expedicao_avancada_participantes (
                id SERIAL PRIMARY KEY,
                expedicao_id INTEGER REFERENCES expedicoes_avancadas(id) ON DELETE CASCADE,
                user_id BIGINT,
                nome TEXT,
                classe_id TEXT,
                nivel INTEGER DEFAULT 1,
                sobreviveu BOOLEAN DEFAULT TRUE,
                inscrito_em TIMESTAMP DEFAULT NOW(),
                UNIQUE(expedicao_id, user_id)
            )
        """)
        
        # Tabela de sessões ativas
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS expedicao_sessoes (
                id SERIAL PRIMARY KEY,
                expedicao_id INTEGER REFERENCES expedicoes_avancadas(id) ON DELETE CASCADE,
                canal_id BIGINT,
                cargo_id BIGINT,
                capitulo_atual INTEGER DEFAULT 0,
                ativa BOOLEAN DEFAULT TRUE,
                iniciada_em TIMESTAMP DEFAULT NOW()
            )
        """)
    
    print("DB expedição avançada OK!")

async def get_materiais_existentes():
    """Pega lista de materiais do catálogo"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch("SELECT DISTINCT item_id, nome, emoji, raridade FROM inventario WHERE tipo='material' LIMIT 100")

async def get_itens_existentes():
    """Pega lista de itens do catálogo"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch("SELECT DISTINCT item_id, nome, emoji, tipo, raridade FROM inventario LIMIT 200")