# cmd_sorteio.py — Comandos de sorteio

import discord
from discord import app_commands

from sistema_sorteio import (
    cmd_sorteio_criar, cmd_sorteio_sortear, cmd_sorteio_cancelar,
    cmd_sorteio_info, cmd_sorteios_listar,
    autocomplete_canal, autocomplete_item_sorteio, autocomplete_sorteio_ativo
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

def setup_sorteio_commands(bot):
    @bot.tree.command(name="sorteio_criar", description="[ADMIN] Cria um novo sorteio")
    @app_commands.describe(
        canal="Canal onde o sorteio será divulgado",
        item="Item que será sorteado (digite para buscar)",
        quantidade="Quantidade do item/moedas/XP"
    )
    @app_commands.autocomplete(canal=autocomplete_canal, item=autocomplete_item_sorteio)
    @admin_only()
    async def sorteio_criar(interaction: discord.Interaction, canal: str, item: str, quantidade: int = 1):
        await cmd_sorteio_criar(interaction, canal, item, quantidade)

    @bot.tree.command(name="sorteio_sortear", description="[ADMIN] Sorteia os vencedores manualmente")
    @app_commands.describe(sorteio_id="ID do sorteio")
    @app_commands.autocomplete(sorteio_id=autocomplete_sorteio_ativo)
    @admin_only()
    async def sorteio_sortear(interaction: discord.Interaction, sorteio_id: int):
        await cmd_sorteio_sortear(interaction, sorteio_id)

    @bot.tree.command(name="sorteio_cancelar", description="[ADMIN] Cancela um sorteio")
    @app_commands.describe(sorteio_id="ID do sorteio")
    @app_commands.autocomplete(sorteio_id=autocomplete_sorteio_ativo)
    @admin_only()
    async def sorteio_cancelar(interaction: discord.Interaction, sorteio_id: int):
        await cmd_sorteio_cancelar(interaction, sorteio_id)

    @bot.tree.command(name="sorteio_info", description="Mostra informações de um sorteio")
    @app_commands.describe(sorteio_id="ID do sorteio")
    @app_commands.autocomplete(sorteio_id=autocomplete_sorteio_ativo)
    async def sorteio_info(interaction: discord.Interaction, sorteio_id: int):
        await cmd_sorteio_info(interaction, sorteio_id)

    @bot.tree.command(name="sorteios", description="Lista todos os sorteios ativos")
    async def sorteios_listar(interaction: discord.Interaction):
        await cmd_sorteios_listar(interaction)