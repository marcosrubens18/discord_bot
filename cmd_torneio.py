# cmd_torneio.py — Comandos de torneio

import discord
from discord import app_commands

from sistema_torneio import (
    cmd_torneio_criar, cmd_torneio_inscrever, cmd_torneio_fechar,
    cmd_torneio_lutar, cmd_torneio_status, cmd_torneio_cancelar
)


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

def setup_torneio_commands(bot):
    @bot.tree.command(name="torneio_criar", description="[ADMIN] Cria um novo torneio")
    @admin_only()
    async def torneio_criar(interaction: discord.Interaction):
        await cmd_torneio_criar(interaction)

    @bot.tree.command(name="torneio_inscrever", description="Inscreve seu personagem no torneio")
    @app_commands.describe(torneio_id="ID do torneio")
    async def torneio_inscrever(interaction: discord.Interaction, torneio_id: int):
        await cmd_torneio_inscrever(interaction, torneio_id)

    @bot.tree.command(name="torneio_fechar", description="[ADMIN] Encerra inscrições e gera chaves")
    @app_commands.describe(torneio_id="ID do torneio")
    @admin_only()
    async def torneio_fechar(interaction: discord.Interaction, torneio_id: int):
        await cmd_torneio_fechar(interaction, torneio_id)

    @bot.tree.command(name="torneio_lutar", description="[ADMIN] Inicia uma luta do torneio")
    @app_commands.describe(torneio_id="ID do torneio", luta_num="Número da luta")
    @admin_only()
    async def torneio_lutar(interaction: discord.Interaction, torneio_id: int, luta_num: int):
        await cmd_torneio_lutar(interaction, torneio_id, luta_num)

    @bot.tree.command(name="torneio_status", description="Mostra status do torneio")
    @app_commands.describe(torneio_id="ID do torneio")
    async def torneio_status(interaction: discord.Interaction, torneio_id: int):
        await cmd_torneio_status(interaction, torneio_id)

    @bot.tree.command(name="torneio_cancelar", description="[ADMIN] Cancela um torneio")
    @app_commands.describe(torneio_id="ID do torneio")
    @admin_only()
    async def torneio_cancelar(interaction: discord.Interaction, torneio_id: int):
        await cmd_torneio_cancelar(interaction, torneio_id)