# commands/hospital.py — Comando do hospital

import discord
from discord import app_commands

from systems.hospital import cmd_hospital


def setup_hospital_commands(bot):
    """Registra o comando do hospital"""

    @bot.tree.command(name="hospital", description="Restaure seu HP e Mana no hospital")
    async def hospital(interaction: discord.Interaction):
        await cmd_hospital(interaction)