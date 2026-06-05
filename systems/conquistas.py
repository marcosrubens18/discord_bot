# systems/conquistas.py — Sistema de Conquistas

import discord
from datetime import datetime, timezone
from typing import Optional, List

from database.db import get_pool
from database.queries import get_personagem
from data.ranks import get_rank
from data.constantes import EMOJI_FICHA, COR_PRIMARY, COR_SUCCESS, COR_DANGER, COR_WARNING, COR_INFO, IMG_CONQUISTAS


# ==================================================
# LISTA DE CONQUISTAS
# ==================================================

CONQUISTAS = [
    # Primeiros Passos
    ("primeira_batalha",  "Primeira Batalha",      "Vença sua primeira batalha",          "⚔️",  "vitorias",  1,    50,   30,  None),
    ("sobrevivente",      "Sobrevivente",           "Sobreviva a 10 batalhas",             "🛡️",  "vitorias",  10,   100,  60,  None),
    ("guerreiro_nato",    "Guerreiro Nato",         "Vença 50 batalhas",                   "🏆",  "vitorias",  50,   300,  200, "Incomum"),
    ("lendario_guerra",   "Lendário da Guerra",     "Vença 200 batalhas",                  "💎",  "vitorias",  200,  800,  500, "Raro"),
    ("transcendente",     "Transcendente",          "Vença 500 batalhas",                  "✨",  "vitorias",  500,  2000, 1500, "Epico"),

    # Dungeons
    ("primeiro_dungeon",  "Aventureiro Corajoso",   "Complete sua primeira dungeon",       "🏰",  "dungeons",  1,    80,   50,  None),
    ("explorador",        "Explorador",             "Complete 5 dungeons",                 "🗺️",  "dungeons",  5,    200,  120, "Incomum"),
    ("conquistador",      "Conquistador",           "Complete 20 dungeons",                "🏅",  "dungeons",  20,   500,  350, "Raro"),
    ("mestre_dungeon",    "Mestre das Dungeons",    "Complete 50 dungeons",                "👑",  "dungeons",  50,   1200, 800, "Epico"),

    # Ranks
    ("rank_e",  "Aprendiz",       "Alcance o Rank E",   "🟩", "rank", 10, 100,  80,  None),
    ("rank_d",  "Guerreiro",      "Alcance o Rank D",   "🟦", "rank", 20, 200,  150, "Incomum"),
    ("rank_c",  "Veterano",       "Alcance o Rank C",   "🟨", "rank", 30, 350,  250, "Raro"),
    ("rank_b",  "Elite",          "Alcance o Rank B",   "🟧", "rank", 40, 600,  400, "Raro"),
    ("rank_a",  "Mestre",         "Alcance o Rank A",   "🟥", "rank", 50, 1000, 700, "Epico"),
    ("rank_s",  "Lendário",       "Alcance o Rank S",   "⭐", "rank", 60, 2000, 1200, "Epico"),
    ("rank_ss", "Transcendente",  "Alcance o Rank SS",  "💎", "rank", 75, 5000, 3000, "Lendario"),

    # PvP
    ("primeiro_pvp",      "Duelista",               "Vença seu primeiro duelo PvP",        "⚔️",  "pvp_vitorias", 1,  100,  70,  None),
    ("campeao_pvp",       "Campeão",                "Vença 10 duelos PvP",                 "🏆",  "pvp_vitorias", 10, 400,  300, "Raro"),
    ("gladiador",         "Gladiador",              "Vença 50 duelos PvP",                 "👑",  "pvp_vitorias", 50, 1500, 1000, "Epico"),

    # Economia
    ("rico",              "Comerciante",            "Acumule 1.000 moedas",                "💰",  "moedas",    1000,  80,  0,   None),
    ("milionario",        "Milionário",             "Acumule 10.000 moedas",               "💎",  "moedas",    10000, 300, 0,   "Incomum"),
    ("magnata",           "Magnata",                "Acumule 100.000 moedas",              "🤑",  "moedas",    100000,1000,0,   "Raro"),

    # Missões
    ("dedicado",          "Dedicado",               "Complete 10 missões diárias",         "📋",  "missoes_completas", 10,  150, 100, None),
    ("disciplinado",      "Disciplinado",           "Complete 30 missões diárias",         "📅",  "missoes_completas", 30,  400, 300, "Incomum"),
]


# ==================================================
# FUNÇÕES AUXILIARES
# ==================================================

async def init_conquistas():
    """Inicializa a tabela de conquistas"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS conquistas (
                user_id      BIGINT,
                conquista_id TEXT,
                progresso    INTEGER DEFAULT 0,
                concluida    INTEGER DEFAULT 0,
                data         TIMESTAMP,
                PRIMARY KEY (user_id, conquista_id)
            )
        """)


async def get_conquistas_usuario(user_id: int) -> dict:
    """Retorna as conquistas do usuário"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM conquistas WHERE user_id = $1", user_id)
        return {r["conquista_id"]: r for r in rows}


async def verificar_conquistas(user_id: int, tipo: str, valor_atual: int) -> list:
    """
    Verifica e completa conquistas do tipo especificado.
    Retorna lista de conquistas completas.
    """
    pool = await get_pool()
    concluidas = []
    
    async with pool.acquire() as conn:
        for cq in CONQUISTAS:
            cid, nome, desc, emoji, cq_tipo, meta, xp, moedas, ficha = cq
            if cq_tipo != tipo:
                continue

            row = await conn.fetchrow(
                "SELECT * FROM conquistas WHERE user_id = $1 AND conquista_id = $2",
                user_id, cid
            )

            if row and row["concluida"]:
                continue

            if valor_atual >= meta:
                # Conclui a conquista
                await conn.execute("""
                    INSERT INTO conquistas (user_id, conquista_id, progresso, concluida, data)
                    VALUES ($1, $2, $3, 1, NOW())
                    ON CONFLICT (user_id, conquista_id) DO UPDATE
                    SET progresso = $3, concluida = 1, data = NOW()
                """, user_id, cid, meta)

                # Dá recompensa
                await conn.execute(
                    "UPDATE personagens SET xp = xp + $1, moedas = moedas + $2 WHERE user_id = $3",
                    xp, moedas, user_id
                )
                if ficha:
                    await conn.execute("""
                        INSERT INTO giros (user_id, roleta_id, raridade, quantidade)
                        VALUES ($1, 'skill', $2, 1)
                        ON CONFLICT (user_id, roleta_id, raridade)
                        DO UPDATE SET quantidade = giros.quantidade + 1
                    """, user_id, ficha)

                concluidas.append({
                    "nome": nome, "desc": desc, "emoji": emoji,
                    "xp": xp, "moedas": moedas, "ficha": ficha
                })
            else:
                # Atualiza progresso
                await conn.execute("""
                    INSERT INTO conquistas (user_id, conquista_id, progresso, concluida, data)
                    VALUES ($1, $2, $3, 0, NOW())
                    ON CONFLICT (user_id, conquista_id) DO UPDATE
                    SET progresso = $3
                """, user_id, cid, valor_atual)

    return concluidas


# ==================================================
# COMANDOS
# ==================================================

async def cmd_conquistas(interaction: discord.Interaction):
    """Comando /conquistas - Mostra as conquistas do jogador"""
    await interaction.response.defer(ephemeral=True)
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        p = await conn.fetchrow("SELECT * FROM personagens WHERE user_id = $1", interaction.user.id)
    
    if not p:
        await interaction.followup.send("Crie seu personagem primeiro!", ephemeral=True)
        return

    conquistas_user = await get_conquistas_usuario(interaction.user.id)
    total = len(CONQUISTAS)
    concluidas = sum(1 for c in conquistas_user.values() if c["concluida"])

    embed = discord.Embed(
        title=f"🏆 Conquistas de {p['nome']}",
        description=f"**{concluidas}/{total}** conquistas desbloqueadas",
        color=COR_PRIMARY
    )

    categorias = {
        "Batalha":   ["primeira_batalha", "sobrevivente", "guerreiro_nato", "lendario_guerra", "transcendente"],
        "Dungeons":  ["primeiro_dungeon", "explorador", "conquistador", "mestre_dungeon"],
        "Ranks":     ["rank_e", "rank_d", "rank_c", "rank_b", "rank_a", "rank_s", "rank_ss"],
        "PvP":       ["primeiro_pvp", "campeao_pvp", "gladiador"],
        "Economia":  ["rico", "milionario", "magnata"],
        "Missões":   ["dedicado", "disciplinado"],
    }

    for cat, ids in categorias.items():
        txt = ""
        for cid in ids:
            cq = next((c for c in CONQUISTAS if c[0] == cid), None)
            if not cq:
                continue
            _, nome, desc, emoji, _, meta, xp, moedas, ficha = cq
            user_cq = conquistas_user.get(cid)
            prog = user_cq["progresso"] if user_cq else 0
            done = user_cq and user_cq["concluida"]
            pct = min(10, int((prog / meta) * 10)) if meta > 0 else 0
            barra = "█" * pct + "░" * (10 - pct)
            ficha_txt = f" {EMOJI_FICHA.get(ficha, '')} {ficha}" if ficha else ""
            
            if done:
                txt += f"✅ {emoji} **{nome}**\n"
            else:
                txt += f"🔒 {emoji} **{nome}** `{barra}` {prog}/{meta}\n"
                txt += f"   *{desc}* | +{xp}XP +{moedas}🪙{ficha_txt}\n"
        
        if txt:
            embed.add_field(name=f"═══ {cat} ═══", value=txt, inline=False)

    embed.set_image(url=IMG_CONQUISTAS)
    embed.set_footer(text="Conquistas desbloqueiam recompensas automáticas!")
    await interaction.followup.send(embed=embed, ephemeral=True)