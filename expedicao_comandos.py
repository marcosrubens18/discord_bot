# expedicao_comandos.py — Comandos administrativos para expedições
import discord
from discord import app_commands
import json
from db import get_pool
from expedicao_db import init_db_expedicao_avancado
from catalogo import (
    get_catalogo_completo, 
    get_itens_por_categoria,
    MATERIAIS_CAT,
    POCOES_CAT,
    ARMAS_POR_CLASSE,
    ARMADURAS_POR_CLASSE
)

# ─── AUTOCOMPLETE BASEADO NO CATÁLOGO EXISTENTE ─────────────────

async def autocomplete_material_catalogo(interaction: discord.Interaction, current: str):
    """Autocomplete usando materiais do catalogo.py"""
    materiais = MATERIAIS_CAT
    filtrado = [m for m in materiais if current.lower() in m["nome"].lower() or not current]
    return [
        app_commands.Choice(
            name=f"{m['emoji']} {m['nome']} [{m['raridade']}]",
            value=m["id"]
        )
        for m in filtrado[:25]
    ]

async def autocomplete_item_catalogo(interaction: discord.Interaction, current: str):
    """Autocomplete usando todos os itens do catalogo.py"""
    itens = get_catalogo_completo()
    filtrado = [i for i in itens if current.lower() in i["nome"].lower() or not current]
    return [
        app_commands.Choice(
            name=f"{i['emoji']} {i['nome']} [{i['raridade']}] — {i['tipo']}",
            value=i["chave"]
        )
        for i in filtrado[:25]
    ]

async def autocomplete_tipo_recompensa(interaction: discord.Interaction, current: str):
    """Autocomplete para tipos de recompensa"""
    tipos = [
        ("🪙 Moedas", "moedas"),
        ("⭐ XP", "xp"),
        ("🎰 Fichas de Roleta", "fichas"),
        ("📦 Material", "material"),
        ("⚔️ Arma", "arma"),
        ("🛡️ Armadura", "armadura"),
        ("🧪 Poção", "pocao"),
    ]
    return [
        app_commands.Choice(name=nome, value=valor)
        for nome, valor in tipos if current.lower() in nome.lower() or not current
    ][:10]

async def autocomplete_expedicao(interaction: discord.Interaction, current: str):
    """Autocomplete para expedições existentes"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        exps = await conn.fetch("""
            SELECT id, nome FROM expedicoes_avancadas 
            WHERE status = 'rascunho' 
            ORDER BY id DESC LIMIT 20
        """)
    return [
        app_commands.Choice(name=f"#{e['id']} - {e['nome'][:50]}", value=str(e['id']))
        for e in exps if current.lower() in e['nome'].lower() or current == str(e['id'])
    ][:25]

# ─── MODAL DE CRIAÇÃO DE EXPEDIÇÃO ───────────────────────────────

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
        embed.add_field(name="📦 Recompensas", value="`/expedicao recompensa_adicionar`", inline=True)
        embed.add_field(name="👹 Monstros", value="`/expedicao monstro_criar`", inline=True)
        embed.add_field(name="📖 Capítulos", value="`/expedicao capitulo_adicionar`", inline=True)
        embed.add_field(name="🖼️ Imagens", value="`/expedicao imagem_definir`", inline=True)
        
        await interaction.followup.send(embed=embed, ephemeral=True)

# ─── COMANDO: ADICIONAR RECOMPENSA (USANDO CATÁLOGO) ─────────────

class AdicionarRecompensaView(discord.ui.View):
    def __init__(self, exp_id: int):
        super().__init__(timeout=120)
        self.exp_id = exp_id
    
    @discord.ui.select(
        placeholder="Selecione o tipo de recompensa",
        options=[
            discord.SelectOption(label="🪙 Moedas", value="moedas", emoji="🪙", description="Quantidade de moedas"),
            discord.SelectOption(label="⭐ XP", value="xp", emoji="⭐", description="Quantidade de XP"),
            discord.SelectOption(label="🎰 Fichas", value="fichas", emoji="🎰", description="Fichas de roleta"),
            discord.SelectOption(label="📦 Material", value="material", emoji="📦", description="Materiais do catálogo"),
            discord.SelectOption(label="⚔️ Arma", value="arma", emoji="⚔️", description="Armas do catálogo"),
            discord.SelectOption(label="🛡️ Armadura", value="armadura", emoji="🛡️", description="Armaduras do catálogo"),
            discord.SelectOption(label="🧪 Poção", value="pocao", emoji="🧪", description="Poções do catálogo"),
        ]
    )
    async def select_tipo(self, interaction: discord.Interaction, select):
        tipo = select.values[0]
        
        if tipo in ["moedas", "xp", "fichas"]:
            modal = QuantidadeModal(self.exp_id, tipo)
            await interaction.response.send_modal(modal)
        else:
            # Para itens do catálogo, mostra um select com os itens disponíveis
            view = SelecionarItemCatalogoView(self.exp_id, tipo)
            await interaction.response.send_message(f"Selecione o item do catálogo:", view=view, ephemeral=True)

class QuantidadeModal(discord.ui.Modal, title="Definir Quantidade"):
    quantidade = discord.ui.TextInput(label="Quantidade", default="1", placeholder="Ex: 1000")
    
    def __init__(self, exp_id: int, tipo: str):
        super().__init__()
        self.exp_id = exp_id
        self.tipo = tipo
        
        if tipo == "moedas":
            self.quantidade.placeholder = "Ex: 5000"
            self.title = "Quantidade de Moedas"
        elif tipo == "xp":
            self.quantidade.placeholder = "Ex: 1000"
            self.title = "Quantidade de XP"
        elif tipo == "fichas":
            self.quantidade.placeholder = "Ex: 3"
            self.title = "Quantidade de Fichas"
    
    async def on_submit(self, interaction: discord.Interaction):
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO expedicao_recompensas (expedicao_id, tipo, quantidade)
                VALUES ($1, $2, $3)
            """, self.exp_id, self.tipo, int(self.quantidade.value))
        
        await interaction.response.send_message(f"✅ Adicionado **{self.quantidade.value}** {self.tipo} como recompensa!", ephemeral=True)

class SelecionarItemCatalogoView(discord.ui.View):
    def __init__(self, exp_id: int, tipo: str):
        super().__init__(timeout=60)
        self.exp_id = exp_id
        self.tipo = tipo
        self.add_item(ItemCatalogoSelectMenu(exp_id, tipo))

class ItemCatalogoSelectMenu(discord.ui.Select):
    def __init__(self, exp_id: int, tipo: str):
        self.exp_id = exp_id
        self.tipo = tipo
        
        # Busca itens do catálogo baseado no tipo
        opcoes = []
        
        if tipo == "material":
            itens = MATERIAIS_CAT
            for item in itens[:25]:
                opcoes.append(discord.SelectOption(
                    label=item["nome"][:50],
                    value=item["id"],
                    description=f"{item['raridade']}",
                    emoji=item.get("emoji", "📦")
                ))
        elif tipo == "pocao":
            itens = POCOES_CAT
            for item in itens[:25]:
                opcoes.append(discord.SelectOption(
                    label=item["nome"][:50],
                    value=item["id"],
                    description=f"{item['raridade']} - {item.get('desc', '')[:40]}",
                    emoji=item.get("emoji", "🧪")
                ))
        elif tipo == "arma":
            for classe, armas in ARMAS_POR_CLASSE.items():
                for arma in armas[:5]:  # Limita por classe
                    opcoes.append(discord.SelectOption(
                        label=f"[{classe.title()}] {arma['nome'][:40]}",
                        value=f"arma:{classe}:{arma['id']}",
                        description=f"{arma['raridade']} - ATK +{arma['atk_bonus']}",
                        emoji=arma.get("emoji", "⚔️")
                    ))
        elif tipo == "armadura":
            for classe, armaduras in ARMADURAS_POR_CLASSE.items():
                for armadura in armaduras[:5]:
                    opcoes.append(discord.SelectOption(
                        label=f"[{classe.title()}] {armadura['nome'][:40]}",
                        value=f"armadura:{classe}:{armadura['id']}",
                        description=f"{armadura['raridade']} - DEF +{armadura['def_bonus']}",
                        emoji=armadura.get("emoji", "🛡️")
                    ))
        
        if not opcoes:
            opcoes = [discord.SelectOption(label="Nenhum item encontrado", value="none")]
        
        super().__init__(placeholder=f"Selecione um {tipo} do catálogo...", options=opcoes, min_values=1, max_values=1)
    
    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "none":
            await interaction.response.send_message("Nenhum item disponível!", ephemeral=True)
            return
        
        modal = ItemQuantidadeModal(self.exp_id, self.tipo, self.values[0])
        await interaction.response.send_modal(modal)

class ItemQuantidadeModal(discord.ui.Modal, title="Quantidade do Item"):
    quantidade = discord.ui.TextInput(label="Quantidade", default="1", placeholder="Ex: 1")
    
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
        
        await interaction.response.send_message(f"✅ Adicionado **{self.quantidade.value}x** do item como recompensa!", ephemeral=True)

# ─── COMANDO: LISTAR RECOMPENSAS ─────────────────────────────────

async def cmd_listar_recompensas(interaction: discord.Interaction, expedicao_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        recompensas = await conn.fetch("SELECT * FROM expedicao_recompensas WHERE expedicao_id=$1", expedicao_id)
    
    if not recompensas:
        await interaction.response.send_message("Nenhuma recompensa cadastrada!", ephemeral=True)
        return
    
    embed = discord.Embed(title=f"📦 Recompensas da Expedição #{expedicao_id}", color=0xE4AF3C)
    desc = []
    for r in recompensas:
        if r["tipo"] in ["moedas", "xp", "fichas"]:
            emoji = {"moedas": "🪙", "xp": "⭐", "fichas": "🎰"}.get(r["tipo"], "📦")
            desc.append(f"{emoji} **{r['quantidade']}** {r['tipo']}")
        else:
            desc.append(f"📦 **{r['quantidade']}x** {r['item_id']}")
    
    embed.description = "\n".join(desc)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ─── COMANDO: CRIAR MONSTRO PERSONALIZADO ────────────────────────

class CriarMonstroModal(discord.ui.Modal, title="Novo Monstro Personalizado"):
    nome = discord.ui.TextInput(label="Nome do Monstro", max_length=50)
    vida = discord.ui.TextInput(label="Vida", default="500")
    ataque = discord.ui.TextInput(label="Ataque", default="80")
    defesa = discord.ui.TextInput(label="Defesa", default="40")
    critico = discord.ui.TextInput(label="Crítico %", default="10")
    imagem = discord.ui.TextInput(label="URL da Imagem", required=False, placeholder="https://...")
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

# ─── COMANDO: ADICIONAR HABILIDADE AO MONSTRO ────────────────────

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
        
        await interaction.response.send_message(f"✅ Habilidade **{self.nome.value}** adicionada!", ephemeral=True)

# ─── COMANDO: ADICIONAR CAPÍTULO ─────────────────────────────────

class AdicionarCapituloModal(discord.ui.Modal, title="Novo Capítulo"):
    titulo = discord.ui.TextInput(label="Título do Capítulo", max_length=100)
    texto = discord.ui.TextInput(label="Texto Narrativo", style=discord.TextStyle.paragraph)
    imagem = discord.ui.TextInput(label="URL da Imagem", required=False, placeholder="https://...")
    
    def __init__(self, exp_id: int):
        super().__init__()
        self.exp_id = exp_id
    
    async def on_submit(self, interaction: discord.Interaction):
        pool = await get_pool()
        async with pool.acquire() as conn:
            ultimo = await conn.fetchval("SELECT COALESCE(MAX(ordem), 0) FROM expedicao_capitulos WHERE expedicao_id=$1", self.exp_id)
            
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

# ─── COMANDO: DEFINIR IMAGENS ────────────────────────────────────

class DefinirImagemModal(discord.ui.Modal, title="Definir Imagem"):
    url = discord.ui.TextInput(label="URL da Imagem", placeholder="https://...")
    
    def __init__(self, exp_id: int, tipo: str):
        super().__init__()
        self.exp_id = exp_id
        self.tipo = tipo
    
    async def on_submit(self, interaction: discord.Interaction):
        pool = await get_pool()
        async with pool.acquire() as conn:
            if self.tipo in ["divulgacao", "final", "background", "banner"]:
                campo = f"imagem_{self.tipo}"
                await conn.execute(f"UPDATE expedicoes_avancadas SET {campo}=$1 WHERE id=$2", self.url.value, self.exp_id)
            else:
                exp = await conn.fetchrow("SELECT config FROM expedicoes_avancadas WHERE id=$1", self.exp_id)
                config = json.loads(exp["config"]) if exp["config"] else {}
                config[f"imagem_{self.tipo}"] = self.url.value
                await conn.execute("UPDATE expedicoes_avancadas SET config=$1 WHERE id=$2", json.dumps(config), self.exp_id)
        
        await interaction.response.send_message(f"✅ Imagem de **{self.tipo}** definida!", ephemeral=True)

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
    
    if exp.get('imagem_divulgacao'):
        embed.set_image(url=exp['imagem_divulgacao'])
    
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

# ─── EXPORTAÇÃO DOS COMANDOS ─────────────────────────────────────

def register_commands(bot):
    """Registra todos os comandos de expedição no bot"""
    
    exp_group = app_commands.Group(name="expedicao", description="Sistema de Expedições Avançado")
    
    @exp_group.command(name="criar", description="Cria uma nova expedição")
    async def exp_criar(interaction: discord.Interaction):
        await interaction.response.send_modal(CriarExpedicaoModal())
    
    @exp_group.command(name="visualizar", description="Visualiza detalhes de uma expedição")
    @app_commands.describe(expedicao_id="ID da expedição")
    @app_commands.autocomplete(expedicao_id=autocomplete_expedicao)
    async def exp_visualizar(interaction: discord.Interaction, expedicao_id: int):
        await cmd_visualizar_expedicao(interaction, expedicao_id)
    
    @exp_group.command(name="recompensa_adicionar", description="Adiciona recompensa à expedição")
    @app_commands.describe(expedicao_id="ID da expedição")
    @app_commands.autocomplete(expedicao_id=autocomplete_expedicao)
    async def exp_recompensa_adicionar(interaction: discord.Interaction, expedicao_id: int):
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
    
    @exp_group.command(name="monstro_habilidade", description="Adiciona habilidade a um monstro")
    @app_commands.describe(monstro_id="ID do monstro")
    async def exp_monstro_habilidade(interaction: discord.Interaction, monstro_id: int):
        await interaction.response.send_modal(AdicionarHabilidadeModal(monstro_id))
    
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
