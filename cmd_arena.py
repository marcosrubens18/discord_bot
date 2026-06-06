# cmd_arena.py — Comandos de arena ranqueada

import discord
from discord import app_commands

from sistema_arena import (
    cmd_arena_desafiar, cmd_arena_ranking, cmd_arena_meuperfil,
    cmd_arena_recompensas, cmd_arena_temporada
)


# ==================================================
# REGISTRO DOS COMANDOS
# ==================================================

def setup_arena_commands(bot):
    @bot.tree.command(name="arena_desafiar", description="Desafia um jogador para batalha ranqueada")
    @app_commands.describe(jogador="Jogador a ser desafiado")
    async def arena_desafiar(interaction: discord.Interaction, jogador: discord.Member):
        await cmd_arena_desafiar(interaction, jogador)

    @bot.tree.command(name="arena_ranking", description="Mostra o ranking da arena")
    @app_commands.describe(elo="Filtrar por elo")
    @app_commands.choices(elo=[
        app_commands.Choice(name="Ferro", value="Ferro"),
        app_commands.Choice(name="Bronze", value="Bronze"),
        app_commands.Choice(name="Prata", value="Prata"),
        app_commands.Choice(name="Ouro", value="Ouro"),
        app_commands.Choice(name="Platina", value="Platina"),
        app_commands.Choice(name="Diamante", value="Diamante"),
        app_commands.Choice(name="Mestre", value="Mestre"),
    ])
    async def arena_ranking(interaction: discord.Interaction, elo: str = None):
        await cmd_arena_ranking(interaction, elo)

    @bot.tree.command(name="arena_meuperfil", description="Mostra seu perfil na arena")
    async def arena_meuperfil(interaction: discord.Interaction):
        await cmd_arena_meuperfil(interaction)

    @bot.tree.command(name="arena_recompensas", description="Resgata recompensas de temporadas anteriores")
    async def arena_recompensas(interaction: discord.Interaction):
        await cmd_arena_recompensas(interaction)

    @bot.tree.command(name="arena_temporada", description="Mostra informações da temporada atual")
    async def arena_temporada(interaction: discord.Interaction):
        await cmd_arena_temporada(interaction)