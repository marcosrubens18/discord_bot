# -*- coding: utf-8 -*-
import sys, io, os, random, asyncio
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

import discord
from discord import app_commands
from discord.ext import commands

from db import get_pool, init_db
from catalogo import get_rank, CARGOS_RANK, calcular_mana_max, get_armas_classe, get_armaduras_classe
from setup_cmd import cmd_setup
from dungeon import cmd_dungeon
from hospital import (
    cmd_hospital, cmd_girar, cmd_set_giros, init_db_hospital,
    COR_RAR, EMOJI_FICHA
)
from batalha import (
    rodar_pvp, rodar_treino, MONSTROS, SKILLS_POR_CLASSE,
    get_skills_eq, get_skills_desbloq, GerenciarSkillsView,
    AceitarDueloView, EscolherArenaView, init_db_batalha,
    ARENAS, LOJA_ITENS, RECEITAS, POCOES
)
from missoes import cmd_missoes, cmd_ranking, init_db_missoes, atualizar_progresso

# ─── CONFIG ──────────────────────────────────────────────────────

CLASSES = [
    {"id":"guerreiro",  "nome":"Guerreiro",  "emoji":"🗡️","raridade":"Comum",   "peso":30},
    {"id":"arqueiro",   "nome":"Arqueiro",   "emoji":"🏹","raridade":"Comum",   "peso":25},
    {"id":"mago",       "nome":"Mago",       "emoji":"🔮","raridade":"Comum",   "peso":20},
    {"id":"paladino",   "nome":"Paladino",   "emoji":"⚡","raridade":"Incomum", "peso":12},
    {"id":"necromante", "nome":"Necromante", "emoji":"🌑","raridade":"Raro",    "peso":8},
    {"id":"dracomante", "nome":"Dracomante", "emoji":"🐉","raridade":"Lendario","peso":2},
    {"id":"arcano",     "nome":"Arcano",     "emoji":"✨","raridade":"Epico",   "peso":3},
]
PODERES = [
    {"id":"fraquinho","nome":"Fraquinho",     "emoji":"💀","valor":10},
    {"id":"mediano",  "nome":"Mediano",       "emoji":"⚖️","valor":18},
    {"id":"acima",    "nome":"Acima da media","emoji":"📈","valor":26},
    {"id":"forte",    "nome":"Forte",         "emoji":"💪","valor":35},
    {"id":"epico",    "nome":"Epico",         "emoji":"⚡","valor":48},
    {"id":"absurdo",  "nome":"Absurdo",       "emoji":"🔥","valor":65},
]
PESOS_PODER = [20,30,25,15,7,3]
DESTINOS = [
    {"id":"equilibrado","nome":"Equilibrado",  "emoji":"⚖️","desc":"Stats balanceados"},
    {"id":"prodigio",   "nome":"Prodigio",     "emoji":"🔥","desc":"+25% ataque, -10% defesa"},
    {"id":"maldito",    "nome":"Maldito",      "emoji":"💀","desc":"Fraco mas evolui 2x mais rapido"},
    {"id":"guardiao",   "nome":"Guardiao",     "emoji":"🛡️","desc":"+25% defesa, -10% ataque"},
    {"id":"abencado",   "nome":"Abencado",     "emoji":"🌟","desc":"+10% em todos os stats"},
    {"id":"amaldicoado","nome":"Amaldicado",   "emoji":"☠️","desc":"Stats aleatorios a cada nivel"},
    {"id":"filho_caos", "nome":"Filho do Caos","emoji":"🌀","desc":"Efeito aleatorio em batalha"},
]
ITEM_INICIAL = {
    "guerreiro":  ("espada_ferro", "Espada de Ferro","arma","Comum",   "⚔️","Uma espada basica"),
    "mago":       ("cajado_pinho", "Cajado de Pinho","arma","Comum",   "🪄","Um cajado simples"),
    "arqueiro":   ("arco_madeira", "Arco de Madeira","arma","Comum",   "🏹","Um arco simples"),
    "paladino":   ("maca_sagrada", "Maca Sagrada",   "arma","Incomum", "⚡","Uma maca abencada"),
    "necromante": ("cajado_osso",  "Cajado de Osso", "arma","Raro",    "💀","Feito de ossos"),
    "dracomante": ("garra_dragao", "Garra de Dragao","arma","Epico",   "🐉","Garra de dragao"),
    "arcano":     ("orbe_arcano",  "Orbe Arcano",    "arma","Epico",   "✨","Orbe arcano"),
}
EMOJI_CLASSE = {"guerreiro":"🗡️","mago":"🔮","arqueiro":"🏹","paladino":"⚡","necromante":"🌑","dracomante":"🐉","arcano":"✨"}

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ─── DB HELPERS ──────────────────────────────────────────────────

async def get_personagem(user_id):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM personagens WHERE user_id=$1", user_id)

async def get_inventario(user_id):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch(
            "SELECT * FROM inventario WHERE user_id=$1 ORDER BY equipado DESC, tipo, nome",
            user_id
        )

# ─── HELPERS ─────────────────────────────────────────────────────

def get_classe(cid):
    return next((c for c in CLASSES if c["id"] == cid), None)

def get_poder(pid):
    return next((p for p in PODERES if p["id"] == pid), None)

def get_destino(did):
    return next((d for d in DESTINOS if d["id"] == did), None)

def calcular_stats(poder_valor, destino_id, nivel):
    hp  = 80 + poder_valor*3 + nivel*5
    atk = 8  + poder_valor//2 + nivel*2
    dfs = 5  + poder_valor//3 + nivel*1
    if destino_id == "prodigio":    atk = int(atk*1.25); dfs = int(dfs*0.9)
    elif destino_id == "guardiao":  dfs = int(dfs*1.25); atk = int(atk*0.9)
    elif destino_id == "abencado":  hp=int(hp*1.1); atk=int(atk*1.1); dfs=int(dfs*1.1)
    elif destino_id == "maldito":   atk=int(atk*0.7); dfs=int(dfs*0.7)
    elif destino_id == "amaldicoado": atk=random.randint(5,atk*2); dfs=random.randint(3,dfs*2)
    return hp, atk, dfs

def xp_needed(nivel):
    return 100 + (nivel-1)*50

def sortear_peso(lista, pesos):
    total = sum(pesos)
    r = random.random() * total
    for i, item in enumerate(lista):
        r -= pesos[i]
        if r <= 0: return item
    return lista[-1]

# ─── CARGO DE NIVEL ──────────────────────────────────────────────

async def atualizar_cargo_nivel(guild, member, nivel):
    """Atualiza cargo de nivel (Aventureiro/Veterano/Elite/Mestre)."""
    if not guild or not member: return
    CARGOS_NIVEL = [
        (50, "💎 Mestre"),
        (30, "🥇 Elite"),
        (15, "🥈 Veterano"),
        (5,  "🥉 Aventureiro"),
    ]
    for _, nome in CARGOS_NIVEL:
        cargo = discord.utils.get(guild.roles, name=nome)
        if cargo and cargo in member.roles:
            try: await member.remove_roles(cargo)
            except: pass
    for nivel_min, nome in CARGOS_NIVEL:
        if nivel >= nivel_min:
            cargo = discord.utils.get(guild.roles, name=nome)
            if cargo:
                try: await member.add_roles(cargo)
                except: pass
            break

async def atualizar_cargo_rank(guild, member, rank_str):
    """Atualiza cargo de rank (F ao SS)."""
    if not guild or not member: return
    todos_ranks = ["🟫 Rank F","🟩 Rank E","🟦 Rank D","🟨 Rank C","🟧 Rank B","🟥 Rank A","⭐ Rank S","💎 Rank SS"]
    for nome in todos_ranks:
        cargo = discord.utils.get(guild.roles, name=nome)
        if cargo and cargo in member.roles:
            try: await member.remove_roles(cargo)
            except: pass
    nome_novo = CARGOS_RANK.get(rank_str)
    if nome_novo:
        cargo = discord.utils.get(guild.roles, name=nome_novo)
        if cargo:
            try: await member.add_roles(cargo)
            except: pass

# ─── CANAL PRIVADO ───────────────────────────────────────────────

async def criar_canal_privado(guild, member, nome_jogador, classe):
    if not member: return
    import re
    nome_canal = re.sub(r'[^a-z0-9-]', '', nome_jogador.lower().replace(' ', '-'))[:32]
    canal_existente = discord.utils.get(guild.text_channels, name=nome_canal)
    if canal_existente: return canal_existente
    categoria = None
    for nome_cat in ["👤 ─── MEU PERFIL ───", "MEU PERFIL", "Meu Perfil"]:
        categoria = discord.utils.get(guild.categories, name=nome_cat)
        if categoria: break
    everyone = guild.default_role
    overwrites = {
        everyone: discord.PermissionOverwrite(read_messages=False),
        member:   discord.PermissionOverwrite(read_messages=True, send_messages=True),
    }
    for cargo_nome in ["🔧 Staff", "⚙️ Admin"]:
        cargo = discord.utils.get(guild.roles, name=cargo_nome)
        if cargo:
            overwrites[cargo] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
    try:
        canal = await guild.create_text_channel(nome_canal, category=categoria, overwrites=overwrites)
        emoji_j = EMOJI_CLASSE.get(classe["id"], "⚔️")
        embed = discord.Embed(
            title=f"{emoji_j} Bem-vindo ao seu espaco privado, {nome_jogador}!",
            description="Este canal e so seu.\n\n`/perfil` `/inventario` `/skills` `/setup` `/hospital` `/girar` `/deletar_personagem`",
            color=0x7F77DD
        )
        await canal.send(content=member.mention, embed=embed)
        return canal
    except Exception as e:
        print(f"Erro canal privado: {e}")
        return None

# ─── /criar_personagem ───────────────────────────────────────────

@bot.tree.command(name="criar_personagem", description="Cria seu personagem girando as roletas!")
async def criar_personagem(interaction: discord.Interaction):
    await interaction.response.defer()
    uid = interaction.user.id
    if await get_personagem(uid):
        await interaction.followup.send("Voce ja tem personagem! Use `/perfil`.", ephemeral=True)
        return

    embed0 = discord.Embed(title="As roletas do destino estao girando...", description=f"{interaction.user.mention}, prepare-se!", color=0x7F77DD)
    await interaction.followup.send(embed=embed0)
    await asyncio.sleep(1)

    pesos_cls = [c["peso"] for c in CLASSES]
    classe = sortear_peso(CLASSES, pesos_cls)
    e1 = discord.Embed(title="Roleta 1 — Classe", color=COR_RAR.get(classe["raridade"], 0x888780))
    e1.description = "Girando..."
    m1 = await interaction.followup.send(embed=e1, wait=True)
    for _ in range(6):
        rc = random.choice(CLASSES)
        e1.description = f"**{rc['emoji']} {rc['nome']}**"
        await m1.edit(embed=e1); await asyncio.sleep(0.3)
    e1.description = f"**{classe['emoji']} {classe['nome']} — {classe['raridade']}**"
    await m1.edit(embed=e1); await asyncio.sleep(0.5)

    poder = sortear_peso(PODERES, PESOS_PODER)
    e2 = discord.Embed(title="Roleta 2 — Poder base", color=0xD85A30)
    e2.description = "Girando..."
    m2 = await interaction.followup.send(embed=e2, wait=True)
    for _ in range(6):
        rp = random.choice(PODERES)
        e2.description = f"**{rp['emoji']} {rp['nome']} ({rp['valor']})**"
        await m2.edit(embed=e2); await asyncio.sleep(0.3)
    e2.description = f"**{poder['emoji']} {poder['nome']} — Poder {poder['valor']}**"
    await m2.edit(embed=e2); await asyncio.sleep(0.5)

    destino = random.choice(DESTINOS)
    e3 = discord.Embed(title="Roleta 3 — Destino", color=0xE4AF3C)
    e3.description = "Girando..."
    m3 = await interaction.followup.send(embed=e3, wait=True)
    for _ in range(6):
        rd = random.choice(DESTINOS)
        e3.description = f"**{rd['emoji']} {rd['nome']}**"
        await m3.edit(embed=e3); await asyncio.sleep(0.3)
    e3.description = f"**{destino['emoji']} {destino['nome']} — {destino['desc']}**"
    await m3.edit(embed=e3); await asyncio.sleep(0.5)

    skills_cls = SKILLS_POR_CLASSE.get(classe["id"], [])
    todas_sk = [s for cls in SKILLS_POR_CLASSE.values() for s in cls]
    disponiveis = list(skills_cls); random.shuffle(disponiveis)
    skills_sorteadas = disponiveis[:4]
    while len(skills_sorteadas) < 4 and disponiveis:
        skills_sorteadas.append(random.choice(disponiveis))

    for i, sk_final in enumerate(skills_sorteadas):
        e_sk = discord.Embed(title=f"Roleta {4+i} — Skill {i+1}", color=0x1D9E75)
        e_sk.description = "Girando..."
        m_sk = await interaction.followup.send(embed=e_sk, wait=True)
        for _ in range(6):
            rs = random.choice(todas_sk)
            e_sk.description = f"**{rs['emoji']} {rs['nome']}**"
            await m_sk.edit(embed=e_sk); await asyncio.sleep(0.25)
        e_sk.description = f"**{sk_final['emoji']} {sk_final['nome']}** — {sk_final['desc']}"
        await m_sk.edit(embed=e_sk); await asyncio.sleep(0.4)

    hp, atk, dfs = calcular_stats(poder["valor"], destino["id"], 1)
    nome = interaction.user.display_name
    it = ITEM_INICIAL.get(classe["id"], ITEM_INICIAL["guerreiro"])

    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO personagens
            (user_id,nome,classe_id,raridade,poder_id,poder_valor,destino_id,skill_id,
             nivel,xp,hp_max,hp_atual,ataque,defesa,mana_max,mana_atual,moedas)
            VALUES($1,$2,$3,$4,$5,$6,$7,$8,1,0,$9,$10,$11,$12,100,100,50)
        """, uid, nome, classe["id"], classe["raridade"], poder["id"], poder["valor"],
            destino["id"], skills_sorteadas[0]["id"] if skills_sorteadas else "",
            hp, hp, atk, dfs)
        for i, sk in enumerate(skills_sorteadas):
            await conn.execute(
                "INSERT INTO skills_desbloqueadas(user_id,skill_id) VALUES($1,$2) ON CONFLICT DO NOTHING",
                uid, sk["id"]
            )
            await conn.execute(
                "INSERT INTO skills_equipadas(user_id,skill_id,slot) VALUES($1,$2,$3) ON CONFLICT(user_id,slot) DO UPDATE SET skill_id=EXCLUDED.skill_id",
                uid, sk["id"], i
            )
        await conn.execute("""
            INSERT INTO inventario(user_id,item_id,nome,tipo,raridade,emoji,descricao,equipado)
            VALUES($1,$2,$3,$4,$5,$6,$7,1)
        """, uid, it[0], it[1], it[2], it[3], it[4], it[5])

    cor = COR_RAR.get(classe["raridade"], 0x888780)
    efinal = discord.Embed(title=f"{classe['emoji']} {nome} entrou na cidade!", color=cor)
    if classe["raridade"] in ("Lendario", "Epico"):
        efinal.description = f"CLASSE {classe['raridade'].upper()}!"
    efinal.add_field(name="Classe",  value=f"{classe['emoji']} {classe['nome']} ({classe['raridade']})", inline=True)
    efinal.add_field(name="Poder",   value=f"{poder['emoji']} {poder['nome']} ({poder['valor']})", inline=True)
    efinal.add_field(name="Destino", value=f"{destino['emoji']} {destino['nome']}", inline=True)
    sk_nomes = " | ".join([f"{s['emoji']} {s['nome']}" for s in skills_sorteadas])
    efinal.add_field(name="Skills",  value=sk_nomes, inline=False)
    efinal.add_field(name="HP",      value=str(hp),  inline=True)
    efinal.add_field(name="Ataque",  value=str(atk), inline=True)
    efinal.add_field(name="Defesa",  value=str(dfs), inline=True)
    efinal.add_field(name="Item",    value=f"{it[4]} {it[1]}", inline=True)
    efinal.set_footer(text="Use /setup para equipar e /perfil para ver sua ficha")
    await interaction.followup.send(embed=efinal)

    guild = interaction.guild
    if guild:
        member = guild.get_member(uid)
        if member:
            for cn in ["🏠 Morador da Vila", classe["nome"]]:
                cargo = discord.utils.get(guild.roles, name=cn)
                if cargo:
                    try: await member.add_roles(cargo)
                    except: pass
            for nome_recem in ["🌱 Recem-chegado", "Recem-chegado"]:
                recem = discord.utils.get(guild.roles, name=nome_recem)
                if recem and recem in member.roles:
                    try: await member.remove_roles(recem)
                    except: pass
        await criar_canal_privado(guild, member, nome, classe)

# ─── /perfil ─────────────────────────────────────────────────────

@bot.tree.command(name="perfil", description="Mostra a ficha do personagem")
@app_commands.describe(jogador="Ver perfil de outro jogador (opcional)")
async def perfil(interaction: discord.Interaction, jogador: discord.Member = None):
    await interaction.response.defer()
    alvo = jogador or interaction.user
    p = await get_personagem(alvo.id)
    if not p:
        msg = "Voce ainda nao criou um personagem! Use `/criar_personagem`." if alvo == interaction.user else f"{alvo.display_name} nao tem personagem."
        await interaction.followup.send(msg, ephemeral=True); return

    cls = get_classe(p["classe_id"]); pod = get_poder(p["poder_id"]); dst = get_destino(p["destino_id"])
    sks = await get_skills_desbloq(alvo.id); eq = await get_skills_eq(alvo.id)
    todas = SKILLS_POR_CLASSE.get(p["classe_id"], [])
    xp_cur = p["xp"]; xp_nxt = xp_needed(p["nivel"])
    pct = xp_cur / xp_nxt if xp_nxt > 0 else 0
    barra = "█" * int(pct*10) + "░" * (10-int(pct*10))

    rank_info = get_rank(p["nivel"])
    embed = discord.Embed(
        title=f"{cls['emoji'] if cls else '?'} {p['nome']}",
        description=(
            f"**Classe:** {cls['nome'] if cls else p['classe_id']} — *{p['raridade']}*\n"
            f"**Rank:** {rank_info['emoji']} {rank_info['rank']} — {rank_info['nome']}\n"
            f"**Destino:** {dst['emoji'] if dst else ''} {dst['nome'] if dst else p['destino_id']}\n"
            f"**Poder:** {pod['nome'] if pod else p['poder_id']} ({p['poder_valor']})"
        ),
        color=COR_RAR.get(p["raridade"], 0x888780)
    )
    embed.add_field(name="Nivel",    value=str(p["nivel"]), inline=True)
    embed.add_field(name="XP",       value=f"{xp_cur}/{xp_nxt}\n`{barra}`", inline=True)
    embed.add_field(name="\u200b",   value="\u200b", inline=True)
    embed.add_field(name="HP",       value=f"{p['hp_atual']}/{p['hp_max']}", inline=True)
    embed.add_field(name="Ataque",   value=str(p["ataque"]), inline=True)
    embed.add_field(name="Defesa",   value=str(p["defesa"]), inline=True)
    embed.add_field(name="Moedas",   value=f"{p['moedas']} 🪙", inline=True)
    embed.add_field(name="Vitorias", value=str(p["vitorias"]), inline=True)
    embed.add_field(name="Derrotas", value=str(p["derrotas"]), inline=True)

    atv  = [s for s in todas if s["id"] in sks]
    bloq = [s for s in todas if s["id"] not in sks]
    if atv:
        txt = "\n".join([f"{'🟢' if s['id'] in eq else '⚪'} {s['emoji']} **{s['nome']}** — {s['desc']}" for s in atv])
        embed.add_field(name="Skills (🟢=equipada)", value=txt, inline=False)
    if bloq:
        txt = "\n".join([f"🔒 {s['emoji']} {s['nome']} — Nv {s['nivel']}" for s in bloq])
        embed.add_field(name="Bloqueadas", value=txt, inline=False)

    embed.set_footer(text=f"ID: {alvo.id} • Use /setup para montar seu equipamento")
    await interaction.followup.send(embed=embed)

# ─── /inventario ─────────────────────────────────────────────────

@bot.tree.command(name="inventario", description="Mostra seu inventario")
@app_commands.describe(jogador="Ver inventario de outro jogador (opcional)")
async def inventario(interaction: discord.Interaction, jogador: discord.Member = None):
    await interaction.response.defer()
    alvo = jogador or interaction.user
    p = await get_personagem(alvo.id)
    if not p:
        await interaction.followup.send("Personagem nao encontrado!", ephemeral=True); return

    itens = await get_inventario(alvo.id)
    cls = get_classe(p["classe_id"])
    embed = discord.Embed(title=f"{cls['emoji'] if cls else '?'} Inventario de {p['nome']}", color=COR_RAR.get(p["raridade"], 0x888780))
    if not itens:
        embed.description = "*Inventario vazio.*"
    else:
        eq  = [i for i in itens if i["equipado"] == 1]
        neq = [i for i in itens if i["equipado"] == 0]
        if eq:
            txt = "\n".join([f"{i['emoji']} **{i['nome']}** [{i['raridade']}]\n_{i['descricao']}_" for i in eq])
            embed.add_field(name="Equipado", value=txt, inline=False)
        if neq:
            txt = "\n".join([f"{i['emoji']} **{i['nome']}** [{i['raridade']}] (x{i['quantidade']})" for i in neq])
            embed.add_field(name="Mochila", value=txt, inline=False)
    embed.add_field(name="Moedas", value=f"{p['moedas']} 🪙", inline=True)
    embed.set_footer(text="Use /setup para equipar itens")
    await interaction.followup.send(embed=embed)

# ─── /setup ──────────────────────────────────────────────────────

@bot.tree.command(name="setup", description="Monte seu setup completo")
async def setup(interaction: discord.Interaction):
    await cmd_setup(interaction)

# ─── /skills ─────────────────────────────────────────────────────

@bot.tree.command(name="skills", description="Veja e gerencie suas skills")
async def skills_cmd(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    p = await get_personagem(interaction.user.id)
    if not p:
        await interaction.followup.send("Crie seu personagem primeiro!", ephemeral=True); return

    desbloq_ids   = await get_skills_desbloq(interaction.user.id)
    equipadas_ids = await get_skills_eq(interaction.user.id)
    todas = SKILLS_POR_CLASSE.get(p["classe_id"], [])
    desbl = [s for s in todas if s["id"] in desbloq_ids]
    bloq  = [s for s in todas if s["id"] not in desbloq_ids]

    emoji_j = EMOJI_CLASSE.get(p["classe_id"], "⚔️")
    embed = discord.Embed(
        title=f"{emoji_j} Skills de {p['nome']} — Nivel {p['nivel']}",
        description=f"Voce pode equipar ate **4 skills**. Equipadas: **{len(equipadas_ids)}/4**",
        color=0x7F77DD
    )
    if desbl:
        txt = "\n".join([f"{'🟢' if s['id'] in equipadas_ids else '⚪'} {s['emoji']} **{s['nome']}** — {s['desc']} | 💙{s.get('mana',0)}" for s in desbl])
        embed.add_field(name="Desbloqueadas", value=txt, inline=False)
    if bloq:
        txt = "\n".join([f"🔒 {s['emoji']} {s['nome']} — Nivel {s['nivel']}" for s in bloq])
        embed.add_field(name="Bloqueadas", value=txt, inline=False)
    embed.set_footer(text="Dica: use /setup para equipar skills e itens de uma vez!")

    opcoes = [
        discord.SelectOption(
            label=f"{s['emoji']} {s['nome']}",
            value=s["id"],
            description=f"{s['desc']} | Mana: {s.get('mana',0)}"[:50],
            default=s["id"] in equipadas_ids
        ) for s in desbl
    ]
    if opcoes:
        sel = discord.ui.Select(placeholder="Escolha ate 4 skills...", min_values=1, max_values=min(4,len(opcoes)), options=opcoes)
        async def salvar_skills(inter: discord.Interaction):
            try: await inter.response.defer()
            except: pass
            selecionadas = inter.data["values"][:4]
            pool = await get_pool()
            async with pool.acquire() as conn:
                await conn.execute("DELETE FROM skills_equipadas WHERE user_id=$1", interaction.user.id)
                for slot, sid in enumerate(selecionadas):
                    await conn.execute(
                        "INSERT INTO skills_equipadas(user_id,skill_id,slot) VALUES($1,$2,$3) ON CONFLICT(user_id,slot) DO UPDATE SET skill_id=EXCLUDED.skill_id",
                        interaction.user.id, sid, slot
                    )
            nomes = [s["nome"] for s in desbl if s["id"] in selecionadas]
            await inter.followup.send(embed=discord.Embed(title="Skills atualizadas!", description="\n".join([f"• {n}" for n in nomes]), color=0x1D9E75), ephemeral=True)
        sel.callback = salvar_skills
        v = discord.ui.View(timeout=60); v.add_item(sel)
        await interaction.followup.send(embed=embed, view=v, ephemeral=True)
    else:
        await interaction.followup.send(embed=embed, ephemeral=True)

# ─── /equipar ────────────────────────────────────────────────────

@bot.tree.command(name="equipar", description="Equipa um item do inventario")
@app_commands.describe(nome_item="Nome do item")
async def equipar(interaction: discord.Interaction, nome_item: str):
    await interaction.response.defer(ephemeral=True)
    pool = await get_pool()
    async with pool.acquire() as conn:
        item = await conn.fetchrow(
            "SELECT * FROM inventario WHERE user_id=$1 AND LOWER(nome) LIKE $2",
            interaction.user.id, f"%{nome_item.lower()}%"
        )
        if not item:
            await interaction.followup.send(f"Item '{nome_item}' nao encontrado.", ephemeral=True); return
        if item["equipado"]:
            await interaction.followup.send(f"**{item['nome']}** ja esta equipado!", ephemeral=True); return
        await conn.execute(
            "UPDATE inventario SET equipado=0 WHERE user_id=$1 AND tipo=$2 AND equipado=1",
            interaction.user.id, item["tipo"]
        )
        await conn.execute("UPDATE inventario SET equipado=1 WHERE id=$1", item["id"])
    await interaction.followup.send(embed=discord.Embed(title="Item equipado!", description=f"{item['emoji']} **{item['nome']}** equipado!", color=0x1D9E75), ephemeral=True)

# ─── /jogar-fora ─────────────────────────────────────────────────

class ConfirmarDescarte(discord.ui.View):
    def __init__(self, uid, item_id, nome, emoji):
        super().__init__(timeout=30)
        self.uid=uid; self.item_id=item_id; self.nome=nome; self.emoji=emoji

    @discord.ui.button(label="Sim, descartar", style=discord.ButtonStyle.danger)
    async def confirmar(self, inter: discord.Interaction, b):
        if inter.user.id != self.uid:
            await inter.response.send_message("Nao e seu inventario!", ephemeral=True); return
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM inventario WHERE id=$1", self.item_id)
        await inter.response.edit_message(embed=discord.Embed(description=f"{self.emoji} **{self.nome}** descartado.", color=0x888780), view=None)

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.secondary)
    async def cancelar(self, inter: discord.Interaction, b):
        await inter.response.edit_message(content="Cancelado.", embed=None, view=None)

@bot.tree.command(name="jogar-fora", description="Descarta um item do inventario")
@app_commands.describe(nome_item="Nome do item")
async def jogar_fora(interaction: discord.Interaction, nome_item: str):
    await interaction.response.defer(ephemeral=True)
    pool = await get_pool()
    async with pool.acquire() as conn:
        item = await conn.fetchrow(
            "SELECT * FROM inventario WHERE user_id=$1 AND LOWER(nome) LIKE $2",
            interaction.user.id, f"%{nome_item.lower()}%"
        )
    if not item:
        await interaction.followup.send(f"Item '{nome_item}' nao encontrado.", ephemeral=True); return
    if item["equipado"]:
        await interaction.followup.send("Desequipe o item antes de descartar!", ephemeral=True); return
    await interaction.followup.send(
        embed=discord.Embed(title="Tem certeza?", description=f"Descartar **{item['emoji']} {item['nome']}**?", color=0xE24B4A),
        view=ConfirmarDescarte(interaction.user.id, item["id"], item["nome"], item["emoji"]),
        ephemeral=True
    )

# ─── /dar ────────────────────────────────────────────────────────

@bot.tree.command(name="dar", description="Da um item para outro jogador")
@app_commands.describe(jogador="Quem vai receber", nome_item="Nome do item")
async def dar(interaction: discord.Interaction, jogador: discord.Member, nome_item: str):
    await interaction.response.defer()
    if jogador.id == interaction.user.id:
        await interaction.followup.send("Nao pode dar pra si mesmo!", ephemeral=True); return
    if not await get_personagem(jogador.id):
        await interaction.followup.send(f"{jogador.display_name} nao tem personagem!", ephemeral=True); return
    pool = await get_pool()
    async with pool.acquire() as conn:
        item = await conn.fetchrow(
            "SELECT * FROM inventario WHERE user_id=$1 AND LOWER(nome) LIKE $2",
            interaction.user.id, f"%{nome_item.lower()}%"
        )
        if not item:
            await interaction.followup.send(f"Item '{nome_item}' nao encontrado.", ephemeral=True); return
        if item["equipado"]:
            await interaction.followup.send("Desequipe o item antes de dar!", ephemeral=True); return
        await conn.execute("DELETE FROM inventario WHERE id=$1", item["id"])
        await conn.execute(
            "INSERT INTO inventario(user_id,item_id,nome,tipo,raridade,emoji,descricao) VALUES($1,$2,$3,$4,$5,$6,$7)",
            jogador.id, item["item_id"], item["nome"], item["tipo"], item["raridade"], item["emoji"], item["descricao"]
        )
    await interaction.followup.send(embed=discord.Embed(
        title="Item transferido!",
        description=f"{interaction.user.mention} deu **{item['emoji']} {item['nome']}** para {jogador.mention}!",
        color=0x1D9E75
    ))

# ─── /set-item ───────────────────────────────────────────────────

@bot.tree.command(name="set-item", description="[ADMIN] Adiciona item ao inventario de um jogador")
@app_commands.describe(jogador="Jogador que vai receber o item")
@app_commands.checks.has_permissions(administrator=True)
async def set_item(interaction: discord.Interaction, jogador: discord.Member):
    await interaction.response.defer(ephemeral=True)
    if not await get_personagem(jogador.id):
        await interaction.followup.send(f"{jogador.display_name} nao tem personagem!", ephemeral=True); return

    CATALOGO = [
        {"id":"pocao_hp_p",     "nome":"Pocao de Cura P",     "emoji":"🧪","tipo":"pocao",   "raridade":"Comum",   "desc":"Recupera 30 HP"},
        {"id":"pocao_hp_m",     "nome":"Pocao de Cura M",     "emoji":"💊","tipo":"pocao",   "raridade":"Comum",   "desc":"Recupera 60 HP"},
        {"id":"pocao_hp_g",     "nome":"Pocao de Cura G",     "emoji":"❤️","tipo":"pocao",   "raridade":"Comum",   "desc":"Recupera 120 HP"},
        {"id":"pocao_mana_p",   "nome":"Pocao de Mana P",     "emoji":"🔵","tipo":"pocao",   "raridade":"Comum",   "desc":"Recupera 20 Mana"},
        {"id":"pocao_mana_m",   "nome":"Pocao de Mana M",     "emoji":"💙","tipo":"pocao",   "raridade":"Comum",   "desc":"Recupera 50 Mana"},
        {"id":"elixir",         "nome":"Elixir Supremo",      "emoji":"✨","tipo":"pocao",   "raridade":"Epico",   "desc":"HP e Mana full"},
        {"id":"espada_prata",   "nome":"Espada de Prata",     "emoji":"⚔️","tipo":"arma",    "raridade":"Incomum", "desc":"Dano +5"},
        {"id":"cajado_magico",  "nome":"Cajado Magico",       "emoji":"🪄","tipo":"arma",    "raridade":"Raro",    "desc":"Magia +10"},
        {"id":"arco_elfico",    "nome":"Arco Elfico",         "emoji":"🏹","tipo":"arma",    "raridade":"Raro",    "desc":"Critico +15%"},
        {"id":"lanca_sagrada",  "nome":"Lanca Sagrada",       "emoji":"🔱","tipo":"arma",    "raridade":"Epico",   "desc":"Sagrado +20"},
        {"id":"espada_orc",     "nome":"Espada Orc",          "emoji":"🗡️","tipo":"arma",    "raridade":"Raro",    "desc":"Forjada com metal orc"},
        {"id":"cajado_osso2",   "nome":"Cajado Osseo+",       "emoji":"💀","tipo":"arma",    "raridade":"Raro",    "desc":"Amplifica magia negra"},
        {"id":"armadura_couro", "nome":"Armadura de Couro",   "emoji":"🥋","tipo":"armadura","raridade":"Comum",   "desc":"Defesa +3"},
        {"id":"cota_malha",     "nome":"Cota de Malha",       "emoji":"🛡️","tipo":"armadura","raridade":"Incomum", "desc":"Defesa +8"},
        {"id":"armadura_plena", "nome":"Armadura Plena",      "emoji":"⚙️","tipo":"armadura","raridade":"Raro",    "desc":"Defesa +15"},
        {"id":"armadura_escama","nome":"Armadura de Escama",  "emoji":"🐉","tipo":"armadura","raridade":"Epico",   "desc":"Escamas de dragao"},
        {"id":"elmo_dragao",    "nome":"Elmo do Dragao",      "emoji":"🪖","tipo":"armadura","raridade":"Lendario","desc":"Protecao maxima"},
        {"id":"dente_orc",      "nome":"Dente de Orc",        "emoji":"🦷","tipo":"material","raridade":"Incomum", "desc":"Ingrediente alquimico"},
        {"id":"fragmento_golem","nome":"Fragmento de Golem",  "emoji":"🪨","tipo":"material","raridade":"Raro",    "desc":"Material magico"},
        {"id":"escama_dragao",  "nome":"Escama de Dragao",    "emoji":"🐉","tipo":"material","raridade":"Lendario","desc":"Material lendario"},
        {"id":"sangue_anciao",  "nome":"Sangue Anciao",       "emoji":"🩸","tipo":"material","raridade":"Raro",    "desc":"Pocao rara"},
        {"id":"olho_dragao",    "nome":"Olho de Dragao",      "emoji":"👁️","tipo":"material","raridade":"Epico",   "desc":"Ingrediente raro"},
    ]

    embed = discord.Embed(title=f"Dar item para {jogador.display_name}", description="Escolha o item e a quantidade:", color=0x7F77DD)
    item_sel = {"id": None}; qtd_sel = {"v": 1}
    opcoes1 = [discord.SelectOption(label=f"{it['emoji']} {it['nome']}", value=it["id"], description=f"{it['tipo'].title()} | {it['raridade']}"[:100]) for it in CATALOGO[:25]]
    opcoes_qtd = [discord.SelectOption(label=f"{i}x", value=str(i)) for i in [1,2,3,5,10,20,50]]
    btn = discord.ui.Button(label="Confirmar", style=discord.ButtonStyle.success, disabled=True, row=2)
    s1 = discord.ui.Select(placeholder="Escolha o item...", options=opcoes1, row=0)
    sq = discord.ui.Select(placeholder="Quantidade...", options=opcoes_qtd, row=1)

    async def on_s1(inter):
        item_sel["id"] = s1.values[0]; btn.disabled = False
        await inter.response.edit_message(view=v)
    async def on_sq(inter):
        qtd_sel["v"] = int(sq.values[0])
        await inter.response.edit_message(view=v)
    async def on_btn(inter):
        if inter.user.id != interaction.user.id: return
        iid = item_sel["id"]; qtd = qtd_sel["v"]
        it = next((i for i in CATALOGO if i["id"] == iid), None)
        if not it: return
        pool = await get_pool()
        async with pool.acquire() as conn:
            for _ in range(qtd):
                ex = await conn.fetchrow("SELECT id,quantidade FROM inventario WHERE user_id=$1 AND item_id=$2", jogador.id, iid)
                if ex:
                    await conn.execute("UPDATE inventario SET quantidade=quantidade+1 WHERE id=$1", ex["id"])
                else:
                    await conn.execute(
                        "INSERT INTO inventario(user_id,item_id,nome,tipo,raridade,emoji,descricao) VALUES($1,$2,$3,$4,$5,$6,$7)",
                        jogador.id, iid, it["nome"], it["tipo"], it["raridade"], it["emoji"], it["desc"]
                    )
        await inter.response.edit_message(
            embed=discord.Embed(title="Item adicionado!", description=f"{it['emoji']} **{it['nome']}** x{qtd} para {jogador.mention}!", color=COR_RAR.get(it["raridade"], 0x888780)),
            view=None
        )
        await asyncio.sleep(3)
        try:
            msg = await inter.original_response()
            await msg.delete()
        except: pass

    s1.callback = on_s1; sq.callback = on_sq; btn.callback = on_btn
    v = discord.ui.View(timeout=120)
    v.add_item(s1); v.add_item(sq); v.add_item(btn)
    await interaction.followup.send(embed=embed, view=v, ephemeral=True)

# ─── /set-moedas ─────────────────────────────────────────────────

@bot.tree.command(name="set-moedas", description="[ADMIN] Define ou adiciona moedas")
@app_commands.describe(jogador="Alvo", quantidade="Quantidade", modo="adicionar ou definir")
@app_commands.choices(modo=[
    app_commands.Choice(name="adicionar", value="adicionar"),
    app_commands.Choice(name="definir",   value="definir"),
])
@app_commands.checks.has_permissions(administrator=True)
async def set_moedas(interaction: discord.Interaction, jogador: discord.Member, quantidade: int, modo: str = "adicionar"):
    await interaction.response.defer(ephemeral=True)
    p = await get_personagem(jogador.id)
    if not p:
        await interaction.followup.send(f"{jogador.display_name} nao tem personagem!", ephemeral=True); return
    novo = quantidade if modo == "definir" else p["moedas"] + quantidade
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("UPDATE personagens SET moedas=$1 WHERE user_id=$2", novo, jogador.id)
    await interaction.followup.send(embed=discord.Embed(title="Moedas atualizadas!", description=f"{jogador.mention} agora tem **{novo} 🪙**", color=0xE4AF3C), ephemeral=True)

# ─── /treinar ────────────────────────────────────────────────────

@bot.tree.command(name="treinar", description="Batalha contra um monstro para ganhar XP")
@app_commands.choices(dificuldade=[
    app_commands.Choice(name="Facil — Goblin/Lobo",        value="facil"),
    app_commands.Choice(name="Medio — Orc/Golem",          value="medio"),
    app_commands.Choice(name="Dificil — Vampiro",          value="dificil"),
    app_commands.Choice(name="Lendario — Dragao (nv 25+)", value="lendario"),
])
async def treinar(interaction: discord.Interaction, dificuldade: str = "facil"):
    await interaction.response.defer()
    p = await get_personagem(interaction.user.id)
    if not p:
        await interaction.followup.send("Crie seu personagem com `/criar_personagem`!", ephemeral=True); return
    if dificuldade == "lendario" and p["nivel"] < 25:
        await interaction.followup.send(f"Precisa ser nivel 25+! (Seu nivel: {p['nivel']})", ephemeral=True); return

    view_arena = EscolherArenaView(interaction.user.id)
    await interaction.followup.send("Escolha a arena:", view=view_arena, wait=True)
    await view_arena.wait()
    arena = view_arena.arena

    monstros = [m for m in MONSTROS if m["dificuldade"] == dificuldade]
    if not monstros: monstros = [MONSTROS[0]]
    monstro = dict(random.choice(monstros))
    escala = max(1.0, p["nivel"] / max(1, monstro["nivel"]))
    if escala > 1.2:
        monstro["hp"]     = int(monstro["hp"]     * min(escala, 2.0))
        monstro["ataque"] = int(monstro["ataque"] * min(escala, 1.5))
        monstro["xp"]     = int(monstro["xp"]     * min(escala, 2.0))
        monstro["moedas"] = int(monstro["moedas"] * min(escala, 2.0))

    await rodar_treino(interaction, p, monstro, arena)

# ─── /desafiar ───────────────────────────────────────────────────

@bot.tree.command(name="desafiar", description="Desafia outro jogador para um duelo PvP")
@app_commands.describe(jogador="Jogador que voce quer desafiar")
async def desafiar(interaction: discord.Interaction, jogador: discord.Member):
    await interaction.response.defer()
    if jogador.id == interaction.user.id:
        await interaction.followup.send("Nao pode se desafiar!", ephemeral=True); return
    if jogador.bot:
        await interaction.followup.send("Use `/treinar` para batalhar contra monstros!", ephemeral=True); return
    p1 = await get_personagem(interaction.user.id)
    p2 = await get_personagem(jogador.id)
    if not p1:
        await interaction.followup.send("Crie seu personagem primeiro!", ephemeral=True); return
    if not p2:
        await interaction.followup.send(f"{jogador.display_name} nao tem personagem!", ephemeral=True); return

    arena = random.choice(ARENAS)
    view_d = AceitarDueloView(interaction.user.id, jogador.id)
    desc = (
        f"{interaction.user.mention} desafia {jogador.mention} para um duelo!\n\n"
        f"**{p1['nome']}** (Nv {p1['nivel']}) vs **{p2['nome']}** (Nv {p2['nivel']})\n\n"
        f"{arena['emoji']} Arena sorteada: **{arena['nome']}** — {arena['bonus']}\n\n"
        f"{jogador.mention}, voce aceita?"
    )
    embed_d = discord.Embed(title="Desafio de Duelo!", description=desc, color=0xD85A30)
    embed_d.set_footer(text="Expira em 5 minutos.")
    msg_d = await interaction.followup.send(embed=embed_d, view=view_d, wait=True)
    await view_d.wait()

    if view_d.resposta is None:
        await msg_d.edit(embed=discord.Embed(title="Desafio expirado.", color=0x888780), view=None); return
    if not view_d.resposta:
        await msg_d.edit(embed=discord.Embed(title="Desafio recusado.", color=0x888780), view=None); return

    await msg_d.edit(embed=discord.Embed(title=f"Duelo aceito! Arena: {arena['emoji']} {arena['nome']}", color=0x1D9E75), view=None)
    canal_batalha = discord.utils.get(interaction.guild.text_channels, name="🥊┃arena-pública") or interaction.channel
    await asyncio.sleep(1)
    await rodar_pvp(canal_batalha, p1, p2, interaction.user, jogador, arena)

# ─── /dungeon ────────────────────────────────────────────────────

@bot.tree.command(name="dungeon", description="Entre em uma dungeon e enfrente os chefes")
@app_commands.describe(rank="Rank da dungeon")
@app_commands.choices(rank=[
    app_commands.Choice(name="Rank F — Nivel 1+",  value="F"),
    app_commands.Choice(name="Rank E — Nivel 5+",  value="E"),
    app_commands.Choice(name="Rank D — Nivel 10+", value="D"),
    app_commands.Choice(name="Rank C — Nivel 20+", value="C"),
    app_commands.Choice(name="Rank B — Nivel 30+", value="B"),
    app_commands.Choice(name="Rank A — Nivel 40+", value="A"),
    app_commands.Choice(name="Rank S — Nivel 50+", value="S"),
])
async def dungeon(interaction: discord.Interaction, rank: str):
    await cmd_dungeon(interaction, rank)

# ─── /hospital ───────────────────────────────────────────────────

@bot.tree.command(name="hospital", description="Restaura seu HP e Mana pagando moedas")
async def hospital(interaction: discord.Interaction):
    await cmd_hospital(interaction)

# ─── /girar ──────────────────────────────────────────────────────

@bot.tree.command(name="girar", description="Use seus giros de roleta acumulados")
async def girar(interaction: discord.Interaction):
    await cmd_girar(interaction)

# ─── /set-giros ──────────────────────────────────────────────────

@bot.tree.command(name="set-giros", description="[ADMIN] Da giros de roleta para um jogador")
@app_commands.describe(jogador="Jogador que vai receber os giros")
@app_commands.checks.has_permissions(administrator=True)
async def set_giros(interaction: discord.Interaction, jogador: discord.Member):
    await cmd_set_giros(interaction, jogador)

# ─── /loja ───────────────────────────────────────────────────────

@bot.tree.command(name="loja", description="Compre itens da loja — armas, armaduras e pocoes da sua classe")
@app_commands.choices(categoria=[
    app_commands.Choice(name="⚔️ Armas da minha classe",     value="armas"),
    app_commands.Choice(name="🛡️ Armaduras da minha classe", value="armaduras"),
    app_commands.Choice(name="🧪 Pocoes e Elixires",         value="pocoes"),
])
async def loja(interaction: discord.Interaction, categoria: str = "pocoes"):
    await interaction.response.defer(ephemeral=True)
    p = await get_personagem(interaction.user.id)
    if not p:
        await interaction.followup.send("Crie seu personagem primeiro!", ephemeral=True); return

    rank_info = get_rank(p["nivel"])

    if categoria == "armas":
        itens_cat = get_armas_classe(p["classe_id"])
        # so mostra itens com preco > 0 (os de preco 0 sao de dungeon/ferreiro)
        itens = [
            {"id":i["id"],"nome":i["nome"],"emoji":i["emoji"],
             "raridade":i["raridade"],"preco":i["preco"],"desc":i["desc"],"tipo":"arma"}
            for i in itens_cat if i["preco"] > 0
        ]
    elif categoria == "armaduras":
        itens_cat = get_armaduras_classe(p["classe_id"])
        itens = [
            {"id":i["id"],"nome":i["nome"],"emoji":i["emoji"],
             "raridade":i["raridade"],"preco":i["preco"],"desc":i["desc"],"tipo":"armadura"}
            for i in itens_cat if i["preco"] > 0
        ]
    else:
        itens = list(LOJA_ITENS.get("pocoes", []))

    COR_RAR_LOJA = {"Comum":"⬜","Incomum":"🟩","Raro":"🟦","Epico":"🟪","Lendario":"🟧"}
    classe_nome = p["classe_id"].title()
    titulo_cat = f"⚔️ Armas — {classe_nome}" if categoria=="armas" else (f"🛡️ Armaduras — {classe_nome}" if categoria=="armaduras" else "🧪 Pocoes")

    embed = discord.Embed(
        title=f"🏪 Loja — {titulo_cat}",
        description=(
            f"Jogador: **{p['nome']}** {rank_info['emoji']} Rank {rank_info['rank']} — Nv {p['nivel']}\n"
            f"Moedas: **{p['moedas']} 🪙** | Classe: **{classe_nome}**\n\n"
            f"{'*Mostrando apenas itens compraveis — itens Lendarios e gratuitos sao de dungeons/ferreiro*' if categoria in ('armas','armaduras') else ''}"
        ),
        color=0xE4AF3C
    )
    for it in itens[:15]:
        rar_emoji = COR_RAR_LOJA.get(it['raridade'], "⬜")
        embed.add_field(
            name=f"{rar_emoji} {it['emoji']} {it['nome']}",
            value=f"*{it['desc']}*\n**{it['preco']} 🪙** | {it['raridade']}",
            inline=True
        )

    if not itens:
        embed.description += "\n\n*Nenhum item disponivel para compra nesta categoria.*"
        await interaction.followup.send(embed=embed, ephemeral=True); return

    opcoes = [
        discord.SelectOption(
            label=f"{it['emoji']} {it['nome']} — {it['preco']} 🪙",
            value=it["id"],
            description=f"{it['raridade']} | {it['desc'][:50]}"
        ) for it in itens[:25]
    ]
    sel = discord.ui.Select(placeholder="Selecione o item para comprar...", options=opcoes)

    async def comprar(inter: discord.Interaction):
        if inter.user.id != interaction.user.id: return
        item_def = next((i for i in itens if i["id"] == sel.values[0]), None)
        if not item_def: return
        p2 = await get_personagem(inter.user.id)
        if p2["moedas"] < item_def["preco"]:
            await inter.response.send_message(f"Moedas insuficientes! Precisa de **{item_def['preco']} 🪙**", ephemeral=True); return
        tipo = item_def.get("tipo", "pocao")
        db_pool = await get_pool()
        async with db_pool.acquire() as conn:
            await conn.execute("UPDATE personagens SET moedas=moedas-$1 WHERE user_id=$2", item_def["preco"], inter.user.id)
            ex = await conn.fetchrow("SELECT id, quantidade FROM inventario WHERE user_id=$1 AND item_id=$2", inter.user.id, item_def["id"])
            if ex:
                await conn.execute("UPDATE inventario SET quantidade=quantidade+1 WHERE id=$1", ex["id"])
            else:
                await conn.execute(
                    "INSERT INTO inventario(user_id,item_id,nome,tipo,raridade,emoji,descricao) VALUES($1,$2,$3,$4,$5,$6,$7)",
                    inter.user.id, item_def["id"], item_def["nome"], tipo, item_def["raridade"], item_def["emoji"], item_def["desc"]
                )
        try: await atualizar_progresso(inter.user.id, "moedas_gastas", item_def["preco"])
        except: pass
        rar_e = COR_RAR_LOJA.get(item_def["raridade"], "⬜")
        await inter.response.edit_message(
            embed=discord.Embed(
                title="✅ Compra realizada!",
                description=f"{rar_e} {item_def['emoji']} **{item_def['nome']}** adicionado ao inventario!\n\n-{item_def['preco']} 🪙 | Saldo restante: {p2['moedas']-item_def['preco']} 🪙",
                color=0x1D9E75
            ),
            view=None
        )

    sel.callback = comprar
    v = discord.ui.View(timeout=60); v.add_item(sel)
    await interaction.followup.send(embed=embed, view=v, ephemeral=True)

# ─── /ferreiro ───────────────────────────────────────────────────

@bot.tree.command(name="ferreiro", description="Forje itens usando materiais coletados")
async def ferreiro(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    p = await get_personagem(interaction.user.id)
    if not p:
        await interaction.followup.send("Crie seu personagem primeiro!", ephemeral=True); return

    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT item_id, quantidade FROM inventario WHERE user_id=$1 AND tipo='material'", interaction.user.id)
    inv = {r["item_id"]: r["quantidade"] for r in rows}

    embed = discord.Embed(title="Ferreiro", description=f"Suas moedas: **{p['moedas']} 🪙**\nEscolha uma receita:", color=0x888780)
    for r in RECEITAS:
        mats = " | ".join([f"{qty}x {mid}" for mid, qty in r["materiais"].items()])
        tem = all(inv.get(mid, 0) >= qty for mid, qty in r["materiais"].items())
        embed.add_field(name=f"{'✅' if tem else '❌'} {r['emoji']} {r['nome']} [{r['raridade']}]", value=f"{r['desc']}\nMateriais: {mats}\nForja: {r['preco_forja']} 🪙", inline=False)

    opcoes = [discord.SelectOption(label=f"{r['emoji']} {r['nome']} — {r['preco_forja']} 🪙", value=r["id"], description=r["desc"][:50]) for r in RECEITAS]
    sel = discord.ui.Select(placeholder="Escolha uma receita...", options=opcoes)

    async def forjar(inter: discord.Interaction):
        if inter.user.id != interaction.user.id: return
        rec = next((r for r in RECEITAS if r["id"] == sel.values[0]), None)
        if not rec: return
        p2 = await get_personagem(inter.user.id)
        pool2 = await get_pool()
        async with pool2.acquire() as conn:
            rows2 = await conn.fetch("SELECT item_id, quantidade FROM inventario WHERE user_id=$1 AND tipo='material'", inter.user.id)
            inv2 = {r["item_id"]: r["quantidade"] for r in rows2}
            falta = [f"{qty}x {mid}" for mid, qty in rec["materiais"].items() if inv2.get(mid, 0) < qty]
            if falta:
                await inter.response.send_message(f"Faltam materiais: {', '.join(falta)}", ephemeral=True); return
            if p2["moedas"] < rec["preco_forja"]:
                await inter.response.send_message(f"Precisa de {rec['preco_forja']} 🪙!", ephemeral=True); return
            for mid, qty in rec["materiais"].items():
                row = await conn.fetchrow("SELECT id,quantidade FROM inventario WHERE user_id=$1 AND item_id=$2", inter.user.id, mid)
                if row:
                    if row["quantidade"] > qty:
                        await conn.execute("UPDATE inventario SET quantidade=quantidade-$1 WHERE id=$2", qty, row["id"])
                    else:
                        await conn.execute("DELETE FROM inventario WHERE id=$1", row["id"])
            await conn.execute("UPDATE personagens SET moedas=moedas-$1 WHERE user_id=$2", rec["preco_forja"], inter.user.id)
            await conn.execute(
                "INSERT INTO inventario(user_id,item_id,nome,tipo,raridade,emoji,descricao) VALUES($1,$2,$3,$4,$5,$6,$7)",
                inter.user.id, rec["id"], rec["nome"], rec["tipo"], rec["raridade"], rec["emoji"], rec["desc"]
            )
        await inter.response.edit_message(
            embed=discord.Embed(title="Item forjado!", description=f"{rec['emoji']} **{rec['nome']}** [{rec['raridade']}] adicionado!", color=COR_RAR.get(rec["raridade"], 0x888780)),
            view=None
        )

    sel.callback = forjar
    v = discord.ui.View(timeout=60); v.add_item(sel)
    await interaction.followup.send(embed=embed, view=v, ephemeral=True)

# ─── /missoes ────────────────────────────────────────────────────

@bot.tree.command(name="missoes", description="Veja suas missoes diarias e progresso")
async def missoes(interaction: discord.Interaction):
    await cmd_missoes(interaction)

# ─── /ranking ────────────────────────────────────────────────────

@bot.tree.command(name="ranking", description="Veja o ranking do servidor")
async def ranking(interaction: discord.Interaction):
    await cmd_ranking(interaction)

# ─── /deletar_personagem ─────────────────────────────────────────

class ConfirmarDelete(discord.ui.View):
    def __init__(self, uid, nome, classe_id):
        super().__init__(timeout=30)
        self.uid = uid; self.nome = nome; self.classe_id = classe_id

    @discord.ui.button(label="Sim, DELETAR tudo", style=discord.ButtonStyle.danger)
    async def confirmar(self, inter: discord.Interaction, b):
        if inter.user.id != self.uid:
            await inter.response.send_message("Nao e voce!", ephemeral=True); return
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM personagens WHERE user_id=$1",          self.uid)
            await conn.execute("DELETE FROM inventario WHERE user_id=$1",            self.uid)
            await conn.execute("DELETE FROM skills_desbloqueadas WHERE user_id=$1",  self.uid)
            await conn.execute("DELETE FROM skills_equipadas WHERE user_id=$1",      self.uid)
            await conn.execute("DELETE FROM giros WHERE user_id=$1",                 self.uid)
            await conn.execute("DELETE FROM missoes_diarias WHERE user_id=$1",       self.uid)
        guild = inter.guild
        if guild:
            member = guild.get_member(self.uid)
            if member:
                for cn in ["Guerreiro","Arqueiro","Mago","Paladino","Necromante","Dracomante","Arcano"]:
                    cargo = discord.utils.get(guild.roles, name=cn)
                    if cargo and cargo in member.roles:
                        try: await member.remove_roles(cargo)
                        except: pass
                recem = discord.utils.get(guild.roles, name="🌱 Recem-chegado")
                if recem:
                    try: await member.add_roles(recem)
                    except: pass
        await inter.response.edit_message(
            embed=discord.Embed(title="Personagem deletado.", description=f"**{self.nome}** foi removido.\nUse `/criar_personagem` para comecar de novo.", color=0x888780),
            view=None
        )

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.secondary)
    async def cancelar(self, inter: discord.Interaction, b):
        await inter.response.edit_message(embed=discord.Embed(description="Acao cancelada.", color=0x1D9E75), view=None)

@bot.tree.command(name="deletar_personagem", description="Deleta seu personagem PERMANENTEMENTE")
async def deletar_personagem(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    p = await get_personagem(interaction.user.id)
    if not p:
        await interaction.followup.send("Voce nao tem personagem!", ephemeral=True); return
    embed = discord.Embed(
        title="ATENCAO — Acao irreversivel!",
        description=f"Voce esta prestes a deletar **{p['nome']}** (Nv {p['nivel']}).\n\nIsso apaga tudo: personagem, inventario, skills, giros e missoes.\n\n**Esta acao NAO pode ser desfeita.**",
        color=0xE24B4A
    )
    await interaction.followup.send(embed=embed, view=ConfirmarDelete(interaction.user.id, p["nome"], p["classe_id"]), ephemeral=True)

# ─── /ajuda ──────────────────────────────────────────────────────

@bot.tree.command(name="ajuda", description="Lista todos os comandos")
async def ajuda(interaction: discord.Interaction):
    embed = discord.Embed(title="Comandos do RPG", color=0x7F77DD)
    embed.add_field(name="Personagem",  value="`/criar_personagem` `/perfil` `/skills` `/setup` `/deletar_personagem`", inline=False)
    embed.add_field(name="Inventario",  value="`/inventario` `/equipar` `/jogar-fora` `/dar`", inline=False)
    embed.add_field(name="Batalha",     value="`/treinar` `/desafiar` `/dungeon`", inline=False)
    embed.add_field(name="Economia",    value="`/loja` `/ferreiro` `/hospital`", inline=False)
    embed.add_field(name="Progresso",   value="`/missoes` `/ranking` `/girar`", inline=False)
    embed.add_field(name="Admin",       value="`/set-item` `/set-moedas` `/set-giros`", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ─── EVENTOS ─────────────────────────────────────────────────────

@bot.event
async def on_ready():
    print("Iniciando...")
    try:
        await init_db()
        await init_db_batalha()
        await init_db_hospital()
        await init_db_missoes()
    except Exception as e:
        print(f"ERRO no banco: {e}")
    try:
        guild_id = int(os.getenv("GUILD_ID", "0"))
        if guild_id:
            bot.tree.copy_global_to(guild=discord.Object(id=guild_id))
            synced = await bot.tree.sync(guild=discord.Object(id=guild_id))
            print(f"Comandos sincronizados: {len(synced)}")
    except Exception as e:
        print(f"ERRO ao sincronizar: {e}")
    print(f"Bot online: {bot.user}")

@bot.event
async def on_member_join(member: discord.Member):
    for nome_cargo in ["🌱 Recem-chegado"]:
        cargo = discord.utils.get(member.guild.roles, name=nome_cargo)
        if cargo:
            try: await member.add_roles(cargo)
            except: pass
    try:
        embed = discord.Embed(
            title="⚔️ Bem-vindo a Villa Eldoria!",
            description=(
                f"Ola **{member.display_name}**!\n\n"
                "Use `/criar_personagem` no canal **#criar-personagem** para comecar sua jornada!\n\n"
                "**7 classes disponíveis:**\n"
                "🗡️ Guerreiro | 🏹 Arqueiro | 🔮 Mago | ⚡ Paladino\n"
                "🌑 Necromante | ✨ Arcano | 🐉 Dracomante\n\n"
                "**Sistema de Ranks:** F → E → D → C → B → A → S → SS\n"
                "Bom jogo!"
            ),
            color=0x7F77DD
        )
        await member.send(embed=embed)
    except: pass

if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        try:
            with open("config.txt") as f:
                for linha in f:
                    if linha.startswith("DISCORD_TOKEN="):
                        token = linha.split("=",1)[1].strip()
        except: pass
    if not token:
        print("ERRO: Token nao encontrado.")
        exit(1)
    bot.run(token)
