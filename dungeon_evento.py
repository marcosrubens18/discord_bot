# dungeon_evento.py — Dungeons customizadas de evento
import discord
import asyncio
import random
from datetime import datetime, timedelta
from db import get_pool

# ─── DB ───────────────────────────────────────────────────────────

async def init_db_dungeon_evento():
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS dungeons_evento (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                descricao TEXT DEFAULT '',
                imagem_url TEXT DEFAULT '',
                canal_id BIGINT DEFAULT 0,
                msg_id BIGINT DEFAULT 0,
                rank_minimo TEXT DEFAULT 'F',
                modo_fechamento TEXT DEFAULT 'tempo',
                dias_aberta INTEGER DEFAULT 7,
                max_tentativas INTEGER DEFAULT 0,
                premio TEXT DEFAULT '',
                status TEXT DEFAULT 'inativa',
                criado_por BIGINT,
                fechada_em TIMESTAMP
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS dungeon_evento_andares (
                id SERIAL PRIMARY KEY,
                dungeon_id INTEGER REFERENCES dungeons_evento(id),
                numero INTEGER,
                nome_monstro TEXT,
                emoji_monstro TEXT DEFAULT '👹',
                hp INTEGER DEFAULT 100,
                ataque INTEGER DEFAULT 20,
                defesa INTEGER DEFAULT 5,
                loot_desc TEXT DEFAULT '',
                loot_item_id TEXT DEFAULT '',
                loot_item_nome TEXT DEFAULT '',
                loot_item_emoji TEXT DEFAULT '📦',
                loot_item_tipo TEXT DEFAULT 'material',
                loot_item_raridade TEXT DEFAULT 'Raro',
                eh_boss BOOLEAN DEFAULT FALSE,
                UNIQUE(dungeon_id, numero)
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS dungeon_evento_runs (
                id SERIAL PRIMARY KEY,
                dungeon_id INTEGER REFERENCES dungeons_evento(id),
                user_id BIGINT,
                tentativa INTEGER DEFAULT 1,
                concluida BOOLEAN DEFAULT FALSE,
                falhou BOOLEAN DEFAULT FALSE,
                iniciada_em TIMESTAMP DEFAULT NOW(),
                UNIQUE(dungeon_id, user_id, tentativa)
            )
        """)
    print("DB dungeon_evento OK!")

# ─── MODAL 1: INFO BASICA ─────────────────────────────────────────

class DungeonEventoModal1(discord.ui.Modal, title="Dungeon de Evento — Parte 1 de 3"):
    nome = discord.ui.TextInput(
        label="Nome da Dungeon",
        placeholder="Ex: Cripta do Lich Anciao",
        max_length=80
    )
    descricao = discord.ui.TextInput(
        label="Descricao / Historia",
        style=discord.TextStyle.paragraph,
        placeholder="Descreva a dungeon, a historia, o perigo...",
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
    premio = discord.ui.TextInput(
        label="Premio para quem completar",
        placeholder="Ex: 15000 moedas | ficha:3 | cargo:Conquistador",
        max_length=150
    )

    async def on_submit(self, interaction: discord.Interaction):
        self._dados = {
            "nome":       str(self.nome),
            "descricao":  str(self.descricao),
            "imagem_url": str(self.imagem_url) if self.imagem_url else "",
            "canal_id":   int(str(self.canal_id)) if str(self.canal_id).isdigit() else 0,
            "premio":     str(self.premio),
            "guild":      interaction.guild,
            "criado_por": interaction.user.id,
        }
        await interaction.response.send_modal(DungeonEventoModal2(self._dados))


# ─── MODAL 2: CONFIGURACAO ────────────────────────────────────────

class DungeonEventoModal2(discord.ui.Modal, title="Dungeon de Evento — Parte 2 de 3"):
    rank_minimo = discord.ui.TextInput(
        label="Rank Minimo para Entrar",
        placeholder="F | E | D | C | B | A | S | SS",
        max_length=2,
        default="F"
    )
    modo_fechamento = discord.ui.TextInput(
        label="Modo de Fechamento",
        placeholder="tempo | primeiro  (tempo = X dias, primeiro = fecha ao completar)",
        max_length=10,
        default="tempo"
    )
    dias_aberta = discord.ui.TextInput(
        label="Dias que fica aberta (se modo = tempo)",
        placeholder="Ex: 7 = 1 semana | 3 = 3 dias | 1 = 1 dia",
        max_length=3,
        default="7"
    )
    max_tentativas = discord.ui.TextInput(
        label="Max tentativas por jogador (0 = ilimitado)",
        placeholder="Ex: 0 = ilimitado | 1 = apenas 1 tentativa | 3 = 3 tentativas",
        max_length=3,
        default="0"
    )

    def __init__(self, dados: dict):
        super().__init__()
        self.dados = dados

    async def on_submit(self, interaction: discord.Interaction):
        ranks_validos = ["F","E","D","C","B","A","S","SS"]
        rank = str(self.rank_minimo).strip().upper()
        if rank not in ranks_validos: rank = "F"
        modo = "primeiro" if "primeiro" in str(self.modo_fechamento).lower() else "tempo"
        try: dias = int(str(self.dias_aberta))
        except: dias = 7
        try: max_tent = int(str(self.max_tentativas))
        except: max_tent = 0

        self.dados.update({
            "rank_minimo": rank,
            "modo_fechamento": modo,
            "dias_aberta": dias,
            "max_tentativas": max_tent,
        })
        await interaction.response.send_modal(DungeonEventoModal3(self.dados))


# ─── MODAL 3: CONFIRMACAO ─────────────────────────────────────────

class DungeonEventoModal3(discord.ui.Modal, title="Dungeon de Evento — Parte 3 de 3"):
    confirmar = discord.ui.TextInput(
        label="Revise e confirme (digite CRIAR para confirmar)",
        placeholder="CRIAR",
        max_length=5
    )

    def __init__(self, dados: dict):
        super().__init__()
        self.dados = dados
        # Show summary in description (via placeholder trick)
        d = dados
        tent_txt = f"{d['max_tentativas']}x" if d['max_tentativas'] else "Ilimitadas"
        fecha_txt = "Fecha ao completar" if d['modo_fechamento']=="primeiro" else f"{d['dias_aberta']} dias"
        self.confirmar.label = (
            f"Nome: {d['nome'][:20]} | Rank: {d['rank_minimo']} | "
            f"Fechamento: {fecha_txt} | Tent: {tent_txt}"
        )[:45]

    async def on_submit(self, interaction: discord.Interaction):
        if str(self.confirmar).strip().upper() != "CRIAR":
            await interaction.response.send_message("Cancelado! Digite CRIAR para confirmar.", ephemeral=True); return

        await interaction.response.defer(ephemeral=True)
        await init_db_dungeon_evento()

        pool = await get_pool()
        d = self.dados
        async with pool.acquire() as conn:
            dg = await conn.fetchrow("""
                INSERT INTO dungeons_evento
                (nome,descricao,imagem_url,canal_id,rank_minimo,modo_fechamento,
                 dias_aberta,max_tentativas,premio,status,criado_por)
                VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,'inativa',$10) RETURNING *
            """, d["nome"], d["descricao"], d["imagem_url"], d["canal_id"],
                d["rank_minimo"], d["modo_fechamento"], d["dias_aberta"],
                d["max_tentativas"], d["premio"], d["criado_por"])

        tent_txt  = f"{d['max_tentativas']}x por jogador" if d["max_tentativas"] else "Ilimitadas"
        fecha_txt = "Fecha ao primeiro completar" if d["modo_fechamento"]=="primeiro" else f"{d['dias_aberta']} dias"
        await interaction.followup.send(
            f"✅ Dungeon **{d['nome']}** criada! ID: `{dg['id']}`\n\n"
            f"**Rank minimo:** {d['rank_minimo']} | **Fechamento:** {fecha_txt} | **Tentativas:** {tent_txt}\n\n"
            f"Agora configure os andares com `/dungeon-evento-configurar {dg['id']}`\n"
            f"Quando pronto, ative com `/dungeon-evento-ativar {dg['id']}`",
            ephemeral=True
        )


# ─── CONFIGURAR ANDARES (VIEW INTERATIVA) ────────────────────────

class ConfigurarDungeonView(discord.ui.View):
    def __init__(self, dungeon_id: int, guild):
        super().__init__(timeout=300)
        self.dungeon_id = dungeon_id
        self.guild      = guild

    @discord.ui.button(label="➕ Adicionar Andar", style=discord.ButtonStyle.primary)
    async def add_andar(self, interaction: discord.Interaction, button):
        await interaction.response.send_modal(AndarModal1(self.dungeon_id))

    @discord.ui.button(label="📋 Ver Andares", style=discord.ButtonStyle.secondary)
    async def ver_andares(self, interaction: discord.Interaction, button):
        await interaction.response.defer(ephemeral=True)
        pool = await get_pool()
        async with pool.acquire() as conn:
            andares = await conn.fetch(
                "SELECT * FROM dungeon_evento_andares WHERE dungeon_id=$1 ORDER BY numero",
                self.dungeon_id)
            dg = await conn.fetchrow("SELECT nome FROM dungeons_evento WHERE id=$1", self.dungeon_id)
        if not andares:
            await interaction.followup.send("Nenhum andar configurado ainda!", ephemeral=True); return
        embed = discord.Embed(title=f"Andares — {dg['nome']}", color=0x7F77DD)
        for a in andares:
            loot_txt = f"\n🎁 {a['loot_item_emoji']} {a['loot_item_nome']}" if a["loot_item_nome"] else ""
            embed.add_field(
                name=f"Andar {a['numero']} {'💀 BOSS' if a['eh_boss'] else ''}",
                value=f"{a['emoji_monstro']} **{a['nome_monstro']}**\nHP:{a['hp']} ATK:{a['ataque']} DEF:{a['defesa']}{loot_txt}",
                inline=True
            )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="✅ Pronto!", style=discord.ButtonStyle.success)
    async def pronto(self, interaction: discord.Interaction, button):
        await interaction.response.defer(ephemeral=True)
        pool = await get_pool()
        async with pool.acquire() as conn:
            total = await conn.fetchval(
                "SELECT COUNT(*) FROM dungeon_evento_andares WHERE dungeon_id=$1", self.dungeon_id)
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)
        await interaction.followup.send(
            f"✅ {total} andar(es) configurados!\nUse `/dungeon-evento-ativar {self.dungeon_id}` quando quiser ativar.",
            ephemeral=True)
        self.stop()


# ─── MODAL ANDAR PARTE 1: MONSTRO ────────────────────────────────

class AndarModal1(discord.ui.Modal, title="Configurar Andar — Parte 1 de 2"):
    numero = discord.ui.TextInput(
        label="Numero do Andar",
        placeholder="Ex: 1 | 2 | 3 | 10...",
        max_length=3
    )
    nome_monstro = discord.ui.TextInput(
        label="Nome do Monstro",
        placeholder="Ex: Goblin Guardiao | Lich Anciao | Dragao de Gelo",
        max_length=60
    )
    emoji_monstro = discord.ui.TextInput(
        label="Emoji do Monstro",
        placeholder="Ex: 👹 | 💀 | 🐉 | 🧟 | 👺",
        max_length=8,
        default="👹"
    )
    hp_monstro = discord.ui.TextInput(
        label="HP do Monstro",
        placeholder="Ex: 500 | 1200 | 3000",
        max_length=6
    )
    ataque_monstro = discord.ui.TextInput(
        label="Ataque do Monstro",
        placeholder="Ex: 45 | 80 | 120",
        max_length=5
    )

    def __init__(self, dungeon_id: int):
        super().__init__()
        self.dungeon_id = dungeon_id

    async def on_submit(self, interaction: discord.Interaction):
        try: num = int(str(self.numero))
        except:
            await interaction.response.send_message("Numero invalido!", ephemeral=True); return
        try: hp = int(str(self.hp_monstro))
        except: hp = 100
        try: atk = int(str(self.ataque_monstro))
        except: atk = 20

        dados_andar = {
            "dungeon_id":    self.dungeon_id,
            "numero":        num,
            "nome_monstro":  str(self.nome_monstro),
            "emoji_monstro": str(self.emoji_monstro).strip(),
            "hp":            hp,
            "ataque":        atk,
        }
        await interaction.response.send_modal(AndarModal2(dados_andar))


# ─── MODAL ANDAR PARTE 2: DEFESA, LOOT E BOSS ────────────────────

class AndarModal2(discord.ui.Modal, title="Configurar Andar — Parte 2 de 2"):
    defesa_monstro = discord.ui.TextInput(
        label="Defesa do Monstro",
        placeholder="Ex: 5 | 15 | 30",
        max_length=4,
        default="5"
    )
    eh_boss = discord.ui.TextInput(
        label="E o boss final da dungeon?",
        placeholder="sim | nao",
        max_length=3,
        default="nao"
    )
    loot_nome = discord.ui.TextInput(
        label="Nome do Item de Loot (opcional)",
        placeholder="Ex: Fragmento de Obsidiana | Olho do Lich",
        required=False,
        max_length=60
    )
    loot_config = discord.ui.TextInput(
        label="Config do Loot (id|tipo|raridade|emoji)",
        placeholder="Ex: fragmento_obs|material|Raro|🪨  (deixe vazio se nao tiver loot)",
        required=False,
        max_length=100
    )

    def __init__(self, dados_andar: dict):
        super().__init__()
        self.dados_andar = dados_andar

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        try: dfs = int(str(self.defesa_monstro))
        except: dfs = 5
        boss = str(self.eh_boss).strip().lower() in ("sim","s","yes","1")

        l_id = l_nome = l_tipo = l_rar = l_emoji = ""
        if self.loot_nome and str(self.loot_nome):
            l_nome = str(self.loot_nome).strip()
        if self.loot_config and str(self.loot_config):
            partes = str(self.loot_config).split("|")
            l_id    = partes[0].strip() if len(partes) > 0 else ""
            l_tipo  = partes[1].strip() if len(partes) > 1 else "material"
            l_rar   = partes[2].strip() if len(partes) > 2 else "Raro"
            l_emoji = partes[3].strip() if len(partes) > 3 else "📦"

        d = self.dados_andar
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO dungeon_evento_andares
                (dungeon_id,numero,nome_monstro,emoji_monstro,hp,ataque,defesa,
                 loot_item_id,loot_item_nome,loot_item_tipo,loot_item_raridade,
                 loot_item_emoji,eh_boss)
                VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)
                ON CONFLICT(dungeon_id,numero)
                DO UPDATE SET
                    nome_monstro=EXCLUDED.nome_monstro, emoji_monstro=EXCLUDED.emoji_monstro,
                    hp=EXCLUDED.hp, ataque=EXCLUDED.ataque, defesa=EXCLUDED.defesa,
                    loot_item_id=EXCLUDED.loot_item_id, loot_item_nome=EXCLUDED.loot_item_nome,
                    loot_item_tipo=EXCLUDED.loot_item_tipo, loot_item_raridade=EXCLUDED.loot_item_raridade,
                    loot_item_emoji=EXCLUDED.loot_item_emoji, eh_boss=EXCLUDED.eh_boss
            """, d["dungeon_id"], d["numero"], d["nome_monstro"], d["emoji_monstro"],
                d["hp"], d["ataque"], dfs, l_id, l_nome, l_tipo, l_rar, l_emoji, boss)
            total = await conn.fetchval(
                "SELECT COUNT(*) FROM dungeon_evento_andares WHERE dungeon_id=$1", d["dungeon_id"])

        boss_txt = " 💀 **BOSS FINAL**" if boss else ""
        loot_txt = f"\n🎁 Loot: {l_emoji} {l_nome}" if l_nome else ""
        await interaction.followup.send(
            f"✅ Andar {d['numero']} salvo!{boss_txt}\n"
            f"{d['emoji_monstro']} **{d['nome_monstro']}** | HP:{d['hp']} ATK:{d['ataque']} DEF:{dfs}"
            f"{loot_txt}\n\n📋 Total de andares: **{total}**",
            ephemeral=True
        )


# ─── ATIVAR DUNGEON ───────────────────────────────────────────────

async def cmd_dungeon_evento_ativar(interaction: discord.Interaction, dungeon_id: int):
    await interaction.response.defer(ephemeral=True)
    pool = await get_pool()
    async with pool.acquire() as conn:
        dg = await conn.fetchrow("SELECT * FROM dungeons_evento WHERE id=$1", dungeon_id)
        if not dg:
            await interaction.followup.send("Dungeon nao encontrada!", ephemeral=True); return
        andares = await conn.fetch(
            "SELECT * FROM dungeon_evento_andares WHERE dungeon_id=$1 ORDER BY numero", dungeon_id)
        if not andares:
            await interaction.followup.send("Configure os andares primeiro com `/dungeon-evento-configurar`!", ephemeral=True); return
        await conn.execute("UPDATE dungeons_evento SET status='ativa' WHERE id=$1", dungeon_id)

    total = len(andares)
    tent_txt  = f"{dg['max_tentativas']}x por jogador" if dg["max_tentativas"] else "Ilimitadas"
    fecha_txt = "Fecha ao primeiro completar" if dg["modo_fechamento"]=="primeiro" else f"Aberta por {dg['dias_aberta']} dias"
    embed = discord.Embed(title=f"🏰 {dg['nome']}", description=dg["descricao"], color=0x7F77DD)
    embed.add_field(name="Andares",     value=str(total),          inline=True)
    embed.add_field(name="Rank Min",    value=dg["rank_minimo"],   inline=True)
    embed.add_field(name="Tentativas",  value=tent_txt,            inline=True)
    embed.add_field(name="Duracao",     value=fecha_txt,           inline=True)
    embed.add_field(name="🏆 Premio",   value=dg["premio"],        inline=False)
    embed.set_footer(text=f"Dungeon Evento #{dungeon_id} | Clique para entrar!")
    if dg["imagem_url"]: embed.set_image(url=dg["imagem_url"])

    class EntrarView(discord.ui.View):
        def __init__(self): super().__init__(timeout=None)
        @discord.ui.button(label="⚔️ Entrar na Dungeon!", style=discord.ButtonStyle.danger,
                           custom_id=f"dg_evento_{dungeon_id}")
        async def btn(self, inter, b): await _rodar_dungeon_evento(inter, dungeon_id)

    canal = interaction.guild.get_channel(dg["canal_id"]) or interaction.channel
    msg   = await canal.send(embed=embed, view=EntrarView())
    async with pool.acquire() as conn:
        await conn.execute("UPDATE dungeons_evento SET msg_id=$1, canal_id=$2 WHERE id=$3",
            msg.id, canal.id, dungeon_id)
    await interaction.followup.send(f"✅ Dungeon **{dg['nome']}** ativada em {canal.mention}!", ephemeral=True)

    if dg["modo_fechamento"] == "tempo":
        asyncio.create_task(_agendar_fechar(dungeon_id, dg["dias_aberta"]*86400, interaction.guild))

async def _agendar_fechar(dungeon_id, seg, guild):
    await asyncio.sleep(seg)
    await _fechar(dungeon_id, guild, "Tempo esgotado!")

async def _fechar(dungeon_id, guild, motivo=""):
    pool = await get_pool()
    async with pool.acquire() as conn:
        dg = await conn.fetchrow("SELECT * FROM dungeons_evento WHERE id=$1 AND status='ativa'", dungeon_id)
        if not dg: return
        await conn.execute("UPDATE dungeons_evento SET status='fechada', fechada_em=NOW() WHERE id=$1", dungeon_id)
    canal = guild.get_channel(dg["canal_id"])
    if canal: await canal.send(f"🔒 **{dg['nome']}** foi fechada. {motivo}")


# ─── RODAR DUNGEON DE EVENTO ──────────────────────────────────────

async def _rodar_dungeon_evento(interaction: discord.Interaction, dungeon_id: int):
    await interaction.response.defer(ephemeral=True)
    pool = await get_pool()
    async with pool.acquire() as conn:
        dg = await conn.fetchrow("SELECT * FROM dungeons_evento WHERE id=$1 AND status='ativa'", dungeon_id)
        if not dg:
            await interaction.followup.send("Esta dungeon nao esta mais ativa!", ephemeral=True); return
        p = await conn.fetchrow("SELECT * FROM personagens WHERE user_id=$1", interaction.user.id)
        if not p:
            await interaction.followup.send("Crie seu personagem primeiro!", ephemeral=True); return
        from catalogo import get_rank
        ranks_order = ["F","E","D","C","B","A","S","SS"]
        rank_p = get_rank(p["nivel"])["rank"]
        if ranks_order.index(rank_p) < ranks_order.index(dg["rank_minimo"]):
            await interaction.followup.send(f"Rank insuficiente! Precisa de Rank **{dg['rank_minimo']}**.", ephemeral=True); return
        if dg["max_tentativas"] > 0:
            tent_count = await conn.fetchval(
                "SELECT COUNT(*) FROM dungeon_evento_runs WHERE dungeon_id=$1 AND user_id=$2",
                dungeon_id, interaction.user.id)
            if tent_count >= dg["max_tentativas"]:
                await interaction.followup.send(f"Limite de {dg['max_tentativas']} tentativa(s) atingido!", ephemeral=True); return
        from batalha import BATALHAS_ATIVAS
        if interaction.user.id in BATALHAS_ATIVAS:
            await interaction.followup.send("Voce ja esta em batalha!", ephemeral=True); return
        tent_num = await conn.fetchval(
            "SELECT COALESCE(MAX(tentativa),0)+1 FROM dungeon_evento_runs WHERE dungeon_id=$1 AND user_id=$2",
            dungeon_id, interaction.user.id)
        run = await conn.fetchrow(
            "INSERT INTO dungeon_evento_runs(dungeon_id,user_id,tentativa) VALUES($1,$2,$3) RETURNING *",
            dungeon_id, interaction.user.id, tent_num)
        andares = await conn.fetch(
            "SELECT * FROM dungeon_evento_andares WHERE dungeon_id=$1 ORDER BY numero", dungeon_id)

    if not andares:
        await interaction.followup.send("Dungeon sem andares configurados!", ephemeral=True); return

    from batalha import BATALHAS_ATIVAS, calc_dano, BatalhaView, get_pocoes_inv, get_skills_eq
    from catalogo import SKILLS_COMPLETAS
    BATALHAS_ATIVAS.add(interaction.user.id)

    hp_j = p["hp_atual"]; hp_jmx = p["hp_max"]
    mana_j = p["mana_atual"]; mana_jmx = p["mana_max"]
    timeout_count = 0
    ids_eq = await get_skills_eq(interaction.user.id)
    skills = [s for sid in ids_eq for s in SKILLS_COMPLETAS.get(p["classe_id"],[]) if s["id"]==sid]
    if not skills: skills = SKILLS_COMPLETAS.get(p["classe_id"],[])[:4]

    await interaction.followup.send(
        embed=discord.Embed(title=f"🏰 Entrando em {dg['nome']}",
            description=f"{len(andares)} andares te aguardam...", color=0x7F77DD))

    for andar in andares:
        hp_m = andar["hp"]; hp_mmx = andar["hp"]
        turno = 1
        boss_txt = " 💀 **BOSS FINAL**" if andar["eh_boss"] else ""
        embed_a = discord.Embed(
            title=f"🏰 Andar {andar['numero']}{boss_txt}",
            description=f"{andar['emoji_monstro']} **{andar['nome_monstro']}** aparece!\n❤️ {hp_j}/{hp_jmx} | 💙 {mana_j}/{mana_jmx}",
            color=0xE24B4A if andar["eh_boss"] else 0x7F77DD)
        await interaction.followup.send(embed=embed_a)

        while hp_j > 0 and hp_m > 0:
            pocoes = await get_pocoes_inv(interaction.user.id)
            view   = BatalhaView(interaction.user.id, skills, pocoes, nivel=p["nivel"])
            cor_hp = 0x1D9E75 if hp_j > hp_jmx*0.5 else (0xE4AF3C if hp_j > hp_jmx*0.25 else 0xE24B4A)
            embed_t = discord.Embed(
                title=f"Turno {turno} — {andar['emoji_monstro']} {andar['nome_monstro']}",
                description=f"Voce: ❤️ {hp_j}/{hp_jmx} 💙 {mana_j}/{mana_jmx}\nInimigo: ❤️ {hp_m}/{hp_mmx}",
                color=cor_hp)
            msg_t = await interaction.followup.send(embed=embed_t, view=view, wait=True)
            await view.wait()
            try: await msg_t.edit(view=None)
            except: pass
            acao, val = view.acao or ("timeout", None)

            if acao == "timeout":
                timeout_count += 1
                if timeout_count >= 3:
                    await interaction.followup.send(embed=discord.Embed(
                        title="💤 Expulso por inatividade!", color=0x888780))
                    BATALHAS_ATIVAS.discard(interaction.user.id)
                    async with pool.acquire() as conn:
                        await conn.execute("UPDATE dungeon_evento_runs SET falhou=TRUE WHERE id=$1", run["id"])
                    return
                await interaction.followup.send(embed=discord.Embed(
                    title=f"⏰ Turno perdido! ({timeout_count}/3)",
                    description=f"Mais {3-timeout_count} vez(es) = expulso!", color=0xE4AF3C))
                continue
            else:
                timeout_count = 0

            if acao == "fugir":
                await interaction.followup.send(embed=discord.Embed(
                    title="🏃 Voce fugiu!", description="Nenhuma recompensa.", color=0x888780))
                BATALHAS_ATIVAS.discard(interaction.user.id)
                async with pool.acquire() as conn:
                    await conn.execute("UPDATE dungeon_evento_runs SET falhou=TRUE WHERE id=$1", run["id"])
                return

            linha = ""
            if acao == "atk_basico":
                mult = 1.0 + (p["nivel"]//10)*0.1
                dano = calc_dano(p["ataque"], andar["defesa"], mult)
                hp_m = max(0, hp_m - dano)
                linha = f"⚔️ Ataque: **{dano} de dano**!"
            elif acao == "skill" and val is not None:
                sk = skills[val] if val < len(skills) else skills[0]
                if mana_j >= sk.get("mana",0):
                    mana_j -= sk.get("mana",0)
                    dano = calc_dano(p["ataque"], andar["defesa"], sk.get("dano",1.0))
                    hp_m = max(0, hp_m - dano)
                    linha = f"{sk['emoji']} **{sk['nome']}**: **{dano} de dano**!"
                else:
                    dano = calc_dano(p["ataque"], andar["defesa"])
                    hp_m = max(0, hp_m - dano)
                    linha = f"Sem mana! Auto: **{dano} de dano**."
            elif acao == "defesa":
                if random.random() < 0.6:
                    dm = int(calc_dano(andar["ataque"], p["defesa"]) * 0.2)
                    hp_j = max(0, hp_j - dm)
                    linha = f"🛡️ Bloqueou! Tomou apenas **{dm}**."
                else:
                    dm = calc_dano(andar["ataque"], p["defesa"])
                    hp_j = max(0, hp_j - dm)
                    linha = f"🛡️ Falhou! Tomou **{dm}**."
                await interaction.followup.send(embed=discord.Embed(
                    description=f"{linha}\n❤️ {hp_j}/{hp_jmx}", color=0x378ADD))
                turno += 1; continue
            elif acao == "pocao" and val:
                from batalha import aplicar_efeito_pocao, remover_pocao
                hp_j, mana_j, linha = aplicar_efeito_pocao(val, hp_j, hp_jmx, mana_j, mana_jmx)
                await remover_pocao(interaction.user.id, val)
                await interaction.followup.send(embed=discord.Embed(description=linha, color=0x1D9E75))
                turno += 1; continue
            else:
                dano = calc_dano(p["ataque"], andar["defesa"])
                hp_m = max(0, hp_m - dano)
                linha = f"⚔️ Auto: **{dano} de dano**!"

            if hp_m <= 0:
                await interaction.followup.send(embed=discord.Embed(
                    description=f"{linha}\n{andar['emoji_monstro']} **{andar['nome_monstro']}** derrotado! ✅",
                    color=0x1D9E75)); break

            dm = calc_dano(andar["ataque"], p["defesa"])
            hp_j = max(0, hp_j - dm)
            mana_j = min(mana_jmx, mana_j + 5)
            cor = 0x1D9E75 if hp_j > hp_jmx*0.5 else (0xE4AF3C if hp_j > hp_jmx*0.25 else 0xE24B4A)
            await interaction.followup.send(embed=discord.Embed(
                description=f"{linha}\n{andar['emoji_monstro']} contra: **{dm} de dano**!\n❤️ {hp_j}/{hp_jmx} 💙 {mana_j}/{mana_jmx}",
                color=cor))
            turno += 1

        if hp_j <= 0:
            await interaction.followup.send(embed=discord.Embed(
                title="💀 Voce foi derrotado!",
                description=f"Caiu no andar **{andar['numero']}** de {len(andares)}.",
                color=0xE24B4A))
            BATALHAS_ATIVAS.discard(interaction.user.id)
            async with pool.acquire() as conn:
                await conn.execute("UPDATE dungeon_evento_runs SET falhou=TRUE WHERE id=$1", run["id"])
            return

        # Loot do andar
        if andar["loot_item_id"] and andar["loot_item_nome"]:
            async with pool.acquire() as conn:
                ex = await conn.fetchrow("SELECT id FROM inventario WHERE user_id=$1 AND item_id=$2",
                    interaction.user.id, andar["loot_item_id"])
                if ex: await conn.execute("UPDATE inventario SET quantidade=quantidade+1 WHERE id=$1", ex["id"])
                else: await conn.execute(
                    "INSERT INTO inventario(user_id,item_id,nome,tipo,raridade,emoji,descricao) VALUES($1,$2,$3,$4,$5,$6,$7)",
                    interaction.user.id, andar["loot_item_id"], andar["loot_item_nome"],
                    andar["loot_item_tipo"], andar["loot_item_raridade"], andar["loot_item_emoji"],
                    f"Loot — {dg['nome']}")
            await interaction.followup.send(embed=discord.Embed(
                description=f"🎁 Loot: {andar['loot_item_emoji']} **{andar['loot_item_nome']}** adicionado ao inventario!",
                color=0x1D9E75))

        await asyncio.sleep(0.5)

    # Completou!
    BATALHAS_ATIVAS.discard(interaction.user.id)
    async with pool.acquire() as conn:
        await conn.execute("UPDATE dungeon_evento_runs SET concluida=TRUE WHERE id=$1", run["id"])

    await interaction.followup.send(embed=discord.Embed(
        title=f"🏆 {dg['nome']} — COMPLETADA!",
        description=f"Voce completou todos os **{len(andares)} andares**!\n\n🏆 **Premio:** {dg['premio']}",
        color=0xE4AF3C))

    # Entrega premio
    await _dar_premio_dg(interaction.guild, interaction.user.id, dg["premio"])

    if dg["modo_fechamento"] == "primeiro":
        await _fechar(dungeon_id, interaction.guild,
            f"Primeiro a completar: **{interaction.user.display_name}**!")

async def _dar_premio_dg(guild, user_id, premio_str):
    if not premio_str: return
    pool = await get_pool()
    try:
        async with pool.acquire() as conn:
            s = premio_str.lower()
            if "moedas" in s or s.strip().isdigit():
                qtd = int(''.join(filter(str.isdigit, s)) or "0")
                if qtd: await conn.execute("UPDATE personagens SET moedas=moedas+$1 WHERE user_id=$2", qtd, user_id)
            elif "xp" in s:
                qtd = int(''.join(filter(str.isdigit, s)) or "0")
                if qtd: await conn.execute("UPDATE personagens SET xp=xp+$1 WHERE user_id=$2", qtd, user_id)
            elif "ficha" in s:
                qtd = int(''.join(filter(str.isdigit, s)) or "1")
                await conn.execute("""
                    INSERT INTO giros(user_id,roleta_id,raridade,quantidade) VALUES($1,'skill','Lendario',$2)
                    ON CONFLICT(user_id,roleta_id,raridade) DO UPDATE SET quantidade=giros.quantidade+$2
                """, user_id, qtd)
            elif "cargo" in s:
                nome_cargo = premio_str.split(":")[-1].strip()
                member = guild.get_member(user_id)
                if member:
                    cargo = discord.utils.get(guild.roles, name=nome_cargo)
                    if cargo: await member.add_roles(cargo)
    except Exception as e:
        print(f"Erro ao dar premio dungeon evento: {e}")

# ─── COMANDOS EXPORTADOS ──────────────────────────────────────────

async def cmd_dungeon_evento_criar(interaction: discord.Interaction):
    await interaction.response.send_modal(DungeonEventoModal1())

async def cmd_dungeon_evento_configurar(interaction: discord.Interaction, dungeon_id: int):
    await interaction.response.defer(ephemeral=True)
    pool = await get_pool()
    async with pool.acquire() as conn:
        dg = await conn.fetchrow("SELECT * FROM dungeons_evento WHERE id=$1", dungeon_id)
        if not dg:
            await interaction.followup.send("Dungeon nao encontrada!", ephemeral=True); return
        total = await conn.fetchval(
            "SELECT COUNT(*) FROM dungeon_evento_andares WHERE dungeon_id=$1", dungeon_id)
    embed = discord.Embed(
        title=f"⚙️ Configurar — {dg['nome']}",
        description=f"**{total}** andar(es) configurado(s) ate agora.\n\nUse os botoes abaixo para adicionar andares:",
        color=0x7F77DD)
    embed.set_footer(text=f"Dungeon #{dungeon_id} | Rank: {dg['rank_minimo']} | Premio: {dg['premio']}")
    view = ConfigurarDungeonView(dungeon_id, interaction.guild)
    await interaction.followup.send(embed=embed, view=view, ephemeral=True)

async def cmd_dungeon_evento_info(interaction: discord.Interaction, dungeon_id: int):
    await interaction.response.defer(ephemeral=True)
    pool = await get_pool()
    async with pool.acquire() as conn:
        dg = await conn.fetchrow("SELECT * FROM dungeons_evento WHERE id=$1", dungeon_id)
        if not dg:
            await interaction.followup.send("Dungeon nao encontrada!", ephemeral=True); return
        andares    = await conn.fetch("SELECT * FROM dungeon_evento_andares WHERE dungeon_id=$1 ORDER BY numero", dungeon_id)
        concluidas = await conn.fetchval("SELECT COUNT(*) FROM dungeon_evento_runs WHERE dungeon_id=$1 AND concluida=TRUE", dungeon_id)
        tentativas = await conn.fetchval("SELECT COUNT(*) FROM dungeon_evento_runs WHERE dungeon_id=$1", dungeon_id)
    embed = discord.Embed(title=f"🏰 {dg['nome']}", description=dg["descricao"], color=0x7F77DD)
    embed.add_field(name="Status",     value=dg["status"].title(), inline=True)
    embed.add_field(name="Andares",    value=str(len(andares)),    inline=True)
    embed.add_field(name="Rank Min",   value=dg["rank_minimo"],    inline=True)
    embed.add_field(name="Concluidas", value=str(concluidas),      inline=True)
    embed.add_field(name="Tentativas", value=str(tentativas),      inline=True)
    embed.add_field(name="🏆 Premio",  value=dg["premio"],         inline=False)
    if andares:
        lista = "\n".join([
            f"**{a['numero']}.** {a['emoji_monstro']} {a['nome_monstro']} — HP:{a['hp']} ATK:{a['ataque']} DEF:{a['defesa']}{' 💀 BOSS' if a['eh_boss'] else ''}"
            for a in andares])
        embed.add_field(name="Andares", value=lista[:1000], inline=False)
    if dg["imagem_url"]: embed.set_image(url=dg["imagem_url"])
    await interaction.followup.send(embed=embed, ephemeral=True)

async def cmd_dungeon_evento_fechar(interaction: discord.Interaction, dungeon_id: int):
    await interaction.response.defer(ephemeral=True)
    await _fechar(dungeon_id, interaction.guild, "Encerrada pelo admin.")
    await interaction.followup.send(f"✅ Dungeon #{dungeon_id} fechada!", ephemeral=True)
