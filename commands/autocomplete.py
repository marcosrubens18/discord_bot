# commands/autocomplete.py — Funções de autocomplete para comandos

from discord import app_commands
from catalogo import get_catalogo_completo, get_itens_por_categoria


async def autocomplete_item_categoria(interaction: discord.Interaction, current: str):
    try:
        categoria = str(interaction.namespace.categoria or "")
    except:
        categoria = ""
    itens = get_itens_por_categoria(categoria) if categoria else get_catalogo_completo()
    filtrado = [i for i in itens if current.lower() in i["nome"].lower() or current.lower() in i["raridade"].lower()]
    return [
        app_commands.Choice(
            name=f"{i['emoji']} {i['nome']} [{i['raridade']}]"[:100],
            value=i["chave"]
        )
        for i in filtrado[:25]
    ]


async def autocomplete_item_todos(interaction: discord.Interaction, current: str):
    itens = get_catalogo_completo()
    filtrado = [i for i in itens if current.lower() in i["nome"].lower() or current.lower() in i["raridade"].lower() or current.lower() in i["tipo"].lower()]
    return [
        app_commands.Choice(
            name=f"{i['emoji']} {i['nome']} [{i['raridade']}] — {i['tipo']}{' ('+i['classe']+')' if i['classe'] else ''}"[:100],
            value=i["chave"]
        )
        for i in filtrado[:25]
    ]


async def autocomplete_materiais(interaction: discord.Interaction, current: str):
    itens = get_catalogo_completo()
    filtrado = [i for i in itens if i["tipo"] in ("material", "pocao") and (current.lower() in i["nome"].lower() or not current)]
    return [
        app_commands.Choice(
            name=f"{i['emoji']} {i['nome']} [{i['raridade']}]"[:100],
            value=i["chave"]
        )
        for i in filtrado[:25]
    ]


async def autocomplete_item_premio(interaction: discord.Interaction, current: str):
    try:
        premio_tipo = str(interaction.namespace.premio_tipo or "")
    except:
        premio_tipo = ""
    
    if premio_tipo == "item":
        itens = get_catalogo_completo()
        filtrado = [i for i in itens if current.lower() in i["nome"].lower() or not current]
        return [
            app_commands.Choice(
                name=f"{i['emoji']} {i['nome']} [{i['raridade']}]"[:100],
                value=f"{i['id']}|{i['nome']}|{i['tipo']}|{i['raridade']}|{i['emoji']}|{i.get('desc','')}"[:100]
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