# cmd_roleta.py — Comandos de roleta e giros

import discord
from discord import app_commands

from sistema_roleta import cmd_girar, cmd_set_giros
from sistema_personagem import get_personagem


def admin_only():
    def decorator(func):
        async def wrapper(interaction: discord.Interaction, *args, **kwargs):
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message(
                    "❌ Apenas administradores podem usar este comando!",
                    ephemeral=True
                )
                return
            return await func(interaction, *args, **kwargs)
        return wrapper
    return decorator


# ==================================================
# REGISTRO DOS COMANDOS
# ==================================================

def setup_roleta_commands(bot):
    @bot.tree.command(name="girar", description="Use fichas de roleta para ganhar itens raros")
    async def girar(interaction: discord.Interaction):
        await cmd_girar(interaction)

    @bot.tree.command(name="set-giros", description="[ADMIN] Adiciona fichas de roleta a um jogador")
    @app_commands.describe(jogador="Jogador que receberá as fichas")
    @admin_only()
    async def set_giros(interaction: discord.Interaction, jogador: discord.Member):
        await cmd_set_giros(interaction, jogador)