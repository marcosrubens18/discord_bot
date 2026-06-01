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
                fase TEXT DEFAULT '',
                luta_num INTEGER DEFAULT 1,
                user1_id BIGINT DEFAULT 0,
                user2_id BIGINT DEFAULT 0,
                vencedor_id BIGINT DEFAULT 0,
                bye BOOLEAN DEFAULT FALSE,
                concluida BOOLEAN DEFAULT FALSE
            )
        """)
    print("DB torneio OK!")

# ─── HELPERS ──────────────────────────────────────────────────────

def proxima_potencia_2(n):
    p = 1
    while p < n: p *= 2
    return p

def nome_fase(total_lutas):
    if total_lutas == 1: return "Final"
    if total_lutas == 2: return "Semifinal"
    if total_lutas == 4: return "Quartas de Final"
    if total_lutas == 8: return "Oitavas de Final"
    return f"Rodada de {total_lutas}"

async def entregar_premio_torneio(guild, user_id, premio_str):
    if not premio_str or not premio_str.strip(): return
    pool = await get_pool()
    try:
        async with pool.acquire() as conn:
            p = await conn.fetchrow("SELECT * FROM personagens WHERE user_id=$1", user_id)
            if not p: return
            s = premio_str.lower().strip()
            if "moedas" in s or s.replace(" ","").isdigit():
                qtd = int("".join(filter(str.isdigit, s)) or "0")
                if qtd: await conn.execute(
                    "UPDATE personagens SET moedas=moedas+$1 WHERE user_id=$2", qtd, user_id)
            elif "xp" in s:
                qtd = int("".join(filter(str.isdigit, s)) or "0")
                if qtd: await conn.execute(
                    "UPDATE personagens SET xp=xp+$1 WHERE user_id=$2", qtd, user_id)
            elif "ficha" in s or "giro" in s:
                qtd = int("".join(filter(str.isdigit, s)) or "1")
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
        print(f"Erro premio torneio: {e}")

# ─── MODAL UNICO ──────────────────────────────────────────────────

class TorneioModal(discord.ui.Modal, title="Criar Torneio"):
    nome_input = discord.ui.TextInput(
        label="Nome do Torneio",
        placeholder="Ex: Copa Villa Eldoria",
        max_length=80
    )
    descricao_input = discord.ui.TextInput(
        label="Descricao",
        style=discord.TextStyle.paragraph,
        placeholder="Descricao do torneio...",
        max_length=300
    )
    valor_horas_input = discord.ui.TextInput(
        label="Inscricao (moedas) | Duracao (horas)",
        placeholder="Ex: 500|24  ou  0|48  (0 = gratuito)",
        max_length=20
    )
    premios_input = discord.ui.TextInput(
        label="Premios: 1o|2o|3o (2o e 3o opcionais)",
        placeholder="Ex: 10000 moedas|5000 moedas|2000 moedas",
        max_length=200
    )
    imagem_input = discord.ui.TextInput(
        label="URL da Imagem (opcional)",
        placeholder="https://i.imgur.com/xxx.png",
        required=False,
        max_length=200
    )

    def __init__(self, guild):
        super().__init__()
        self.guild = guild

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await init_db_torneio()

        # Parse valor|horas
        valor, horas = 0, 24
        try:
            partes = str(self.valor_horas_input).split("|")
            valor = int(partes[0].strip()) if partes[0].strip().isdigit() else 0
            horas = int(partes[1].strip()) if len(partes) > 1 and partes[1].strip().isdigit() else 24
        except: pass

        # Parse premios
        partes_p = [x.strip() for x in str(self.premios_input).split("|")]
        p1 = partes_p[0] if len(partes_p) > 0 else ""
        p2 = partes_p[1] if len(partes_p) > 1 else ""
        p3 = partes_p[2] if len(partes_p) > 2 else ""

        img_url = str(self.imagem_input).strip() if self.imagem_input else ""
        fim     = datetime.utcnow() + timedelta(hours=horas)
        dur_txt = f"{horas}h" if horas < 24 else f"{horas//24}d"

        pool = await get_pool()
        async with pool.acquire() as conn:
            torneio = await conn.fetchrow("""
                INSERT INTO torneios
                (nome,descricao,imagem_url,canal_id,valor_inscricao,
                 fim_inscricoes,premio_1,premio_2,premio_3,status,criado_por)
                VALUES($1,$2,$3,0,$4,$5,$6,$7,$8,'inscricoes',$9) RETURNING *
            """, str(self.nome_input), str(self.descricao_input), img_url,
                valor, fim, p1, p2, p3, interaction.user.id)

        # ChannelSelect para escolher canal
        class CanalView(discord.ui.View):
            def __init__(self_v): super().__init__(timeout=120)

            @discord.ui.select(
                cls=discord.ui.ChannelSelect,
                placeholder="Escolha o canal de anuncio...",
                
            )
            async def sel(self_v, inter: discord.Interaction, s: discord.ui.ChannelSelect):
                if inter.user.id != interaction.user.id:
                    await inter.response.defer(); return
                canal_raw = s.values[0]
                canal = interaction.guild.get_channel(canal_raw.id) or canal_raw

                # Monta embed de anuncio
                embed = discord.Embed(
                    title=f"🏆 {str(self.nome_input)}",
                    description=str(self.descricao_input),
                    color=0xE4AF3C
                )
                embed.add_field(
                    name="Inscricao",
                    value=f"{valor} moedas" if valor else "Gratuita",
                    inline=True
                )
                embed.add_field(
                    name="Inscricoes ate",
                    value=f"<t:{int(fim.timestamp())}:R>",
                    inline=True
                )
                if p1: embed.add_field(name="1 Lugar", value=p1, inline=False)
                if p2: embed.add_field(name="2 Lugar", value=p2, inline=False)
                if p3: embed.add_field(name="3 Lugar", value=p3, inline=False)
                embed.set_footer(text=f"Torneio #{torneio['id']} | Clique para se inscrever!")
                if img_url: embed.set_image(url=img_url)

                class InscreverView(discord.ui.View):
                    def __init__(self):
                        super().__init__(timeout=None)
                    @discord.ui.button(
                        label="Inscrever-se!",
                        style=discord.ButtonStyle.success,
                        custom_id=f"torneio_ins_{torneio['id']}"
                    )
                    async def btn(self, inter2: discord.Interaction, b):
                        await _inscrever(inter2, torneio["id"])

                msg = await canal.send(embed=embed, view=InscreverView())
                pool2 = await get_pool()
                async with pool2.acquire() as conn2:
                    await conn2.execute(
                        "UPDATE torneios SET msg_id=$1, canal_id=$2 WHERE id=$3",
                        msg.id, canal.id, torneio["id"])

                await inter.response.send_message(
                    f"Torneio **{str(self.nome_input)}** criado! ID: `{torneio['id']}`\n"
                    f"Inscricoes abertas por **{dur_txt}** em {canal.mention}\n\n"
                    f"Use `/torneio-fechar-inscricoes {torneio['id']}` quando quiser fechar.",
                    ephemeral=True
                )
                self_v.stop()
                asyncio.create_task(
                    _agendar_fechamento(torneio["id"], horas*3600, self.guild))

        await interaction.followup.send(
            "Escolha o canal onde o torneio sera anunciado:",
            view=CanalView(),
            ephemeral=True
        )

# ─── INSCRICAO ────────────────────────────────────────────────────

async def _inscrever(interaction: discord.Interaction, torneio_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        t = await conn.fetchrow(
            "SELECT * FROM torneios WHERE id=$1 AND status='inscricoes'", torneio_id)
        if not t:
            await interaction.response.send_message(
                "Inscricoes encerradas!", ephemeral=True); return
        p = await conn.fetchrow(
            "SELECT * FROM personagens WHERE user_id=$1", interaction.user.id)
        if not p:
            await interaction.response.send_message(
                "Crie seu personagem primeiro!", ephemeral=True); return
        ex = await conn.fetchrow(
            "SELECT id FROM torneio_inscritos WHERE torneio_id=$1 AND user_id=$2",
            torneio_id, interaction.user.id)
        if ex:
            await interaction.response.send_message(
                "Voce ja esta inscrito!", ephemeral=True); return
        if t["valor_inscricao"] > 0:
            if p["moedas"] < t["valor_inscricao"]:
                await interaction.response.send_message(
                    f"Moedas insuficientes! Precisa de {t['valor_inscricao']}.", ephemeral=True); return
            await conn.execute(
                "UPDATE personagens SET moedas=moedas-$1 WHERE user_id=$2",
                t["valor_inscricao"], interaction.user.id)
        from catalogo import get_rank
        rank = get_rank(p["nivel"])["rank"]
        await conn.execute(
            "INSERT INTO torneio_inscritos(torneio_id,user_id,nome,nivel,rank) VALUES($1,$2,$3,$4,$5)",
            torneio_id, interaction.user.id, p["nome"], p["nivel"], rank)
        total = await conn.fetchval(
            "SELECT COUNT(*) FROM torneio_inscritos WHERE torneio_id=$1", torneio_id)
    await interaction.response.send_message(
        f"Inscrito no **{t['nome']}**! Total: {total} inscritos. Boa sorte!",
        ephemeral=True)

# ─── FECHAR INSCRICOES ────────────────────────────────────────────

async def fechar_inscricoes(torneio_id: int, guild):
    pool = await get_pool()
    async with pool.acquire() as conn:
        t = await conn.fetchrow(
            "SELECT * FROM torneios WHERE id=$1 AND status='inscricoes'", torneio_id)
        if not t: return
        inscritos = await conn.fetch(
            "SELECT * FROM torneio_inscritos WHERE torneio_id=$1 ORDER BY nivel DESC",
            torneio_id)
        if len(inscritos) < 2:
            await conn.execute(
                "UPDATE torneios SET status='cancelado' WHERE id=$1", torneio_id)
            canal = guild.get_channel(t["canal_id"])
            if canal:
                await canal.send(f"Torneio **{t['nome']}** cancelado — inscritos insuficientes.")
            return

        n = len(inscritos)
        pot2 = proxima_potencia_2(n)
        byes = pot2 - n
        fase = nome_fase(pot2 // 2)
        luta_num = 1
        lista = list(inscritos)

        # Byes para os melhores rankeados
        for i in range(byes):
            await conn.execute(
                "INSERT INTO torneio_lutas(torneio_id,fase,luta_num,user1_id,user2_id,vencedor_id,bye,concluida) VALUES($1,$2,$3,$4,$4,$4,TRUE,TRUE)",
                torneio_id, fase, luta_num, lista[i]["user_id"])
            luta_num += 1

        # Pares com os restantes
        restantes = lista[byes:]
        for i in range(0, len(restantes)-1, 2):
            await conn.execute(
                "INSERT INTO torneio_lutas(torneio_id,fase,luta_num,user1_id,user2_id) VALUES($1,$2,$3,$4,$5)",
                torneio_id, fase, luta_num,
                restantes[i]["user_id"], restantes[i+1]["user_id"])
            luta_num += 1

        await conn.execute(
            "UPDATE torneios SET status='em_andamento' WHERE id=$1", torneio_id)

    canal = guild.get_channel(t["canal_id"])
    if canal:
        embed = discord.Embed(
            title=f"Torneio {t['nome']} — Chaves Montadas!",
            description=f"**{n} jogadores** inscritos!{f' ({byes} bye(s) automatico)' if byes else ''}\n\n"
                       f"Use `/torneio-status {torneio_id}` para ver as chaves.\n"
                       f"Admin usa `/torneio-lutar` para iniciar cada luta.",
            color=0xE4AF3C
        )
        await canal.send(embed=embed)

async def _agendar_fechamento(torneio_id, segundos, guild):
    await asyncio.sleep(segundos)
    await fechar_inscricoes(torneio_id, guild)

# ─── COMANDOS EXPORTADOS ──────────────────────────────────────────

async def cmd_torneio_criar(interaction: discord.Interaction):
    await interaction.response.send_modal(TorneioModal(interaction.guild))

async def cmd_torneio_status(interaction: discord.Interaction, torneio_id: int):
    await interaction.response.defer()
    pool = await get_pool()
    async with pool.acquire() as conn:
        t = await conn.fetchrow("SELECT * FROM torneios WHERE id=$1", torneio_id)
        if not t:
            await interaction.followup.send("Torneio nao encontrado!", ephemeral=True); return
        inscritos = await conn.fetchval(
            "SELECT COUNT(*) FROM torneio_inscritos WHERE torneio_id=$1 AND NOT eliminado", torneio_id)
        lutas = await conn.fetch(
            "SELECT * FROM torneio_lutas WHERE torneio_id=$1 ORDER BY fase,luta_num", torneio_id)

    status_map = {
        "inscricoes":   "📋 Inscricoes abertas",
        "em_andamento": "Combates em andamento",
        "finalizado":   "Finalizado",
        "cancelado":    "Cancelado"
    }
    embed = discord.Embed(
        title=f"🏆 {t['nome']}",
        color=0xE4AF3C,
        description=f"**Status:** {status_map.get(t['status'], t['status'])}\n"
                   f"**Jogadores ativos:** {inscritos}"
    )
    if t["status"] == "inscricoes" and t["fim_inscricoes"]:
        embed.add_field(name="Inscricoes ate",
            value=f"<t:{int(t['fim_inscricoes'].timestamp())}:R>", inline=True)
    if t["premio_1"]: embed.add_field(name="1 Lugar", value=t["premio_1"], inline=True)
    if t["premio_2"]: embed.add_field(name="2 Lugar", value=t["premio_2"], inline=True)
    if t["premio_3"]: embed.add_field(name="3 Lugar", value=t["premio_3"], inline=True)

    if lutas:
        fases = {}
        for l in lutas:
            fases.setdefault(l["fase"], []).append(l)
        for fase, fl in fases.items():
            txt = ""
            for l in fl:
                if l["bye"]:
                    txt += f"BYE: <@{l['user1_id']}>\n"
                elif l["concluida"]:
                    txt += f"<@{l['user1_id']}> vs <@{l['user2_id']}> → **<@{l['vencedor_id']}>**\n"
                else:
                    txt += f"<@{l['user1_id']}> vs <@{l['user2_id']}> (pendente)\n"
            if txt:
                embed.add_field(name=fase, value=txt[:1000], inline=False)

    if t["imagem_url"]: embed.set_image(url=t["imagem_url"])
    await interaction.followup.send(embed=embed)

async def cmd_torneio_lutar(interaction: discord.Interaction, torneio_id: int,
                             jogador1: discord.Member, jogador2: discord.Member):
    await interaction.response.defer()
    pool = await get_pool()
    async with pool.acquire() as conn:
        t = await conn.fetchrow(
            "SELECT * FROM torneios WHERE id=$1 AND status='em_andamento'", torneio_id)
        if not t:
            await interaction.followup.send(
                "Torneio nao encontrado ou nao em andamento!", ephemeral=True); return
        # Busca luta nas chaves (qualquer ordem)
        luta = await conn.fetchrow("""
            SELECT * FROM torneio_lutas
            WHERE torneio_id=$1 AND NOT concluida
            AND ((user1_id=$2 AND user2_id=$3) OR (user1_id=$3 AND user2_id=$2))
        """, torneio_id, jogador1.id, jogador2.id)
        if not luta:
            await interaction.followup.send(
                "Luta nao encontrada nas chaves!", ephemeral=True); return
        p1 = await conn.fetchrow("SELECT * FROM personagens WHERE user_id=$1", jogador1.id)
        p2 = await conn.fetchrow("SELECT * FROM personagens WHERE user_id=$1", jogador2.id)

    if not p1 or not p2:
        await interaction.followup.send("Um dos jogadores nao tem personagem!", ephemeral=True); return

    from batalha import rodar_pvp, ARENAS
    import random
    arena = random.choice(ARENAS)
    embed_i = discord.Embed(
        title=f"Torneio {t['nome']} — {luta['fase']}",
        description=f"**{jogador1.display_name}** vs **{jogador2.display_name}**",
        color=0xE4AF3C
    )
    await interaction.followup.send(embed=embed_i)

    luta_id = luta["id"]
    async def registrar(venc_id):
        await _registrar_vencedor(torneio_id, luta_id, venc_id, interaction.guild)

    await rodar_pvp(interaction.channel, p1, p2, jogador1, jogador2, arena, callback=registrar)

async def _registrar_vencedor(torneio_id, luta_id, vencedor_id, guild):
    pool = await get_pool()
    async with pool.acquire() as conn:
        luta = await conn.fetchrow("SELECT * FROM torneio_lutas WHERE id=$1", luta_id)
        if not luta: return
        perdedor_id = luta["user2_id"] if luta["user1_id"] == vencedor_id else luta["user1_id"]
        await conn.execute(
            "UPDATE torneio_lutas SET vencedor_id=$1, concluida=TRUE WHERE id=$2",
            vencedor_id, luta_id)
        await conn.execute(
            "UPDATE torneio_inscritos SET eliminado=TRUE WHERE torneio_id=$1 AND user_id=$2",
            torneio_id, perdedor_id)

        # Verifica se a fase terminou
        fase = luta["fase"]
        pendentes = await conn.fetchval(
            "SELECT COUNT(*) FROM torneio_lutas WHERE torneio_id=$1 AND fase=$2 AND NOT concluida",
            torneio_id, fase)
        if pendentes > 0: return

        # Pega vencedores da fase
        vencedores = await conn.fetch(
            "SELECT vencedor_id FROM torneio_lutas WHERE torneio_id=$1 AND fase=$2",
            torneio_id, fase)
        ids_v = [v["vencedor_id"] for v in vencedores]

        if len(ids_v) == 1:
            # Campeao!
            await conn.execute("UPDATE torneios SET status='finalizado' WHERE id=$1", torneio_id)
            t = await conn.fetchrow("SELECT * FROM torneios WHERE id=$1", torneio_id)
            # Top 3
            semifinalistas = await conn.fetch("""
                SELECT user1_id, user2_id, vencedor_id FROM torneio_lutas
                WHERE torneio_id=$1 AND fase='Semifinal'
            """, torneio_id)
            segundo = terceiro = None
            for l in semifinalistas:
                perd = l["user2_id"] if l["user1_id"]==l["vencedor_id"] else l["user1_id"]
                if segundo is None: segundo = perd
                elif terceiro is None: terceiro = perd
            # Entrega premios
            await entregar_premio_torneio(guild, ids_v[0], t["premio_1"])
            if segundo and t["premio_2"]:
                await entregar_premio_torneio(guild, segundo, t["premio_2"])
            if terceiro and t["premio_3"]:
                await entregar_premio_torneio(guild, terceiro, t["premio_3"])
            # Anuncia
            canal = guild.get_channel(t["canal_id"])
            if canal:
                campeao = guild.get_member(ids_v[0])
                await canal.send(embed=discord.Embed(
                    title=f"Torneio {t['nome']} — CAMPEAO!",
                    description=f"🏆 **{campeao.mention if campeao else ids_v[0]}** e o grande campeao!\nPremio: **{t['premio_1']}**",
                    color=0xE4AF3C))
        elif len(ids_v) >= 2:
            # Proxima fase
            prox = nome_fase(len(ids_v) // 2)
            for i in range(0, len(ids_v)-1, 2):
                await conn.execute(
                    "INSERT INTO torneio_lutas(torneio_id,fase,luta_num,user1_id,user2_id) VALUES($1,$2,$3,$4,$5)",
                    torneio_id, prox, i//2+1, ids_v[i], ids_v[i+1])
            t = await conn.fetchrow("SELECT * FROM torneios WHERE id=$1", torneio_id)
            canal = guild.get_channel(t["canal_id"])
            if canal:
                await canal.send(embed=discord.Embed(
                    title=f"Fase anterior concluida!",
                    description=f"Proxima fase: **{prox}**\nUse `/torneio-status {torneio_id}` para ver as chaves.",
                    color=0xE4AF3C))

async def cmd_torneio_fechar_inscricoes(interaction: discord.Interaction, torneio_id: int):
    await interaction.response.defer(ephemeral=True)
    await fechar_inscricoes(torneio_id, interaction.guild)
    await interaction.followup.send(
        f"Inscricoes do torneio #{torneio_id} encerradas! Chaves montadas.", ephemeral=True)

async def cmd_torneio_cancelar(interaction: discord.Interaction, torneio_id: int):
    await interaction.response.defer(ephemeral=True)
    pool = await get_pool()
    async with pool.acquire() as conn:
        t = await conn.fetchrow("SELECT * FROM torneios WHERE id=$1", torneio_id)
        if not t:
            await interaction.followup.send("Torneio nao encontrado!", ephemeral=True); return
        if t["valor_inscricao"] > 0:
            inscritos = await conn.fetch(
                "SELECT user_id FROM torneio_inscritos WHERE torneio_id=$1", torneio_id)
            for ins in inscritos:
                await conn.execute(
                    "UPDATE personagens SET moedas=moedas+$1 WHERE user_id=$2",
                    t["valor_inscricao"], ins["user_id"])
        await conn.execute("UPDATE torneios SET status='cancelado' WHERE id=$1", torneio_id)
    canal = interaction.guild.get_channel(t["canal_id"])
    if canal:
        await canal.send(
            f"Torneio **{t['nome']}** foi cancelado. Inscricoes devolvidas.")
    await interaction.followup.send(f"Torneio #{torneio_id} cancelado!", ephemeral=True)
