# expedicao_executor.py — Executa a expedição usando seu sistema de combate
import discord
import asyncio
import json
from db import get_pool
from expedicao_combate import rodar_combate_expedicao  # ← usa seu combate existente

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
        
        # Busca participantes inscritos
        participantes = await conn.fetch("""
            SELECT ep.*, p.hp_atual, p.hp_max, p.mana_atual, p.mana_max, p.ataque, p.defesa, p.raca_id 
            FROM expedicao_avancada_participantes ep
            JOIN personagens p ON ep.user_id = p.user_id
            WHERE ep.expedicao_id = $1
        """, exp_id)
        
        if not participantes:
            await interaction.followup.send("Nenhum participante inscrito!", ephemeral=True)
            return
        
        # Cria canal temporário
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
        
        nome_canal = f"🧭-{exp['nome'][:20].lower().replace(' ', '-')}"
        canal = await interaction.guild.create_text_channel(nome_canal, category=cat, overwrites=overwrites)
        
        # Busca capítulos
        capitulos = await conn.fetch("SELECT * FROM expedicao_capitulos WHERE expedicao_id=$1 ORDER BY ordem", exp_id)
        
        # Busca monstros personalizados
        monstros = {m["id"]: dict(m) for m in await conn.fetch("SELECT * FROM expedicao_monstros WHERE expedicao_id=$1", exp_id)}
        
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
        "monstros": monstros,
        "recompensas": [dict(r) for r in recompensas],
        "participantes": [dict(p) for p in participantes],
        "participantes_ids": [p["user_id"] for p in participantes],
        "participantes_vivos": [p["user_id"] for p in participantes],
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
    
    # Mensagem de boas-vindas
    embed = discord.Embed(
        title=f"🧭 {estado['expedicao']['nome']}",
        description=estado['expedicao']['descricao'] or "A aventura começou!",
        color=0x7F77DD
    )
    if estado['expedicao'].get('imagem_divulgacao'):
        embed.set_image(url=estado['expedicao']['imagem_divulgacao'])
    await canal.send(embed=embed)
    
    await asyncio.sleep(2)
    
    # Executa cada capítulo
    for idx, capitulo in enumerate(capitulos):
        estado["capitulo_atual"] = idx
        
        # Envia capítulo
        embed = discord.Embed(
            title=f"📖 {capitulo['titulo']}",
            description=capitulo['texto'],
            color=0x7F77DD
        )
        if capitulo.get('imagem'):
            embed.set_image(url=capitulo['imagem'])
        
        await canal.send(embed=embed)
        await asyncio.sleep(2)
        
        # Processa de acordo com o tipo
        if capitulo['tipo'] == 'combate':
            # Usa seu sistema de combate existente!
            await processar_combate(estado, capitulo)
        elif capitulo['tipo'] == 'escolha':
            await processar_escolha(estado, capitulo)
        elif capitulo['tipo'] == 'recompensa':
            await processar_recompensa(estado, capitulo)
        elif capitulo['tipo'] == 'loja':
            await processar_loja(estado, capitulo)
        elif capitulo['tipo'] == 'npc':
            await processar_npc(estado, capitulo)
        elif capitulo['tipo'] == 'narrativa':
            pass  # Já enviou a narrativa
        
        # Verifica se todos morreram
        if not estado.get("participantes_vivos"):
            await finalizar_expedicao(exp_id, sucesso=False)
            return
        
        await asyncio.sleep(1)
    
    # Finaliza com sucesso
    await finalizar_expedicao(exp_id, sucesso=True)

async def processar_combate(estado: dict, capitulo: dict):
    """Processa capítulo de combate usando o sistema existente"""
    canal = estado["canal"]
    config = json.loads(capitulo.get("config", "{}"))
    
    # Pega o monstro (pode ser personalizado ou do catálogo)
    monstro_nome = config.get("monstro_nome", "Goblin")
    monstro_id = config.get("monstro_id")
    quantidade = config.get("quantidade", 1)
    
    # Se tem monstro personalizado, usa ele
    if monstro_id and monstro_id in estado["monstros"]:
        monstro = estado["monstros"][monstro_id]
        monstro_nome = monstro["nome"]
        
        # Mostra ficha do monstro personalizado
        embed = discord.Embed(
            title=f"⚔️ {monstro['nome']} apareceu!",
            description=monstro['descricao'] or "Preparem-se para a batalha!",
            color=0xE24B4A
        )
        embed.add_field(name="❤️ Vida", value=monstro['vida'], inline=True)
        embed.add_field(name="⚔️ Ataque", value=monstro['ataque'], inline=True)
        embed.add_field(name="🛡️ Defesa", value=monstro['defesa'], inline=True)
        embed.add_field(name="🎯 Crítico", value=f"{monstro['critico']}%", inline=True)
        
        if monstro.get('imagem'):
            embed.set_image(url=monstro['imagem'])
        
        # Mostra habilidades
        habilidades = json.loads(monstro.get("habilidades", "[]"))
        if habilidades:
            texto_habs = "\n".join([f"✨ {h['nome']} - {h['dano']} dmg" for h in habilidades[:3]])
            embed.add_field(name="Habilidades", value=texto_habs, inline=False)
        
        await canal.send(embed=embed)
    
    await asyncio.sleep(2)
    
    # Usa o sistema de combate existente do servidor
    await canal.send(f"⚔️ **COMBATE CONTRA {quantidade}x {monstro_nome}!** ⚔️")
    
    try:
        resultado = await rodar_combate_expedicao(
            canal=canal,
            participantes_ids=estado["participantes_vivos"],
            nome_monstro=monstro_nome,
            quantidade=quantidade
        )
        
        # Atualiza participantes vivos
        estado["participantes_vivos"] = resultado["sobreviventes"]
        
        # Atualiza banco de dados
        pool = await get_pool()
        async with pool.acquire() as conn:
            for uid in resultado["derrotados"]:
                await conn.execute("""
                    UPDATE expedicao_avancada_participantes 
                    SET sobreviveu = FALSE 
                    WHERE expedicao_id = $1 AND user_id = $2
                """, estado["expedicao"]["id"], uid)
        
        if resultado["sucesso"]:
            await canal.send(f"✅ **VITÓRIA!** O {monstro_nome} foi derrotado!")
        else:
            await canal.send(f"💀 **DERROTA!** O grupo foi derrotado pelo {monstro_nome}...")
            
            # Se todos morreram, encerra expedição
            if not resultado["sobreviventes"]:
                await finalizar_expedicao(estado["expedicao"]["id"], sucesso=False)
                return
                
    except Exception as e:
        await canal.send(f"❌ Erro no combate: {e}")
        print(f"Erro no combate da expedição: {e}")

async def processar_escolha(estado: dict, capitulo: dict):
    """Processa capítulo de escolha"""
    canal = estado["canal"]
    config = json.loads(capitulo.get("config", "{}"))
    opcoes = config.get("opcoes", [])
    
    if not opcoes:
        return
    
    # Mostra opções
    desc_opcoes = "\n".join([f"**{i+1}.** {op}" for i, op in enumerate(opcoes)])
    embed = discord.Embed(
        title="🤔 Faça sua escolha!",
        description=f"{desc_opcoes}\n\nReaja com o número da sua escolha!",
        color=0xE4AF3C
    )
    msg = await canal.send(embed=embed)
    
    # Adiciona reações
    for i in range(len(opcoes)):
        await msg.add_reaction(f"{i+1}️⃣")
    
    # Aguarda votação (30 segundos)
    await asyncio.sleep(30)
    
    # Tenta remover as reações
    try:
        await msg.clear_reactions()
    except:
        pass
    
    await canal.send("✅ **Votação encerrada!** Continuando a jornada...")
    
    # Pega a opção mais votada (implementação simples)
    # Você pode expandir isso depois

async def processar_recompensa(estado: dict, capitulo: dict):
    """Processa capítulo de recompensa"""
    canal = estado["canal"]
    
    if not estado["recompensas"]:
        return
    
    embed = discord.Embed(
        title="💰 RECOMPENSAS!",
        description="Os aventureiros encontram tesouros pelo caminho!",
        color=0xE4AF3C
    )
    
    desc = []
    for r in estado["recompensas"]:
        if r["tipo"] == "moedas":
            desc.append(f"🪙 **{r['quantidade']} Moedas** para cada aventureiro")
        elif r["tipo"] == "xp":
            desc.append(f"⭐ **{r['quantidade']} XP** para cada aventureiro")
        elif r["tipo"] == "fichas":
            desc.append(f"🎰 **{r['quantidade']} Fichas** de roleta")
        else:
            desc.append(f"📦 **{r['quantidade']}x** {r['item_id']}")
    
    embed.description = "\n".join(desc)
    await canal.send(embed=embed)
    
    # Distribui recompensas (opcional - pode fazer no final)
    pool = await get_pool()
    async with pool.acquire() as conn:
        for p in estado["participantes_vivos"]:
            for r in estado["recompensas"]:
                if r["tipo"] == "moedas":
                    await conn.execute("UPDATE personagens SET moedas = moedas + $1 WHERE user_id = $2", 
                                       r["quantidade"], p)
                elif r["tipo"] == "xp":
                    await conn.execute("UPDATE personagens SET xp = xp + $1 WHERE user_id = $2", 
                                       r["quantidade"], p)

async def processar_loja(estado: dict, capitulo: dict):
    """Processa capítulo de loja temporária"""
    canal = estado["canal"]
    config = json.loads(capitulo.get("config", "{}"))
    itens = config.get("itens", [])
    
    if not itens:
        return
    
    embed = discord.Embed(
        title="🏪 LOJA TEMPORÁRIA",
        description="Um mercador viajante aparece! Aproveite as ofertas!",
        color=0x1D9E75
    )
    
    for item in itens:
        embed.add_field(
            name=f"{item.get('emoji', '📦')} {item.get('nome', 'Item')}",
            value=f"{item.get('preco', 0)} moedas | Estoque: {item.get('estoque', '∞')}",
            inline=True
        )
    
    await canal.send(embed=embed)
    await asyncio.sleep(5)
    await canal.send("💤 O mercador seguiu viagem...")

async def processar_npc(estado: dict, capitulo: dict):
    """Processa capítulo de NPC"""
    canal = estado["canal"]
    config = json.loads(capitulo.get("config", "{}"))
    
    embed = discord.Embed(
        title=f"👤 {config.get('nome', '???')}",
        description=f"*{config.get('dialogo', '...')}*",
        color=0x7F77DD
    )
    
    if config.get("imagem"):
        embed.set_thumbnail(url=config["imagem"])
    
    await canal.send(embed=embed)

async def finalizar_expedicao(exp_id: int, sucesso: bool = True):
    """Finaliza a expedição e limpa o canal"""
    estado = EXPEDICOES_ATIVAS.get(exp_id)
    if not estado:
        return
    
    canal = estado["canal"]
    exp = estado["expedicao"]
    
    # Mensagem final
    if sucesso:
        embed = discord.Embed(
            title="🏆 EXPEDIÇÃO CONCLUÍDA COM SUCESSO!",
            description=f"**{exp['nome']}**\n\nOs aventureiros completaram sua jornada e retornam como heróis!",
            color=0x1D9E75
        )
    else:
        embed = discord.Embed(
            title="💀 EXPEDIÇÃO FRACASSADA",
            description=f"**{exp['nome']}**\n\nOs aventureiros foram derrotados... A missão falhou.",
            color=0xE24B4A
        )
    
    if exp.get('imagem_final'):
        embed.set_image(url=exp['imagem_final'])
    
    await canal.send(embed=embed)
    
    # Aguarda 15 segundos e deleta o canal
    await asyncio.sleep(15)
    
    try:
        await canal.delete(reason="Expedição finalizada")
    except Exception as e:
        print(f"Erro ao deletar canal: {e}")
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("UPDATE expedicoes_avancadas SET status='finalizada' WHERE id=$1", exp_id)
        await conn.execute("UPDATE expedicao_sessoes SET ativa=FALSE WHERE expedicao_id=$1", exp_id)
    
    EXPEDICOES_ATIVAS.pop(exp_id, None)
    
    print(f"Expedição {exp_id} finalizada com {'sucesso' if sucesso else 'derrota'}")
