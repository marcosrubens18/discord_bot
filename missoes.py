# missoes.py — PostgreSQL version
import discord
import asyncio
import random
from datetime import date
from db import get_pool
from catalogo import get_rank
from imagens import IMG_MISSOES, IMG_RANKING

COR_RAR = {"Comum":0x888780,"Incomum":0x1D9E75,"Raro":0x378ADD,"Epico":0x7F77DD,"Lendario":0xD85A30}
EMOJI_FICHA = {"Comum":"🟫","Incomum":"🟩","Raro":"🟦","Epico":"🟪","Lendario":"🟧"}

# (id, descricao, tipo, meta, xp, moedas, ficha, rank_minimo)
POOL_MISSOES = [
    # ── Rank F (iniciante) ────────────────────────────────────────
    ("vencer_batalhas_1",  "Venca 1 batalha de treino",           "vitorias_treino", 1,  35,  20,  None,      "F"),
    ("vencer_batalhas_3",  "Venca 3 batalhas de treino",          "vitorias_treino", 3,  90,  55,  None,      "F"),
    ("usar_skills_5",      "Use skills 5 vezes em batalha",       "skills_usadas",   5,  45,  30,  None,      "F"),
    ("usar_pocao",         "Use uma pocao em batalha",            "pocoes_usadas",   1,  25,  15,  None,      "F"),
    ("usar_hospital",      "Use o hospital",                      "hospital_usado",  1,  25,  0,   None,      "F"),
    ("gastos_loja",        "Gaste 100 moedas na loja",            "moedas_gastas",   100,45,  0,   None,      "F"),
    ("coleta_loot",        "Colete loot em 3 batalhas",           "loots_coletados", 3,  65,  40,  None,      "F"),
    # ── Rank E+ ───────────────────────────────────────────────────
    ("vencer_batalhas_5",  "Venca 5 batalhas de treino",          "vitorias_treino", 5,  160, 100, "Incomum", "E"),
    ("dungeon_qualquer",   "Complete qualquer dungeon",            "dungeons",        1,  110, 85,  "Incomum", "E"),
    ("nivel_up",           "Suba de nivel",                       "level_ups",       1,  70,  50,  "Incomum", "E"),
    ("usar_skills_10",     "Use skills 10 vezes em batalha",      "skills_usadas",   10, 90,  65,  None,      "E"),
    ("usar_pocao_3",       "Use 3 pocoes em batalha",             "pocoes_usadas",   3,  70,  45,  None,      "E"),
    # ── Rank D+ ───────────────────────────────────────────────────
    ("pvp_participar",     "Participe de um duelo PvP",           "pvp_jogados",     1,  60,  45,  None,      "D"),
    ("pvp_vencer",         "Venca um duelo PvP",                  "pvp_vitorias",    1,  140, 100, "Raro",    "D"),
    ("treino_medio",       "Venca 5 treinos Medios",              "vitorias_treino", 5,  120, 80,  None,      "D"),
    # ── Rank C+ ───────────────────────────────────────────────────
    ("dungeon_c_plus",     "Complete dungeon Rank C ou acima",    "dungeons_c_plus", 1,  220, 160, "Raro",    "C"),
    ("treino_dificil",     "Venca um treino Dificil",             "treino_hard",     1,  120, 80,  "Raro",    "C"),
    ("pvp_vencer_3",       "Venca 3 duelos PvP",                  "pvp_vitorias",    3,  350, 220, "Epico",   "C"),
    # ── Rank B+ ───────────────────────────────────────────────────
    ("treino_lendario",    "Venca um treino Lendario",            "treino_hard",     1,  200, 150, "Epico",   "B"),
    ("dungeon_b_plus",     "Complete dungeon Rank B ou acima",    "dungeons_c_plus", 1,  400, 300, "Epico",   "B"),
    # ── Rank S+ ───────────────────────────────────────────────────
    ("dungeon_s",          "Complete dungeon Rank S",             "dungeons_c_plus", 1,  800, 600, "Lendario","S"),
    ("pvp_5_vitorias",     "Venca 5 duelos PvP seguidos",         "pvp_vitorias",    5,  700, 500, "Lendario","S"),
]

RANK_ORDEM = ["F","E","D","C","B","A","S","SS"]

def sortear_missoes_dia(rank_atual="F"):
    rank_idx = RANK_ORDEM.index(rank_atual) if rank_atual in RANK_ORDEM else 0
    # Pega missoes do rank atual e anteriores
    disponiveis = [m for m in POOL_MISSOES if RANK_ORDEM.index(m[7]) <= rank_idx]
    if len(disponiveis) < 3:
        disponiveis = POOL_MISSOES[:7]
    return random.sample(disponiveis, min(3, len(disponiveis)))

async def init_db_missoes():
    pass  # tabelas criadas no db.py

async def get_personagem(user_id):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM personagens WHERE user_id=$1", user_id)

async def get_missoes_hoje(user_id):
    hoje = date.today().isoformat()
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch(
            "SELECT * FROM missoes_diarias WHERE user_id=$1 AND data=$2",
            user_id, hoje
        )

async def criar_missoes_hoje(user_id, rank_atual="F"):
    hoje = date.today().isoformat()
    missoes = sortear_missoes_dia(rank_atual)
    pool = await get_pool()
    async with pool.acquire() as conn:
        for m in missoes:
            mid, desc, tipo, meta, xp, moedas, ficha, rank_min = m
            await conn.execute("""
                INSERT INTO missoes_diarias
                (user_id, data, missao_id, descricao, tipo, meta, progresso, concluida, xp, moedas, ficha)
                VALUES ($1,$2,$3,$4,$5,$6,0,0,$7,$8,$9)
                ON CONFLICT DO NOTHING
            """, user_id, hoje, mid, desc, tipo, meta, xp, moedas, ficha or "")

async def atualizar_progresso(user_id, tipo, quantidade=1):
    hoje = date.today().isoformat()
    pool = await get_pool()
    async with pool.acquire() as conn:
        missoes = await conn.fetch(
            "SELECT * FROM missoes_diarias WHERE user_id=$1 AND data=$2 AND tipo=$3 AND concluida=0",
            user_id, hoje, tipo
        )
        recompensas = []
        for m in missoes:
            novo_prog = m["progresso"] + quantidade
            if novo_prog >= m["meta"]:
                await conn.execute(
                    "UPDATE missoes_diarias SET progresso=$1, concluida=1 WHERE user_id=$2 AND data=$3 AND missao_id=$4",
                    m["meta"], user_id, hoje, m["missao_id"]
                )
                await conn.execute(
                    "UPDATE personagens SET xp=xp+$1, moedas=moedas+$2 WHERE user_id=$3",
                    m["xp"], m["moedas"], user_id
                )
                if m["ficha"]:
                    await conn.execute("""
                        INSERT INTO giros (user_id, roleta_id, raridade, quantidade)
                        VALUES ($1, 'skill', $2, 1)
                        ON CONFLICT (user_id, roleta_id, raridade)
                        DO UPDATE SET quantidade = giros.quantidade + 1
                    """, user_id, m["ficha"])
                recompensas.append({"descricao": m["descricao"], "xp": m["xp"], "moedas": m["moedas"], "ficha": m["ficha"]})
            else:
                await conn.execute(
                    "UPDATE missoes_diarias SET progresso=$1 WHERE user_id=$2 AND data=$3 AND missao_id=$4",
                    novo_prog, user_id, hoje, m["missao_id"]
                )
        return recompensas

async def cmd_missoes(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    p = await get_personagem(interaction.user.id)
    if not p:
        await interaction.followup.send("Crie seu personagem primeiro!", ephemeral=True); return

    missoes = await get_missoes_hoje(interaction.user.id)
    if not missoes:
        rank_atual = get_rank(p["nivel"])["rank"]
        await criar_missoes_hoje(interaction.user.id, rank_atual)
        missoes = await get_missoes_hoje(interaction.user.id)

    hoje = date.today().strftime("%d/%m/%Y")
    embed = discord.Embed(title=f"📋 Missões Diárias — {hoje}",
        description="Complete missoes para ganhar XP, moedas e fichas!\nRenovam todo dia a meia-noite.", color=0xE4AF3C)

    total_concluidas = 0
    for m in missoes:
        if m["concluida"]:
            status = "Concluida"; barra = "██████████"; total_concluidas += 1
        else:
            pct = m["progresso"] / max(1, m["meta"]); f = int(pct*10)
            barra = "█"*f + "░"*(10-f); status = "Em progresso"
        recomp = f"+{m['xp']} XP | +{m['moedas']} 🪙"
        if m["ficha"]:
            fe = EMOJI_FICHA.get(m["ficha"],"⬜")
            recomp += f" | {fe} Ficha {m['ficha']}"
        embed.add_field(
            name=f"{'✅' if m['concluida'] else '🔄'} {m['descricao']}",
            value=f"`{barra}` {m['progresso']}/{m['meta']}\n{recomp}",
            inline=False
        )
    embed.set_image(url=IMG_MISSOES)
    embed.set_footer(text=f"Concluidas: {total_concluidas}/3 hoje")
    await interaction.followup.send(embed=embed, ephemeral=True)

async def cmd_ranking(interaction: discord.Interaction):
    await interaction.response.defer()
    pool = await get_pool()
    async with pool.acquire() as conn:
        top_vitorias = await conn.fetch("SELECT nome, classe_id, nivel, vitorias, moedas FROM personagens ORDER BY vitorias DESC LIMIT 10")
        top_nivel    = await conn.fetch("SELECT nome, classe_id, nivel, vitorias, moedas FROM personagens ORDER BY nivel DESC, xp DESC LIMIT 10")
        top_moedas   = await conn.fetch("SELECT nome, classe_id, nivel, vitorias, moedas FROM personagens ORDER BY moedas DESC LIMIT 10")

    EMOJI_CLASSE = {"guerreiro":"🗡️","mago":"🔮","arqueiro":"🏹","paladino":"⚡","necromante":"🌑","dracomante":"🐉","arcano":"✨"}
    MEDALHAS = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]

    def fmt(lista, campo):
        txt = ""
        for i, p in enumerate(lista):
            e = EMOJI_CLASSE.get(p["classe_id"],"⚔️"); m = MEDALHAS[i] if i < 10 else f"{i+1}."
            valor = f"{p['vitorias']} vitorias" if campo=="vitorias" else (f"Nivel {p['nivel']}" if campo=="nivel" else f"{p['moedas']} 🪙")
            txt += f"{m} {e} **{p['nome']}** — {valor}\n"
        return txt or "*Ninguem ainda*"

    embed = discord.Embed(title="🏆 Ranking do Servidor", color=0xE4AF3C)
    embed.add_field(name="⚔️ Top Vitorias", value=fmt(top_vitorias,"vitorias"), inline=True)
    embed.add_field(name="⭐ Top Nivel",    value=fmt(top_nivel,"nivel"),    inline=True)
    embed.add_field(name="💰 Top Moedas",   value=fmt(top_moedas,"moedas"),  inline=True)
    embed.set_image(url=IMG_RANKING)
    embed.set_footer(text="Ranking atualizado em tempo real")
    await interaction.followup.send(embed=embed)
