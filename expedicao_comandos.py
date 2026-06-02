# expedicao_comandos.py — Comandos para criar expedições avançadas
import discord
from discord import app_commands
import json
from db import get_pool
from expedicao_db import init_db_expedicao_avancado, get_materiais_existentes, get_itens_existentes

# ─── AUTOCOMPLETE ─────────────────────────────────────────────────

async def autocomplete_material(interaction: discord.Interaction, current: str):
    materiais = await get_materiais_existentes()
    return [
        app_commands.Choice(name=f"{m['emoji']} {m['nome']} [{m['raridade']}]", value=m['item_id'])
        for m in materiais if current.lower() in m['nome'].lower()
    ][:25]

async def autocomplete_item(interaction: discord.Interaction, current: str):
    itens = await get_itens_existentes()
    return [
        app_commands.Choice(name=f"{i['emoji']} {i['nome']} [{i['tipo']}]", value=i['item_id'])
        for i in itens if current.lower() in i['nome'].lower()
    ][:25]

async def autocomplete_expedicao(interaction: discord.Interaction, current: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        exps = await conn.fetch("SELECT id, nome FROM expedicoes_avancadas WHERE status='rascunho' ORDER BY id DESC LIMIT 10")
    return [
        app_commands.Choice(name=f"#{e['id']} - {e['nome'][:50]}", value=str(e['id']))
        for e in exps if current.lower() in e['nome'].lower() or current == str(e['id'])
    ][:25]

# ─── COMANDO: CRIAR EXPEDIÇÃO ─────────────────────────────────────

class CriarExpedicaoModal(discord.ui.Modal, title="Nova Expedição"):
    nome = discord.ui.TextInput(label="Nome da Expedição", max_length=100)
    descricao = discord.ui.TextInput(label="Descrição", style=discord.TextStyle.paragraph, max_length=500, required=False)
    nivel_min = discord.ui.TextInput(label="Nível Mínimo", default="1", max_length=3)
    max_jogadores = discord.ui.TextInput(label="Máximo de Jogadores", default="5", max_length=2)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await init_db_expedicao_avancado()
        
        pool = await get_pool()
        async with pool.acquire() as conn:
            exp = await conn.fetchrow("""
                INSERT INTO expedicoes_avancadas (nome, descricao, nivel_minimo, max_participantes, criado_por, status)
                VALUES ($1, $2, $3, $4, $5, 'rascunho') RETURNING id
            """, self.nome.value, self.descricao.value, int(self.nivel_min.value), int(self.max_jogadores.value), interaction.user.id)
        
        embed = discord.Embed(
            title="✅ Expedição Criada!",
            description=f"**ID:** `{exp['id']}`\n**Nome:** {self.nome.value}\n\nUse os comandos abaixo para configurar:",
            color=0x1D9E75
        )
        embed.add_field(name="📦 Recompensas", value="`/expedicao recompensa adicionar`", inline=True)
        embed.add_field(name="👹 Monstros", value="`/expedicao monstro criar`", inline=True)
        embed.add_field(name="📖 Capítulos", value="`/expedicao capitulo adicionar`", inline=True)
        embed.add_field(name="🖼️ Imagens", value="`/expedicao imagem definir`", inline=True)
        
        await interaction.followup.send(embed=embed, ephemeral=True)

# ─── COMANDO: ADICIONAR RECOMPENSA ────────────────────────────────

class AdicionarRecompensaView(discord.ui.View):
    def __init__(self, exp_id: int):
        super().__init__(timeout=120)
        self.exp_id = exp_id
    
    @discord.ui.select(
        placeholder="Selecione o tipo de recompensa",
        options=[
            discord.SelectOption(label="🪙 Moedas", value="moedas", emoji="🪙"),
            discord.SelectOption(label="⭐ XP", value="xp", emoji="⭐"),
            discord.SelectOption(label="🎰 Fichas", value="fichas", emoji="🎰"),
            discord.SelectOption(label="📦 Material", value="material", emoji="📦"),
            discord.SelectOption(label="⚔️ Item", value="item", emoji="⚔️"),
        ]
    )
    async def select_tipo(self, interaction: discord.Interaction, select):
        if select.values[0] in ["moedas", "xp", "fichas"]:
            modal = QuantidadeModal(self.exp_id, select.values[0])
            await interaction.response.send_modal(modal)
        else:
            # Para materiais e itens, mostra outro select
            view = SelecionarItemView(self.exp_id, select.values[0])
            await interaction.response.send_message("Selecione o item:", view=view, ephemeral=True)

class QuantidadeModal(discord.ui.Modal, title="Definir Quantidade"):
    quantidade = discord.ui.TextInput(label="Quantidade", default="1")
    
    def __init__(self, exp_id: int, tipo: str):
        super().__init__()
        self.exp_id = exp_id
        self.tipo = tipo
    
    async def on_submit(self, interaction: discord.Interaction):
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO expedicao_recompensas (expedicao_id, tipo, quantidade)
                VALUES ($1, $2, $3)
            """, self.exp_id, self.tipo, int(self.quantidade.value))
        
        await interaction.response.send_message(f"✅ Adicionado {self.quantidade.value} {self.tipo} como recompensa!", ephemeral=True)

class SelecionarItemView(discord.ui.View):
    def __init__(self, exp_id: int, tipo: str):
        super().__init__(timeout=60)
        self.exp_id = exp_id
        self.tipo = tipo
        self.add_item(ItemSelectMenu(exp_id, tipo))

class ItemSelectMenu(discord.ui.Select):
    def __init__(self, exp_id: int, tipo: str):
        self.exp_id = exp_id
        self.tipo = tipo
        options = []
        
        # Carrega opções dinamicamente
        if tipo == "material":
            itens = []  # Buscar do DB
            options = [discord.SelectOption(label="Carregando...", value="loading")]
        else:
            options = [discord.SelectOption(label="Carregando...", value="loading")]
        
        super().__init__(placeholder="Selecione o item...", options=options, min_values=1, max_values=1)
    
    async def callback(self, interaction: discord.Interaction):
        modal = ItemQuantidadeModal(self.exp_id, self.tipo, self.values[0])
        await interaction.response.send_modal(modal)

class ItemQuantidadeModal(discord.ui.Modal, title="Quantidade"):
    quantidade = discord.ui.TextInput(label="Quantidade", default="1")
    
    def __init__(self, exp_id: int, tipo: str, item_id: str):
        super().__init__()
        self.exp_id = exp_id
        self.tipo = tipo
        self.item_id = item_id
    
    async def on_submit(self, interaction: discord.Interaction):
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO expedicao_recompensas (expedicao_id, tipo, item_id, quantidade)
                VALUES ($1, $2, $3, $4)
            """, self.exp_id, self.tipo, self.item_id, int(self.quantidade.value))
        
        await interaction.response.send_message(f"✅ Adicionado {self.quantidade.value}x do item como recompensa!", ephemeral=True)

# ─── COMANDO: CRIAR MONSTRO PERSONALIZADO ─────────────────────────

class CriarMonstroModal(discord.ui.Modal, title="Novo Monstro"):
    nome = discord.ui.TextInput(label="Nome do Monstro", max_length=50)
    vida = discord.ui.TextInput(label="Vida", default="500")
    ataque = discord.ui.TextInput(label="Ataque", default="80")
    defesa = discord.ui.TextInput(label="Defesa", default="40")
    critico = discord.ui.TextInput(label="Crítico %", default="10")
    imagem = discord.ui.TextInput(label="URL da Imagem", required=False)
    descricao = discord.ui.TextInput(label="Descrição", style=discord.TextStyle.paragraph, required=False)
    
    def __init__(self, exp_id: int):
        super().__init__()
        self.exp_id = exp_id
    
    async def on_submit(self, interaction: discord.Interaction):
        pool = await get_pool()
        async with pool.acquire() as conn:
            monstro = await conn.fetchrow("""
                INSERT INTO expedicao_monstros (expedicao_id, nome, vida, ataque, defesa, critico, imagem, descricao)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING id
            """, self.exp_id, self.nome.value, int(self.vida.value), int(self.ataque.value), 
               int(self.defesa.value), int(self.critico.value), self.imagem.value, self.descricao.value)
        
        embed = discord.Embed(
            title=f"👹 {self.nome.value}",
            description=self.descricao.value or "Sem descrição",
            color=0xE24B4A
        )
        embed.add_field(name="❤️ Vida", value=self.vida.value, inline=True)
        embed.add_field(name="⚔️ Ataque", value=self.ataque.value, inline=True)
        embed.add_field(name="🛡️ Defesa", value=self.defesa.value, inline=True)
        embed.add_field(name="🎯 Crítico", value=f"{self.critico.value}%", inline=True)
        if self.imagem.value:
            embed.set_image(url=self.imagem.value)
        embed.set_footer(text=f"ID: {monstro['id']}")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

# ─── COMANDO: ADICIONAR HABILIDADE AO MONSTRO ─────────────────────

class AdicionarHabilidadeModal(discord.ui.Modal, title="Nova Habilidade"):
    nome = discord.ui.TextInput(label="Nome da Habilidade", max_length=50)
    dano = discord.ui.TextInput(label="Dano", default="100")
    efeito = discord.ui.TextInput(label="Efeito", placeholder="Ex: Reduz defesa por 2 turnos", required=False)
    cooldown = discord.ui.TextInput(label="Cooldown (turnos)", default="2")
    
    def __init__(self, monstro_id: int):
        super().__init__()
        self.monstro_id = monstro_id
    
    async def on_submit(self, interaction: discord.Interaction):
        pool = await get_pool()
        async with pool.acquire() as conn:
            monstro = await conn.fetchrow("SELECT habilidades FROM expedicao_monstros WHERE id=$1", self.monstro_id)
            habilidades = json.loads(monstro["habilidades"]) if monstro["habilidades"] else []
            habilidades.append({
                "id": len(habilidades) + 1,
                "nome": self.nome.value,
                "dano": int(self.dano.value),
                "efeito": self.efeito.value,
                "cooldown": int(self.cooldown.value)
            })
            await conn.execute("UPDATE expedicao_monstros SET habilidades=$1 WHERE id=$2", json.dumps(habilidades), self.monstro_id)
        
        embed = discord.Embed(
            title=f"✨ Habilidade Adicionada: {self.nome.value}",
            description=f"**Dano:** {self.dano.value}\n**Efeito:** {self.efeito.value or 'Nenhum'}\n**Cooldown:** {self.cooldown.value} turnos",
            color=0x7F77DD
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

# ─── COMANDO: ADICIONAR CAPÍTULO ─────────────────────────────────

class AdicionarCapituloModal(discord.ui.Modal, title="Novo Capítulo"):
    titulo = discord.ui.TextInput(label="Título do Capítulo", max_length=100)
    texto = discord.ui.TextInput(label="Texto Narrativo", style=discord.TextStyle.paragraph)
    imagem = discord.ui.TextInput(label="URL da Imagem", required=False)
    
    def __init__(self, exp_id: int):
        super().__init__()
        self.exp_id = exp_id
    
    async def on_submit(self, interaction: discord.Interaction):
        pool = await get_pool()
        async with pool.acquire() as conn:
            # Pega próxima ordem
            ultimo = await conn.fetchval("SELECT COALESCE(MAX(ordem), 0) FROM expedicao_capitulos WHERE expedicao_id=$1", self.exp_id)
            
            # Mostra menu de tipo
            view = SelecionarTipoView(self.exp_id, ultimo + 1, self.titulo.value, self.texto.value, self.imagem.value)
            await interaction.response.send_message("Selecione o tipo do capítulo:", view=view, ephemeral=True)

class SelecionarTipoView(discord.ui.View):
    def __init__(self, exp_id: int, ordem: int, titulo: str, texto: str, imagem: str):
        super().__init__(timeout=60)
        self.exp_id = exp_id
        self.ordem = ordem
        self.titulo = titulo
        self.texto = texto
        self.imagem = imagem
    
    @discord.ui.select(
        placeholder="Tipo do Capítulo",
        options=[
            discord.SelectOption(label="📖 Narrativa", value="narrativa", emoji="📖", description="Texto narrativo simples"),
            discord.SelectOption(label="🤔 Escolha", value="escolha", emoji="🤔", description="Jogadores escolhem um caminho"),
            discord.SelectOption(label="⚔️ Combate", value="combate", emoji="⚔️", description="Batalha contra monstro"),
            discord.SelectOption(label="💰 Recompensa", value="recompensa", emoji="💰", description="Distribui recompensas"),
            discord.SelectOption(label="🏪 Loja", value="loja", emoji="🏪", description="Loja temporária"),
            discord.SelectOption(label="👤 NPC", value="npc", emoji="👤", description="NPC com diálogo"),
        ]
    )
    async def select_tipo(self, interaction: discord.Interaction, select):
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO expedicao_capitulos (expedicao_id, ordem, titulo, texto, imagem, tipo)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, self.exp_id, self.ordem, self.titulo, self.texto, self.imagem, select.values[0])
        
        embed = discord.Embed(
            title=f"✅ Capítulo Adicionado: {self.titulo}",
            description=f"**Ordem:** {self.ordem}\n**Tipo:** {select.values[0]}\n\n{self.texto[:200]}...",
            color=0x1D9E75
        )
        if self.imagem:
            embed.set_image(url=self.imagem)
        
        await interaction.response.edit_message(embed=embed, view=None)

# ─── COMANDO: DEFINIR IMAGENS DA EXPEDIÇÃO ───────────────────────

class DefinirImagemModal(discord.ui.Modal, title="Definir Imagem"):
    url = discord.ui.TextInput(label="URL da Imagem", placeholder="https://...")
    
    def __init__(self, exp_id: int, tipo: str):
        super().__init__()
        self.exp_id = exp_id
        self.tipo = tipo
    
    async def on_submit(self, interaction: discord.Interaction):
        pool = await get_pool()
        async with pool.acquire() as conn:
            campo = ""
            if self.tipo == "divulgacao":
                campo = "imagem_divulgacao"
            elif self.tipo == "final":
                campo = "imagem_final"
            else:
                # Para outros tipos, armazena no config
                exp = await conn.fetchrow("SELECT config FROM expedicoes_avancadas WHERE id=$1", self.exp_id)
                config = json.loads(exp["config"]) if exp["config"] else {}
                config[f"imagem_{self.tipo}"] = self.url.value
                await conn.execute("UPDATE expedicoes_avancadas SET config=$1 WHERE id=$2", json.dumps(config), self.exp_id)
                await interaction.response.send_message(f"✅ Imagem de {self.tipo} definida!", ephemeral=True)
                return
            
            await conn.execute(f"UPDATE expedicoes_avancadas SET {campo}=$1 WHERE id=$2", self.url.value, self.exp_id)
        
        await interaction.response.send_message(f"✅ Imagem de {self.tipo} definida!", ephemeral=True)

# ─── COMANDO: LISTAR RECOMPENSAS ─────────────────────────────────

async def cmd_listar_recompensas(interaction: discord.Interaction, expedicao_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        recompensas = await conn.fetch("SELECT * FROM expedicao_recompensas WHERE expedicao_id=$1", expedicao_id)
    
    if not recompensas:
        await interaction.response.send_message("Nenhuma recompensa cadastrada!", ephemeral=True)
        return
    
    embed = discord.Embed(title=f"📦 Recompensas da Expedição #{expedicao_id}", color=0xE4AF3C)
    for r in recompensas:
        if r["tipo"] in ["moedas", "xp", "fichas"]:
            embed.add_field(name=r["tipo"].upper(), value=f"{r['quantidade']}", inline=True)
        else:
            embed.add_field(name=f"{r['tipo']}: {r['item_id']}", value=f"x{r['quantidade']}", inline=True)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ─── COMANDO: LISTAR MONSTROS ────────────────────────────────────

async def cmd_listar_monstros(interaction: discord.Interaction, expedicao_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        monstros = await conn.fetch("SELECT * FROM expedicao_monstros WHERE expedicao_id=$1", expedicao_id)
    
    if not monstros:
        await interaction.response.send_message("Nenhum monstro cadastrado!", ephemeral=True)
        return
    
    for m in monstros:
        embed = discord.Embed(title=f"👹 {m['nome']}", description=m['descricao'] or "Sem descrição", color=0xE24B4A)
        embed.add_field(name="❤️ Vida", value=m['vida'], inline=True)
        embed.add_field(name="⚔️ Ataque", value=m['ataque'], inline=True)
        embed.add_field(name="🛡️ Defesa", value=m['defesa'], inline=True)
        if m['imagem']:
            embed.set_image(url=m['imagem'])
        await interaction.followup.send(embed=embed, ephemeral=True)

# ─── COMANDO: VISUALIZAR EXPEDIÇÃO ───────────────────────────────

async def cmd_visualizar_expedicao(interaction: discord.Interaction, expedicao_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        exp = await conn.fetchrow("SELECT * FROM expedicoes_avancadas WHERE id=$1", expedicao_id)
        if not exp:
            await interaction.response.send_message("Expedição não encontrada!", ephemeral=True)
            return
        
        recompensas = await conn.fetch("SELECT * FROM expedicao_recompensas WHERE expedicao_id=$1", expedicao_id)
        monstros = await conn.fetch("SELECT * FROM expedicao_monstros WHERE expedicao_id=$1", expedicao_id)
        capitulos = await conn.fetch("SELECT * FROM expedicao_capitulos WHERE expedicao_id=$1 ORDER BY ordem", expedicao_id)
    
    embed = discord.Embed(
        title=f"🧭 {exp['nome']}",
        description=exp['descricao'] or "Sem descrição",
        color=0x7F77DD
    )
    embed.add_field(name="ID", value=str(exp['id']), inline=True)
    embed.add_field(name="Nível Mínimo", value=str(exp['nivel_minimo']), inline=True)
    embed.add_field(name="Status", value=exp['status'], inline=True)
    embed.add_field(name="📦 Recompensas", value=str(len(recompensas)), inline=True)
    embed.add_field(name="👹 Monstros", value=str(len(monstros)), inline=True)
    embed.add_field(name="📖 Capítulos", value=str(len(capitulos)), inline=True)
    
    if exp['imagem_divulgacao']:
        embed.set_image(url=exp['imagem_divulgacao'])
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ─── EXPORTAÇÃO DOS COMANDOS ─────────────────────────────────────

def register_commands(bot):
    """Registra todos os comandos de expedição no bot"""
    
    # Grupo principal
    exp_group = app_commands.Group(name="expedicao", description="Sistema de Expedições Avançado")
    
    @exp_group.command(name="criar", description="Cria uma nova expedição")
    async def exp_criar(interaction: discord.Interaction):
        await interaction.response.send_modal(CriarExpedicaoModal())
    
    @exp_group.command(name="visualizar", description="Visualiza detalhes de uma expedição")
    @app_commands.describe(expedicao_id="ID da expedição")
    @app_commands.autocomplete(expedicao_id=autocomplete_expedicao)
    async def exp_visualizar(interaction: discord.Interaction, expedicao_id: int):
        await cmd_visualizar_expedicao(interaction, expedicao_id)
    
    @exp_group.command(name="recompensa", description="Gerencia recompensas da expedição")
    @app_commands.describe(expedicao_id="ID da expedição")
    @app_commands.autocomplete(expedicao_id=autocomplete_expedicao)
    async def exp_recompensa(interaction: discord.Interaction, expedicao_id: int):
        view = AdicionarRecompensaView(expedicao_id)
        await interaction.response.send_message("Selecione o tipo de recompensa:", view=view, ephemeral=True)
    
    @exp_group.command(name="recompensas_listar", description="Lista recompensas da expedição")
    @app_commands.describe(expedicao_id="ID da expedição")
    @app_commands.autocomplete(expedicao_id=autocomplete_expedicao)
    async def exp_recompensas_listar(interaction: discord.Interaction, expedicao_id: int):
        await cmd_listar_recompensas(interaction, expedicao_id)
    
    @exp_group.command(name="monstro_criar", description="Cria um monstro personalizado")
    @app_commands.describe(expedicao_id="ID da expedição")
    @app_commands.autocomplete(expedicao_id=autocomplete_expedicao)
    async def exp_monstro_criar(interaction: discord.Interaction, expedicao_id: int):
        await interaction.response.send_modal(CriarMonstroModal(expedicao_id))
    
    @exp_group.command(name="monstro_listar", description="Lista monstros da expedição")
    @app_commands.describe(expedicao_id="ID da expedição")
    @app_commands.autocomplete(expedicao_id=autocomplete_expedicao)
    async def exp_monstro_listar(interaction: discord.Interaction, expedicao_id: int):
        await cmd_listar_monstros(interaction, expedicao_id)
    
    @exp_group.command(name="capitulo_adicionar", description="Adiciona um capítulo à expedição")
    @app_commands.describe(expedicao_id="ID da expedição")
    @app_commands.autocomplete(expedicao_id=autocomplete_expedicao)
    async def exp_capitulo_adicionar(interaction: discord.Interaction, expedicao_id: int):
        await interaction.response.send_modal(AdicionarCapituloModal(expedicao_id))
    
    @exp_group.command(name="imagem_definir", description="Define imagem para a expedição")
    @app_commands.describe(expedicao_id="ID da expedição", tipo="Tipo de imagem")
    @app_commands.autocomplete(expedicao_id=autocomplete_expedicao)
    @app_commands.choices(tipo=[
        app_commands.Choice(name="Divulgação", value="divulgacao"),
        app_commands.Choice(name="Finalização", value="final"),
        app_commands.Choice(name="Background", value="background"),
        app_commands.Choice(name="Banner", value="banner"),
    ])
    async def exp_imagem_definir(interaction: discord.Interaction, expedicao_id: int, tipo: str):
        await interaction.response.send_modal(DefinirImagemModal(expedicao_id, tipo))
    
    bot.tree.add_command(exp_group)