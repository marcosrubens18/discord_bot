# systems/economia/ferreiro.py — Sistema de Forja

import discord
from discord import app_commands

from database.db import get_pool
from database.queries import get_personagem
from data.receitas import RECEITAS


# ==================================================
# COMANDO FERREIRO
# ==================================================

async def cmd_ferreiro(interaction: discord.Interaction):
    """Comando /ferreiro - Forja itens"""
    await interaction.response.defer(ephemeral=True)
    
    p = await get_personagem(interaction.user.id)
    if not p:
        await interaction.followup.send("Crie seu personagem primeiro!", ephemeral=True)
        return
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        inv = await conn.fetch("SELECT item_id, quantidade FROM inventario WHERE user_id = $1", interaction.user.id)
        pf = await conn.fetchrow("SELECT moedas FROM personagens WHERE user_id = $1", interaction.user.id)
    
    inv_map = {r["item_id"]: r["quantidade"] for r in inv}
    
    disp = [
        r for r in RECEITAS
        if all(inv_map.get(m, 0) >= q for m, q in r["materiais"].items())
    ]
    
    linhas = []
    for r in RECEITAS:
        pode = r in disp
        status = "✅" if pode else "❌"
        falta_txt = ""
        if not pode:
            faltando = [
                f"{q - inv_map.get(m, 0)}x {m}"
                for m, q in r["materiais"].items()
                if inv_map.get(m, 0) < q
            ]
            if faltando:
                falta_txt = f" (falta: {', '.join(faltando)})"
        linhas.append(
            f"{status} {r['emoji']} **{r['nome']}** [{r['raridade']}] — {r['preco_forja']} moedas{falta_txt}"
        )
    
    desc = "\n".join(linhas)
    
    if not disp:
        await interaction.followup.send(
            embed=discord.Embed(
                title="🔨 Ferreiro",
                description=f"Sem materiais suficientes!\n\n{desc}",
                color=0x888780
            ),
            ephemeral=True
        )
        return
    
    opcoes = [
        discord.SelectOption(label=f"{r['emoji']} {r['nome']}", value=r["id"])
        for r in disp[:25]
    ]
    
    class FerreiroView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)
            self.escolha = None
        
        @discord.ui.select(placeholder="Escolha a receita...", options=opcoes)
        async def sel(self, inter: discord.Interaction, s):
            if inter.user.id != interaction.user.id:
                return
            self.escolha = s.values[0]
            await inter.response.defer()
            self.stop()
    
    view = FerreiroView()
    await interaction.followup.send(
        embed=discord.Embed(title="🔨 Ferreiro", description=desc, color=0x888780),
        view=view,
        ephemeral=True
    )
    await view.wait()
    
    if not view.escolha:
        return
    
    receita = next((r for r in RECEITAS if r["id"] == view.escolha), None)
    if not receita:
        return
    
    if pf["moedas"] < receita["preco_forja"]:
        await interaction.followup.send("Moedas insuficientes!", ephemeral=True)
        return
    
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE personagens SET moedas = moedas - $1 WHERE user_id = $2",
            receita["preco_forja"], interaction.user.id
        )
        
        for mat, qtd in receita["materiais"].items():
            row = await conn.fetchrow(
                "SELECT id, quantidade FROM inventario WHERE user_id = $1 AND item_id = $2",
                interaction.user.id, mat
            )
            if row:
                if row["quantidade"] > qtd:
                    await conn.execute(
                        "UPDATE inventario SET quantidade = quantidade - $1 WHERE id = $2",
                        qtd, row["id"]
                    )
                else:
                    await conn.execute("DELETE FROM inventario WHERE id = $1", row["id"])
        
        ex = await conn.fetchrow(
            "SELECT id FROM inventario WHERE user_id = $1 AND item_id = $2",
            interaction.user.id, receita["id"]
        )
        if ex:
            await conn.execute(
                "UPDATE inventario SET quantidade = quantidade + 1 WHERE id = $1",
                ex["id"]
            )
        else:
            await conn.execute("""
                INSERT INTO inventario (user_id, item_id, nome, tipo, raridade, emoji, descricao)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, interaction.user.id, receita["id"], receita["nome"], receita["tipo"], receita["raridade"], receita["emoji"], receita["desc"])
    
    await interaction.followup.send(
        f"✅ Forjado: {receita['emoji']} **{receita['nome']}**!",
        ephemeral=True
    )