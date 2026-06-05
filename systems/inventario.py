# systems/inventario.py — Sistema de inventário

import discord
from database.db import get_pool
from database.queries import get_personagem, add_item, remove_item, equipar_item


async def get_inventario_completo(user_id: int):
    """Retorna todos os itens do inventário do usuário"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch(
            "SELECT * FROM inventario WHERE user_id = $1 ORDER BY tipo, raridade",
            user_id
        )


async def cmd_inventario(interaction: discord.Interaction, jogador: discord.Member = None):
    """Mostra o inventário do jogador"""
    alvo = jogador or interaction.user
    p = await get_personagem(alvo.id)
    if not p:
        await interaction.response.send_message("Personagem não encontrado!", ephemeral=True)
        return
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        itens = await conn.fetch("SELECT * FROM inventario WHERE user_id = $1 ORDER BY tipo, raridade", alvo.id)
    
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
            )
            for i in equipaveis[:25]
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
                await equipar_item(inter.user.id, item_id, item_row["tipo"])
                await inter.response.send_message(f"✅ Equipado: {item_row['emoji']} **{item_row['nome']}**!", ephemeral=True)
        
        await interaction.response.send_message(embed=embed, view=EquiparView(), ephemeral=True)
    else:
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def cmd_equipar(interaction: discord.Interaction, item: str):
    """Equipa um item do inventário pelo nome"""
    await interaction.response.defer(ephemeral=True)
    
    p = await get_personagem(interaction.user.id)
    if not p:
        await interaction.followup.send("Crie seu personagem primeiro!", ephemeral=True)
        return
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM inventario WHERE user_id = $1 AND LOWER(nome) LIKE $2 AND tipo IN ('arma', 'armadura') LIMIT 1",
            interaction.user.id, f"%{item.lower()}%"
        )
        if not row:
            await interaction.followup.send(f"Item '{item}' não encontrado!", ephemeral=True)
            return
        await equipar_item(interaction.user.id, row["id"], row["tipo"])
    
    await interaction.followup.send(f"✅ Equipado: {row['emoji']} **{row['nome']}**!", ephemeral=True)


async def cmd_jogar_fora(interaction: discord.Interaction, item: str):
    """Descarta um item do inventário"""
    await interaction.response.defer(ephemeral=True)
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM inventario WHERE user_id = $1 AND LOWER(nome) LIKE $2 LIMIT 1",
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


async def cmd_dar(interaction: discord.Interaction, jogador: discord.Member, item: str):
    """Dá um item para outro jogador"""
    await interaction.response.defer(ephemeral=True)
    
    if jogador.id == interaction.user.id:
        await interaction.followup.send("Você não pode dar item para si mesmo!", ephemeral=True)
        return
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM inventario WHERE user_id = $1 AND LOWER(nome) LIKE $2 LIMIT 1",
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
            "SELECT id, quantidade FROM inventario WHERE user_id = $1 AND item_id = $2",
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