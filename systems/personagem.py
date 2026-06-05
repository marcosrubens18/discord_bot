# systems/personagem.py — Sistema de personagem (criação, perfil, level up)

import discord
import random
import asyncio

from database.db import get_pool
from database.queries import get_personagem, get_skills_desbloqueadas, get_skills_equipadas
from data.classes import CLASSES, PODERES, PESOS_PODER, DESTINOS, MANA_CLASSE, MANA_DESTINO
from data.racas import RACAS, RACAS_BASICAS, get_raca
from data.skills import SKILLS_COMPLETAS, get_skill_by_id
from data.ranks import get_rank, CARGOS_RANK
from data.constantes import EMOJI_CLASSE, COR_RAR, IMG_PERFIL
from utils.calculos import calcular_stats, calcular_mana_max
from utils.helpers import atualizar_todos_cargos, criar_canal_privado


def sortear_peso(lista, pesos):
    """Sorteia um item baseado em pesos"""
    return random.choices(lista, weights=pesos, k=1)[0]


async def get_personagem_db(user_id: int):
    """Alias para get_personagem"""
    return await get_personagem(user_id)


async def criar_personagem(interaction: discord.Interaction):
    """Fluxo de criação de personagem"""
    uid = interaction.user.id
    
    if await get_personagem_db(uid):
        await interaction.followup.send("Voce ja tem personagem! Use /perfil.", ephemeral=True)
        return False, None, None

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
            self.escolha = "humano"
            await inter.response.defer()
            self.stop()
        @discord.ui.button(label="Anao", style=discord.ButtonStyle.primary)
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
        return False, None, None
    
    raca = RACAS[vr.escolha]

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
        return False, None, None
    
    classe = vc.escolha

    await msg.edit(
        embed=discord.Embed(
            title="As roletas giram...",
            description=f"{raca['emoji']} {raca['nome']} + {classe['emoji']} {classe['nome']}\n\nSortindo poder, destino e skills...",
            color=0x7F77DD
        ),
        view=None
    )
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
            VALUES($1, $2, $3, $4, $5, $6, $7, $8, 1, 0, $9, $10, $11, $12, $13, $13, 50, $14)
        """, uid, nome, classe["id"], classe["raridade"], poder["id"], poder["valor"],
            destino["id"], skills_s[0]["id"] if skills_s else "",
            hp, hp, atk, dfs, mana_max, raca["id"])
        
        for i, sk in enumerate(skills_s):
            await conn.execute(
                "INSERT INTO skills_desbloqueadas(user_id, skill_id) VALUES($1, $2) ON CONFLICT DO NOTHING",
                uid, sk["id"]
            )
            await conn.execute(
                "INSERT INTO skills_equipadas(user_id, skill_id, slot) VALUES($1, $2, $3) ON CONFLICT(user_id, slot) DO UPDATE SET skill_id = EXCLUDED.skill_id",
                uid, sk["id"], i
            )

    return True, raca, classe