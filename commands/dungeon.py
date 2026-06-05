# commands/dungeon.py — Comandos de dungeon

import discord
from discord import app_commands

from systems.dungeon import cmd_dungeon
from systems.dungeon_evento import (
    DungeonEventoCriarModal, AdicionarAndarModal,
    cmd_dungeon_evento_ativar, cmd_dungeon_evento_info,
    cmd_dungeon_evento_fechar
)
from utils.decorators import admin_only, em_batalha_guard


def setup_dungeon_commands(bot):
    """Registra os comandos de dungeon"""

    @bot.tree.command(name="dungeon", description="Entre em uma dungeon! Se morrer, perde tudo")
    @app_commands.describe(rank="Rank da dungeon")
    @app_commands.choices(rank=[
        app_commands.Choice(name="Rank F (Nv 1+)", value="F"),
        app_commands.Choice(name="Rank E (Nv 10+)", value="E"),
        app_commands.Choice(name="Rank D (Nv 20+)", value="D"),
        app_commands.Choice(name="Rank C (Nv 30+)", value="C"),
        app_commands.Choice(name="Rank B (Nv 40+)", value="B"),
        app_commands.Choice(name="Rank A (Nv 50+)", value="A"),
        app_commands.Choice(name="Rank S (Nv 60+)", value="S"),
        app_commands.Choice(name="Rank SS (Nv 75+)", value="SS"),
    ])
    @em_batalha_guard()
    async def dungeon(interaction: discord.Interaction, rank: str = "F"):
        await cmd_dungeon(interaction, rank)

    @bot.tree.command(name="dungeon-evento-criar", description="[ADMIN] Cria uma dungeon de evento")
    @admin_only()
    async def dungeon_evento_criar(interaction: discord.Interaction):
        modal = DungeonEventoCriarModal(interaction.guild)
        await interaction.response.send_modal(modal)

    @bot.tree.command(name="dungeon-evento-andar", description="[ADMIN] Adiciona um andar à dungeon de evento")
    @app_commands.describe(dungeon_id="ID da dungeon", loot_item="Item que pode ser dropado (opcional)")
    @app_commands.autocomplete(loot_item=autocomplete_item_todos)
    @admin_only()
    async def dungeon_evento_andar(interaction: discord.Interaction, dungeon_id: int, loot_item: str = ""):
        await interaction.response.send_modal(AdicionarAndarModal(dungeon_id, loot_item))

    @bot.tree.command(name="dungeon-evento-ativar", description="[ADMIN] Ativa uma dungeon de evento")
    @app_commands.describe(dungeon_id="ID da dungeon")
    @admin_only()
    async def dungeon_evento_ativar(interaction: discord.Interaction, dungeon_id: int):
        await cmd_dungeon_evento_ativar(interaction, dungeon_id)

    @bot.tree.command(name="dungeon-evento-info", description="Mostra informações da dungeon de evento")
    @app_commands.describe(dungeon_id="ID da dungeon")
    async def dungeon_evento_info(interaction: discord.Interaction, dungeon_id: int):
        await cmd_dungeon_evento_info(interaction, dungeon_id)

    @bot.tree.command(name="dungeon-evento-fechar", description="[ADMIN] Fecha uma dungeon de evento")
    @app_commands.describe(dungeon_id="ID da dungeon")
    @admin_only()
    async def dungeon_evento_fechar(interaction: discord.Interaction, dungeon_id: int):
        await cmd_dungeon_evento_fechar(interaction, dungeon_id)


# Import necessário para autocomplete
from commands.autocomplete import autocomplete_item_todos
