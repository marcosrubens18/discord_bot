# systems/economia/loja.py — Sistema de Loja

import discord
from discord import app_commands

from database.db import get_pool
from database.queries import get_personagem, add_item
from data.armas import get_armas_classe
from data.armaduras import get_armaduras_classe
from data.itens import POCOES_BATALHA
from data.constantes import COR_PRIMARY, COR_SUCCESS, COR_DANGER


# ==================================================
# COMANDO LOJA
# ==================================================

async def cmd_loja(interaction: discord.Interaction, categoria: str = "pocoes"):
    """Comando /loja - Compra itens"""
    await interaction.response.defer(ephemeral=True)
    
    p = await get_personagem(interaction.user.id)
    if not p:
        await interaction.followup.send("Crie seu personagem primeiro!", ephemeral=True)
        return
    
    if categoria == "armas":
        itens = [i for i in get_armas_classe(p["classe_id"]) if i["raridade"] in ("Comum", "Incomum")]
    elif categoria == "armaduras":
        itens = [i for i in get_armaduras_classe(p["classe_id"]) if i["raridade"] in ("Comum", "Incomum")]
    else:
        itens = [
            {
                "id": k,
                "nome": v["nome"],
                "emoji": v["emoji"],
                "raridade": "Comum",
                "preco": v["preco"],
                "desc": f"Recupera {v['valor']} HP/Mana"
            }
            for k, v in POCOES_BATALHA.items()
        ]
    
    if not itens:
        await interaction.followup.send("Nenhum item disponivel!", ephemeral=True)
        return
    
    opcoes = [
        discord.SelectOption(
            label=f"{i['emoji']} {i['nome']} — {i.get('preco', 0)} moedas",
            value=i["id"],
            description=i.get("desc", "")[:50]
        )
        for i in itens[:25]
    ]
    
    class LojaView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)
            self.item = None
        
        @discord.ui.select(placeholder="Escolha o item...", options=opcoes)
        async def sel(self, inter: discord.Interaction, s):
            if inter.user.id != interaction.user.id:
                return
            self.item = next((i for i in itens if i["id"] == s.values[0]), None)
            await inter.response.defer()
            self.stop()
    
    view = LojaView()
    embed_loja = discord.Embed(
        title=f"🛒 Loja — {categoria.title()}",
        description=f"Moedas: **{p['moedas']} 🪙**",
        color=COR_PRIMARY
    )
    
    await interaction.followup.send(embed=embed_loja, view=view, ephemeral=True)
    await view.wait()
    
    if not view.item:
        return
    
    it = view.item
    preco = it.get("preco", 0)
    
    if p["moedas"] < preco:
        await interaction.followup.send(f"Moedas insuficientes! Precisa de {preco} 🪙.", ephemeral=True)
        return
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("UPDATE personagens SET moedas = moedas - $1 WHERE user_id = $2", preco, interaction.user.id)
        
        ex = await conn.fetchrow(
            "SELECT id FROM inventario WHERE user_id = $1 AND item_id = $2",
            interaction.user.id, it["id"]
        )
        if ex:
            await conn.execute("UPDATE inventario SET quantidade = quantidade + 1 WHERE id = $1", ex["id"])
        else:
            await conn.execute("""
                INSERT INTO inventario (user_id, item_id, nome, tipo, raridade, emoji, descricao)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, interaction.user.id, it["id"], it["nome"], categoria.rstrip("s"), it["raridade"], it["emoji"], it.get("desc", ""))
        
        # Registrar para missões
        from systems.missoes import atualizar_progresso
        await atualizar_progresso(interaction.user.id, "moedas_gastas", preco)
    
    await interaction.followup.send(
        f"✅ Comprou {it['emoji']} **{it['nome']}** por {preco} moedas!",
        ephemeral=True
    )