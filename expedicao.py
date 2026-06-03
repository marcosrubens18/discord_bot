# expedicao.py — Sistema de Expedições Simplificado e Funcional
import discord
from discord import app_commands
import json
import asyncio
from datetime import datetime, timedelta
from db import get_pool
from expedicao_combate import rodar_combate_expedicao
from catalogo import MATERIAIS_CAT, POCOES_CAT, ARMAS_POR_CLASSE, ARMADURAS_POR_CLASSE

# ==================================================
# BANCO DE DADOS
# ==================================================

async def init_db_expedicao():
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Cria tabela principal
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS expedicoes (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                descricao TEXT DEFAULT '',
                imagem_divulgacao TEXT DEFAULT '',
                nivel_minimo INTEGER DEFAULT 1,
                max_participantes INTEGER DEFAULT 5,
                status TEXT DEFAULT 'rascunho',
                recompensa_moedas INTEGER DEFAULT 0,
                recompensa_xp INTEGER DEFAULT 0,
                recompensa_fichas INTEGER DEFAULT 0,
                recompensa_materiais JSONB DEFAULT '[]',
                canal_divulgacao_id BIGINT DEFAULT 0,
                msg_divulgacao_id BIGINT DEFAULT 0,
                criado_por BIGINT,
                criado_em TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Cria tabela de participantes
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS expedicao_participantes (
                id SERIAL PRIMARY KEY,
                expedicao_id INTEGER REFERENCES expedicoes(id) ON DELETE CASCADE,
                user_id BIGINT,
                nome TEXT,
                nivel INTEGER DEFAULT 1,
                inscrito_em TIMESTAMP DEFAULT NOW(),
                UNIQUE(expedicao_id, user_id)
            )
        """)
        
        # Cria tabela de capítulos com TODAS as colunas
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS expedicao_capitulos (
                id SERIAL PRIMARY KEY,
                expedicao_id INTEGER REFERENCES expedicoes(id) ON DELETE CASCADE,
                ordem INTEGER DEFAULT 0,
                titulo TEXT NOT NULL,
                texto TEXT NOT NULL,
                imagem TEXT DEFAULT '',
                tipo TEXT DEFAULT 'narrativa',
                opcoes JSONB DEFAULT '[]',
                monstro_nome TEXT DEFAULT '',
                monstro_qtd INTEGER DEFAULT 1
            )
        """)
        
        # Se a tabela já existia mas sem as colunas, adiciona as que faltam
        try:
            await conn.execute("ALTER TABLE expedicao_capitulos ADD COLUMN IF NOT EXISTS opcoes JSONB DEFAULT '[]'")
        except:
            pass
        try:
            await conn.execute("ALTER TABLE expedicao_capitulos ADD COLUMN IF NOT EXISTS monstro_nome TEXT DEFAULT ''")
        except:
            pass
        try:
            await conn.execute("ALTER TABLE expedicao_capitulos ADD COLUMN IF NOT EXISTS monstro_qtd INTEGER DEFAULT 1")
        except:
            pass
    
    print("DB expedição OK!")

# ==================================================
# MODAL DE CRIAÇÃO DA EXPEDIÇÃO
# ==================================================

class CriarExpedicaoModal(discord.ui.Modal, title="Nova Expedição"):
    nome = discord.ui.TextInput(label="Nome da Expedição", max_length=50)
    descricao = discord.ui.TextInput(label="Descrição", style=discord.TextStyle.paragraph, max_length=300)
    imagem = discord.ui.TextInput(label="URL da imagem de divulgação", required=False, placeholder="https://...")
    nivel_min = discord.ui.TextInput(label="Nível mínimo", default="1")
    max_jogadores = discord.ui.TextInput(label="Máx. jogadores", default="5")
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await init_db_expedicao()
        
        pool = await get_pool()
        async with pool.acquire() as conn:
            exp = await conn.fetchrow("""
                INSERT INTO expedicoes (nome, descricao, imagem_divulgacao, nivel_minimo, max_participantes, criado_por, status)
                VALUES ($1, $2, $3, $4, $5, $6, 'rascunho') RETURNING id
            """, self.nome.value, self.descricao.value, self.imagem.value, int(self.nivel_min.value), int(self.max_jogadores.value), interaction.user.id)
        
        embed = discord.Embed(
            title="✅ Expedição Criada! (Rascunho)",
            description=f"**ID:** `{exp['id']}`\n**Nome:** {self.nome.value}\n\nAgora configure a expedição:",
            color=0x1D9E75
        )
        embed.add_field(name="➕ Adicionar capítulo", value=f"`/expedicao_add_capitulo {exp['id']}`", inline=False)
        embed.add_field(name="💰 Adicionar recompensa", value=f"`/expedicao_add_recompensa {exp['id']}`", inline=False)
        embed.add_field(name="📋 Ver expedição", value=f"`/expedicao_ver {exp['id']}`", inline=False)
        embed.add_field(name="📢 Publicar expedição", value=f"`/expedicao_publicar {exp['id']}`", inline=False)
        
        await interaction.followup.send(embed=embed, ephemeral=True)

# ==================================================
# MODAL PARA ADICIONAR CAPÍTULO
# ==================================================

class AdicionarCapituloModal(discord.ui.Modal, title="Adicionar Capítulo"):
    titulo = discord.ui.TextInput(label="Título do Capítulo", max_length=80)
    texto = discord.ui.TextInput(label="Texto narrativo", style=discord.TextStyle.paragraph)
    imagem = discord.ui.TextInput(label="URL da imagem (opcional)", required=False)
    
    def __init__(self, exp_id: int):
        super().__init__()
        self.exp_id = exp_id
    
    async def on_submit(self, interaction: discord.Interaction):
        view = EscolherTipoView(self.exp_id, self.titulo.value, self.texto.value, self.imagem.value)
        await interaction.response.send_message("**Escolha o tipo do capítulo:**", view=view, ephemeral=True)

class EscolherTipoView(discord.ui.View):
    def __init__(self, exp_id: int, titulo: str, texto: str, imagem: str):
        super().__init__(timeout=60)
        self.exp_id = exp_id
        self.titulo = titulo
        self.texto = texto
        self.imagem = imagem
    
    @discord.ui.select(
        placeholder="Tipo de capítulo",
        options=[
            discord.SelectOption(label="📖 Narrativa", value="narrativa", emoji="📖", description="Apenas texto e imagem"),
            discord.SelectOption(label="🤔 Escolha", value="escolha", emoji="🤔", description="Jogadores votam em uma opção"),
            discord.SelectOption(label="⚔️ Combate", value="combate", emoji="⚔️", description="Batalha contra monstro"),
            discord.SelectOption(label="💰 Recompensa", value="recompensa", emoji="💰", description="Distribui recompensas"),
        ]
    )
    async def select_tipo(self, interaction: discord.Interaction, select):
        tipo = select.values[0]
        
        if tipo == "escolha":
            modal = DefinirOpcoesModal(self.exp_id, self.titulo, self.texto, self.imagem)
            await interaction.response.send_modal(modal)
        elif tipo == "combate":
            modal = DefinirCombateModal(self.exp_id, self.titulo, self.texto, self.imagem)
            await interaction.response.send_modal(modal)
        else:
            pool = await get_pool()
            async with pool.acquire() as conn:
                ordem = await conn.fetchval("SELECT COALESCE(MAX(ordem), 0) + 1 FROM expedicao_capitulos WHERE expedicao_id=$1", self.exp_id)
                await conn.execute("""
                    INSERT INTO expedicao_capitulos (expedicao_id, ordem, titulo, texto, imagem, tipo)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, self.exp_id, ordem, self.titulo, self.texto, self.imagem, tipo)
            
            await interaction.response.edit_message(content=f"✅ Capítulo **{self.titulo}** adicionado!", view=None)

class DefinirOpcoesModal(discord.ui.Modal, title="Definir Opções"):
    opcao1 = discord.ui.TextInput(label="Opção 1", placeholder="Ex: Entrar pela porta da esquerda")
    opcao2 = discord.ui.TextInput(label="Opção 2", placeholder="Ex: Entrar pela porta da direita")
    opcao3 = discord.ui.TextInput(label="Opção 3 (opcional)", required=False)
    opcao4 = discord.ui.TextInput(label="Opção 4 (opcional)", required=False)
    
    def __init__(self, exp_id: int, titulo: str, texto: str, imagem: str):
        super().__init__()
        self.exp_id = exp_id
        self.titulo = titulo
        self.texto = texto
        self.imagem = imagem
    
    async def on_submit(self, interaction: discord.Interaction):
        opcoes = [self.opcao1.value, self.opcao2.value]
        if self.opcao3.value:
            opcoes.append(self.opcao3.value)
        if self.opcao4.value:
            opcoes.append(self.opcao4.value)
        
        pool = await get_pool()
        async with pool.acquire() as conn:
            ordem = await conn.fetchval("SELECT COALESCE(MAX(ordem), 0) + 1 FROM expedicao_capitulos WHERE expedicao_id=$1", self.exp_id)
            await conn.execute("""
                INSERT INTO expedicao_capitulos (expedicao_id, ordem, titulo, texto, imagem, tipo, opcoes)
                VALUES ($1, $2, $3, $4, $5, 'escolha', $6)
            """, self.exp_id, ordem, self.titulo, self.texto, self.imagem, json.dumps(opcoes))
        
        await interaction.response.send_message(f"✅ Capítulo de escolha **{self.titulo}** adicionado com {len(opcoes)} opções!", ephemeral=True)

class DefinirCombateModal(discord.ui.Modal, title="Definir Combate"):
    monstro_nome = discord.ui.TextInput(label="Nome do monstro", placeholder="Ex: Goblin, Lobo, Orc")
    quantidade = discord.ui.TextInput(label="Quantidade", default="1")
    
    def __init__(self, exp_id: int, titulo: str, texto: str, imagem: str):
        super().__init__()
        self.exp_id = exp_id
        self.titulo = titulo
        self.texto = texto
        self.imagem = imagem
    
    async def on_submit(self, interaction: discord.Interaction):
        pool = await get_pool()
        async with pool.acquire() as conn:
            ordem = await conn.fetchval("SELECT COALESCE(MAX(ordem), 0) + 1 FROM expedicao_capitulos WHERE expedicao_id=$1", self.exp_id)
            await conn.execute("""
                INSERT INTO expedicao_capitulos (expedicao_id, ordem, titulo, texto, imagem, tipo, monstro_nome, monstro_qtd)
                VALUES ($1, $2, $3, $4, $5, 'combate', $6, $7)
            """, self.exp_id, ordem, self.titulo, self.texto, self.imagem, self.monstro_nome.value, int(self.quantidade.value))
        
        await interaction.response.send_message(f"✅ Capítulo de combate **{self.titulo}** adicionado!", ephemeral=True)

# ==================================================
# MODAL PARA ADICIONAR RECOMPENSA
# ==================================================

class AdicionarRecompensaView(discord.ui.View):
    def __init__(self, exp_id: int):
        super().__init__(timeout=60)
        self.exp_id = exp_id
    
    @discord.ui.select(
        placeholder="Tipo de recompensa",
        options=[
            discord.SelectOption(label="🪙 Moedas", value="moedas"),
            discord.SelectOption(label="⭐ XP", value="xp"),
            discord.SelectOption(label="🎰 Fichas", value="fichas"),
            discord.SelectOption(label="📦 Material", value="material"),
        ]
    )
    async def select_tipo(self, interaction: discord.Interaction, select):
        tipo = select.values[0]
        
        if tipo in ["moedas", "xp", "fichas"]:
            modal = QuantidadeModal(self.exp_id, tipo)
            await interaction.response.send_modal(modal)
        elif tipo == "material":
            view = SelecionarMaterialView(self.exp_id)
            await interaction.response.send_message("**Selecione o material do catálogo:**", view=view, ephemeral=True)

class QuantidadeModal(discord.ui.Modal):
    quantidade = discord.ui.TextInput(label="Quantidade", default="1")
    
    def __init__(self, exp_id: int, tipo: str):
        super().__init__(title=f"Quantidade de {tipo}")
        self.exp_id = exp_id
        self.tipo = tipo
    
    async def on_submit(self, interaction: discord.Interaction):
        pool = await get_pool()
        async with pool.acquire() as conn:
            if self.tipo == "moedas":
                await conn.execute("UPDATE expedicoes SET recompensa_moedas = recompensa_moedas + $1 WHERE id = $2", 
                                   int(self.quantidade.value), self.exp_id)
            elif self.tipo == "xp":
                await conn.execute("UPDATE expedicoes SET recompensa_xp = recompensa_xp + $1 WHERE id = $2", 
                                   int(self.quantidade.value), self.exp_id)
            elif self.tipo == "fichas":
                await conn.execute("UPDATE expedicoes SET recompensa_fichas = recompensa_fichas + $1 WHERE id = $2", 
                                   int(self.quantidade.value), self.exp_id)
        
        await interaction.response.send_message(f"✅ Adicionado **{self.quantidade.value}** {self.tipo} como recompensa!", ephemeral=True)

class SelecionarMaterialView(discord.ui.View):
    def __init__(self, exp_id: int):
        super().__init__(timeout=60)
        self.exp_id = exp_id
        self.add_item(MaterialSelectMenu(exp_id))

class MaterialSelectMenu(discord.ui.Select):
    def __init__(self, exp_id: int):
        self.exp_id = exp_id
        options = []
        for m in MATERIAIS_CAT[:25]:
            options.append(discord.SelectOption(
                label=m["nome"][:50],
                value=m["id"],
                description=f"{m['raridade']}",
                emoji=m.get("emoji", "📦")
            ))
        super().__init__(placeholder="Selecione o material...", options=options, min_values=1, max_values=1)
    
    async def callback(self, interaction: discord.Interaction):
        modal = MaterialQuantidadeModal(self.exp_id, self.values[0])
        await interaction.response.send_modal(modal)

class MaterialQuantidadeModal(discord.ui.Modal, title="Quantidade do Material"):
    quantidade = discord.ui.TextInput(label="Quantidade", default="1")
    
    def __init__(self, exp_id: int, material_id: str):
        super().__init__()
        self.exp_id = exp_id
        self.material_id = material_id
    
    async def on_submit(self, interaction: discord.Interaction):
        pool = await get_pool()
        async with pool.acquire() as conn:
            materiais = await conn.fetchval("SELECT recompensa_materiais FROM expedicoes WHERE id=$1", self.exp_id)
            lista = json.loads(materiais) if materiais else []
            lista.append({"id": self.material_id, "quantidade": int(self.quantidade.value)})
            await conn.execute("UPDATE expedicoes SET recompensa_materiais = $1 WHERE id = $2", json.dumps(lista), self.exp_id)
        
        await interaction.response.send_message(f"✅ Adicionado **{self.quantidade.value}x** do material!", ephemeral=True)

# ==================================================
# FUNÇÕES DOS COMANDOS
# ==================================================

async def cmd_expedicao_criar(interaction: discord.Interaction):
    """Cria uma nova expedição"""
    await interaction.response.send_modal(CriarExpedicaoModal())

async def cmd_expedicao_add_capitulo(interaction: discord.Interaction, expedicao_id: int):
    """Adiciona um capítulo à expedição"""
    await interaction.response.send_modal(AdicionarCapituloModal(expedicao_id))

async def cmd_expedicao_add_recompensa(interaction: discord.Interaction, expedicao_id: int):
    """Adiciona recompensa à expedição"""
    view = AdicionarRecompensaView(expedicao_id)
    await interaction.response.send_message("**Selecione o tipo de recompensa:**", view=view, ephemeral=True)

async def cmd_expedicao_ver(interaction: discord.Interaction, expedicao_id: int):
    """Ver detalhes de uma expedição"""
    await interaction.response.defer(ephemeral=True)
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        exp = await conn.fetchrow("SELECT * FROM expedicoes WHERE id=$1", expedicao_id)
        if not exp:
            await interaction.followup.send("Expedição não encontrada!", ephemeral=True)
            return
        
        participantes = await conn.fetch("SELECT * FROM expedicao_participantes WHERE expedicao_id=$1", expedicao_id)
        capitulos = await conn.fetch("SELECT * FROM expedicao_capitulos WHERE expedicao_id=$1 ORDER BY ordem", expedicao_id)
    
    materiais = json.loads(exp["recompensa_materiais"]) if exp["recompensa_materiais"] else []
    
    status_emoji = {
        "rascunho": "📝 Rascunho",
        "aberta": "📢 Aberta para inscrições",
        "ativa": "⚔️ Em andamento",
        "finalizada": "🏁 Finalizada"
    }
    
    embed = discord.Embed(title=f"🧭 {exp['nome']}", description=exp['descricao'], color=0x7F77DD)
    embed.add_field(name="ID", value=str(exp['id']), inline=True)
    embed.add_field(name="Status", value=status_emoji.get(exp['status'], exp['status']), inline=True)
    embed.add_field(name="Nível mínimo", value=str(exp['nivel_minimo']), inline=True)
    embed.add_field(name="Participantes", value=f"{len(participantes)}/{exp['max_participantes']}", inline=True)
    
    recomp_txt = []
    if exp['recompensa_moedas'] > 0:
        recomp_txt.append(f"🪙 {exp['recompensa_moedas']} moedas")
    if exp['recompensa_xp'] > 0:
        recomp_txt.append(f"⭐ {exp['recompensa_xp']} XP")
    if exp['recompensa_fichas'] > 0:
        recomp_txt.append(f"🎰 {exp['recompensa_fichas']} fichas")
    for m in materiais:
        recomp_txt.append(f"📦 {m['quantidade']}x {m['id']}")
    
    embed.add_field(name="💰 Recompensas", value="\n".join(recomp_txt) or "Nenhuma", inline=False)
    
    capitulo_txt = "\n".join([f"**{c['ordem']}.** {c['titulo']} ({c['tipo']})" for c in capitulos]) or "Nenhum capítulo"
    embed.add_field(name="📖 Capítulos", value=capitulo_txt[:500], inline=False)
    
    await interaction.followup.send(embed=embed, ephemeral=True)

async def cmd_expedicao_listar(interaction: discord.Interaction):
    """Lista expedições abertas para inscrição"""
    await interaction.response.defer(ephemeral=True)
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        exps = await conn.fetch("""
            SELECT e.*, COUNT(ep.id) as inscritos
            FROM expedicoes e
            LEFT JOIN expedicao_participantes ep ON e.id = ep.expedicao_id
            WHERE e.status = 'aberta'
            GROUP BY e.id
            ORDER BY e.id DESC
        """)
    
    if not exps:
        await interaction.followup.send("Nenhuma expedição disponível no momento!", ephemeral=True)
        return
    
    embed = discord.Embed(title="🧭 Expedições Disponíveis", color=0x7F77DD)
    for exp in exps:
        embed.add_field(
            name=f"#{exp['id']} - {exp['nome']}",
            value=f"📝 {exp['descricao'][:60]}...\n🎯 Nv{exp['nivel_minimo']}+ | 👥 {exp['inscritos']}/{exp['max_participantes']}\n🔹 `/expedicao_inscrever {exp['id']}`",
            inline=False
        )
    await interaction.followup.send(embed=embed, ephemeral=True)

async def cmd_expedicao_inscrever(interaction: discord.Interaction, expedicao_id: int):
    """Inscreve seu personagem em uma expedição"""
    await interaction.response.defer(ephemeral=True)
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        exp = await conn.fetchrow("SELECT * FROM expedicoes WHERE id=$1 AND status='aberta'", expedicao_id)
        if not exp:
            await interaction.followup.send("Expedição não encontrada ou inscrições encerradas!", ephemeral=True)
            return
        
        p = await conn.fetchrow("SELECT * FROM personagens WHERE user_id=$1", interaction.user.id)
        if not p:
            await interaction.followup.send("Crie seu personagem primeiro!", ephemeral=True)
            return
        
        if p["nivel"] < exp["nivel_minimo"]:
            await interaction.followup.send(f"Nível insuficiente! Precisa de nível {exp['nivel_minimo']}.", ephemeral=True)
            return
        
        total = await conn.fetchval("SELECT COUNT(*) FROM expedicao_participantes WHERE expedicao_id=$1", expedicao_id)
        if total >= exp["max_participantes"]:
            await interaction.followup.send("Vagas esgotadas!", ephemeral=True)
            return
        
        await conn.execute("""
            INSERT INTO expedicao_participantes (expedicao_id, user_id, nome, nivel)
            VALUES ($1, $2, $3, $4)
        """, expedicao_id, interaction.user.id, p["nome"], p["nivel"])
        
        novo_total = total + 1
        
        # Atualiza mensagem de divulgação
        if exp["msg_divulgacao_id"]:
            canal = interaction.guild.get_channel(exp["canal_divulgacao_id"])
            if canal:
                try:
                    msg = await canal.fetch_message(exp["msg_divulgacao_id"])
                    if msg.embeds:
                        embed = msg.embeds[0]
                        for i, field in enumerate(embed.fields):
                            if field.name == "👥 Vagas":
                                embed.set_field_at(i, name="👥 Vagas", value=f"{novo_total}/{exp['max_participantes']}", inline=True)
                                break
                        await msg.edit(embed=embed)
                except:
                    pass
    
    await interaction.followup.send(f"✅ Inscrito em **{exp['nome']}**! ({novo_total}/{exp['max_participantes']})\nAguarde o início da expedição!", ephemeral=True)

async def cmd_expedicao_publicar(interaction: discord.Interaction, expedicao_id: int, canal: discord.TextChannel):
    """Publica a expedição em um canal para inscrições"""
    await interaction.response.defer(ephemeral=True)
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        exp = await conn.fetchrow("SELECT * FROM expedicoes WHERE id=$1 AND status='rascunho'", expedicao_id)
        if not exp:
            await interaction.followup.send("Expedição não encontrada ou já publicada!", ephemeral=True)
            return
        
        capitulos = await conn.fetchval("SELECT COUNT(*) FROM expedicao_capitulos WHERE expedicao_id=$1", expedicao_id)
        if capitulos == 0:
            await interaction.followup.send("Adicione pelo menos um capítulo antes de publicar!", ephemeral=True)
            return
        
        await conn.execute("""
            UPDATE expedicoes 
            SET status = 'aberta', canal_divulgacao_id = $1 
            WHERE id = $2
        """, canal.id, expedicao_id)
    
    materiais = json.loads(exp["recompensa_materiais"]) if exp["recompensa_materiais"] else []
    
    embed = discord.Embed(
        title=f"🧭 {exp['nome']}",
        description=exp['descricao'],
        color=0x7F77DD
    )
    if exp['imagem_divulgacao']:
        embed.set_image(url=exp['imagem_divulgacao'])
    
    embed.add_field(name="🎯 Nível mínimo", value=str(exp['nivel_minimo']), inline=True)
    embed.add_field(name="👥 Vagas", value=f"0/{exp['max_participantes']}", inline=True)
    
    recomp_txt = []
    if exp['recompensa_moedas'] > 0:
        recomp_txt.append(f"🪙 {exp['recompensa_moedas']} moedas")
    if exp['recompensa_xp'] > 0:
        recomp_txt.append(f"⭐ {exp['recompensa_xp']} XP")
    if exp['recompensa_fichas'] > 0:
        recomp_txt.append(f"🎰 {exp['recompensa_fichas']} fichas")
    for m in materiais:
        recomp_txt.append(f"📦 {m['quantidade']}x {m['id']}")
    
    if recomp_txt:
        embed.add_field(name="💰 Recompensas", value="\n".join(recomp_txt), inline=False)
    
    embed.set_footer(text=f"Expedição #{exp['id']} • Clique no botão abaixo para participar!")
    
    class ParticiparView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)
        
        @discord.ui.button(label="🧭 Participar da Expedição!", style=discord.ButtonStyle.success, emoji="🧭")
        async def participar(self, inter: discord.Interaction, button):
            await cmd_expedicao_inscrever(inter, expedicao_id)
    
    msg = await canal.send(embed=embed, view=ParticiparView())
    
    async with pool.acquire() as conn:
        await conn.execute("UPDATE expedicoes SET msg_divulgacao_id = $1 WHERE id = $2", msg.id, expedicao_id)
    
    await interaction.followup.send(f"✅ Expedição **{exp['nome']}** publicada em {canal.mention}!", ephemeral=True)

async def cmd_expedicao_iniciar(interaction: discord.Interaction, expedicao_id: int):
    """Inicia a expedição (admin)"""
    await interaction.response.defer(ephemeral=True)
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        exp = await conn.fetchrow("SELECT * FROM expedicoes WHERE id=$1 AND status='aberta'", expedicao_id)
        if not exp:
            await interaction.followup.send("Expedição não encontrada ou já iniciada!", ephemeral=True)
            return
        
        participantes = await conn.fetch("SELECT * FROM expedicao_participantes WHERE expedicao_id=$1", expedicao_id)
        if len(participantes) < 1:
            await interaction.followup.send("Nenhum participante inscrito!", ephemeral=True)
            return
        
        capitulos = await conn.fetch("SELECT * FROM expedicao_capitulos WHERE expedicao_id=$1 ORDER BY ordem", expedicao_id)
        if not capitulos:
            await interaction.followup.send("Nenhum capítulo configurado!", ephemeral=True)
            return
        
        await conn.execute("UPDATE expedicoes SET status='ativa' WHERE id=$1", expedicao_id)
    
    # Criar canal da expedição
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
    
    await interaction.followup.send(f"✅ Expedição **{exp['nome']}** iniciada em {canal.mention}", ephemeral=True)
    
    # Executar expedição
    await executar_expedicao(exp, participantes, capitulos, canal, interaction.guild, interaction.client)

# ==================================================
# EXECUÇÃO DA EXPEDIÇÃO
# ==================================================

async def executar_expedicao(exp, participantes, capitulos, canal, guild, bot):
    """Executa a expedição capítulo por capítulo"""
    participantes_vivos = [p["user_id"] for p in participantes]
    
    # Mensagem de boas-vindas
    embed = discord.Embed(
        title=f"🧭 {exp['nome']}",
        description=exp['descricao'],
        color=0x7F77DD
    )
    await canal.send(embed=embed)
    await canal.send(f"**Aventureiros:** {', '.join([p['nome'] for p in participantes])}\n\nA jornada começa!")
    
    await asyncio.sleep(2)
    
    for capitulo in capitulos:
        if not participantes_vivos:
            await canal.send("💀 **Todos os aventureiros foram derrotados!** A expedição falhou.")
            await finalizar_expedicao(exp, canal, guild, sucesso=False)
            return
        
        embed = discord.Embed(
            title=f"📖 {capitulo['titulo']}",
            description=capitulo['texto'],
            color=0x7F77DD
        )
        if capitulo['imagem']:
            embed.set_image(url=capitulo['imagem'])
        
        await canal.send(embed=embed)
        await asyncio.sleep(2)
        
        if capitulo['tipo'] == "escolha":
            opcoes = json.loads(capitulo['opcoes']) if capitulo['opcoes'] else []
            if opcoes:
                await processar_escolha(canal, bot, opcoes, participantes_vivos)
        
        elif capitulo['tipo'] == "combate":
            resultado = await processar_combate(canal, participantes_vivos, capitulo['monstro_nome'], capitulo['monstro_qtd'])
            participantes_vivos = resultado["sobreviventes"]
            
            if not participantes_vivos:
                await finalizar_expedicao(exp, canal, guild, sucesso=False)
                return
        
        elif capitulo['tipo'] == "recompensa":
            await processar_recompensa(canal, exp, participantes_vivos)
        
        await asyncio.sleep(1)
    
    await finalizar_expedicao(exp, canal, guild, sucesso=True, participantes_vivos=participantes_vivos)

async def processar_escolha(canal, bot, opcoes, participantes_vivos):
    """Processa escolha com votação por reações"""
    desc = "\n".join([f"{chr(127462 + i)} {op}" for i, op in enumerate(opcoes)])
    embed = discord.Embed(
        title="🤔 Faça sua escolha!",
        description=f"{desc}\n\nReaja com o emoji correspondente! (30 segundos)",
        color=0xE4AF3C
    )
    msg = await canal.send(embed=embed)
    
    for i in range(len(opcoes)):
        await msg.add_reaction(chr(127462 + i))
    
    await asyncio.sleep(30)
    
    msg = await canal.fetch_message(msg.id)
    votos = {}
    for i in range(len(opcoes)):
        for reaction in msg.reactions:
            if str(reaction.emoji) == chr(127462 + i):
                votos[i] = reaction.count - 1
                break
        if i not in votos:
            votos[i] = 0
    
    if sum(votos.values()) > 0:
        vencedor = max(votos, key=votos.get)
        await canal.send(f"📊 **Resultado:** A maioria escolheu **{opcoes[vencedor]}**! ({votos[vencedor]} voto(s))")
    else:
        await canal.send("📊 **Ninguém votou!** Continuando com a opção 1...")

async def processar_combate(canal, participantes_ids, monstro_nome, quantidade):
    """Processa combate usando o sistema existente"""
    await canal.send(f"⚔️ **COMBATE!** ⚔️\n{quantidade}x **{monstro_nome}** apareceu!")
    
    try:
        resultado = await rodar_combate_expedicao(
            canal=canal,
            participantes_ids=participantes_ids,
            nome_monstro=monstro_nome,
            quantidade=quantidade
        )
        
        if resultado["sucesso"]:
            await canal.send(f"✅ **VITÓRIA!** O {monstro_nome} foi derrotado!")
        else:
            await canal.send(f"💀 **DERROTA!** O grupo foi derrotado pelo {monstro_nome}...")
        
        return resultado
        
    except Exception as e:
        await canal.send(f"❌ Erro no combate: {e}")
        return {"sucesso": False, "sobreviventes": [], "derrotados": participantes_ids}

async def processar_recompensa(canal, exp, participantes_vivos):
    """Distribui recompensas"""
    materiais = json.loads(exp["recompensa_materiais"]) if exp["recompensa_materiais"] else []
    
    desc = []
    if exp["recompensa_moedas"] > 0:
        desc.append(f"🪙 **{exp['recompensa_moedas']} moedas** para cada")
    if exp["recompensa_xp"] > 0:
        desc.append(f"⭐ **{exp['recompensa_xp']} XP** para cada")
    if exp["recompensa_fichas"] > 0:
        desc.append(f"🎰 **{exp['recompensa_fichas']} fichas** para cada")
    for m in materiais:
        desc.append(f"📦 **{m['quantidade']}x** {m['id']}")
    
    embed = discord.Embed(
        title="💰 RECOMPENSAS!",
        description="Os aventureiros encontram tesouros!\n\n" + "\n".join(desc),
        color=0xE4AF3C
    )
    await canal.send(embed=embed)
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        for uid in participantes_vivos:
            if exp["recompensa_moedas"] > 0:
                await conn.execute("UPDATE personagens SET moedas = moedas + $1 WHERE user_id = $2", exp["recompensa_moedas"], uid)
            if exp["recompensa_xp"] > 0:
                await conn.execute("UPDATE personagens SET xp = xp + $1 WHERE user_id = $2", exp["recompensa_xp"], uid)
            if exp["recompensa_fichas"] > 0:
                await conn.execute("""
                    INSERT INTO giros (user_id, roleta_id, raridade, quantidade)
                    VALUES ($1, 'skill', 'Lendario', $2)
                    ON CONFLICT (user_id, roleta_id, raridade)
                    DO UPDATE SET quantidade = giros.quantidade + $2
                """, uid, exp["recompensa_fichas"])
            
            for m in materiais:
                ex = await conn.fetchrow("SELECT id, quantidade FROM inventario WHERE user_id=$1 AND item_id=$2", uid, m["id"])
                if ex:
                    await conn.execute("UPDATE inventario SET quantidade = quantidade + $1 WHERE id = $2", m["quantidade"], ex["id"])
                else:
                    material = next((mat for mat in MATERIAIS_CAT if mat["id"] == m["id"]), None)
                    if material:
                        await conn.execute("""
                            INSERT INTO inventario (user_id, item_id, nome, tipo, raridade, emoji, descricao)
                            VALUES ($1, $2, $3, 'material', $4, $5, $6)
                        """, uid, m["id"], material["nome"], material["raridade"], material.get("emoji", "📦"), material.get("desc", ""))

async def finalizar_expedicao(exp, canal, guild, sucesso=True, participantes_vivos=None):
    """Finaliza a expedição e limpa o canal"""
    
    if sucesso:
        embed = discord.Embed(
            title="🏆 EXPEDIÇÃO CONCLUÍDA!",
            description=f"**{exp['nome']}**\n\nOs aventureiros completaram sua jornada com sucesso!",
            color=0x1D9E75
        )
    else:
        embed = discord.Embed(
            title="💀 EXPEDIÇÃO FRACASSADA",
            description=f"**{exp['nome']}**\n\nOs aventureiros foram derrotados...",
            color=0xE24B4A
        )
    
    await canal.send(embed=embed)
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("UPDATE expedicoes SET status='finalizada' WHERE id=$1", exp["id"])
    
    await asyncio.sleep(10)
    
    try:
        await canal.delete(reason="Expedição finalizada")
    except:
        pass

# ==================================================
# REGISTRO DOS COMANDOS
# ==================================================

def register_expedicao_commands(bot):
    """Registra todos os comandos de expedição"""
    
    @bot.tree.command(name="expedicao_criar", description="Cria uma nova expedição (rascunho)")
    async def exp_criar(interaction: discord.Interaction):
        await cmd_expedicao_criar(interaction)
    
    @bot.tree.command(name="expedicao_add_capitulo", description="Adiciona um capítulo à expedição")
    @app_commands.describe(expedicao_id="ID da expedição")
    async def exp_add_capitulo(interaction: discord.Interaction, expedicao_id: int):
        await cmd_expedicao_add_capitulo(interaction, expedicao_id)
    
    @bot.tree.command(name="expedicao_add_recompensa", description="Adiciona recompensa à expedição")
    @app_commands.describe(expedicao_id="ID da expedição")
    async def exp_add_recompensa(interaction: discord.Interaction, expedicao_id: int):
        await cmd_expedicao_add_recompensa(interaction, expedicao_id)
    
    @bot.tree.command(name="expedicao_ver", description="Ver detalhes de uma expedição")
    @app_commands.describe(expedicao_id="ID da expedição")
    async def exp_ver(interaction: discord.Interaction, expedicao_id: int):
        await cmd_expedicao_ver(interaction, expedicao_id)
    
    @bot.tree.command(name="expedicao_listar", description="Lista expedições abertas para inscrição")
    async def exp_listar(interaction: discord.Interaction):
        await cmd_expedicao_listar(interaction)
    
    @bot.tree.command(name="expedicao_inscrever", description="Inscreve seu personagem em uma expedição")
    @app_commands.describe(expedicao_id="ID da expedição")
    async def exp_inscrever(interaction: discord.Interaction, expedicao_id: int):
        await cmd_expedicao_inscrever(interaction, expedicao_id)
    
    @bot.tree.command(name="expedicao_publicar", description="Publica a expedição em um canal para inscrições")
    @app_commands.describe(expedicao_id="ID da expedição", canal="Canal onde será divulgada")
    async def exp_publicar(interaction: discord.Interaction, expedicao_id: int, canal: discord.TextChannel):
        await cmd_expedicao_publicar(interaction, expedicao_id, canal)
    
    @bot.tree.command(name="expedicao_iniciar", description="[ADMIN] Inicia uma expedição")
    @app_commands.describe(expedicao_id="ID da expedição")
    @app_commands.checks.has_permissions(administrator=True)
    async def exp_iniciar(interaction: discord.Interaction, expedicao_id: int):
        await cmd_expedicao_iniciar(interaction, expedicao_id)
