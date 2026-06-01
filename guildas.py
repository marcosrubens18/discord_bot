# guildas.py — Sistema de Guildas completo
import discord
import asyncio
from datetime import datetime
from db import get_pool

CARGOS_GUILDA = {"mestre": "👑 Mestre", "oficial": "⚔️ Oficial", "membro": "🛡️ Membro"}
CUSTO_CRIAR   = 5000  # moedas para fundar

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
                max_membros INTEGER DEFAULT 20,
                cargo_id BIGINT DEFAULT 0,
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
                descricao TEXT,
                tipo TEXT,
                meta INTEGER DEFAULT 10,
                progresso INTEGER DEFAULT 0,
                premio_moedas INTEGER DEFAULT 0,
                premio_xp INTEGER DEFAULT 0,
                concluida BOOLEAN DEFAULT FALSE,
                criada_em TIMESTAMP DEFAULT NOW(),
                expira_em TIMESTAMP
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
            "SELECT * FROM guilda_membros WHERE guilda_id=$1 ORDER BY cargo,entrou_em",
            guilda_id)

# ─── MODAIS ───────────────────────────────────────────────────────

class CriarGuildaModal(discord.ui.Modal, title="Criar Guilda"):
    nome_input = discord.ui.TextInput(
        label="Nome da Guilda",
        placeholder="Ex: Guardioes do Caos",
        max_length=40
    )
    emoji_input = discord.ui.TextInput(
        label="Emoji da Guilda",
        placeholder="Ex: 🔥 ou ⚔️",
        max_length=5,
        default="⚔️"
    )
    descricao_input = discord.ui.TextInput(
        label="Descricao",
        style=discord.TextStyle.paragraph,
        placeholder="Descricao da sua guilda...",
        max_length=200
    )
    max_input = discord.ui.TextInput(
        label="Limite de membros (5 a 50)",
        placeholder="Ex: 20",
        max_length=3,
        default="20"
    )

    def __init__(self, guild):
        super().__init__()
        self.discord_guild = guild

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await init_db_guildas()

        nome = str(self.nome_input).strip()
        emoji = str(self.emoji_input).strip() or "⚔️"
        desc  = str(self.descricao_input).strip()
        try:
            max_m = max(5, min(50, int(str(self.max_input).strip())))
        except:
            max_m = 20

        pool = await get_pool()
        async with pool.acquire() as conn:
            # Verifica se ja tem guilda
            ex_m = await conn.fetchrow("SELECT id FROM guilda_membros WHERE user_id=$1", interaction.user.id)
            if ex_m:
                await interaction.followup.send("Voce ja faz parte de uma guilda! Saia primeiro.", ephemeral=True); return
            # Verifica nome unico
            ex_n = await conn.fetchrow("SELECT id FROM guildas WHERE LOWER(nome)=$1", nome.lower())
            if ex_n:
                await interaction.followup.send(f"Ja existe uma guilda chamada **{nome}**!", ephemeral=True); return
            # Verifica moedas
            p = await conn.fetchrow("SELECT moedas, nome FROM personagens WHERE user_id=$1", interaction.user.id)
            if not p:
                await interaction.followup.send("Crie seu personagem primeiro!", ephemeral=True); return
            if p["moedas"] < CUSTO_CRIAR:
                await interaction.followup.send(f"Precisa de **{CUSTO_CRIAR} moedas** para fundar uma guilda! Voce tem {p['moedas']}.", ephemeral=True); return

            # Debita moedas
            await conn.execute("UPDATE personagens SET moedas=moedas-$1 WHERE user_id=$2", CUSTO_CRIAR, interaction.user.id)

            # Cria guilda
            g = await conn.fetchrow("""
                INSERT INTO guildas(nome,emoji,descricao,max_membros,criado_por)
                VALUES($1,$2,$3,$4,$5) RETURNING *
            """, nome, emoji, desc, max_m, interaction.user.id)

            # Adiciona fundador como mestre
            await conn.execute("""
                INSERT INTO guilda_membros(guilda_id,user_id,nome,cargo)
                VALUES($1,$2,$3,'mestre')
            """, g["id"], interaction.user.id, p["nome"])

        # Cria cargo no Discord
        try:
            cargo = await self.discord_guild.create_role(
                name=f"{emoji} {nome}",
                color=discord.Color.blue(),
                reason="Guilda criada"
            )
            member = self.discord_guild.get_member(interaction.user.id)
            if member: await member.add_roles(cargo)
            pool2 = await get_pool()
            async with pool2.acquire() as conn2:
                await conn2.execute("UPDATE guildas SET cargo_id=$1 WHERE id=$2", cargo.id, g["id"])
        except Exception as e:
            print(f"Erro ao criar cargo guilda: {e}")

        await interaction.followup.send(
            f"{emoji} Guilda **{nome}** fundada!\n"
            f"Custo: -{CUSTO_CRIAR} moedas\n"
            f"Max membros: {max_m}\n\n"
            f"Use `/guilda-convidar @jogador` para recrutar membros!",
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
        membros = await conn.fetch(
            "SELECT * FROM guilda_membros WHERE guilda_id=$1 ORDER BY cargo,entrou_em", g["id"])
        total_m = len(membros)
        # Stats coletivos
        ids = [m["user_id"] for m in membros]
        if ids:
            stats = await conn.fetchrow(
                f"SELECT AVG(nivel) as avg_nivel, SUM(vitorias) as total_vit, SUM(moedas) as total_moedas FROM personagens WHERE user_id=ANY($1)",
                ids)
        else:
            stats = None

    embed = discord.Embed(
        title=f"{g['emoji']} {g['nome']}",
        description=g["descricao"],
        color=0x7F77DD
    )
    embed.add_field(name="Membros", value=f"{total_m}/{g['max_membros']}", inline=True)
    embed.add_field(name="Banco",   value=f"{g['banco']} 🪙",              inline=True)
    if stats and stats["avg_nivel"]:
        embed.add_field(name="Nivel Medio",    value=f"{float(stats['avg_nivel']):.1f}", inline=True)
        embed.add_field(name="Vitorias Total", value=str(stats["total_vit"] or 0),       inline=True)

    cargos_txt = {
        "mestre":  "👑",
        "oficial": "⚔️",
        "membro":  "🛡️"
    }
    if membros:
        lista = "\n".join([f"{cargos_txt.get(m['cargo'],'🛡️')} {m['nome']}" for m in membros[:15]])
        embed.add_field(name="Membros", value=lista, inline=False)
    await interaction.followup.send(embed=embed)

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

    # Envia convite com botoes
    class ConviteView(discord.ui.View):
        def __init__(self): super().__init__(timeout=60); self.resposta = None
        @discord.ui.button(label="Aceitar", style=discord.ButtonStyle.success)
        async def aceitar(self, inter: discord.Interaction, b):
            if inter.user.id != jogador.id: return
            self.resposta = True; await inter.response.defer(); self.stop()
        @discord.ui.button(label="Recusar", style=discord.ButtonStyle.danger)
        async def recusar(self, inter: discord.Interaction, b):
            if inter.user.id != jogador.id: return
            self.resposta = False; await inter.response.defer(); self.stop()

    embed_conv = discord.Embed(
        title=f"{g['emoji']} Convite de Guilda",
        description=f"**{interaction.user.display_name}** te convidou para a guilda **{g['nome']}**!\nAceita?",
        color=0x7F77DD
    )
    v = ConviteView()
    await interaction.followup.send(
        content=jogador.mention, embed=embed_conv, view=v)
    await v.wait()

    if not v.resposta:
        await interaction.followup.send(f"{jogador.display_name} recusou o convite.", ephemeral=True); return

    pool = await get_pool()
    async with pool.acquire() as conn:
        p = await conn.fetchrow("SELECT nome FROM personagens WHERE user_id=$1", jogador.id)
        await conn.execute("""
            INSERT INTO guilda_membros(guilda_id,user_id,nome,cargo)
            VALUES($1,$2,$3,'membro')
        """, g["id"], jogador.id, p["nome"])

    # Da o cargo
    if g["cargo_id"]:
        cargo = interaction.guild.get_role(g["cargo_id"])
        if cargo:
            member_obj = interaction.guild.get_member(jogador.id)
            if member_obj:
                try: await member_obj.add_roles(cargo)
                except: pass

    await interaction.followup.send(
        f"{jogador.mention} entrou na guilda **{g['emoji']} {g['nome']}**!", ephemeral=False)

async def cmd_guilda_sair(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    g, m = await get_guilda_do_jogador(interaction.user.id)
    if not g:
        await interaction.followup.send("Voce nao faz parte de nenhuma guilda!", ephemeral=True); return
    if m["cargo"] == "mestre":
        membros = await get_membros(g["id"])
        if len(membros) > 1:
            await interaction.followup.send(
                "Voce e o Mestre! Transfira a lideranca com `/guilda-promover` antes de sair.",
                ephemeral=True); return

    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM guilda_membros WHERE user_id=$1", interaction.user.id)
        membros_restantes = await conn.fetchval(
            "SELECT COUNT(*) FROM guilda_membros WHERE guilda_id=$1", g["id"])
        if membros_restantes == 0:
            await conn.execute("DELETE FROM guildas WHERE id=$1", g["id"])

    # Remove cargo
    if g["cargo_id"]:
        cargo = interaction.guild.get_role(g["cargo_id"])
        if cargo:
            member_obj = interaction.guild.get_member(interaction.user.id)
            if member_obj:
                try: await member_obj.remove_roles(cargo)
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
        ex = await conn.fetchrow(
            "SELECT id FROM guilda_membros WHERE guilda_id=$1 AND user_id=$2", g["id"], jogador.id)
        if not ex:
            await interaction.followup.send(f"{jogador.display_name} nao e membro da guilda!", ephemeral=True); return
        await conn.execute("DELETE FROM guilda_membros WHERE user_id=$1", jogador.id)

    if g["cargo_id"]:
        cargo = interaction.guild.get_role(g["cargo_id"])
        if cargo:
            try: await jogador.remove_roles(cargo)
            except: pass

    await interaction.followup.send(f"{jogador.display_name} foi expulso da guilda!", ephemeral=True)

async def cmd_guilda_promover(interaction: discord.Interaction, jogador: discord.Member):
    await interaction.response.defer(ephemeral=True)
    g, m = await get_guilda_do_jogador(interaction.user.id)
    if not g or m["cargo"] != "mestre":
        await interaction.followup.send("Apenas o Mestre pode promover!", ephemeral=True); return

    pool = await get_pool()
    async with pool.acquire() as conn:
        alvo = await conn.fetchrow(
            "SELECT * FROM guilda_membros WHERE guilda_id=$1 AND user_id=$2", g["id"], jogador.id)
        if not alvo:
            await interaction.followup.send(f"{jogador.display_name} nao e membro!", ephemeral=True); return
        novo_cargo = "oficial" if alvo["cargo"] == "membro" else "mestre"
        await conn.execute(
            "UPDATE guilda_membros SET cargo=$1 WHERE user_id=$2", novo_cargo, jogador.id)
        if novo_cargo == "mestre":
            await conn.execute(
                "UPDATE guilda_membros SET cargo='oficial' WHERE user_id=$1", interaction.user.id)

    emoji_cargo = "⚔️" if novo_cargo == "oficial" else "👑"
    await interaction.followup.send(
        f"{emoji_cargo} **{jogador.display_name}** promovido a **{novo_cargo.title()}**!", ephemeral=True)

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
            await interaction.followup.send(f"Moedas insuficientes! Voce tem {p['moedas'] if p else 0} 🪙", ephemeral=True); return
        await conn.execute("UPDATE personagens SET moedas=moedas-$1 WHERE user_id=$2", valor, interaction.user.id)
        await conn.execute("UPDATE guildas SET banco=banco+$1 WHERE id=$2", valor, g["id"])
        novo_banco = await conn.fetchval("SELECT banco FROM guildas WHERE id=$1", g["id"])

    await interaction.followup.send(
        f"Depositou **{valor} 🪙** no banco da guilda!\nBanco atual: **{novo_banco} 🪙**", ephemeral=True)

async def cmd_guilda_ranking(interaction: discord.Interaction):
    await interaction.response.defer()
    pool = await get_pool()
    async with pool.acquire() as conn:
        guildas = await conn.fetch("SELECT * FROM guildas ORDER BY banco DESC LIMIT 10")
        result = []
        for g in guildas:
            membros = await conn.fetch("SELECT user_id FROM guilda_membros WHERE guilda_id=$1", g["id"])
            ids = [m["user_id"] for m in membros]
            total_vit = 0
            avg_nivel = 0
            if ids:
                stats = await conn.fetchrow(
                    "SELECT AVG(nivel) as avg_nivel, SUM(vitorias) as total_vit FROM personagens WHERE user_id=ANY($1)", ids)
                if stats:
                    avg_nivel = float(stats["avg_nivel"] or 0)
                    total_vit = stats["total_vit"] or 0
            result.append((g, len(membros), avg_nivel, total_vit))

    embed = discord.Embed(title="🏆 Ranking de Guildas", color=0xE4AF3C)
    linhas = []
    for i, (g, nm, avg_n, vit) in enumerate(result):
        linhas.append(f"**{i+1}.** {g['emoji']} **{g['nome']}** — {nm} membros | Nv.Medio: {avg_n:.0f} | {vit} wins | {g['banco']} 🪙")
    embed.description = "\n".join(linhas) if linhas else "Nenhuma guilda ainda!"
    await interaction.followup.send(embed=embed)
