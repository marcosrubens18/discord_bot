# cmd_inventario.py — Comandos de inventário

import discord
from discord import app_commands

from db import get_pool
from sistema_personagem import get_personagem


# ==================================================
# FUNÇÕES AUXILIARES
# ==================================================

async def get_inventario_completo(user_id):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch(
            "SELECT * FROM inventario WHERE user_id=$1 ORDER BY tipo, raridade",
            user_id
        )


# ==================================================
# COMANDO INVENTARIO
# ==================================================

async def cmd_inventario(interaction: discord.Interaction, jogador: discord.Member = None):
    await interaction.response.defer(ephemeral=True)
    alvo = jogador or interaction.user
    p = await get_personagem(alvo.id)
    if not p:
        await interaction.followup.send("Personagem não encontrado!", ephemeral=True)
        return
    
    pool_db = await get_pool()
    async with pool_db.acquire() as conn:
        itens = await conn.fetch("SELECT * FROM inventario WHERE user_id=$1 ORDER BY tipo, raridade", alvo.id)
    
    armas = [i for i in itens if i["tipo"] == "arma"]
    armaduras = [i for i in itens if i["tipo"] == "armadura"]
    pocoes = [i for i in itens if i["tipo"] == "pocao" or i["item_id"] == "elixir"]
    materiais = [i for i in itens if i["tipo"] == "material"]
    
    embed = discord.Embed(title=f"📦 Inventário de {alvo.display_name}", color=0x7F77DD)
    
    def fmt(lista):
        if not lista:
            return "—"
        return "\n".join([
            f"{i['emoji']} **{i['nome']}** [{i['raridade']}] (x{i.get('quantidade', 1)}){' ✅' if i.get('equipado') else ''}"
            for i in lista
        ])
    
    embed.add_field(name="🧪 Poções", value=fmt(pocoes) if pocoes else "—", inline=False)
    embed.add_field(name="⚔️ Armas", value=fmt(armas) if armas else "—", inline=True)
    embed.add_field(name="🛡️ Armaduras", value=fmt(armaduras) if armaduras else "—", inline=True)
    if materiais:
        embed.add_field(name="📦 Materiais", value=fmt(materiais), inline=False)
    embed.set_footer(text=f"Moedas: {p['moedas']} 🪙")
    
    equipaveis = armas + armaduras
    if equipaveis and alvo.id == interaction.user.id:
        opcoes = [
            discord.SelectOption(
                label=f"{i['emoji']} {i['nome'][:40]}",
                value=str(i["id"]),
                description=f"{i['tipo'].title()} | {i['raridade']}",
                default=bool(i.get("equipado"))
            ) for i in equipaveis[:25]
        ]
        
        class EquiparView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
            
            @discord.ui.select(placeholder="Equipar item...", options=opcoes)
            async def sel(self, inter: discord.Interaction, s):
                if inter.user.id != interaction.user.id:
                    return
                item_id = int(s.values[0])
                item_row = next((i for i in equipaveis if i["id"] == item_id), None)
                if not item_row:
                    await inter.response.send_message("Item não encontrado!", ephemeral=True)
                    return
                pool2 = await get_pool()
                async with pool2.acquire() as conn2:
                    await conn2.execute("UPDATE inventario SET equipado=0 WHERE user_id=$1 AND tipo=$2", inter.user.id, item_row["tipo"])
                    await conn2.execute("UPDATE inventario SET equipado=1 WHERE id=$1", item_id)
                await inter.response.send_message(f"✅ Equipado: {item_row['emoji']} **{item_row['nome']}**!", ephemeral=True)
        
        await interaction.followup.send(embed=embed, view=EquiparView(), ephemeral=True)
    else:
        await interaction.followup.send(embed=embed, ephemeral=True)


# ==================================================
# COMANDO EQUIPAR
# ==================================================

async def cmd_equipar(interaction: discord.Interaction, item: str):
    await interaction.response.defer(ephemeral=True)
    
    p = await get_personagem(interaction.user.id)
    if not p:
        await interaction.followup.send("Crie seu personagem primeiro!", ephemeral=True)
        return
    
    pool_db = await get_pool()
    async with pool_db.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM inventario WHERE user_id=$1 AND LOWER(nome) LIKE $2 AND tipo IN ('arma', 'armadura') LIMIT 1",
            interaction.user.id, f"%{item.lower()}%"
        )
        if not row:
            await interaction.followup.send(f"Item '{item}' não encontrado!", ephemeral=True)
            return
        await conn.execute("UPDATE inventario SET equipado=0 WHERE user_id=$1 AND tipo=$2", interaction.user.id, row["tipo"])
        await conn.execute("UPDATE inventario SET equipado=1 WHERE id=$1", row["id"])
    
    await interaction.followup.send(f"✅ Equipado: {row['emoji']} **{row['nome']}**!", ephemeral=True)


# ==================================================
# COMANDO JOGAR FORA
# ==================================================

async def cmd_jogar_fora(interaction: discord.Interaction, item: str):
    await interaction.response.defer(ephemeral=True)
    
    pool_db = await get_pool()
    async with pool_db.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM inventario WHERE user_id=$1 AND LOWER(nome) LIKE $2 LIMIT 1",
            interaction.user.id, f"%{item.lower()}%"
        )
        if not row:
            await interaction.followup.send(f"Item '{item}' não encontrado!", ephemeral=True)
            return
        
        class ConfirmarView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=30)
                self.confirmado = False
            
            @discord.ui.button(label="✅ Sim, descartar", style=discord.ButtonStyle.danger)
            async def confirmar(self, inter: discord.Interaction, button):
                if inter.user.id != interaction.user.id:
                    return
                self.confirmado = True
                self.stop()
            
            @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.secondary)
            async def cancelar(self, inter: discord.Interaction, button):
                self.stop()
        
        view = ConfirmarView()
        embed_conf = discord.Embed(
            title="⚠️ Confirmar descarte",
            description=f"Tem certeza que deseja descartar {row['emoji']} **{row['nome']}**?\n\nEsta ação não pode ser desfeita!",
            color=0xE24B4A
        )
        await interaction.followup.send(embed=embed_conf, view=view, ephemeral=True)
        await view.wait()
        
        if not view.confirmado:
            await interaction.edit_original_response(content="❌ Descarte cancelado.", embed=None, view=None)
            return
        
        if row["quantidade"] > 1:
            await conn.execute("UPDATE inventario SET quantidade = quantidade - 1 WHERE id = $1", row["id"])
        else:
            await conn.execute("DELETE FROM inventario WHERE id = $1", row["id"])
    
    await interaction.edit_original_response(content=f"🗑️ Descartado: {row['emoji']} {row['nome']}", embed=None, view=None)


# ==================================================
# COMANDO DAR
# ==================================================

async def cmd_dar(interaction: discord.Interaction, jogador: discord.Member, item: str):
    await interaction.response.defer(ephemeral=True)
    
    if jogador.id == interaction.user.id:
        await interaction.followup.send("Você não pode dar item para si mesmo!", ephemeral=True)
        return
    
    pool_db = await get_pool()
    async with pool_db.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM inventario WHERE user_id=$1 AND LOWER(nome) LIKE $2 LIMIT 1",
            interaction.user.id, f"%{item.lower()}%"
        )
        if not row:
            await interaction.followup.send(f"Item '{item}' não encontrado!", ephemeral=True)
            return
        
        # Verifica se o item está equipado
        if row.get("equipado"):
            await interaction.followup.send("Você não pode dar um item equipado! Tire-o primeiro.", ephemeral=True)
            return
        
        # Adiciona ao destinatário
        ex = await conn.fetchrow(
            "SELECT id, quantidade FROM inventario WHERE user_id=$1 AND item_id=$2",
            jogador.id, row["item_id"]
        )
        if ex:
            await conn.execute("UPDATE inventario SET quantidade = quantidade + 1 WHERE id = $1", ex["id"])
        else:
            await conn.execute(
                "INSERT INTO inventario (user_id, item_id, nome, tipo, raridade, emoji, descricao) VALUES ($1, $2, $3, $4, $5, $6, $7)",
                jogador.id, row["item_id"], row["nome"], row["tipo"], row["raridade"], row["emoji"], row["descricao"]
            )
        
        # Remove do doador
        if row["quantidade"] > 1:
            await conn.execute("UPDATE inventario SET quantidade = quantidade - 1 WHERE id = $1", row["id"])
        else:
            await conn.execute("DELETE FROM inventario WHERE id = $1", row["id"])
    
    await interaction.followup.send(f"✅ Dado {row['emoji']} **{row['nome']}** para {jogador.mention}!", ephemeral=True)


# ==================================================
# REGISTRO DOS COMANDOS
# ==================================================

def setup_inventario_commands(bot):
    @bot.tree.command(name="inventario", description="Mostra seu inventário completo")
    @app_commands.describe(jogador="Jogador (opcional)")
    async def inventario(interaction: discord.Interaction, jogador: discord.Member = None):
        await cmd_inventario(interaction, jogador)
    
    @bot.tree.command(name="equipar", description="Equipa um item do inventário pelo nome")
    @app_commands.describe(item="Nome do item a equipar")
    async def equipar(interaction: discord.Interaction, item: str):
        await cmd_equipar(interaction, item)
    
    @bot.tree.command(name="jogar-fora", description="Descarta um item do inventário")
    @app_commands.describe(item="Nome do item a descartar")
    async def jogar_fora(interaction: discord.Interaction, item: str):
        await cmd_jogar_fora(interaction, item)
    
    @bot.tree.command(name="dar", description="Dá um item para outro jogador")
    @app_commands.describe(jogador="Jogador que recebe", item="Nome do item")
    async def dar(interaction: discord.Interaction, jogador: discord.Member, item: str):
        await cmd_dar(interaction, jogador, item)