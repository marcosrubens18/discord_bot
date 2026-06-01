# -*- coding: utf-8 -*-
import sys, io, os, random, asyncio
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

import discord
from discord import app_commands
from discord.ext import commands

from db import get_pool, init_db
from catalogo import (
    get_rank, CARGOS_RANK, calcular_mana_max,
    get_armas_classe, get_armaduras_classe
)
from utils import atualizar_cargo_nivel, atualizar_cargo_rank, atualizar_todos_cargos
from setup_cmd import cmd_setup
from dungeon import cmd_dungeon
from hospital import cmd_hospital, cmd_girar, cmd_set_giros, init_db_hospital, COR_RAR, EMOJI_FICHA
from batalha import (
    rodar_pvp, rodar_treino, MONSTROS, SKILLS_POR_CLASSE, BATALHAS_ATIVAS,
    get_skills_eq, get_skills_desbloq, GerenciarSkillsView,
    AceitarDueloView, EscolherArenaView, init_db_batalha,
    ARENAS, LOJA_ITENS, RECEITAS, POCOES
)
from missoes import cmd_missoes, cmd_ranking, init_db_missoes, atualizar_progresso
from conquistas import cmd_conquistas, init_conquistas, verificar_conquistas
from eventos import cmd_criar_evento, cmd_eventos, cmd_evento_info, cmd_encerrar_evento, cmd_add_pontos, init_db_eventos
from anuncios import cmd_anunciar, cmd_anunciar_evento, cmd_agendar_anuncio, CORES
from torneio import (cmd_torneio_criar, cmd_torneio_status, cmd_torneio_lutar,
    cmd_torneio_fechar_inscricoes, cmd_torneio_cancelar, init_db_torneio)
from dungeon_evento import (cmd_dungeon_evento_ativar, cmd_dungeon_evento_info,
    cmd_dungeon_evento_fechar, AdicionarAndarModal, DungeonEventoCriarModal,
    init_db_dungeon_evento)
from mercado import cmd_mercador, cmd_mercado_vender
from racas import RACAS, RACAS_BASICAS, get_raca, PassivaRacial, COR_RAR_RACA
from imagens import (
    IMG_PERFIL, IMG_SETUP, IMG_INVENTARIO, IMG_SKILLS, IMG_AJUDA,
    IMG_LOJA, IMG_FERREIRO, IMG_HOSPITAL, IMG_MERCADO, IMG_MERCADOR,
    IMG_MISSOES, IMG_RANKING, IMG_CONQUISTAS, IMG_ROLETA,
    IMG_BANNER_GERAL, IMG_VITORIA, IMG_DERROTA, IMG_LEVEL_UP, IMG_CLASSE
)

# ─── DADOS ───────────────────────────────────────────────────────
def calcular_stats(poder_valor, destino_id, nivel=1):
    hp  = 80 + poder_valor*2 + nivel*5
    atk = 8  + poder_valor//5 + nivel*2
    dfs = 5  + poder_valor//6 + nivel*1
    if destino_id == "prodigio":    atk = int(atk*1.12); dfs = int(dfs*0.95)
    elif destino_id == "guardiao":  dfs = int(dfs*1.12); atk = int(atk*0.95)
    elif destino_id == "abencado":  hp=int(hp*1.08); atk=int(atk*1.05); dfs=int(dfs*1.05)
    elif destino_id == "maldito":   atk=int(atk*0.85); dfs=int(dfs*0.85)
    elif destino_id == "amaldicoado": atk=random.randint(5,atk+5); dfs=random.randint(3,dfs+3)
    return hp, atk, dfs



CLASSES = [
    {"id":"guerreiro","nome":"Guerreiro","emoji":"🗡️","raridade":"Comum","peso":30,"desc":"Combate corpo a corpo. Alta defesa."},
    {"id":"arqueiro","nome":"Arqueiro","emoji":"🏹","raridade":"Comum","peso":25,"desc":"Precisao e criticos frequentes."},
    {"id":"mago","nome":"Mago","emoji":"🔮","raridade":"Comum","peso":20,"desc":"Dano magico crescente por turno."},
    {"id":"paladino","nome":"Paladino","emoji":"⚡","raridade":"Incomum","peso":12,"desc":"Hibrido: cura e combate."},
    {"id":"necromante","nome":"Necromante","emoji":"🌑","raridade":"Raro","peso":8,"desc":"Drena vida dos inimigos."},
    {"id":"dracomante","nome":"Dracomante","emoji":"🐉","raridade":"Lendario","peso":2,"desc":"Sangue de dragao. Resistencia maxima."},
    {"id":"arcano","nome":"Arcano","emoji":"✨","raridade":"Epico","peso":3,"desc":"Dano arcano que ignora defesa."},
]
PODERES = [
    {"id":"fraquinho","nome":"Fraquinho","emoji":"💀","valor":10},
    {"id":"mediano","nome":"Mediano","emoji":"⚖️","valor":18},
    {"id":"acima","nome":"Acima da media","emoji":"📈","valor":26},
    {"id":"forte","nome":"Forte","emoji":"💪","valor":35},
    {"id":"epico","nome":"Epico","emoji":"⚡","valor":48},
    {"id":"absurdo","nome":"Absurdo","emoji":"🔥","valor":65},
]
PESOS_PODER = [20,30,25,15,7,3]
DESTINOS = [
    {"id":"equilibrado","nome":"Equilibrado","emoji":"⚖️"},
    {"id":"prodigio","nome":"Prodigio","emoji":"🔥"},
    {"id":"maldito","nome":"Maldito","emoji":"💀"},
    {"id":"guardiao","nome":"Guardiao","emoji":"🛡️"},
    {"id":"abencado","nome":"Abencado","emoji":"🌟"},
    {"id":"amaldicoado","nome":"Amaldicado","emoji":"☠️"},
    {"id":"filho_caos","nome":"Filho do Caos","emoji":"🌀"},
]
EMOJI_CLASSE = {"guerreiro":"🗡️","mago":"🔮","arqueiro":"🏹","paladino":"⚡","necromante":"🌑","dracomante":"🐉","arcano":"✨"}
COR_RAR_BOT  = {"Comum":0x888780,"Incomum":0x1D9E75,"Raro":0x378ADD,"Epico":0x7F77DD,"Lendario":0xD85A30}

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ─── HELPERS ─────────────────────────────────────────────────────

def sortear_peso(lista, pesos):
    return random.choices(lista, weights=pesos, k=1)[0]

async def get_personagem(user_id):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM personagens WHERE user_id=$1", user_id)

def em_batalha(uid): return uid in BATALHAS_ATIVAS

async def checar_batalha(inter):
    if em_batalha(inter.user.id):
        try: await inter.response.send_message("Voce esta em batalha! Termine primeiro.", ephemeral=True)
        except: pass
        return False
    return True

async def atualizar_cargo_rank(guild, member, rank):
    for nome_c, rank_c in CARGOS_RANK.items():
        cargo = discord.utils.get(guild.roles, name=nome_c)
        if cargo:
            try:
                if nome_c == rank_c:
                    await member.add_roles(cargo)
                else:
                    if cargo in member.roles:
                        await member.remove_roles(cargo)
            except: pass

async def criar_canal_privado(guild, member, nome, classe):
    try:
        # Busca categoria por varios nomes possiveis
        cat = (discord.utils.get(guild.categories, name="MEU PERFIL") or
               discord.utils.get(guild.categories, name="Meu Perfil") or
               discord.utils.get(guild.categories, name="PERFIL") or
               discord.utils.get(guild.categories, name="perfil"))
        # Se nao existe, cria
        if not cat:
            cat = await guild.create_category("MEU PERFIL")
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }
        nome_canal = f"{classe['emoji']}│{nome.lower()[:20]}"
        canal = await guild.create_text_channel(nome_canal, category=cat, overwrites=overwrites)
        # Manda mensagem de boas vindas no canal
        embed_bv = discord.Embed(
            title=f"Bem-vindo ao seu canal, {nome}!",
            description="Este e o seu espaco privado!\n\nUse `/perfil` `/inventario` `/treinar`",
            color=COR_RAR_BOT.get(classe.get("raridade","Comum"), 0x7F77DD)
        )
        embed_bv.set_footer(text="Villa Eldoria RPG — Sua jornada comeca aqui!")
        await canal.send(member.mention, embed=embed_bv)
    except Exception as e:
        print(f"Erro ao criar canal privado: {e}")

# ─── /criar_personagem ───────────────────────────────────────────

@bot.tree.command(name="criar_personagem", description="Escolha sua raca e classe para comecar!")
async def criar_personagem(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    uid = interaction.user.id
    if await get_personagem(uid):
        await interaction.followup.send("Voce ja tem personagem! Use /perfil.", ephemeral=True)
        return

    # Passo 1: Raca
    embed_raca = discord.Embed(title="Passo 1 — Escolha sua Raca", color=0x7F77DD)
    for rid in RACAS_BASICAS:
        r = RACAS[rid]
        embed_raca.add_field(name=f"{r['emoji']} {r['nome']}", value=r['passiva_desc'], inline=False)

    class RacaView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=120)
            self.escolha = None
        @discord.ui.button(label="Humano", style=discord.ButtonStyle.primary)
        async def btn_h(self, inter, b):
            if inter.user.id != uid: return
            self.escolha = "humano"; await inter.response.defer(); self.stop()
        @discord.ui.button(label="Anao", style=discord.ButtonStyle.primary)
        async def btn_a(self, inter, b):
            if inter.user.id != uid: return
            self.escolha = "anao"; await inter.response.defer(); self.stop()
        @discord.ui.button(label="Elfo", style=discord.ButtonStyle.primary)
        async def btn_e(self, inter, b):
            if inter.user.id != uid: return
            self.escolha = "elfo"; await inter.response.defer(); self.stop()

    vr = RacaView()
    msg = await interaction.followup.send(embed=embed_raca, view=vr, ephemeral=True, wait=True)
    await vr.wait()
    if not vr.escolha:
        await msg.edit(content="Tempo esgotado!", embed=None, view=None); return
    raca = RACAS[vr.escolha]

    # Passo 2: Classe
    BASICAS = [c for c in CLASSES if c["raridade"] == "Comum"]
    embed_cls = discord.Embed(title="Passo 2 — Escolha sua Classe", color=0xE4AF3C)
    for c in BASICAS:
        embed_cls.add_field(name=f"{c['emoji']} {c['nome']}", value=c["desc"], inline=True)
    embed_cls.set_footer(text=f"Raca: {raca['emoji']} {raca['nome']}")

    class ClasseView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=120)
            self.escolha = None
        @discord.ui.button(label="Guerreiro", style=discord.ButtonStyle.success)
        async def btn_g(self, inter, b):
            if inter.user.id != uid: return
            self.escolha = next(c for c in CLASSES if c["id"]=="guerreiro")
            await inter.response.defer(); self.stop()
        @discord.ui.button(label="Arqueiro", style=discord.ButtonStyle.success)
        async def btn_a(self, inter, b):
            if inter.user.id != uid: return
            self.escolha = next(c for c in CLASSES if c["id"]=="arqueiro")
            await inter.response.defer(); self.stop()
        @discord.ui.button(label="Mago", style=discord.ButtonStyle.success)
        async def btn_m(self, inter, b):
            if inter.user.id != uid: return
            self.escolha = next(c for c in CLASSES if c["id"]=="mago")
            await inter.response.defer(); self.stop()

    vc = ClasseView()
    await msg.edit(embed=embed_cls, view=vc)
    await vc.wait()
    if not vc.escolha:
        await msg.edit(content="Tempo esgotado!", embed=None, view=None); return
    classe = vc.escolha

    # Passo 3: Roletas
    await msg.edit(embed=discord.Embed(
        title="As roletas giram...",
        description=f"{raca['emoji']} {raca['nome']} + {classe['emoji']} {classe['nome']}\n\nSortindo poder, destino e skills...",
        color=0x7F77DD), view=None)
    await asyncio.sleep(1.5)

    poder   = sortear_peso(PODERES, PESOS_PODER)
    destino = random.choice(DESTINOS)
    mana_max = calcular_mana_max(classe["id"], 1, poder["valor"], destino["id"])
    if raca["id"] == "elfo": mana_max += 20

    from catalogo import SKILLS_COMPLETAS
    skills_cls = SKILLS_COMPLETAS.get(classe["id"], [])
    disp = [s for s in skills_cls if s["nivel"] <= 5]
    if len(disp) < 2: disp = skills_cls[:2]
    random.shuffle(disp)
    skills_s = disp[:2]

    hp, atk, dfs = calcular_stats(poder["valor"], destino["id"], 1)
    if raca["id"] == "anao": dfs += 8
    nome = interaction.user.display_name

    pool_db = await get_pool()
    async with pool_db.acquire() as conn:
        await conn.execute("""
            INSERT INTO personagens
            (user_id,nome,classe_id,raridade,poder_id,poder_valor,destino_id,skill_id,
             nivel,xp,hp_max,hp_atual,ataque,defesa,mana_max,mana_atual,moedas,raca_id)
            VALUES($1,$2,$3,$4,$5,$6,$7,$8,1,0,$9,$10,$11,$12,$13,$13,50,$14)
        """, uid, nome, classe["id"], classe["raridade"], poder["id"], poder["valor"],
            destino["id"], skills_s[0]["id"] if skills_s else "",
            hp, hp, atk, dfs, mana_max, raca["id"])
        for i, sk in enumerate(skills_s):
            await conn.execute("INSERT INTO skills_desbloqueadas(user_id,skill_id) VALUES($1,$2) ON CONFLICT DO NOTHING", uid, sk["id"])
            await conn.execute("INSERT INTO skills_equipadas(user_id,skill_id,slot) VALUES($1,$2,$3) ON CONFLICT(user_id,slot) DO UPDATE SET skill_id=EXCLUDED.skill_id", uid, sk["id"], i)

    efinal = discord.Embed(title=f"Bem-vindo, {nome}!", color=COR_RAR_BOT.get(classe["raridade"],0x888780))
    efinal.add_field(name="Raca",   value=f"{raca['emoji']} {raca['nome']}", inline=True)
    efinal.add_field(name="Classe", value=f"{classe['emoji']} {classe['nome']}", inline=True)
    efinal.add_field(name="Poder",  value=f"{poder['emoji']} {poder['nome']}", inline=True)
    efinal.add_field(name="Destino",value=f"{destino['emoji']} {destino['nome']}", inline=True)
    efinal.add_field(name="HP",     value=str(hp), inline=True)
    efinal.add_field(name="ATK",    value=str(atk), inline=True)
    efinal.add_field(name="Mana",   value=str(mana_max), inline=True)
    efinal.set_footer(text="Use /loja para comprar sua primeira arma! | /perfil para ver sua ficha")
    await msg.edit(embed=efinal, view=None)

    guild = interaction.guild
    if guild:
        member = guild.get_member(uid)
        if member:
            # Cargo de raca
            cargo_raca = discord.utils.get(guild.roles, name=raca.get("cargos",""))
            if cargo_raca:
                try: await member.add_roles(cargo_raca)
                except: pass
            # Cargo base
            cargo_base = discord.utils.get(guild.roles, name="🏠 Morador da Vila")
            if not cargo_base:
                cargo_base = discord.utils.get(guild.roles, name="Morador da Vila")
            if cargo_base:
                try: await member.add_roles(cargo_base)
                except: pass
            # Remove recem-chegado
            recem = discord.utils.get(guild.roles, name="🌱 Recem-chegado")
            if recem and recem in member.roles:
                try: await member.remove_roles(recem)
                except: pass
            # Cargo de rank/nivel
            await atualizar_todos_cargos(guild, member, 1)
        await criar_canal_privado(guild, member, nome, classe)

# ─── /perfil ─────────────────────────────────────────────────────

@bot.tree.command(name="perfil", description="Mostra a ficha do seu personagem")
@app_commands.describe(jogador="Jogador (opcional)")
async def perfil(interaction: discord.Interaction, jogador: discord.Member = None):
    await interaction.response.defer()
    alvo = jogador or interaction.user
    p = await get_personagem(alvo.id)
    if not p:
        await interaction.followup.send("Personagem nao encontrado!", ephemeral=True); return
    cls    = next((c for c in CLASSES if c["id"]==p["classe_id"]), None)
    raca_p = get_raca(p["raca_id"] if p["raca_id"] else "humano")
    rank_i = get_rank(p["nivel"])
    pool_db = await get_pool()
    async with pool_db.acquire() as conn:
        arma = await conn.fetchrow("SELECT * FROM inventario WHERE user_id=$1 AND tipo='arma' AND equipado=1", alvo.id)
        arm  = await conn.fetchrow("SELECT * FROM inventario WHERE user_id=$1 AND tipo='armadura' AND equipado=1", alvo.id)
        ids_eq = await conn.fetch("SELECT skill_id FROM skills_equipadas WHERE user_id=$1 ORDER BY slot", alvo.id)
    from catalogo import SKILLS_COMPLETAS
    sk_nomes = []
    for r in ids_eq:
        for sk in SKILLS_COMPLETAS.get(p["classe_id"],[]):
            if sk["id"]==r["skill_id"]: sk_nomes.append(f"{sk['emoji']} {sk['nome']}"); break
    xp_need = 100 + (p["nivel"]-1)*50
    embed = discord.Embed(
        title=f"{cls['emoji'] if cls else '?'} {p['nome']}",
        description=(
            f"**Raca:** {raca_p['emoji']} {raca_p['nome']}\n"
            f"**Classe:** {cls['nome'] if cls else p['classe_id']} — *{p['raridade']}*\n"
            f"**Rank:** {rank_i['emoji']} {rank_i['rank']} — {rank_i['nome']}\n"
            f"**Nivel:** {p['nivel']} | XP: {p['xp']}/{xp_need}"
        ),
        color=COR_RAR_BOT.get(p["raridade"],0x888780)
    )
    embed.add_field(name="Stats", value=f"❤️ {p['hp_atual']}/{p['hp_max']} | ⚔️ {p['ataque']} | 🛡️ {p['defesa']} | 💙 {p['mana_atual']}/{p['mana_max']}", inline=False)
    embed.add_field(name="Equipamento", value=f"⚔️ {arma['nome'] if arma else 'Sem arma'} | 🛡️ {arm['nome'] if arm else 'Sem armadura'}", inline=False)
    if sk_nomes: embed.add_field(name="Skills", value=" | ".join(sk_nomes), inline=False)
    embed.add_field(name=f"{raca_p['emoji']} Passiva Racial", value=raca_p['passiva_desc'], inline=False)
    embed.add_field(name="Moedas", value=f"{p['moedas']} 🪙", inline=True)
    embed.add_field(name="Vitorias", value=str(p.get('vitorias',0)), inline=True)
    embed.set_thumbnail(url=alvo.display_avatar.url)
    await interaction.followup.send(embed=embed)

# ─── /inventario ─────────────────────────────────────────────────

@bot.tree.command(name="inventario", description="Mostra seu inventario completo")
@app_commands.describe(jogador="Jogador (opcional)")
async def inventario(interaction: discord.Interaction, jogador: discord.Member = None):
    await interaction.response.defer(ephemeral=True)
    alvo = jogador or interaction.user
    p = await get_personagem(alvo.id)
    if not p:
        await interaction.followup.send("Personagem nao encontrado!", ephemeral=True); return
    pool_db = await get_pool()
    async with pool_db.acquire() as conn:
        itens = await conn.fetch("SELECT * FROM inventario WHERE user_id=$1 ORDER BY tipo,raridade", alvo.id)
    armas  = [i for i in itens if i["tipo"]=="arma"]
    armdrs = [i for i in itens if i["tipo"]=="armadura"]
    pocoes = [i for i in itens if i["tipo"]=="pocao" or i["item_id"]=="elixir"]
    mats   = [i for i in itens if i["tipo"]=="material"]
    embed  = discord.Embed(title=f"Inventario de {alvo.display_name}", color=0x7F77DD)
    def fmt(lista):
        if not lista: return "—"
        return "\n".join([f"{i['emoji']} **{i['nome']}** [{i['raridade']}] (x{i.get('quantidade',1)}){' ✅' if i.get('equipado') else ''}" for i in lista])
    embed.add_field(name="Mochila", value=fmt(pocoes) if pocoes else "—", inline=False)
    embed.add_field(name="Armas",   value=fmt(armas)  if armas  else "—", inline=True)
    embed.add_field(name="Armaduras",value=fmt(armdrs) if armdrs else "—",inline=True)
    if mats: embed.add_field(name="Materiais", value=fmt(mats), inline=False)
    embed.set_footer(text=f"Moedas: {p['moedas']} 🪙")
    if IMG_INVENTARIO: embed.set_image(url=IMG_INVENTARIO)

    # Botoes de equipar para armas e armaduras
    equipaveis = armas + armdrs
    if equipaveis and alvo.id == interaction.user.id:
        opcoes = [discord.SelectOption(
            label=f"{i['emoji']} {i['nome'][:40]}",
            value=str(i["id"]),
            description=f"{i['tipo'].title()} | {i['raridade']}",
            default=bool(i.get("equipado"))
        ) for i in equipaveis[:25]]

        class EquiparView(discord.ui.View):
            def __init__(self): super().__init__(timeout=60)
            @discord.ui.select(placeholder="Equipar item...", options=opcoes)
            async def sel(self, inter: discord.Interaction, s):
                if inter.user.id != interaction.user.id: return
                item_id = int(s.values[0])
                item_row = next((i for i in equipaveis if i["id"]==item_id), None)
                if not item_row: await inter.response.send_message("Item nao encontrado!", ephemeral=True); return
                pool2 = await get_pool()
                async with pool2.acquire() as conn2:
                    await conn2.execute("UPDATE inventario SET equipado=0 WHERE user_id=$1 AND tipo=$2", inter.user.id, item_row["tipo"])
                    await conn2.execute("UPDATE inventario SET equipado=1 WHERE id=$1", item_id)
                await inter.response.send_message(f"Equipado: {item_row['emoji']} **{item_row['nome']}**!", ephemeral=True)

        await interaction.followup.send(embed=embed, view=EquiparView(), ephemeral=True)
    else:
        await interaction.followup.send(embed=embed, ephemeral=True)

# ─── /setup ──────────────────────────────────────────────────────

@bot.tree.command(name="setup", description="Monte seu setup completo")
async def setup(interaction: discord.Interaction):
    await cmd_setup(interaction)

# ─── /skills ─────────────────────────────────────────────────────

@bot.tree.command(name="skills", description="Veja e gerencie suas skills equipadas")
async def skills(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    p = await get_personagem(interaction.user.id)
    if not p:
        await interaction.followup.send("Crie seu personagem primeiro!", ephemeral=True); return
    from catalogo import SKILLS_COMPLETAS
    todas = SKILLS_COMPLETAS.get(p["classe_id"], [])
    ids_desbloq = await get_skills_desbloq(interaction.user.id)
    ids_eq      = await get_skills_eq(interaction.user.id)
    disp = [s for s in todas if s["id"] in ids_desbloq]
    if not disp:
        await interaction.followup.send("Nenhuma skill desbloqueada ainda!", ephemeral=True); return
    view = GerenciarSkillsView(interaction.user.id, disp, ids_eq)
    embed = discord.Embed(title="Gerenciar Skills", description="Selecione ate 4 skills para equipar:", color=0x7F77DD)
    for s in disp:
        mana_txt = f" | {s['mana']} mana" if s.get('mana') else ''
        embed.add_field(name=f"{s['emoji']} {s['nome']} (Nv{s['nivel']})", value=f"{s['desc']}{mana_txt}", inline=True)
    await interaction.followup.send(embed=embed, view=view, ephemeral=True)

# ─── /equipar ────────────────────────────────────────────────────

@bot.tree.command(name="equipar", description="Equipa um item do inventario pelo nome")
@app_commands.describe(item="Nome do item a equipar")
async def equipar(interaction: discord.Interaction, item: str):
    await interaction.response.defer(ephemeral=True)
    p = await get_personagem(interaction.user.id)
    if not p:
        await interaction.followup.send("Crie seu personagem primeiro!", ephemeral=True); return
    pool_db = await get_pool()
    async with pool_db.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM inventario WHERE user_id=$1 AND LOWER(nome) LIKE $2 AND tipo IN ('arma','armadura') LIMIT 1",
            interaction.user.id, f"%{item.lower()}%")
        if not row:
            await interaction.followup.send(f"Item '{item}' nao encontrado!", ephemeral=True); return
        await conn.execute("UPDATE inventario SET equipado=0 WHERE user_id=$1 AND tipo=$2", interaction.user.id, row["tipo"])
        await conn.execute("UPDATE inventario SET equipado=1 WHERE id=$1", row["id"])
    await interaction.followup.send(f"Equipado: {row['emoji']} **{row['nome']}**!", ephemeral=True)

# ─── /jogar-fora ─────────────────────────────────────────────────

@bot.tree.command(name="jogar-fora", description="Descarta um item do inventario")
@app_commands.describe(item="Nome do item a descartar")
async def jogar_fora(interaction: discord.Interaction, item: str):
    await interaction.response.defer(ephemeral=True)
    pool_db = await get_pool()
    async with pool_db.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM inventario WHERE user_id=$1 AND LOWER(nome) LIKE $2 LIMIT 1",
            interaction.user.id, f"%{item.lower()}%")
        if not row:
            await interaction.followup.send(f"Item '{item}' nao encontrado!", ephemeral=True); return
        await conn.execute("DELETE FROM inventario WHERE id=$1", row["id"])
    await interaction.followup.send(f"Descartado: {row['emoji']} {row['nome']}", ephemeral=True)

# ─── /dar ────────────────────────────────────────────────────────

@bot.tree.command(name="dar", description="Da um item para outro jogador")
@app_commands.describe(jogador="Jogador que recebe", item="Nome do item")
async def dar(interaction: discord.Interaction, jogador: discord.Member, item: str):
    await interaction.response.defer(ephemeral=True)
    if jogador.id == interaction.user.id:
        await interaction.followup.send("Voce nao pode dar item para si mesmo!", ephemeral=True); return
    pool_db = await get_pool()
    async with pool_db.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM inventario WHERE user_id=$1 AND LOWER(nome) LIKE $2 LIMIT 1",
            interaction.user.id, f"%{item.lower()}%")
        if not row:
            await interaction.followup.send(f"Item '{item}' nao encontrado!", ephemeral=True); return
        ex = await conn.fetchrow("SELECT id,quantidade FROM inventario WHERE user_id=$1 AND item_id=$2", jogador.id, row["item_id"])
        if ex: await conn.execute("UPDATE inventario SET quantidade=quantidade+1 WHERE id=$1", ex["id"])
        else: await conn.execute("INSERT INTO inventario(user_id,item_id,nome,tipo,raridade,emoji,descricao) VALUES($1,$2,$3,$4,$5,$6,$7)",
            jogador.id, row["item_id"], row["nome"], row["tipo"], row["raridade"], row["emoji"], row["descricao"])
        if row["quantidade"] > 1: await conn.execute("UPDATE inventario SET quantidade=quantidade-1 WHERE id=$1", row["id"])
        else: await conn.execute("DELETE FROM inventario WHERE id=$1", row["id"])
    await interaction.followup.send(f"Dado {row['emoji']} **{row['nome']}** para {jogador.mention}!", ephemeral=True)

# ─── /treinar ────────────────────────────────────────────────────

@bot.tree.command(name="treinar", description="Batalha contra monstros para ganhar XP")
@app_commands.describe(dificuldade="Escolha a dificuldade")
@app_commands.choices(dificuldade=[
    app_commands.Choice(name="Facil",    value="facil"),
    app_commands.Choice(name="Medio",    value="medio"),
    app_commands.Choice(name="Dificil",  value="dificil"),
    app_commands.Choice(name="Lendario", value="lendario"),
])
async def treinar(interaction: discord.Interaction, dificuldade: str = "facil"):
    await interaction.response.defer()
    if em_batalha(interaction.user.id):
        await interaction.followup.send("Voce ja esta em batalha!", ephemeral=True); return
    p = await get_personagem(interaction.user.id)
    if not p:
        await interaction.followup.send("Use /criar_personagem primeiro!", ephemeral=True); return
    monstros_d = [m for m in MONSTROS if m["dificuldade"] == dificuldade]
    if not monstros_d:
        await interaction.followup.send("Dificuldade invalida!", ephemeral=True); return
    monstro = random.choice(monstros_d)
    view_arena = EscolherArenaView(interaction.user.id)
    await interaction.followup.send("Escolha a arena:", view=view_arena, wait=True)
    await view_arena.wait()
    arena = view_arena.arena or random.choice(ARENAS)
    await rodar_treino(interaction, p, monstro, arena)

# ─── /desafiar ───────────────────────────────────────────────────

@bot.tree.command(name="desafiar", description="Desafia outro jogador para um duelo PvP")
@app_commands.describe(jogador="Jogador a desafiar")
async def desafiar(interaction: discord.Interaction, jogador: discord.Member):
    await interaction.response.defer()
    if em_batalha(interaction.user.id):
        await interaction.followup.send("Voce ja esta em batalha!", ephemeral=True); return
    if jogador.bot or jogador.id == interaction.user.id:
        await interaction.followup.send("Jogador invalido!", ephemeral=True); return
    p1 = await get_personagem(interaction.user.id)
    p2 = await get_personagem(jogador.id)
    if not p1: await interaction.followup.send("Voce nao tem personagem!", ephemeral=True); return
    if not p2: await interaction.followup.send(f"{jogador.display_name} nao tem personagem!", ephemeral=True); return
    view = AceitarDueloView(interaction.user.id, jogador.id)
    embed = discord.Embed(title="Desafio de Duelo!", description=f"{interaction.user.mention} desafia {jogador.mention}!\nVoce aceita?", color=0xE4AF3C)
    msg_d = await interaction.followup.send(embed=embed, view=view, wait=True)
    await view.wait()
    if not view.resposta:
        await msg_d.edit(embed=discord.Embed(title="Desafio recusado!", color=0x888780), view=None); return
    arena = random.choice(ARENAS)
    await msg_d.edit(embed=discord.Embed(title=f"Duelo! {arena['emoji']} {arena['nome']}", color=0x1D9E75), view=None)
    await rodar_pvp(interaction.channel, p1, p2, interaction.user, jogador, arena)

# ─── /dungeon ────────────────────────────────────────────────────

@bot.tree.command(name="dungeon", description="Entre em uma dungeon! Se morrer perde tudo")
@app_commands.describe(rank="Rank da dungeon")
@app_commands.choices(rank=[
    app_commands.Choice(name="Rank F (Nv 1+)",   value="F"),
    app_commands.Choice(name="Rank E (Nv 10+)",  value="E"),
    app_commands.Choice(name="Rank D (Nv 20+)",  value="D"),
    app_commands.Choice(name="Rank C (Nv 30+)",  value="C"),
    app_commands.Choice(name="Rank B (Nv 40+)",  value="B"),
    app_commands.Choice(name="Rank A (Nv 50+)",  value="A"),
    app_commands.Choice(name="Rank S (Nv 60+)",  value="S"),
    app_commands.Choice(name="Rank SS (Nv 75+)", value="SS"),
])
async def dungeon(interaction: discord.Interaction, rank: str = "F"):
    if interaction.user.id in BATALHAS_ATIVAS:
        await interaction.response.send_message("Voce ja esta em batalha!", ephemeral=True); return
    await cmd_dungeon(interaction, rank)

# ─── /hospital ───────────────────────────────────────────────────

@bot.tree.command(name="hospital", description="Restaure seu HP e Mana no hospital")
async def hospital(interaction: discord.Interaction):
    await cmd_hospital(interaction)

# ─── /girar ──────────────────────────────────────────────────────

@bot.tree.command(name="girar", description="Use fichas de roleta para ganhar itens raros")
async def girar(interaction: discord.Interaction):
    await cmd_girar(interaction)

# ─── /loja ───────────────────────────────────────────────────────

@bot.tree.command(name="loja", description="Compre armas, armaduras e pocoes")
@app_commands.describe(categoria="Categoria de item")
@app_commands.choices(categoria=[
    app_commands.Choice(name="Armas",     value="armas"),
    app_commands.Choice(name="Armaduras", value="armaduras"),
    app_commands.Choice(name="Pocoes",    value="pocoes"),
])
async def loja(interaction: discord.Interaction, categoria: str = "pocoes"):
    await interaction.response.defer(ephemeral=True)
    p = await get_personagem(interaction.user.id)
    if not p:
        await interaction.followup.send("Crie seu personagem primeiro!", ephemeral=True); return
    if categoria == "armas":
        itens = [i for i in get_armas_classe(p["classe_id"]) if i["raridade"] in ("Comum","Incomum")]
    elif categoria == "armaduras":
        itens = [i for i in get_armaduras_classe(p["classe_id"]) if i["raridade"] in ("Comum","Incomum")]
    else:
        itens = [{"id":k,"nome":v["nome"],"emoji":v["emoji"],"raridade":"Comum","preco":v["preco"],"desc":f"Recupera {v['valor']} HP/Mana"} for k,v in POCOES.items()]
    if not itens:
        await interaction.followup.send("Nenhum item disponivel!", ephemeral=True); return
    opcoes = [discord.SelectOption(label=f"{i['emoji']} {i['nome']} — {i.get('preco',0)} moedas", value=i["id"], description=i.get("desc","")[:50]) for i in itens[:25]]
    class LojaView(discord.ui.View):
        def __init__(self): super().__init__(timeout=60); self.item = None
        @discord.ui.select(placeholder="Escolha o item...", options=opcoes)
        async def sel(self, inter, s):
            if inter.user.id != interaction.user.id: return
            self.item = next((i for i in itens if i["id"]==s.values[0]), None)
            await inter.response.defer(); self.stop()
    v = LojaView()
    embed_loja = discord.Embed(title=f"Loja — {categoria.title()}", description=f"Moedas: **{p['moedas']}**", color=0xE4AF3C)
    await interaction.followup.send(embed=embed_loja, view=v, ephemeral=True)
    await v.wait()
    if not v.item: return
    it = v.item; preco = it.get("preco",0)
    if p["moedas"] < preco:
        await interaction.followup.send(f"Moedas insuficientes! Precisa de {preco}.", ephemeral=True); return
    pool_db = await get_pool()
    async with pool_db.acquire() as conn:
        await conn.execute("UPDATE personagens SET moedas=moedas-$1 WHERE user_id=$2", preco, interaction.user.id)
        ex = await conn.fetchrow("SELECT id FROM inventario WHERE user_id=$1 AND item_id=$2", interaction.user.id, it["id"])
        if ex: await conn.execute("UPDATE inventario SET quantidade=quantidade+1 WHERE id=$1", ex["id"])
        else: await conn.execute("INSERT INTO inventario(user_id,item_id,nome,tipo,raridade,emoji,descricao) VALUES($1,$2,$3,$4,$5,$6,$7)",
            interaction.user.id, it["id"], it["nome"], categoria.rstrip("s"), it["raridade"], it["emoji"], it.get("desc",""))
    await interaction.followup.send(f"Comprou {it['emoji']} **{it['nome']}** por {preco} moedas!", ephemeral=True)

# ─── /ferreiro ───────────────────────────────────────────────────

@bot.tree.command(name="ferreiro", description="Forje itens com materiais de dungeon")
async def ferreiro(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    p = await get_personagem(interaction.user.id)
    if not p:
        await interaction.followup.send("Crie seu personagem primeiro!", ephemeral=True); return
    pool_db = await get_pool()
    async with pool_db.acquire() as conn:
        inv = await conn.fetch("SELECT item_id,quantidade FROM inventario WHERE user_id=$1", interaction.user.id)
        pf  = await conn.fetchrow("SELECT moedas FROM personagens WHERE user_id=$1", interaction.user.id)
    inv_map = {r["item_id"]:r["quantidade"] for r in inv}
    disp = [r for r in RECEITAS if all(inv_map.get(m,0)>=q for m,q in r["materiais"].items())]
    desc = "\n".join([f"{r['emoji']} **{r['nome']}** [{r['raridade']}] — {r['preco_forja']} moedas" for r in RECEITAS])
    if not disp:
        await interaction.followup.send(embed=discord.Embed(title="Ferreiro", description=f"Sem materiais suficientes!\n\n{desc}", color=0x888780), ephemeral=True); return
    opcoes = [discord.SelectOption(label=f"{r['emoji']} {r['nome']}", value=r["id"]) for r in disp[:25]]
    class FerreiroView(discord.ui.View):
        def __init__(self): super().__init__(timeout=60); self.escolha = None
        @discord.ui.select(placeholder="Escolha a receita...", options=opcoes)
        async def sel(self, inter, s):
            if inter.user.id != interaction.user.id: return
            self.escolha = s.values[0]; await inter.response.defer(); self.stop()
    v = FerreiroView()
    await interaction.followup.send(embed=discord.Embed(title="Ferreiro", description=desc, color=0x888780), view=v, ephemeral=True)
    await v.wait()
    if not v.escolha: return
    receita = next((r for r in RECEITAS if r["id"]==v.escolha), None)
    if not receita: return
    if pf["moedas"] < receita["preco_forja"]:
        await interaction.followup.send("Moedas insuficientes!", ephemeral=True); return
    async with pool_db.acquire() as conn:
        await conn.execute("UPDATE personagens SET moedas=moedas-$1 WHERE user_id=$2", receita["preco_forja"], interaction.user.id)
        for mat, qtd in receita["materiais"].items():
            row = await conn.fetchrow("SELECT id,quantidade FROM inventario WHERE user_id=$1 AND item_id=$2", interaction.user.id, mat)
            if row:
                if row["quantidade"] > qtd: await conn.execute("UPDATE inventario SET quantidade=quantidade-$1 WHERE id=$2", qtd, row["id"])
                else: await conn.execute("DELETE FROM inventario WHERE id=$1", row["id"])
        ex = await conn.fetchrow("SELECT id FROM inventario WHERE user_id=$1 AND item_id=$2", interaction.user.id, receita["id"])
        if ex: await conn.execute("UPDATE inventario SET quantidade=quantidade+1 WHERE id=$1", ex["id"])
        else: await conn.execute("INSERT INTO inventario(user_id,item_id,nome,tipo,raridade,emoji,descricao) VALUES($1,$2,$3,$4,$5,$6,$7)",
            interaction.user.id, receita["id"], receita["nome"], receita["tipo"], receita["raridade"], receita["emoji"], receita["desc"])
    await interaction.followup.send(f"Forjado: {receita['emoji']} **{receita['nome']}**!", ephemeral=True)

# ─── /mercado ────────────────────────────────────────────────────

@bot.tree.command(name="mercado", description="Venda itens do inventario por moedas")
async def mercado(interaction: discord.Interaction):
    await cmd_mercado_vender(interaction)

# ─── /mercador ───────────────────────────────────────────────────

@bot.tree.command(name="mercador", description="Troque materiais por itens exclusivos")
async def mercador(interaction: discord.Interaction):
    await cmd_mercador(interaction)

# ─── /missoes ────────────────────────────────────────────────────

@bot.tree.command(name="missoes", description="Veja e complete suas missoes diarias")
async def missoes(interaction: discord.Interaction):
    await cmd_missoes(interaction)

# ─── /ranking ────────────────────────────────────────────────────

@bot.tree.command(name="ranking", description="Top 10 jogadores do servidor")
async def ranking(interaction: discord.Interaction):
    await cmd_ranking(interaction)

# ─── /conquistas ─────────────────────────────────────────────────

@bot.tree.command(name="conquistas", description="Veja suas conquistas e progresso")
async def conquistas(interaction: discord.Interaction):
    await cmd_conquistas(interaction)

# ─── /set-item ───────────────────────────────────────────────────

@bot.tree.command(name="set-item", description="[ADMIN] Da item a um jogador")
@app_commands.describe(jogador="Jogador alvo", categoria="Categoria", quantidade="Quantidade")
@app_commands.choices(categoria=[
    app_commands.Choice(name="Pocoes",             value="pocoes"),
    app_commands.Choice(name="Armas Guerreiro",    value="arma_guerreiro"),
    app_commands.Choice(name="Armas Arqueiro",     value="arma_arqueiro"),
    app_commands.Choice(name="Armas Mago",         value="arma_mago"),
    app_commands.Choice(name="Armas Paladino",     value="arma_paladino"),
    app_commands.Choice(name="Armas Necromante",   value="arma_necromante"),
    app_commands.Choice(name="Armas Dracomante",   value="arma_dracomante"),
    app_commands.Choice(name="Armas Arcano",       value="arma_arcano"),
    app_commands.Choice(name="Armaduras Guerreiro",value="arm_guerreiro"),
    app_commands.Choice(name="Armaduras Arqueiro", value="arm_arqueiro"),
    app_commands.Choice(name="Armaduras Mago",     value="arm_mago"),
    app_commands.Choice(name="Armaduras Paladino", value="arm_paladino"),
    app_commands.Choice(name="Armaduras Necromante",value="arm_necromante"),
    app_commands.Choice(name="Armaduras Dracomante",value="arm_dracomante"),
    app_commands.Choice(name="Armaduras Arcano",   value="arm_arcano"),
    app_commands.Choice(name="Materiais",          value="materiais"),
])
@app_commands.checks.has_permissions(administrator=True)
async def set_item(interaction: discord.Interaction, jogador: discord.Member, categoria: str, quantidade: int = 1):
    await interaction.response.defer(ephemeral=True)
    if not await get_personagem(jogador.id):
        await interaction.followup.send(f"{jogador.display_name} nao tem personagem!", ephemeral=True); return
    from catalogo import ARMAS_POR_CLASSE, ARMADURAS_POR_CLASSE
    POCOES_LIST = [
        {"id":"pocao_hp_p","nome":"Pocao de Cura P","emoji":"🧪","tipo":"pocao","raridade":"Comum","desc":"Recupera 30 HP"},
        {"id":"pocao_hp_m","nome":"Pocao de Cura M","emoji":"💊","tipo":"pocao","raridade":"Comum","desc":"Recupera 60 HP"},
        {"id":"pocao_hp_g","nome":"Pocao de Cura G","emoji":"❤️","tipo":"pocao","raridade":"Raro","desc":"Recupera 120 HP"},
        {"id":"pocao_mana_p","nome":"Pocao de Mana P","emoji":"🔵","tipo":"pocao","raridade":"Comum","desc":"Recupera 20 Mana"},
        {"id":"pocao_mana_m","nome":"Pocao de Mana M","emoji":"💙","tipo":"pocao","raridade":"Incomum","desc":"Recupera 50 Mana"},
        {"id":"elixir","nome":"Elixir Supremo","emoji":"✨","tipo":"pocao","raridade":"Epico","desc":"HP e Mana full"},
    ]
    MATS_LIST = [
        {"id":"dente_orc","nome":"Dente de Orc","emoji":"🦷","tipo":"material","raridade":"Incomum","desc":"Ingrediente"},
        {"id":"fragmento_golem","nome":"Fragmento de Golem","emoji":"🪨","tipo":"material","raridade":"Raro","desc":"Material magico"},
        {"id":"sangue_anciao","nome":"Sangue Anciao","emoji":"🩸","tipo":"material","raridade":"Raro","desc":"Raro"},
        {"id":"escama_dragao_p","nome":"Escama de Dragao","emoji":"🐉","tipo":"material","raridade":"Raro","desc":"Fragmento"},
        {"id":"olho_dragao","nome":"Olho de Dragao","emoji":"👁️","tipo":"material","raridade":"Epico","desc":"Epico"},
        {"id":"essencia_lich","nome":"Essencia do Lich","emoji":"💀","tipo":"material","raridade":"Lendario","desc":"Lendario"},
        {"id":"coroa_criador","nome":"Coroa do Criador","emoji":"👑","tipo":"armadura","raridade":"Lendario","desc":"Definitiva"},
    ]
    cat_map = {
        "pocoes": POCOES_LIST,
        "arma_guerreiro":[{"id":a["id"],"nome":a["nome"],"emoji":a["emoji"],"tipo":"arma","raridade":a["raridade"],"desc":a["desc"]} for a in ARMAS_POR_CLASSE["guerreiro"]],
        "arma_arqueiro": [{"id":a["id"],"nome":a["nome"],"emoji":a["emoji"],"tipo":"arma","raridade":a["raridade"],"desc":a["desc"]} for a in ARMAS_POR_CLASSE["arqueiro"]],
        "arma_mago":     [{"id":a["id"],"nome":a["nome"],"emoji":a["emoji"],"tipo":"arma","raridade":a["raridade"],"desc":a["desc"]} for a in ARMAS_POR_CLASSE["mago"]],
        "arma_paladino": [{"id":a["id"],"nome":a["nome"],"emoji":a["emoji"],"tipo":"arma","raridade":a["raridade"],"desc":a["desc"]} for a in ARMAS_POR_CLASSE["paladino"]],
        "arma_necromante":[{"id":a["id"],"nome":a["nome"],"emoji":a["emoji"],"tipo":"arma","raridade":a["raridade"],"desc":a["desc"]} for a in ARMAS_POR_CLASSE["necromante"]],
        "arma_dracomante":[{"id":a["id"],"nome":a["nome"],"emoji":a["emoji"],"tipo":"arma","raridade":a["raridade"],"desc":a["desc"]} for a in ARMAS_POR_CLASSE["dracomante"]],
        "arma_arcano":   [{"id":a["id"],"nome":a["nome"],"emoji":a["emoji"],"tipo":"arma","raridade":a["raridade"],"desc":a["desc"]} for a in ARMAS_POR_CLASSE["arcano"]],
        "arm_guerreiro": [{"id":a["id"],"nome":a["nome"],"emoji":a["emoji"],"tipo":"armadura","raridade":a["raridade"],"desc":a["desc"]} for a in ARMADURAS_POR_CLASSE["guerreiro"]],
        "arm_arqueiro":  [{"id":a["id"],"nome":a["nome"],"emoji":a["emoji"],"tipo":"armadura","raridade":a["raridade"],"desc":a["desc"]} for a in ARMADURAS_POR_CLASSE["arqueiro"]],
        "arm_mago":      [{"id":a["id"],"nome":a["nome"],"emoji":a["emoji"],"tipo":"armadura","raridade":a["raridade"],"desc":a["desc"]} for a in ARMADURAS_POR_CLASSE["mago"]],
        "arm_paladino":  [{"id":a["id"],"nome":a["nome"],"emoji":a["emoji"],"tipo":"armadura","raridade":a["raridade"],"desc":a["desc"]} for a in ARMADURAS_POR_CLASSE["paladino"]],
        "arm_necromante":[{"id":a["id"],"nome":a["nome"],"emoji":a["emoji"],"tipo":"armadura","raridade":a["raridade"],"desc":a["desc"]} for a in ARMADURAS_POR_CLASSE["necromante"]],
        "arm_dracomante":[{"id":a["id"],"nome":a["nome"],"emoji":a["emoji"],"tipo":"armadura","raridade":a["raridade"],"desc":a["desc"]} for a in ARMADURAS_POR_CLASSE["dracomante"]],
        "arm_arcano":    [{"id":a["id"],"nome":a["nome"],"emoji":a["emoji"],"tipo":"armadura","raridade":a["raridade"],"desc":a["desc"]} for a in ARMADURAS_POR_CLASSE["arcano"]],
        "materiais": MATS_LIST,
    }
    itens = cat_map.get(categoria, [])
    if not itens:
        await interaction.followup.send("Categoria invalida!", ephemeral=True); return
    qtd = max(1, min(quantidade, 99))
    opcoes = [discord.SelectOption(label=f"{it['emoji']} {it['nome'][:40]}", value=it["id"], description=f"{it['raridade']}") for it in itens[:25]]
    class SetItemView(discord.ui.View):
        def __init__(self): super().__init__(timeout=120); self.item = None
        @discord.ui.select(placeholder="Escolha o item...", options=opcoes)
        async def sel(self, inter, s):
            if inter.user.id != interaction.user.id: return
            self.item = next((i for i in itens if i["id"]==s.values[0]), None)
            await inter.response.defer(); self.stop()
    v = SetItemView()
    embed = discord.Embed(title=f"Dar item para {jogador.display_name}", description=f"Categoria: **{categoria}** | Qtd: **{qtd}x**", color=0x7F77DD)
    await interaction.followup.send(embed=embed, view=v, ephemeral=True)
    await v.wait()
    if not v.item: return
    it = v.item
    pool_db = await get_pool()
    async with pool_db.acquire() as conn:
        ex = await conn.fetchrow("SELECT id,quantidade FROM inventario WHERE user_id=$1 AND item_id=$2", jogador.id, it["id"])
        if ex: await conn.execute("UPDATE inventario SET quantidade=quantidade+$1 WHERE id=$2", qtd, ex["id"])
        else: await conn.execute("INSERT INTO inventario(user_id,item_id,nome,tipo,raridade,emoji,descricao) VALUES($1,$2,$3,$4,$5,$6,$7)",
            jogador.id, it["id"], it["nome"], it["tipo"], it["raridade"], it["emoji"], it["desc"])
    await interaction.followup.send(f"Dado {it['emoji']} **{it['nome']}** x{qtd} para {jogador.mention}!", ephemeral=True)


# ─── /set-vida ───────────────────────────────────────────────────

@bot.tree.command(name="set-vida", description="[ADMIN] Define o HP de um jogador")
@app_commands.describe(jogador="Jogador alvo", quantidade="HP a definir (0 = HP max)")
@app_commands.checks.has_permissions(administrator=True)
async def set_vida(interaction: discord.Interaction, jogador: discord.Member, quantidade: int = 0):
    await interaction.response.defer(ephemeral=True)
    p = await get_personagem(jogador.id)
    if not p:
        await interaction.followup.send(f"{jogador.display_name} nao tem personagem!", ephemeral=True); return
    novo_hp = p["hp_max"] if quantidade <= 0 else min(quantidade, p["hp_max"])
    pool_db = await get_pool()
    async with pool_db.acquire() as conn:
        await conn.execute("UPDATE personagens SET hp_atual=$1 WHERE user_id=$2", novo_hp, jogador.id)
    await interaction.followup.send(f"HP de {jogador.display_name} definido para **{novo_hp}/{p['hp_max']}** ❤️", ephemeral=True)


# ─── /set-mana ───────────────────────────────────────────────────

@bot.tree.command(name="set-mana", description="[ADMIN] Define a mana de um jogador")
@app_commands.describe(jogador="Jogador alvo", quantidade="Mana a definir (0 = mana max)")
@app_commands.checks.has_permissions(administrator=True)
async def set_mana(interaction: discord.Interaction, jogador: discord.Member, quantidade: int = 0):
    await interaction.response.defer(ephemeral=True)
    p = await get_personagem(jogador.id)
    if not p:
        await interaction.followup.send(f"{jogador.display_name} nao tem personagem!", ephemeral=True); return
    nova_mana = p["mana_max"] if quantidade <= 0 else min(quantidade, p["mana_max"])
    pool_db = await get_pool()
    async with pool_db.acquire() as conn:
        await conn.execute("UPDATE personagens SET mana_atual=$1 WHERE user_id=$2", nova_mana, jogador.id)
    await interaction.followup.send(f"Mana de {jogador.display_name} definida para **{nova_mana}/{p['mana_max']}** 💙", ephemeral=True)


# ─── /set-moedas ─────────────────────────────────────────────────

@bot.tree.command(name="set-moedas", description="[ADMIN] Define ou adiciona moedas")
@app_commands.describe(jogador="Jogador alvo", quantidade="Quantidade", modo="definir ou adicionar")
@app_commands.choices(modo=[
    app_commands.Choice(name="Adicionar", value="adicionar"),
    app_commands.Choice(name="Definir",   value="definir"),
])
@app_commands.checks.has_permissions(administrator=True)
async def set_moedas(interaction: discord.Interaction, jogador: discord.Member, quantidade: int, modo: str = "adicionar"):
    await interaction.response.defer(ephemeral=True)
    if not await get_personagem(jogador.id):
        await interaction.followup.send(f"{jogador.display_name} nao tem personagem!", ephemeral=True); return
    pool_db = await get_pool()
    async with pool_db.acquire() as conn:
        if modo == "definir": await conn.execute("UPDATE personagens SET moedas=$1 WHERE user_id=$2", quantidade, jogador.id)
        else: await conn.execute("UPDATE personagens SET moedas=moedas+$1 WHERE user_id=$2", quantidade, jogador.id)
    await interaction.followup.send(f"Moedas de {jogador.display_name} atualizadas!", ephemeral=True)

# ─── /set-nivel ──────────────────────────────────────────────────

@bot.tree.command(name="set-nivel", description="[ADMIN] Define o nivel de um jogador")
@app_commands.describe(jogador="Jogador alvo", nivel="Nivel (1-100)")
@app_commands.checks.has_permissions(administrator=True)
async def set_nivel(interaction: discord.Interaction, jogador: discord.Member, nivel: int):
    await interaction.response.defer(ephemeral=True)
    if nivel < 1 or nivel > 100:
        await interaction.followup.send("Nivel deve ser entre 1 e 100!", ephemeral=True); return
    p = await get_personagem(jogador.id)
    if not p:
        await interaction.followup.send(f"{jogador.display_name} nao tem personagem!", ephemeral=True); return
    nd = nivel - p["nivel"]
    hp_n = max(50, p["hp_max"]+nd*5); atk_n = max(5, p["ataque"]+nd*2); dfs_n = max(3, p["defesa"]+nd*1)
    mana_n = calcular_mana_max(p["classe_id"], nivel, p["poder_valor"], p["destino_id"])
    pool_db = await get_pool()
    async with pool_db.acquire() as conn:
        await conn.execute("UPDATE personagens SET nivel=$1,xp=0,hp_max=$2,hp_atual=$3,ataque=$4,defesa=$5,mana_max=$6,mana_atual=$7 WHERE user_id=$8",
            nivel, hp_n, hp_n, atk_n, dfs_n, mana_n, mana_n, jogador.id)
        from catalogo import SKILLS_COMPLETAS
        for sk in SKILLS_COMPLETAS.get(p["classe_id"], []):
            if sk["nivel"] <= nivel:
                await conn.execute("INSERT INTO skills_desbloqueadas(user_id,skill_id) VALUES($1,$2) ON CONFLICT DO NOTHING", jogador.id, sk["id"])
    guild = interaction.guild
    if guild:
        member = guild.get_member(jogador.id)
        if member: await atualizar_todos_cargos(guild, member, nivel)
    rank_o = get_rank(nivel)
    await interaction.followup.send(f"{jogador.mention} agora e Nivel {nivel} — {rank_o['emoji']} Rank {rank_o['rank']}!", ephemeral=True)

# ─── /set-giros ──────────────────────────────────────────────────

@bot.tree.command(name="set-giros", description="[ADMIN] Da fichas de roleta a um jogador")
@app_commands.describe(jogador="Jogador alvo")
@app_commands.checks.has_permissions(administrator=True)
async def set_giros(interaction: discord.Interaction, jogador: discord.Member):
    await cmd_set_giros(interaction, jogador)

# ─── /deletar_personagem ─────────────────────────────────────────

@bot.tree.command(name="deletar_personagem", description="Deleta seu personagem permanentemente")
async def deletar_personagem(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    p = await get_personagem(interaction.user.id)
    if not p:
        await interaction.followup.send("Voce nao tem personagem!", ephemeral=True); return
    class ConfView(discord.ui.View):
        def __init__(self): super().__init__(timeout=30); self.ok = None
        @discord.ui.button(label="Confirmar delecao", style=discord.ButtonStyle.danger)
        async def sim(self, inter, b):
            if inter.user.id != interaction.user.id: return
            self.ok = True; await inter.response.defer(); self.stop()
        @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.secondary)
        async def nao(self, inter, b):
            self.ok = False; await inter.response.defer(); self.stop()
    v = ConfView()
    await interaction.followup.send("ATENCAO: Isso apaga seu personagem! Confirma?", view=v, ephemeral=True)
    await v.wait()
    if not v.ok: return
    pool_db = await get_pool()
    async with pool_db.acquire() as conn:
        for t in ["skills_equipadas","skills_desbloqueadas","inventario","missoes_diarias","conquistas","giros"]:
            try: await conn.execute(f"DELETE FROM {t} WHERE user_id=$1", interaction.user.id)
            except: pass
        await conn.execute("DELETE FROM personagens WHERE user_id=$1", interaction.user.id)
    await interaction.followup.send("Personagem deletado. Use /criar_personagem para recomecar.", ephemeral=True)


# ─── /criar-evento ───────────────────────────────────────────────

@bot.tree.command(name="criar-evento", description="[ADMIN] Cria um novo evento no servidor")
@app_commands.describe(
    tipo="Tipo do evento",
    premio_tipo="Tipo de premio",
    premio_valor="Valor do premio (moedas: 5000 | ficha: 3 | cargo: Nome do Cargo | classe: dracomante | item: id|nome|tipo|raridade|emoji|desc)",
    canal="Canal onde o evento sera anunciado"
)
@app_commands.choices(tipo=[
    app_commands.Choice(name="Torneio de Batalha",  value="batalha"),
    app_commands.Choice(name="Corrida de Dungeon",  value="dungeon"),
    app_commands.Choice(name="Coleta de Materiais", value="coleta"),
    app_commands.Choice(name="Corrida de Nivel",    value="nivel"),
    app_commands.Choice(name="Evento Livre",        value="livre"),
])
@app_commands.choices(premio_tipo=[
    app_commands.Choice(name="Moedas",           value="moedas"),
    app_commands.Choice(name="XP",               value="xp"),
    app_commands.Choice(name="Fichas de Roleta", value="ficha"),
    app_commands.Choice(name="Item especifico",  value="item"),
    app_commands.Choice(name="Cargo exclusivo",  value="cargo"),
    app_commands.Choice(name="Classe especial",  value="classe"),
])
@app_commands.checks.has_permissions(administrator=True)
async def criar_evento(interaction: discord.Interaction, tipo: str, premio_tipo: str, premio_valor: str, canal: discord.TextChannel):
    await cmd_criar_evento(interaction, tipo, premio_tipo, premio_valor, canal)


# ─── /eventos ────────────────────────────────────────────────────

@bot.tree.command(name="eventos", description="Lista os eventos ativos no servidor")
async def eventos(interaction: discord.Interaction):
    await cmd_eventos(interaction)


# ─── /evento-info ────────────────────────────────────────────────

@bot.tree.command(name="evento-info", description="Detalhes de um evento e ranking de participantes")
@app_commands.describe(evento_id="ID do evento (0 = evento ativo atual)")
async def evento_info(interaction: discord.Interaction, evento_id: int = 0):
    await cmd_evento_info(interaction, evento_id)


# ─── /encerrar-evento ────────────────────────────────────────────

@bot.tree.command(name="encerrar-evento", description="[ADMIN] Encerra evento e entrega premio ao 1o lugar")
@app_commands.describe(evento_id="ID do evento a encerrar")
@app_commands.checks.has_permissions(administrator=True)
async def encerrar_evento(interaction: discord.Interaction, evento_id: int):
    await cmd_encerrar_evento(interaction, evento_id)


# ─── /add-pontos ─────────────────────────────────────────────────

@bot.tree.command(name="add-pontos", description="[ADMIN] Adiciona pontos a um participante do evento")
@app_commands.describe(jogador="Jogador alvo", pontos="Pontos a adicionar", evento_id="ID do evento (0 = atual)")
@app_commands.checks.has_permissions(administrator=True)
async def add_pontos(interaction: discord.Interaction, jogador: discord.Member, pontos: int, evento_id: int = 0):
    await cmd_add_pontos(interaction, jogador, pontos, evento_id)



# ─── /anunciar ───────────────────────────────────────────────────

@bot.tree.command(name="anunciar", description="[ADMIN] Cria e envia um anuncio formatado")
@app_commands.describe(
    canal="Canal onde o anuncio sera enviado",
    cor="Cor do embed",
    ping="Cargo a pingar (opcional)"
)
@app_commands.choices(cor=[
    app_commands.Choice(name="Dourado", value="dourado"),
    app_commands.Choice(name="Roxo", value="roxo"),
    app_commands.Choice(name="Verde", value="verde"),
    app_commands.Choice(name="Azul", value="azul"),
    app_commands.Choice(name="Vermelho", value="vermelho"),
    app_commands.Choice(name="Laranja", value="laranja"),
    app_commands.Choice(name="Cinza", value="cinza"),
    app_commands.Choice(name="Preto", value="preto"),
])
@app_commands.checks.has_permissions(administrator=True)
async def anunciar(interaction: discord.Interaction, canal: discord.TextChannel,
                   cor: str = "roxo", ping: discord.Role = None):
    await cmd_anunciar(interaction, canal, cor, ping)


# ─── /anunciar-evento ────────────────────────────────────────────

@bot.tree.command(name="anunciar-evento", description="[ADMIN] Anuncia um evento com data e premio")
@app_commands.describe(
    canal="Canal do anuncio",
    ping="Cargo a pingar (opcional)"
)
@app_commands.checks.has_permissions(administrator=True)
async def anunciar_evento(interaction: discord.Interaction, canal: discord.TextChannel,
                          ping: discord.Role = None):
    await cmd_anunciar_evento(interaction, canal, ping)


# ─── /agendar-anuncio ────────────────────────────────────────────

@bot.tree.command(name="agendar-anuncio", description="[ADMIN] Agenda um anuncio para enviar depois")
@app_commands.describe(
    canal="Canal do anuncio",
    cor="Cor do embed"
)
@app_commands.choices(cor=[
    app_commands.Choice(name="Dourado", value="dourado"),
    app_commands.Choice(name="Roxo", value="roxo"),
    app_commands.Choice(name="Verde", value="verde"),
    app_commands.Choice(name="Azul", value="azul"),
    app_commands.Choice(name="Vermelho", value="vermelho"),
    app_commands.Choice(name="Laranja", value="laranja"),
    app_commands.Choice(name="Cinza", value="cinza"),
    app_commands.Choice(name="Preto", value="preto"),
])
@app_commands.checks.has_permissions(administrator=True)
async def agendar_anuncio(interaction: discord.Interaction, canal: discord.TextChannel,
                          cor: str = "dourado"):
    await cmd_agendar_anuncio(interaction, canal, cor)



# ─── /torneio-criar ──────────────────────────────────────────────

@bot.tree.command(name="torneio-criar", description="[ADMIN] Cria um torneio PvP")
@app_commands.checks.has_permissions(administrator=True)
async def torneio_criar(interaction: discord.Interaction):
    await cmd_torneio_criar(interaction)


# ─── /torneio-status ─────────────────────────────────────────────

@bot.tree.command(name="torneio-status", description="Veja as chaves e status de um torneio")
@app_commands.describe(torneio_id="ID do torneio")
async def torneio_status(interaction: discord.Interaction, torneio_id: int):
    await cmd_torneio_status(interaction, torneio_id)


# ─── /torneio-lutar ──────────────────────────────────────────────

@bot.tree.command(name="torneio-lutar", description="[ADMIN] Inicia uma luta do torneio")
@app_commands.describe(torneio_id="ID do torneio", jogador1="Jogador 1", jogador2="Jogador 2")
@app_commands.checks.has_permissions(administrator=True)
async def torneio_lutar(interaction: discord.Interaction, torneio_id: int,
                         jogador1: discord.Member, jogador2: discord.Member):
    await cmd_torneio_lutar(interaction, torneio_id, jogador1, jogador2)


# ─── /torneio-fechar-inscricoes ──────────────────────────────────

@bot.tree.command(name="torneio-fechar-inscricoes", description="[ADMIN] Fecha inscricoes e monta as chaves")
@app_commands.describe(torneio_id="ID do torneio")
@app_commands.checks.has_permissions(administrator=True)
async def torneio_fechar_inscricoes(interaction: discord.Interaction, torneio_id: int):
    await cmd_torneio_fechar_inscricoes(interaction, torneio_id)


# ─── /torneio-cancelar ───────────────────────────────────────────

@bot.tree.command(name="torneio-cancelar", description="[ADMIN] Cancela torneio e devolve inscricoes")
@app_commands.describe(torneio_id="ID do torneio")
@app_commands.checks.has_permissions(administrator=True)
async def torneio_cancelar(interaction: discord.Interaction, torneio_id: int):
    await cmd_torneio_cancelar(interaction, torneio_id)


# ─── /dungeon-evento-criar ───────────────────────────────────────

@bot.tree.command(name="dungeon-evento-criar", description="[ADMIN] Cria uma dungeon de evento customizada")
@app_commands.checks.has_permissions(administrator=True)
async def dungeon_evento_criar(interaction: discord.Interaction):
    await interaction.response.send_modal(DungeonEventoCriarModal(interaction.guild))


# ─── /dungeon-evento-andar ───────────────────────────────────────

@bot.tree.command(name="dungeon-evento-andar", description="[ADMIN] Adiciona um andar a dungeon de evento")
@app_commands.describe(dungeon_id="ID da dungeon")
@app_commands.checks.has_permissions(administrator=True)
async def dungeon_evento_andar(interaction: discord.Interaction, dungeon_id: int):
    await interaction.response.send_modal(AdicionarAndarModal(dungeon_id))


# ─── /dungeon-evento-ativar ──────────────────────────────────────

@bot.tree.command(name="dungeon-evento-ativar", description="[ADMIN] Ativa e anuncia a dungeon de evento")
@app_commands.describe(dungeon_id="ID da dungeon")
@app_commands.checks.has_permissions(administrator=True)
async def dungeon_evento_ativar(interaction: discord.Interaction, dungeon_id: int):
    await cmd_dungeon_evento_ativar(interaction, dungeon_id)


# ─── /dungeon-evento-info ────────────────────────────────────────

@bot.tree.command(name="dungeon-evento-info", description="Veja detalhes e andares de uma dungeon de evento")
@app_commands.describe(dungeon_id="ID da dungeon")
async def dungeon_evento_info(interaction: discord.Interaction, dungeon_id: int):
    await cmd_dungeon_evento_info(interaction, dungeon_id)


# ─── /dungeon-evento-fechar ──────────────────────────────────────

@bot.tree.command(name="dungeon-evento-fechar", description="[ADMIN] Fecha uma dungeon de evento")
@app_commands.describe(dungeon_id="ID da dungeon")
@app_commands.checks.has_permissions(administrator=True)
async def dungeon_evento_fechar(interaction: discord.Interaction, dungeon_id: int):
    await cmd_dungeon_evento_fechar(interaction, dungeon_id)


# ─── /ajuda ──────────────────────────────────────────────────────

@bot.tree.command(name="ajuda", description="Lista todos os comandos do RPG")
async def ajuda(interaction: discord.Interaction):
    embed = discord.Embed(title="Comandos — Villa Eldoria RPG", color=0x7F77DD)
    embed.add_field(name="Personagem", value="`/criar_personagem` `/perfil` `/skills` `/setup` `/deletar_personagem`", inline=False)
    embed.add_field(name="Inventario", value="`/inventario` `/equipar` `/jogar-fora` `/dar`", inline=False)
    embed.add_field(name="Batalha",    value="`/treinar` `/desafiar` `/dungeon`", inline=False)
    embed.add_field(name="Economia",   value="`/loja` `/ferreiro` `/hospital` `/mercado` `/mercador`", inline=False)
    embed.add_field(name="Progresso",  value="`/missoes` `/conquistas` `/ranking` `/girar`", inline=False)
    embed.add_field(name="Admin",      value="`/set-item` `/set-moedas` `/set-nivel` `/set-giros` `/set-vida` `/set-mana`", inline=False)
    embed.add_field(name="Eventos",    value="`/criar-evento` `/eventos` `/evento-info` `/encerrar-evento` `/add-pontos`", inline=False)
    embed.add_field(name="Anuncios",   value="`/anunciar` `/anunciar-evento` `/agendar-anuncio`", inline=False)
    embed.add_field(name="Torneio",    value="`/torneio-criar` `/torneio-status` `/torneio-lutar` `/torneio-fechar-inscricoes` `/torneio-cancelar`", inline=False)
    embed.add_field(name="Dungeon Evento", value="`/dungeon-evento-criar` `/dungeon-evento-andar` `/dungeon-evento-ativar` `/dungeon-evento-info` `/dungeon-evento-fechar`", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ─── SYNC MANUAL ─────────────────────────────────────────────────

@bot.command(name="sync")
async def sync_cmd(ctx):
    try:
        guild_id = int(os.getenv("GUILD_ID","0"))
        total = 0
        if guild_id:
            guild_obj = discord.Object(id=guild_id)
            bot.tree.copy_global_to(guild=guild_obj)
            s = await bot.tree.sync(guild=guild_obj)
            total += len(s)
        s2 = await bot.tree.sync()
        total += len(s2)
        await ctx.send(f"✅ {total} comandos sincronizados!")
    except Exception as e:
        await ctx.send(f"❌ Erro: {e}")

# ─── EVENTOS ─────────────────────────────────────────────────────

@bot.event
async def on_ready():
    print(f"Bot: {bot.user}")
    cmds_no_tree = len(bot.tree.get_commands())
    print(f"Comandos no tree: {cmds_no_tree}")

    # DB
    try:
        await init_db(); await init_db_batalha(); await init_db_hospital()
        await init_db_missoes(); await init_conquistas()
        print("DB OK!")
    except Exception as e:
        print(f"ERRO DB: {e}")

    # Sync — global primeiro para garantir todos os comandos
    try:
        global_synced = await bot.tree.sync()
        print(f"Comandos globais: {len(global_synced)}")
        for c in global_synced: print(f"  /{c.name}")
    except Exception as e:
        print(f"ERRO sync global: {e}")

    # Sync no servidor para efeito imediato
    try:
        guild_id = int(os.getenv("GUILD_ID","0"))
        if guild_id:
            guild_obj = discord.Object(id=guild_id)
            bot.tree.copy_global_to(guild=guild_obj)
            guild_synced = await bot.tree.sync(guild=guild_obj)
            print(f"Comandos no servidor: {len(guild_synced)}")
    except Exception as e:
        print(f"ERRO sync servidor: {e}")

    print("Bot pronto!")

@bot.event
async def on_member_join(member: discord.Member):
    cargo = discord.utils.get(member.guild.roles, name="🌱 Recem-chegado")
    if cargo:
        try: await member.add_roles(cargo)
        except: pass

# ─── MAIN ────────────────────────────────────────────────────────

if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN","")
    if not token:
        try:
            with open("config.txt") as f:
                for l in f:
                    if l.startswith("DISCORD_TOKEN="):
                        token = l.split("=",1)[1].strip()
        except: pass
    if not token:
        print("ERRO: Token nao encontrado."); exit(1)
    bot.run(token)
