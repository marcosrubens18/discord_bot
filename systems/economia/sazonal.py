# systems/economia/sazonal.py — Loja Sazonal (itens rotativos)

import discord
from discord import app_commands
from datetime import date

from database.db import get_pool
from database.queries import get_personagem, add_item
from data.constantes import COR_PRIMARY, COR_SUCCESS


async def init_db_loja_sazonal():
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS loja_sazonal (
                id SERIAL PRIMARY KEY,
                item_id TEXT NOT NULL,
                nome TEXT NOT NULL,
                emoji TEXT DEFAULT '📦',
                tipo TEXT DEFAULT 'material',
                raridade TEXT DEFAULT 'Raro',
                descricao TEXT DEFAULT '',
                preco INTEGER DEFAULT 500,
                estoque INTEGER DEFAULT -1,
                ativo BOOLEAN DEFAULT TRUE,
                criado_em TIMESTAMP DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS loja_rotativa (
                id SERIAL PRIMARY KEY,
                item_id TEXT NOT NULL,
                nome TEXT NOT NULL,
                emoji TEXT DEFAULT '📦',
                tipo TEXT DEFAULT 'material',
                raridade TEXT DEFAULT 'Raro',
                descricao TEXT DEFAULT '',
                preco INTEGER DEFAULT 300,
                data DATE DEFAULT CURRENT_DATE,
                estoque INTEGER DEFAULT 5
            )
        """)
    print("DB Loja Sazonal OK!")


class LojaItemModal(discord.ui.Modal, title="Adicionar Item Sazonal"):
    item_info = discord.ui.TextInput(
        label="ID | Nome | Emoji | Tipo | Raridade",
        placeholder="Ex: espada_gelo|Espada de Gelo|❄️|arma|Epico",
        max_length=150
    )
    preco_estoque = discord.ui.TextInput(
        label="Preço | Estoque (-1 = ilimitado)",
        placeholder="Ex: 2000|10  ou  500|-1",
        max_length=20
    )
    descricao = discord.ui.TextInput(
        label="Descrição do item",
        placeholder="Ex: Arma lendária do inverno eterno",
        max_length=200
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await init_db_loja_sazonal()
        
        try:
            partes = [x.strip() for x in str(self.item_info).split("|")]
            item_id = partes[0]
            nome = partes[1] if len(partes) > 1 else "Item"
            emoji = partes[2] if len(partes) > 2 else "📦"
            tipo = partes[3] if len(partes) > 3 else "material"
            raridade = partes[4] if len(partes) > 4 else "Raro"
        except:
            await interaction.followup.send("Formato inválido!", ephemeral=True)
            return
        
        try:
            pv = str(self.preco_estoque).split("|")
            preco = int(pv[0].strip()) if pv[0].strip().lstrip('-').isdigit() else 500
            estoque = int(pv[1].strip()) if len(pv) > 1 and pv[1].strip().lstrip('-').isdigit() else -1
        except:
            preco, estoque = 500, -1

        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO loja_sazonal(item_id, nome, emoji, tipo, raridade, descricao, preco, estoque)
                VALUES($1, $2, $3, $4, $5, $6, $7, $8)
            """, item_id, nome, emoji, tipo, raridade, str(self.descricao), preco, estoque)
        
        est_txt = str(estoque) if estoque >= 0 else "Ilimitado"
        await interaction.followup.send(
            f"✅ Item sazonal adicionado!\n{emoji} **{nome}** [{raridade}] — {preco} moedas | Estoque: {est_txt}",
            ephemeral=True
        )


class LojaRotativaModal(discord.ui.Modal, title="Adicionar Item Rotativo"):
    item_info = discord.ui.TextInput(
        label="ID | Nome | Emoji | Tipo | Raridade",
        placeholder="Ex: pocao_exp|Poção de XP|✨|pocao|Raro",
        max_length=150
    )
    preco_estoque = discord.ui.TextInput(
        label="Preço | Estoque",
        placeholder="Ex: 300|3",
        max_length=20
    )
    descricao = discord.ui.TextInput(
        label="Descrição",
        placeholder="Disponível somente hoje!",
        max_length=150,
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await init_db_loja_sazonal()
        
        try:
            partes = [x.strip() for x in str(self.item_info).split("|")]
            item_id = partes[0]
            nome = partes[1] if len(partes) > 1 else "Item"
            emoji = partes[2] if len(partes) > 2 else "📦"
            tipo = partes[3] if len(partes) > 3 else "material"
            raridade = partes[4] if len(partes) > 4 else "Raro"
        except:
            await interaction.followup.send("Formato inválido!", ephemeral=True)
            return
        
        try:
            pv = str(self.preco_estoque).split("|")
            preco = int(pv[0].strip()) if pv[0].strip().isdigit() else 300
            estoque = int(pv[1].strip()) if len(pv) > 1 and pv[1].strip().isdigit() else 3
        except:
            preco, estoque = 300, 3

        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO loja_rotativa(item_id, nome, emoji, tipo, raridade, descricao, preco, estoque)
                VALUES($1, $2, $3, $4, $5, $6, $7, $8)
            """, item_id, nome, emoji, tipo, raridade, str(self.descricao or ""), preco, estoque)
        
        await interaction.followup.send(
            f"✅ Item rotativo de hoje adicionado!\n{emoji} **{nome}** — {preco} moedas | Estoque: {estoque}",
            ephemeral=True
        )


async def cmd_loja_sazonal(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    await init_db_loja_sazonal()
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        itens_saz = await conn.fetch("SELECT * FROM loja_sazonal WHERE ativo=TRUE ORDER BY id DESC LIMIT 20")
        itens_rot = await conn.fetch("SELECT * FROM loja_rotativa WHERE data=CURRENT_DATE AND estoque>0 ORDER BY id")
        p = await conn.fetchrow("SELECT moedas FROM personagens WHERE user_id=$1", interaction.user.id)

    if not itens_saz and not itens_rot:
        await interaction.followup.send("Nenhum item disponível no momento!", ephemeral=True)
        return

    embed = discord.Embed(title="🌟 Loja Especial", color=0xD85A30,
                         description=f"Suas moedas: **{p['moedas'] if p else 0} 🪙**")

    if itens_rot:
        rot_txt = "\n".join([f"{i['emoji']} **{i['nome']}** [{i['raridade']}] — {i['preco']} 🪙 | Estoque: {i['estoque']}" for i in itens_rot])
        embed.add_field(name="🔄 Oferta do Dia", value=rot_txt, inline=False)
    if itens_saz:
        saz_txt = "\n".join([f"{i['emoji']} **{i['nome']}** [{i['raridade']}] — {i['preco']} 🪙" + (f" | Est: {i['estoque']}" if i['estoque'] >= 0 else "") for i in itens_saz])
        embed.add_field(name="✨ Itens Sazonais", value=saz_txt, inline=False)

    todos = list(itens_rot) + list(itens_saz)
    if not todos:
        await interaction.followup.send(embed=embed, ephemeral=True)
        return

    opcoes = [
        discord.SelectOption(
            label=f"{it['emoji']} {it['nome'][:40]}",
            value=f"{'rot' if it in itens_rot else 'saz'}_{it['id']}",
            description=f"{it['raridade']} — {it['preco']} moedas"
        )
        for it in todos[:25]
    ]

    class LojaView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)
            self.item = None
            self.tipo_id = None
            self.iid = None
        
        @discord.ui.select(placeholder="Escolha o item...", options=opcoes)
        async def sel(self, inter: discord.Interaction, s):
            if inter.user.id != interaction.user.id:
                return
            tipo_id, iid = s.values[0].split("_", 1)
            self.tipo_id = tipo_id
            self.iid = int(iid)
            await inter.response.defer()
            self.stop()

    v = LojaView()
    await interaction.followup.send(embed=embed, view=v, ephemeral=True)
    await v.wait()
    
    if not hasattr(v, 'iid'):
        return

    pool = await get_pool()
    async with pool.acquire() as conn:
        p2 = await conn.fetchrow("SELECT moedas FROM personagens WHERE user_id=$1", interaction.user.id)
        if v.tipo_id == "rot":
            it = await conn.fetchrow("SELECT * FROM loja_rotativa WHERE id=$1 AND estoque>0", v.iid)
        else:
            it = await conn.fetchrow("SELECT * FROM loja_sazonal WHERE id=$1 AND ativo=TRUE", v.iid)
        
        if not it:
            await interaction.followup.send("Item indisponível!", ephemeral=True)
            return
        
        if not p2 or p2["moedas"] < it["preco"]:
            await interaction.followup.send(f"Moedas insuficientes! Precisa de {it['preco']} 🪙", ephemeral=True)
            return
        
        await conn.execute("UPDATE personagens SET moedas = moedas - $1 WHERE user_id = $2", it["preco"], interaction.user.id)
        
        if v.tipo_id == "rot":
            await conn.execute("UPDATE loja_rotativa SET estoque = estoque - 1 WHERE id = $1", v.iid)
        elif it["estoque"] >= 0:
            await conn.execute("UPDATE loja_sazonal SET estoque = estoque - 1 WHERE id = $1", v.iid)
            if it["estoque"] - 1 <= 0:
                await conn.execute("UPDATE loja_sazonal SET ativo = FALSE WHERE id = $1", v.iid)
        
        ex = await conn.fetchrow("SELECT id FROM inventario WHERE user_id = $1 AND item_id = $2", interaction.user.id, it["item_id"])
        if ex:
            await conn.execute("UPDATE inventario SET quantidade = quantidade + 1 WHERE id = $1", ex["id"])
        else:
            await conn.execute("""
                INSERT INTO inventario(user_id, item_id, nome, tipo, raridade, emoji, descricao)
                VALUES($1, $2, $3, $4, $5, $6, $7)
            """, interaction.user.id, it["item_id"], it["nome"], it["tipo"], it["raridade"], it["emoji"], it.get("descricao", ""))
    
    await interaction.followup.send(f"✅ Comprou {it['emoji']} **{it['nome']}** por {it['preco']} 🪙!", ephemeral=True)


async def cmd_loja_sazonal_remover(interaction: discord.Interaction, item_id: int):
    await interaction.response.defer(ephemeral=True)
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("UPDATE loja_sazonal SET ativo = FALSE WHERE id = $1", item_id)
    await interaction.followup.send(f"✅ Item #{item_id} removido da loja sazonal!", ephemeral=True)