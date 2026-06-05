# sorteios.py — Sistema completo de sorteios para Villa Eldoria RPG
import discord
from discord import app_commands
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from db import get_pool
from constants import COR_PRIMARY, COR_SUCCESS, COR_DANGER, COR_WARNING, COR_INFO

# ==================================================
# BANCO DE DADOS
# ==================================================

async def init_db_sorteios():
    """Inicializa as tabelas de sorteios no banco de dados"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS sorteios (
                id SERIAL PRIMARY KEY,
                guild_id BIGINT NOT NULL,
                canal_id BIGINT NOT NULL,
                mensagem_id BIGINT NOT NULL,
                criador_id BIGINT NOT NULL,
                titulo TEXT NOT NULL,
                descricao TEXT DEFAULT '',
                imagem TEXT DEFAULT '',
                item_id TEXT NOT NULL,
                item_nome TEXT NOT NULL,
                item_raridade TEXT DEFAULT 'Comum',
                quantidade_item INTEGER DEFAULT 1,
                quantidade_ganhadores INTEGER DEFAULT 1,
                participantes_count INTEGER DEFAULT 0,
                data_criacao TIMESTAMP DEFAULT NOW(),
                data_encerramento TIMESTAMP NOT NULL,
                status TEXT DEFAULT 'ativo'
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS sorteio_participantes (
                id SERIAL PRIMARY KEY,
                sorteio_id INTEGER REFERENCES sorteios(id) ON DELETE CASCADE,
                usuario_id BIGINT NOT NULL,
                data_participacao TIMESTAMP DEFAULT NOW(),
                UNIQUE(sorteio_id, usuario_id)
            )
        """)
    print("DB Sorteios OK!")

# ==================================================
# FUNÇÕES AUXILIARES
# ==================================================

async def get_sorteios_ativos(guild_id: int) -> List[dict]:
    """Retorna lista de sorteios ativos do servidor"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT * FROM sorteios 
            WHERE guild_id = $1 AND status = 'ativo' 
            ORDER BY data_encerramento ASC
        """, guild_id)
        return [dict(r) for r in rows]

async def get_sorteio_by_id(sorteio_id: int) -> Optional[dict]:
    """Retorna um sorteio pelo ID"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM sorteios WHERE id = $1", sorteio_id)
        return dict(row) if row else None

async def get_participantes(sorteio_id: int) -> List[int]:
    """Retorna lista de IDs dos participantes do sorteio"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT usuario_id FROM sorteio_participantes WHERE sorteio_id = $1", sorteio_id)
        return [r["usuario_id"] for r in rows]

async def usuario_ja_participou(sorteio_id: int, usuario_id: int) -> bool:
    """Verifica se o usuário já participou do sorteio"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id FROM sorteio_participantes WHERE sorteio_id = $1 AND usuario_id = $2",
            sorteio_id, usuario_id
        )
        return row is not None

async def adicionar_participante(sorteio_id: int, usuario_id: int) -> bool:
    """Adiciona um participante ao sorteio"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        try:
            await conn.execute("""
                INSERT INTO sorteio_participantes (sorteio_id, usuario_id)
                VALUES ($1, $2)
            """, sorteio_id, usuario_id)
            await conn.execute("""
                UPDATE sorteios SET participantes_count = participantes_count + 1
                WHERE id = $1
            """, sorteio_id)
            return True
        except:
            return False

async def entregar_recompensa(conn, user_id: int, item_id: str, item_nome: str, item_raridade: str, quantidade: int):
    """Entrega a recompensa do sorteio para o vencedor usando o sistema existente"""
    # Verifica se o item já existe no inventário
    ex = await conn.fetchrow(
        "SELECT id, quantidade FROM inventario WHERE user_id = $1 AND item_id = $2",
        user_id, item_id
    )
    if ex:
        await conn.execute(
            "UPDATE inventario SET quantidade = quantidade + $1 WHERE id = $2",
            quantidade, ex["id"]
        )
    else:
        # Busca emoji do item pelo catálogo
        from catalogo import get_catalogo_completo
        itens = get_catalogo_completo()
        item = next((i for i in itens if i["id"] == item_id), None)
        emoji = item["emoji"] if item else "📦"
        
        await conn.execute("""
            INSERT INTO inventario (user_id, item_id, nome, tipo, raridade, emoji, descricao, quantidade)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """, user_id, item_id, item_nome, "premio", item_raridade, emoji, f"Prêmio de sorteio", quantidade)

async def finalizar_sorteio(sorteio_id: int, guild, canal_id: int, mensagem_id: int, manual: bool = False):
    """Finaliza o sorteio, sorteia os vencedores e entrega os prêmios"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        sorteio = await conn.fetchrow("SELECT * FROM sorteios WHERE id = $1", sorteio_id)
        if not sorteio or sorteio["status"] != "ativo":
            return None, None
        
        participantes = await conn.fetch("SELECT usuario_id FROM sorteio_participantes WHERE sorteio_id = $1", sorteio_id)
        ids_participantes = [p["usuario_id"] for p in participantes]
        
        await conn.execute("UPDATE sorteios SET status = 'encerrado' WHERE id = $1", sorteio_id)
        
        # Sorteia os vencedores
        vencedores = []
        qtd_ganhadores = sorteio["quantidade_ganhadores"]
        
        if len(ids_participantes) <= qtd_ganhadores:
            vencedores = ids_participantes.copy()
        else:
            import random
            temp_ids = ids_participantes.copy()
            random.shuffle(temp_ids)
            vencedores = temp_ids[:qtd_ganhadores]
        
        # Entrega as recompensas
        for vencedor_id in vencedores:
            await entregar_recompensa(
                conn, vencedor_id,
                sorteio["item_id"], sorteio["item_nome"],
                sorteio["item_raridade"], sorteio["quantidade_item"]
            )
        
        return vencedores, ids_participantes

async def atualizar_embed_sorteio(guild, canal_id: int, mensagem_id: int):
    """Atualiza a embed do sorteio com os participantes atuais"""
    canal = guild.get_channel(canal_id)
    if not canal:
        return
    
    try:
        msg = await canal.fetch_message(mensagem_id)
        if not msg:
            return
    except:
        return
    
    # Busca dados atualizados do sorteio
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM sorteios WHERE mensagem_id = $1", mensagem_id)
        if not row:
            return
        sorteio = dict(row)
        participantes_count = sorteio["participantes_count"]
    
    # Atualiza a embed
    embed = msg.embeds[0] if msg.embeds else None
    if embed:
        # Procura o campo de participantes e atualiza
        for i, field in enumerate(embed.fields):
            if field.name == "👥 Participantes":
                embed.set_field_at(i, name="👥 Participantes", value=f"**{participantes_count}** jogadores", inline=True)
                break
        
        # Se o sorteio foi encerrado, atualiza o status
        if sorteio["status"] != "ativo":
            for i, field in enumerate(embed.fields):
                if field.name == "📌 Status":
                    status_text = "🔴 ENCERRADO" if sorteio["status"] == "encerrado" else "❌ CANCELADO"
                    embed.set_field_at(i, name="📌 Status", value=status_text, inline=True)
                    break
        
        await msg.edit(embed=embed)

# ==================================================
# MODAL DE CRIAÇÃO DE SORTEIO
# ==================================================

class CriarSorteioModal(discord.ui.Modal, title="🎲 Criar Sorteio"):
    titulo = discord.ui.TextInput(
        label="Título do Sorteio",
        placeholder="Ex: Espada Lendária de Fogo",
        max_length=100
    )
    descricao = discord.ui.TextInput(
        label="Descrição",
        style=discord.TextStyle.paragraph,
        placeholder="Descreva o sorteio...",
        max_length=500,
        required=False
    )
    imagem = discord.ui.TextInput(
        label="URL da Imagem (opcional)",
        placeholder="https://i.imgur.com/...",
        required=False,
        max_length=200
    )
    qtd_ganhadores = discord.ui.TextInput(
        label="Quantidade de Ganhadores",
        placeholder="Ex: 1, 2, 3...",
        default="1",
        max_length=3
    )
    horas_duracao = discord.ui.TextInput(
        label="Duração em horas",
        placeholder="Ex: 24, 48, 72...",
        default="24",
        max_length=5
    )
    
    def __init__(self, canal_id: int, item_id: str, item_nome: str, item_raridade: str, quantidade_item: int):
        super().__init__()
        self.canal_id = canal_id
        self.item_id = item_id
        self.item_nome = item_nome
        self.item_raridade = item_raridade
        self.quantidade_item = quantidade_item
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await init_db_sorteios()
        
        try:
            qtd_ganhadores = max(1, min(int(self.qtd_ganhadores.value), 50))
        except:
            qtd_ganhadores = 1
        
        try:
            horas = max(1, int(self.horas_duracao.value))
        except:
            horas = 24
        
        data_encerramento = datetime.now(timezone.utc) + timedelta(hours=horas)
        
        pool = await get_pool()
        async with pool.acquire() as conn:
            sorteio = await conn.fetchrow("""
                INSERT INTO sorteios 
                (guild_id, canal_id, criador_id, titulo, descricao, imagem,
                 item_id, item_nome, item_raridade, quantidade_item,
                 quantidade_ganhadores, data_encerramento)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                RETURNING *
            """, interaction.guild.id, self.canal_id, interaction.user.id,
                self.titulo.value, self.descricao.value, self.imagem.value,
                self.item_id, self.item_nome, self.item_raridade,
                self.quantidade_item, qtd_ganhadores, data_encerramento)
        
        # Cria a embed do sorteio
        embed = discord.Embed(
            title=f"🎲 {self.titulo.value}",
            description=self.descricao.value or "Participe para concorrer!",
            color=COR_PRIMARY
        )
        
        # Emoji por raridade
        raridade_emoji = {
            "Comum": "⬜", "Incomum": "🟩", "Raro": "🟦",
            "Epico": "🟪", "Lendario": "🟧", "Lendário": "🟧"
        }.get(self.item_raridade, "🎁")
        
        embed.add_field(name="🎁 Recompensa", value=f"{raridade_emoji} **{self.item_nome}** x{self.quantidade_item}", inline=True)
        embed.add_field(name="👥 Ganhadores", value=f"**{qtd_ganhadores}** jogador(es)", inline=True)
        embed.add_field(name="📅 Encerramento", value=f"<t:{int(data_encerramento.timestamp())}:R>", inline=True)
        embed.add_field(name="👥 Participantes", value="**0** jogadores", inline=True)
        embed.add_field(name="👑 Criado por", value=interaction.user.mention, inline=True)
        embed.add_field(name="📌 Status", value="🟢 ATIVO", inline=True)
        
        if self.imagem.value:
            embed.set_image(url=self.imagem.value)
        
        embed.set_footer(text=f"Sorteio #{sorteio['id']} • Boa sorte!")
        
        # Classe da view com botão de participar
        class SorteioView(discord.ui.View):
            def __init__(self, sorteio_id: int, canal_id: int):
                super().__init__(timeout=None)
                self.sorteio_id = sorteio_id
                self.canal_id = canal_id
            
            @discord.ui.button(label="🎟 Participar", style=discord.ButtonStyle.success, custom_id=f"sorteio_participar_{sorteio_id}")
            async def participar(self, inter: discord.Interaction, button):
                await cmd_sorteio_participar(inter, self.sorteio_id, self.canal_id)
        
        canal = interaction.guild.get_channel(self.canal_id)
        if not canal:
            await interaction.followup.send("❌ Canal não encontrado!", ephemeral=True)
            return
        
        msg = await canal.send(embed=embed, view=SorteioView(sorteio["id"], self.canal_id))
        
        async with pool.acquire() as conn:
            await conn.execute("UPDATE sorteios SET mensagem_id = $1 WHERE id = $2", msg.id, sorteio["id"])
        
        # Agenda o encerramento automático
        asyncio.create_task(_agendar_encerramento_sorteio(sorteio["id"], horas * 3600, interaction.guild))
        
        await interaction.followup.send(
            f"✅ Sorteio **{self.titulo.value}** criado!\n"
            f"📢 Canal: {canal.mention}\n"
            f"🎁 Recompensa: {self.item_nome} x{self.quantidade_item}\n"
            f"⏰ Termina em {horas} horas",
            ephemeral=True
        )

async def _agendar_encerramento_sorteio(sorteio_id: int, segundos: int, guild):
    """Agenda o encerramento automático do sorteio"""
    await asyncio.sleep(segundos)
    await finalizar_e_anunciar_sorteio(sorteio_id, guild)

async def finalizar_e_anunciar_sorteio(sorteio_id: int, guild):
    """Finaliza o sorteio e anuncia os vencedores"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        sorteio = await conn.fetchrow("SELECT * FROM sorteios WHERE id = $1 AND status = 'ativo'", sorteio_id)
        if not sorteio:
            return
    
    vencedores, participantes = await finalizar_sorteio(sorteio_id, guild, sorteio["canal_id"], sorteio["mensagem_id"], False)
    
    if vencedores is None:
        return
    
    canal = guild.get_channel(sorteio["canal_id"])
    if not canal:
        return
    
    # Busca a mensagem original para atualizar
    try:
        msg_original = await canal.fetch_message(sorteio["mensagem_id"])
        if msg_original and msg_original.embeds:
            embed = msg_original.embeds[0]
            # Atualiza status
            for i, field in enumerate(embed.fields):
                if field.name == "📌 Status":
                    embed.set_field_at(i, name="📌 Status", value="🔴 ENCERRADO", inline=True)
                    break
            await msg_original.edit(embed=embed, view=None)
    except:
        pass
    
    # Anuncia os vencedores
    if not vencedores:
        embed_fim = discord.Embed(
            title=f"🎲 SORTEIO ENCERRADO - {sorteio['titulo']}",
            description=f"**Ninguém participou!**\nO sorteio foi encerrado sem vencedores.",
            color=COR_DANGER
        )
        await canal.send(embed=embed_fim)
        return
    
    # Monta lista de vencedores
    vencedores_mentions = []
    for vid in vencedores:
        member = guild.get_member(vid)
        if member:
            vencedores_mentions.append(member.mention)
        else:
            vencedores_mentions.append(f"<@{vid}>")
    
    raridade_emoji = {
        "Comum": "⬜", "Incomum": "🟩", "Raro": "🟦",
        "Epico": "🟪", "Lendario": "🟧", "Lendário": "🟧"
    }.get(sorteio["item_raridade"], "🎁")
    
    embed_fim = discord.Embed(
        title=f"🎉 SORTEIO ENCERRADO!",
        description=f"**{sorteio['titulo']}**\n\n"
                   f"🎁 **Recompensa:** {raridade_emoji} {sorteio['item_nome']} x{sorteio['quantidade_item']}\n"
                   f"👥 **Total de participantes:** {len(participantes)}\n\n"
                   f"🏆 **Ganhadores:**\n{chr(10).join(vencedores_mentions)}",
        color=COR_SUCCESS
    )
    embed_fim.set_footer(text=f"Sorteio #{sorteio_id}")
    if sorteio["imagem"]:
        embed_fim.set_image(url=sorteio["imagem"])
    
    await canal.send(embed=embed_fim)

# ==================================================
# COMANDO PARTICIPAR
# ==================================================

async def cmd_sorteio_participar(interaction: discord.Interaction, sorteio_id: int, canal_id: int):
    """Comando para participar de um sorteio (chamado pelo botão)"""
    await interaction.response.defer(ephemeral=True)
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        sorteio = await conn.fetchrow("SELECT * FROM sorteios WHERE id = $1 AND status = 'ativo'", sorteio_id)
        if not sorteio:
            await interaction.followup.send("❌ Este sorteio não está mais ativo!", ephemeral=True)
            return
        
        if await usuario_ja_participou(sorteio_id, interaction.user.id):
            await interaction.followup.send("❌ Você já está participando deste sorteio!", ephemeral=True)
            return
        
        if await adicionar_participante(sorteio_id, interaction.user.id):
            # Atualiza o contador na embed
            await atualizar_embed_sorteio(interaction.guild, canal_id, sorteio["mensagem_id"])
            await interaction.followup.send("✅ Você entrou no sorteio com sucesso! Boa sorte! 🍀", ephemeral=True)
        else:
            await interaction.followup.send("❌ Erro ao participar do sorteio. Tente novamente.", ephemeral=True)

# ==================================================
# AUTOCOMPLETE
# ==================================================

async def autocomplete_canal(interaction: discord.Interaction, current: str):
    """Autocomplete para canais de texto"""
    if not interaction.guild:
        return []
    canais = [
        ch for ch in interaction.guild.text_channels
        if not current or current.lower() in ch.name.lower()
    ]
    return [
        app_commands.Choice(name=f"#{ch.name}", value=str(ch.id))
        for ch in canais[:25]
    ]

async def autocomplete_item_sorteio(interaction: discord.Interaction, current: str):
    """Autocomplete para itens do catálogo (mesmo sistema do set-item)"""
    from catalogo import get_catalogo_completo
    itens = get_catalogo_completo()
    filtrado = [i for i in itens if current.lower() in i["nome"].lower() or not current]
    return [
        app_commands.Choice(
            name=f"{i['emoji']} {i['nome']} [{i['raridade']}]"[:100],
            value=f"{i['id']}|{i['nome']}|{i['raridade']}"
        )
        for i in filtrado[:25]
    ]

async def autocomplete_sorteio_ativo(interaction: discord.Interaction, current: str):
    """Autocomplete para sorteios ativos"""
    if not interaction.guild:
        return []
    sorteios = await get_sorteios_ativos(interaction.guild.id)
    return [
        app_commands.Choice(
            name=f"#{s['id']} - {s['titulo'][:50]}",
            value=str(s["id"])
        )
        for s in sorteios if not current or current.lower() in s["titulo"].lower()
    ][:25]

# ==================================================
# COMANDO CRIAR SORTEIO
# ==================================================

async def cmd_sorteio_criar(interaction: discord.Interaction, canal: str, item: str, quantidade: int):
    """Cria um novo sorteio"""
    await interaction.response.defer(ephemeral=True)
    
    # Verifica permissão de administrador
    if not interaction.user.guild_permissions.administrator:
        await interaction.followup.send("❌ Apenas administradores podem criar sorteios!", ephemeral=True)
        return
    
    # Parse do canal
    try:
        canal_id = int(canal)
        canal_obj = interaction.guild.get_channel(canal_id)
        if not canal_obj or not isinstance(canal_obj, discord.TextChannel):
            await interaction.followup.send("❌ Canal inválido!", ephemeral=True)
            return
    except:
        await interaction.followup.send("❌ Canal inválido!", ephemeral=True)
        return
    
    # Parse do item
    partes = item.split("|")
    if len(partes) < 3:
        await interaction.followup.send("❌ Item inválido! Selecione da lista de sugestões.", ephemeral=True)
        return
    
    item_id = partes[0]
    item_nome = partes[1]
    item_raridade = partes[2]
    
    if quantidade < 1 or quantidade > 999:
        await interaction.followup.send("❌ Quantidade inválida! Use entre 1 e 999.", ephemeral=True)
        return
    
    # Abre o modal para preencher o restante
    modal = CriarSorteioModal(canal_obj.id, item_id, item_nome, item_raridade, quantidade)
    await interaction.response.send_modal(modal)

# ==================================================
# COMANDO SORTEAR (MANUAL)
# ==================================================

async def cmd_sorteio_sortear(interaction: discord.Interaction, sorteio_id: int):
    """Sorteia manualmente um sorteio ativo"""
    await interaction.response.defer(ephemeral=True)
    
    # Verifica permissão
    if not interaction.user.guild_permissions.administrator:
        await interaction.followup.send("❌ Apenas administradores podem sortear manualmente!", ephemeral=True)
        return
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        sorteio = await conn.fetchrow("SELECT * FROM sorteios WHERE id = $1 AND status = 'ativo'", sorteio_id)
        if not sorteio:
            await interaction.followup.send("❌ Sorteio não encontrado ou já encerrado!", ephemeral=True)
            return
    
    await finalizar_e_anunciar_sorteio(sorteio_id, interaction.guild)
    await interaction.followup.send(f"✅ Sorteio #{sorteio_id} finalizado e vencedores anunciados!", ephemeral=True)

# ==================================================
# COMANDO CANCELAR SORTEIO
# ==================================================

async def cmd_sorteio_cancelar(interaction: discord.Interaction, sorteio_id: int):
    """Cancela um sorteio ativo"""
    await interaction.response.defer(ephemeral=True)
    
    # Verifica permissão
    if not interaction.user.guild_permissions.administrator:
        await interaction.followup.send("❌ Apenas administradores podem cancelar sorteios!", ephemeral=True)
        return
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        sorteio = await conn.fetchrow("SELECT * FROM sorteios WHERE id = $1 AND status = 'ativo'", sorteio_id)
        if not sorteio:
            await interaction.followup.send("❌ Sorteio não encontrado ou já encerrado!", ephemeral=True)
            return
        
        await conn.execute("UPDATE sorteios SET status = 'cancelado' WHERE id = $1", sorteio_id)
    
    # Atualiza a embed
    canal = interaction.guild.get_channel(sorteio["canal_id"])
    if canal:
        try:
            msg = await canal.fetch_message(sorteio["mensagem_id"])
            if msg and msg.embeds:
                embed = msg.embeds[0]
                for i, field in enumerate(embed.fields):
                    if field.name == "📌 Status":
                        embed.set_field_at(i, name="📌 Status", value="❌ CANCELADO", inline=True)
                        break
                await msg.edit(embed=embed, view=None)
        except:
            pass
    
    await interaction.followup.send(f"✅ Sorteio **{sorteio['titulo']}** cancelado!", ephemeral=True)

# ==================================================
# COMANDO INFO SORTEIO
# ==================================================

async def cmd_sorteio_info(interaction: discord.Interaction, sorteio_id: int):
    """Mostra informações detalhadas de um sorteio"""
    await interaction.response.defer(ephemeral=True)
    
    sorteio = await get_sorteio_by_id(sorteio_id)
    if not sorteio:
        await interaction.followup.send("❌ Sorteio não encontrado!", ephemeral=True)
        return
    
    participantes = await get_participantes(sorteio_id)
    
    status_emoji = {
        "ativo": "🟢 ATIVO",
        "encerrado": "🔴 ENCERRADO",
        "cancelado": "❌ CANCELADO"
    }.get(sorteio["status"], "❓ DESCONHECIDO")
    
    raridade_emoji = {
        "Comum": "⬜", "Incomum": "🟩", "Raro": "🟦",
        "Epico": "🟪", "Lendario": "🟧", "Lendário": "🟧"
    }.get(sorteio["item_raridade"], "🎁")
    
    embed = discord.Embed(
        title=f"🎲 Sorteio #{sorteio['id']}",
        description=f"**{sorteio['titulo']}**\n\n{sorteio['descricao'] or 'Sem descrição'}",
        color=COR_PRIMARY
    )
    embed.add_field(name="📌 Status", value=status_emoji, inline=True)
    embed.add_field(name="👑 Criador", value=f"<@{sorteio['criador_id']}>", inline=True)
    embed.add_field(name="👥 Participantes", value=f"{len(participantes)} jogadores", inline=True)
    embed.add_field(name="🎁 Recompensa", value=f"{raridade_emoji} {sorteio['item_nome']} x{sorteio['quantidade_item']}", inline=True)
    embed.add_field(name="🏆 Ganhadores", value=f"{sorteio['quantidade_ganhadores']} jogador(es)", inline=True)
    embed.add_field(name="📅 Criado em", value=f"<t:{int(sorteio['data_criacao'].timestamp())}:R>", inline=True)
    embed.add_field(name="⏰ Encerramento", value=f"<t:{int(sorteio['data_encerramento'].timestamp())}:R>", inline=False)
    
    await interaction.followup.send(embed=embed, ephemeral=True)

# ==================================================
# REGISTRO DOS COMANDOS
# ==================================================

def register_sorteio_commands(bot):
    """Registra todos os comandos de sorteio no bot"""
    
    @bot.tree.command(name="sorteio_criar", description="[ADMIN] Cria um novo sorteio")
    @app_commands.describe(
        canal="Canal onde o sorteio será divulgado",
        item="Item que será sorteado",
        quantidade="Quantidade do item"
    )
    @app_commands.autocomplete(canal=autocomplete_canal, item=autocomplete_item_sorteio)
    async def sorteio_criar(interaction: discord.Interaction, canal: str, item: str, quantidade: int = 1):
        await cmd_sorteio_criar(interaction, canal, item, quantidade)
    
    @bot.tree.command(name="sorteio_sortear", description="[ADMIN] Sorteia os vencedores manualmente")
    @app_commands.describe(sorteio_id="ID do sorteio")
    @app_commands.autocomplete(sorteio_id=autocomplete_sorteio_ativo)
    async def sorteio_sortear(interaction: discord.Interaction, sorteio_id: int):
        await cmd_sorteio_sortear(interaction, sorteio_id)
    
    @bot.tree.command(name="sorteio_cancelar", description="[ADMIN] Cancela um sorteio")
    @app_commands.describe(sorteio_id="ID do sorteio")
    @app_commands.autocomplete(sorteio_id=autocomplete_sorteio_ativo)
    async def sorteio_cancelar(interaction: discord.Interaction, sorteio_id: int):
        await cmd_sorteio_cancelar(interaction, sorteio_id)
    
    @bot.tree.command(name="sorteio_info", description="Mostra informações de um sorteio")
    @app_commands.describe(sorteio_id="ID do sorteio")
    @app_commands.autocomplete(sorteio_id=autocomplete_sorteio_ativo)
    async def sorteio_info(interaction: discord.Interaction, sorteio_id: int):
        await cmd_sorteio_info(interaction, sorteio_id)
    
    @bot.tree.command(name="sorteios", description="Lista todos os sorteios ativos")
    async def sorteios_listar(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        sorteios = await get_sorteios_ativos(interaction.guild.id)
        if not sorteios:
            await interaction.followup.send("📭 Nenhum sorteio ativo no momento!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🎲 SORTEIOS ATIVOS",
            description=f"Total: {len(sorteios)} sorteio(s) ativo(s)",
            color=COR_PRIMARY
        )
        
        for s in sorteios:
            participantes = await get_participantes(s["id"])
            raridade_emoji = {
                "Comum": "⬜", "Incomum": "🟩", "Raro": "🟦",
                "Epico": "🟪", "Lendario": "🟧", "Lendário": "🟧"
            }.get(s["item_raridade"], "🎁")
            
            embed.add_field(
                name=f"#{s['id']} - {s['titulo']}",
                value=f"🎁 {raridade_emoji} {s['item_nome']} x{s['quantidade_item']}\n"
                      f"👥 {len(participantes)} participantes\n"
                      f"⏰ Termina: <t:{int(s['data_encerramento'].timestamp())}:R>\n"
                      f"🔗 ID: `{s['id']}`",
                inline=False
            )
        
        embed.set_footer(text="Use /sorteio_info [ID] para ver detalhes")
        await interaction.followup.send(embed=embed, ephemeral=True)

    # Reagendar sorteios pendentes ao iniciar o bot
    @bot.event
    async def on_ready_sorteios():
        await init_db_sorteios()
        # Busca sorteios ativos que já passaram do prazo
        pool = await get_pool()
        async with pool.acquire() as conn:
            expirados = await conn.fetch("""
                SELECT id FROM sorteios 
                WHERE status = 'ativo' AND data_encerramento <= NOW()
            """)
            for exp in expirados:
                asyncio.create_task(finalizar_e_anunciar_sorteio(exp["id"], None))
    
    # Chama a função de reagendamento
    asyncio.create_task(on_ready_sorteios())