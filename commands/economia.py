# commands/economia.py — Comandos de economia (loja, ferreiro, mercado, mercador)

import discord
from discord import app_commands

from systems.economia.loja import cmd_loja
from systems.economia.ferreiro import cmd_ferreiro
from systems.economia.mercado import cmd_mercado_vender
from systems.economia.mercador import cmd_mercador
from loja_sazonal import cmd_loja_sazonal, cmd_loja_sazonal_remover
from utils.decorators import admin_only


def setup_economia_commands(bot):
    """Registra os comandos de economia"""

    @bot.tree.command(name="loja", description="Compre armas, armaduras e poções")
    @app_commands.describe(categoria="Categoria de item")
    @app_commands.choices(categoria=[
        app_commands.Choice(name="Armas", value="armas"),
        app_commands.Choice(name="Armaduras", value="armaduras"),
        app_commands.Choice(name="Poções", value="pocoes"),
    ])
    async def loja(interaction: discord.Interaction, categoria: str = "pocoes"):
        await cmd_loja(interaction, categoria)

    @bot.tree.command(name="ferreiro", description="Forje itens com materiais de dungeon")
    async def ferreiro(interaction: discord.Interaction):
        await cmd_ferreiro(interaction)

    @bot.tree.command(name="mercado", description="Venda itens do inventário por moedas")
    async def mercado(interaction: discord.Interaction):
        await cmd_mercado_vender(interaction)

    @bot.tree.command(name="mercador", description="Troque materiais por itens exclusivos")
    async def mercador(interaction: discord.Interaction):
        await cmd_mercador(interaction)

    @bot.tree.command(name="loja-sazonal", description="Compre itens sazonais e ofertas do dia")
    async def loja_sazonal(interaction: discord.Interaction):
        await cmd_loja_sazonal(interaction)

    @bot.tree.command(name="loja-sazonal-remover", description="[ADMIN] Remove um item da loja sazonal")
    @app_commands.describe(item_id="ID do item a remover")
    @admin_only()
    async def loja_sazonal_remover(interaction: discord.Interaction, item_id: int):
        await cmd_loja_sazonal_remover(interaction, item_id)