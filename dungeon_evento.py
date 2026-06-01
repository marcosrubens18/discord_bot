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
                canal_id BIGINT,
                msg_id BIGINT DEFAULT 0,
                rank_minimo TEXT DEFAULT 'F',
                modo_fechamento TEXT DEFAULT 'tempo',
                dias_aberta INTEGER DEFAULT 7,
                max_tentativas INTEGER DEFAULT 0,
                premio TEXT DEFAULT '',
                status TEXT DEFAULT 'inativa',
                criado_por BIGINT,
                criado_em TIMESTAMP DEFAULT NOW(),
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
                eh_boss BOOLEAN DEFAULT FALSE
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS dungeon_evento_runs (
                id SERIAL PRIMARY KEY,
                dungeon_id INTEGER REFERENCES dungeons_evento(id),
                user_id BIGINT,
                tentativa INTEGER DEFAULT 1,
                andar_atual INTEGER DEFAULT 1,
                concluida BOOLEAN DEFAULT FALSE,
                falhou BOOLEAN DEFAULT FALSE,
                iniciada_em TIMESTAMP DEFAULT NOW(),
                concluida_em TIMESTAMP,
                UNIQUE(dungeon_id, user_id, tentativa)
            )
        """)
    print("DB dungeon_evento OK!")

# ─── MODAIS ───────────────────────────────────────────────────────

class DungeonEventoCriarModal(discord.ui.Modal, title="Criar Dungeon de Evento"):
    nome = discord.ui.TextInput(label="Nome da Dungeon", max_length=80,
        placeholder="Ex: Cripta do Lich Anciao")
    descricao = discord.ui.TextInput(label="Descricao", style=discord.TextStyle.paragraph,
        max_length=400, placeholder="Historia e contexto da dungeon...")
    config = discord.ui.TextInput(
        label="Config: RankMin | Fechamento | Tentativas",
        placeholder="Ex: B|tempo:3dias|2  ou  F|primeiro|ilimitado",
        max_length=60
    )
    premio = discord.ui.TextInput(label="Premio para quem completar",
        placeholder="Ex: 15000 moedas | cargo:Conquistador | ficha:3",
        max_length=200)
    imagem_canal = discord.ui.TextInput(
        label="Imagem URL | ID do Canal",
        placeholder="https://i.imgur.com/xxx.png|123456789",
        required=False, max_length=250
    )

    def __init__(self, guild):
        super().__init__()
        self.guild = guild

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await init_db_dungeon_evento()

        # Parse config: RankMin|fechamento|tentativas
        rank_min = "F"
        modo = "tempo"
        dias = 7
        max_tent = 0
        try:
            partes = [p.strip() for p in str(self.config).split("|")]
            if partes[0]: rank_min = partes[0].upper()
            if len(partes) > 1:
                fc = partes[1].lower()
                if "primeiro" in fc or "first" in fc:
                    modo = "primeiro"
                else:
                    modo = "tempo"
                    nums = ''.join(filter(str.isdigit, fc))
                    dias = int(nums) if nums else 7
            if len(partes) > 2:
                t = partes[2].lower()
                max_tent = 0 if "ilimit" in t else int(''.join(filter(str.isdigit, t)) or "0")
        except:
            pass

        # Parse imagem|canal
        img_url = ""
        canal_id = None
        if self.imagem_canal and str(self.imagem_canal):
            partes_ic = str(self.imagem_canal).split("|")
            img_url = partes_ic[0].strip()
            if len(partes_ic) > 1:
                try: canal_id = int(partes_ic[1].strip())
                except: pass

        pool = await get_pool()
        async with pool.acquire() as conn:
            dg = await conn.fetchrow("""
                INSERT INTO dungeons_evento(nome,descricao,imagem_url,canal_id,rank_minimo,
                    modo_fechamento,dias_aberta,max_tentativas,premio,status,criado_por)
                VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,'inativa',$10) RETURNING *
            """, str(self.nome), str(self.descricao), img_url, canal_id,
                rank_min, modo, dias, max_tent, str(self.premio), interaction.user.id)

        tent_txt = f"{max_tent} por jogador" if max_tent else "Ilimitadas"
        fecha_txt = "Quando alguem completar" if modo == "primeiro" else f"{dias} dias apos ativar"
        await interaction.followup.send(
            f"✅ Dungeon **{str(self.nome)}** criada! ID: `{dg['id']}`\n\n"
            f"📋 Rank minimo: **{rank_min}** | Fechamento: **{fecha_txt}** | Tentativas: **{tent_txt}**\n\n"
            f"Agora adicione os andares com `/dungeon-evento-andar {dg['id']}`\n"
            f"Quando estiver pronto, ative com `/dungeon-evento-ativar {dg['id']}`",
            ephemeral=True
        )

class AdicionarAndarModal(discord.ui.Modal, title="Adicionar Andar"):
    numero_monstro = discord.ui.TextInput(
        label="Numero do Andar | Nome do Monstro",
        placeholder="Ex: 1|Goblin Guardiao  ou  5|Lich Anciao (boss final)",
        max_length=80
    )
    emoji_stats = discord.ui.TextInput(
        label="Emoji | HP | ATK | DEF",
        placeholder="Ex: 👹|500|45|20",
        max_length=40
    )
    loot_andar = discord.ui.TextInput(
        label="Loot do Andar (descricao)",
        placeholder="Ex: Fragmento de Obsidiana x2",
        required=False, max_length=100
    )
    loot_item = discord.ui.TextInput(
        label="Item para inventario (id|nome|tipo|raridade|emoji)",
        placeholder="Ex: fragmento_obs|Fragmento de Obs|material|Raro|🪨",
        required=False, max_length=150
    )
    eh_boss = discord.ui.TextInput(
        label="E o boss final? (sim/nao)",
        placeholder="sim ou nao",
        max_length=5,
        default="nao"
    )

    def __init__(self, dungeon_id: int):
        super().__init__()
        self.dungeon_id = dungeon_id

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        # Parse numero|monstro
        try:
            partes_nm = str(self.numero_monstro).split("|")
            numero = int(partes_nm[0].strip())
            nome_m = partes_nm[1].strip() if len(partes_nm) > 1 else "Monstro"
        except:
            await interaction.followup.send("Formato invalido! Use: numero|Nome", ephemeral=True); return

        # Parse emoji|hp|atk|def
        try:
            partes_s = str(self.emoji_stats).split("|")
            emoji = partes_s[0].strip() if partes_s[0].strip() else "👹"
            hp  = int(partes_s[1].strip()) if len(partes_s) > 1 else 100
            atk = int(partes_s[2].strip()) if len(partes_s) > 2 else 20
            dfs = int(partes_s[3].strip()) if len(partes_s) > 3 else 5
        except:
            hp, atk, dfs, emoji = 100, 20, 5, "👹"

        # Parse loot item
        l_id = l_nome = l_emoji = ""
        l_tipo = "material"; l_rar = "Raro"
        if self.loot_item and str(self.loot_item):
            partes_l = str(self.loot_item).split("|")
            l_id    = partes_l[0].strip() if len(partes_l) > 0 else ""
            l_nome  = partes_l[1].strip() if len(partes_l) > 1 else ""
            l_tipo  = partes_l[2].strip() if len(partes_l) > 2 else "material"
            l_rar   = partes_l[3].strip() if len(partes_l) > 3 else "Raro"
            l_emoji = partes_l[4].strip() if len(partes_l) > 4 else "📦"

        boss = str(self.eh_boss).strip().lower() in ("sim","s","yes","true","1")

        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO dungeon_evento_andares
                (dungeon_id,numero,nome_monstro,emoji_monstro,hp,ataque,defesa,
                 loot_desc,loot_item_id,loot_item_nome,loot_item_emoji,
                 loot_item_tipo,loot_item_raridade,eh_boss)
                VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14)
                ON CONFLICT DO NOTHING
            """, self.dungeon_id, numero, nome_m, emoji, hp, atk, dfs,
                str(self.loot_andar or ""), l_id, l_nome, l_emoji, l_tipo, l_rar, boss)
            total = await conn.fetchval("SELECT COUNT(*) FROM dungeon_evento_andares WHERE dungeon_id=$1", self.dungeon_id)
        await interaction.followup.send(
            f"✅ Andar {numero} adicionado: **{emoji} {nome_m}** | HP:{hp} ATK:{atk} DEF:{dfs}"
            + (" 💀 BOSS" if boss else "") +
            f"\nTotal de andares: {total}",
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
        andares = await conn.fetch("SELECT * FROM dungeon_evento_andares WHERE dungeon_id=$1 ORDER BY numero", dungeon_id)
        if not andares:
            await interaction.followup.send("Adicione pelo menos 1 andar antes de ativar!", ephemeral=True); return
        await conn.execute("UPDATE dungeons_evento SET status='ativa' WHERE id=$1", dungeon_id)

    total_andares = len(andares)
    tent_txt = f"{dg['max_tentativas']}x por jogador" if dg["max_tentativas"] else "Ilimitadas"
    fecha_txt = "Fecha quando alguem completar" if dg["modo_fechamento"] == "primeiro" else f"Aberta por {dg['dias_aberta']} dias"

    embed = discord.Embed(
        title=f"🏰 {dg['nome']}",
        description=dg["descricao"],
        color=0x7F77DD
    )
    embed.add_field(name="Andares",      value=str(total_andares), inline=True)
    embed.add_field(name="Rank Minimo",  value=dg["rank_minimo"],  inline=True)
    embed.add_field(name="Tentativas",   value=tent_txt,            inline=True)
    embed.add_field(name="Duracao",      value=fecha_txt,           inline=True)
    embed.add_field(name="🏆 Premio",    value=dg["premio"],        inline=False)
    embed.set_footer(text=f"Dungeon #{dungeon_id} | Clique para entrar!")
    if dg["imagem_url"]: embed.set_image(url=dg["imagem_url"])

    class EntrarView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)
        @discord.ui.button(label="⚔️ Entrar na Dungeon!", style=discord.ButtonStyle.danger,
                           custom_id=f"dg_evento_{dungeon_id}")
        async def btn(self, inter: discord.Interaction, b):
            await cmd_dungeon_evento_entrar(inter, dungeon_id)

    canal_id = dg["canal_id"]
    canal = interaction.guild.get_channel(canal_id) if canal_id else interaction.channel
    msg = await canal.send(embed=embed, view=EntrarView())
    async with pool.acquire() as conn:
        await conn.execute("UPDATE dungeons_evento SET msg_id=$1, canal_id=$2 WHERE id=$3",
            msg.id, canal.id, dungeon_id)

    await interaction.followup.send(f"✅ Dungeon **{dg['nome']}** ativada!", ephemeral=True)

    if dg["modo_fechamento"] == "tempo" and dg["dias_aberta"] > 0:
        asyncio.create_task(_agendar_fechamento_dg(dungeon_id, dg["dias_aberta"]*86400, interaction.guild))

async def _agendar_fechamento_dg(dungeon_id, segundos, guild):
    await asyncio.sleep(segundos)
    await _fechar_dungeon_evento(dungeon_id, guild, "Tempo esgotado")

async def _fechar_dungeon_evento(dungeon_id, guild, motivo=""):
    pool = await get_pool()
    async with pool.acquire() as conn:
        dg = await conn.fetchrow("SELECT * FROM dungeons_evento WHERE id=$1 AND status='ativa'", dungeon_id)
        if not dg: return
        await conn.execute("UPDATE dungeons_evento SET status='fechada', fechada_em=NOW() WHERE id=$1", dungeon_id)
    canal = guild.get_channel(dg["canal_id"])
    if canal:
        await canal.send(f"🔒 A dungeon **{dg['nome']}** foi fechada. {motivo}")

# ─── RODAR DUNGEON DE EVENTO ──────────────────────────────────────

async def cmd_dungeon_evento_entrar(interaction: discord.Interaction, dungeon_id: int):
    await interaction.response.defer(ephemeral=True)
    pool = await get_pool()
    async with pool.acquire() as conn:
        dg = await conn.fetchrow("SELECT * FROM dungeons_evento WHERE id=$1 AND status='ativa'", dungeon_id)
        if not dg:
            await interaction.followup.send("Esta dungeon nao esta mais ativa!", ephemeral=True); return
        p = await conn.fetchrow("SELECT * FROM personagens WHERE user_id=$1", interaction.user.id)
        if not p:
            await interaction.followup.send("Crie seu personagem primeiro!", ephemeral=True); return
        # Verifica rank minimo
        from catalogo import get_rank
        rank_p = get_rank(p["nivel"])["rank"]
        ranks_order = ["F","E","D","C","B","A","S","SS"]
        if ranks_order.index(rank_p) < ranks_order.index(dg["rank_minimo"]):
            await interaction.followup.send(
                f"Rank insuficiente! Precisa ser pelo menos Rank **{dg['rank_minimo']}**.", ephemeral=True); return
        # Verifica tentativas
        if dg["max_tentativas"] > 0:
            tent_count = await conn.fetchval(
                "SELECT COUNT(*) FROM dungeon_evento_runs WHERE dungeon_id=$1 AND user_id=$2",
                dungeon_id, interaction.user.id)
            if tent_count >= dg["max_tentativas"]:
                await interaction.followup.send(
                    f"Limite de tentativas atingido ({dg['max_tentativas']}x)!", ephemeral=True); return
        # Verifica se ja esta em batalha
        from batalha import BATALHAS_ATIVAS
        if interaction.user.id in BATALHAS_ATIVAS:
            await interaction.followup.send("Voce ja esta em batalha!", ephemeral=True); return
        # Cria run
        tent_num = await conn.fetchval(
            "SELECT COALESCE(MAX(tentativa),0)+1 FROM dungeon_evento_runs WHERE dungeon_id=$1 AND user_id=$2",
            dungeon_id, interaction.user.id)
        run = await conn.fetchrow(
            "INSERT INTO dungeon_evento_runs(dungeon_id,user_id,tentativa) VALUES($1,$2,$3) RETURNING *",
            dungeon_id, interaction.user.id, tent_num)
        andares = await conn.fetch(
            "SELECT * FROM dungeon_evento_andares WHERE dungeon_id=$1 ORDER BY numero", dungeon_id)

    if not andares:
        await interaction.followup.send("Esta dungeon nao tem andares configurados!", ephemeral=True); return

    await interaction.followup.send(
        f"🏰 Iniciando **{dg['nome']}**! {len(andares)} andares te aguardam...", ephemeral=True)

    from batalha import BATALHAS_ATIVAS, calc_dano, BatalhaView, get_pocoes_inv, get_skills_eq, SKILLS_COMPLETAS
    BATALHAS_ATIVAS.add(interaction.user.id)

    hp_j = p["hp_atual"]
    hp_jmx = p["hp_max"]
    mana_j = p["mana_atual"]
    mana_jmx = p["mana_max"]
    timeout_count = 0

    ids_eq = await get_skills_eq(interaction.user.id)
    skills = [s for sid in ids_eq for s in SKILLS_COMPLETAS.get(p["classe_id"],[]) if s["id"]==sid]
    if not skills:
        skills = SKILLS_COMPLETAS.get(p["classe_id"],[])[:4]

    for andar in andares:
        hp_m = andar["hp"]
        hp_mmx = andar["hp"]
        turno = 1

        boss_txt = " 💀 **BOSS**" if andar["eh_boss"] else ""
        embed_a = discord.Embed(
            title=f"🏰 {dg['nome']} — Andar {andar['numero']}{boss_txt}",
            description=f"{andar['emoji_monstro']} **{andar['nome_monstro']}** aparece!\n\n"
                       f"❤️ {hp_j}/{hp_jmx} | 💙 {mana_j}/{mana_jmx}",
            color=0x7F77DD if not andar["eh_boss"] else 0xE24B4A
        )
        await interaction.followup.send(embed=embed_a)
        await asyncio.sleep(0.5)

        while hp_j > 0 and hp_m > 0:
            pocoes = await get_pocoes_inv(interaction.user.id)
            view   = BatalhaView(interaction.user.id, skills, pocoes, nivel=p["nivel"])
            embed_t = discord.Embed(
                title=f"Turno {turno} — {andar['emoji_monstro']} {andar['nome_monstro']}",
                description=f"Voce: ❤️ {hp_j}/{hp_jmx} 💙 {mana_j}/{mana_jmx}\n"
                           f"Inimigo: ❤️ {hp_m}/{hp_mmx}",
                color=0x378ADD
            )
            msg_t = await interaction.followup.send(embed=embed_t, view=view, wait=True)
            await view.wait()
            try: await msg_t.edit(view=None)
            except: pass

            acao, val = view.acao or ("timeout", None)

            if acao == "timeout":
                timeout_count += 1
                if timeout_count >= 3:
                    embed_exp = discord.Embed(title="💤 Expulso por inatividade!",
                        description="Voce foi removido da dungeon.", color=0x888780)
                    await interaction.followup.send(embed=embed_exp)
                    BATALHAS_ATIVAS.discard(interaction.user.id)
                    async with pool.acquire() as conn:
                        await conn.execute("UPDATE dungeon_evento_runs SET falhou=TRUE WHERE id=$1", run["id"])
                    return
                await interaction.followup.send(
                    embed=discord.Embed(title=f"Turno perdido! ({timeout_count}/3)",
                        description=f"Sem acao em 30s.", color=0xE4AF3C))
                continue
            else:
                timeout_count = 0

            # Acao do jogador
            dano_j = 0
            if acao == "fugir":
                await interaction.followup.send(embed=discord.Embed(
                    title="🏃 Voce fugiu!", description="Nenhuma recompensa.", color=0x888780))
                BATALHAS_ATIVAS.discard(interaction.user.id)
                async with pool.acquire() as conn:
                    await conn.execute("UPDATE dungeon_evento_runs SET falhou=TRUE WHERE id=$1", run["id"])
                return
            elif acao == "atk_basico":
                mult = 1.0 + (p["nivel"]//10) * 0.1
                dano_j = calc_dano(p["ataque"], andar["defesa"], mult)
                hp_m = max(0, hp_m - dano_j)
                linha_j = f"⚔️ Ataque Basico: **{dano_j} de dano**!"
            elif acao == "skill" and val is not None:
                sk = skills[val] if val < len(skills) else skills[0]
                if mana_j >= sk.get("mana",0):
                    mana_j -= sk.get("mana",0)
                    dano_j  = calc_dano(p["ataque"], andar["defesa"], sk.get("dano",1.0))
                    hp_m = max(0, hp_m - dano_j)
                    linha_j = f"{sk['emoji']} **{sk['nome']}**: **{dano_j} de dano**!"
                else:
                    dano_j = calc_dano(p["ataque"], andar["defesa"])
                    hp_m = max(0, hp_m - dano_j)
                    linha_j = f"Sem mana! Ataque basico: **{dano_j} de dano**."
            elif acao == "defesa":
                if random.random() < 0.6:
                    dano_m = int(calc_dano(andar["ataque"], p["defesa"]) * 0.2)
                    hp_j = max(0, hp_j - dano_m)
                    linha_j = f"🛡️ Bloqueou! Tomou apenas **{dano_m} de dano**."
                else:
                    dano_m = calc_dano(andar["ataque"], p["defesa"])
                    hp_j = max(0, hp_j - dano_m)
                    linha_j = f"🛡️ Defesa falhou! Tomou **{dano_m} de dano**."
                turno += 1
                await interaction.followup.send(embed=discord.Embed(description=f"{linha_j}\n❤️ {hp_j}/{hp_jmx}", color=0x378ADD))
                continue
            elif acao == "pocao" and val:
                from batalha import aplicar_efeito_pocao, remover_pocao
                hp_j, mana_j, linha_j = aplicar_efeito_pocao(val, hp_j, hp_jmx, mana_j, mana_jmx)
                await remover_pocao(interaction.user.id, val)
                turno += 1
                await interaction.followup.send(embed=discord.Embed(description=linha_j, color=0x1D9E75))
                continue
            else:
                dano_j = calc_dano(p["ataque"], andar["defesa"])
                hp_m = max(0, hp_m - dano_j)
                linha_j = f"⚔️ Ataque: **{dano_j} de dano**!"

            if hp_m <= 0:
                await interaction.followup.send(embed=discord.Embed(
                    description=f"{linha_j}\n{andar['emoji_monstro']} **{andar['nome_monstro']}** foi derrotado!",
                    color=0x1D9E75))
                break

            # Ataque do monstro
            dano_m = calc_dano(andar["ataque"], p["defesa"])
            hp_j = max(0, hp_j - dano_m)
            mana_j = min(mana_jmx, mana_j + 5)

            cor_hp = 0x1D9E75 if hp_j > hp_jmx*0.5 else (0xE4AF3C if hp_j > hp_jmx*0.25 else 0xE24B4A)
            await interaction.followup.send(embed=discord.Embed(
                description=f"{linha_j}\n{andar['emoji_monstro']} contra-ataca: **{dano_m} de dano**!\n❤️ {hp_j}/{hp_jmx} 💙 {mana_j}/{mana_jmx}",
                color=cor_hp))
            turno += 1

        if hp_j <= 0:
            await interaction.followup.send(embed=discord.Embed(
                title="💀 Voce foi derrotado!",
                description=f"Caiu no andar **{andar['numero']}** de {len(andares)}.", color=0xE24B4A))
            BATALHAS_ATIVAS.discard(interaction.user.id)
            async with pool.acquire() as conn:
                await conn.execute("UPDATE dungeon_evento_runs SET falhou=TRUE WHERE id=$1", run["id"])
            return

        # Loot do andar
        if andar["loot_item_id"]:
            async with pool.acquire() as conn:
                ex = await conn.fetchrow("SELECT id FROM inventario WHERE user_id=$1 AND item_id=$2",
                    interaction.user.id, andar["loot_item_id"])
                if ex:
                    await conn.execute("UPDATE inventario SET quantidade=quantidade+1 WHERE id=$1", ex["id"])
                else:
                    await conn.execute(
                        "INSERT INTO inventario(user_id,item_id,nome,tipo,raridade,emoji,descricao) VALUES($1,$2,$3,$4,$5,$6,$7)",
                        interaction.user.id, andar["loot_item_id"], andar["loot_item_nome"],
                        andar["loot_item_tipo"], andar["loot_item_raridade"], andar["loot_item_emoji"],
                        f"Loot — {dg['nome']}")
            loot_txt = f"\n🎁 Loot: {andar['loot_item_emoji']} **{andar['loot_item_nome']}**" if andar["loot_item_nome"] else ""
            await interaction.followup.send(embed=discord.Embed(
                description=f"✅ Andar {andar['numero']} concluido!{loot_txt}", color=0x1D9E75))

        await asyncio.sleep(0.5)

    # Dungeon completa!
    BATALHAS_ATIVAS.discard(interaction.user.id)
    async with pool.acquire() as conn:
        await conn.execute("UPDATE dungeon_evento_runs SET concluida=TRUE, concluida_em=NOW() WHERE id=$1", run["id"])
        total = await conn.fetchval("SELECT COUNT(*) FROM dungeon_evento_runs WHERE dungeon_id=$1 AND concluida=TRUE", dungeon_id)

    embed_fim = discord.Embed(
        title=f"🏆 {dg['nome']} — COMPLETADA!",
        description=f"Parabens! Voce completou todos os **{len(andares)} andares**!\n\n🏆 **Premio:** {dg['premio']}",
        color=0xE4AF3C
    )
    await interaction.followup.send(embed=embed_fim)

    # Entrega premio
    from eventos import _entregar_premio
    await _entregar_premio(interaction.guild, interaction.user.id, "item", dg["premio"])

    # Fecha se modo for "primeiro"
    if dg["modo_fechamento"] == "primeiro":
        await _fechar_dungeon_evento(dungeon_id, interaction.guild, f"Primeiro a completar: {interaction.user.display_name}!")

async def cmd_dungeon_evento_info(interaction: discord.Interaction, dungeon_id: int):
    await interaction.response.defer(ephemeral=True)
    pool = await get_pool()
    async with pool.acquire() as conn:
        dg = await conn.fetchrow("SELECT * FROM dungeons_evento WHERE id=$1", dungeon_id)
        if not dg:
            await interaction.followup.send("Dungeon nao encontrada!", ephemeral=True); return
        andares = await conn.fetch("SELECT * FROM dungeon_evento_andares WHERE dungeon_id=$1 ORDER BY numero", dungeon_id)
        concluidas = await conn.fetchval("SELECT COUNT(*) FROM dungeon_evento_runs WHERE dungeon_id=$1 AND concluida=TRUE", dungeon_id)
        tentativas = await conn.fetchval("SELECT COUNT(*) FROM dungeon_evento_runs WHERE dungeon_id=$1", dungeon_id)

    embed = discord.Embed(title=f"🏰 {dg['nome']}",
        description=dg["descricao"], color=0x7F77DD)
    embed.add_field(name="Status",     value=dg["status"].title(), inline=True)
    embed.add_field(name="Andares",    value=str(len(andares)),     inline=True)
    embed.add_field(name="Concluidas", value=str(concluidas),       inline=True)
    embed.add_field(name="Tentativas", value=str(tentativas),       inline=True)
    embed.add_field(name="Rank Min",   value=dg["rank_minimo"],     inline=True)
    embed.add_field(name="Premio",     value=dg["premio"],          inline=False)
    if andares:
        lista = "\n".join([f"**{a['numero']}.** {a['emoji_monstro']} {a['nome_monstro']} — HP:{a['hp']} ATK:{a['ataque']}{' 💀' if a['eh_boss'] else ''}" for a in andares])
        embed.add_field(name="Andares Configurados", value=lista[:1000], inline=False)
    if dg["imagem_url"]: embed.set_image(url=dg["imagem_url"])
    await interaction.followup.send(embed=embed, ephemeral=True)

async def cmd_dungeon_evento_fechar(interaction: discord.Interaction, dungeon_id: int):
    await interaction.response.defer(ephemeral=True)
    await _fechar_dungeon_evento(dungeon_id, interaction.guild, "Encerrada pelo admin.")
    await interaction.followup.send(f"✅ Dungeon #{dungeon_id} fechada!", ephemeral=True)
