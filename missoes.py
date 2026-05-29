# missoes.py — Sistema de missoes diarias e ranking
import discord
import aiosqlite
import asyncio
import random
from datetime import datetime, date

DB_PATH = "rpg.db"

COR_RAR = {"Comum":0x888780,"Incomum":0x1D9E75,"Raro":0x378ADD,"Epico":0x7F77DD,"Lendario":0xD85A30}

# ─── POOL DE MISSOES ─────────────────────────────────────────────

POOL_MISSOES = [
    # (id, descricao, tipo, meta, recompensa_xp, recompensa_moedas, recompensa_ficha)
    ("vencer_batalhas_1",  "Venca 1 batalha de treino",         "vitorias_treino", 1,  30,  20,  None),
    ("vencer_batalhas_3",  "Venca 3 batalhas de treino",         "vitorias_treino", 3,  80,  50,  None),
    ("vencer_batalhas_5",  "Venca 5 batalhas de treino",         "vitorias_treino", 5,  150, 100, "Incomum"),
    ("dungeon_qualquer",   "Complete qualquer dungeon",           "dungeons",        1,  100, 80,  "Incomum"),
    ("dungeon_dificil",    "Complete uma dungeon Rank C ou acima","dungeons_c_plus", 1,  200, 150, "Raro"),
    ("usar_skills_5",      "Use skills 5 vezes em batalha",      "skills_usadas",   5,  40,  30,  None),
    ("usar_skills_10",     "Use skills 10 vezes em batalha",     "skills_usadas",   10, 80,  60,  None),
    ("usar_pocao",         "Use uma pocao em batalha",           "pocoes_usadas",   1,  20,  15,  None),
    ("usar_pocao_3",       "Use 3 pocoes em batalha",            "pocoes_usadas",   3,  60,  40,  None),
    ("pvp_participar",     "Participe de um duelo PvP",          "pvp_jogados",     1,  50,  40,  None),
    ("pvp_vencer",         "Venca um duelo PvP",                 "pvp_vitorias",    1,  120, 90,  "Raro"),
    ("pvp_vencer_3",       "Venca 3 duelos PvP",                 "pvp_vitorias",    3,  300, 200, "Epico"),
    ("gastos_loja",        "Gaste 100 moedas na loja",           "moedas_gastas",   100,40,  0,   None),
    ("nivel_up",           "Suba de nivel",                      "level_ups",       1,  60,  50,  "Incomum"),
    ("usar_hospital",      "Use o hospital",                     "hospital_usado",  1,  20,  0,   None),
    ("treino_dificil",     "Venca um treino Dificil ou Lendario","treino_hard",     1,  100, 70,  "Raro"),
    ("coleta_loot",        "Colete loot em 3 batalhas",          "loots_coletados", 3,  60,  40,  None),
]

# Sorteia 3 missoes por dia para o jogador
def sortear_missoes_dia():
    return random.sample(POOL_MISSOES, min(3, len(POOL_MISSOES)))

# ─── DB ──────────────────────────────────────────────────────────

async def init_db_missoes():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS missoes_diarias (
                user_id     INTEGER,
                data        TEXT,
                missao_id   TEXT,
                descricao   TEXT,
                tipo        TEXT,
                meta        INTEGER,
                progresso   INTEGER DEFAULT 0,
                concluida   INTEGER DEFAULT 0,
                xp          INTEGER,
                moedas      INTEGER,
                ficha       TEXT,
                PRIMARY KEY (user_id, data, missao_id)
            )
        """)
        await db.commit()
    print("DB missoes OK")

async def get_personagem(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM personagens WHERE user_id=?", (user_id,)) as c:
            return await c.fetchone()

async def get_missoes_hoje(user_id):
    hoje = date.today().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM missoes_diarias WHERE user_id=? AND data=?",
            (user_id, hoje)
        ) as c:
            return await c.fetchall()

async def criar_missoes_hoje(user_id):
    hoje = date.today().isoformat()
    missoes = sortear_missoes_dia()
    async with aiosqlite.connect(DB_PATH) as db:
        for m in missoes:
            mid, desc, tipo, meta, xp, moedas, ficha = m
            await db.execute("""
                INSERT OR IGNORE INTO missoes_diarias
                (user_id, data, missao_id, descricao, tipo, meta, progresso, concluida, xp, moedas, ficha)
                VALUES (?,?,?,?,?,?,0,0,?,?,?)
            """, (user_id, hoje, mid, desc, tipo, meta, xp, moedas, ficha or ""))
        await db.commit()

async def atualizar_progresso(user_id, tipo, quantidade=1):
    """Atualiza progresso das missoes do tipo especificado."""
    hoje = date.today().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM missoes_diarias WHERE user_id=? AND data=? AND tipo=? AND concluida=0",
            (user_id, hoje, tipo)
        ) as c:
            missoes = await c.fetchall()

        recompensas = []
        for m in missoes:
            novo_prog = m["progresso"] + quantidade
            if novo_prog >= m["meta"]:
                # Missao concluida!
                await db.execute(
                    "UPDATE missoes_diarias SET progresso=?, concluida=1 WHERE user_id=? AND data=? AND missao_id=?",
                    (m["meta"], user_id, hoje, m["missao_id"])
                )
                # Da recompensa
                await db.execute(
                    "UPDATE personagens SET xp=xp+?, moedas=moedas+? WHERE user_id=?",
                    (m["xp"], m["moedas"], user_id)
                )
                recompensas.append({
                    "descricao": m["descricao"],
                    "xp": m["xp"],
                    "moedas": m["moedas"],
                    "ficha": m["ficha"]
                })
                # Da ficha de roleta se houver
                if m["ficha"]:
                    await db.execute("""
                        INSERT INTO giros (user_id, roleta_id, raridade, quantidade)
                        VALUES (?, 'skill', ?, 1)
                        ON CONFLICT(user_id, roleta_id, raridade)
                        DO UPDATE SET quantidade = quantidade + 1
                    """, (user_id, m["ficha"]))
            else:
                await db.execute(
                    "UPDATE missoes_diarias SET progresso=? WHERE user_id=? AND data=? AND missao_id=?",
                    (novo_prog, user_id, hoje, m["missao_id"])
                )
        await db.commit()
        return recompensas

# ─── COMANDO /missoes ────────────────────────────────────────────

async def cmd_missoes(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    p = await get_personagem(interaction.user.id)
    if not p:
        await interaction.followup.send("Crie seu personagem primeiro!", ephemeral=True)
        return

    # Cria missoes do dia se nao existirem
    missoes = await get_missoes_hoje(interaction.user.id)
    if not missoes:
        await criar_missoes_hoje(interaction.user.id)
        missoes = await get_missoes_hoje(interaction.user.id)

    hoje = date.today().strftime("%d/%m/%Y")
    embed = discord.Embed(
        title=f"📋 Missoes Diarias — {hoje}",
        description="Complete missoes para ganhar XP, moedas e fichas de roleta!\nRenovam todo dia a meia-noite.",
        color=0xE4AF3C
    )

    total_concluidas = 0
    for m in missoes:
        if m["concluida"]:
            status = "✅"
            barra  = "██████████"
            total_concluidas += 1
        else:
            pct    = m["progresso"] / max(1, m["meta"])
            f      = int(pct * 10)
            barra  = "█" * f + "░" * (10 - f)
            status = "🔄"

        recomp = f"+{m['xp']} XP | +{m['moedas']} 🪙"
        if m["ficha"]:
            from hospital import EMOJI_FICHA
            fe = EMOJI_FICHA.get(m["ficha"], "⬜")
            recomp += f" | {fe} Ficha {m['ficha']}"

        embed.add_field(
            name=f"{status} {m['descricao']}",
            value=f"`{barra}` {m['progresso']}/{m['meta']}\n{recomp}",
            inline=False
        )

    embed.set_footer(text=f"Concluidas: {total_concluidas}/3 hoje")
    await interaction.followup.send(embed=embed, ephemeral=True)

# ─── COMANDO /ranking ────────────────────────────────────────────

async def cmd_ranking(interaction: discord.Interaction):
    await interaction.response.defer()

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        async with db.execute("""
            SELECT nome, classe_id, nivel, vitorias, moedas
            FROM personagens ORDER BY vitorias DESC LIMIT 10
        """) as c:
            top_vitorias = await c.fetchall()

        async with db.execute("""
            SELECT nome, classe_id, nivel, vitorias, moedas
            FROM personagens ORDER BY nivel DESC, xp DESC LIMIT 10
        """) as c:
            top_nivel = await c.fetchall()

        async with db.execute("""
            SELECT nome, classe_id, nivel, vitorias, moedas
            FROM personagens ORDER BY moedas DESC LIMIT 10
        """) as c:
            top_moedas = await c.fetchall()

    EMOJI_CLASSE = {
        "guerreiro":"🗡️","mago":"🔮","arqueiro":"🏹","paladino":"⚡",
        "necromante":"🌑","dracomante":"🐉","arcano":"✨"
    }
    MEDALHAS = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]

    def formatar_lista(lista, campo):
        txt = ""
        for i, p in enumerate(lista):
            emoji = EMOJI_CLASSE.get(p["classe_id"], "⚔️")
            medalha = MEDALHAS[i] if i < len(MEDALHAS) else f"{i+1}."
            if campo == "vitorias":
                valor = f"{p['vitorias']} vitorias"
            elif campo == "nivel":
                valor = f"Nivel {p['nivel']}"
            else:
                valor = f"{p['moedas']} 🪙"
            txt += f"{medalha} {emoji} **{p['nome']}** — {valor}\n"
        return txt or "*Ninguem ainda*"

    embed = discord.Embed(
        title="🏆 Ranking do Servidor",
        color=0xE4AF3C
    )
    embed.add_field(
        name="⚔️ Top Vitorias",
        value=formatar_lista(top_vitorias, "vitorias"),
        inline=True
    )
    embed.add_field(
        name="⭐ Top Nivel",
        value=formatar_lista(top_nivel, "nivel"),
        inline=True
    )
    embed.add_field(
        name="💰 Top Moedas",
        value=formatar_lista(top_moedas, "moedas"),
        inline=True
    )
    embed.set_footer(text="Ranking atualizado em tempo real")
    await interaction.followup.send(embed=embed)
