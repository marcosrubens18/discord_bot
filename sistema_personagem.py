# sistema_personagem.py — Sistema de personagem (criação, level up, salvamento)

import discord
import random
import asyncio

from db import get_pool
from data_racas import RACAS, RACAS_BASICAS, get_raca
from data_classes import CLASSES, PODERES, PESOS_PODER, DESTINOS
from data_skills import SKILLS_COMPLETAS
from constants import COR_RAR, EMOJI_CLASSE, RANK_BONUS
from imagens import IMG_PERFIL
from utils import atualizar_todos_cargos
from data_ranks import get_rank


# ==================================================
# CÁLCULO DE MANA
# ==================================================

MANA_CLASSE = {
    "guerreiro": {"base": 105, "mult_nivel": 10, "mult_poder": 0.3},
    "arqueiro": {"base": 105, "mult_nivel": 11, "mult_poder": 0.3},
    "mago": {"base": 120, "mult_nivel": 15, "mult_poder": 0.6},
    "paladino": {"base": 110, "mult_nivel": 12, "mult_poder": 0.4},
    "necromante": {"base": 115, "mult_nivel": 13, "mult_poder": 0.5},
    "dracomante": {"base": 115, "mult_nivel": 11, "mult_poder": 0.4},
    "arcano": {"base": 125, "mult_nivel": 16, "mult_poder": 0.7},
}

MANA_DESTINO = {
    "equilibrado": 1.00,
    "prodigio": 0.85,
    "maldito": 0.70,
    "guardiao": 1.10,
    "abencado": 1.15,
    "amaldicoado": 1.00,
    "filho_caos": 1.20,
}


def calcular_mana_max(classe_id, nivel, poder_valor, destino_id):
    cfg = MANA_CLASSE.get(classe_id, {"base": 100, "mult_nivel": 10, "mult_poder": 0.4})
    base = cfg["base"] + (nivel - 1) * cfg["mult_nivel"] + poder_valor * cfg["mult_poder"]
    mult = MANA_DESTINO.get(destino_id, 1.0)
    return max(100, int(base * mult))


# ==================================================
# FUNÇÕES AUXILIARES
# ==================================================

def sortear_peso(lista, pesos):
    return random.choices(lista, weights=pesos, k=1)[0]


def calcular_stats(poder_valor, destino_id, nivel=1):
    hp = 90 + poder_valor * 2 + nivel * 6
    atk = 9 + poder_valor // 5 + nivel * 2
    dfs = 6 + poder_valor // 7 + nivel * 1
    
    if destino_id == "prodigio":
        atk = int(atk * 1.12)
        dfs = int(dfs * 0.95)
    elif destino_id == "guardiao":
        dfs = int(dfs * 1.12)
        atk = int(atk * 0.95)
    elif destino_id == "abencado":
        hp = int(hp * 1.08)
        atk = int(atk * 1.05)
        dfs = int(dfs * 1.05)
    elif destino_id == "maldito":
        atk = int(atk * 0.85)
        dfs = int(dfs * 0.85)
    elif destino_id == "amaldicoado":
        atk = random.randint(5, atk + 5)
        dfs = random.randint(3, dfs + 3)
    
    return hp, atk, dfs


async def criar_canal_privado(guild, member, nome, classe):
    try:
        cat = (discord.utils.get(guild.categories, name="MEU PERFIL") or
               discord.utils.get(guild.categories, name="Meu Perfil") or
               discord.utils.get(guild.categories, name="PERFIL") or
               discord.utils.get(guild.categories, name="perfil"))
        if not cat:
            cat = await guild.create_category("MEU PERFIL")
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }
        nome_canal = f"{classe['emoji']}│{nome.lower()[:20]}"
        canal = await guild.create_text_channel(nome_canal, category=cat, overwrites=overwrites)
        cor = COR_RAR.get(classe.get("raridade", "Comum"), 0x7F77DD)
        await canal.send(content=member.mention)
        return canal
    except Exception as e:
        print(f"Erro ao criar canal privado: {e}")
        return None


async def get_personagem(user_id):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM personagens WHERE user_id=$1", user_id)


async def add_loot(user_id, loot):
    pool = await get_pool()
    async with pool.acquire() as conn:
        for it in loot:
            iid, nome, tipo, rar, emoji, desc = it
            ex = await conn.fetchrow(
                "SELECT id, quantidade FROM inventario WHERE user_id=$1 AND item_id=$2",
                user_id, iid
            )
            if ex:
                await conn.execute(
                    "UPDATE inventario SET quantidade = quantidade + 1 WHERE id = $1",
                    ex["id"]
                )
            else:
                await conn.execute(
                    "INSERT INTO inventario(user_id, item_id, nome, tipo, raridade, emoji, descricao) VALUES($1,$2,$3,$4,$5,$6,$7)",
                    user_id, iid, nome, tipo, rar, emoji, desc
                )


async def salvar_resultado(user_id, hp, xp_ganho, moedas_ganhas, vitoria, classe_id, nivel_atual, mana_atual_batalha=None):
    pool = await get_pool()
    async with pool.acquire() as conn:
        p = await conn.fetchrow(
            "SELECT xp, nivel, hp_max, hp_atual, ataque, defesa, mana_max, mana_atual, poder_valor, destino_id, raca_id FROM personagens WHERE user_id=$1",
            user_id
        )
        if not p:
            return 0, nivel_atual, False, None

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

        for s in SKILLS_COMPLETAS.get(classe_id, []):
            if s["nivel"] <= nv:
                await conn.execute(
                    "INSERT INTO skills_desbloqueadas(user_id, skill_id) VALUES($1,$2) ON CONFLICT DO NOTHING",
                    user_id, s["id"]
                )

        if levelups > 0:
            try:
                from sistema_eventos import registrar_level_up_evento
                await registrar_level_up_evento(user_id, levelups)
            except Exception as e:
                print(f"Erro ao registrar level up: {e}")

        rank_novo_obj = get_rank(nv)
        rank_mudou = rank_novo_obj["rank"] != rank_antes

        return levelups, nv, rank_mudou, rank_novo_obj
