# batalha.py — Sistema de batalha corrigido com callback e integração de party
import discord
import asyncio
import random
from db import get_pool
from racas import PassivaRacial, get_raca
from imagens import IMG_VITORIA, IMG_DERROTA, IMG_LEVEL_UP, IMG_MONSTRO
from catalogo import (
    get_rank, CARGOS_RANK,
    get_bonus_arma, get_bonus_armadura,
    get_ids_armas_classe, get_ids_armaduras_classe,
    get_skill_by_id, SKILLS_COMPLETAS,
    calcular_mana_max,
)
from constants import COOLDOWN_BATALHA, COR_SUCCESS, COR_DANGER, COR_WARNING, COR_INFO
from cooldown import cooldown_manager

# ─── CONTROLE DE BATALHAS ATIVAS ────────────────────────────────
BATALHAS_ATIVAS: set = set()  # user_ids com batalha em andamento

# ─── CONSTANTES ──────────────────────────────────────────────────

EMOJI_CLASSE = {
    "guerreiro": "🗡️", "mago": "🔮", "arqueiro": "🏹",
    "paladino": "⚡", "necromante": "🌑", "dracomante": "🐉", "arcano": "✨"
}
COR_RAR = {
    "Comum": 0x888780, "Incomum": 0x1D9E75, "Raro": 0x378ADD,
    "Epico": 0x7F77DD, "Lendario": 0xD85A30
}

ARENAS = [
    {"id": "floresta", "nome": "Floresta Sombria", "emoji": "🌲", "bonus": "magia +15%", "cor": 0x1D9E75,
     "img": "https://i.imgur.com/5Q2xXkN.png"},
    {"id": "vulcao", "nome": "Cratera Vulcanica", "emoji": "🌋", "bonus": "fogo +20%", "cor": 0xD85A30,
     "img": "https://i.imgur.com/6kqJv1R.png"},
    {"id": "gelo", "nome": "Pico de Gelo", "emoji": "❄️", "bonus": "def +10%", "cor": 0x378ADD,
     "img": "https://i.imgur.com/3nQpLmZ.png"},
    {"id": "ruinas", "nome": "Ruinas Arcanas", "emoji": "🏚️", "bonus": "crit +10%", "cor": 0x7F77DD,
     "img": "https://i.imgur.com/8PqWrTz.png"},
    {"id": "coloseu", "nome": "Coloseu Real", "emoji": "🏟️", "bonus": "neutro", "cor": 0xE4AF3C,
     "img": "https://i.imgur.com/2LmNxKp.png"},
]

POCOES = {
    "pocao_hp_p": {"nome": "Pocao de Cura P", "emoji": "🧪", "tipo": "hp", "valor": 30, "preco": 50},
    "pocao_hp_m": {"nome": "Pocao de Cura M", "emoji": "💊", "tipo": "hp", "valor": 60, "preco": 100},
    "pocao_hp_g": {"nome": "Pocao de Cura G", "emoji": "❤️", "tipo": "hp", "valor": 120, "preco": 200},
    "pocao_mana_p": {"nome": "Pocao de Mana P", "emoji": "🔵", "tipo": "mana", "valor": 20, "preco": 60},
    "pocao_mana_m": {"nome": "Pocao de Mana M", "emoji": "💙", "tipo": "mana", "valor": 50, "preco": 120},
    "elixir": {"nome": "Elixir Supremo", "emoji": "✨", "tipo": "full", "valor": 999, "preco": 500},
}

LOJA_ITENS = {
    "pocoes": [
        {"id": k, "nome": v["nome"], "emoji": v["emoji"], "raridade": "Comum", "preco": v["preco"],
         "desc": f"Recupera {v['valor']} {'HP' if v['tipo'] == 'hp' else 'Mana'}"}
        for k, v in POCOES.items()
    ],
}

RECEITAS = [
    # ── Rank Raro ─────────────────────────────────────────────────
    {"id": "espada_orc", "nome": "Espada Orc", "emoji": "🗡️", "tipo": "arma", "raridade": "Raro",
     "desc": "Forjada com metal orc. ATK +20",
     "materiais": {"dente_orc": 2, "minerio_ferro": 3}, "preco_forja": 100},
    {"id": "cajado_osso2", "nome": "Cajado Osseo+", "emoji": "💀", "tipo": "arma", "raridade": "Raro",
     "desc": "Amplifica magia negra. Magia +17",
     "materiais": {"dente_orc": 1, "sangue_anciao": 1}, "preco_forja": 200},
    {"id": "anel_combate", "nome": "Anel de Combate", "emoji": "💍", "tipo": "acessorio", "raridade": "Raro",
     "desc": "+10 ATK e +5 DEF permanente",
     "materiais": {"fragmento_golem": 1, "minerio_ferro": 2}, "preco_forja": 150},
    {"id": "manto_sombra2", "nome": "Manto das Sombras+", "emoji": "🧥", "tipo": "armadura", "raridade": "Raro",
     "desc": "DEF +20 e +15% esquiva",
     "materiais": {"muco_troll": 2, "essencia_sombria": 1}, "preco_forja": 220},
    {"id": "pocao_superior", "nome": "Pocao Superior", "emoji": "🍶", "tipo": "pocao", "raridade": "Raro",
     "desc": "Restaura 200 HP instantaneamente",
     "materiais": {"sangue_anciao": 1, "olho_dragao": 1}, "preco_forja": 180},
    {"id": "lanca_orc", "nome": "Lanca Orc", "emoji": "🔱", "tipo": "arma", "raridade": "Raro",
     "desc": "Forjada com ossos de orc. ATK +18",
     "materiais": {"dente_orc": 3, "osso_oco": 2}, "preco_forja": 160},

    # ── Rank Epico ────────────────────────────────────────────────
    {"id": "armadura_escama", "nome": "Armadura de Escama", "emoji": "🐉", "tipo": "armadura", "raridade": "Epico",
     "desc": "Escamas de dragao. DEF +25",
     "materiais": {"escama_dragao": 1, "fragmento_golem": 2}, "preco_forja": 300},
    {"id": "espada_sombria2", "nome": "Espada das Trevas", "emoji": "🗡️", "tipo": "arma", "raridade": "Epico",
     "desc": "Drena HP ao acertar. ATK +28",
     "materiais": {"essencia_sombria": 2, "dente_orc": 2}, "preco_forja": 400},
    {"id": "cajado_vazio2", "nome": "Cajado do Vazio+", "emoji": "🌀", "tipo": "arma", "raridade": "Epico",
     "desc": "Ignora 20% da defesa. ATK +26",
     "materiais": {"essencia_sombria": 1, "olho_dragao": 1, "fragmento_golem": 1}, "preco_forja": 450},
    {"id": "capa_grifo", "nome": "Capa do Grifo", "emoji": "🦅", "tipo": "armadura", "raridade": "Epico",
     "desc": "DEF +30 e +20% velocidade",
     "materiais": {"pena_grifo": 3, "pele_lobo": 4}, "preco_forja": 380},

    # ── Rank Lendario ─────────────────────────────────────────────
    {"id": "elmo_dragao", "nome": "Elmo do Dragao", "emoji": "🪖", "tipo": "armadura", "raridade": "Lendario",
     "desc": "Protecao maxima. DEF +32",
     "materiais": {"escama_dragao": 2, "olho_dragao": 1}, "preco_forja": 500},
    {"id": "espada_dragao2", "nome": "Espada do Dragao+", "emoji": "⚔️", "tipo": "arma", "raridade": "Lendario",
     "desc": "Flamejante eternamente. ATK +40",
     "materiais": {"escama_dragao": 3, "dente_dragao": 2}, "preco_forja": 700},
    {"id": "armadura_titan", "nome": "Armadura do Titan", "emoji": "🗿", "tipo": "armadura", "raridade": "Lendario",
     "desc": "Maxima protecao. DEF +45 +20% HP max",
     "materiais": {"fragmento_titan": 2, "escama_dragao": 2, "fragmento_golem": 3}, "preco_forja": 900},
    {"id": "cajado_lich2", "nome": "Cetro do Lich+", "emoji": "💀", "tipo": "arma", "raridade": "Lendario",
     "desc": "Poder necrotico supremo. ATK +47",
     "materiais": {"essencia_lich": 1, "coroa_lich": 1}, "preco_forja": 800},
]

MONSTROS = [
    # ── FACIL ─────────────────────────────────────────────────────
    {"id": "goblin", "img": "https://i.imgur.com/3NpKzQm.png", "nome": "Goblin", "emoji": "👺", "nivel": 1, "hp": 50,
     "ataque": 22, "defesa": 2, "xp": 6, "moedas": 5, "dificuldade": "facil",
     "skills": [{"nome": "Mordida", "emoji": "🦷", "dano": 8}, {"nome": "Arranhao", "emoji": "💢", "dano": 5}],
     "loot": [("pedra_suja", "Pedra Suja", "material", "Comum", "🪨", "Ingrediente basico")]},
    {"id": "lobo", "img": "https://i.imgur.com/5Q2xXkN.png", "nome": "Lobo Selvagem", "emoji": "🐺", "nivel": 3,
     "hp": 65, "ataque": 28, "defesa": 3, "xp": 8, "moedas": 5, "dificuldade": "facil",
     "skills": [{"nome": "Mordida Feroz", "emoji": "🦷", "dano": 14}, {"nome": "Investida", "emoji": "💨", "dano": 10}],
     "loot": [("pele_lobo", "Pele de Lobo", "material", "Comum", "🐾", "Material de armadura")]},
    {"id": "rato_gigante", "img": "https://i.imgur.com/6kqJv1R.png", "nome": "Rato Gigante", "emoji": "🐀", "nivel": 2,
     "hp": 55, "ataque": 8, "defesa": 3, "xp": 6, "moedas": 5, "dificuldade": "facil",
     "skills": [{"nome": "Arranhao Duplo", "emoji": "💢", "dano": 9}, {"nome": "Fuga", "emoji": "💨", "dano": 4}],
     "loot": [("pelo_rato", "Pelo de Rato", "material", "Comum", "🐾", "Material comum")]},
    {"id": "goblin_arqueiro", "img": "https://i.imgur.com/8PqWrTz.png", "nome": "Goblin Arqueiro", "emoji": "👺", "nivel": 4,
     "hp": 60, "ataque": 9, "defesa": 3, "xp": 7, "moedas": 5, "dificuldade": "facil",
     "skills": [{"nome": "Flechada", "emoji": "🏹", "dano": 12}, {"nome": "Tiro Rapido", "emoji": "🏹", "dano": 8}],
     "loot": [("flecha_goblin", "Flecha de Goblin", "material", "Comum", "🏹", "Material de projétil")]},

    # ── MEDIO ─────────────────────────────────────────────────────
    {"id": "orc", "img": "https://i.imgur.com/2LmNxKp.png", "nome": "Orc Guerreiro", "emoji": "👹", "nivel": 7,
     "hp": 280, "ataque": 40, "defesa": 8, "xp": 18, "moedas": 10, "dificuldade": "medio",
     "skills": [{"nome": "Machado", "emoji": "🪓", "dano": 22}, {"nome": "Grito de Guerra", "emoji": "😤", "dano": 12}],
     "loot": [("dente_orc", "Dente de Orc", "material", "Incomum", "🦷", "Ingrediente alquimico"),
              ("minerio_ferro", "Minerio de Ferro", "material", "Comum", "⛏️", "Metal bruto")]},
    {"id": "golem", "img": "https://i.imgur.com/3nQpLmZ.png", "nome": "Golem de Pedra", "emoji": "🗿", "nivel": 12,
     "hp": 380, "ataque": 52, "defesa": 15, "xp": 22, "moedas": 10, "dificuldade": "medio",
     "skills": [{"nome": "Soco de Pedra", "emoji": "👊", "dano": 30}, {"nome": "Terremoto", "emoji": "🌋", "dano": 20}],
     "loot": [("fragmento_golem", "Fragmento de Golem", "material", "Raro", "🪨", "Material magico")]},
    {"id": "esqueleto", "img": "https://i.imgur.com/6MqWrZp.png", "nome": "Esqueleto Armado", "emoji": "💀", "nivel": 9,
     "hp": 300, "ataque": 20, "defesa": 12, "xp": 18, "moedas": 10, "dificuldade": "medio",
     "skills": [{"nome": "Espada Ossea", "emoji": "⚔️", "dano": 25}, {"nome": "Lanca de Osso", "emoji": "🔱", "dano": 18}],
     "loot": [("osso_oco", "Osso Oco", "material", "Incomum", "💀", "Material necrotico")]},
    {"id": "troll_pântano", "img": "https://i.imgur.com/4NqKpZm.png", "nome": "Troll do Pantano", "emoji": "🧌", "nivel": 11,
     "hp": 350, "ataque": 24, "defesa": 8, "xp": 20, "moedas": 10, "dificuldade": "medio",
     "skills": [{"nome": "Porrada", "emoji": "👊", "dano": 32}, {"nome": "Lama Toxica", "emoji": "🟢", "dano": 15}],
     "loot": [("muco_troll", "Muco de Troll", "material", "Incomum", "🟢", "Ingrediente alquimico")]},

    # ── DIFICIL ───────────────────────────────────────────────────
    {"id": "vampiro", "img": "https://i.imgur.com/5QrLpKz.png", "nome": "Vampiro Anciao", "emoji": "🧛", "nivel": 20,
     "hp": 550, "ataque": 75, "defesa": 14, "xp": 40, "moedas": 20, "dificuldade": "dificil",
     "skills": [{"nome": "Drenar Sangue", "emoji": "🩸", "dano": 40}, {"nome": "Hipnose", "emoji": "👁️", "dano": 15}],
     "loot": [("sangue_fresco", "Sangue Fresco", "material", "Incomum", "🩸", "Ingrediente alquimico"),
              ("sangue_anciao", "Sangue Anciao", "material", "Raro", "🩸", "Ingrediente raro")]},
    {"id": "troll_pedra", "img": "https://i.imgur.com/8WmKzNp.png", "nome": "Troll das Pedras", "emoji": "🗿", "nivel": 22,
     "hp": 620, "ataque": 38, "defesa": 25, "xp": 42, "moedas": 20, "dificuldade": "dificil",
     "skills": [{"nome": "Avalanche", "emoji": "🪨", "dano": 45}, {"nome": "Esmagar", "emoji": "💥", "dano": 35}],
     "loot": [("nucleo_pedra", "Nucleo de Pedra", "material", "Raro", "💎", "Material magico raro")]},
    {"id": "bruxa", "img": "https://i.imgur.com/4QzXpKn.png", "nome": "Bruxa das Trevas", "emoji": "🧙", "nivel": 25,
     "hp": 500, "ataque": 42, "defesa": 15, "xp": 45, "moedas": 20, "dificuldade": "dificil",
     "skills": [{"nome": "Maldicao", "emoji": "🩸", "dano": 38}, {"nome": "Bola de Fogo Sombria", "emoji": "🔥", "dano": 50}],
     "loot": [("essencia_sombria", "Essencia Sombria", "material", "Raro", "🌑", "Ingrediente sombrio")]},
    {"id": "grifo", "img": "https://i.imgur.com/7RmKpXz.png", "nome": "Grifo Selvagem", "emoji": "🦅", "nivel": 28,
     "hp": 580, "ataque": 40, "defesa": 20, "xp": 46, "moedas": 20, "dificuldade": "dificil",
     "skills": [{"nome": "Bico de Aco", "emoji": "⚔️", "dano": 42}, {"nome": "Garra Dupla", "emoji": "🐾", "dano": 35}],
     "loot": [("pena_grifo", "Pena de Grifo", "material", "Raro", "🦅", "Material de voo")]},

    # ── LENDARIO ──────────────────────────────────────────────────
    {"id": "dragao", "img": "https://i.imgur.com/9WqLpNm.png", "nome": "Dragao Jovem", "emoji": "🐉", "nivel": 35,
     "hp": 1200, "ataque": 120, "defesa": 20, "xp": 80, "moedas": 50, "dificuldade": "lendario",
     "skills": [{"nome": "Baforada de Fogo", "emoji": "🔥", "dano": 70}, {"nome": "Garra Draconica", "emoji": "🐾", "dano": 55}],
     "loot": [("escama_dragao_p", "Escama de Dragao Pequena", "material", "Raro", "🐉", "Fragmento de escama"),
              ("escama_dragao_p", "Escama Pequena", "material", "Raro", "🐉", "Escama de dragao jovem")]},
    {"id": "quimera", "img": "https://i.imgur.com/3NpKzQm.png", "nome": "Quimera Anciao", "emoji": "🦁", "nivel": 40,
     "hp": 1400, "ataque": 70, "defesa": 40, "xp": 90, "moedas": 50, "dificuldade": "lendario",
     "skills": [{"nome": "Rugido do Caos", "emoji": "😤", "dano": 75}, {"nome": "Chamas e Gelo", "emoji": "❄️", "dano": 60}],
     "loot": [("corno_quimera_p", "Fragmento de Corno", "material", "Raro", "🦄", "Material raro"),
              ("escama_dragao_p", "Escama de Dragao Pequena", "material", "Raro", "🐉", "Fragmento de escama")]},
    {"id": "lich", "img": "https://i.imgur.com/6MqWrZp.png", "nome": "Lich Anciao", "emoji": "💀", "nivel": 45,
     "hp": 1300, "ataque": 75, "defesa": 30, "xp": 95, "moedas": 50, "dificuldade": "lendario",
     "skills": [{"nome": "Toque da Morte", "emoji": "☠️", "dano": 80}, {"nome": "Exercito Espectral", "emoji": "👻", "dano": 50}],
     "loot": [("essencia_sombria_p", "Essencia Sombria", "material", "Raro", "💀", "Ingrediente sombrio"),
              ("osso_lich", "Osso do Lich", "material", "Raro", "💀", "Ingrediente raro")]},
    {"id": "titan", "img": "https://i.imgur.com/4NqKpZm.png", "nome": "Titan Primordial", "emoji": "🗿", "nivel": 50,
     "hp": 1600, "ataque": 85, "defesa": 50, "xp": 100, "moedas": 50, "dificuldade": "lendario",
     "skills": [{"nome": "Golpe Primordial", "emoji": "💥", "dano": 90}, {"nome": "Tremor da Terra", "emoji": "🌋", "dano": 70}],
     "loot": [("fragmento_titan", "Fragmento do Titan", "material", "Lendario", "🗿", "Lendario absoluto"),
              ("escama_dragao_p", "Escama de Dragao Pequena", "material", "Raro", "🐉", "Fragmento de escama")]},
]

# ─── DB HELPERS ──────────────────────────────────────────────────

async def get_skills_eq(user_id):
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT skill_id FROM skills_equipadas WHERE user_id=$1 AND slot!=99 ORDER BY slot",
            user_id
        )
        return [r["skill_id"] for r in rows]

async def get_skills_desbloq(user_id):
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT skill_id FROM skills_desbloqueadas WHERE user_id=$1", user_id)
        return [r["skill_id"] for r in rows]

async def get_pocoes_inv(user_id):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch(
            "SELECT * FROM inventario WHERE user_id=$1 AND (item_id LIKE 'pocao%' OR item_id='elixir')",
            user_id
        )

async def get_arma_equipada(user_id):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            "SELECT * FROM inventario WHERE user_id=$1 AND tipo='arma' AND equipado=1 LIMIT 1",
            user_id
        )

async def get_armadura_equipada(user_id):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            "SELECT * FROM inventario WHERE user_id=$1 AND tipo='armadura' AND equipado=1 LIMIT 1",
            user_id
        )

async def add_loot(user_id, loot):
    pool = await get_pool()
    async with pool.acquire() as conn:
        for it in loot:
            iid, nome, tipo, rar, emoji, desc = it
            ex = await conn.fetchrow(
                "SELECT id, quantidade FROM inventario WHERE user_id=$1 AND item_id=$2",
                user_id, iid
            )
            if ex:
                await conn.execute(
                    "UPDATE inventario SET quantidade=quantidade+1 WHERE id=$1",
                    ex["id"]
                )
            else:
                await conn.execute(
                    "INSERT INTO inventario(user_id,item_id,nome,tipo,raridade,emoji,descricao) VALUES($1,$2,$3,$4,$5,$6,$7)",
                    user_id, iid, nome, tipo, rar, emoji, desc
                )

async def remover_pocao(user_id, item_id):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, quantidade FROM inventario WHERE user_id=$1 AND item_id=$2",
            user_id, item_id
        )
        if row:
            if row["quantidade"] > 1:
                await conn.execute("UPDATE inventario SET quantidade=quantidade-1 WHERE id=$1", row["id"])
            else:
                await conn.execute("DELETE FROM inventario WHERE id=$1", row["id"])

async def desbloquear_skills_nivel(conn, user_id, classe_id, nivel):
    """Desbloqueia skills da classe pelo nivel atual."""
    skills = SKILLS_COMPLETAS.get(classe_id, [])
    for s in skills:
        if s["nivel"] <= nivel:
            await conn.execute(
                "INSERT INTO skills_desbloqueadas(user_id,skill_id) VALUES($1,$2) ON CONFLICT DO NOTHING",
                user_id, s["id"]
            )

async def salvar_resultado(user_id, hp, xp_ganho, moedas_ganhas, vitoria, classe_id, nivel_atual, mana_atual_batalha=None):
    """Salva resultado e retorna (levelups, nivel_novo, rank_mudou, rank_novo)."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        p = await conn.fetchrow(
            "SELECT xp, nivel, hp_max, hp_atual, ataque, defesa, mana_max, mana_atual, poder_valor, destino_id FROM personagens WHERE user_id=$1",
            user_id
        )
        if not p:
            return 0, nivel_atual, False, None

        # Bonus de XP racial (Humano +15%)
        from racas import get_raca as _get_raca
        _raca = _get_raca(p.get("raca_id", "humano")) if "raca_id" in p.keys() else {"bonus_xp": 0.0}
        _bonus_xp = _raca.get("bonus_xp", 0.0) if isinstance(_raca, dict) else 0.0
        xp_ganho = int(xp_ganho * (1.0 + _bonus_xp))
        novo_xp = p["xp"] + xp_ganho
        nv = p["nivel"]
        levelups = 0
        rank_antes = get_rank(nv)["rank"]

        # Calcula level ups
        needed = 100 + (nv - 1) * 50
        while novo_xp >= needed:
            novo_xp -= needed
            nv += 1
            needed = 100 + (nv - 1) * 50
            levelups += 1

        # Atualiza stats por nivel
        hp_max_novo = p["hp_max"] + levelups * 12
        atk_novo = p["ataque"] + levelups * 2
        dfs_novo = p["defesa"] + levelups * 1

        # Bonus de rank up (so se mudou de rank)
        rank_bonus_hp = rank_bonus_mana = rank_bonus_atk = rank_bonus_dfs = 0
        if rank_antes != get_rank(nv)["rank"]:
            novo_rank = get_rank(nv)["rank"]
            bonus = RANK_BONUS.get(novo_rank, {})
            rank_bonus_hp = bonus.get("hp", 0)
            rank_bonus_mana = bonus.get("mana", 0)
            rank_bonus_atk = bonus.get("atk", 0)
            rank_bonus_dfs = bonus.get("dfs", 0)
            hp_max_novo += rank_bonus_hp
            atk_novo += rank_bonus_atk
            dfs_novo += rank_bonus_dfs
        mana_max_novo = calcular_mana_max(classe_id, nv, p["poder_valor"], p["destino_id"]) + rank_bonus_mana
        hp_final = max(1, min(hp, hp_max_novo))

        mana_base = int(mana_atual_batalha) if mana_atual_batalha is not None else p["mana_atual"]
        mana_salvar = max(0, min(mana_base + levelups * 10, mana_max_novo))

        await conn.execute("""
            UPDATE personagens
            SET hp_atual=$1, hp_max=$2, xp=$3, nivel=$4,
                ataque=$5, defesa=$6, mana_max=$7, mana_atual=$8,
                moedas=moedas+$9, vitorias=vitorias+$10, derrotas=derrotas+$11
            WHERE user_id=$12
        """,
            hp_final, hp_max_novo, novo_xp, nv,
            atk_novo, dfs_novo, mana_max_novo, mana_salvar,
            moedas_ganhas,
            1 if vitoria else 0,
            0 if vitoria else 1,
            user_id
        )

        # Desbloqueia skills pelo novo nivel
        await desbloquear_skills_nivel(conn, user_id, classe_id, nv)

        # Log de batalha
        try:
            await conn.execute("""
                INSERT INTO log_batalhas(user_id,tipo,resultado,oponente,xp_ganho,moedas_ganhas,nivel_apos)
                VALUES($1,'treino',$2,$3,$4,$5,$6)
            """, user_id,
                "vitoria" if vitoria else "derrota",
                "Treino", xp_ganho, moedas_ganhas, nv)
        except:
            pass

        rank_novo_obj = get_rank(nv)
        rank_mudou = rank_novo_obj["rank"] != rank_antes

        return levelups, nv, rank_mudou, rank_novo_obj


async def init_db_batalha():
    pass  # tabelas criadas no db.py


# ─── CALCULOS ────────────────────────────────────────────────────

def calc_dano(atk, dfs, mult=1.0, crit=False, bonus_atk=1.0, ignorar_defesa=False, nivel=1, hp_max_monstro=None, passiva_mult=1.0):
    """Dano escalado pelo nivel de forma linear e controlada."""
    if nivel <= 9:
        div_forca = 1.1
        mult_cap = 1.15
    elif nivel <= 19:
        div_forca = 0.95
        mult_cap = 1.35
    elif nivel <= 29:
        div_forca = 0.85
        mult_cap = 1.55
    elif nivel <= 39:
        div_forca = 0.78
        mult_cap = 1.70
    elif nivel <= 49:
        div_forca = 0.72
        mult_cap = 1.80
    elif nivel <= 59:
        div_forca = 0.67
        mult_cap = 1.80
    elif nivel <= 74:
        div_forca = 0.62
        mult_cap = 1.80
    else:
        div_forca = 0.58
        mult_cap = 1.80

    mult_real = min(mult_cap, mult)
    dano_minimo = max(15, int(atk * 0.25))

    if ignorar_defesa:
        base = int((atk / div_forca) * mult_real)
    else:
        atk_efetivo = max(1, atk - int(dfs * 0.35))
        base = int((atk_efetivo / div_forca) * mult_real)

    base = max(dano_minimo, base)

    variacao = random.randint(-max(1, base // 10), max(1, base // 10))
    dano = max(dano_minimo, base + variacao)

    dano = int(dano * min(bonus_atk, 1.15))

    if crit:
        dano = int(dano * 1.30)

    if hp_max_monstro:
        cap = max(dano_minimo, int(hp_max_monstro * 0.35))
        dano = min(cap, dano)

    return max(dano_minimo, dano)


def barra_hp(cur, mx):
    if mx <= 0:
        return "░░░░░░░░░░"
    p = max(0.0, cur / mx)
    f = int(p * 10)
    char = "█" if p > 0.6 else ("▓" if p > 0.3 else "▒")
    return char * f + "░" * (10 - f)


def get_skill_resolv(classe_id, skill_id):
    """Resolve skill pelo catalogo novo, fallback para antigo."""
    sk = get_skill_by_id(skill_id)
    if sk:
        return sk
    for s in SKILLS_COMPLETAS.get(classe_id, []):
        if s["id"] == skill_id:
            return dict(s, classe_origem=classe_id)
    return None


def calcular_bonus_equip(classe_id, arma, armadura):
    """Retorna (bonus_atk_mult, bonus_dfs_mult) com base na afinidade."""
    bonus_atk = 1.0
    bonus_dfs = 1.0
    if arma:
        arma_id = arma["item_id"]
        _, compat = get_bonus_arma(arma_id, classe_id)
        if compat is True:
            bonus_atk = 1.15
        elif compat is False:
            bonus_atk = 0.85
    if armadura:
        arm_id = armadura["item_id"]
        _, compat = get_bonus_armadura(arm_id, classe_id)
        if compat is True:
            bonus_dfs = 1.10
        elif compat is False:
            bonus_dfs = 0.90
    return bonus_atk, bonus_dfs


def aplicar_efeito_pocao(item_id, hp, hp_max, mana, mana_max):
    """Aplica pocao e retorna (hp_novo, mana_nova, descricao)."""
    poc = POCOES.get(item_id)
    if not poc:
        return hp, mana, "Pocao desconhecida."
    if poc["tipo"] == "hp":
        ganho = min(poc["valor"], hp_max - hp)
        hp_novo = hp + ganho
        return hp_novo, mana, f"{poc['emoji']} {poc['nome']} usada! +{ganho} HP ❤️"
    elif poc["tipo"] == "mana":
        ganho = min(poc["valor"], mana_max - mana)
        mana_nova = mana + ganho
        return hp, mana_nova, f"{poc['emoji']} {poc['nome']} usada! +{ganho} Mana 💙"
    else:
        return hp_max, mana_max, f"{poc['emoji']} Elixir Supremo! HP e Mana restaurados! ✨"


# ─── PASSIVA DE CLASSE ───────────────────────────────────────────

class Passiva:
    def __init__(self, classe_id):
        self.classe_id = classe_id
        self.turno = 0
        self.bonus_dreno = 1.0
        self.bonus_mag_acum = 0.0
        self.arcano_turnos = 0
        self.arcano_acum = 0.0

    def inicio_turno(self, hp_j, hp_jmx):
        self.turno += 1
        cura = 0
        if self.classe_id == "paladino" and hp_jmx > 0 and (hp_j / hp_jmx) < 0.30:
            cura = 15
        if self.classe_id == "mago":
            self.bonus_mag_acum = min(0.40, self.bonus_mag_acum + 0.08)
        return cura

    def apos_critico(self):
        return 8 if self.classe_id == "arqueiro" else 0

    def apos_dreno(self):
        if self.classe_id == "necromante":
            self.bonus_dreno = min(2.0, self.bonus_dreno + 0.10)
        return self.bonus_dreno

    def apos_tomar_dano(self):
        if self.classe_id == "arcano":
            self.arcano_acum = 0.0
            self.arcano_turnos = 0

    def fim_turno_sem_dano(self):
        if self.classe_id == "arcano":
            self.arcano_turnos += 1
            self.arcano_acum = min(0.50, self.arcano_turnos * 0.10)

    def bonus_defesa_fixa(self):
        if self.classe_id == "guerreiro":
            return min(30, (self.turno // 3) * 3)
        return 0

    def reducao_dano(self):
        return 0.10 if self.classe_id == "dracomante" else 0.0

    def imune_status(self, status):
        return self.classe_id == "dracomante" and status in ("queimadura", "veneno")

    def multiplicador_dano(self):
        if self.classe_id == "mago":
            return 1.0 + self.bonus_mag_acum
        if self.classe_id == "arcano":
            return 1.0 + self.arcano_acum
        return 1.0

    def desc_passiva(self):
        if self.classe_id == "guerreiro":
            return f"🗡️ DEF passiva: +{self.bonus_defesa_fixa()}"
        if self.classe_id == "arqueiro":
            return "🏹 Crítico recupera 8 mana"
        if self.classe_id == "mago":
            return f"🔮 Dano mágico +{int(self.bonus_mag_acum * 100)}%"
        if self.classe_id == "paladino":
            return "⚡ Cura auto 15 HP/turno se HP<30%"
        if self.classe_id == "necromante":
            return f"🌑 Dreno x{self.bonus_dreno:.1f}"
        if self.classe_id == "dracomante":
            return "🐉 -10% dano, imune veneno/queimadura"
        if self.classe_id == "arcano":
            return f"✨ Dano arcano +{int(self.arcano_acum * 100)}%"
        return ""


# ─── PROCESSAMENTO DE EFEITOS ─────────────────────────────────────

def processar_efeitos_turno(efeitos):
    """
    Processa efeitos no inicio do turno.
    Retorna (dano_de_efeito, msg_efeito, efeitos_atualizados).
    """
    dano_total = 0
    msgs = []
    novos_efeitos = {}

    for ef, dados in efeitos.items():
        if isinstance(dados, dict):
            duracao = dados.get("duracao", 0)
            valor = dados.get("valor", 0)
        else:
            duracao = dados
            valor = 0

        if duracao <= 0:
            continue

        duracao -= 1

        if ef == "veneno":
            dano_total += valor
            msgs.append(f"☠️ Veneno causou **{valor}** de dano!")
        elif ef == "queimadura":
            dano_total += valor
            msgs.append(f"🔥 Queimadura causou **{valor}** de dano!")
        elif ef == "regeneracao":
            msgs.append(f"💚 Regeneracao: +{valor} HP!")
        elif ef in ("defesa", "escudo", "esquiva", "escudo_total", "armadura", "reflexo",
                    "buff_ataque", "buff_all", "berserker", "congelar", "paralisia",
                    "atordoado", "confusao", "terror", "enfraquecer"):
            pass

        if duracao > 0:
            novos_efeitos[ef] = {"duracao": duracao, "valor": valor}

    return dano_total, msgs, novos_efeitos


def efeito_ativo(efeitos, nome):
    ef = efeitos.get(nome)
    if ef is None:
        return False
    if isinstance(ef, dict):
        return ef.get("duracao", 0) > 0
    return ef > 0


def add_efeito(efeitos, nome, duracao, valor=0):
    efeitos[nome] = {"duracao": duracao, "valor": valor}


# ─── VIEWS ───────────────────────────────────────────────────────

class EscolherArenaView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=30)
        self.user_id = user_id
        self.arena = None
        opcoes = [
            discord.SelectOption(
                label=f"{a['emoji']} {a['nome']}",
                value=a["id"],
                description=f"Bonus: {a['bonus']}",
                default=False
            ) for a in ARENAS
        ]
        sel = discord.ui.Select(
            placeholder="🏟️ Escolha uma arena...",
            options=opcoes,
            min_values=1,
            max_values=1
        )
        sel.callback = self._escolher
        self.add_item(sel)

    async def _escolher(self, inter: discord.Interaction):
        if inter.user.id != self.user_id:
            await inter.response.defer()
            return
        self.arena = next(a for a in ARENAS if a["id"] == inter.data["values"][0])
        await inter.response.edit_message(
            embed=discord.Embed(
                title=f"{self.arena['emoji']} Arena: {self.arena['nome']}",
                description=f"Bonus: **{self.arena['bonus']}**",
                color=self.arena["cor"]
            ),
            view=None
        )
        self.stop()

    async def on_timeout(self):
        if not self.arena:
            self.arena = random.choice(ARENAS)
        self.stop()


class AceitarDueloView(discord.ui.View):
    def __init__(self, desafiante_id, desafiado_id):
        super().__init__(timeout=300)
        self.desafiante_id = desafiante_id
        self.desafiado_id = desafiado_id
        self.resposta = None

    @discord.ui.button(label="✅ Aceitar", style=discord.ButtonStyle.success)
    async def aceitar(self, inter: discord.Interaction, b):
        if inter.user.id != self.desafiado_id:
            await inter.response.send_message("Nao e voce que foi desafiado!", ephemeral=True)
            return
        self.resposta = True
        await inter.response.defer()
        self.stop()

    @discord.ui.button(label="❌ Recusar", style=discord.ButtonStyle.danger)
    async def recusar(self, inter: discord.Interaction, b):
        if inter.user.id not in (self.desafiado_id, self.desafiante_id):
            await inter.response.send_message("Nao e sua batalha!", ephemeral=True)
            return
        self.resposta = False
        await inter.response.defer()
        self.stop()


class GerenciarSkillsView(discord.ui.View):
    def __init__(self, user_id, skills, skills_eq):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.skills = skills
        opcoes = [
            discord.SelectOption(
                label=f"{s['emoji']} {s['nome']} (Nv{s['nivel']})",
                value=s["id"],
                description=s["desc"][:50],
                default=s["id"] in skills_eq
            ) for s in skills[:25]
        ]
        if opcoes:
            sel = discord.ui.Select(
                placeholder="Selecione até 4 skills...",
                min_values=1, max_values=min(4, len(opcoes)),
                options=opcoes
            )
            sel.callback = self._sel
            self.add_item(sel)

    async def _sel(self, inter: discord.Interaction):
        if inter.user.id != self.user_id:
            await inter.response.send_message("Nao e seu personagem!", ephemeral=True)
            return
        selecionadas = inter.data["values"][:4]
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM skills_equipadas WHERE user_id=$1", self.user_id)
            for slot, sid in enumerate(selecionadas):
                await conn.execute(
                    "INSERT INTO skills_equipadas(user_id,skill_id,slot) VALUES($1,$2,$3) ON CONFLICT(user_id,slot) DO UPDATE SET skill_id=EXCLUDED.skill_id",
                    self.user_id, sid, slot
                )
        nomes = [s["nome"] for s in self.skills if s["id"] in selecionadas]
        await inter.response.edit_message(
            embed=discord.Embed(
                title="Skills atualizadas!",
                description="\n".join([f"• {n}" for n in nomes]),
                color=0x1D9E75
            ),
            view=None
        )


class BatalhaView(discord.ui.View):
    def __init__(self, user_id, skills, pocoes, nivel=1):
        super().__init__(timeout=30)
        self.user_id = user_id
        self.acao = None
        self.acao_feita = False
        self._pocoes = list(pocoes) if pocoes else []
        self._skills = list(skills) if skills else []

        if nivel <= 9:
            max_slots = 2
        elif nivel <= 19:
            max_slots = 3
        else:
            max_slots = 4

        for i, sk in enumerate(skills[:max_slots]):
            mana_txt = f" ({sk.get('mana', 0)}💙)" if sk.get("mana", 0) > 0 else ""
            btn = discord.ui.Button(
                label=f"{sk['emoji']} {sk['nome']}{mana_txt}",
                style=discord.ButtonStyle.primary,
                row=i // 2,
                custom_id=f"skill_{i}"
            )
            btn.callback = self._fazer_skill(i)
            self.add_item(btn)
        self._max_slots = max_slots

        atk_btn = discord.ui.Button(
            label="⚔️ Ataque Básico",
            style=discord.ButtonStyle.secondary,
            row=2,
            custom_id="atk_basico"
        )
        atk_btn.callback = self._atk_basico
        self.add_item(atk_btn)

        def_btn = discord.ui.Button(
            label="🛡️ Defesa",
            style=discord.ButtonStyle.secondary,
            row=2,
            custom_id="defesa_basica"
        )
        def_btn.callback = self._defesa_basica
        self.add_item(def_btn)

        mochila_btn = discord.ui.Button(
            label=f"🎒 Mochila ({len(self._pocoes)})" if self._pocoes else "🎒 Mochila (vazia)",
            style=discord.ButtonStyle.secondary,
            disabled=len(self._pocoes) == 0,
            row=3,
            custom_id="mochila"
        )
        mochila_btn.callback = self._abrir_mochila
        self.add_item(mochila_btn)

        fugir_btn = discord.ui.Button(
            label="🏃 Fugir", style=discord.ButtonStyle.danger,
            row=3, custom_id="fugir"
        )
        fugir_btn.callback = self._fugir
        self.add_item(fugir_btn)

    async def on_timeout(self):
        self.acao = ("timeout", None)
        self.stop()

    def _fazer_skill(self, idx):
        async def callback(inter: discord.Interaction):
            try:
                await inter.response.defer()
            except:
                pass
            if inter.user.id != self.user_id or self.acao_feita:
                return
            self.acao_feita = True
            self.acao = ("skill", idx)
            self.stop()
        return callback

    async def _abrir_mochila(self, inter: discord.Interaction):
        if inter.user.id != self.user_id or self.acao_feita:
            try:
                await inter.response.defer()
            except:
                pass
            return
        if not self._pocoes:
            try:
                await inter.response.send_message("Mochila vazia!", ephemeral=True)
            except:
                pass
            return
        opcoes = [
            discord.SelectOption(
                label=f"{p['emoji']} {p['nome']} (x{p['quantidade']})",
                value=p["item_id"]
            ) for p in self._pocoes[:10]
        ]
        sel = discord.ui.Select(placeholder="Qual pocao usar?", options=opcoes)
        parent = self

        async def usar(inter2: discord.Interaction):
            try:
                await inter2.response.defer()
            except:
                pass
            if inter2.user.id != parent.user_id or parent.acao_feita:
                return
            parent.acao_feita = True
            parent.acao = ("pocao", inter2.data["values"][0])
            parent.stop()

        sel.callback = usar
        v = discord.ui.View(timeout=20)
        v.add_item(sel)
        try:
            await inter.response.send_message("Escolha a pocao:", view=v, ephemeral=True)
        except:
            pass

    async def _atk_basico(self, inter: discord.Interaction):
        try:
            await inter.response.defer()
        except:
            pass
        if inter.user.id != self.user_id or self.acao_feita:
            return
        self.acao_feita = True
        self.acao = ("atk_basico", None)
        self.stop()

    async def _defesa_basica(self, inter: discord.Interaction):
        try:
            await inter.response.defer()
        except:
            pass
        if inter.user.id != self.user_id or self.acao_feita:
            return
        self.acao_feita = True
        self.acao = ("defesa_basica", None)
        self.stop()

    async def _fugir(self, inter: discord.Interaction):
        try:
            await inter.response.defer()
        except:
            pass
        if inter.user.id != self.user_id or self.acao_feita:
            return
        self.acao_feita = True
        self.acao = ("fugir", None)
        self.stop()


# ─── ENGINE DE TREINO COM INTEGRAÇÃO DE PARTY ─────────────────────

RANK_BONUS = {
    "E": {"hp": 20, "mana": 15, "atk": 5, "dfs": 3},
    "D": {"hp": 35, "mana": 25, "atk": 8, "dfs": 5},
    "C": {"hp": 55, "mana": 40, "atk": 14, "dfs": 9},
    "B": {"hp": 80, "mana": 60, "atk": 22, "dfs": 14},
    "A": {"hp": 120, "mana": 90, "atk": 35, "dfs": 22},
    "S": {"hp": 180, "mana": 130, "atk": 55, "dfs": 35},
    "SS": {"hp": 280, "mana": 200, "atk": 85, "dfs": 55},
}


async def notificar_level_up(guild, user_id, nome, classe_id, nivel_novo, rank_mudou, rank_obj,
                              hp_bonus, mana_bonus, atk_bonus, def_bonus):
    """Manda embed de level up no canal privado do jogador."""
    if not guild:
        return
    try:
        emoji_cls = EMOJI_CLASSE.get(classe_id, "⚔️")
        nome_lower = nome.lower()[:20]
        canal = None
        cat = discord.utils.get(guild.categories, name="MEU PERFIL")
        if cat:
            for ch in cat.channels:
                if nome_lower in ch.name.lower():
                    canal = ch
                    break
        if not canal:
            return
        cor = rank_obj["cor"] if "cor" in rank_obj else 0xE4AF3C
        embed = discord.Embed(
            title=f"🎉 LEVEL UP! {emoji_cls} {nome}",
            description=f"Voce subiu para o **Nivel {nivel_novo}**!",
            color=0xE4AF3C
        )
        embed.add_field(name="Ganhos", value=f"+{hp_bonus} HP Max | +{mana_bonus} Mana | +{atk_bonus} ATK | +{def_bonus} DEF", inline=False)
        if rank_mudou:
            embed.add_field(name="RANK UP!", value=f"{rank_obj['emoji']} Rank {rank_obj['rank']} — {rank_obj['nome']}", inline=False)
        embed.set_footer(text="Continue sua jornada em Villa Eldoria!")
        member = guild.get_member(user_id)
        mention = member.mention if member else ""
        await canal.send(content=mention, embed=embed)
    except Exception as e:
        print(f"Erro notif level up: {e}")


async def (interaction: discord.Interaction, p, monstro, arena):
    uid = p["user_id"]

    # Verifica cooldown
    pode, tempo = cooldown_manager.check(uid, "treinar", COOLDOWN_BATALHA)
    if not pode:
        await interaction.followup.send(f"⏰ Aguarde **{tempo} segundos** antes de treinar novamente!", ephemeral=True)
        return

    BATALHAS_ATIVAS.add(uid)

    # Skills
    ids_eq = await get_skills_eq(uid)
    if not ids_eq:
        ids_eq = []
    skills = [get_skill_resolv(p["classe_id"], sid) for sid in ids_eq if get_skill_resolv(p["classe_id"], sid)]
    if not skills:
        default = SKILLS_COMPLETAS.get(p["classe_id"], [])
        skills = default[:4]

    # Equipamento
    arma = await get_arma_equipada(uid)
    armadura = await get_armadura_equipada(uid)
    bonus_atk, bonus_dfs = calcular_bonus_equip(p["classe_id"], arma, armadura)

    arma_txt = f"{arma['emoji']} {arma['nome']}" if arma else "Sem arma"
    armadura_txt = f"{armadura['emoji']} {armadura['nome']}" if armadura else "Sem armadura"
    compat_arma = "✅ +15%" if bonus_atk > 1 else ("❌ -15%" if bonus_atk < 1 else "—")
    compat_arm = "✅ +10%" if bonus_dfs > 1 else ("❌ -10%" if bonus_dfs < 1 else "—")

    # Stats iniciais
    hp_j = p["hp_atual"]
    hp_jmx = p["hp_max"]
    mana_j = p["mana_atual"] if p["mana_atual"] else 100
    mana_jmx = p["mana_max"] if p["mana_max"] else 100
    hp_m = monstro["hp"]
    hp_mmx = monstro["hp"]
    turno = 1
    efeitos_j = {}
    efeitos_m = {}
    passiva = Passiva(p["classe_id"])
    passiva_racial = PassivaRacial(p.get("raca_id", "humano"))
    ressuscitou = False
    tomou_dano = False
    emoji_j = EMOJI_CLASSE.get(p["classe_id"], "⚔️")
    msgs_batalha = []
    timeout_count = 0

    def barra_status():
        ef_txt = ""
        ativos = [k for k, v in efeitos_j.items() if (v["duracao"] if isinstance(v, dict) else v) > 0]
        if ativos:
            ef_txt = f"\n🔮 Efeitos: {', '.join(ativos)}"
        return (
            f"{emoji_j} **{p['nome']}** ❤️`{barra_hp(hp_j, hp_jmx)}`**{hp_j}/{hp_jmx}** 💙{mana_j}/{mana_jmx}{ef_txt}\n"
            f"{monstro['emoji']} **{monstro['nome']}** ❤️`{barra_hp(hp_m, hp_mmx)}`**{hp_m}/{hp_mmx}**"
        )

    img_monstro = monstro.get("img", IMG_MONSTRO.get(monstro.get("id", ""), IMG_MONSTRO["default"]))
    embed_monstro = discord.Embed(
        title=f"{monstro['emoji']} {monstro['nome']} aparece!",
        description=(
            f"**{emoji_j} {p['nome']}** vs **{monstro['emoji']} {monstro['nome']}**\n\n"
            f"{barra_status()}\n\n"
            f"⚔️ {arma_txt} {compat_arma} | 🛡️ {armadura_txt} {compat_arm}"
        ),
        color=arena["cor"]
    )
    if img_monstro:
        embed_monstro.set_image(url=img_monstro)
    msgs_batalha.append(await interaction.followup.send(embed=embed_monstro, wait=True))
    await asyncio.sleep(1)

    # ─── LOOP DE BATALHA ─────────────────────────────────────────

    while hp_j > 0 and hp_m > 0:
        mana_antes = mana_j

        # 1. Efeitos de status no jogador
        dano_ef, msgs_ef, efeitos_j = processar_efeitos_turno(efeitos_j)
        if dano_ef > 0:
            hp_j = max(0, hp_j - dano_ef)
        # Efeitos no monstro
        dano_ef_m, msgs_ef_m, efeitos_m = processar_efeitos_turno(efeitos_m)
        if dano_ef_m > 0:
            hp_m = max(0, hp_m - dano_ef_m)

        # 2. Passiva inicio de turno
        tomou_dano = False
        cura_passiva = passiva.inicio_turno(hp_j, hp_jmx)
        if cura_passiva > 0:
            hp_j = min(hp_jmx, hp_j + cura_passiva)

        if hp_m <= 0:
            break

        # 3. Pocoes disponíveis
        pocoes = await get_pocoes_inv(uid)
        view = BatalhaView(uid, skills, pocoes, nivel=p["nivel"])

        passiva_txt = passiva.desc_passiva()
        embed_vez = discord.Embed(
            title=f"🎮 Turno {turno} — Sua vez!",
            description=barra_status() + (f"\n{passiva_txt}" if passiva_txt else ""),
            color=0x7F77DD
        )
        if msgs_ef:
            embed_vez.add_field(name="Efeitos de status", value="\n".join(msgs_ef), inline=False)
        if msgs_ef_m:
            embed_vez.add_field(name="Efeitos no inimigo", value="\n".join(msgs_ef_m), inline=False)

        msg_vez = await interaction.followup.send(embed=embed_vez, view=view, wait=True)
        msgs_batalha.append(msg_vez)
        await view.wait()

        acao, val = view.acao or ("timeout", None)
        nivel_p = p["nivel"]
        try:
            await msg_vez.edit(view=None)
        except:
            pass

        # 4. Inatividade
        if acao == "timeout":
            timeout_count += 1
            if timeout_count >= 3:
                embed_exp = discord.Embed(
                    title="💤 Expulso por inatividade!",
                    description=f"**{p['nome']}** ficou inativo por 3 turnos!\nNenhuma recompensa.",
                    color=0x888780
                )
                await interaction.followup.send(embed=embed_exp)
                BATALHAS_ATIVAS.discard(uid)
                return
            else:
                aviso = discord.Embed(
                    title=f"⏰ Turno perdido! ({timeout_count}/3)",
                    description=f"Sem acao em 30s. Mais **{3 - timeout_count}x** = expulso!",
                    color=0xE4AF3C
                )
                await interaction.followup.send(embed=aviso)
                turno += 1
                continue
        else:
            timeout_count = 0

        # 5. Processa acao
        linha_jogador = ""
        cor_acao = arena["cor"]

        if acao == "fugir":
            embed_fuga = discord.Embed(
                title="🏃 Voce fugiu!",
                description=f"Escapou de **{monstro['emoji']} {monstro['nome']}**!\nNenhuma recompensa.",
                color=0x888780
            )
            if IMG_DERROTA:
                embed_fuga.set_image(url=IMG_DERROTA)
            await interaction.followup.send(embed=embed_fuga)
            BATALHAS_ATIVAS.discard(uid)
            for m in msgs_batalha:
                try:
                    await m.delete()
                except:
                    pass
            return

        elif acao == "atk_basico":
            if nivel_p <= 9:
                mult_basico = 1.0
            elif nivel_p <= 19:
                mult_basico = 1.1
            elif nivel_p <= 29:
                mult_basico = 1.2
            elif nivel_p <= 39:
                mult_basico = 1.3
            elif nivel_p <= 49:
                mult_basico = 1.4
            elif nivel_p <= 59:
                mult_basico = 1.5
            elif nivel_p <= 74:
                mult_basico = 1.6
            else:
                mult_basico = 1.8
            dano = calc_dano(p["ataque"], monstro["defesa"], mult_basico,
                             bonus_atk=bonus_atk, nivel=p["nivel"], hp_max_monstro=hp_mmx)
            hp_m = max(0, hp_m - dano)
            linha_jogador = f"⚔️ **Ataque Básico**: **{dano} de dano**! *(sem custo de mana)*"
            cor_acao = 0x888780

        elif acao == "defesa_basica":
            add_efeito(efeitos_j, "defesa_basica", 1, valor=0)
            linha_jogador = f"🛡️ **Postura Defensiva!** 60% de chance de reduzir 80% do dano no próximo ataque. *(sem custo de mana)*"
            cor_acao = 0x378ADD

        elif acao == "timeout":
            if nivel_p <= 9:
                mult_basico = 1.0
            elif nivel_p <= 19:
                mult_basico = 1.1
            elif nivel_p <= 29:
                mult_basico = 1.2
            elif nivel_p <= 39:
                mult_basico = 1.3
            elif nivel_p <= 49:
                mult_basico = 1.4
            elif nivel_p <= 59:
                mult_basico = 1.5
            elif nivel_p <= 74:
                mult_basico = 1.6
            else:
                mult_basico = 1.8
            dano = calc_dano(p["ataque"], monstro["defesa"], mult_basico,
                             bonus_atk=bonus_atk, nivel=p["nivel"], hp_max_monstro=hp_mmx)
            hp_m = max(0, hp_m - dano)
            linha_jogador = f"⏰ Tempo! ⚔️ **Ataque Básico** (auto): **{dano} de dano**!"

        elif acao == "pocao":
            hp_j, mana_j, linha_jogador = aplicar_efeito_pocao(val, hp_j, hp_jmx, mana_j, mana_jmx)
            await remover_pocao(uid, val)
            cor_acao = 0x2ecc71

        elif acao == "skill":
            sk = skills[val] if val < len(skills) else skills[0]
            custo = sk.get("mana", 0)
            efeito = sk.get("efeito")

            if mana_j < custo:
                linha_jogador = f"⚠️ Mana insuficiente para **{sk['nome']}**! Ataque basico."
                dano = calc_dano(p["ataque"], monstro["defesa"], 1.0, bonus_atk=bonus_atk)
                hp_m = max(0, hp_m - dano)
                linha_jogador += f" **{dano} de dano**."
            else:
                mana_j -= custo

                if efeito == "cura":
                    cura = int(hp_jmx * 0.35)
                    hp_j = min(hp_jmx, hp_j + cura)
                    linha_jogador = f"{sk['emoji']} **{sk['nome']}**: +{cura} HP! ❤️"
                    cor_acao = 0x2ecc71

                elif efeito == "cura_grande":
                    cura = int(hp_jmx * 0.60)
                    hp_j = min(hp_jmx, hp_j + cura)
                    linha_jogador = f"{sk['emoji']} **{sk['nome']}**: +{cura} HP! ❤️"
                    cor_acao = 0x2ecc71

                elif efeito in ("defesa", "escudo", "esquiva", "escudo_total", "armadura", "reflexo"):
                    nomes_ef = {
                        "defesa": "Postura defensiva! -50% dano por 1 turno.",
                        "escudo": "Escudo arcano! Absorve próximo ataque.",
                        "esquiva": "Esquiva pronta! Evitará próximo ataque.",
                        "escudo_total": "Escudo total! Bloqueia próximos 2 ataques.",
                        "armadura": "Escamas! -35% dano por 3 turnos.",
                        "reflexo": "Campo de força! Reflete 40% do dano por 2 turnos.",
                    }
                    duracao = 2 if efeito in ("escudo_total",) else (3 if efeito == "armadura" else 1)
                    add_efeito(efeitos_j, efeito, duracao)
                    linha_jogador = f"{sk['emoji']} **{sk['nome']}**! {nomes_ef.get(efeito, 'Efeito ativo!')}"
                    cor_acao = 0x7F77DD

                elif efeito == "dreno":
                    mult_dreno = passiva.apos_dreno()
                    dano = calc_dano(p["ataque"], monstro["defesa"], sk.get("dano", 1.0), bonus_atk=bonus_atk, nivel=p["nivel"], hp_max_monstro=hp_mmx)
                    roubo = int(dano // 2 * mult_dreno)
                    hp_m = max(0, hp_m - dano)
                    hp_j = min(hp_jmx, hp_j + roubo)
                    linha_jogador = f"{sk['emoji']} **{sk['nome']}**: **{dano} de dano** e drenou **+{roubo} HP**! (x{mult_dreno:.1f})"
                    cor_acao = 0x1D9E75

                elif efeito in ("buff_ataque", "buff_all", "berserker"):
                    add_efeito(efeitos_j, efeito, 3)
                    bonus_txt = "+35% ATK" if efeito == "buff_ataque" else ("+25% ATK e DEF" if efeito == "buff_all" else "+60% ATK com regeneração")
                    linha_jogador = f"{sk['emoji']} **{sk['nome']}**: {bonus_txt} por 3 turnos! 🔥"
                    cor_acao = 0xD85A30

                elif efeito in ("queimadura", "veneno"):
                    dano = calc_dano(p["ataque"], monstro["defesa"], sk.get("dano", 1.0), bonus_atk=bonus_atk)
                    dano = int(dano * passiva.multiplicador_dano())
                    hp_m = max(0, hp_m - dano)
                    if not passiva.imune_status(efeito):
                        add_efeito(efeitos_m, efeito, 3, valor=max(5, dano // 4))
                    emoji_ef = "🔥" if efeito == "queimadura" else "☠️"
                    linha_jogador = f"{sk['emoji']} **{sk['nome']}**: **{dano} de dano**! {emoji_ef} Inimigo ficou com {efeito}!"
                    cor_acao = 0xD85A30

                elif efeito in ("atordoar", "paralisia", "congelar"):
                    dano = calc_dano(p["ataque"], monstro["defesa"], sk.get("dano", 1.0), bonus_atk=bonus_atk, nivel=p["nivel"], hp_max_monstro=hp_mmx, passiva_mult=passiva.multiplicador_dano())
                    hp_m = max(0, hp_m - dano)
                    if random.random() < 0.40:
                        add_efeito(efeitos_m, "atordoado", 1)
                        linha_jogador = f"{sk['emoji']} **{sk['nome']}**: **{dano} de dano** + inimigo **atordoado** por 1 turno! 💫"
                    else:
                        linha_jogador = f"{sk['emoji']} **{sk['nome']}**: **{dano} de dano**! (não atordoou)"
                    cor_acao = 0xE4AF3C

                elif efeito in ("hits2", "hits3", "hits4", "hits5"):
                    n_hits = int(efeito.replace("hits", ""))
                    dano_total = 0
                    cap_por_hit = int(hp_mmx * 0.20) if hp_mmx else 999
                    for _ in range(n_hits):
                        d = calc_dano(p["ataque"], monstro["defesa"], sk.get("dano", 0.6), bonus_atk=bonus_atk, nivel=p["nivel"], passiva_mult=passiva.multiplicador_dano())
                        dano_total += min(d, cap_por_hit)
                    dano_total = min(dano_total, int(hp_mmx * 0.70) if hp_mmx else dano_total)
                    hp_m = max(0, hp_m - dano_total)
                    linha_jogador = f"{sk['emoji']} **{sk['nome']}**: {n_hits} golpes → **{dano_total} de dano total**!"
                    cor_acao = 0xD85A30

                elif efeito == "ignorar_defesa":
                    dano = calc_dano(p["ataque"], monstro["defesa"], sk.get("dano", 1.0), bonus_atk=bonus_atk, ignorar_defesa=True, nivel=p["nivel"], hp_max_monstro=hp_mmx, passiva_mult=passiva.multiplicador_dano())
                    hp_m = max(0, hp_m - dano)
                    linha_jogador = f"{sk['emoji']} **{sk['nome']}**: **{dano} de dano** (ignora defesa)! 🔱"
                    cor_acao = 0x7F77DD

                elif efeito == "critico_bonus":
                    crit = random.random() < 0.55
                    dano = calc_dano(p["ataque"], monstro["defesa"], sk.get("dano", 1.0), crit=crit, bonus_atk=bonus_atk, nivel=p["nivel"], hp_max_monstro=hp_mmx, passiva_mult=passiva.multiplicador_dano())
                    hp_m = max(0, hp_m - dano)
                    if crit:
                        mana_j = min(mana_jmx, mana_j + passiva.apos_critico())
                    linha_jogador = f"{sk['emoji']} **{sk['nome']}**: **{dano} de dano**{'💥 CRÍTICO!' if crit else ''}!"
                    cor_acao = 0xE4AF3C if crit else arena["cor"]

                elif efeito == "instakill_chance":
                    if random.random() < 0.20:
                        hp_m = 0
                        linha_jogador = f"{sk['emoji']} **{sk['nome']}**: 💀 **MORTE INSTANTÂNEA!**"
                        cor_acao = 0x7F77DD
                    else:
                        dano = calc_dano(p["ataque"], monstro["defesa"], sk.get("dano", 1.0), bonus_atk=bonus_atk, nivel=p["nivel"], hp_max_monstro=hp_mmx)
                        hp_m = max(0, hp_m - dano)
                        linha_jogador = f"{sk['emoji']} **{sk['nome']}**: **{dano} de dano** (não instakill)"

                else:
                    crit = random.random() < 0.15
                    mult = sk.get("dano", 1.0) * passiva.multiplicador_dano()
                    dano = calc_dano(p["ataque"], monstro["defesa"], mult, crit=crit, bonus_atk=bonus_atk)
                    hp_m = max(0, hp_m - dano)
                    if crit:
                        mana_j = min(mana_jmx, mana_j + passiva.apos_critico())
                    critico_txt = " **💥 CRÍTICO!**" if crit else ""
                    passiva_bonus_txt = f" *(passiva +{int((passiva.multiplicador_dano() - 1) * 100)}%)*" if passiva.multiplicador_dano() > 1.0 else ""
                    linha_jogador = f"{sk['emoji']} **{sk['nome']}**: **{dano} de dano**{critico_txt}{passiva_bonus_txt}!"
                    cor_acao = 0xD85A30 if crit else arena["cor"]

        embed_acao = discord.Embed(
            title=f"⚔️ {emoji_j} {p['nome']} age!",
            description=f"{linha_jogador}\n\n{barra_status()}",
            color=cor_acao
        )
        msgs_batalha.append(await interaction.followup.send(embed=embed_acao, wait=True))

        if hp_m <= 0:
            break

        await asyncio.sleep(1.2)

        # ─── TURNO DO MONSTRO ─────────────────────────────────────

        if efeito_ativo(efeitos_m, "atordoado"):
            linha_monstro = f"{monstro['emoji']} **{monstro['nome']}** está **atordoado** e não pode atacar! 💫"
            cor_monstro = 0x888780
        else:
            sk_m = random.choice(monstro["skills"])
            def_total = int(p["defesa"] * bonus_dfs) + passiva.bonus_defesa_fixa()
            if efeito_ativo(efeitos_j, "armadura") or efeito_ativo(efeitos_j, "buff_all"):
                def_total = int(def_total * 1.35)
            dano_m_base = calc_dano(monstro["ataque"], def_total)
            reducao = passiva.reducao_dano()
            dano_m = max(1, int(dano_m_base * (1.0 - reducao)))
            cor_monstro = 0xE24B4A

            if efeito_ativo(efeitos_j, "esquiva"):
                linha_monstro = f"{monstro['emoji']} **{monstro['nome']}** usou **{sk_m['emoji']} {sk_m['nome']}**... mas você **esquivou!** 💨"
                efeitos_j["esquiva"]["duracao"] = 0
                cor_monstro = 0x888780

            elif efeito_ativo(efeitos_j, "escudo") or efeito_ativo(efeitos_j, "escudo_total"):
                linha_monstro = f"{monstro['emoji']} **{monstro['nome']}** usou **{sk_m['emoji']} {sk_m['nome']}**... mas o **escudo absorveu!** 💜"
                ef_key = "escudo_total" if efeito_ativo(efeitos_j, "escudo_total") else "escudo"
                efeitos_j[ef_key]["duracao"] -= 1
                cor_monstro = 0x7F77DD

            elif efeito_ativo(efeitos_j, "defesa_basica"):
                efeitos_j["defesa_basica"]["duracao"] = 0
                if random.random() < 0.60:
                    dano_m = max(1, int(dano_m * 0.20))
                    hp_j = max(0, hp_j - dano_m)
                    tomou_dano = True
                    passiva.apos_tomar_dano()
                    linha_monstro = f"{monstro['emoji']} **{monstro['nome']}** usou **{sk_m['emoji']} {sk_m['nome']}**: **{dano_m} de dano** (🛡️ Defesa funcionou! -80% dano!)"
                else:
                    hp_j = max(0, hp_j - dano_m)
                    tomou_dano = True
                    passiva.apos_tomar_dano()
                    linha_monstro = f"{monstro['emoji']} **{monstro['nome']}** usou **{sk_m['emoji']} {sk_m['nome']}**: **{dano_m} de dano** (❌ Defesa falhou! Dano total!)"

            elif efeito_ativo(efeitos_j, "defesa"):
                dano_m = max(1, dano_m // 2)
                hp_j = max(0, hp_j - dano_m)
                tomou_dano = True
                passiva.apos_tomar_dano()
                efeitos_j["defesa"]["duracao"] -= 1
                linha_monstro = f"{monstro['emoji']} **{monstro['nome']}** usou **{sk_m['emoji']} {sk_m['nome']}**: **{dano_m} de dano** (bloqueado -50%! 🛡️)"

            elif efeito_ativo(efeitos_j, "reflexo"):
                refletido = int(dano_m * 0.40)
                hp_m = max(0, hp_m - refletido)
                hp_j = max(0, hp_j - (dano_m - refletido))
                tomou_dano = True
                passiva.apos_tomar_dano()
                efeitos_j["reflexo"]["duracao"] -= 1
                linha_monstro = f"{monstro['emoji']} **{monstro['nome']}** usou **{sk_m['emoji']} {sk_m['nome']}**: {dano_m} dano! Refletiu **{refletido}** de volta! 🔮"

            else:
                hp_j -= dano_m
                hp_j = max(0, hp_j)
                tomou_dano = True
                passiva.apos_tomar_dano()
                reducao_txt = f" (-10% dragão)" if reducao > 0 else ""
                linha_monstro = f"{monstro['emoji']} **{monstro['nome']}** usou **{sk_m['emoji']} {sk_m['nome']}**: **{dano_m} de dano**{reducao_txt}!"

        if not tomou_dano:
            passiva.fim_turno_sem_dano()

        # Regen de mana por turno
        nivel_p = p["nivel"]
        if nivel_p <= 9:
            regen_mana = 3
        elif nivel_p <= 19:
            regen_mana = 5
        elif nivel_p <= 29:
            regen_mana = 8
        elif nivel_p <= 39:
            regen_mana = 12
        elif nivel_p <= 49:
            regen_mana = 16
        elif nivel_p <= 59:
            regen_mana = 22
        elif nivel_p <= 74:
            regen_mana = 30
        else:
            regen_mana = 40
        mana_j = min(mana_jmx, mana_j + regen_mana)

        regen_txt = f"\n💙 +{regen_mana} mana regenerada ({mana_j}/{mana_jmx})" if mana_j > mana_antes else ""

        embed_m = discord.Embed(
            title=f"{monstro['emoji']} {monstro['nome']} age!",
            description=f"{linha_monstro}\n\n{barra_status()}{regen_txt}",
            color=cor_monstro
        )
        msgs_batalha.append(await interaction.followup.send(embed=embed_m, wait=True))

        turno += 1
        await asyncio.sleep(1.0)

    # ─── RESULTADO ─────────────────────────────────────────────
    BATALHAS_ATIVAS.discard(uid)
    vitoria = hp_m <= 0

    # NOVO: Calcular bônus de party
    bonus_party = 0
    try:
        from party import get_bonus_party, registrar_batalha_party
        bonus_party = await get_bonus_party([interaction.user.id], interaction.guild)
        await registrar_batalha_party([interaction.user.id], vitoria, interaction.guild)
    except ImportError:
        pass
    except Exception as e:
        print(f"Erro ao integrar party: {e}")

    if vitoria:
        _chance_loot = {"facil": 0.15, "medio": 0.22, "dificil": 0.30, "lendario": 0.40}
        _chance = _chance_loot.get(monstro.get("dificuldade", "facil"), 0.20)
        loot = [random.choice(monstro["loot"])] if random.random() < _chance else []

        # Aplica bônus de party no XP
        xp_base = monstro["xp"]
        xp_com_bonus = xp_base + int(xp_base * bonus_party / 100)

        lvlups, nivel_novo, rank_mudou, rank_obj = await salvar_resultado(
            uid, hp_j, xp_com_bonus, 5, True, p["classe_id"], p["nivel"], mana_j
        )
        if loot:
            await add_loot(uid, loot)

        desc = (
            f"🏆 Você derrotou **{monstro['emoji']} {monstro['nome']}**!\n\n"
            f"✨ **+{xp_com_bonus} XP** | 💰 **+5 moedas**\n📦 Venda o loot no `/mercado` para mais moedas!"
        )
        if bonus_party > 0:
            desc += f"\n\n🤝 **Bônus de Party: +{bonus_party}% XP!**"
        if loot:
            desc += f"\n🎁 Loot: {loot[0][4]} **{loot[0][1]}** [{loot[0][3]}]"
        if lvlups:
            if rank_mudou:
                b = RANK_BONUS.get(rank_obj["rank"], {})
                rank_txt = (f" | 🏅 **RANK UP: {rank_obj['emoji']} {rank_obj['rank']}!**"
                           f"\n🎁 Bonus: +{b.get('hp', 0)} HP | +{b.get('mana', 0)} Mana | +{b.get('atk', 0)} ATK | +{b.get('dfs', 0)} DEF")
            else:
                rank_txt = ""
            desc += f"\n\n⬆️ **LEVEL UP x{lvlups}! → Nível {nivel_novo}**{rank_txt}\n+{12 * lvlups} HP máx | +{10 * lvlups} Mana | +{2 * lvlups} ATK | +{lvlups} DEF 🎊"

        # Missoes
        try:
            from missoes import atualizar_progresso
            recomps = await atualizar_progresso(uid, "vitorias_treino")
            if monstro["dificuldade"] in ("dificil", "lendario"):
                await atualizar_progresso(uid, "treino_hard")
            if loot:
                await atualizar_progresso(uid, "loots_coletados")
            await atualizar_progresso(uid, "skills_usadas")
            for rm in recomps:
                desc += f"\n\n🎯 **Missão concluída!** {rm['descricao']}\n+{rm['xp']} XP | +{rm['moedas']} 🪙"
        except Exception:
            pass

        # Conquistas
        try:
            from conquistas import verificar_conquistas
            from db import get_pool as _gp
            _pool = await _gp()
            async with _pool.acquire() as _conn:
                _p2 = await _conn.fetchrow("SELECT vitorias, moedas FROM personagens WHERE user_id=$1", uid)
            cqs_vit = await verificar_conquistas(uid, "vitorias", _p2["vitorias"] if _p2 else 0)
            cqs_mon = await verificar_conquistas(uid, "moedas", _p2["moedas"] if _p2 else 0)
            cqs_rnk = await verificar_conquistas(uid, "rank", nivel_novo)
            for cq in (cqs_vit + cqs_mon + cqs_rnk):
                desc += f"\n\n🏆 **Conquista desbloqueada!** {cq['emoji']} {cq['nome']}\n+{cq['xp']} XP | +{cq['moedas']} 🪙"
        except Exception:
            pass

        # Atualiza cargos em todo level up
        if lvlups:
            try:
                from utils import atualizar_todos_cargos
                guild = interaction.guild
                member = guild.get_member(uid) if guild else None
                if member:
                    await atualizar_todos_cargos(guild, member, nivel_novo)
            except Exception:
                pass

        cor = 0x1D9E75
        titulo = "🏆 Vitória!"

    else:
        lvlups, nivel_novo, rank_mudou, rank_obj = await salvar_resultado(
            uid, 10, 0, 0, False, p["classe_id"], p["nivel"], mana_j
        )
        desc = (
            f"Você foi derrotado por **{monstro['emoji']} {monstro['nome']}**...\n\n"
            f"❤️ HP restaurado para **10** | 😴 Acordou na cidade\n\n"
            f"*Use /hospital para se recuperar antes da próxima batalha!*"
        )
        cor = 0xE24B4A
        titulo = "💀 Você foi derrotado!"

    fim = discord.Embed(title=titulo, description=desc, color=cor)
    img_resultado = IMG_VITORIA if vitoria else IMG_DERROTA
    if img_resultado:
        fim.set_image(url=img_resultado)
    msg_fim = await interaction.followup.send(embed=fim, wait=True)

    await asyncio.sleep(1.5)

    for m in msgs_batalha:
        try:
            await m.delete()
        except:
            pass

    await asyncio.sleep(300)
    try:
        await msg_fim.delete()
    except:
        pass

    # NOVO: Aplicar cooldown
    cooldown_manager.set(uid, "treinar", COOLDOWN_BATALHA)


# ─── ENGINE PVP COM CALLBACK ─────────────────────────────────────

async def rodar_pvp(channel, p1, p2, m1, m2, arena, callback=None):
    uid1, uid2 = p1["user_id"], p2["user_id"]

    async def pegar_skills(p, uid):
        ids = await get_skills_eq(uid)
        sks = [get_skill_resolv(p["classe_id"], sid) for sid in ids if get_skill_resolv(p["classe_id"], sid)]
        if not sks:
            sks = SKILLS_COMPLETAS.get(p["classe_id"], [])[:4]
        return sks

    skills1 = await pegar_skills(p1, uid1)
    skills2 = await pegar_skills(p2, uid2)

    arma1 = await get_arma_equipada(uid1)
    armadura1 = await get_armadura_equipada(uid1)
    arma2 = await get_arma_equipada(uid2)
    armadura2 = await get_armadura_equipada(uid2)

    bonus_atk1, bonus_dfs1 = calcular_bonus_equip(p1["classe_id"], arma1, armadura1)
    bonus_atk2, bonus_dfs2 = calcular_bonus_equip(p2["classe_id"], arma2, armadura2)

    hp1 = p1["hp_atual"]
    hp1mx = p1["hp_max"]
    hp2 = p2["hp_atual"]
    hp2mx = p2["hp_max"]
    mana1 = p1["mana_atual"] or 100
    mana1mx = p1["mana_max"] or 100
    mana2 = p2["mana_atual"] or 100
    mana2mx = p2["mana_max"] or 100
    turno = 1
    efeitos1 = {}
    efeitos2 = {}
    passiva1 = Passiva(p1["classe_id"])
    passiva2 = Passiva(p2["classe_id"])
    msgs = []
    e1 = EMOJI_CLASSE.get(p1["classe_id"], "⚔️")
    e2 = EMOJI_CLASSE.get(p2["classe_id"], "⚔️")
    timeout1 = 0
    timeout2 = 0

    def barra_status_pvp():
        return (
            f"{e1} **{p1['nome']}** ❤️`{barra_hp(hp1, hp1mx)}`**{hp1}/{hp1mx}** 💙{mana1}/{mana1mx}\n"
            f"{e2} **{p2['nome']}** ❤️`{barra_hp(hp2, hp2mx)}`**{hp2}/{hp2mx}** 💙{mana2}/{mana2mx}"
        )

    embed_ini = discord.Embed(
        title=f"⚔️ Duelo PvP — {arena['emoji']} {arena['nome']}",
        description=f"**{m1.mention}** vs **{m2.mention}**\n\n{barra_status_pvp()}",
        color=arena["cor"]
    )
    if arena.get("img"):
        embed_ini.set_image(url=arena["img"])
    msgs.append(await channel.send(embed=embed_ini))

    for t in range(1, 21):
        if hp1 <= 0 or hp2 <= 0:
            break

        # Turno p1
        pocoes1 = await get_pocoes_inv(uid1)
        view1 = BatalhaView(uid1, skills1, pocoes1)
        embed_v1 = discord.Embed(
            title=f"🎮 Turno {t} — {e1} {p1['nome']}, sua vez!",
            description=barra_status_pvp(),
            color=0x7F77DD
        )
        msg_v1 = await channel.send(content=m1.mention, embed=embed_v1, view=view1)
        msgs.append(msg_v1)
        await view1.wait()

        try:
            await msg_v1.edit(view=None)
        except:
            pass

        acao1, val1 = view1.acao or ("timeout", None)
        linha = ""
        if acao1 == "atk_basico":
            mult_b = 1.0 + (p1["nivel"] // 10) * 0.1
            dano = calc_dano(p1["ataque"], p2["defesa"], mult_b, bonus_atk=bonus_atk1)
            hp2 = max(0, hp2 - dano)
            linha = f"{e1} Ataque Basico: **{dano} de dano**!"
        elif acao1 == "defesa_basica":
            add_efeito(efeitos1, "defesa_basica", 1)
            linha = f"{e1} Postura defensiva!"
        elif acao1 == "skill" and val1 is not None:
            sk = skills1[val1] if val1 < len(skills1) else skills1[0]
            if mana1 >= sk.get("mana", 0):
                mana1 -= sk.get("mana", 0)
                dano = calc_dano(p1["ataque"], p2["defesa"], sk.get("dano", 1.0), bonus_atk=bonus_atk1)
                dano = int(dano * passiva1.multiplicador_dano())
                hp2 = max(0, hp2 - dano)
                linha = f"{e1} {sk['emoji']} **{sk['nome']}**: **{dano} de dano**!"
            else:
                dano = calc_dano(p1["ataque"], p2["defesa"], bonus_atk=bonus_atk1)
                hp2 = max(0, hp2 - dano)
                linha = f"{e1} Sem mana! Ataque basico: **{dano} de dano**."
        elif acao1 == "pocao" and val1:
            hp1, mana1, linha = aplicar_efeito_pocao(val1, hp1, hp1mx, mana1, mana1mx)
            await remover_pocao(uid1, val1)
        elif acao1 == "fugir":
            embed_f = discord.Embed(title=f"{e1} {p1['nome']} fugiu!", description=f"Vitoria de **{p2['nome']}** por abandono!", color=0x888780)
            await channel.send(embed=embed_f)
            for m in msgs:
                try:
                    await m.delete()
                except:
                    pass
            if callback:
                await callback(p2["user_id"], p1["user_id"])
            return
        if not linha:
            dano = calc_dano(p1["ataque"], p2["defesa"], bonus_atk=bonus_atk1)
            hp2 = max(0, hp2 - dano)
            linha = f"{e1} Ataque: **{dano} de dano**!"
        elif acao1 == "timeout":
            timeout1 += 1
            if timeout1 >= 3:
                embed_f = discord.Embed(
                    title=f"💤 {p1['nome']} foi expulso por inatividade!",
                    description=f"**{p2['nome']}** vence por W.O.!",
                    color=0x888780
                )
                await channel.send(embed=embed_f)
                BATALHAS_ATIVAS.discard(uid1)
                BATALHAS_ATIVAS.discard(uid2)
                if callback:
                    await callback(p2["user_id"], p1["user_id"])
                return
            else:
                dano = calc_dano(p1["ataque"], p2["defesa"], bonus_atk=bonus_atk1)
                hp2 = max(0, hp2 - dano)
                linha = f"⏰ Auto ({timeout1}/3): **{dano} de dano**! ({3 - timeout1} inativo(s) restante(s))"
        else:
            timeout1 = 0
            dano = calc_dano(p1["ataque"], p2["defesa"], bonus_atk=bonus_atk1)
            hp2 = max(0, hp2 - dano)
            linha = f"⏰ Auto: **{dano} de dano**!"

        mana1 = min(mana1mx, mana1 + 5)
        embed_a1 = discord.Embed(
            title=f"{e1} {p1['nome']} age!",
            description=f"{linha}\n\n{barra_status_pvp()}",
            color=arena["cor"]
        )
        msgs.append(await channel.send(embed=embed_a1))

        if hp2 <= 0:
            break

        await asyncio.sleep(1.0)

        # Turno p2
        pocoes2 = await get_pocoes_inv(uid2)
        view2 = BatalhaView(uid2, skills2, pocoes2)
        embed_v2 = discord.Embed(
            title=f"🎮 Turno {t} — {e2} {p2['nome']}, sua vez!",
            description=barra_status_pvp(),
            color=0xD85A30
        )
        msg_v2 = await channel.send(content=m2.mention, embed=embed_v2, view=view2)
        msgs.append(msg_v2)
        await view2.wait()

        try:
            await msg_v2.edit(view=None)
        except:
            pass

        acao2, val2 = view2.acao or ("timeout", None)
        linha = ""
        if acao2 == "atk_basico":
            mult_b = 1.0 + (p2["nivel"] // 10) * 0.1
            dano = calc_dano(p2["ataque"], p1["defesa"], mult_b, bonus_atk=bonus_atk2)
            hp1 = max(0, hp1 - dano)
            linha = f"{e2} Ataque Basico: **{dano} de dano**!"
        elif acao2 == "defesa_basica":
            add_efeito(efeitos2, "defesa_basica", 1)
            linha = f"{e2} Postura defensiva!"
        elif acao2 == "skill" and val2 is not None:
            sk = skills2[val2] if val2 < len(skills2) else skills2[0]
            if mana2 >= sk.get("mana", 0):
                mana2 -= sk.get("mana", 0)
                dano = calc_dano(p2["ataque"], p1["defesa"], sk.get("dano", 1.0), bonus_atk=bonus_atk2)
                dano = int(dano * passiva2.multiplicador_dano())
                hp1 = max(0, hp1 - dano)
                linha = f"{e2} {sk['emoji']} **{sk['nome']}**: **{dano} de dano**!"
            else:
                dano = calc_dano(p2["ataque"], p1["defesa"], bonus_atk=bonus_atk2)
                hp1 = max(0, hp1 - dano)
                linha = f"{e2} Sem mana! Ataque basico: **{dano} de dano**."
        elif acao2 == "pocao" and val2:
            hp2, mana2, linha = aplicar_efeito_pocao(val2, hp2, hp2mx, mana2, mana2mx)
            await remover_pocao(uid2, val2)
        elif acao2 == "fugir":
            embed_f = discord.Embed(title=f"{e2} {p2['nome']} fugiu!", description=f"Vitoria de **{p1['nome']}** por abandono!", color=0x888780)
            await channel.send(embed=embed_f)
            for m in msgs:
                try:
                    await m.delete()
                except:
                    pass
            if callback:
                await callback(p1["user_id"], p2["user_id"])
            return
        else:
            timeout2 += 1
            if timeout2 >= 3:
                embed_f = discord.Embed(
                    title=f"💤 {p2['nome']} foi expulso por inatividade!",
                    description=f"**{p1['nome']}** vence por W.O.!",
                    color=0x888780
                )
                await channel.send(embed=embed_f)
                BATALHAS_ATIVAS.discard(uid1)
                BATALHAS_ATIVAS.discard(uid2)
                if callback:
                    await callback(p1["user_id"], p2["user_id"])
                return
            dano = calc_dano(p2["ataque"], p1["defesa"], bonus_atk=bonus_atk2)
            hp1 = max(0, hp1 - dano)
            linha = f"⏰ Auto ({timeout2}/3): **{dano} de dano**!"
        mana2 = min(mana2mx, mana2 + 5)
        embed_a2 = discord.Embed(
            title=f"{e2} {p2['nome']} age!",
            description=f"{linha}\n\n{barra_status_pvp()}",
            color=arena["cor"]
        )
        msgs.append(await channel.send(embed=embed_a2))
        await asyncio.sleep(1.0)

    # Resultado PvP
    if hp1 > hp2:
        vencedor, perdedor, mv, mp = p1, p2, m1, m2
        hp_v = hp1
    else:
        vencedor, perdedor, mv, mp = p2, p1, m2, m1
        hp_v = hp2

    xp_v = 80
    mo_v = 60
    await salvar_resultado(vencedor["user_id"], hp_v, xp_v, mo_v, True, vencedor["classe_id"], vencedor["nivel"])
    await salvar_resultado(perdedor["user_id"], 10, 20, 0, False, perdedor["classe_id"], perdedor["nivel"])

    fim = discord.Embed(
        title=f"🏆 {vencedor['nome']} vence o duelo!",
        description=(
            f"{mv.mention} derrotou {mp.mention}!\n\n"
            f"+{xp_v} XP | +{mo_v} 🪙 para o vencedor\n"
            f"+20 XP para o derrotado"
        ),
        color=0xE4AF3C
    )
    fim.set_image(url=IMG_VITORIA)
    await channel.send(embed=fim)

    await asyncio.sleep(1.5)

    for m in msgs:
        try:
            await m.delete()
        except:
            pass

    # NOVO: Chamar callback se existir
    if callback:
        await callback(vencedor["user_id"], perdedor["user_id"])


# ─── SKILLS_POR_CLASSE (compatibilidade) ─────────────────────────
SKILLS_POR_CLASSE = SKILLS_COMPLETAS
