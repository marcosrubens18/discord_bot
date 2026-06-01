# torneio.py — Sistema de Torneios PvP
import discord
import asyncio
import math
from datetime import datetime, timedelta
from db import get_pool

# ─── DB ───────────────────────────────────────────────────────────

async def init_db_torneio():
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS torneios (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                descricao TEXT DEFAULT '',
                imagem_url TEXT DEFAULT '',
                canal_id BIGINT DEFAULT 0,
                msg_id BIGINT DEFAULT 0,
                valor_inscricao INTEGER DEFAULT 0,
                fim_inscricoes TIMESTAMP,
                premio_1 TEXT DEFAULT '',
                premio_2 TEXT DEFAULT '',
                premio_3 TEXT DEFAULT '',
                status TEXT DEFAULT 'inscricoes',
                criado_por BIGINT,
                criado_em TIMESTAMP DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS torneio_inscritos (
                id SERIAL PRIMARY KEY,
                torneio_id INTEGER REFERENCES torneios(id),
                user_id BIGINT,
                nome TEXT,
                nivel INTEGER DEFAULT 1,
                rank TEXT DEFAULT 'F',
                eliminado BOOLEAN DEFAULT FALSE,
                UNIQUE(torneio_id, user_id)
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS torneio_lutas (
                id SERIAL PRIMARY KEY,
                torneio_id INTEGER REFERENCES torneios(id),
                fase TEXT,
                luta_num INTEGER,
                user1_id BIGINT,
                user2_id BIGINT,
                vencedor_id BIGINT DEFAULT 0,
                bye BOOLEAN DEFAULT FALSE,
                concluida BOOLEAN DEFAULT FALSE
            )
        """)
    print("DB torneio OK!")

def proxima_potencia_2(n):
    p = 1
    while p < n: p *= 2
    return p

def nome_fase(total):
    if total == 1: return "Final"
    if total == 2: return "Semifinal"
    if total == 4: return "Quartas de Final"
    if total == 8: return "Oitavas de Final"
    return f"Rodada {total} lutas"

# ─── MODAL 1: INFO BASICA ─────────────────────────────────────────

class TorneioModal1(discord.ui.Modal, title="Criar Torneio — Parte 1 de 2"):
    nome = discord.ui.TextInput(
        label="Nome do Torneio",
        placeholder="Ex: Copa Villa Eldoria — Inverno 2026",
        max_length=80
    )
    descricao = discord.ui.TextInput(
        label="Descricao",
        style=discord.TextStyle.paragraph,
        placeholder="Descreva o torneio, regras, formato...",
        max_length=400
    )
    imagem_url = discord.ui.TextInput(
        label="URL da Imagem",
        placeholder="https://i.imgur.com/...",
        required=False,
        max_length=200
    )
    canal_id = discord.ui.TextInput(
        label="ID do Canal de Anuncio",
        placeholder="Ex: 1234567890123456789",
        max_length=20
    )
    duracao_horas = discord.ui.TextInput(
        label="Duracao das Inscricoes (em horas)",
        placeholder="Ex: 24 = 1 dia | 48 = 2 dias | 168 = 1 semana",
        max_length=5
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Salva dados parciais e abre modal 2
        self._dados = {
            "nome": str(self.nome),
            "descricao": str(self.descricao),
            "imagem_url": str(self.imagem_url) if self.imagem_url else "",
            "canal_id": int(str(self.canal_id)) if str(self.canal_id).isdigit() else 0,
            "horas": int(str(self.duracao_horas)) if str(self.duracao_horas).isdigit() else 24,
            "guild": interaction.guild,
            "criado_por": interaction.user.id,
        }
        await interaction.response.send_modal(TorneioModal2(self._dados))


# ─── MODAL 2: INSCRICAO E PREMIOS ────────────────────────────────

class TorneioModal2(discord.ui.Modal, title="Criar Torneio — Parte 2 de 2"):
    valor_inscricao = discord.ui.TextInput(
        label="Valor da Inscricao (moedas)",
        placeholder="Ex: 500 | Digite 0 para inscricao gratuita",
        max_length=8
    )
    premio_1 = discord.ui.TextInput(
        label="Premio do 1 Lugar",
        placeholder="Ex: 10000 moedas | cargo:Campeao | ficha:3",
        max_length=150
    )
    premio_2 = discord.ui.TextInput(
        label="Premio do 2 Lugar (opcional)",
        placeholder="Ex: 5000 moedas | Deixe vazio se nao quiser",
        required=False,
        max_length=150
    )
    premio_3 = discord.ui.TextInput(
        label="Premio do 3 Lugar (opcional)",
        placeholder="Ex: 2000 moedas | Deixe vazio se nao quiser",
        required=False,
        max_length=150
    )

    def __init__(self, dados: dict):
        super().__init__()
        self.dados = dados

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await init_db_torneio()

        try: valor = int(str(self.valor_inscricao))
        except: valor = 0

        horas = self.dados["horas"]
        fim   = datetime.utcnow() + timedelta(hours=horas)

        pool = await get_pool()
        async with pool.acquire() as conn:
            torneio = await conn.fetchrow("""
                INSERT INTO torneios
                (nome,descricao,imagem_url,canal_id,valor_inscricao,
                 fim_inscricoes,premio_1,premio_2,premio_3,status,criado_por)
                VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,'inscricoes',$10) RETURNING *
            """,
                self.dados["nome"], self.dados["descricao"],
                self.dados["imagem_url"], self.dados["canal_id"],
                valor, fim,
                str(self.premio_1),
                str(self.premio_2) if self.premio_2 else "",
                str(self.premio_3) if self.premio_3 else "",
                self.dados["criado_por"]
            )

        dur_txt = f"{horas}h" if horas < 24 else f"{horas//24} dia(s)"
        embed = discord.Embed(
            title=f"🏆 {self.dados['nome']}",
            description=self.dados["descricao"],
            color=0xE4AF3C
        )
        embed.add_field(name="💰 Inscricao",    value=f"{valor} moedas" if valor else "Gratuita", inline=True)
        embed.add_field(name="⏱️ Inscricoes",   value=f"<t:{int(fim.timestamp())}:R>",            inline=True)
        if str(self.premio_1): embed.add_field(name="🥇 1 Lugar", value=str(self.premio_1), inline=False)
        if self.premio_2 and str(self.premio_2): embed.add_field(name="🥈 2 Lugar", value=str(self.premio_2), inline=False)
        if self.premio_3 and str(self.premio_3): embed.add_field(name="🥉 3 Lugar", value=str(self.premio_3), inline=False)
        embed.set_footer(text=f"Torneio #{torneio['id']} | Clique abaixo para se inscrever!")
        if self.dados["imagem_url"]: embed.set_image(url=self.dados["imagem_url"])

        class InscreverView(discord.ui.View):
            def __init__(self): super().__init__(timeout=None)
            @discord.ui.button(label="⚔️ Inscrever-se!", style=discord.ButtonStyle.success,
                               custom_id=f"torneio_ins_{torneio['id']}")
            async def btn(self, inter, b): await _inscrever(inter, torneio["id"])

        guild = self.dados["guild"]
        canal = guild.get_channel(self.dados["canal_id"]) or interaction.channel
        msg = await canal.send(embed=embed, view=InscreverView())
        async with pool.acquire() as conn:
            await conn.execute("UPDATE torneios SET msg_id=$1, canal_id=$2 WHERE id=$3",
                msg.id, canal.id, torneio["id"])

        await interaction.followup.send(
            f"✅ Torneio **{self.dados['nome']}** criado! ID: `{torneio['id']}`\n"
            f"Inscricoes abertas por **{dur_txt}**.\n"
            f"Use `/torneio-fechar-inscricoes {torneio['id']}` para fechar e montar as chaves.",
            ephemeral=True
        )
        asyncio.create_task(_agendar_fechamento(torneio["id"], horas*3600, guild))


async def _agendar_fechamento(tid, seg, guild):
    await asyncio.sleep(seg)
    await fechar_inscricoes(tid, guild)

async def _inscrever(interaction: discord.Interaction, torneio_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        t = await conn.fetchrow("SELECT * FROM torneios WHERE id=$1", torneio_id)
        if not t or t["status"] != "inscricoes":
            await interaction.response.send_message("Inscricoes encerradas!", ephemeral=True); return
        p = await conn.fetchrow("SELECT * FROM personagens WHERE user_id=$1", interaction.user.id)
        if not p:
            await interaction.response.send_message("Crie seu personagem primeiro!", ephemeral=True); return
        ex = await conn.fetchrow("SELECT id FROM torneio_inscritos WHERE torneio_id=$1 AND user_id=$2",
            torneio_id, interaction.user.id)
        if ex:
            await interaction.response.send_message("Voce ja esta inscrito!", ephemeral=True); return
        if t["valor_inscricao"] > 0:
            if p["moedas"] < t["valor_inscricao"]:
                await interaction.response.send_message(
                    f"Moedas insuficientes! Precisa de {t['valor_inscricao']} moedas.", ephemeral=True); return
            await conn.execute("UPDATE personagens SET moedas=moedas-$1 WHERE user_id=$2",
                t["valor_inscricao"], interaction.user.id)
        from catalogo import get_rank
        rank = get_rank(p["nivel"])["rank"]
        await conn.execute(
            "INSERT INTO torneio_inscritos(torneio_id,user_id,nome,nivel,rank) VALUES($1,$2,$3,$4,$5)",
            torneio_id, interaction.user.id, p["nome"], p["nivel"], rank)
        total = await conn.fetchval("SELECT COUNT(*) FROM torneio_inscritos WHERE torneio_id=$1", torneio_id)
    await interaction.response.send_message(
        f"✅ Inscrito em **{t['nome']}**! ({total} inscritos) Boa sorte! ⚔️", ephemeral=True)

async def fechar_inscricoes(torneio_id: int, guild):
    pool = await get_pool()
    async with pool.acquire() as conn:
        t = await conn.fetchrow("SELECT * FROM torneios WHERE id=$1 AND status='inscricoes'", torneio_id)
        if not t: return
        inscritos = await conn.fetch(
            "SELECT * FROM torneio_inscritos WHERE torneio_id=$1 ORDER BY nivel DESC", torneio_id)
        if len(inscritos) < 2:
            await conn.execute("UPDATE torneios SET status='cancelado' WHERE id=$1", torneio_id)
            canal = guild.get_channel(t["canal_id"])
            if canal: await canal.send(f"❌ Torneio **{t['nome']}** cancelado — inscritos insuficientes.")
            return
        n    = len(inscritos)
        pot2 = proxima_potencia_2(n)
        byes = pot2 - n
        fase = nome_fase(pot2 // 2)
        luta_num = 1
        jogadores = list(inscritos)
        for i in range(byes):
            await conn.execute(
                "INSERT INTO torneio_lutas(torneio_id,fase,luta_num,user1_id,user2_id,vencedor_id,bye,concluida) VALUES($1,$2,$3,$4,$4,$4,TRUE,TRUE)",
                torneio_id, fase, luta_num, jogadores[i]["user_id"])
            luta_num += 1
        restantes = jogadores[byes:]
        for i in range(0, len(restantes)-1, 2):
            await conn.execute(
                "INSERT INTO torneio_lutas(torneio_id,fase,luta_num,user1_id,user2_id) VALUES($1,$2,$3,$4,$5)",
                torneio_id, fase, luta_num, restantes[i]["user_id"], restantes[i+1]["user_id"])
            luta_num += 1
        await conn.execute("UPDATE torneios SET status='em_andamento' WHERE id=$1", torneio_id)
    canal = guild.get_channel(t["canal_id"])
    if canal:
        embed = discord.Embed(
            title=f"⚔️ {t['nome']} — Chaves Montadas!",
            description=f"**{n} jogadores** inscritos!{f' ({byes} bye(s) automatico(s) para os melhores rankeados).' if byes else ''}\n\nUse `/torneio-status {torneio_id}` para ver as chaves.\nAdmin: `/torneio-lutar` para iniciar cada luta!",
            color=0xE4AF3C
        )
        await canal.send(embed=embed)

async def _registrar_vencedor(torneio_id, luta_id, vencedor_id, guild):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("UPDATE torneio_lutas SET vencedor_id=$1, concluida=TRUE WHERE id=$2",
            vencedor_id, luta_id)
        luta = await conn.fetchrow("SELECT * FROM torneio_lutas WHERE id=$1", luta_id)
        if luta:
            perdedor_id = luta["user2_id"] if luta["user1_id"] == vencedor_id else luta["user1_id"]
            await conn.execute("UPDATE torneio_inscritos SET eliminado=TRUE WHERE torneio_id=$1 AND user_id=$2",
                torneio_id, perdedor_id)
        t   = await conn.fetchrow("SELECT * FROM torneios WHERE id=$1", torneio_id)
        fase_atual = luta["fase"] if luta else ""
        pendentes  = await conn.fetchval(
            "SELECT COUNT(*) FROM torneio_lutas WHERE torneio_id=$1 AND fase=$2 AND NOT concluida",
            torneio_id, fase_atual)
        if pendentes == 0:
            vencedores = [r["vencedor_id"] for r in await conn.fetch(
                "SELECT vencedor_id FROM torneio_lutas WHERE torneio_id=$1 AND fase=$2",
                torneio_id, fase_atual)]
            if len(vencedores) == 1:
                await conn.execute("UPDATE torneios SET status='finalizado' WHERE id=$1", torneio_id)
                await _premiar(t, vencedores[0], torneio_id, guild, conn)
            elif len(vencedores) >= 2:
                prox = nome_fase(len(vencedores) // 2)
                for i in range(0, len(vencedores)-1, 2):
                    await conn.execute(
                        "INSERT INTO torneio_lutas(torneio_id,fase,luta_num,user1_id,user2_id) VALUES($1,$2,$3,$4,$5)",
                        torneio_id, prox, i//2+1, vencedores[i], vencedores[i+1])
                canal = guild.get_channel(t["canal_id"])
                if canal:
                    await canal.send(embed=discord.Embed(
                        title=f"⚔️ Fase concluida! Proxima: {prox}",
                        description=f"Use `/torneio-status {torneio_id}` para ver as novas lutas!",
                        color=0xE4AF3C))

async def _premiar(t, campeao_id, torneio_id, guild, conn):
    await _dar_premio(guild, campeao_id, t["premio_1"])
    semi = await conn.fetch(
        "SELECT * FROM torneio_lutas WHERE torneio_id=$1 AND fase='Semifinal'", torneio_id)
    perdedores = [l["user1_id"] if l["user2_id"]==l["vencedor_id"] else l["user2_id"] for l in semi]
    perdedores = [p for p in perdedores if p != campeao_id]
    if perdedores and t["premio_2"]: await _dar_premio(guild, perdedores[0], t["premio_2"])
    if len(perdedores) > 1 and t["premio_3"]: await _dar_premio(guild, perdedores[1], t["premio_3"])
    canal = guild.get_channel(t["canal_id"])
    if canal:
        m = guild.get_member(campeao_id)
        embed = discord.Embed(
            title=f"🏆 {t['nome']} — CAMPEAO!",
            description=f"🥇 {m.mention if m else campeao_id} e o grande campeao!\n**Premio:** {t['premio_1']}",
            color=0xE4AF3C)
        if t["imagem_url"]: embed.set_image(url=t["imagem_url"])
        await canal.send(embed=embed)

async def _dar_premio(guild, user_id, premio_str):
    if not premio_str: return
    pool = await get_pool()
    try:
        async with pool.acquire() as conn:
            p = await conn.fetchrow("SELECT * FROM personagens WHERE user_id=$1", user_id)
            if not p: return
            s = premio_str.lower()
            if "moedas" in s or s.strip().isdigit():
                qtd = int(''.join(filter(str.isdigit, s)) or "0")
                if qtd: await conn.execute("UPDATE personagens SET moedas=moedas+$1 WHERE user_id=$2", qtd, user_id)
            elif "xp" in s:
                qtd = int(''.join(filter(str.isdigit, s)) or "0")
                if qtd: await conn.execute("UPDATE personagens SET xp=xp+$1 WHERE user_id=$2", qtd, user_id)
            elif "ficha" in s or "giro" in s:
                qtd = int(''.join(filter(str.isdigit, s)) or "1")
                await conn.execute("""
                    INSERT INTO giros(user_id,roleta_id,raridade,quantidade)
                    VALUES($1,'skill','Lendario',$2)
                    ON CONFLICT(user_id,roleta_id,raridade)
                    DO UPDATE SET quantidade=giros.quantidade+$2
                """, user_id, qtd)
            elif "cargo" in s:
                nome_cargo = premio_str.split(":")[-1].strip()
                member = guild.get_member(user_id)
                if member:
                    cargo = discord.utils.get(guild.roles, name=nome_cargo)
                    if cargo: await member.add_roles(cargo)
    except Exception as e:
        print(f"Erro ao dar premio: {e}")

# ─── COMANDOS ────────────────────────────────────────────────────

async def cmd_torneio_criar(interaction: discord.Interaction):
    await interaction.response.send_modal(TorneioModal1())

async def cmd_torneio_status(interaction: discord.Interaction, torneio_id: int):
    await interaction.response.defer()
    pool = await get_pool()
    async with pool.acquire() as conn:
        t = await conn.fetchrow("SELECT * FROM torneios WHERE id=$1", torneio_id)
        if not t:
            await interaction.followup.send("Torneio nao encontrado!", ephemeral=True); return
        ativos = await conn.fetchval("SELECT COUNT(*) FROM torneio_inscritos WHERE torneio_id=$1 AND NOT eliminado", torneio_id)
        lutas  = await conn.fetch("SELECT * FROM torneio_lutas WHERE torneio_id=$1 ORDER BY fase,luta_num", torneio_id)
    status_map = {"inscricoes":"📋 Inscricoes","em_andamento":"⚔️ Em andamento","finalizado":"🏆 Finalizado","cancelado":"❌ Cancelado"}
    embed = discord.Embed(title=f"🏆 {t['nome']}",
        description=f"**Status:** {status_map.get(t['status'],t['status'])} | **Ativos:** {ativos}", color=0xE4AF3C)
    if t["status"]=="inscricoes" and t["fim_inscricoes"]:
        embed.add_field(name="Encerra em", value=f"<t:{int(t['fim_inscricoes'].timestamp())}:R>", inline=True)
    if t["premio_1"]: embed.add_field(name="🥇", value=t["premio_1"], inline=True)
    if t["premio_2"]: embed.add_field(name="🥈", value=t["premio_2"], inline=True)
    if t["premio_3"]: embed.add_field(name="🥉", value=t["premio_3"], inline=True)
    fases = {}
    for l in lutas: fases.setdefault(l["fase"],[]).append(l)
    for fase, fl in fases.items():
        txt = ""
        for l in fl:
            if l["bye"]: txt += f"➡️ BYE: <@{l['user1_id']}>\n"
            elif l["concluida"]: txt += f"✅ <@{l['user1_id']}> vs <@{l['user2_id']}> → **<@{l['vencedor_id']}>**\n"
            else: txt += f"⏳ <@{l['user1_id']}> vs <@{l['user2_id']}>\n"
        if txt: embed.add_field(name=fase, value=txt[:1000], inline=False)
    if t["imagem_url"]: embed.set_image(url=t["imagem_url"])
    await interaction.followup.send(embed=embed)

async def cmd_torneio_lutar(interaction: discord.Interaction, torneio_id: int,
                             jogador1: discord.Member, jogador2: discord.Member):
    await interaction.response.defer()
    pool = await get_pool()
    async with pool.acquire() as conn:
        t = await conn.fetchrow("SELECT * FROM torneios WHERE id=$1 AND status='em_andamento'", torneio_id)
        if not t:
            await interaction.followup.send("Torneio nao ativo!", ephemeral=True); return
        luta = await conn.fetchrow(
            "SELECT * FROM torneio_lutas WHERE torneio_id=$1 AND NOT concluida AND ((user1_id=$2 AND user2_id=$3) OR (user1_id=$3 AND user2_id=$2))",
            torneio_id, jogador1.id, jogador2.id)
        if not luta:
            await interaction.followup.send("Luta nao encontrada nas chaves!", ephemeral=True); return
        p1 = await conn.fetchrow("SELECT * FROM personagens WHERE user_id=$1", jogador1.id)
        p2 = await conn.fetchrow("SELECT * FROM personagens WHERE user_id=$1", jogador2.id)
    if not p1 or not p2:
        await interaction.followup.send("Um dos jogadores nao tem personagem!", ephemeral=True); return
    from batalha import rodar_pvp, ARENAS
    import random
    arena = random.choice(ARENAS)
    embed_i = discord.Embed(
        title=f"⚔️ {t['nome']} — {luta['fase']}",
        description=f"**{jogador1.display_name}** ⚔️ **{jogador2.display_name}**\nArena: {arena['emoji']} {arena['nome']}",
        color=0xE4AF3C)
    await interaction.followup.send(embed=embed_i)
    await rodar_pvp(interaction.channel, p1, p2, jogador1, jogador2, arena,
        callback=lambda vid: _registrar_vencedor(torneio_id, luta["id"], vid, interaction.guild))

async def cmd_torneio_fechar_inscricoes(interaction: discord.Interaction, torneio_id: int):
    await interaction.response.defer(ephemeral=True)
    await fechar_inscricoes(torneio_id, interaction.guild)
    await interaction.followup.send(f"✅ Inscricoes do torneio #{torneio_id} encerradas e chaves montadas!", ephemeral=True)

async def cmd_torneio_cancelar(interaction: discord.Interaction, torneio_id: int):
    await interaction.response.defer(ephemeral=True)
    pool = await get_pool()
    async with pool.acquire() as conn:
        t = await conn.fetchrow("SELECT * FROM torneios WHERE id=$1", torneio_id)
        if not t:
            await interaction.followup.send("Torneio nao encontrado!", ephemeral=True); return
        if t["valor_inscricao"] > 0:
            ins = await conn.fetch("SELECT user_id FROM torneio_inscritos WHERE torneio_id=$1", torneio_id)
            for i in ins:
                await conn.execute("UPDATE personagens SET moedas=moedas+$1 WHERE user_id=$2",
                    t["valor_inscricao"], i["user_id"])
        await conn.execute("UPDATE torneios SET status='cancelado' WHERE id=$1", torneio_id)
    canal = interaction.guild.get_channel(t["canal_id"])
    if canal: await canal.send(f"❌ Torneio **{t['nome']}** cancelado. Inscricoes devolvidas.")
    await interaction.followup.send(f"✅ Torneio #{torneio_id} cancelado!", ephemeral=True)
