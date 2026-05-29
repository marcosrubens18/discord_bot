# missoes.py — PostgreSQL version
import discord
import asyncio
import random
from datetime import date
from db import get_pool

COR_RAR = {"Comum":0x888780,"Incomum":0x1D9E75,"Raro":0x378ADD,"Epico":0x7F77DD,"Lendario":0xD85A30}
EMOJI_FICHA = {"Comum":"🟫","Incomum":"🟩","Raro":"🟦","Epico":"🟪","Lendario":"🟧"}

POOL_MISSOES = [
    ("vencer_batalhas_1",  "Venca 1 batalha de treino",          "vitorias_treino", 1,  30,  20,  None),
    ("vencer_batalhas_3",  "Venca 3 batalhas de treino",          "vitorias_treino", 3,  80,  50,  None),
    ("vencer_batalhas_5",  "Venca 5 batalhas de treino",          "vitorias_treino", 5,  150, 100, "Incomum"),
    ("dungeon_qualquer",   "Complete qualquer dungeon",            "dungeons",        1,  100, 80,  "Incomum"),
    ("dungeon_dificil",    "Complete uma dungeon Rank C ou acima", "dungeons_c_plus", 1,  200, 150, "Raro"),
    ("usar_skills_5",      "Use skills 5 vezes em batalha",       "skills_usadas",   5,  40,  30,  None),
    ("usar_skills_10",     "Use skills 10 vezes em batalha",      "skills_usadas",   10, 80,  60,  None),
    ("usar_pocao",         "Use uma pocao em batalha",            "pocoes_usadas",   1,  20,  15,  None),
    ("usar_pocao_3",       "Use 3 pocoes em batalha",             "pocoes_usadas",   3,  60,  40,  None),
    ("pvp_participar",     "Participe de um duelo PvP",           "pvp_jogados",     1,  50,  40,  None),
    ("pvp_vencer",         "Venca um duelo PvP",                  "pvp_vitorias",    1,  120, 90,  "Raro"),
    ("pvp_vencer_3",       "Venca 3 duelos PvP",                  "pvp_vitorias",    3,  300, 200, "Epico"),
    ("gastos_loja",        "Gaste 100 moedas na loja",            "moedas_gastas",   100,40,  0,   None),
    ("nivel_up",           "Suba de nivel",                       "level_ups",       1,  60,  50,  "Incomum"),
    ("usar_hospital",      "Use o hospital",                      "hospital_usado",  1,  20,  0,   None),
    ("treino_dificil",     "Venca um treino Dificil ou Lendario", "treino_hard",     1,  100, 70,  "Raro"),
    ("coleta_loot",        "Colete loot em 3 batalhas",           "loots_coletados", 3,  60,  40,  None),
]

def sortear_missoes_dia():
    return random.sample(POOL_MISSOES, min(3, len(POOL_MISSOES)))

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

async def criar_missoes_hoje(user_id):
    hoje = date.today().isoformat()
    missoes = sortear_missoes_dia()
    pool = await get_pool()
    async with pool.acquire() as conn:
        for m in missoes:
            mid, desc, tipo, meta, xp, moedas, ficha = m
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
        await criar_missoes_hoje(interaction.user.id)
        missoes = await get_missoes_hoje(interaction.user.id)

    hoje = date.today().strftime("%d/%m/%Y")
    embed = discord.Embed(title=f"Missoes Diarias — {hoje}",
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
    embed.set_footer(text="Ranking atualizado em tempo real")
    await interaction.followup.send(embed=embed)
