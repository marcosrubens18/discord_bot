# guildas.py — Sistema de Guildas completo v2
import discord
import asyncio
import random
from datetime import datetime, timedelta, date
from db import get_pool

# ─── CONSTANTES ───────────────────────────────────────────────────

CUSTO_CRIAR = 5000

NIVEIS_GUILDA = {
    1: {"xp_needed": 0,    "bonus_xp": 0,   "bonus_moedas": 0,   "bonus_loot": 0,   "desc": "Iniciante"},
    2: {"xp_needed": 500,  "bonus_xp": 5,   "bonus_moedas": 0,   "bonus_loot": 0,   "desc": "Estabelecida"},
    3: {"xp_needed": 1500, "bonus_xp": 10,  "bonus_moedas": 10,  "bonus_loot": 0,   "desc": "Reconhecida"},
    4: {"xp_needed": 3500, "bonus_xp": 15,  "bonus_moedas": 15,  "bonus_loot": 10,  "desc": "Poderosa"},
    5: {"xp_needed": 7000, "bonus_xp": 20,  "bonus_moedas": 20,  "bonus_loot": 20,  "desc": "Lendaria"},
}

MISSOES_POOL = [
    {"tipo": "vitorias_treino", "desc": "Vencer {meta} batalhas de treino", "meta_range": (10, 25), "xp": 300, "moedas": 500},
    {"tipo": "dungeons",        "desc": "Completar {meta} dungeons",         "meta_range": (5, 15),  "xp": 500, "moedas": 800},
    {"tipo": "vitorias_pvp",    "desc": "Vencer {meta} duelos PvP",          "meta_range": (3, 8),   "xp": 400, "moedas": 600},
    {"tipo": "treinos_total",   "desc": "Realizar {meta} treinos no total",  "meta_range": (15, 30), "xp": 200, "moedas": 400},
    {"tipo": "dungeons_rank",   "desc": "Completar {meta} dungeons Rank C+", "meta_range": (3, 8),   "xp": 600, "moedas": 1000},
]

# ─── DB ───────────────────────────────────────────────────────────

async def init_db_guildas():
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS guildas (
                id SERIAL PRIMARY KEY,
                nome TEXT UNIQUE NOT NULL,
                emoji TEXT DEFAULT '⚔️',
                descricao TEXT DEFAULT '',
                banco INTEGER DEFAULT 0,
                xp INTEGER DEFAULT 0,
                nivel INTEGER DEFAULT 1,
                max_membros INTEGER DEFAULT 20,
                cargo_id BIGINT DEFAULT 0,
                canal_id BIGINT DEFAULT 0,
                criado_por BIGINT,
                criado_em TIMESTAMP DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS guilda_membros (
                id SERIAL PRIMARY KEY,
                guilda_id INTEGER REFERENCES guildas(id) ON DELETE CASCADE,
                user_id BIGINT UNIQUE,
                nome TEXT,
                cargo TEXT DEFAULT 'membro',
                entrou_em TIMESTAMP DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS guilda_missoes (
                id SERIAL PRIMARY KEY,
                guilda_id INTEGER REFERENCES guildas(id) ON DELETE CASCADE,
                tipo TEXT,
                descricao TEXT,
                meta INTEGER,
                progresso INTEGER DEFAULT 0,
                premio_xp INTEGER DEFAULT 0,
                premio_moedas INTEGER DEFAULT 0,
                semana DATE DEFAULT CURRENT_DATE,
                concluida BOOLEAN DEFAULT FALSE
            )
        """)
    print("DB guildas OK!")

# ─── HELPERS ──────────────────────────────────────────────────────

async def get_guilda_do_jogador(user_id):
    pool = await get_pool()
    async with pool.acquire() as conn:
        m = await conn.fetchrow("SELECT * FROM guilda_membros WHERE user_id=$1", user_id)
        if not m: return None, None
        g = await conn.fetchrow("SELECT * FROM guildas WHERE id=$1", m["guilda_id"])
        return g, m

async def get_membros(guilda_id):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch(
            "SELECT * FROM guilda_membros WHERE guilda_id=$1 ORDER BY cargo, entrou_em",
            guilda_id)

def get_bonus_guilda(nivel: int):
    return NIVEIS_GUILDA.get(nivel, NIVEIS_GUILDA[1])

async def dar_xp_guilda(guilda_id: int, xp: int, guild=None):
    """Dá XP para a guilda e verifica level up."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        g = await conn.fetchrow("SELECT xp, nivel FROM guildas WHERE id=$1", guilda_id)
        if not g: return
        novo_xp = g["xp"] + xp
        nivel   = g["nivel"]
        # Verifica level up
        while nivel < 5:
            prox = NIVEIS_GUILDA.get(nivel + 1, {})
            if novo_xp >= prox.get("xp_needed", 99999):
                nivel += 1
                # Anuncia no canal da guilda
                if guild:
                    guilda = await conn.fetchrow("SELECT * FROM guildas WHERE id=$1", guilda_id)
                    canal = guild.get_channel(guilda["canal_id"]) if guilda else None
                    if canal:
                        info = NIVEIS_GUILDA[nivel]
                        embed = discord.Embed(
                            title=f"🎉 A guilda subiu para Nível {nivel}!",
                            description=f"**{guilda['emoji']} {guilda['nome']}** é agora uma guilda **{info['desc']}**!\n\nNovos bônus para todos os membros:\n+{info['bonus_xp']}% XP | +{info['bonus_moedas']}% Moedas | +{info['bonus_loot']}% Loot",
                            color=0xE4AF3C
                        )
                        await canal.send(embed=embed)
            else:
                break
        await conn.execute("UPDATE guildas SET xp=$1, nivel=$2 WHERE id=$3", novo_xp, nivel, guilda_id)

async def atualizar_missao_guilda(user_id: int, tipo: str, quantidade: int = 1):
    """Atualiza progresso de missão semanal da guilda do jogador."""
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            m = await conn.fetchrow("SELECT guilda_id FROM guilda_membros WHERE user_id=$1", user_id)
            if not m: return
            guilda_id = m["guilda_id"]
            semana_atual = date.today().isocalendar()[1]  # número da semana
            missoes = await conn.fetch("""
                SELECT * FROM guilda_missoes
                WHERE guilda_id=$1 AND tipo=$2 AND NOT concluida
                AND EXTRACT(WEEK FROM semana) = $3
            """, guilda_id, tipo, semana_atual)
            for miss in missoes:
                novo_prog = miss["progresso"] + quantidade
                if novo_prog >= miss["meta"]:
                    await conn.execute("UPDATE guilda_missoes SET progresso=$1, concluida=TRUE WHERE id=$2",
                        miss["meta"], miss["id"])
                    # Distribui prêmio para todos membros
                    membros = await conn.fetch("SELECT user_id FROM guilda_membros WHERE guilda_id=$1", guilda_id)
                    for mb in membros:
                        await conn.execute("UPDATE personagens SET xp=xp+$1, moedas=moedas+$2 WHERE user_id=$3",
                            miss["premio_xp"], miss["premio_moedas"], mb["user_id"])
                    # Notifica no canal da guilda
                    guilda = await conn.fetchrow("SELECT * FROM guildas WHERE id=$1", guilda_id)
                    if guilda and guilda["canal_id"]:
                        canal_id = guilda["canal_id"]
                        return (canal_id, miss["descricao"], miss["premio_xp"], miss["premio_moedas"])
                else:
                    await conn.execute("UPDATE guilda_missoes SET progresso=$1 WHERE id=$2",
                        novo_prog, miss["id"])
    except Exception as e:
        print(f"Erro missao guilda: {e}")
    return None

async def gerar_missoes_semanais(guilda_id: int):
    """Gera 3 missões semanais para a guilda."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        semana_atual = date.today().isocalendar()[1]
        ja_tem = await conn.fetchval("""
            SELECT COUNT(*) FROM guilda_missoes
            WHERE guilda_id=$1 AND EXTRACT(WEEK FROM semana) = $2
        """, guilda_id, semana_atual)
        if ja_tem >= 3: return False
        escolhidas = random.sample(MISSOES_POOL, 3)
        for miss in escolhidas:
            meta = random.randint(*miss["meta_range"])
            desc = miss["desc"].format(meta=meta)
            await conn.execute("""
                INSERT INTO guilda_missoes(guilda_id,tipo,descricao,meta,premio_xp,premio_moedas,semana)
                VALUES($1,$2,$3,$4,$5,$6,CURRENT_DATE)
            """, guilda_id, miss["tipo"], desc, meta, miss["xp"], miss["moedas"])
        return True

# ─── CRIAR CANAL DA GUILDA ────────────────────────────────────────

async def criar_canal_guilda(guild: discord.Guild, nome: str, emoji: str, cargo: discord.Role, bot_member):
    """Cria categoria GUILDAS e canal da guilda."""
    try:
        cat = discord.utils.get(guild.categories, name="GUILDAS")
        if not cat:
            cat = await guild.create_category("GUILDAS")
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            cargo: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            bot_member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }
        nome_canal = f"{emoji}│{nome.lower()[:20].replace(' ', '-')}"
        canal = await guild.create_text_channel(nome_canal, category=cat, overwrites=overwrites)
        return canal
    except Exception as e:
        print(f"Erro criar canal guilda: {e}")
        return None

# ─── MODAL CRIAR GUILDA ───────────────────────────────────────────

class CriarGuildaModal(discord.ui.Modal, title="Criar Guilda"):
    nome_input = discord.ui.TextInput(label="Nome da Guilda", max_length=40,
        placeholder="Ex: Guardioes do Caos")
    emoji_input = discord.ui.TextInput(label="Emoji da Guilda", max_length=5, default="⚔️",
        placeholder="Ex: 🔥")
    descricao_input = discord.ui.TextInput(label="Descricao", style=discord.TextStyle.paragraph,
        max_length=200, placeholder="Descricao da sua guilda...")
    max_input = discord.ui.TextInput(label="Limite de membros (5 a 50)", max_length=3,
        default="20", placeholder="Ex: 20")

    def __init__(self, guild):
        super().__init__()
        self.discord_guild = guild

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await init_db_guildas()

        nome  = str(self.nome_input).strip()
        emoji = str(self.emoji_input).strip() or "⚔️"
        desc  = str(self.descricao_input).strip()
        try:
            max_m = max(5, min(50, int(str(self.max_input).strip())))
        except:
            max_m = 20

        pool = await get_pool()
        async with pool.acquire() as conn:
            ex_m = await conn.fetchrow("SELECT id FROM guilda_membros WHERE user_id=$1", interaction.user.id)
            if ex_m:
                await interaction.followup.send("Voce ja faz parte de uma guilda! Saia primeiro.", ephemeral=True); return
            ex_n = await conn.fetchrow("SELECT id FROM guildas WHERE LOWER(nome)=$1", nome.lower())
            if ex_n:
                await interaction.followup.send(f"Ja existe uma guilda chamada **{nome}**!", ephemeral=True); return
            p = await conn.fetchrow("SELECT moedas, nome FROM personagens WHERE user_id=$1", interaction.user.id)
            if not p:
                await interaction.followup.send("Crie seu personagem primeiro!", ephemeral=True); return
            if p["moedas"] < CUSTO_CRIAR:
                await interaction.followup.send(f"Precisa de **{CUSTO_CRIAR} moedas**! Voce tem {p['moedas']}.", ephemeral=True); return

            await conn.execute("UPDATE personagens SET moedas=moedas-$1 WHERE user_id=$2", CUSTO_CRIAR, interaction.user.id)
            g = await conn.fetchrow("""
                INSERT INTO guildas(nome,emoji,descricao,max_membros,nivel,xp,criado_por)
                VALUES($1,$2,$3,$4,1,0,$5) RETURNING *
            """, nome, emoji, desc, max_m, interaction.user.id)
            await conn.execute("""
                INSERT INTO guilda_membros(guilda_id,user_id,nome,cargo)
                VALUES($1,$2,$3,'mestre')
            """, g["id"], interaction.user.id, p["nome"])

        # Cria cargo
        cargo = None
        try:
            cargo = await self.discord_guild.create_role(
                name=f"{emoji} {nome}", color=discord.Color.blue(), reason="Guilda criada")
            member = self.discord_guild.get_member(interaction.user.id)
            if member: await member.add_roles(cargo)
        except Exception as e:
            print(f"Erro cargo: {e}")

        # Cria canal da guilda
        canal = None
        if cargo:
            canal = await criar_canal_guilda(self.discord_guild, nome, emoji, cargo, self.discord_guild.me)

        # Salva cargo e canal
        async with pool.acquire() as conn:
            await conn.execute("UPDATE guildas SET cargo_id=$1, canal_id=$2 WHERE id=$3",
                cargo.id if cargo else 0, canal.id if canal else 0, g["id"])

        # Gera missoes semanais iniciais
        await gerar_missoes_semanais(g["id"])

        # Mensagem de boas vindas no canal
        if canal:
            embed_bv = discord.Embed(
                title=f"Bem-vindos ao QG da guilda {emoji} {nome}!",
                description=(
                    f"Este e o canal exclusivo da guilda!\n\n"
                    f"**Comandos da guilda:**\n"
                    f"`/guilda-info` — Ver info e membros\n"
                    f"`/guilda-missoes` — Missoes semanais\n"
                    f"`/guilda-depositar` — Depositar no banco\n"
                    f"`/guilda-convidar @jogador` — Recrutar\n\n"
                    f"**Nivel atual:** 1 — Iniciante\n"
                    f"Jogue junto para subir o nivel da guilda e ganhar bonus!"
                ),
                color=0x7F77DD
            )
            await canal.send(embed=embed_bv)

        canal_txt = canal.mention if canal else "nao criado"
        await interaction.followup.send(
            f"{emoji} Guilda **{nome}** fundada!\n"
            f"Canal: {canal_txt}\n"
            f"Custo: -{CUSTO_CRIAR} moedas\n"
            f"3 missoes semanais geradas!\n\n"
            f"Use `/guilda-convidar @jogador` para recrutar!",
            ephemeral=True
        )

# ─── COMANDOS ─────────────────────────────────────────────────────

async def cmd_guilda_criar(interaction: discord.Interaction):
    await interaction.response.send_modal(CriarGuildaModal(interaction.guild))

async def cmd_guilda_info(interaction: discord.Interaction, nome: str = ""):
    await interaction.response.defer()
    pool = await get_pool()
    async with pool.acquire() as conn:
        if nome:
            g = await conn.fetchrow("SELECT * FROM guildas WHERE LOWER(nome)=$1", nome.lower())
        else:
            m = await conn.fetchrow("SELECT guilda_id FROM guilda_membros WHERE user_id=$1", interaction.user.id)
            g = await conn.fetchrow("SELECT * FROM guildas WHERE id=$1", m["guilda_id"]) if m else None
        if not g:
            await interaction.followup.send("Guilda nao encontrada!", ephemeral=True); return
        membros = await conn.fetch("SELECT * FROM guilda_membros WHERE guilda_id=$1 ORDER BY cargo,entrou_em", g["id"])
        ids = [m["user_id"] for m in membros]
        stats = await conn.fetchrow(
            "SELECT AVG(nivel) as avg_nivel, SUM(vitorias) as total_vit FROM personagens WHERE user_id=ANY($1)", ids
        ) if ids else None

    nivel_info = NIVEIS_GUILDA.get(g["nivel"], NIVEIS_GUILDA[1])
    prox_nivel = NIVEIS_GUILDA.get(g["nivel"]+1)
    xp_atual = g["xp"]

    # Barra de XP
    if prox_nivel:
        xp_needed = prox_nivel["xp_needed"]
        pct = min(1.0, xp_atual / xp_needed)
        f = int(pct * 10)
        barra = "█" * f + "░" * (10 - f)
        xp_txt = f"`{barra}` {xp_atual}/{xp_needed} XP"
    else:
        xp_txt = "Nivel maximo!"

    embed = discord.Embed(
        title=f"{g['emoji']} {g['nome']}",
        description=g["descricao"],
        color=0x7F77DD
    )
    embed.add_field(name="Nivel",   value=f"{g['nivel']} — {nivel_info['desc']}", inline=True)
    embed.add_field(name="XP",      value=xp_txt,                                  inline=True)
    embed.add_field(name="Banco",   value=f"{g['banco']} 🪙",                      inline=True)
    embed.add_field(name="Membros", value=f"{len(membros)}/{g['max_membros']}",    inline=True)
    if stats and stats["avg_nivel"]:
        embed.add_field(name="Nivel Medio",    value=f"{float(stats['avg_nivel']):.1f}", inline=True)
        embed.add_field(name="Vitorias Total", value=str(stats["total_vit"] or 0),       inline=True)
    # Bonus ativos
    bonus_txt = f"+{nivel_info['bonus_xp']}% XP | +{nivel_info['bonus_moedas']}% Moedas | +{nivel_info['bonus_loot']}% Loot"
    embed.add_field(name="Bonus Ativos", value=bonus_txt, inline=False)
    # Lista membros
    cargos_emoji = {"mestre": "👑", "oficial": "⚔️", "membro": "🛡️"}
    lista = "\n".join([f"{cargos_emoji.get(m['cargo'],'🛡️')} {m['nome']}" for m in membros[:15]])
    embed.add_field(name="Membros", value=lista or "—", inline=False)
    await interaction.followup.send(embed=embed)

async def cmd_guilda_missoes(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    g, m = await get_guilda_do_jogador(interaction.user.id)
    if not g:
        await interaction.followup.send("Voce nao faz parte de nenhuma guilda!", ephemeral=True); return

    # Gera missoes se nao tiver para essa semana
    await gerar_missoes_semanais(g["id"])

    pool = await get_pool()
    async with pool.acquire() as conn:
        semana_atual = date.today().isocalendar()[1]
        missoes = await conn.fetch("""
            SELECT * FROM guilda_missoes
            WHERE guilda_id=$1 AND EXTRACT(WEEK FROM semana) = $2
            ORDER BY id
        """, g["id"], semana_atual)

    if not missoes:
        await interaction.followup.send("Nenhuma missao disponivel esta semana!", ephemeral=True); return

    embed = discord.Embed(
        title=f"📋 Missoes Semanais — {g['emoji']} {g['nome']}",
        description="Complete as missoes em equipe para recompensar toda a guilda!",
        color=0x7F77DD
    )
    for miss in missoes:
        status = "✅" if miss["concluida"] else f"{miss['progresso']}/{miss['meta']}"
        barra_p = int((miss["progresso"]/miss["meta"])*10) if miss["meta"] > 0 else 0
        barra   = "█"*barra_p + "░"*(10-barra_p)
        embed.add_field(
            name=f"{'✅' if miss['concluida'] else '📌'} {miss['descricao']}",
            value=f"`{barra}` {status}\n🏆 Recompensa: +{miss['premio_xp']} XP | +{miss['premio_moedas']} 🪙 para TODOS",
            inline=False
        )
    await interaction.followup.send(embed=embed, ephemeral=True)

async def cmd_guilda_convidar(interaction: discord.Interaction, jogador: discord.Member):
    await interaction.response.defer(ephemeral=True)
    g, m = await get_guilda_do_jogador(interaction.user.id)
    if not g:
        await interaction.followup.send("Voce nao faz parte de nenhuma guilda!", ephemeral=True); return
    if m["cargo"] not in ("mestre","oficial"):
        await interaction.followup.send("Apenas Mestre e Oficial podem convidar!", ephemeral=True); return

    pool = await get_pool()
    async with pool.acquire() as conn:
        membros = await conn.fetch("SELECT id FROM guilda_membros WHERE guilda_id=$1", g["id"])
        if len(membros) >= g["max_membros"]:
            await interaction.followup.send("Guilda cheia!", ephemeral=True); return
        ex = await conn.fetchrow("SELECT id FROM guilda_membros WHERE user_id=$1", jogador.id)
        if ex:
            await interaction.followup.send(f"{jogador.display_name} ja faz parte de uma guilda!", ephemeral=True); return
        p = await conn.fetchrow("SELECT nome FROM personagens WHERE user_id=$1", jogador.id)
        if not p:
            await interaction.followup.send(f"{jogador.display_name} nao tem personagem!", ephemeral=True); return

    class ConviteView(discord.ui.View):
        def __init__(self): super().__init__(timeout=60); self.resposta = None
        @discord.ui.button(label="Aceitar", style=discord.ButtonStyle.success)
        async def aceitar(self, inter, b):
            if inter.user.id != jogador.id: return
            self.resposta = True; await inter.response.defer(); self.stop()
        @discord.ui.button(label="Recusar", style=discord.ButtonStyle.danger)
        async def recusar(self, inter, b):
            if inter.user.id != jogador.id: return
            self.resposta = False; await inter.response.defer(); self.stop()

    embed_conv = discord.Embed(
        title=f"{g['emoji']} Convite de Guilda",
        description=f"**{interaction.user.display_name}** te convidou para **{g['nome']}**!\n\nNivel {g['nivel']} — {len(membros)}/{g['max_membros']} membros",
        color=0x7F77DD
    )
    v = ConviteView()
    await interaction.followup.send(content=jogador.mention, embed=embed_conv, view=v)
    await v.wait()
    if not v.resposta:
        await interaction.followup.send(f"{jogador.display_name} recusou.", ephemeral=True); return

    pool = await get_pool()
    async with pool.acquire() as conn:
        p = await conn.fetchrow("SELECT nome FROM personagens WHERE user_id=$1", jogador.id)
        await conn.execute("INSERT INTO guilda_membros(guilda_id,user_id,nome,cargo) VALUES($1,$2,$3,'membro')",
            g["id"], jogador.id, p["nome"])

    if g["cargo_id"]:
        cargo = interaction.guild.get_role(g["cargo_id"])
        if cargo:
            try: await jogador.add_roles(cargo)
            except: pass

    # Anuncia no canal da guilda
    if g["canal_id"]:
        canal = interaction.guild.get_channel(g["canal_id"])
        if canal:
            await canal.send(f"👋 {jogador.mention} entrou na guilda! Bem-vindo!")

    await interaction.followup.send(f"{jogador.mention} entrou em **{g['emoji']} {g['nome']}**!")

async def cmd_guilda_sair(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    g, m = await get_guilda_do_jogador(interaction.user.id)
    if not g:
        await interaction.followup.send("Voce nao faz parte de nenhuma guilda!", ephemeral=True); return
    if m["cargo"] == "mestre":
        membros = await get_membros(g["id"])
        if len(membros) > 1:
            await interaction.followup.send("Voce e o Mestre! Transfira a lideranca antes de sair.", ephemeral=True); return

    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM guilda_membros WHERE user_id=$1", interaction.user.id)
        restantes = await conn.fetchval("SELECT COUNT(*) FROM guilda_membros WHERE guilda_id=$1", g["id"])
        if restantes == 0:
            # Apaga canal e cargo
            if g["cargo_id"]:
                cargo = interaction.guild.get_role(g["cargo_id"])
                if cargo:
                    try: await cargo.delete()
                    except: pass
            if g["canal_id"]:
                canal = interaction.guild.get_channel(g["canal_id"])
                if canal:
                    try: await canal.delete()
                    except: pass
            await conn.execute("DELETE FROM guildas WHERE id=$1", g["id"])

    if g["cargo_id"]:
        cargo = interaction.guild.get_role(g["cargo_id"])
        if cargo:
            member = interaction.guild.get_member(interaction.user.id)
            if member:
                try: await member.remove_roles(cargo)
                except: pass

    await interaction.followup.send(f"Voce saiu da guilda **{g['nome']}**.", ephemeral=True)

async def cmd_guilda_expulsar(interaction: discord.Interaction, jogador: discord.Member):
    await interaction.response.defer(ephemeral=True)
    g, m = await get_guilda_do_jogador(interaction.user.id)
    if not g or m["cargo"] != "mestre":
        await interaction.followup.send("Apenas o Mestre pode expulsar!", ephemeral=True); return
    if jogador.id == interaction.user.id:
        await interaction.followup.send("Nao pode se expulsar!", ephemeral=True); return

    pool = await get_pool()
    async with pool.acquire() as conn:
        ex = await conn.fetchrow("SELECT id FROM guilda_membros WHERE guilda_id=$1 AND user_id=$2", g["id"], jogador.id)
        if not ex:
            await interaction.followup.send(f"{jogador.display_name} nao e membro!", ephemeral=True); return
        await conn.execute("DELETE FROM guilda_membros WHERE user_id=$1", jogador.id)

    if g["cargo_id"]:
        cargo = interaction.guild.get_role(g["cargo_id"])
        if cargo:
            try: await jogador.remove_roles(cargo)
            except: pass

    await interaction.followup.send(f"{jogador.display_name} foi expulso!", ephemeral=True)

async def cmd_guilda_promover(interaction: discord.Interaction, jogador: discord.Member):
    await interaction.response.defer(ephemeral=True)
    g, m = await get_guilda_do_jogador(interaction.user.id)
    if not g or m["cargo"] != "mestre":
        await interaction.followup.send("Apenas o Mestre pode promover!", ephemeral=True); return

    pool = await get_pool()
    async with pool.acquire() as conn:
        alvo = await conn.fetchrow("SELECT * FROM guilda_membros WHERE guilda_id=$1 AND user_id=$2", g["id"], jogador.id)
        if not alvo:
            await interaction.followup.send(f"{jogador.display_name} nao e membro!", ephemeral=True); return
        novo_cargo = "oficial" if alvo["cargo"] == "membro" else "mestre"
        await conn.execute("UPDATE guilda_membros SET cargo=$1 WHERE user_id=$2", novo_cargo, jogador.id)
        if novo_cargo == "mestre":
            await conn.execute("UPDATE guilda_membros SET cargo='oficial' WHERE user_id=$1", interaction.user.id)

    emoji_cargo = "⚔️" if novo_cargo == "oficial" else "👑"
    await interaction.followup.send(f"{emoji_cargo} **{jogador.display_name}** promovido a **{novo_cargo.title()}**!", ephemeral=True)

async def cmd_guilda_depositar(interaction: discord.Interaction, valor: int):
    await interaction.response.defer(ephemeral=True)
    g, m = await get_guilda_do_jogador(interaction.user.id)
    if not g:
        await interaction.followup.send("Voce nao faz parte de nenhuma guilda!", ephemeral=True); return
    if valor <= 0:
        await interaction.followup.send("Valor invalido!", ephemeral=True); return

    pool = await get_pool()
    async with pool.acquire() as conn:
        p = await conn.fetchrow("SELECT moedas FROM personagens WHERE user_id=$1", interaction.user.id)
        if not p or p["moedas"] < valor:
            await interaction.followup.send(f"Moedas insuficientes!", ephemeral=True); return
        await conn.execute("UPDATE personagens SET moedas=moedas-$1 WHERE user_id=$2", valor, interaction.user.id)
        await conn.execute("UPDATE guildas SET banco=banco+$1 WHERE id=$2", valor, g["id"])
        novo_banco = await conn.fetchval("SELECT banco FROM guildas WHERE id=$1", g["id"])

    # XP para guilda por deposito
    await dar_xp_guilda(g["id"], valor // 100, interaction.guild)

    await interaction.followup.send(
        f"Depositou **{valor} 🪙** no banco da guilda!\nBanco: **{novo_banco} 🪙**", ephemeral=True)

async def cmd_guilda_retirar(interaction: discord.Interaction, valor: int):
    await interaction.response.defer(ephemeral=True)
    g, m = await get_guilda_do_jogador(interaction.user.id)
    if not g or m["cargo"] != "mestre":
        await interaction.followup.send("Apenas o Mestre pode retirar do banco!", ephemeral=True); return
    if valor <= 0:
        await interaction.followup.send("Valor invalido!", ephemeral=True); return

    pool = await get_pool()
    async with pool.acquire() as conn:
        if g["banco"] < valor:
            await interaction.followup.send(f"Banco insuficiente! Tem {g['banco']} 🪙", ephemeral=True); return
        await conn.execute("UPDATE guildas SET banco=banco-$1 WHERE id=$2", valor, g["id"])
        await conn.execute("UPDATE personagens SET moedas=moedas+$1 WHERE user_id=$2", valor, interaction.user.id)

    await interaction.followup.send(f"Retirou **{valor} 🪙** do banco da guilda!", ephemeral=True)

async def cmd_guilda_ranking(interaction: discord.Interaction):
    await interaction.response.defer()
    pool = await get_pool()
    async with pool.acquire() as conn:
        guildas = await conn.fetch("SELECT * FROM guildas ORDER BY nivel DESC, xp DESC, banco DESC LIMIT 10")
        result = []
        for g in guildas:
            membros = await conn.fetch("SELECT user_id FROM guilda_membros WHERE guilda_id=$1", g["id"])
            ids = [m["user_id"] for m in membros]
            total_vit = 0
            if ids:
                stats = await conn.fetchrow("SELECT SUM(vitorias) as tv FROM personagens WHERE user_id=ANY($1)", ids)
                if stats: total_vit = stats["tv"] or 0
            result.append((g, len(membros), total_vit))

    embed = discord.Embed(title="Ranking de Guildas", color=0xE4AF3C)
    linhas = []
    for i, (g, nm, vit) in enumerate(result):
        nivel_info = NIVEIS_GUILDA.get(g["nivel"], NIVEIS_GUILDA[1])
        linhas.append(
            f"**{i+1}.** {g['emoji']} **{g['nome']}** — Nv{g['nivel']} {nivel_info['desc']} | "
            f"{nm} membros | {vit} wins | {g['banco']} 🪙"
        )
    embed.description = "\n".join(linhas) if linhas else "Nenhuma guilda ainda!"
    await interaction.followup.send(embed=embed)
