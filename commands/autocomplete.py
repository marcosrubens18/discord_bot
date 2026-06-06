# commands/autocomplete.py — Funções de autocomplete para comandos

import discord
from discord import app_commands

from data.armas import ARMAS_POR_CLASSE
from data.armaduras import ARMADURAS_POR_CLASSE
from data.itens import POCOES_CAT, MATERIAIS_CAT
from data.constantes import RARIDADES


def get_catalogo_completo():
    """Retorna todos os itens do catálogo (armas, armaduras, poções, materiais) SEM DUPLICAÇÃO"""
    todos = []
    itens_ids_vistos = set()
    
    # Armas (apenas uma vez por item, não por classe)
    for cls, armas in ARMAS_POR_CLASSE.items():
        for a in armas:
            if a["id"] not in itens_ids_vistos:
                itens_ids_vistos.add(a["id"])
                todos.append({
                    "chave": f"arma:{cls}:{a['id']}",
                    "id": a["id"], "nome": a["nome"],
                    "emoji": a.get("emoji", "⚔️"), "tipo": "arma",
                    "raridade": a["raridade"], "classe": cls,
                    "desc": a.get("desc", ""), "preco": a.get("preco", 0), "venda": a.get("venda", 0)
                })
    
    # Armaduras (apenas uma vez por item)
    itens_ids_vistos = set()
    for cls, arms in ARMADURAS_POR_CLASSE.items():
        for a in arms:
            if a["id"] not in itens_ids_vistos:
                itens_ids_vistos.add(a["id"])
                todos.append({
                    "chave": f"armadura:{cls}:{a['id']}",
                    "id": a["id"], "nome": a["nome"],
                    "emoji": a.get("emoji", "🛡️"), "tipo": "armadura",
                    "raridade": a["raridade"], "classe": cls,
                    "desc": a.get("desc", ""), "preco": a.get("preco", 0), "venda": a.get("venda", 0)
                })
    
    # Poções
    for p in POCOES_CAT:
        todos.append({
            **p, "chave": f"pocao::{p['id']}", "classe": "", 
            "preco": p.get("preco", 0), "venda": p.get("venda", 0)
        })
    
    # Materiais
    for m in MATERIAIS_CAT:
        todos.append({
            **m, "chave": f"material::{m['id']}", "classe": "", 
            "preco": m.get("preco", 0), "venda": m.get("venda", 0)
        })
    
    return todos


def get_item_por_chave(chave: str):
    for it in get_catalogo_completo():
        if it["chave"] == chave:
            return it
    return None


def get_itens_por_categoria(categoria: str):
    todos = get_catalogo_completo()
    cat_map = {
        "pocoes": [i for i in todos if i["tipo"] == "pocao"],
        "arma_guerreiro": [i for i in todos if i["tipo"] == "arma" and i["classe"] == "guerreiro"],
        "arma_arqueiro": [i for i in todos if i["tipo"] == "arma" and i["classe"] == "arqueiro"],
        "arma_mago": [i for i in todos if i["tipo"] == "arma" and i["classe"] == "mago"],
        "arma_paladino": [i for i in todos if i["tipo"] == "arma" and i["classe"] == "paladino"],
        "arma_necromante": [i for i in todos if i["tipo"] == "arma" and i["classe"] == "necromante"],
        "arma_dracomante": [i for i in todos if i["tipo"] == "arma" and i["classe"] == "dracomante"],
        "arma_arcano": [i for i in todos if i["tipo"] == "arma" and i["classe"] == "arcano"],
        "arm_guerreiro": [i for i in todos if i["tipo"] == "armadura" and i["classe"] == "guerreiro"],
        "arm_arqueiro": [i for i in todos if i["tipo"] == "armadura" and i["classe"] == "arqueiro"],
        "arm_mago": [i for i in todos if i["tipo"] == "armadura" and i["classe"] == "mago"],
        "arm_paladino": [i for i in todos if i["tipo"] == "armadura" and i["classe"] == "paladino"],
        "arm_necromante": [i for i in todos if i["tipo"] == "armadura" and i["classe"] == "necromante"],
        "arm_dracomante": [i for i in todos if i["tipo"] == "armadura" and i["classe"] == "dracomante"],
        "arm_arcano": [i for i in todos if i["tipo"] == "armadura" and i["classe"] == "arcano"],
        "materiais": [i for i in todos if i["tipo"] == "material"],
    }
    return cat_map.get(categoria, todos)


async def autocomplete_item_categoria(interaction: discord.Interaction, current: str):
    try:
        categoria = getattr(interaction.namespace, 'categoria', '')
    except:
        categoria = ""
    
    itens = get_itens_por_categoria(categoria) if categoria else get_catalogo_completo()
    
    # Filtra e ordena por relevância
    current_lower = current.lower()
    filtrado = [
        i for i in itens 
        if current_lower in i["nome"].lower() or current_lower in i["raridade"].lower()
    ]
    # Ordena: primeiro os que começam com o termo, depois os que contêm
    filtrado.sort(key=lambda x: (
        0 if x["nome"].lower().startswith(current_lower) else 1,
        x["nome"].lower()
    ))
    
    return [
        app_commands.Choice(
            name=f"{i['emoji']} {i['nome']} [{i['raridade']}]"[:100],
            value=i["chave"]
        )
        for i in filtrado[:25]
    ]


async def autocomplete_item_todos(interaction: discord.Interaction, current: str):
    itens = get_catalogo_completo()
    current_lower = current.lower()
    filtrado = [
        i for i in itens 
        if current_lower in i["nome"].lower() or current_lower in i["raridade"].lower() or current_lower in i["tipo"].lower()
    ]
    filtrado.sort(key=lambda x: (
        0 if x["nome"].lower().startswith(current_lower) else 1,
        x["nome"].lower()
    ))
    
    return [
        app_commands.Choice(
            name=f"{i['emoji']} {i['nome']} [{i['raridade']}] — {i['tipo']}{' ('+i['classe']+')' if i['classe'] else ''}"[:100],
            value=i["chave"]
        )
        for i in filtrado[:25]
    ]


async def autocomplete_materiais(interaction: discord.Interaction, current: str):
    itens = get_catalogo_completo()
    filtrado = [
        i for i in itens 
        if i["tipo"] in ("material", "pocao") and (current.lower() in i["nome"].lower() or not current)
    ]
    filtrado.sort(key=lambda x: x["nome"].lower())
    
    return [
        app_commands.Choice(
            name=f"{i['emoji']} {i['nome']} [{i['raridade']}]"[:100],
            value=i["chave"]
        )
        for i in filtrado[:25]
    ]


async def autocomplete_item_premio(interaction: discord.Interaction, current: str):
    try:
        premio_tipo = getattr(interaction.namespace, 'premio_tipo', '')
    except:
        premio_tipo = ""
    
    if premio_tipo == "item":
        itens = get_catalogo_completo()
        filtrado = [
            i for i in itens 
            if current.lower() in i["nome"].lower() or not current
        ]
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
