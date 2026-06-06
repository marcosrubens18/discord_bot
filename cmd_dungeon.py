# cmd_dungeon.py — Comandos de dungeon

import discord
from discord import app_commands

from sistema_dungeon import cmd_dungeon
from sistema_dungeon_evento import (
    DungeonEventoCriarModal, AdicionarAndarModal,
    cmd_dungeon_evento_ativar, cmd_dungeon_evento_info,
    cmd_dungeon_evento_fechar
)
from sistema_combate import BATALHAS_ATIVAS


def em_batalha(uid):
    return uid in BATALHAS_ATIVAS


# ==================================================
# COMANDO DUNGEON
# ==================================================

async def cmd_dungeon_wrapper(interaction: discord.Interaction, rank: str = "F"):
    if em_batalha(interaction.user.id):
        await interaction.response.send_message("❌ Você já está em batalha!", ephemeral=True)
        return
    await cmd_dungeon(interaction, rank)


# ==================================================
# COMANDOS DE EVENTO
# ==================================================

async def cmd_dungeon_evento_criar(interaction: discord.Interaction):
    modal = DungeonEventoCriarModal(interaction.guild)
    await interaction.response.send_modal(modal)


async def cmd_dungeon_evento_andar(interaction: discord.Interaction, dungeon_id: int, loot_item: str = ""):
    await interaction.response.send_modal(AdicionarAndarModal(dungeon_id, loot_item))


async def cmd_dungeon_evento_ativar_wrapper(interaction: discord.Interaction, dungeon_id: int):
    await cmd_dungeon_evento_ativar(interaction, dungeon_id)


async def cmd_dungeon_evento_info_wrapper(interaction: discord.Interaction, dungeon_id: int):
    await cmd_dungeon_evento_info(interaction, dungeon_id)


async def cmd_dungeon_evento_fechar_wrapper(interaction: discord.Interaction, dungeon_id: int):
    await cmd_dungeon_evento_fechar(interaction, dungeon_id)


# ==================================================
# AUTOCOMPLETE PARA LOOT ITEM
# ==================================================

async def autocomplete_loot_item(interaction: discord.Interaction, current: str):
    from data_itens import get_catalogo_completo
    
    itens = get_catalogo_completo()
    filtrado = [i for i in itens if current.lower() in i["nome"].lower() or current.lower() in i["raridade"].lower() or current.lower() in i["tipo"].lower()]
    filtrado.sort(key=lambda x: x["nome"].lower())
    
    return [
        app_commands.Choice(
            name=f"{i['emoji']} {i['nome']} [{i['raridade']}] — {i['tipo']}{' ('+i['classe']+')' if i.get('classe') else ''}"[:100],
            value=i["chave"]
        )
        for i in filtrado[:25]
    ]


# ==================================================
# REGISTRO DOS COMANDOS
# ==================================================

def setup_dungeon_commands(bot):
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
    async def dungeon(interaction: discord.Interaction, rank: str = "F"):
        await cmd_dungeon_wrapper(interaction, rank)

    @bot.tree.command(name="dungeon-evento-criar", description="[ADMIN] Cria uma dungeon de evento")
    async def dungeon_evento_criar(interaction: discord.Interaction):
        await cmd_dungeon_evento_criar(interaction)

    @bot.tree.command(name="dungeon-evento-andar", description="[ADMIN] Adiciona um andar à dungeon de evento")
    @app_commands.describe(dungeon_id="ID da dungeon", loot_item="Item que pode ser dropado (opcional)")
    @app_commands.autocomplete(loot_item=autocomplete_loot_item)
    async def dungeon_evento_andar(interaction: discord.Interaction, dungeon_id: int, loot_item: str = ""):
        await cmd_dungeon_evento_andar(interaction, dungeon_id, loot_item)

    @bot.tree.command(name="dungeon-evento-ativar", description="[ADMIN] Ativa uma dungeon de evento")
    @app_commands.describe(dungeon_id="ID da dungeon")
    async def dungeon_evento_ativar(interaction: discord.Interaction, dungeon_id: int):
        await cmd_dungeon_evento_ativar_wrapper(interaction, dungeon_id)

    @bot.tree.command(name="dungeon-evento-info", description="Mostra informações da dungeon de evento")
    @app_commands.describe(dungeon_id="ID da dungeon")
    async def dungeon_evento_info(interaction: discord.Interaction, dungeon_id: int):
        await cmd_dungeon_evento_info_wrapper(interaction, dungeon_id)

    @bot.tree.command(name="dungeon-evento-fechar", description="[ADMIN] Fecha uma dungeon de evento")
    @app_commands.describe(dungeon_id="ID da dungeon")
    async def dungeon_evento_fechar(interaction: discord.Interaction, dungeon_id: int):
        await cmd_dungeon_evento_fechar_wrapper(interaction, dungeon_id)