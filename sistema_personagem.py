# sistema_personagem.py — Sistema de personagem (criação, level up, salvamento)

import discord
import random
import asyncio

from db import get_pool
from data_racas import RACAS, RACAS_BASICAS, get_raca
from data_classes import CLASSES, PODERES, PESOS_PODER, DESTINOS, MANA_CLASSE, MANA_DESTINO
from data_skills import SKILLS_COMPLETAS, get_skill_by_id
from constants import COR_RAR, EMOJI_CLASSE
from imagens import IMG_PERFIL
from utils import atualizar_todos_cargos
from catalogo import get_rank, RANK_BONUS, calcular_mana_max


def sortear_peso(lista, pesos):
    """Sorteia um item baseado em pesos"""
    return random.choices(lista, weights=pesos, k=1)[0]


def calcular_stats(poder_valor, destino_id, nivel=1):
    """Calcula HP, ATK e DEF base do personagem"""
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
    """Cria canal privado para o jogador"""
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
    """Retorna o personagem do usuário"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM personagens WHERE user_id=$1", user_id)


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
                from sistema_eventos import registrar_level_up_evento
                await registrar_level_up_evento(user_id, levelups)
            except Exception as e:
                print(f"Erro ao registrar level up: {e}")

        rank_novo_obj = get_rank(nv)
        rank_mudou = rank_novo_obj["rank"] != rank_antes

        return levelups, nv, rank_mudou, rank_novo_obj