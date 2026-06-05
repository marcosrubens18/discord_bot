# commands/competitivo.py — Comandos de arena e torneio

import discord
from discord import app_commands

from systems.arena import (
    cmd_arena_desafiar, cmd_arena_ranking, cmd_arena_meuperfil,
    cmd_arena_recompensas, cmd_arena_temporada
)
from systems.torneio import (
    cmd_torneio_criar, cmd_torneio_inscrever, cmd_torneio_fechar,
    cmd_torneio_lutar, cmd_torneio_status, cmd_torneio_cancelar,
    autocomplete_torneio_ativo
)
from utils.decorators import admin_only


def setup_competitivo_commands(bot):
    """Registra os comandos de arena e torneio"""

    # ==================================================
    # COMANDOS DE ARENA
    # ==================================================

    @bot.tree.command(name="arena_desafiar", description="Desafia um jogador para batalha ranqueada")
    @app_commands.describe(jogador="Jogador a ser desafiado")
    async def arena_desafiar(interaction: discord.Interaction, jogador: discord.Member):
        await cmd_arena_desafiar(interaction, jogador)

    @bot.tree.command(name="arena_ranking", description="Mostra o ranking da arena")
    @app_commands.describe(elo="Filtrar por elo")
    @app_commands.choices(elo=[
        app_commands.Choice(name="Ferro", value="Ferro"),
        app_commands.Choice(name="Bronze", value="Bronze"),
        app_commands.Choice(name="Prata", value="Prata"),
        app_commands.Choice(name="Ouro", value="Ouro"),
        app_commands.Choice(name="Platina", value="Platina"),
        app_commands.Choice(name="Diamante", value="Diamante"),
        app_commands.Choice(name="Mestre", value="Mestre"),
    ])
    async def arena_ranking(interaction: discord.Interaction, elo: str = None):
        await cmd_arena_ranking(interaction, elo)

    @bot.tree.command(name="arena_meuperfil", description="Mostra seu perfil na arena")
    async def arena_meuperfil(interaction: discord.Interaction):
        await cmd_arena_meuperfil(interaction)

    @bot.tree.command(name="arena_recompensas", description="Resgata recompensas de temporadas anteriores")
    async def arena_recompensas(interaction: discord.Interaction):
        await cmd_arena_recompensas(interaction)

    @bot.tree.command(name="arena_temporada", description="Mostra informações da temporada atual")
    async def arena_temporada(interaction: discord.Interaction):
        await cmd_arena_temporada(interaction)

    # ==================================================
    # COMANDOS DE TORNEIO
    # ==================================================

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