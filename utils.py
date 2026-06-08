# utils.py — Utilitarios compartilhados (sem imports circulares)
import discord
from catalogo import get_rank, CARGOS_RANK

# ─── CARGOS DE NIVEL E RANK ──────────────────────────────────────

async def atualizar_cargo_nivel(guild, member, nivel):
    """Atualiza cargo de nivel (Aventureiro/Veterano/Elite/Mestre)."""
    if not guild or not member:
        return
    CARGOS_NIVEL = [
        (50, "💎 Mestre"),
        (30, "🥇 Elite"),
        (15, "🥈 Veterano"),
        (5,  "🥉 Aventureiro"),
    ]
    # Remove todos os cargos de nivel
    for _, nome in CARGOS_NIVEL:
        cargo = discord.utils.get(guild.roles, name=nome)
        if cargo and cargo in member.roles:
            try:
                await member.remove_roles(cargo)
            except Exception:
                pass
    # Adiciona o correto
    for nivel_min, nome in CARGOS_NIVEL:
        if nivel >= nivel_min:
            cargo = discord.utils.get(guild.roles, name=nome)
            if cargo:
                try:
                    await member.add_roles(cargo)
                except Exception:
                    pass
            break

async def atualizar_cargo_rank(guild, member, rank_str):
    """Atualiza cargo de rank (F ao SS)."""
    if not guild or not member:
        return
    todos_ranks = [
        "🟫 Rank F", "🟩 Rank E", "🟦 Rank D", "🟨 Rank C",
        "🟧 Rank B", "🟥 Rank A", "⭐ Rank S",  "💎 Rank SS",
    ]
    # Remove todos os cargos de rank
    for nome in todos_ranks:
        cargo = discord.utils.get(guild.roles, name=nome)
        if cargo and cargo in member.roles:
            try:
                await member.remove_roles(cargo)
            except Exception:
                pass
    # Adiciona o correto
    nome_novo = CARGOS_RANK.get(rank_str)
    if nome_novo:
        cargo = discord.utils.get(guild.roles, name=nome_novo)
        if cargo:
            try:
                await member.add_roles(cargo)
            except Exception:
                pass

async def atualizar_todos_cargos(guild, member, nivel):
    """Atualiza cargo de nivel e rank de uma vez."""
    rank_obj = get_rank(nivel)
    await atualizar_cargo_nivel(guild, member, nivel)
    await atualizar_cargo_rank(guild, member, rank_obj["rank"])
    return rank_obj
