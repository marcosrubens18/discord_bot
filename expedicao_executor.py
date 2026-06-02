# expedicao_executor.py — Executa a expedição com base na configuração
import discord
import asyncio
import json
from db import get_pool

EXPEDICOES_ATIVAS = {}

async def iniciar_expedicao(interaction: discord.Interaction, exp_id: int):
    """Inicia a execução da expedição"""
    await interaction.response.defer(ephemeral=True)
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        exp = await conn.fetchrow("SELECT * FROM expedicoes_avancadas WHERE id=$1 AND status='rascunho'", exp_id)
        if not exp:
            await interaction.followup.send("Expedição não encontrada ou já finalizada!", ephemeral=True)
            return
        
        # Pega participantes (você precisará implementar inscrição)
        participantes = []  # TODO: buscar participantes
        
        # Cria canal
        cat = discord.utils.get(interaction.guild.categories, name="EXPEDIÇÕES")
        if not cat:
            cat = await interaction.guild.create_category("EXPEDIÇÕES")
        
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }
        
        for p in participantes:
            member = interaction.guild.get_member(p["user_id"])
            if member:
                overwrites[member] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        
        canal = await interaction.guild.create_text_channel(f"🧭-{exp['nome'][:20]}", category=cat, overwrites=overwrites)
        
        # Busca capítulos
        capitulos = await conn.fetch("SELECT * FROM expedicao_capitulos WHERE expedicao_id=$1 ORDER BY ordem", exp_id)
        
        # Busca monstros
        monstros = await conn.fetch("SELECT * FROM expedicao_monstros WHERE expedicao_id=$1", exp_id)
        
        # Busca recompensas
        recompensas = await conn.fetch("SELECT * FROM expedicao_recompensas WHERE expedicao_id=$1", exp_id)
        
        await conn.execute("UPDATE expedicoes_avancadas SET status='ativa' WHERE id=$1", exp_id)
        
        # Salva sessão
        sessao = await conn.fetchrow("""
            INSERT INTO expedicao_sessoes (expedicao_id, canal_id, ativa)
            VALUES ($1, $2, TRUE) RETURNING id
        """, exp_id, canal.id)
    
    # Estado da expedição
    EXPEDICOES_ATIVAS[exp_id] = {
        "expedicao": dict(exp),
        "canal": canal,
        "capitulos": [dict(c) for c in capitulos],
        "monstros": {m["id"]: dict(m) for m in monstros},
        "recompensas": [dict(r) for r in recompensas],
        "participantes": participantes,
        "guild": interaction.guild,
        "bot": interaction.client,
        "sessao_id": sessao["id"]
    }
    
    await interaction.followup.send(f"✅ Expedição **{exp['nome']}** iniciada em {canal.mention}", ephemeral=True)
    
    # Executa a expedição
    asyncio.create_task(executar_expedicao(exp_id))

async def executar_expedicao(exp_id: int):
    """Executa a expedição capítulo por capítulo"""
    estado = EXPEDICOES_ATIVAS.get(exp_id)
    if not estado:
        return
    
    canal = estado["canal"]
    capitulos = estado["capitulos"]
    
    await canal.send(f"🧭 **{estado['expedicao']['nome']}** começou!")
    
    if estado["expedicao"]["imagem_divulgacao"]:
        embed = discord.Embed(title="🎬 Aventura Iniciada!", color=0x7F77DD)
        embed.set_image(url=estado["expedicao"]["imagem_divulgacao"])
        await canal.send(embed=embed)
    
    for idx, capitulo in enumerate(capitulos):
        estado["capitulo_atual"] = idx
        
        embed = discord.Embed(
            title=f"📖 {capitulo['titulo']}",
            description=capitulo['texto'],
            color=0x7F77DD
        )
        
        if capitulo['imagem']:
            embed.set_image(url=capitulo['imagem'])
        
        await canal.send(embed=embed)
        await asyncio.sleep(2)
        
        if capitulo['tipo'] == 'escolha':
            await processar_escolha(estado, capitulo)
        elif capitulo['tipo'] == 'combate':
            await processar_combate(estado, capitulo)
        elif capitulo['tipo'] == 'recompensa':
            await processar_recompensa(estado, capitulo)
        elif capitulo['tipo'] == 'loja':
            await processar_loja(estado, capitulo)
        elif capitulo['tipo'] == 'npc':
            await processar_npc(estado, capitulo)
        
        await asyncio.sleep(1)
    
    # Finaliza expedição
    await finalizar_expedicao(exp_id)

async def processar_escolha(estado: dict, capitulo: dict):
    """Processa capítulo de escolha"""
    canal = estado["canal"]
    config = json.loads(capitulo.get("config", "{}"))
    opcoes = config.get("opcoes", [])
    
    if not opcoes:
        return
    
    embed = discord.Embed(
        title="🤔 Faça sua escolha!",
        description="\n".join([f"**{i+1}.** {op}" for i, op in enumerate(opcoes)]),
        color=0xE4AF3C
    )
    await canal.send(embed=embed)
    
    # Aguarda 30 segundos para votação
    await asyncio.sleep(30)
    await canal.send("✅ Votação encerrada! Continuando...")

async def processar_combate(estado: dict, capitulo: dict):
    """Processa capítulo de combate"""
    canal = estado["canal"]
    config = json.loads(capitulo.get("config", "{}"))
    monstro_id = config.get("monstro_id")
    
    if monstro_id and monstro_id in estado["monstros"]:
        monstro = estado["monstros"][monstro_id]
        
        embed = discord.Embed(
            title=f"⚔️ {monstro['nome']} apareceu!",
            description=monstro['descricao'] or "Preparem-se para a batalha!",
            color=0xE24B4A
        )
        embed.add_field(name="❤️ Vida", value=monstro['vida'], inline=True)
        embed.add_field(name="⚔️ Ataque", value=monstro['ataque'], inline=True)
        embed.add_field(name="🛡️ Defesa", value=monstro['defesa'], inline=True)
        
        if monstro['imagem']:
            embed.set_image(url=monstro['imagem'])
        
        await canal.send(embed=embed)
        
        # Aqui você chama o sistema de combate existente
        # from batalha import rodar_combate_expedicao
        # resultado = await rodar_combate_expedicao(canal, [p["user_id"] for p in estado["participantes"]], monstro["nome"], 1)
    
    await asyncio.sleep(2)

async def processar_recompensa(estado: dict, capitulo: dict):
    """Processa capítulo de recompensa"""
    canal = estado["canal"]
    config = json.loads(capitulo.get("config", "{}"))
    
    embed = discord.Embed(title="💰 Recompensas!", color=0xE4AF3C)
    desc = []
    
    for r in estado["recompensas"]:
        if r["tipo"] == "moedas":
            desc.append(f"🪙 {r['quantidade']} Moedas")
        elif r["tipo"] == "xp":
            desc.append(f"⭐ {r['quantidade']} XP")
        elif r["tipo"] == "fichas":
            desc.append(f"🎰 {r['quantidade']} Fichas")
        else:
            desc.append(f"📦 {r['quantidade']}x {r['item_id']}")
    
    embed.description = "\n".join(desc)
    await canal.send(embed=embed)

async def processar_loja(estado: dict, capitulo: dict):
    """Processa capítulo de loja temporária"""
    canal = estado["canal"]
    config = json.loads(capitulo.get("config", "{}"))
    itens = config.get("itens", [])
    
    embed = discord.Embed(title="🏪 LOJA TEMPORÁRIA", description="Aproveite as ofertas exclusivas!", color=0x1D9E75)
    
    for item in itens:
        embed.add_field(name=item.get("nome", "Item"), value=f"{item.get('preco', 0)} moedas", inline=True)
    
    await canal.send(embed=embed)

async def processar_npc(estado: dict, capitulo: dict):
    """Processa capítulo de NPC"""
    canal = estado["canal"]
    config = json.loads(capitulo.get("config", "{}"))
    
    embed = discord.Embed(
        title=f"👤 {config.get('nome', 'NPC')}",
        description=config.get("dialogo", "..."),
        color=0x7F77DD
    )
    
    if config.get("imagem"):
        embed.set_image(url=config["imagem"])
    
    await canal.send(embed=embed)

async def finalizar_expedicao(exp_id: int):
    """Finaliza a expedição e limpa o canal"""
    estado = EXPEDICOES_ATIVAS.get(exp_id)
    if not estado:
        return
    
    canal = estado["canal"]
    exp = estado["expedicao"]
    
    embed = discord.Embed(
        title="🏆 EXPEDIÇÃO CONCLUÍDA!",
        description=f"**{exp['nome']}**\n\nOs aventureiros completaram sua jornada!",
        color=0x1D9E75
    )
    
    if exp.get("imagem_final"):
        embed.set_image(url=exp["imagem_final"])
    
    await canal.send(embed=embed)
    
    # Aguarda 10 segundos e deleta o canal
    await asyncio.sleep(10)
    
    try:
        await canal.delete(reason="Expedição concluída")
    except:
        pass
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("UPDATE expedicoes_avancadas SET status='finalizada' WHERE id=$1", exp_id)
        await conn.execute("UPDATE expedicao_sessoes SET ativa=FALSE WHERE expedicao_id=$1", exp_id)
    
    EXPEDICOES_ATIVAS.pop(exp_id, None)