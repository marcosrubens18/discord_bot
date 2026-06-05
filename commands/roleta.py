# commands/roleta.py — Comandos de roleta e giros

import discord
from discord import app_commands

from systems.roleta import cmd_girar, cmd_set_giros
from utils.decorators import admin_only


def setup_roleta_commands(bot):
    """Registra os comandos de roleta"""

    @bot.tree.command(name="girar", description="Use fichas de roleta para ganhar itens raros")
    async def girar(interaction: discord.Interaction):
        await cmd_girar(interaction)

    @bot.tree.command(name="set-giros", description="[ADMIN] Adiciona fichas de roleta a um jogador")
    @app_commands.describe(jogador="Jogador que receberá as fichas")
    @admin_only()
    async def set_giros(interaction: discord.Interaction, jogador: discord.Member):
        await cmd_set_giros(interaction, jogador)