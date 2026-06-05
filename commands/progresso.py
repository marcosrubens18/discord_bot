# commands/progresso.py — Comandos de progresso (missões, conquistas, ranking, eventos, passe)

import discord
from discord import app_commands

from systems.missoes import cmd_missoes, cmd_ranking
from systems.conquistas import cmd_conquistas
from systems.eventos import cmd_eventos, cmd_evento_info
from systems.passe import (
    cmd_passe_ver, cmd_passe_resgatar, cmd_passe_ranking, cmd_passe_recompensas,
    autocomplete_nivel
)


def setup_progresso_commands(bot):
    """Registra os comandos de progresso"""

    @bot.tree.command(name="missoes", description="Veja e complete suas missões diárias")
    async def missoes(interaction: discord.Interaction):
        await cmd_missoes(interaction)

    @bot.tree.command(name="ranking", description="Top 10 jogadores do servidor")
    async def ranking(interaction: discord.Interaction):
        await cmd_ranking(interaction)

    @bot.tree.command(name="conquistas", description="Veja suas conquistas e progresso")
    async def conquistas(interaction: discord.Interaction):
        await cmd_conquistas(interaction)

    @bot.tree.command(name="eventos", description="Lista os eventos ativos no servidor")
    async def eventos(interaction: discord.Interaction):
        await cmd_eventos(interaction)

    @bot.tree.command(name="evento-info", description="Detalhes de um evento e ranking de participantes")
    @app_commands.describe(evento_id="ID do evento (0 = evento ativo atual)")
    async def evento_info(interaction: discord.Interaction, evento_id: int = 0):
        await cmd_evento_info(interaction, evento_id)

    # ==================================================
    # COMANDOS DO PASSE
    # ==================================================

    @bot.tree.command(name="passe_ver", description="Mostra seu progresso no passe")
    async def passe_ver(interaction: discord.Interaction):
        await cmd_passe_ver(interaction)

    @bot.tree.command(name="passe_resgatar", description="Resgata uma recompensa do passe")
    @app_commands.describe(nivel="Nível da recompensa")
    @app_commands.autocomplete(nivel=autocomplete_nivel)
    async def passe_resgatar(interaction: discord.Interaction, nivel: int):
        await cmd_passe_resgatar(interaction, nivel)

    @bot.tree.command(name="passe_ranking", description="Ranking do passe")
    async def passe_ranking(interaction: discord.Interaction):
        await cmd_passe_ranking(interaction)

    @bot.tree.command(name="passe_recompensas", description="Lista todas as recompensas")
    async def passe_recompensas(interaction: discord.Interaction):
        await cmd_passe_recompensas(interaction)