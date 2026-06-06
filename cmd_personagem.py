# cmd_personagem.py — Comandos de personagem

import discord
from discord import app_commands
import random
import asyncio

from db import get_pool
from data_racas import RACAS, RACAS_BASICAS, get_raca
from data_classes import CLASSES, PODERES, PESOS_PODER, DESTINOS
from data_skills import SKILLS_COMPLETAS
from constants import COR_RAR, EMOJI_CLASSE
from imagens import IMG_PERFIL
from utils import atualizar_todos_cargos
from catalogo import get_rank, calcular_mana_max
from sistema_personagem import get_personagem, criar_canal_privado, calcular_stats
from sistema_combate import get_skills_eq, get_skills_desbloq, GerenciarSkillsView
from setup_cmd import cmd_setup


def sortear_peso(lista, pesos):
    return random.choices(lista, weights=pesos, k=1)[0]


# ==================================================
# COMANDO CRIAR PERSONAGEM
# ==================================================

async def cmd_criar_personagem(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    uid = interaction.user.id
    if await get_personagem(uid):
        await interaction.followup.send("Você já tem personagem! Use /perfil.", ephemeral=True)
        return

    embed_raca = discord.Embed(title="Passo 1 — Escolha sua Raça", color=0x7F77DD)
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
            self.escolha = "humano"
            await inter.response.defer()
            self.stop()
        @discord.ui.button(label="Anão", style=discord.ButtonStyle.primary)
        async def btn_a(self, inter, b):
            if inter.user.id != uid: return
            self.escolha = "anao"
            await inter.response.defer()
            self.stop()
        @discord.ui.button(label="Elfo", style=discord.ButtonStyle.primary)
        async def btn_e(self, inter, b):
            if inter.user.id != uid: return
            self.escolha = "elfo"
            await inter.response.defer()
            self.stop()

    vr = RacaView()
    msg = await interaction.followup.send(embed=embed_raca, view=vr, ephemeral=True, wait=True)
    await vr.wait()
    if not vr.escolha:
        await msg.edit(content="Tempo esgotado!", embed=None, view=None)
        return
    raca = RACAS[vr.escolha]

    BASICAS = [c for c in CLASSES if c["raridade"] == "Comum"]
    embed_cls = discord.Embed(title="Passo 2 — Escolha sua Classe", color=0xE4AF3C)
    for c in BASICAS:
        embed_cls.add_field(name=f"{c['emoji']} {c['nome']}", value=c["desc"], inline=True)
    embed_cls.set_footer(text=f"Raça: {raca['emoji']} {raca['nome']}")

    class ClasseView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=120)
            self.escolha = None
        @discord.ui.button(label="Guerreiro", style=discord.ButtonStyle.success)
        async def btn_g(self, inter, b):
            if inter.user.id != uid: return
            self.escolha = next(c for c in CLASSES if c["id"] == "guerreiro")
            await inter.response.defer()
            self.stop()
        @discord.ui.button(label="Arqueiro", style=discord.ButtonStyle.success)
        async def btn_a(self, inter, b):
            if inter.user.id != uid: return
            self.escolha = next(c for c in CLASSES if c["id"] == "arqueiro")
            await inter.response.defer()
            self.stop()
        @discord.ui.button(label="Mago", style=discord.ButtonStyle.success)
        async def btn_m(self, inter, b):
            if inter.user.id != uid: return
            self.escolha = next(c for c in CLASSES if c["id"] == "mago")
            await inter.response.defer()
            self.stop()

    vc = ClasseView()
    await msg.edit(embed=embed_cls, view=vc)
    await vc.wait()
    if not vc.escolha:
        await msg.edit(content="Tempo esgotado!", embed=None, view=None)
        return
    classe = vc.escolha

    await msg.edit(embed=discord.Embed(
        title="As roletas giram...",
        description=f"{raca['emoji']} {raca['nome']} + {classe['emoji']} {classe['nome']}\n\nSortindo poder, destino e skills...",
        color=0x7F77DD), view=None)
    await asyncio.sleep(1.5)

    poder = sortear_peso(PODERES, PESOS_PODER)
    destino = random.choice(DESTINOS)
    mana_max = calcular_mana_max(classe["id"], 1, poder["valor"], destino["id"])
    if raca["id"] == "elfo":
        mana_max += 20

    skills_cls = SKILLS_COMPLETAS.get(classe["id"], [])
    disp = [s for s in skills_cls if s["nivel"] <= 5]
    if len(disp) < 2:
        disp = skills_cls[:2]
    random.shuffle(disp)
    skills_s = disp[:2]

    hp, atk, dfs = calcular_stats(poder["valor"], destino["id"], 1)
    if raca["id"] == "anao":
        dfs += 5
    nome = interaction.user.display_name

    pool_db = await get_pool()
    async with pool_db.acquire() as conn:
        await conn.execute("""
            INSERT INTO personagens
            (user_id, nome, classe_id, raridade, poder_id, poder_valor, destino_id, skill_id,
             nivel, xp, hp_max, hp_atual, ataque, defesa, mana_max, mana_atual, moedas, raca_id)
            VALUES($1,$2,$3,$4,$5,$6,$7,$8,1,0,$9,$10,$11,$12,$13,$13,50,$14)
        """, uid, nome, classe["id"], classe["raridade"], poder["id"], poder["valor"],
            destino["id"], skills_s[0]["id"] if skills_s else "",
            hp, hp, atk, dfs, mana_max, raca["id"])
        for i, sk in enumerate(skills_s):
            await conn.execute("INSERT INTO skills_desbloqueadas(user_id, skill_id) VALUES($1,$2) ON CONFLICT DO NOTHING", uid, sk["id"])
            await conn.execute("INSERT INTO skills_equipadas(user_id, skill_id, slot) VALUES($1,$2,$3) ON CONFLICT(user_id, slot) DO UPDATE SET skill_id=EXCLUDED.skill_id", uid, sk["id"], i)

    efinal = discord.Embed(title=f"Bem-vindo, {nome}!", color=COR_RAR.get(classe["raridade"], 0x888780))
    efinal.add_field(name="Raça", value=f"{raca['emoji']} {raca['nome']}", inline=True)
    efinal.add_field(name="Classe", value=f"{classe['emoji']} {classe['nome']}", inline=True)
    efinal.add_field(name="Poder", value=f"{poder['emoji']} {poder['nome']}", inline=True)
    efinal.add_field(name="Destino", value=f"{destino['emoji']} {destino['nome']}", inline=True)
    efinal.add_field(name="HP", value=str(hp), inline=True)
    efinal.add_field(name="ATK", value=str(atk), inline=True)
    efinal.add_field(name="Mana", value=str(mana_max), inline=True)
    efinal.set_footer(text="Use /loja para comprar sua primeira arma! | /perfil para ver sua ficha")
    await msg.edit(embed=efinal, view=None)

    guild = interaction.guild
    if guild:
        member = guild.get_member(uid)
        if member:
            cargo_raca = discord.utils.get(guild.roles, name=raca.get("cargos", ""))
            if cargo_raca:
                try:
                    await member.add_roles(cargo_raca)
                except:
                    pass
            cargo_base = discord.utils.get(guild.roles, name="🏠 Morador da Vila")
            if not cargo_base:
                cargo_base = discord.utils.get(guild.roles, name="Morador da Vila")
            if cargo_base:
                try:
                    await member.add_roles(cargo_base)
                except:
                    pass
            recem = discord.utils.get(guild.roles, name="🌱 Recem-chegado")
            if recem and recem in member.roles:
                try:
                    await member.remove_roles(recem)
                except:
                    pass
            await atualizar_todos_cargos(guild, member, 1)
        await criar_canal_privado(guild, member, nome, classe)


# ==================================================
# COMANDO PERFIL
# ==================================================

async def cmd_perfil(interaction: discord.Interaction, jogador: discord.Member = None):
    await interaction.response.defer()
    alvo = jogador or interaction.user
    p = await get_personagem(alvo.id)
    if not p:
        await interaction.followup.send("Personagem não encontrado!", ephemeral=True)
        return
    cls = next((c for c in CLASSES if c["id"] == p["classe_id"]), None)
    raca_p = get_raca(p["raca_id"] if p["raca_id"] else "humano")
    rank_i = get_rank(p["nivel"])
    pool_db = await get_pool()
    async with pool_db.acquire() as conn:
        arma = await conn.fetchrow("SELECT * FROM inventario WHERE user_id=$1 AND tipo='arma' AND equipado=1", alvo.id)
        arm = await conn.fetchrow("SELECT * FROM inventario WHERE user_id=$1 AND tipo='armadura' AND equipado=1", alvo.id)
        ids_eq = await conn.fetch("SELECT skill_id FROM skills_equipadas WHERE user_id=$1 ORDER BY slot", alvo.id)
    sk_nomes = []
    for r in ids_eq:
        for sk in SKILLS_COMPLETAS.get(p["classe_id"], []):
            if sk["id"] == r["skill_id"]:
                sk_nomes.append(f"{sk['emoji']} {sk['nome']}")
                break
    xp_need = 100 + (p["nivel"] - 1) * 50
    embed = discord.Embed(
        title=f"{cls['emoji'] if cls else '?'} {p['nome']}",
        description=(
            f"**Raça:** {raca_p['emoji']} {raca_p['nome']}\n"
            f"**Classe:** {cls['nome'] if cls else p['classe_id']} — *{p['raridade']}*\n"
            f"**Rank:** {rank_i['emoji']} {rank_i['rank']} — {rank_i['nome']}\n"
            f"**Nível:** {p['nivel']} | XP: {p['xp']}/{xp_need}"
        ),
        color=COR_RAR.get(p["raridade"], 0x888780)
    )
    embed.add_field(name="Stats", value=f"❤️ {p['hp_atual']}/{p['hp_max']} | ⚔️ {p['ataque']} | 🛡️ {p['defesa']} | 💙 {p['mana_atual']}/{p['mana_max']}", inline=False)
    embed.add_field(name="Equipamento", value=f"⚔️ {arma['nome'] if arma else 'Sem arma'} | 🛡️ {arm['nome'] if arm else 'Sem armadura'}", inline=False)
    if sk_nomes:
        embed.add_field(name="Skills", value=" | ".join(sk_nomes), inline=False)
    embed.add_field(name=f"{raca_p['emoji']} Passiva Racial", value=raca_p['passiva_desc'], inline=False)
    embed.add_field(name="Moedas", value=f"{p['moedas']} 🪙", inline=True)
    embed.add_field(name="Vitórias", value=str(p.get('vitorias', 0)), inline=True)
    embed.set_thumbnail(url=alvo.display_avatar.url)
    embed.set_image(url=IMG_PERFIL)
    await interaction.followup.send(embed=embed)


# ==================================================
# COMANDO SKILLS
# ==================================================

async def cmd_skills(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    p = await get_personagem(interaction.user.id)
    if not p:
        await interaction.followup.send("Crie seu personagem primeiro!", ephemeral=True)
        return
    todas = SKILLS_COMPLETAS.get(p["classe_id"], [])
    ids_desbloq = await get_skills_desbloq(interaction.user.id)
    ids_eq = await get_skills_eq(interaction.user.id)
    disp = [s for s in todas if s["id"] in ids_desbloq]
    if not disp:
        await interaction.followup.send("Nenhuma skill desbloqueada ainda!", ephemeral=True)
        return
    view = GerenciarSkillsView(interaction.user.id, disp, ids_eq)
    embed = discord.Embed(title="Gerenciar Skills", description="Selecione até 4 skills para equipar:", color=0x7F77DD)
    for s in disp:
        mana_txt = f" | {s['mana']} mana" if s.get('mana') else ''
        embed.add_field(name=f"{s['emoji']} {s['nome']} (Nv{s['nivel']})", value=f"{s['desc']}{mana_txt}", inline=True)
    await interaction.followup.send(embed=embed, view=view, ephemeral=True)


# ==================================================
# COMANDO SETUP
# ==================================================

async def cmd_setup_wrapper(interaction: discord.Interaction):
    await cmd_setup(interaction)


# ==================================================
# COMANDO DELETAR PERSONAGEM
# ==================================================

async def cmd_deletar_personagem(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    p = await get_personagem(interaction.user.id)
    if not p:
        await interaction.followup.send("Você não tem personagem!", ephemeral=True)
        return
    class ConfView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=30)
            self.ok = None
        @discord.ui.button(label="Confirmar deleção", style=discord.ButtonStyle.danger)
        async def sim(self, inter, b):
            if inter.user.id != interaction.user.id:
                return
            self.ok = True
            await inter.response.defer()
            self.stop()
        @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.secondary)
        async def nao(self, inter, b):
            self.ok = False
            await inter.response.defer()
            self.stop()
    v = ConfView()
    await interaction.followup.send("⚠️ **ATENÇÃO:** Isso apaga seu personagem permanentemente! Confirma?", view=v, ephemeral=True)
    await v.wait()
    if not v.ok:
        await interaction.followup.send("❌ Deleção cancelada.", ephemeral=True)
        return
    pool_db = await get_pool()
    async with pool_db.acquire() as conn:
        for t in ["skills_equipadas", "skills_desbloqueadas", "inventario", "missoes_diarias", "conquistas", "giros"]:
            try:
                await conn.execute(f"DELETE FROM {t} WHERE user_id=$1", interaction.user.id)
            except:
                pass
        await conn.execute("DELETE FROM personagens WHERE user_id=$1", interaction.user.id)
    await interaction.followup.send("🗑️ Personagem deletado. Use `/criar_personagem` para recomeçar.", ephemeral=True)


# ==================================================
# REGISTRO DOS COMANDOS
# ==================================================

def setup_personagem_commands(bot):
    @bot.tree.command(name="criar_personagem", description="Crie seu personagem para começar a jogar!")
    async def criar_personagem(interaction: discord.Interaction):
        await cmd_criar_personagem(interaction)
    
    @bot.tree.command(name="perfil", description="Mostra a ficha do seu personagem")
    @app_commands.describe(jogador="Jogador (opcional)")
    async def perfil(interaction: discord.Interaction, jogador: discord.Member = None):
        await cmd_perfil(interaction, jogador)
    
    @bot.tree.command(name="skills", description="Veja e gerencie suas skills equipadas")
    async def skills(interaction: discord.Interaction):
        await cmd_skills(interaction)
    
    @bot.tree.command(name="setup", description="Configure suas skills e equipamentos")
    async def setup(interaction: discord.Interaction):
        await cmd_setup_wrapper(interaction)
    
    @bot.tree.command(name="deletar_personagem", description="Deleta seu personagem permanentemente")
    async def deletar_personagem(interaction: discord.Interaction):
        await cmd_deletar_personagem(interaction)