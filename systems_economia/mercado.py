# systems/economia/mercado.py — Sistema de Venda de Itens

import discord
import asyncio

from database.db import get_pool
from database.queries import get_personagem


# ==================================================
# CÁLCULO DE PREÇO DE VENDA
# ==================================================

PRECO_BASE = {
    "Comum": 50,
    "Incomum": 150,
    "Raro": 400,
    "Epico": 1000,
    "Lendario": 2500,
}

EMOJI_RAR = {
    "Comum": "⬜",
    "Incomum": "🟩",
    "Raro": "🟦",
    "Epico": "🟪",
    "Lendario": "🟧",
}


def calcular_preco_venda(raridade: str) -> int:
    """Calcula preço de venda baseado na raridade (metade do valor de compra)"""
    base = PRECO_BASE.get(raridade, 50)
    return base // 2


# ==================================================
# FUNÇÕES AUXILIARES
# ==================================================

async def get_inventario_completo(user_id: int):
    """Retorna todos os itens do inventário do usuário"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch(
            "SELECT * FROM inventario WHERE user_id = $1 ORDER BY raridade DESC, nome",
            user_id
        )


# ==================================================
# COMANDO MERCADO
# ==================================================

async def cmd_mercado_vender(interaction: discord.Interaction):
    """Comando /mercado - Vende itens do inventário"""
    await interaction.response.defer(ephemeral=True)
    
    p = await get_personagem(interaction.user.id)
    if not p:
        await interaction.followup.send("Crie seu personagem primeiro!", ephemeral=True)
        return

    itens = await get_inventario_completo(interaction.user.id)
    vendaveis = [i for i in itens if not i["equipado"]]

    if not vendaveis:
        await interaction.followup.send(
            embed=discord.Embed(
                title="🏪 Mercado — Vender Item",
                description="Você não tem itens disponíveis para venda.\n*(Itens equipados não podem ser vendidos)*",
                color=0x888780
            ),
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="🏪 Mercado — Vender Item",
        description=(
            f"Selecione um item para vender.\n"
            f"Os preços são calculados pelo mercado com base na raridade.\n\n"
            f"Moedas atuais: **{p['moedas']} 🪙**"
        ),
        color=0xE4AF3C
    )

    # Mostra tabela de preços
    preco_txt = " | ".join([f"{EMOJI_RAR[r]} {calcular_preco_venda(r)}🪙" for r in ["Comum", "Incomum", "Raro", "Epico", "Lendario"]])
    embed.add_field(name="📊 Preços de mercado", value=preco_txt, inline=False)

    opcoes = []
    for it in vendaveis[:25]:
        preco = calcular_preco_venda(it["raridade"])
        rar_e = EMOJI_RAR.get(it["raridade"], "⬜")
        qtd_txt = f" (x{it['quantidade']})" if it["quantidade"] > 1 else ""
        opcoes.append(discord.SelectOption(
            label=f"{it['emoji']} {it['nome']}{qtd_txt}",
            value=str(it["id"]),
            description=f"{rar_e} {it['raridade']} — Vende por {preco} 🪙"
        ))

    sel = discord.ui.Select(placeholder="Escolha o item para vender...", options=opcoes)

    async def confirmar_venda(inter: discord.Interaction):
        if inter.user.id != interaction.user.id:
            await inter.response.send_message("Não é você!", ephemeral=True)
            return
        await inter.response.defer()

        item_id_db = int(sel.values[0])
        item = next((i for i in vendaveis if i["id"] == item_id_db), None)
        if not item:
            await inter.followup.send("Item não encontrado!", ephemeral=True)
            return

        preco = calcular_preco_venda(item["raridade"])
        rar_e = EMOJI_RAR.get(item["raridade"], "⬜")

        class ConfView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=30)

            @discord.ui.button(label="✅ Confirmar", style=discord.ButtonStyle.success)
            async def sim(self, inter2: discord.Interaction, b):
                if inter2.user.id != interaction.user.id:
                    return
                await inter2.response.defer()
                pool = await get_pool()
                async with pool.acquire() as conn:
                    row = await conn.fetchrow("SELECT id, quantidade FROM inventario WHERE id = $1", item_id_db)
                    if not row:
                        await inter2.followup.send("Item não encontrado!", ephemeral=True)
                        return
                    if row["quantidade"] > 1:
                        await conn.execute("UPDATE inventario SET quantidade = quantidade - 1 WHERE id = $1", item_id_db)
                    else:
                        await conn.execute("DELETE FROM inventario WHERE id = $1", item_id_db)
                    await conn.execute("UPDATE personagens SET moedas = moedas + $1 WHERE user_id = $2", preco, inter2.user.id)

                p3 = await get_personagem(inter2.user.id)
                embed_ok = discord.Embed(
                    title="✅ Item vendido!",
                    description=(
                        f"{item['emoji']} **{item['nome']}** vendido!\n\n"
                        f"+**{preco} 🪙** recebidos\n"
                        f"Saldo atual: **{p3['moedas']} 🪙**"
                    ),
                    color=0x1D9E75
                )
                msg_ok = await inter2.followup.send(embed=embed_ok, wait=True)
                await asyncio.sleep(300)
                try:
                    await msg_ok.delete()
                except:
                    pass
                self.stop()

            @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.danger)
            async def nao(self, inter2: discord.Interaction, b):
                if inter2.user.id != interaction.user.id:
                    return
                await inter2.response.edit_message(content="Cancelado.", embed=None, view=None)
                self.stop()

        embed_conf = discord.Embed(
            title="⚠️ Confirmar venda?",
            description=(
                f"{item['emoji']} **{item['nome']}**\n"
                f"{rar_e} {item['raridade']}\n\n"
                f"Você receberá: **{preco} 🪙**\n\n"
                f"*Esta ação não pode ser desfeita!*"
            ),
            color=0xE4AF3C
        )
        await inter.followup.send(embed=embed_conf, view=ConfView(), ephemeral=True)

    sel.callback = confirmar_venda
    v = discord.ui.View(timeout=120)
    v.add_item(sel)
    msg = await interaction.followup.send(embed=embed, view=v, wait=True)
    await asyncio.sleep(300)
    try:
        await msg.delete()
    except:
        pass