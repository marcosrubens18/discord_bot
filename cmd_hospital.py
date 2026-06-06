# cmd_hospital.py — Comando do hospital

import discord
from discord import app_commands

from sistema_hospital import cmd_hospital


# ==================================================
# REGISTRO DO COMANDO
# ==================================================

def setup_hospital_commands(bot):
    @bot.tree.command(name="hospital", description="Restaure seu HP e Mana no hospital")
    async def hospital(interaction: discord.Interaction):
        await cmd_hospital(interaction)