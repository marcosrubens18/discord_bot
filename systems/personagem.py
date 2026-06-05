# systems/personagem.py — Sistema de personagem (criação, perfil, level up)

import discord
import random
import asyncio

from database.db import get_pool
from database.queries import get_personagem, get_skills_desbloqueadas, get_skills_equipadas
from data.classes import CLASSES, PODERES, PESOS_PODER, DESTINOS, MANA_CLASSE, MANA_DESTINO
from data.racas import RACAS, RACAS_BASICAS, get_raca
from data.skills import SKILLS_COMPLETAS, get_skill_by_id
from data.ranks import get_rank, RANK_BONUS
from data.constantes import EMOJI_CLASSE, COR_RAR, IMG_PERFIL
from utils.calculos import calcular_stats, calcular_mana_max
from utils.helpers import atualizar_todos_cargos, criar_canal_privado


def sortear_peso(lista, pesos):
    """Sorteia um item baseado em pesos"""
    return random.choices(lista, weights=pesos, k=1)[0]


async def criar_personagem(interaction: discord.Interaction):
    """Fluxo de criação de personagem"""
    uid = interaction.user.id
    
    if await get_personagem(uid):
        await interaction.followup.send("Você já tem personagem! Use /perfil.", ephemeral=True)
        return False, None, None

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
        return False, None, None
    
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


# ==================================================
# SALVAR RESULTADO DE BATALHA
# ==================================================

async def salvar_resultado(user_id, hp, xp_ganho, moedas_ganhas, vitoria, classe_id, nivel_atual, mana_atual_batalha=None):
    """Salva o resultado de uma batalha (XP, moedas, level up)"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        p = await conn.fetchrow(
            "SELECT xp, nivel, hp_max, hp_atual, ataque, defesa, mana_max, mana_atual, poder_valor, destino_id, raca_id FROM personagens WHERE user_id=$1",
            user_id
        )
        if not p:
            return 0, nivel_atual, False, None

        # Bônus de XP por raça
        _raca = get_raca(p.get("raca_id", "humano"))
        _bonus_xp = _raca.get("bonus_xp", 0.0) if isinstance(_raca, dict) else 0.0
        _bonus_moedas = _raca.get("bonus_moedas", 0.0) if isinstance(_raca, dict) else 0.0
        
        xp_ganho = int(xp_ganho * (1.0 + _bonus_xp))
        moedas_ganhas = int(moedas_ganhas * (1.0 + _bonus_moedas))
        
        novo_xp = p["xp"] + xp_ganho
        nv = p["nivel"]
        levelups = 0
        rank_antes = get_rank(nv)["rank"]

        needed = 100 + (nv - 1) * 50
        while novo_xp >= needed:
            novo_xp -= needed
            nv += 1
            needed = 100 + (nv - 1) * 50
            levelups += 1

        hp_max_novo = p["hp_max"] + levelups * 6
        atk_novo = p["ataque"] + levelups * 2
        dfs_novo = p["defesa"] + levelups * 1

        rank_bonus_hp = rank_bonus_mana = rank_bonus_atk = rank_bonus_dfs = 0
        if rank_antes != get_rank(nv)["rank"]:
            novo_rank = get_rank(nv)["rank"]
            bonus = RANK_BONUS.get(novo_rank, {})
            rank_bonus_hp = bonus.get("hp", 0)
            rank_bonus_mana = bonus.get("mana", 0)
            rank_bonus_atk = bonus.get("atk", 0)
            rank_bonus_dfs = bonus.get("dfs", 0)
            hp_max_novo += rank_bonus_hp
            atk_novo += rank_bonus_atk
            dfs_novo += rank_bonus_dfs
            
        mana_max_novo = calcular_mana_max(classe_id, nv, p["poder_valor"], p["destino_id"]) + rank_bonus_mana
        hp_final = max(1, min(hp, hp_max_novo))

        mana_base = int(mana_atual_batalha) if mana_atual_batalha is not None else p["mana_atual"]
        mana_salvar = max(0, min(mana_base + levelups * 10, mana_max_novo))

        await conn.execute("""
            UPDATE personagens
            SET hp_atual=$1, hp_max=$2, xp=$3, nivel=$4,
                ataque=$5, defesa=$6, mana_max=$7, mana_atual=$8,
                moedas=moedas+$9, vitorias=vitorias+$10, derrotas=derrotas+$11
            WHERE user_id=$12
        """,
            hp_final, hp_max_novo, novo_xp, nv,
            atk_novo, dfs_novo, mana_max_novo, mana_salvar,
            moedas_ganhas,
            1 if vitoria else 0,
            0 if vitoria else 1,
            user_id
        )

        # Desbloqueia skills pelo novo nível
        for s in SKILLS_COMPLETAS.get(classe_id, []):
            if s["nivel"] <= nv:
                await conn.execute(
                    "INSERT INTO skills_desbloqueadas(user_id, skill_id) VALUES($1,$2) ON CONFLICT DO NOTHING",
                    user_id, s["id"]
                )

        # Registra level up no evento
        if levelups > 0:
            try:
                from systems.eventos import registrar_level_up_evento
                await registrar_level_up_evento(user_id, levelups)
            except Exception as e:
                print(f"Erro ao registrar level up: {e}")

        rank_novo_obj = get_rank(nv)
        rank_mudou = rank_novo_obj["rank"] != rank_antes

        return levelups, nv, rank_mudou, rank_novo_obj
