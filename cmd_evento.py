# cmd_evento.py — Comandos de eventos

import discord
from discord import app_commands

from sistema_eventos import (
    cmd_criar_evento, cmd_eventos, cmd_evento_info,
    cmd_encerrar_evento, cmd_add_pontos
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


def resolver_canal(guild, canal):
    if canal is None:
        return None
    if hasattr(canal, 'id'):
        return guild.get_channel(canal.id) or canal
    canal_str = str(canal)
    if canal_str.isdigit():
        return guild.get_channel(int(canal_str))
    return discord.utils.get(guild.channels, name=canal_str.lstrip('#'))


async def autocomplete_canal(interaction: discord.Interaction, current: str):
    if not interaction.guild:
        return []
    canais = [
        ch for ch in interaction.guild.channels
        if isinstance(ch, (discord.TextChannel, discord.ForumChannel))
        and (not current or current.lower() in ch.name.lower())
    ]
    canais.sort(key=lambda ch: ch.name)
    return [
        app_commands.Choice(name=f"#{ch.name}", value=str(ch.id))
        for ch in canais[:25]
    ]


async def autocomplete_item_premio(interaction: discord.Interaction, current: str):
    try:
        premio_tipo = str(interaction.namespace.premio_tipo or "")
    except:
        premio_tipo = ""
    
    if premio_tipo == "item":
        from data_itens import get_catalogo_completo
        itens = get_catalogo_completo()
        filtrado = [i for i in itens if current.lower() in i["nome"].lower() or not current]
        filtrado.sort(key=lambda x: x["nome"].lower())
        return [
            app_commands.Choice(
                name=f"{i['emoji']} {i['nome']} [{i['raridade']}]"[:100],
                value=f"{i['id']}|{i['nome']}|{i['tipo']}|{i['raridade']}|{i['emoji']}|{i.get('desc', '').replace('|', ' ')}"[:100]
            )
            for i in filtrado[:25]
        ]
    elif premio_tipo == "moedas":
        exemplos = ["1000", "2000", "5000", "10000", "20000", "50000"]
        return [app_commands.Choice(name=f"{v} moedas", value=v) for v in exemplos if current in v]
    elif premio_tipo == "xp":
        exemplos = ["500", "1000", "2000", "5000", "10000"]
        return [app_commands.Choice(name=f"{v} XP", value=v) for v in exemplos if current in v]
    elif premio_tipo == "ficha":
        exemplos = ["1", "2", "3", "5", "10"]
        return [app_commands.Choice(name=f"{v} ficha(s)", value=v) for v in exemplos if current in v]
    elif premio_tipo == "cargo":
        return [app_commands.Choice(name="Nome do cargo (ex: Campeão)", value=current or "Campeão")]
    elif premio_tipo == "classe":
        classes = ["guerreiro", "arqueiro", "mago", "paladino", "necromante", "dracomante", "arcano"]
        EMOJI_CLS = {"guerreiro": "🗡️", "arqueiro": "🏹", "mago": "🔮", "paladino": "⚡", "necromante": "🌑", "dracomante": "🐉", "arcano": "✨"}
        return [app_commands.Choice(name=f"{EMOJI_CLS[cl]} {cl.title()}", value=cl) for cl in classes if current.lower() in cl]
    
    return [app_commands.Choice(name=current or "Digite o valor do prêmio", value=current or "")]


# ==================================================
# REGISTRO DOS COMANDOS
# ==================================================

def setup_evento_commands(bot):
    @bot.tree.command(name="criar-evento", description="[ADMIN] Cria um novo evento no servidor")
    @app_commands.describe(
        tipo="Tipo do evento",
        premio_tipo="Tipo de prêmio",
        premio_valor="Valor do prêmio",
        canal="Canal onde o evento será anunciado"
    )
    @app_commands.choices(tipo=[
        app_commands.Choice(name="Torneio de Batalha", value="batalha"),
        app_commands.Choice(name="Corrida de Dungeon", value="dungeon"),
        app_commands.Choice(name="Coleta de Materiais", value="coleta"),
        app_commands.Choice(name="Corrida de Nível", value="nivel"),
        app_commands.Choice(name="Evento Livre", value="livre"),
    ])
    @app_commands.choices(premio_tipo=[
        app_commands.Choice(name="Moedas", value="moedas"),
        app_commands.Choice(name="XP", value="xp"),
        app_commands.Choice(name="Fichas de Roleta", value="ficha"),
        app_commands.Choice(name="Item específico", value="item"),
        app_commands.Choice(name="Cargo exclusivo", value="cargo"),
        app_commands.Choice(name="Classe especial", value="classe"),
    ])
    @app_commands.autocomplete(premio_valor=autocomplete_item_premio, canal=autocomplete_canal)
    @admin_only()
    async def criar_evento(interaction: discord.Interaction, tipo: str, premio_tipo: str, premio_valor: str, canal: str):
        canal_obj = resolver_canal(interaction.guild, canal)
        if not canal_obj:
            await interaction.response.send_message('❌ Canal não encontrado!', ephemeral=True)
            return
        await cmd_criar_evento(interaction, tipo, premio_tipo, premio_valor, canal_obj)

    @bot.tree.command(name="eventos", description="Lista os eventos ativos no servidor")
    async def eventos(interaction: discord.Interaction):
        await cmd_eventos(interaction)

    @bot.tree.command(name="evento-info", description="Detalhes de um evento e ranking de participantes")
    @app_commands.describe(evento_id="ID do evento (0 = evento ativo atual)")
    async def evento_info(interaction: discord.Interaction, evento_id: int = 0):
        await cmd_evento_info(interaction, evento_id)

    @bot.tree.command(name="encerrar-evento", description="[ADMIN] Encerra evento e entrega prêmio ao 1º lugar")
    @app_commands.describe(evento_id="ID do evento a encerrar")
    @admin_only()
    async def encerrar_evento(interaction: discord.Interaction, evento_id: int):
        await cmd_encerrar_evento(interaction, evento_id)

    @bot.tree.command(name="add-pontos", description="[ADMIN] Adiciona pontos a um participante do evento")
    @app_commands.describe(jogador="Jogador alvo", pontos="Pontos a adicionar", evento_id="ID do evento (0 = atual)")
    @admin_only()
    async def add_pontos(interaction: discord.Interaction, jogador: discord.Member, pontos: int, evento_id: int = 0):
        await cmd_add_pontos(interaction, jogador, pontos, evento_id)