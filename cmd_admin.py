# cmd_admin.py — Comandos administrativos

import discord
from discord import app_commands

from sistema_personagem import get_personagem
from sistema_roleta import cmd_set_giros
from sistema_eventos import cmd_criar_evento, cmd_encerrar_evento, cmd_add_pontos
from sistema_anuncios import cmd_anunciar, cmd_anunciar_evento, cmd_agendar_anuncio
from catalogo import get_item_por_chave, get_itens_por_categoria, get_rank, calcular_mana_max
from data_skills import SKILLS_COMPLETAS
from constants import COR_RAR
from utils import atualizar_todos_cargos


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


async def autocomplete_item_categoria(interaction: discord.Interaction, current: str):
    try:
        categoria = str(interaction.namespace.categoria or "")
    except:
        categoria = ""
    itens = get_itens_por_categoria(categoria) if categoria else get_catalogo_completo()
    filtrado = [i for i in itens if current.lower() in i["nome"].lower() or current.lower() in i["raridade"].lower()]
    filtrado.sort(key=lambda x: x["nome"].lower())
    return [
        app_commands.Choice(
            name=f"{i['emoji']} {i['nome']} [{i['raridade']}]"[:100],
            value=i["chave"]
        )
        for i in filtrado[:25]
    ]


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


def resolver_canal(guild, canal):
    if canal is None:
        return None
    if hasattr(canal, 'id'):
        return guild.get_channel(canal.id) or canal
    canal_str = str(canal)
    if canal_str.isdigit():
        return guild.get_channel(int(canal_str))
    return discord.utils.get(guild.channels, name=canal_str.lstrip('#'))


from data_itens import get_catalogo_completo


# ==================================================
# REGISTRO DOS COMANDOS
# ==================================================

def setup_admin_commands(bot):
    @bot.tree.command(name="set-item", description="[ADMIN] Dá um item para um jogador")
    @app_commands.describe(
        jogador="Jogador que vai receber o item",
        categoria="Categoria do item",
        item="Digite para buscar o item",
        quantidade="Quantidade (padrão: 1)"
    )
    @app_commands.choices(categoria=[
        app_commands.Choice(name="Poções", value="pocoes"),
        app_commands.Choice(name="Armas Guerreiro", value="arma_guerreiro"),
        app_commands.Choice(name="Armas Arqueiro", value="arma_arqueiro"),
        app_commands.Choice(name="Armas Mago", value="arma_mago"),
        app_commands.Choice(name="Armas Paladino", value="arma_paladino"),
        app_commands.Choice(name="Armas Necromante", value="arma_necromante"),
        app_commands.Choice(name="Armas Dracomante", value="arma_dracomante"),
        app_commands.Choice(name="Armas Arcano", value="arma_arcano"),
        app_commands.Choice(name="Armaduras Guerreiro", value="arm_guerreiro"),
        app_commands.Choice(name="Armaduras Arqueiro", value="arm_arqueiro"),
        app_commands.Choice(name="Armaduras Mago", value="arm_mago"),
        app_commands.Choice(name="Armaduras Paladino", value="arm_paladino"),
        app_commands.Choice(name="Armaduras Necromante", value="arm_necromante"),
        app_commands.Choice(name="Armaduras Dracomante", value="arm_dracomante"),
        app_commands.Choice(name="Armaduras Arcano", value="arm_arcano"),
        app_commands.Choice(name="Materiais", value="materiais"),
    ])
    @app_commands.autocomplete(item=autocomplete_item_categoria)
    @admin_only()
    async def set_item(interaction: discord.Interaction, jogador: discord.Member,
                       categoria: str, item: str, quantidade: int = 1):
        from db import get_pool
        
        await interaction.response.defer(ephemeral=True)
        
        if not await get_personagem(jogador.id):
            await interaction.followup.send(f"{jogador.display_name} não tem personagem!", ephemeral=True)
            return

        it = get_item_por_chave(item)
        if not it:
            itens_cat = get_itens_por_categoria(categoria)
            it = next((i for i in itens_cat if i["id"] == item), None)
        if not it:
            await interaction.followup.send(f"Item não encontrado! Selecione da lista de sugestões.", ephemeral=True)
            return

        qtd = max(1, min(quantidade, 99))
        pool = await get_pool()
        async with pool.acquire() as conn:
            ex = await conn.fetchrow(
                "SELECT id, quantidade FROM inventario WHERE user_id = $1 AND item_id = $2",
                jogador.id, it["id"])
            if ex:
                await conn.execute("UPDATE inventario SET quantidade = quantidade + $1 WHERE id = $2", qtd, ex["id"])
            else:
                await conn.execute(
                    "INSERT INTO inventario(user_id, item_id, nome, tipo, raridade, emoji, descricao) VALUES($1,$2,$3,$4,$5,$6,$7)",
                    jogador.id, it["id"], it["nome"], it["tipo"], it["raridade"], it["emoji"], it.get("desc", ""))

        cor = COR_RAR.get(it["raridade"], 0x888780)
        await interaction.followup.send(
            embed=discord.Embed(
                title="✅ Item adicionado!",
                description=f"{it['emoji']} **{it['nome']}** x{qtd} para {jogador.mention}!",
                color=cor
            ), ephemeral=True
        )

    @bot.tree.command(name="set-moedas", description="[ADMIN] Define ou adiciona moedas")
    @app_commands.describe(jogador="Jogador alvo", quantidade="Quantidade", modo="definir ou adicionar")
    @app_commands.choices(modo=[
        app_commands.Choice(name="Adicionar", value="adicionar"),
        app_commands.Choice(name="Definir", value="definir"),
    ])
    @admin_only()
    async def set_moedas(interaction: discord.Interaction, jogador: discord.Member, quantidade: int, modo: str = "adicionar"):
        from db import get_pool
        
        await interaction.response.defer(ephemeral=True)
        
        if not await get_personagem(jogador.id):
            await interaction.followup.send(f"{jogador.display_name} não tem personagem!", ephemeral=True)
            return
        
        pool = await get_pool()
        async with pool.acquire() as conn:
            if modo == "definir":
                await conn.execute("UPDATE personagens SET moedas = $1 WHERE user_id = $2", quantidade, jogador.id)
            else:
                await conn.execute("UPDATE personagens SET moedas = moedas + $1 WHERE user_id = $2", quantidade, jogador.id)
        
        await interaction.followup.send(f"✅ Moedas de {jogador.display_name} atualizadas!", ephemeral=True)

    @bot.tree.command(name="set-nivel", description="[ADMIN] Define o nível de um jogador")
    @app_commands.describe(jogador="Jogador alvo", nivel="Nível (1-100)")
    @admin_only()
    async def set_nivel(interaction: discord.Interaction, jogador: discord.Member, nivel: int):
        from db import get_pool
        
        await interaction.response.defer(ephemeral=True)
        
        if nivel < 1 or nivel > 100:
            await interaction.followup.send("Nível deve ser entre 1 e 100!", ephemeral=True)
            return
        
        p = await get_personagem(jogador.id)
        if not p:
            await interaction.followup.send(f"{jogador.display_name} não tem personagem!", ephemeral=True)
            return
        
        nd = nivel - p["nivel"]
        hp_n = max(50, p["hp_max"] + nd * 6)
        atk_n = max(5, p["ataque"] + nd * 2)
        dfs_n = max(3, p["defesa"] + nd * 1)
        mana_n = calcular_mana_max(p["classe_id"], nivel, p["poder_valor"], p["destino_id"])
        
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE personagens 
                SET nivel = $1, xp = 0, hp_max = $2, hp_atual = $3, ataque = $4, defesa = $5, mana_max = $6, mana_atual = $7 
                WHERE user_id = $8
            """, nivel, hp_n, hp_n, atk_n, dfs_n, mana_n, mana_n, jogador.id)
            
            for sk in SKILLS_COMPLETAS.get(p["classe_id"], []):
                if sk["nivel"] <= nivel:
                    await conn.execute("INSERT INTO skills_desbloqueadas(user_id, skill_id) VALUES($1,$2) ON CONFLICT DO NOTHING", jogador.id, sk["id"])
        
        guild = interaction.guild
        if guild:
            member = guild.get_member(jogador.id)
            if member:
                await atualizar_todos_cargos(guild, member, nivel)
        
        rank_o = get_rank(nivel)
        await interaction.followup.send(f"✅ {jogador.mention} agora é Nível {nivel} — {rank_o['emoji']} Rank {rank_o['rank']}!", ephemeral=True)

    @bot.tree.command(name="set-giros", description="[ADMIN] Dá fichas de roleta a um jogador")
    @app_commands.describe(jogador="Jogador alvo")
    @admin_only()
    async def set_giros(interaction: discord.Interaction, jogador: discord.Member):
        await cmd_set_giros(interaction, jogador)

    @bot.tree.command(name="anunciar", description="[ADMIN] Cria e envia um anúncio formatado")
    @app_commands.describe(
        canal="Canal (digite para buscar)",
        cor="Cor do embed",
        ping="Cargo a pingar (opcional)"
    )
    @app_commands.autocomplete(canal=autocomplete_canal)
    @app_commands.choices(cor=[
        app_commands.Choice(name="Dourado", value="dourado"),
        app_commands.Choice(name="Roxo", value="roxo"),
        app_commands.Choice(name="Verde", value="verde"),
        app_commands.Choice(name="Azul", value="azul"),
        app_commands.Choice(name="Vermelho", value="vermelho"),
        app_commands.Choice(name="Laranja", value="laranja"),
        app_commands.Choice(name="Cinza", value="cinza"),
        app_commands.Choice(name="Preto", value="preto"),
    ])
    @admin_only()
    async def anunciar(interaction: discord.Interaction, canal: str,
                       cor: str = "roxo", ping: discord.Role = None):
        canal_obj = resolver_canal(interaction.guild, canal)
        if not canal_obj:
            await interaction.response.send_message('❌ Canal não encontrado!', ephemeral=True)
            return
        await cmd_anunciar(interaction, canal_obj, cor, ping)

    @bot.tree.command(name="anunciar-evento", description="[ADMIN] Anuncia um evento com data e prêmio")
    @app_commands.describe(
        canal="Canal (digite para buscar)",
        ping="Cargo a pingar (opcional)"
    )
    @app_commands.autocomplete(canal=autocomplete_canal)
    @admin_only()
    async def anunciar_evento(interaction: discord.Interaction, canal: str, ping: discord.Role = None):
        canal_obj = resolver_canal(interaction.guild, canal)
        if not canal_obj:
            await interaction.response.send_message('❌ Canal não encontrado!', ephemeral=True)
            return
        await cmd_anunciar_evento(interaction, canal_obj, ping)

    @bot.tree.command(name="agendar-anuncio", description="[ADMIN] Agenda um anúncio para enviar depois")
    @app_commands.describe(
        canal="Canal do anúncio",
        cor="Cor do embed"
    )
    @app_commands.choices(cor=[
        app_commands.Choice(name="Dourado", value="dourado"),
        app_commands.Choice(name="Roxo", value="roxo"),
        app_commands.Choice(name="Verde", value="verde"),
        app_commands.Choice(name="Azul", value="azul"),
        app_commands.Choice(name="Vermelho", value="vermelho"),
        app_commands.Choice(name="Laranja", value="laranja"),
        app_commands.Choice(name="Cinza", value="cinza"),
        app_commands.Choice(name="Preto", value="preto"),
    ])
    @admin_only()
    async def agendar_anuncio(interaction: discord.Interaction, canal: str, cor: str = "dourado"):
        canal_obj = resolver_canal(interaction.guild, canal)
        if not canal_obj:
            await interaction.response.send_message('❌ Canal não encontrado!', ephemeral=True)
            return
        await cmd_agendar_anuncio(interaction, canal_obj, cor)