# party.py — Sistema de Party para Villa Eldoria RPG
import discord
from discord import app_commands
import asyncio
from datetime import datetime, timedelta
from db import get_pool

# ==================================================
# CONSTANTES
# ==================================================

MAX_MEMBROS_PADRAO = 5
TEMPO_CONVITE = 300  # 5 minutos em segundos

NIVEIS_PARTY = {
    1: {"xp_needed": 0, "bonus_xp": 0, "bonus_moedas": 0, "titulo": "Recruta", "cor": 0x888780},
    2: {"xp_needed": 500, "bonus_xp": 1, "bonus_moedas": 0, "titulo": "Grupo Unido", "cor": 0x7F77DD},
    3: {"xp_needed": 1500, "bonus_xp": 2, "bonus_moedas": 0, "titulo": "Equipe Leal", "cor": 0x378ADD},
    4: {"xp_needed": 3500, "bonus_xp": 3, "bonus_moedas": 0, "titulo": "Irmandade", "cor": 0x378ADD},
    5: {"xp_needed": 7000, "bonus_xp": 5, "bonus_moedas": 0, "titulo": "Clã Respeitado", "cor": 0x1D9E75},
    6: {"xp_needed": 12000, "bonus_xp": 7, "bonus_moedas": 0, "titulo": "Guerreiros Juntos", "cor": 0x1D9E75},
    7: {"xp_needed": 18000, "bonus_xp": 10, "bonus_moedas": 0, "titulo": "Força Coletiva", "cor": 0xE4AF3C},
    8: {"xp_needed": 25000, "bonus_xp": 12, "bonus_moedas": 5, "titulo": "Legião", "cor": 0xE4AF3C},
    9: {"xp_needed": 35000, "bonus_xp": 15, "bonus_moedas": 10, "titulo": "Exército", "cor": 0xD85A30},
    10: {"xp_needed": 50000, "bonus_xp": 20, "bonus_moedas": 15, "titulo": "Lenda Viva", "cor": 0xE24B4A},
}

BONUS_POR_MEMBROS = {
    2: 5,
    3: 10,
    4: 15,
    5: 20,
}

# ==================================================
# BANCO DE DADOS
# ==================================================

async def init_db_party():
    """Inicializa todas as tabelas do sistema de Party"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Tabela principal de Parties
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS parties (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                lider_id BIGINT NOT NULL,
                canal_id BIGINT DEFAULT 0,
                cargo_id BIGINT DEFAULT 0,
                nivel INTEGER DEFAULT 1,
                xp INTEGER DEFAULT 0,
                max_membros INTEGER DEFAULT 5,
                status TEXT DEFAULT 'ativa',
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Tabela de membros
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS party_membros (
                id SERIAL PRIMARY KEY,
                party_id INTEGER REFERENCES parties(id) ON DELETE CASCADE,
                user_id BIGINT NOT NULL,
                nome TEXT NOT NULL,
                classe_id TEXT,
                nivel INTEGER DEFAULT 1,
                entrou_em TIMESTAMP DEFAULT NOW(),
                UNIQUE(party_id, user_id)
            )
        """)
        
        # Tabela de convites pendentes
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS party_convites (
                id SERIAL PRIMARY KEY,
                party_id INTEGER REFERENCES parties(id) ON DELETE CASCADE,
                user_id BIGINT NOT NULL,
                convidado_id BIGINT NOT NULL,
                status TEXT DEFAULT 'pendente',
                criado_em TIMESTAMP DEFAULT NOW(),
                UNIQUE(party_id, convidado_id)
            )
        """)
        
        # Tabela de estatísticas
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS party_stats (
                id SERIAL PRIMARY KEY,
                party_id INTEGER REFERENCES parties(id) ON DELETE CASCADE,
                total_batalhas INTEGER DEFAULT 0,
                total_vitorias INTEGER DEFAULT 0,
                total_derrotas INTEGER DEFAULT 0,
                total_dungeons INTEGER DEFAULT 0,
                total_xp_ganho INTEGER DEFAULT 0,
                total_moedas_ganhas INTEGER DEFAULT 0
            )
        """)
        
        # Tabela de histórico
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS party_historico (
                id SERIAL PRIMARY KEY,
                party_id INTEGER REFERENCES parties(id) ON DELETE CASCADE,
                evento TEXT,
                descricao TEXT,
                data TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Tabela de níveis da Party
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS party_niveis (
                nivel INTEGER PRIMARY KEY,
                xp_necessario INTEGER NOT NULL,
                bonus_xp INTEGER DEFAULT 0,
                bonus_moedas INTEGER DEFAULT 0,
                titulo TEXT DEFAULT '',
                cor INTEGER DEFAULT 0x7F77DD
            )
        """)
        
        # Insere níveis se não existirem
        for nivel, dados in NIVEIS_PARTY.items():
            await conn.execute("""
                INSERT INTO party_niveis (nivel, xp_necessario, bonus_xp, bonus_moedas, titulo, cor)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (nivel) DO UPDATE SET
                    xp_necessario = EXCLUDED.xp_necessario,
                    bonus_xp = EXCLUDED.bonus_xp,
                    bonus_moedas = EXCLUDED.bonus_moedas,
                    titulo = EXCLUDED.titulo,
                    cor = EXCLUDED.cor
            """, nivel, dados["xp_needed"], dados["bonus_xp"], dados["bonus_moedas"], dados["titulo"], dados["cor"])
        
        # Adiciona colunas extras se necessário
        try:
            await conn.execute("ALTER TABLE parties ADD COLUMN IF NOT EXISTS dungeon_atual TEXT DEFAULT ''")
            await conn.execute("ALTER TABLE parties ADD COLUMN IF NOT EXISTS dungeon_andar INTEGER DEFAULT 0")
        except:
            pass
    
    print("DB Party OK!")

# ==================================================
# FUNÇÕES AUXILIARES
# ==================================================

async def get_party_do_jogador(user_id: int):
    """Retorna a party de um jogador, ou None se não tiver"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        membro = await conn.fetchrow("""
            SELECT pm.*, p.* 
            FROM party_membros pm
            JOIN parties p ON pm.party_id = p.id
            WHERE pm.user_id = $1 AND p.status = 'ativa'
        """, user_id)
        return dict(membro) if membro else None

async def get_membros_party(party_id: int):
    """Retorna lista de membros da party"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch("""
            SELECT * FROM party_membros WHERE party_id = $1 ORDER BY entrou_em
        """, party_id)

async def get_stats_party(party_id: int):
    """Retorna estatísticas da party"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        stats = await conn.fetchrow("SELECT * FROM party_stats WHERE party_id = $1", party_id)
        if not stats:
            await conn.execute("INSERT INTO party_stats (party_id) VALUES ($1)", party_id)
            stats = await conn.fetchrow("SELECT * FROM party_stats WHERE party_id = $1", party_id)
        return dict(stats)

async def adicionar_xp_party(party_id: int, xp: int, guild):
    """Adiciona XP para a party e verifica level up"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        party = await conn.fetchrow("SELECT * FROM parties WHERE id = $1", party_id)
        if not party:
            return
        
        novo_xp = party["xp"] + xp
        nivel_atual = party["nivel"]
        nivel_novo = nivel_atual
        
        # Verifica level up
        while nivel_novo < 10:
            xp_necessario = NIVEIS_PARTY.get(nivel_novo + 1, {}).get("xp_needed", 999999)
            if novo_xp >= xp_necessario:
                nivel_novo += 1
            else:
                break
        
        await conn.execute("""
            UPDATE parties SET xp = $1, nivel = $2, updated_at = NOW()
            WHERE id = $3
        """, novo_xp, nivel_novo, party_id)
        
        # Atualiza estatísticas
        await conn.execute("""
            UPDATE party_stats SET total_xp_ganho = total_xp_ganho + $1
            WHERE party_id = $2
        """, xp, party_id)
        
        # Se subiu de nível, anuncia
        if nivel_novo > nivel_atual:
            await anunciar_level_up_party(party, nivel_novo, nivel_atual, guild)
        
        return nivel_novo > nivel_atual

async def anunciar_level_up_party(party, novo_nivel, nivel_antigo, guild):
    """Anuncia level up da party no canal dela"""
    info_novo = NIVEIS_PARTY.get(novo_nivel, {})
    
    if party["canal_id"]:
        canal = guild.get_channel(party["canal_id"])
        if canal:
            embed = discord.Embed(
                title=f"🎉 Level Up da Party!",
                description=f"**{party['nome']}** subiu para o **Nível {novo_nivel}**!\n"
                           f"Título: **{info_novo.get('titulo', '')}**\n\n"
                           f"Novos bônus:\n"
                           f"⭐ +{info_novo.get('bonus_xp', 0)}% XP\n"
                           f"🪙 +{info_novo.get('bonus_moedas', 0)}% Moedas",
                color=info_novo.get("cor", 0xE4AF3C)
            )
            await canal.send(embed=embed)
    
    # Registra no histórico
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO party_historico (party_id, evento, descricao)
            VALUES ($1, 'level_up', $2)
        """, party["id"], f"Party subiu para o nível {novo_nivel}")

async def calcular_bonus_party(participantes_ids: list, guild) -> int:
    """Calcula bônus de XP baseado nos membros da mesma party"""
    if len(participantes_ids) < 2:
        return 0
    
    # Pega a party do primeiro participante
    party = await get_party_do_jogador(participantes_ids[0])
    if not party:
        return 0
    
    # Verifica se todos são da mesma party
    for uid in participantes_ids:
        p = await get_party_do_jogador(uid)
        if not p or p["id"] != party["id"]:
            return 0
    
    # Bônus baseado no número de membros
    qtd = len(participantes_ids)
    bonus = BONUS_POR_MEMBROS.get(min(qtd, 5), 0)
    
    # Adiciona bônus de nível da party
    nivel_info = NIVEIS_PARTY.get(party["nivel"], {})
    bonus += nivel_info.get("bonus_xp", 0)
    
    return bonus

async def adicionar_historico_party(party_id: int, evento: str, descricao: str):
    """Adiciona evento ao histórico da party"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO party_historico (party_id, evento, descricao, data)
            VALUES ($1, $2, $3, NOW())
        """, party_id, evento, descricao)

# ==================================================
# CRIAÇÃO DA PARTY
# ==================================================

class CriarPartyModal(discord.ui.Modal, title="Criar Nova Party"):
    nome = discord.ui.TextInput(
        label="Nome da Party",
        placeholder="Ex: Guardiões da Alvorada",
        max_length=50
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        # Verifica se já tem party
        party_existente = await get_party_do_jogador(interaction.user.id)
        if party_existente:
            await interaction.followup.send("❌ Você já faz parte de uma party! Use `/party sair` primeiro.", ephemeral=True)
            return
        
        pool = await get_pool()
        async with pool.acquire() as conn:
            # Cria a party
            party = await conn.fetchrow("""
                INSERT INTO parties (nome, lider_id, max_membros)
                VALUES ($1, $2, $3)
                RETURNING *
            """, self.nome.value, interaction.user.id, MAX_MEMBROS_PADRAO)
            
            # Adiciona líder como membro
            p = await conn.fetchrow("SELECT nome, classe_id, nivel FROM personagens WHERE user_id = $1", interaction.user.id)
            await conn.execute("""
                INSERT INTO party_membros (party_id, user_id, nome, classe_id, nivel)
                VALUES ($1, $2, $3, $4, $5)
            """, party["id"], interaction.user.id, p["nome"], p["classe_id"], p["nivel"])
            
            # Cria estatísticas
            await conn.execute("INSERT INTO party_stats (party_id) VALUES ($1)", party["id"])
            
            # Registra histórico
            await conn.execute("""
                INSERT INTO party_historico (party_id, evento, descricao)
                VALUES ($1, 'criacao', $2)
            """, party["id"], f"Party criada por {interaction.user.display_name}")
        
        # Cria cargo no Discord
        cargo = None
        try:
            cargo = await interaction.guild.create_role(
                name=f"🏰 {self.nome.value}",
                color=discord.Color.purple(),
                mentionable=True
            )
            await interaction.user.add_roles(cargo)
        except Exception as e:
            print(f"Erro ao criar cargo: {e}")
        
        # Cria canal privado
        canal = None
        try:
            cat = discord.utils.get(interaction.guild.categories, name="PARTIES")
            if not cat:
                cat = await interaction.guild.create_category("PARTIES")
            
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            }
            
            nome_canal = f"🏰┃{self.nome.value[:20].lower().replace(' ', '-')}"
            canal = await interaction.guild.create_text_channel(nome_canal, category=cat, overwrites=overwrites)
            
            # Mensagem de boas-vindas no canal
            embed = discord.Embed(
                title=f"🏰 {self.nome.value}",
                description=f"Bem-vindos ao canal da party!\n\n"
                           f"**Líder:** {interaction.user.mention}\n"
                           f"**Membros:** 1/{MAX_MEMBROS_PADRAO}\n\n"
                           f"Use `/party info` para ver detalhes.\n"
                           f"Use `/party convidar` para adicionar membros.",
                color=0x7F77DD
            )
            await canal.send(embed=embed)
            
        except Exception as e:
            print(f"Erro ao criar canal: {e}")
        
        # Atualiza party com IDs do Discord
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE parties SET cargo_id = $1, canal_id = $2 WHERE id = $3
            """, cargo.id if cargo else 0, canal.id if canal else 0, party["id"])
        
        embed_sucesso = discord.Embed(
            title="✅ Party Criada!",
            description=f"**{self.nome.value}** foi criada com sucesso!\n\n"
                       f"📢 Canal: {canal.mention if canal else 'Não criado'}\n"
                       f"👥 Limite: {MAX_MEMBROS_PADRAO} membros\n\n"
                       f"Use `/party convidar @jogador` para adicionar membros!",
            color=0x1D9E75
        )
        await interaction.followup.send(embed=embed_sucesso, ephemeral=True)

# ==================================================
# COMANDOS
# ==================================================

async def cmd_party_criar(interaction: discord.Interaction):
    """Cria uma nova party"""
    await interaction.response.send_modal(CriarPartyModal())

async def cmd_party_info(interaction: discord.Interaction):
    """Mostra informações da party"""
    await interaction.response.defer()
    
    party = await get_party_do_jogador(interaction.user.id)
    if not party:
        await interaction.followup.send("❌ Você não faz parte de nenhuma party!", ephemeral=True)
        return
    
    membros = await get_membros_party(party["id"])
    stats = await get_stats_party(party["id"])
    
    nivel_info = NIVEIS_PARTY.get(party["nivel"], NIVEIS_PARTY[1])
    proximo_nivel = NIVEIS_PARTY.get(party["nivel"] + 1)
    
    # Barra de XP
    if proximo_nivel:
        xp_need = proximo_nivel["xp_needed"] - party["xp"]
        xp_atual = party["xp"] - nivel_info["xp_needed"]
        xp_total = proximo_nivel["xp_needed"] - nivel_info["xp_needed"]
        pct = min(1.0, xp_atual / xp_total) if xp_total > 0 else 0
        f = int(pct * 10)
        barra = "█" * f + "░" * (10 - f)
        xp_txt = f"`{barra}` {xp_atual}/{xp_total} XP"
    else:
        xp_txt = "🏆 Nível Máximo!"
    
    # Lista de membros
    membros_txt = ""
    for m in membros:
        lider_txt = "👑 " if m["user_id"] == party["lider_id"] else "🛡️ "
        membros_txt += f"{lider_txt} {m['nome']} (Nv{m['nivel']})\n"
    
    embed = discord.Embed(
        title=f"🏰 {party['nome']}",
        color=nivel_info["cor"]
    )
    embed.add_field(name="👑 Líder", value=f"<@{party['lider_id']}>", inline=True)
    embed.add_field(name="📊 Nível", value=f"{party['nivel']} — {nivel_info['titulo']}", inline=True)
    embed.add_field(name="👥 Membros", value=f"{len(membros)}/{party['max_membros']}", inline=True)
    embed.add_field(name="⭐ XP da Party", value=xp_txt, inline=False)
    embed.add_field(name="🎯 Bônus Ativos", value=f"⭐ +{nivel_info['bonus_xp']}% XP\n🪙 +{nivel_info['bonus_moedas']}% Moedas", inline=True)
    embed.add_field(name="📊 Estatísticas", value=f"⚔️ {stats['total_batalhas']} batalhas\n🏆 {stats['total_vitorias']} vitórias\n🏰 {stats['total_dungeons']} dungeons", inline=True)
    embed.add_field(name="👥 Membros", value=membros_txt, inline=False)
    embed.add_field(name="📅 Criada em", value=f"<t:{int(party['created_at'].timestamp())}:R>", inline=True)
    embed.set_footer(text="Use /party sair para sair da party | /party convidar para adicionar membros")
    
    await interaction.followup.send(embed=embed)

async def cmd_party_convidar(interaction: discord.Interaction, jogador: discord.Member):
    """Convida um jogador para a party"""
    await interaction.response.defer(ephemeral=True)
    
    # Verifica se é líder
    party = await get_party_do_jogador(interaction.user.id)
    if not party:
        await interaction.followup.send("❌ Você não faz parte de nenhuma party!", ephemeral=True)
        return
    
    if party["lider_id"] != interaction.user.id:
        await interaction.followup.send("❌ Apenas o líder pode convidar membros!", ephemeral=True)
        return
    
    # Verifica limite
    membros = await get_membros_party(party["id"])
    if len(membros) >= party["max_membros"]:
        await interaction.followup.send(f"❌ Party cheia! Limite de {party['max_membros']} membros.", ephemeral=True)
        return
    
    # Verifica se jogador já tem party
    party_jogador = await get_party_do_jogador(jogador.id)
    if party_jogador:
        await interaction.followup.send(f"❌ {jogador.display_name} já faz parte de uma party!", ephemeral=True)
        return
    
    # Verifica se já tem convite pendente
    pool = await get_pool()
    async with pool.acquire() as conn:
        convite_existente = await conn.fetchrow("""
            SELECT * FROM party_convites 
            WHERE party_id = $1 AND convidado_id = $2 AND status = 'pendente'
        """, party["id"], jogador.id)
        
        if convite_existente:
            await interaction.followup.send(f"⏳ Já existe um convite pendente para {jogador.mention}!", ephemeral=True)
            return
        
        await conn.execute("""
            INSERT INTO party_convites (party_id, user_id, convidado_id)
            VALUES ($1, $2, $3)
        """, party["id"], interaction.user.id, jogador.id)
    
    # Envia DM com convite
    class ConviteView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=TEMPO_CONVITE)
        
        @discord.ui.button(label="✅ Aceitar", style=discord.ButtonStyle.success)
        async def aceitar(self, inter: discord.Interaction, button):
            if inter.user.id != jogador.id:
                await inter.response.send_message("❌ Este convite não é para você!", ephemeral=True)
                return
            
            await aceitar_convite(inter, party["id"])
            self.stop()
        
        @discord.ui.button(label="❌ Recusar", style=discord.ButtonStyle.danger)
        async def recusar(self, inter: discord.Interaction, button):
            if inter.user.id != jogador.id:
                await inter.response.send_message("❌ Este convite não é para você!", ephemeral=True)
                return
            
            await recusar_convite(inter, party["id"])
            self.stop()
    
    embed_convite = discord.Embed(
        title=f"🏰 Convite para Party!",
        description=f"**{interaction.user.display_name}** te convidou para entrar na party **{party['nome']}**!\n\n"
                   f"👥 Membros atuais: {len(membros)}/{party['max_membros']}\n"
                   f"📊 Nível da Party: {party['nivel']}\n\n"
                   f"⏱️ O convite expira em 5 minutos.",
        color=0x7F77DD
    )
    
    try:
        await jogador.send(embed=embed_convite, view=ConviteView())
        await interaction.followup.send(f"✅ Convite enviado para {jogador.mention}!", ephemeral=True)
    except:
        await interaction.followup.send(f"❌ Não foi possível enviar convite para {jogador.mention}. Ele pode ter as DMs desativadas.", ephemeral=True)

async def aceitar_convite(interaction: discord.Interaction, party_id: int):
    """Aceita o convite para a party"""
    await interaction.response.defer(ephemeral=True)
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        convite = await conn.fetchrow("""
            SELECT * FROM party_convites 
            WHERE party_id = $1 AND convidado_id = $2 AND status = 'pendente'
        """, party_id, interaction.user.id)
        
        if not convite:
            await interaction.followup.send("❌ Convite expirado ou inválido!", ephemeral=True)
            return
        
        party = await conn.fetchrow("SELECT * FROM parties WHERE id = $1", party_id)
        if not party or party["status"] != "ativa":
            await interaction.followup.send("❌ Esta party não existe mais!", ephemeral=True)
            return
        
        membros = await conn.fetch("SELECT * FROM party_membros WHERE party_id = $1", party_id)
        if len(membros) >= party["max_membros"]:
            await interaction.followup.send(f"❌ Party cheia! Limite de {party['max_membros']} membros.", ephemeral=True)
            return
        
        p = await conn.fetchrow("SELECT nome, classe_id, nivel FROM personagens WHERE user_id = $1", interaction.user.id)
        
        await conn.execute("""
            INSERT INTO party_membros (party_id, user_id, nome, classe_id, nivel)
            VALUES ($1, $2, $3, $4, $5)
        """, party_id, interaction.user.id, p["nome"], p["classe_id"], p["nivel"])
        
        await conn.execute("""
            UPDATE party_convites SET status = 'aceito' WHERE id = $1
        """, convite["id"])
        
        await conn.execute("""
            INSERT INTO party_historico (party_id, evento, descricao)
            VALUES ($1, 'entrada', $2)
        """, party_id, f"{p['nome']} entrou na party")
    
    # Adiciona cargo
    if party["cargo_id"]:
        cargo = interaction.guild.get_role(party["cargo_id"])
        if cargo:
            try:
                await interaction.user.add_roles(cargo)
            except:
                pass
    
    # Adiciona acesso ao canal
    if party["canal_id"]:
        canal = interaction.guild.get_channel(party["canal_id"])
        if canal:
            try:
                await canal.set_permissions(interaction.user, read_messages=True, send_messages=True)
                await canal.send(f"🎉 {interaction.user.mention} entrou na party! Bem-vindo!")
            except:
                pass
    
    await interaction.followup.send(f"✅ Você entrou na party **{party['nome']}**!", ephemeral=True)

async def recusar_convite(interaction: discord.Interaction, party_id: int):
    """Recusa o convite para a party"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE party_convites SET status = 'recusado' 
            WHERE party_id = $1 AND convidado_id = $2
        """, party_id, interaction.user.id)
    
    await interaction.response.send_message("❌ Você recusou o convite.", ephemeral=True)

async def cmd_party_sair(interaction: discord.Interaction):
    """Sai da party atual"""
    await interaction.response.defer(ephemeral=True)
    
    party = await get_party_do_jogador(interaction.user.id)
    if not party:
        await interaction.followup.send("❌ Você não faz parte de nenhuma party!", ephemeral=True)
        return
    
    # Verifica se é líder
    if party["lider_id"] == interaction.user.id:
        membros = await get_membros_party(party["id"])
        if len(membros) > 1:
            await interaction.followup.send("❌ Você é o líder! Transfira a liderança primeiro com `/party lider @jogador` ou encerre a party com `/party encerrar`.", ephemeral=True)
            return
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM party_membros WHERE party_id = $1 AND user_id = $2", party["id"], interaction.user.id)
        
        # Verifica se ficou vazia
        restantes = await conn.fetchval("SELECT COUNT(*) FROM party_membros WHERE party_id = $1", party["id"])
        if restantes == 0:
            await conn.execute("UPDATE parties SET status = 'encerrada' WHERE id = $1", party["id"])
            await conn.execute("INSERT INTO party_historico (party_id, evento, descricao) VALUES ($1, 'encerramento', 'Party encerrada por falta de membros')", party["id"])
        else:
            await conn.execute("""
                INSERT INTO party_historico (party_id, evento, descricao)
                VALUES ($1, 'saida', $2)
            """, party["id"], f"{interaction.user.display_name} saiu da party")
    
    # Remove cargo
    if party["cargo_id"]:
        cargo = interaction.guild.get_role(party["cargo_id"])
        if cargo:
            try:
                await interaction.user.remove_roles(cargo)
            except:
                pass
    
    # Remove acesso ao canal
    if party["canal_id"]:
        canal = interaction.guild.get_channel(party["canal_id"])
        if canal:
            try:
                await canal.set_permissions(interaction.user, overwrite=None)
                await canal.send(f"👋 {interaction.user.mention} saiu da party.")
            except:
                pass
    
    await interaction.followup.send(f"✅ Você saiu da party **{party['nome']}**.", ephemeral=True)

async def cmd_party_expulsar(interaction: discord.Interaction, jogador: discord.Member):
    """Expulsa um membro da party"""
    await interaction.response.defer(ephemeral=True)
    
    party = await get_party_do_jogador(interaction.user.id)
    if not party:
        await interaction.followup.send("❌ Você não faz parte de nenhuma party!", ephemeral=True)
        return
    
    if party["lider_id"] != interaction.user.id:
        await interaction.followup.send("❌ Apenas o líder pode expulsar membros!", ephemeral=True)
        return
    
    if jogador.id == interaction.user.id:
        await interaction.followup.send("❌ Você não pode se expulsar! Use `/party sair`.", ephemeral=True)
        return
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        membro = await conn.fetchrow("SELECT * FROM party_membros WHERE party_id = $1 AND user_id = $2", party["id"], jogador.id)
        if not membro:
            await interaction.followup.send(f"❌ {jogador.display_name} não é membro desta party!", ephemeral=True)
            return
        
        await conn.execute("DELETE FROM party_membros WHERE id = $1", membro["id"])
        await conn.execute("""
            INSERT INTO party_historico (party_id, evento, descricao)
            VALUES ($1, 'expulsao', $2)
        """, party["id"], f"{jogador.display_name} foi expulso da party")
    
    # Remove cargo
    if party["cargo_id"]:
        cargo = interaction.guild.get_role(party["cargo_id"])
        if cargo:
            try:
                await jogador.remove_roles(cargo)
            except:
                pass
    
    # Remove acesso ao canal
    if party["canal_id"]:
        canal = interaction.guild.get_channel(party["canal_id"])
        if canal:
            try:
                await canal.set_permissions(jogador, overwrite=None)
                await canal.send(f"👋 {jogador.mention} foi expulso da party.")
            except:
                pass
    
    await interaction.followup.send(f"✅ {jogador.display_name} foi expulso da party!", ephemeral=True)

async def cmd_party_lider(interaction: discord.Interaction, jogador: discord.Member):
    """Transfere liderança para outro membro"""
    await interaction.response.defer(ephemeral=True)
    
    party = await get_party_do_jogador(interaction.user.id)
    if not party:
        await interaction.followup.send("❌ Você não faz parte de nenhuma party!", ephemeral=True)
        return
    
    if party["lider_id"] != interaction.user.id:
        await interaction.followup.send("❌ Apenas o líder pode transferir a liderança!", ephemeral=True)
        return
    
    if jogador.id == interaction.user.id:
        await interaction.followup.send("❌ Você já é o líder!", ephemeral=True)
        return
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        membro = await conn.fetchrow("SELECT * FROM party_membros WHERE party_id = $1 AND user_id = $2", party["id"], jogador.id)
        if not membro:
            await interaction.followup.send(f"❌ {jogador.display_name} não é membro desta party!", ephemeral=True)
            return
        
        await conn.execute("UPDATE parties SET lider_id = $1 WHERE id = $2", jogador.id, party["id"])
        await conn.execute("""
            INSERT INTO party_historico (party_id, evento, descricao)
            VALUES ($1, 'lideranca', $2)
        """, party["id"], f"Liderança transferida para {jogador.display_name}")
    
    # Anuncia no canal
    if party["canal_id"]:
        canal = interaction.guild.get_channel(party["canal_id"])
        if canal:
            await canal.send(f"👑 **{jogador.mention}** é o novo líder da party!")
    
    await interaction.followup.send(f"✅ Liderança transferida para {jogador.display_name}!", ephemeral=True)

async def cmd_party_encerrar(interaction: discord.Interaction):
    """Encerra a party permanentemente"""
    await interaction.response.defer(ephemeral=True)
    
    party = await get_party_do_jogador(interaction.user.id)
    if not party:
        await interaction.followup.send("❌ Você não faz parte de nenhuma party!", ephemeral=True)
        return
    
    if party["lider_id"] != interaction.user.id:
        await interaction.followup.send("❌ Apenas o líder pode encerrar a party!", ephemeral=True)
        return
    
    # Confirmação
    class ConfirmarView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=30)
            self.confirmado = False
        
        @discord.ui.button(label="✅ Sim, encerrar party", style=discord.ButtonStyle.danger)
        async def confirmar(self, inter: discord.Interaction, button):
            if inter.user.id != interaction.user.id:
                await inter.response.send_message("❌ Apenas o líder pode confirmar!", ephemeral=True)
                return
            self.confirmado = True
            self.stop()
        
        @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.secondary)
        async def cancelar(self, inter: discord.Interaction, button):
            self.stop()
    
    embed_conf = discord.Embed(
        title="⚠️ Confirmar Encerramento",
        description=f"Tem certeza que deseja encerrar a party **{party['nome']}**?\n\n"
                   f"Isso irá:\n"
                   f"• Remover todos os membros\n"
                   f"• Deletar o canal da party\n"
                   f"• Remover o cargo da party\n\n"
                   f"**Esta ação não pode ser desfeita!**",
        color=0xE24B4A
    )
    
    view = ConfirmarView()
    await interaction.followup.send(embed=embed_conf, view=view, ephemeral=True)
    await view.wait()
    
    if not view.confirmado:
        await interaction.edit_original_response(content="❌ Encerramento cancelado.", embed=None, view=None)
        return
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Pega todos os membros
        membros = await conn.fetch("SELECT user_id FROM party_membros WHERE party_id = $1", party["id"])
        
        # Remove cargos
        if party["cargo_id"]:
            cargo = interaction.guild.get_role(party["cargo_id"])
            if cargo:
                for m in membros:
                    member = interaction.guild.get_member(m["user_id"])
                    if member:
                        try:
                            await member.remove_roles(cargo)
                        except:
                            pass
                try:
                    await cargo.delete()
                except:
                    pass
        
        # Remove canal
        if party["canal_id"]:
            canal = interaction.guild.get_channel(party["canal_id"])
            if canal:
                try:
                    await canal.delete()
                except:
                    pass
        
        await conn.execute("UPDATE parties SET status = 'encerrada' WHERE id = $1", party["id"])
        await conn.execute("""
            INSERT INTO party_historico (party_id, evento, descricao)
            VALUES ($1, 'encerramento', $2)
        """, party["id"], f"Party encerrada por {interaction.user.display_name}")
    
    await interaction.edit_original_response(content=f"✅ Party **{party['nome']}** foi encerrada!", embed=None, view=None)

async def cmd_party_painel(interaction: discord.Interaction):
    """Mostra painel completo da party"""
    await interaction.response.defer()
    
    party = await get_party_do_jogador(interaction.user.id)
    if not party:
        await interaction.followup.send("❌ Você não faz parte de nenhuma party!", ephemeral=True)
        return
    
    membros = await get_membros_party(party["id"])
    stats = await get_stats_party(party["id"])
    nivel_info = NIVEIS_PARTY.get(party["nivel"], NIVEIS_PARTY[1])
    
    # Busca histórico recente
    pool = await get_pool()
    async with pool.acquire() as conn:
        historico = await conn.fetch("""
            SELECT * FROM party_historico 
            WHERE party_id = $1 
            ORDER BY data DESC LIMIT 5
        """, party["id"])
    
    embed = discord.Embed(
        title=f"🏰 PAINEL DA PARTY — {party['nome']}",
        color=nivel_info["cor"]
    )
    
    # Informações principais
    embed.add_field(name="📊 Informações", 
                   value=f"👑 Líder: <@{party['lider_id']}>\n"
                         f"📈 Nível: {party['nivel']} — {nivel_info['titulo']}\n"
                         f"⭐ XP: {party['xp']} / {nivel_info['xp_needed'] if party['nivel'] < 10 else 'MAX'}\n"
                         f"👥 Membros: {len(membros)}/{party['max_membros']}", 
                   inline=False)
    
    # Bônus
    embed.add_field(name="🎯 Bônus Ativos", 
                   value=f"⭐ +{nivel_info['bonus_xp']}% XP em grupo\n"
                         f"🪙 +{nivel_info['bonus_moedas']}% Moedas\n"
                         f"🤝 Bônus por membros: +{BONUS_POR_MEMBROS.get(min(len(membros), 5), 0)}% XP",
                   inline=True)
    
    # Estatísticas
    embed.add_field(name="📊 Estatísticas", 
                   value=f"⚔️ Batalhas: {stats['total_batalhas']}\n"
                         f"🏆 Vitórias: {stats['total_vitorias']}\n"
                         f"💀 Derrotas: {stats['total_derrotas']}\n"
                         f"🏰 Dungeons: {stats['total_dungeons']}\n"
                         f"⭐ XP total: {stats['total_xp_ganho']}\n"
                         f"🪙 Moedas: {stats['total_moedas_ganhas']}",
                   inline=True)
    
    # Membros
    membros_txt = ""
    for m in membros:
        lider_txt = "👑 " if m["user_id"] == party["lider_id"] else "🛡️ "
        membros_txt += f"{lider_txt} {m['nome']} — Nv{m['nivel']}\n"
    embed.add_field(name="👥 Membros", value=membros_txt or "Nenhum", inline=False)
    
    # Histórico recente
    if historico:
        hist_txt = "\n".join([f"📌 {h['descricao'][:50]} — <t:{int(h['data'].timestamp())}:R>" for h in historico[:3]])
        embed.add_field(name="📜 Histórico Recente", value=hist_txt, inline=False)
    
    embed.set_footer(text="Party System • Villa Eldoria RPG")
    
    await interaction.followup.send(embed=embed)

async def cmd_party_convites(interaction: discord.Interaction):
    """Lista convites pendentes da party"""
    await interaction.response.defer(ephemeral=True)
    
    party = await get_party_do_jogador(interaction.user.id)
    if not party:
        await interaction.followup.send("❌ Você não faz parte de nenhuma party!", ephemeral=True)
        return
    
    if party["lider_id"] != interaction.user.id:
        await interaction.followup.send("❌ Apenas o líder pode ver os convites!", ephemeral=True)
        return
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        convites = await conn.fetch("""
            SELECT * FROM party_convites 
            WHERE party_id = $1 AND status = 'pendente'
            ORDER BY criado_em DESC
        """, party["id"])
    
    if not convites:
        await interaction.followup.send("📭 Nenhum convite pendente.", ephemeral=True)
        return
    
    embed = discord.Embed(
        title=f"📨 Convites Pendentes — {party['nome']}",
        color=0xE4AF3C
    )
    
    for c in convites:
        embed.add_field(
            name=f"Para: <@{c['convidado_id']}>",
            value=f"Enviado: <t:{int(c['criado_em'].timestamp())}:R>",
            inline=False
        )
    
    await interaction.followup.send(embed=embed, ephemeral=True)

# ==================================================
# FUNÇÕES DE INTEGRAÇÃO (para usar em batalha.py)
# ==================================================

async def registrar_batalha_party(user_ids: list, vitoria: bool, guild):
    """Registra uma batalha para os membros da party (usado em batalha.py)"""
    if len(user_ids) < 2:
        return
    
    # Verifica se todos são da mesma party
    party = await get_party_do_jogador(user_ids[0])
    if not party:
        return
    
    for uid in user_ids:
        p = await get_party_do_jogador(uid)
        if not p or p["id"] != party["id"]:
            return
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE party_stats 
            SET total_batalhas = total_batalhas + 1,
                total_vitorias = total_vitorias + $1,
                total_derrotas = total_derrotas + $2
            WHERE party_id = $3
        """, 1 if vitoria else 0, 0 if vitoria else 1, party["id"])
        
        # Adiciona XP para a party (10% do XP individual)
        xp_party = 5  # XP base por batalha
        await adicionar_xp_party(party["id"], xp_party, guild)

async def registrar_dungeon_party(user_ids: list, guild):
    """Registra uma dungeon completa para a party (para uso futuro)"""
    if len(user_ids) < 2:
        return
    
    party = await get_party_do_jogador(user_ids[0])
    if not party:
        return
    
    for uid in user_ids:
        p = await get_party_do_jogador(uid)
        if not p or p["id"] != party["id"]:
            return
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE party_stats 
            SET total_dungeons = total_dungeons + 1
            WHERE party_id = $1
        """, party["id"])
        
        # Adiciona XP extra para party por dungeon
        await adicionar_xp_party(party["id"], 25, guild)

async def get_bonus_party(participantes_ids: list, guild) -> int:
    """Retorna o bônus de XP para os participantes (usado em batalha.py)"""
    return await calcular_bonus_party(participantes_ids, guild)

# ==================================================
# REGISTRO DOS COMANDOS
# ==================================================

def register_party_commands(bot):
    """Registra todos os comandos de party no bot"""
    
    @bot.tree.command(name="party_criar", description="Cria uma nova party")
    async def party_criar(interaction: discord.Interaction):
        await cmd_party_criar(interaction)
    
    @bot.tree.command(name="party_info", description="Mostra informações da sua party")
    async def party_info(interaction: discord.Interaction):
        await cmd_party_info(interaction)
    
    @bot.tree.command(name="party_convidar", description="Convida um jogador para sua party")
    @app_commands.describe(jogador="Jogador a ser convidado")
    async def party_convidar(interaction: discord.Interaction, jogador: discord.Member):
        await cmd_party_convidar(interaction, jogador)
    
    @bot.tree.command(name="party_sair", description="Sai da sua party atual")
    async def party_sair(interaction: discord.Interaction):
        await cmd_party_sair(interaction)
    
    @bot.tree.command(name="party_expulsar", description="Expulsa um membro da party (apenas líder)")
    @app_commands.describe(jogador="Membro a ser expulso")
    async def party_expulsar(interaction: discord.Interaction, jogador: discord.Member):
        await cmd_party_expulsar(interaction, jogador)
    
    @bot.tree.command(name="party_lider", description="Transfere liderança para outro membro")
    @app_commands.describe(jogador="Novo líder")
    async def party_lider(interaction: discord.Interaction, jogador: discord.Member):
        await cmd_party_lider(interaction, jogador)
    
    @bot.tree.command(name="party_encerrar", description="Encerra sua party permanentemente (apenas líder)")
    async def party_encerrar(interaction: discord.Interaction):
        await cmd_party_encerrar(interaction)
    
    @bot.tree.command(name="party_painel", description="Mostra painel completo da party")
    async def party_painel(interaction: discord.Interaction):
        await cmd_party_painel(interaction)
    
    @bot.tree.command(name="party_convites", description="Lista convites pendentes da party")
    async def party_convites(interaction: discord.Interaction):
        await cmd_party_convites(interaction)