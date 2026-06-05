# commands/social.py — Comandos sociais (guildas, party)

import discord
from discord import app_commands

from systems.social.guildas import (
    cmd_guilda_criar, cmd_guilda_info, cmd_guilda_convidar, cmd_guilda_sair,
    cmd_guilda_expulsar, cmd_guilda_promover, cmd_guilda_depositar, cmd_guilda_retirar,
    cmd_guilda_ranking, cmd_guilda_missoes
)
from systems.social.party import (
    cmd_party_criar, cmd_party_info, cmd_party_convidar, cmd_party_sair,
    cmd_party_expulsar, cmd_party_lider, cmd_party_encerrar, cmd_party_painel, cmd_party_convites
)


def setup_social_commands(bot):
    """Registra os comandos sociais"""

    # ==================================================
    # COMANDOS DE GUILDA
    # ==================================================

    @bot.tree.command(name="guilda-criar", description="Cria uma nova guilda (custa 5000 moedas)")
    async def guilda_criar(interaction: discord.Interaction):
        await cmd_guilda_criar(interaction)

    @bot.tree.command(name="guilda-info", description="Mostra informações da sua guilda")
    @app_commands.describe(nome="Nome da guilda (opcional)")
    async def guilda_info(interaction: discord.Interaction, nome: str = ""):
        await cmd_guilda_info(interaction, nome)

    @bot.tree.command(name="guilda-convidar", description="Convida um jogador para sua guilda")
    @app_commands.describe(jogador="Jogador a ser convidado")
    async def guilda_convidar(interaction: discord.Interaction, jogador: discord.Member):
        await cmd_guilda_convidar(interaction, jogador)

    @bot.tree.command(name="guilda-sair", description="Sai da sua guilda atual")
    async def guilda_sair(interaction: discord.Interaction):
        await cmd_guilda_sair(interaction)

    @bot.tree.command(name="guilda-expulsar", description="Expulsa um membro da guilda (apenas mestre)")
    @app_commands.describe(jogador="Membro a ser expulso")
    async def guilda_expulsar(interaction: discord.Interaction, jogador: discord.Member):
        await cmd_guilda_expulsar(interaction, jogador)

    @bot.tree.command(name="guilda-promover", description="Promove um membro da guilda (apenas mestre)")
    @app_commands.describe(jogador="Membro a ser promovido")
    async def guilda_promover(interaction: discord.Interaction, jogador: discord.Member):
        await cmd_guilda_promover(interaction, jogador)

    @bot.tree.command(name="guilda-depositar", description="Deposita moedas no banco da guilda")
    @app_commands.describe(valor="Quantidade de moedas")
    async def guilda_depositar(interaction: discord.Interaction, valor: int):
        await cmd_guilda_depositar(interaction, valor)

    @bot.tree.command(name="guilda-retirar", description="Retira moedas do banco da guilda (apenas mestre)")
    @app_commands.describe(valor="Quantidade de moedas")
    async def guilda_retirar(interaction: discord.Interaction, valor: int):
        await cmd_guilda_retirar(interaction, valor)

    @bot.tree.command(name="guilda-ranking", description="Ranking de guildas do servidor")
    async def guilda_ranking(interaction: discord.Interaction):
        await cmd_guilda_ranking(interaction)

    @bot.tree.command(name="guilda-missoes", description="Mostra as missões semanais da guilda")
    async def guilda_missoes(interaction: discord.Interaction):
        await cmd_guilda_missoes(interaction)

    # ==================================================
    # COMANDOS DE PARTY
    # ==================================================

    @bot.tree.command(name="party-criar", description="Cria uma nova party")
    async def party_criar(interaction: discord.Interaction):
        await cmd_party_criar(interaction)

    @bot.tree.command(name="party-info", description="Mostra informações da sua party")
    async def party_info(interaction: discord.Interaction):
        await cmd_party_info(interaction)

    @bot.tree.command(name="party-convidar", description="Convida um jogador para sua party")
    @app_commands.describe(jogador="Jogador a ser convidado")
    async def party_convidar(interaction: discord.Interaction, jogador: discord.Member):
        await cmd_party_convidar(interaction, jogador)

    @bot.tree.command(name="party-sair", description="Sai da sua party atual")
    async def party_sair(interaction: discord.Interaction):
        await cmd_party_sair(interaction)

    @bot.tree.command(name="party-expulsar", description="Expulsa um membro da party (apenas líder)")
    @app_commands.describe(jogador="Membro a ser expulso")
    async def party_expulsar(interaction: discord.Interaction, jogador: discord.Member):
        await cmd_party_expulsar(interaction, jogador)

    @bot.tree.command(name="party-lider", description="Transfere a liderança da party")
    @app_commands.describe(jogador="Novo líder")
    async def party_lider(interaction: discord.Interaction, jogador: discord.Member):
        await cmd_party_lider(interaction, jogador)

    @bot.tree.command(name="party-encerrar", description="Encerra sua party permanentemente (apenas líder)")
    async def party_encerrar(interaction: discord.Interaction):
        await cmd_party_encerrar(interaction)

    @bot.tree.command(name="party-painel", description="Mostra o painel completo da party")
    async def party_painel(interaction: discord.Interaction):
        await cmd_party_painel(interaction)

    @bot.tree.command(name="party-convites", description="Lista os convites pendentes da party")
    async def party_convites(interaction: discord.Interaction):
        await cmd_party_convites(interaction)