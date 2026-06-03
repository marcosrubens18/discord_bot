# torneio.py — Sistema de Torneios PvP com Canal Privado e Cargo Temporário
import discord
from discord import app_commands
import asyncio
import random
from datetime import datetime, timedelta
from db import get_pool
from batalha import rodar_pvp, ARENAS, BATALHAS_ATIVAS

# ==================================================
# CONSTANTES
# ==================================================

TEMPO_INSCRICAO_PADRAO = 48  # horas

# ==================================================
# BANCO DE DADOS
# ==================================================

async def init_db_torneio():
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS torneios (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                descricao TEXT DEFAULT '',
                imagem_url TEXT DEFAULT '',
                canal_id BIGINT DEFAULT 0,
                cargo_id BIGINT DEFAULT 0,
                msg_id BIGINT DEFAULT 0,
                valor_inscricao INTEGER DEFAULT 0,
                fim_inscricoes TIMESTAMP,
                premio_1 TEXT DEFAULT '',
                premio_2 TEXT DEFAULT '',
                premio_3 TEXT DEFAULT '',
                status TEXT DEFAULT 'inscricoes',
                fase_atual TEXT DEFAULT '',
                criado_por BIGINT,
                criado_em TIMESTAMP DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS torneio_inscritos (
                id SERIAL PRIMARY KEY,
                torneio_id INTEGER REFERENCES torneios(id),
                user_id BIGINT,
                nome TEXT,
                nivel INTEGER DEFAULT 1,
                rank TEXT DEFAULT 'F',
                eliminado BOOLEAN DEFAULT FALSE,
                inscrito_em TIMESTAMP DEFAULT NOW(),
                UNIQUE(torneio_id, user_id)
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS torneio_lutas (
                id SERIAL PRIMARY KEY,
                torneio_id INTEGER REFERENCES torneios(id),
                fase TEXT DEFAULT '',
                luta_num INTEGER DEFAULT 1,
                user1_id BIGINT DEFAULT 0,
                user2_id BIGINT DEFAULT 0,
                user1_nome TEXT DEFAULT '',
                user2_nome TEXT DEFAULT '',
                vencedor_id BIGINT DEFAULT 0,
                vencedor_nome TEXT DEFAULT '',
                bye BOOLEAN DEFAULT FALSE,
                concluida BOOLEAN DEFAULT FALSE
            )
        """)
    print("DB torneio OK!")

# ==================================================
# FUNÇÕES AUXILIARES
# ==================================================

def proxima_potencia_2(n):
    p = 1
    while p < n:
        p *= 2
    return p

def nome_fase(total_lutas):
    if total_lutas == 1:
        return "FINAL"
    if total_lutas == 2:
        return "SEMIFINAL"
    if total_lutas == 4:
        return "QUARTAS"
    if total_lutas == 8:
        return "OITAVAS"
    return f"RODADA {total_lutas}"

async def entregar_premio(guild, user_id, premio_str):
    """Entrega prêmio ao jogador"""
    if not premio_str or not premio_str.strip():
        return
    
    pool = await get_pool()
    try:
        async with pool.acquire() as conn:
            s = premio_str.lower().strip()
            member = guild.get_member(user_id)
            
            if "moedas" in s or s.isdigit():
                qtd = int("".join(filter(str.isdigit, s)) or "0")
                if qtd:
                    await conn.execute("UPDATE personagens SET moedas = moedas + $1 WHERE user_id = $2", qtd, user_id)
                    return
            
            if "xp" in s:
                qtd = int("".join(filter(str.isdigit, s)) or "0")
                if qtd:
                    await conn.execute("UPDATE personagens SET xp = xp + $1 WHERE user_id = $2", qtd, user_id)
                    return
            
            if "ficha" in s or "giro" in s:
                qtd = int("".join(filter(str.isdigit, s)) or "1")
                await conn.execute("""
                    INSERT INTO giros (user_id, roleta_id, raridade, quantidade)
                    VALUES ($1, 'skill', 'Lendario', $2)
                    ON CONFLICT (user_id, roleta_id, raridade)
                    DO UPDATE SET quantidade = giros.quantidade + $2
                """, user_id, qtd)
                return
            
            if "cargo:" in s:
                nome_cargo = s.split("cargo:")[-1].strip()
                if member:
                    cargo = discord.utils.get(guild.roles, name=nome_cargo)
                    if cargo:
                        await member.add_roles(cargo)
                return
            
            if "classe:" in s:
                classe = s.split("classe:")[-1].strip()
                await conn.execute("UPDATE personagens SET classe_id = $1 WHERE user_id = $2", classe, user_id)
                return
                
    except Exception as e:
        print(f"Erro premio: {e}")

# ==================================================
# MODAL DE CRIAÇÃO
# ==================================================

class CriarTorneioModal(discord.ui.Modal, title="Criar Torneio"):
    nome = discord.ui.TextInput(label="Nome do Torneio", max_length=50)
    descricao = discord.ui.TextInput(label="Descrição", style=discord.TextStyle.paragraph, max_length=300, required=False)
    imagem = discord.ui.TextInput(label="URL da Imagem", required=False, placeholder="https://...")
    inscricao_valor = discord.ui.TextInput(label="Valor da inscrição (moedas)", default="0")
    horas = discord.ui.TextInput(label="Duração das inscrições (horas)", default="48")
    
    premio1 = discord.ui.TextInput(label="🥇 1º Lugar", placeholder="Ex: 10000 moedas")
    premio2 = discord.ui.TextInput(label="🥈 2º Lugar", placeholder="Ex: 5000 moedas", required=False)
    premio3 = discord.ui.TextInput(label="🥉 3º Lugar", placeholder="Ex: 2000 moedas", required=False)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await init_db_torneio()
        
        try:
            valor = int(self.inscricao_valor.value)
        except:
            valor = 0
        
        try:
            horas = max(1, int(self.horas.value))
        except:
            horas = 48
        
        fim = datetime.utcnow() + timedelta(hours=horas)
        
        pool = await get_pool()
        async with pool.acquire() as conn:
            torneio = await conn.fetchrow("""
                INSERT INTO torneios (nome, descricao, imagem_url, valor_inscricao, fim_inscricoes, 
                                       premio_1, premio_2, premio_3, status, criado_por)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'inscricoes', $9)
                RETURNING *
            """, self.nome.value, self.descricao.value, self.imagem.value, 
                valor, fim, self.premio1.value, self.premio2.value, self.premio3.value, interaction.user.id)
        
        embed = discord.Embed(
            title=f"🏆 {self.nome.value}",
            description=self.descricao.value or "Torneio PvP",
            color=0xE4AF3C
        )
        embed.add_field(name="💰 Inscrição", value=f"{valor} moedas" if valor else "Gratuita", inline=True)
        embed.add_field(name="⏰ Inscrições até", value=f"<t:{int(fim.timestamp())}:R>", inline=True)
        embed.add_field(name="🏆 1º Lugar", value=self.premio1.value, inline=False)
        if self.premio2.value:
            embed.add_field(name="🥈 2º Lugar", value=self.premio2.value, inline=True)
        if self.premio3.value:
            embed.add_field(name="🥉 3º Lugar", value=self.premio3.value, inline=True)
        embed.set_footer(text=f"ID: {torneio['id']} • Use /torneio_inscrever {torneio['id']} para participar!")
        if self.imagem.value:
            embed.set_image(url=self.imagem.value)
        
        await interaction.followup.send(
            f"✅ Torneio **{self.nome.value}** criado! ID: `{torneio['id']}`\n"
            f"📢 Use `/torneio_inscrever {torneio['id']}` para se inscrever\n"
            f"🔒 Use `/torneio_fechar {torneio['id']}` para encerrar inscrições e gerar as chaves",
            ephemeral=True
        )
        
        # Mostra embed de divulgação no canal (opcional)
        canal = interaction.channel
        msg = await canal.send(embed=embed)
        async with pool.acquire() as conn:
            await conn.execute("UPDATE torneios SET msg_id = $1, canal_id = $2 WHERE id = $3", msg.id, canal.id, torneio["id"])

# ==================================================
# INSCREVER
# ==================================================

async def cmd_torneio_inscrever(interaction: discord.Interaction, torneio_id: int):
    await interaction.response.defer(ephemeral=True)
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        t = await conn.fetchrow("SELECT * FROM torneios WHERE id = $1 AND status = 'inscricoes'", torneio_id)
        if not t:
            await interaction.followup.send("❌ Torneio não encontrado ou inscrições encerradas!", ephemeral=True)
            return
        
        p = await conn.fetchrow("SELECT * FROM personagens WHERE user_id = $1", interaction.user.id)
        if not p:
            await interaction.followup.send("❌ Crie seu personagem primeiro!", ephemeral=True)
            return
        
        # Verifica se já está inscrito
        existe = await conn.fetchrow("SELECT id FROM torneio_inscritos WHERE torneio_id = $1 AND user_id = $2", torneio_id, interaction.user.id)
        if existe:
            await interaction.followup.send("❌ Você já está inscrito neste torneio!", ephemeral=True)
            return
        
        # Cobra inscrição
        if t["valor_inscricao"] > 0:
            if p["moedas"] < t["valor_inscricao"]:
                await interaction.followup.send(f"❌ Moedas insuficientes! Precisa de {t['valor_inscricao']} moedas.", ephemeral=True)
                return
            await conn.execute("UPDATE personagens SET moedas = moedas - $1 WHERE user_id = $2", t["valor_inscricao"], interaction.user.id)
        
        from catalogo import get_rank
        rank = get_rank(p["nivel"])["rank"]
        
        await conn.execute("""
            INSERT INTO torneio_inscritos (torneio_id, user_id, nome, nivel, rank)
            VALUES ($1, $2, $3, $4, $5)
        """, torneio_id, interaction.user.id, p["nome"], p["nivel"], rank)
        
        total = await conn.fetchval("SELECT COUNT(*) FROM torneio_inscritos WHERE torneio_id = $1", torneio_id)
    
    await interaction.followup.send(f"✅ Inscrito no torneio **{t['nome']}**! ({total} inscritos)", ephemeral=True)

# ==================================================
# FECHAR INSCRIÇÕES - CRIA CANAL, CARGO E CHAVES
# ==================================================

async def cmd_torneio_fechar(interaction: discord.Interaction, torneio_id: int):
    await interaction.response.defer(ephemeral=True)
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        t = await conn.fetchrow("SELECT * FROM torneios WHERE id = $1 AND status = 'inscricoes'", torneio_id)
        if not t:
            await interaction.followup.send("❌ Torneio não encontrado ou já encerrado!", ephemeral=True)
            return
        
        inscritos = await conn.fetch("SELECT * FROM torneio_inscritos WHERE torneio_id = $1 ORDER BY nivel DESC", torneio_id)
        
        if len(inscritos) < 2:
            await conn.execute("UPDATE torneios SET status = 'cancelado' WHERE id = $1", torneio_id)
            await interaction.followup.send("❌ Torneio cancelado! Número insuficiente de participantes (mínimo 2).", ephemeral=True)
            return
        
        # 1. CRIA CARGO TEMPORÁRIO
        cargo = await interaction.guild.create_role(
            name=f"🏆 {t['nome'][:20]}",
            color=discord.Color.gold(),
            mentionable=True
        )
        
        # 2. ADICIONA PARTICIPANTES AO CARGO
        for ins in inscritos:
            member = interaction.guild.get_member(ins["user_id"])
            if member:
                await member.add_roles(cargo)
        
        # 3. CRIA CANAL PRIVADO DO TORNEIO
        cat = discord.utils.get(interaction.guild.categories, name="TORNEIOS")
        if not cat:
            cat = await interaction.guild.create_category("TORNEIOS")
        
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            cargo: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }
        
        nome_canal = f"🏆┃{t['nome'][:25].lower().replace(' ', '-')}"
        canal = await interaction.guild.create_text_channel(nome_canal, category=cat, overwrites=overwrites)
        
        # 4. ATUALIZA BANCO
        await conn.execute("""
            UPDATE torneios SET status = 'em_andamento', canal_id = $1, cargo_id = $2
            WHERE id = $3
        """, canal.id, cargo.id, torneio_id)
        
        # 5. GERA CHAVES
        n = len(inscritos)
        pot2 = proxima_potencia_2(n)
        byes = pot2 - n
        fase = nome_fase(pot2 // 2)
        
        lista_ids = [i["user_id"] for i in inscritos]
        lista_nomes = [i["nome"] for i in inscritos]
        
        luta_num = 1
        
        # Byes (avançam automaticamente)
        for i in range(byes):
            await conn.execute("""
                INSERT INTO torneio_lutas (torneio_id, fase, luta_num, user1_id, user1_nome, bye, concluida)
                VALUES ($1, $2, $3, $4, $5, TRUE, TRUE)
            """, torneio_id, fase, luta_num, lista_ids[i], lista_nomes[i])
            luta_num += 1
        
        # Pares
        restantes_ids = lista_ids[byes:]
        restantes_nomes = lista_nomes[byes:]
        
        for i in range(0, len(restantes_ids) - 1, 2):
            await conn.execute("""
                INSERT INTO torneio_lutas (torneio_id, fase, luta_num, user1_id, user1_nome, user2_id, user2_nome)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, torneio_id, fase, luta_num, 
                restantes_ids[i], restantes_nomes[i],
                restantes_ids[i+1], restantes_nomes[i+1])
            luta_num += 1
        
        await conn.execute("UPDATE torneios SET fase_atual = $1 WHERE id = $2", fase, torneio_id)
    
    # 6. ENVIA MENSAGEM COM AS CHAVES
    await enviar_chaves(canal, torneio_id, t["nome"], fase, interaction.guild)
    
    await interaction.followup.send(f"✅ Torneio **{t['nome']}** iniciado!\n📢 Canal: {canal.mention}\n👥 Cargo: {cargo.mention}", ephemeral=True)

async def enviar_chaves(canal, torneio_id, nome_torneio, fase, guild):
    """Envia as chaves do torneio no canal"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        lutas = await conn.fetch("""
            SELECT * FROM torneio_lutas 
            WHERE torneio_id = $1 AND fase = $2 
            ORDER BY luta_num
        """, torneio_id, fase)
    
    embed = discord.Embed(
        title=f"🏆 {nome_torneio}",
        description=f"**Fase: {fase}**\n\nAs chaves foram sorteadas!",
        color=0xE4AF3C
    )
    
    for l in lutas:
        if l["bye"]:
            embed.add_field(
                name=f"⚡ Luta #{l['luta_num']} (BYE)",
                value=f"🔄 **{l['user1_nome']}** avança automaticamente!",
                inline=False
            )
        else:
            embed.add_field(
                name=f"⚔️ Luta #{l['luta_num']}",
                value=f"**{l['user1_nome']}** vs **{l['user2_nome']}**\n"
                      f"📌 Use `/torneio_lutar {torneio_id} {l['luta_num']}` para iniciar",
                inline=False
            )
    
    embed.set_footer(text="Use /torneio_status para ver o andamento")
    await canal.send(embed=embed)

# ==================================================
# LUTAR (INICIAR BATALHA DE UMA LUTA ESPECÍFICA)
# ==================================================

async def cmd_torneio_lutar(interaction: discord.Interaction, torneio_id: int, luta_num: int):
    await interaction.response.defer()
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        t = await conn.fetchrow("SELECT * FROM torneios WHERE id = $1 AND status = 'em_andamento'", torneio_id)
        if not t:
            await interaction.followup.send("❌ Torneio não encontrado ou não está em andamento!", ephemeral=True)
            return
        
        luta = await conn.fetchrow("""
            SELECT * FROM torneio_lutas 
            WHERE torneio_id = $1 AND luta_num = $2 AND concluida = FALSE AND bye = FALSE
        """, torneio_id, luta_num)
        
        if not luta:
            await interaction.followup.send("❌ Luta não encontrada, já concluída ou é BYE!", ephemeral=True)
            return
        
        # Pega os jogadores
        p1 = await conn.fetchrow("SELECT * FROM personagens WHERE user_id = $1", luta["user1_id"])
        p2 = await conn.fetchrow("SELECT * FROM personagens WHERE user_id = $1", luta["user2_id"])
        
        if not p1 or not p2:
            await interaction.followup.send("❌ Um dos jogadores não tem personagem!", ephemeral=True)
            return
        
        # Verifica se estão em batalha
        if luta["user1_id"] in BATALHAS_ATIVAS or luta["user2_id"] in BATALHAS_ATIVAS:
            await interaction.followup.send("❌ Um dos jogadores já está em batalha!", ephemeral=True)
            return
        
        membro1 = interaction.guild.get_member(luta["user1_id"])
        membro2 = interaction.guild.get_member(luta["user2_id"])
        
        arena = random.choice(ARENAS)
        
        embed_pre = discord.Embed(
            title=f"🏆 {t['nome']} — {t['fase_atual']}",
            description=f"**Luta #{luta_num}**\n\n"
                       f"⚔️ {membro1.mention if membro1 else luta['user1_nome']} vs {membro2.mention if membro2 else luta['user2_nome']}\n"
                       f"🏟️ Arena: {arena['emoji']} {arena['nome']}\n\n"
                       f"⚔️ A batalha vai começar!",
            color=0xE4AF3C
        )
        await interaction.followup.send(embed=embed_pre)
        
        # Callback para registrar resultado
        async def registrar_resultado(vencedor_id, perdedor_id):
            await _registrar_vencedor(torneio_id, luta["id"], vencedor_id, perdedor_id, interaction.guild, interaction.channel)
        
        # Inicia batalha
        await rodar_pvp(interaction.channel, p1, p2, membro1, membro2, arena, callback=registrar_resultado)

async def _registrar_vencedor(torneio_id, luta_id, vencedor_id, perdedor_id, guild, canal):
    """Registra vencedor e avança para próxima fase"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        luta = await conn.fetchrow("SELECT * FROM torneio_lutas WHERE id = $1", luta_id)
        if not luta or luta["concluida"]:
            return
        
        # Pega nomes
        vencedor_nome = await conn.fetchval("SELECT nome FROM personagens WHERE user_id = $1", vencedor_id)
        perdedor_nome = await conn.fetchval("SELECT nome FROM personagens WHERE user_id = $1", perdedor_id)
        
        # Atualiza luta
        await conn.execute("""
            UPDATE torneio_lutas 
            SET vencedor_id = $1, vencedor_nome = $2, concluida = TRUE
            WHERE id = $3
        """, vencedor_id, vencedor_nome, luta_id)
        
        # Marca perdedor como eliminado
        await conn.execute("""
            UPDATE torneio_inscritos SET eliminado = TRUE 
            WHERE torneio_id = $1 AND user_id = $2
        """, torneio_id, perdedor_id)
        
        # Anuncia resultado
        await canal.send(f"🏆 **{vencedor_nome}** venceu a luta e avançou para a próxima fase!")
        
        # Verifica se a fase atual terminou
        fase = luta["fase"]
        pendentes = await conn.fetchval("""
            SELECT COUNT(*) FROM torneio_lutas 
            WHERE torneio_id = $1 AND fase = $2 AND concluida = FALSE AND bye = FALSE
        """, torneio_id, fase)
        
        if pendentes > 0:
            return
        
        # Pega vencedores da fase
        vencedores = await conn.fetch("""
            SELECT vencedor_id, vencedor_nome FROM torneio_lutas 
            WHERE torneio_id = $1 AND fase = $2 AND concluida = TRUE
        """, torneio_id, fase)
        
        ids_v = [v["vencedor_id"] for v in vencedores]
        nomes_v = [v["vencedor_nome"] for v in vencedores]
        
        if len(ids_v) == 1:
            # TORNEIO FINALIZADO
            await conn.execute("UPDATE torneios SET status = 'finalizado' WHERE id = $1", torneio_id)
            t = await conn.fetchrow("SELECT * FROM torneios WHERE id = $1", torneio_id)
            
            # Entrega prêmios
            await entregar_premio(guild, ids_v[0], t["premio_1"])
            
            # Busca 2º e 3º lugar
            segundo = None
            terceiro = None
            
            # Pega finalistas
            final = await conn.fetchrow("""
                SELECT user1_id, user2_id, vencedor_id FROM torneio_lutas 
                WHERE torneio_id = $1 AND fase = 'FINAL'
            """, torneio_id)
            if final:
                segundo = final["user2_id"] if final["vencedor_id"] == final["user1_id"] else final["user1_id"]
            
            # Busca semifinalistas para 3º
            semis = await conn.fetch("""
                SELECT user1_id, user2_id, vencedor_id FROM torneio_lutas 
                WHERE torneio_id = $1 AND fase = 'SEMIFINAL'
            """, torneio_id)
            for sf in semis:
                perd = sf["user2_id"] if sf["vencedor_id"] == sf["user1_id"] else sf["user1_id"]
                if perd and perd != segundo and not terceiro:
                    terceiro = perd
            
            if segundo and t["premio_2"]:
                await entregar_premio(guild, segundo, t["premio_2"])
            if terceiro and t["premio_3"]:
                await entregar_premio(guild, terceiro, t["premio_3"])
            
            # Anuncia final
            campeao = guild.get_member(ids_v[0])
            embed_final = discord.Embed(
                title=f"🏆 TORNEIO FINALIZADO!",
                description=f"**{t['nome']}**\n\n"
                           f"🥇 **{campeao.mention if campeao else ids_v[0]}** é o campeão!\n\n"
                           f"🏆 Prêmio: {t['premio_1']}",
                color=0xE4AF3C
            )
            await canal.send(embed=embed_final)
            
            # Limpa cargo e canal após 1 minuto
            await asyncio.sleep(60)
            
            # Remove cargo
            if t["cargo_id"]:
                cargo = guild.get_role(t["cargo_id"])
                if cargo:
                    await cargo.delete()
            
            # Deleta canal
            if t["canal_id"]:
                canal_t = guild.get_channel(t["canal_id"])
                if canal_t:
                    await canal_t.delete()
            
        else:
            # PRÓXIMA FASE
            prox_fase = nome_fase(len(ids_v) // 2)
            await conn.execute("UPDATE torneios SET fase_atual = $1 WHERE id = $2", prox_fase, torneio_id)
            
            luta_num = 1
            for i in range(0, len(ids_v) - 1, 2):
                await conn.execute("""
                    INSERT INTO torneio_lutas (torneio_id, fase, luta_num, user1_id, user1_nome, user2_id, user2_nome)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, torneio_id, prox_fase, luta_num, ids_v[i], nomes_v[i], ids_v[i+1], nomes_v[i+1])
                luta_num += 1
            
            # Anuncia próxima fase
            embed_prox = discord.Embed(
                title=f"📢 PRÓXIMA FASE: {prox_fase}",
                description=f"Os vencedores avançaram! Use `/torneio_status {torneio_id}` para ver as novas chaves.",
                color=0x1D9E75
            )
            await canal.send(embed=embed_prox)
            
            # Mostra novas chaves
            await enviar_chaves(canal, torneio_id, t["nome"], prox_fase, guild)

# ==================================================
# STATUS DO TORNEIO
# ==================================================

async def cmd_torneio_status(interaction: discord.Interaction, torneio_id: int):
    await interaction.response.defer(ephemeral=True)
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        t = await conn.fetchrow("SELECT * FROM torneios WHERE id = $1", torneio_id)
        if not t:
            await interaction.followup.send("❌ Torneio não encontrado!", ephemeral=True)
            return
        
        inscritos = await conn.fetch("SELECT * FROM torneio_inscritos WHERE torneio_id = $1 ORDER BY nivel DESC", torneio_id)
        lutas = await conn.fetch("SELECT * FROM torneio_lutas WHERE torneio_id = $1 ORDER BY fase, luta_num", torneio_id)
    
    status_map = {
        "inscricoes": "📋 Inscrições abertas",
        "em_andamento": "⚔️ Em andamento",
        "finalizado": "🏆 Finalizado",
        "cancelado": "❌ Cancelado"
    }
    
    embed = discord.Embed(
        title=f"🏆 {t['nome']}",
        description=f"**Status:** {status_map.get(t['status'], t['status'])}\n"
                   f"**Inscritos:** {len(inscritos)}",
        color=0xE4AF3C
    )
    
    if t["status"] == "inscricoes" and t["fim_inscricoes"]:
        embed.add_field(name="⏰ Inscrições até", value=f"<t:{int(t['fim_inscricoes'].timestamp())}:R>", inline=True)
    
    if t["premio_1"]:
        embed.add_field(name="🏆 1º Lugar", value=t["premio_1"], inline=True)
    if t["premio_2"]:
        embed.add_field(name="🥈 2º Lugar", value=t["premio_2"], inline=True)
    if t["premio_3"]:
        embed.add_field(name="🥉 3º Lugar", value=t["premio_3"], inline=True)
    
    # Mostra chaves por fase
    fases = {}
    for l in lutas:
        fases.setdefault(l["fase"], []).append(l)
    
    for fase, fl in fases.items():
        txt = ""
        for l in fl:
            if l["bye"]:
                txt += f"🔄 BYE: **{l['user1_nome']}** (avançou)\n"
            elif l["concluida"]:
                txt += f"✅ **{l['user1_nome']}** vs **{l['user2_nome']}** → 🏆 **{l['vencedor_nome']}**\n"
            else:
                txt += f"⏳ **{l['user1_nome']}** vs **{l['user2_nome']}** (pendente)\n"
        if txt:
            embed.add_field(name=f"📌 {fase}", value=txt[:1000], inline=False)
    
    if t["imagem_url"]:
        embed.set_image(url=t["imagem_url"])
    
    await interaction.followup.send(embed=embed, ephemeral=True)

# ==================================================
# CANCELAR TORNEIO
# ==================================================

async def cmd_torneio_cancelar(interaction: discord.Interaction, torneio_id: int):
    await interaction.response.defer(ephemeral=True)
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        t = await conn.fetchrow("SELECT * FROM torneios WHERE id = $1", torneio_id)
        if not t:
            await interaction.followup.send("❌ Torneio não encontrado!", ephemeral=True)
            return
        
        # Devolve inscrições
        if t["valor_inscricao"] > 0 and t["status"] == "inscricoes":
            inscritos = await conn.fetch("SELECT user_id FROM torneio_inscritos WHERE torneio_id = $1", torneio_id)
            for ins in inscritos:
                await conn.execute("UPDATE personagens SET moedas = moedas + $1 WHERE user_id = $2", t["valor_inscricao"], ins["user_id"])
        
        await conn.execute("UPDATE torneios SET status = 'cancelado' WHERE id = $1", torneio_id)
        
        # Remove cargo se existir
        if t["cargo_id"]:
            cargo = interaction.guild.get_role(t["cargo_id"])
            if cargo:
                await cargo.delete()
        
        # Deleta canal se existir
        if t["canal_id"]:
            canal = interaction.guild.get_channel(t["canal_id"])
            if canal:
                await canal.delete()
    
    await interaction.followup.send(f"✅ Torneio **{t['nome']}** cancelado! Inscrições devolvidas.", ephemeral=True)

# ==================================================
# REGISTRO DOS COMANDOS
# ==================================================

def register_torneio_commands(bot):
    """Registra todos os comandos de torneio"""
    
    @bot.tree.command(name="torneio_criar", description="[ADMIN] Cria um novo torneio")
    @app_commands.checks.has_permissions(administrator=True)
    async def torneio_criar(interaction: discord.Interaction):
        await interaction.response.send_modal(CriarTorneioModal())
    
    @bot.tree.command(name="torneio_inscrever", description="Inscreve seu personagem no torneio")
    @app_commands.describe(torneio_id="ID do torneio")
    async def torneio_inscrever(interaction: discord.Interaction, torneio_id: int):
        await cmd_torneio_inscrever(interaction, torneio_id)
    
    @bot.tree.command(name="torneio_fechar", description="[ADMIN] Encerra inscrições e gera chaves")
    @app_commands.describe(torneio_id="ID do torneio")
    @app_commands.checks.has_permissions(administrator=True)
    async def torneio_fechar(interaction: discord.Interaction, torneio_id: int):
        await cmd_torneio_fechar(interaction, torneio_id)
    
    @bot.tree.command(name="torneio_lutar", description="[ADMIN] Inicia uma luta do torneio")
    @app_commands.describe(torneio_id="ID do torneio", luta_num="Número da luta")
    @app_commands.checks.has_permissions(administrator=True)
    async def torneio_lutar(interaction: discord.Interaction, torneio_id: int, luta_num: int):
        await cmd_torneio_lutar(interaction, torneio_id, luta_num)
    
    @bot.tree.command(name="torneio_status", description="Mostra status do torneio")
    @app_commands.describe(torneio_id="ID do torneio")
    async def torneio_status(interaction: discord.Interaction, torneio_id: int):
        await cmd_torneio_status(interaction, torneio_id)
    
    @bot.tree.command(name="torneio_cancelar", description="[ADMIN] Cancela um torneio")
    @app_commands.describe(torneio_id="ID do torneio")
    @app_commands.checks.has_permissions(administrator=True)
    async def torneio_cancelar(interaction: discord.Interaction, torneio_id: int):
        await cmd_torneio_cancelar(interaction, torneio_id)
