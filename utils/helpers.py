# utils/helpers.py — Funções auxiliares e utilitárias

import discord
import random
from data.ranks import get_rank
from data.constantes import EMOJI_CLASSE, COR_RAR
from database.db import get_pool

# ==================================================
# CARGOS E PERMISSÕES
# ==================================================

async def atualizar_cargo_nivel(guild, member, nivel):
    """Atualiza cargo de nivel (Aventureiro/Veterano/Elite/Mestre)"""
    if not guild or not member:
        return
    CARGOS_NIVEL = [
        (50, "💎 Mestre"),
        (30, "🥇 Elite"),
        (15, "🥈 Veterano"),
        (5,  "🥉 Aventureiro"),
    ]
    for _, nome in CARGOS_NIVEL:
        cargo = discord.utils.get(guild.roles, name=nome)
        if cargo and cargo in member.roles:
            try:
                await member.remove_roles(cargo)
            except Exception:
                pass
    for nivel_min, nome in CARGOS_NIVEL:
        if nivel >= nivel_min:
            cargo = discord.utils.get(guild.roles, name=nome)
            if cargo:
                try:
                    await member.add_roles(cargo)
                except Exception:
                    pass
            break


async def atualizar_cargo_rank(guild, member, rank_str):
    """Atualiza cargo de rank (F ao SS)"""
    if not guild or not member:
        return
    from data.ranks import CARGOS_RANK
    
    todos_ranks = [
        "🟫 Rank F", "🟩 Rank E", "🟦 Rank D", "🟨 Rank C",
        "🟧 Rank B", "🟥 Rank A", "⭐ Rank S", "💎 Rank SS",
    ]
    for nome in todos_ranks:
        cargo = discord.utils.get(guild.roles, name=nome)
        if cargo and cargo in member.roles:
            try:
                await member.remove_roles(cargo)
            except Exception:
                pass
    nome_novo = CARGOS_RANK.get(rank_str)
    if nome_novo:
        cargo = discord.utils.get(guild.roles, name=nome_novo)
        if cargo:
            try:
                await member.add_roles(cargo)
            except Exception:
                pass


async def atualizar_todos_cargos(guild, member, nivel):
    """Atualiza cargo de nivel e rank de uma vez"""
    rank_obj = get_rank(nivel)
    await atualizar_cargo_nivel(guild, member, nivel)
    await atualizar_cargo_rank(guild, member, rank_obj["rank"])
    return rank_obj


# ==================================================
# CANAL PRIVADO
# ==================================================

async def criar_canal_privado(guild, member, nome, classe):
    """Cria canal privado para o jogador"""
    from data.constantes import COR_RAR
    
    try:
        cat = (discord.utils.get(guild.categories, name="MEU PERFIL") or
               discord.utils.get(guild.categories, name="Meu Perfil") or
               discord.utils.get(guild.categories, name="PERFIL") or
               discord.utils.get(guild.categories, name="perfil"))
        if not cat:
            cat = await guild.create_category("MEU PERFIL")
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }
        nome_canal = f"{classe['emoji']}│{nome.lower()[:20]}"
        canal = await guild.create_text_channel(nome_canal, category=cat, overwrites=overwrites)
        cor = COR_RAR.get(classe.get("raridade", "Comum"), 0x7F77DD)
        await canal.send(content=member.mention)
        return canal
    except Exception as e:
        print(f"Erro ao criar canal privado: {e}")
        return None


# ==================================================
# FORMATAÇÃO
# ==================================================

def formatar_item(item):
    """Formata um item para exibição"""
    emoji = item.get("emoji", "📦")
    nome = item["nome"]
    raridade = item.get("raridade", "Comum")
    quantidade = item.get("quantidade", 1)
    equipado = " ✅" if item.get("equipado") else ""
    return f"{emoji} **{nome}** [{raridade}] (x{quantidade}){equipado}"


def formatar_lista(lista, titulo=None):
    """Formata uma lista para exibição em embed"""
    if not lista:
        return "—"
    return "\n".join([formatar_item(i) for i in lista])


# ==================================================
# SORTEIO COM PESOS
# ==================================================

def sortear_com_pesos(opcoes, pesos):
    """Sorteia um item baseado em pesos"""
    if not opcoes or not pesos:
        return None
    return random.choices(opcoes, weights=pesos, k=1)[0]


# ==================================================
# XP E NÍVEL
# ==================================================

def xp_necessario_para_nivel(nivel):
    """Calcula XP necessário para o próximo nível"""
    return 100 + (nivel - 1) * 50


def calcular_level_up(xp_atual, nivel_atual):
    """Calcula quantos níveis o jogador sobe com o XP atual"""
    novo_xp = xp_atual
    nv = nivel_atual
    levelups = 0
    
    needed = xp_necessario_para_nivel(nv)
    while novo_xp >= needed:
        novo_xp -= needed
        nv += 1
        needed = xp_necessario_para_nivel(nv)
        levelups += 1
    
    return levelups, nv, novo_xp


# ==================================================
# ANÚNCIOS
# ==================================================

async def enviar_anuncio(canal, titulo, descricao, cor=0xE4AF3C, imagem=None, rodape=None):
    """Envia um anúncio formatado"""
    embed = discord.Embed(title=titulo, description=descricao, color=cor)
    if imagem:
        embed.set_image(url=imagem)
    if rodape:
        embed.set_footer(text=rodape)
    await canal.send(embed=embed)


# ==================================================
# VALIDAÇÕES
# ==================================================

def validar_nivel(nivel):
    """Valida se o nível está entre 1 e 100"""
    return 1 <= nivel <= 100


def validar_quantidade(qtd, min_qtd=1, max_qtd=999):
    """Valida se a quantidade está dentro dos limites"""
    return min_qtd <= qtd <= max_qtd


def validar_preco(moedas, preco):
    """Valida se o jogador tem moedas suficientes"""
    return moedas >= preco
