# sistema_hospital.py — Sistema de Hospital e Cura (sem roleta)

import discord
from datetime import datetime, timedelta

from db import get_pool
from constants import PLANOS_HOSPITAL
from imagens import IMG_HOSPITAL


# ==================================================
# FUNÇÕES AUXILIARES
# ==================================================

async def get_descanso(user_id: int):
    """Retorna None se pode descansar, ou datetime do próximo descanso"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT proximo_descanso FROM descanso WHERE user_id = $1", user_id)
        if not row:
            return None
        if datetime.utcnow() >= row["proximo_descanso"]:
            return None
        return row["proximo_descanso"]


async def usar_descanso(user_id: int):
    """Usa o descanso grátis. Retorna o personagem atualizado ou None"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        proximo = datetime.utcnow() + timedelta(minutes=30)
        await conn.execute("""
            INSERT INTO descanso(user_id, proximo_descanso) VALUES($1, $2)
            ON CONFLICT(user_id) DO UPDATE SET proximo_descanso = $2
        """, user_id, proximo)
        p = await conn.fetchrow("SELECT hp_max, mana_max FROM personagens WHERE user_id = $1", user_id)
        if p:
            await conn.execute(
                "UPDATE personagens SET hp_atual = $1, mana_atual = $2 WHERE user_id = $3",
                p["hp_max"], p["mana_max"], user_id
            )
            return await conn.fetchrow("SELECT * FROM personagens WHERE user_id = $1", user_id)
    return None


async def get_personagem(user_id):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM personagens WHERE user_id = $1", user_id)


# ==================================================
# COMANDO HOSPITAL
# ==================================================

async def cmd_hospital(interaction: discord.Interaction):
    """Comando /hospital - Restaura HP e Mana"""
    await interaction.response.defer()
    
    p = await get_personagem(interaction.user.id)
    if not p:
        await interaction.followup.send("Crie seu personagem primeiro!", ephemeral=True)
        return

    hp_a = p["hp_atual"]
    hp_m = p["hp_max"]
    mana_a = p.get("mana_atual", 100)
    mana_m = p.get("mana_max", 100)

    embed = discord.Embed(
        title="🏥 Hospital da Cidade",
        color=0x1D9E75,
        description=f"Bem-vindo, **{p['nome']}**!\n\nHP: **{hp_a}/{hp_m}** | Mana: **{mana_a}/{mana_m}**\nMoedas: **{p['moedas']} 🪙**\n\nEscolha um plano:"
    )
    
    for pl in PLANOS_HOSPITAL:
        embed.add_field(name=f"{pl['emoji']} {pl['nome']} — {pl['preco']} 🪙", value=pl["desc"], inline=False)

    opcoes = [
        discord.SelectOption(
            label=f"{pl['emoji']} {pl['nome']} — {pl['preco']} moedas",
            value=pl["id"],
            description=pl["desc"]
        )
        for pl in PLANOS_HOSPITAL
    ]
    
    sel = discord.ui.Select(placeholder="Escolha o atendimento...", options=opcoes)

    async def escolher(inter: discord.Interaction):
        if inter.user.id != interaction.user.id:
            await inter.response.send_message("Não é você!", ephemeral=True)
            return
        
        plano = next((pl for pl in PLANOS_HOSPITAL if pl["id"] == sel.values[0]), None)
        if not plano:
            return
        
        p2 = await get_personagem(inter.user.id)
        if not p2:
            return
        
        if p2["moedas"] < plano["preco"]:
            await inter.response.send_message(f"Moedas insuficientes! Precisa de **{plano['preco']} 🪙**", ephemeral=True)
            return
        
        novo_hp = int(p2["hp_max"] * plano["hp_pct"])
        novo_mana = int((p2.get("mana_max", 100)) * plano["mana_pct"])
        
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE personagens SET hp_atual = $1, mana_atual = $2, moedas = moedas - $3 WHERE user_id = $4",
                novo_hp, novo_mana, plano["preco"], inter.user.id
            )
        
        ganho_hp = novo_hp - p2["hp_atual"]
        desc = f"{plano['emoji']} **{plano['nome']}** aplicado!\n\nHP: {p2['hp_atual']} → **{novo_hp}/{p2['hp_max']}** (+{max(0, ganho_hp)})\nMana: restaurada para **{novo_mana}**\n-{plano['preco']} 🪙"
        
        await inter.response.edit_message(
            embed=discord.Embed(title="Atendimento concluído!", description=desc, color=plano["cor"]),
            view=None
        )

    sel.callback = escolher
    v = discord.ui.View(timeout=60)
    v.add_item(sel)
    
    # Botão de descanso grátis
    proximo_desc = await get_descanso(interaction.user.id)
    pode_descansar = proximo_desc is None
    
    if not pode_descansar and proximo_desc:
        secs = max(0, int((proximo_desc - datetime.utcnow()).total_seconds()))
        mins = secs // 60
        segs = secs % 60
        desc_label = f"Descanso grátis disponível em {mins}min {segs}s"
    else:
        desc_label = "Descansar grátis (recupera tudo em 30 min)"
    
    btn_desc = discord.ui.Button(
        label=desc_label,
        style=discord.ButtonStyle.success if pode_descansar else discord.ButtonStyle.secondary,
        disabled=not pode_descansar,
        row=1
    )
    
    async def on_descanso(inter: discord.Interaction):
        if inter.user.id != interaction.user.id:
            return
        res = await usar_descanso(inter.user.id)
        if res:
            await inter.response.send_message(
                f"✅ Descansou e recuperou todo HP e Mana! Próximo descanso grátis em **30 minutos**.",
                ephemeral=True
            )
        else:
            await inter.response.send_message("❌ Erro ao descansar!", ephemeral=True)
    
    btn_desc.callback = on_descanso
    v.add_item(btn_desc)
    
    if IMG_HOSPITAL:
        embed.set_image(url=IMG_HOSPITAL)
    
    await interaction.followup.send(embed=embed, view=v)


# ==================================================
# INICIALIZAÇÃO DO BANCO DE DADOS DO HOSPITAL
# ==================================================

async def init_db_hospital():
    """Inicializa as tabelas do sistema de hospital"""
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            # Garantir que a tabela descanso existe
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS descanso (
                    user_id BIGINT PRIMARY KEY,
                    proximo_descanso TIMESTAMP DEFAULT NOW()
                )
            """)
        print("✅ DB Hospital inicializado")
    except Exception as e:
        print(f"⚠️ Erro ao inicializar DB Hospital: {e}")
