# commands/roleta.py — Comandos de roleta e giros

import discord
from discord import app_commands

from systems.roleta import cmd_girar
from utils.decorators import admin_only


def setup_roleta_commands(bot):
    """Registra os comandos de roleta"""

    @bot.tree.command(name="girar", description="Use fichas de roleta para ganhar itens raros")
    async def girar(interaction: discord.Interaction):
        await cmd_girar(interaction)
