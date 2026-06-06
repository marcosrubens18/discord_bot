# systems/eventos.py — Sistema de Eventos

import discord
import asyncio
import random
from datetime import datetime, timedelta, timezone
from typing import Optional, List

from database.db import get_pool
from database.queries import get_personagem
from data.constantes import TIPOS_EVENTO, TIPOS_PREMIO, COR_PRIMARY, COR_SUCCESS, COR_DANGER, COR_WARNING, COR_INFO


# ==================================================
# BANCO DE DADOS
# ==================================================

async def init_db_eventos():
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS eventos (
                id SERIAL PRIMARY KEY,
                titulo TEXT NOT NULL,
                descricao TEXT,
                tipo TEXT DEFAULT 'livre',
                imagem_url TEXT DEFAULT '',
                premio_tipo TEXT DEFAULT 'moedas',
                premio_valor TEXT DEFAULT '1000',
                premio_desc TEXT DEFAULT '',
                criado_por BIGINT,
                canal_id BIGINT,
                msg_id BIGINT DEFAULT 0,
                inicio TIMESTAMP DEFAULT NOW(),
                fim TIMESTAMP,
                ativo BOOLEAN DEFAULT TRUE,
                encerrado BOOLEAN DEFAULT FALSE
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS evento_participantes (
                id SERIAL PRIMARY KEY,
                evento_id INTEGER REFERENCES eventos(id),
                user_id BIGINT,
                nome TEXT,
                pontos INTEGER DEFAULT 0,
                inscrito_em TIMESTAMP DEFAULT NOW(),
                UNIQUE(evento_id, user_id)
            )
        """)
    print("DB Eventos OK!")


# ==================================================
# FUNÇÕES DE PONTUAÇÃO AUTOMÁTICA
# ==================================================

async def registrar_pontos_evento(user_id: int, tipo: str, valor: int = 1) -> tuple:
    """Registra pontos para eventos do tipo especificado"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        evento = await conn.fetchrow("""
            SELECT id FROM eventos 
            WHERE tipo = $1 AND ativo = TRUE AND encerrado = FALSE
            ORDER BY id DESC LIMIT 1
        """, tipo)
        
        if not evento:
            return False, None
        
        participante = await conn.fetchrow("""
            SELECT id, pontos FROM evento_participantes 
            WHERE evento_id = $1 AND user_id = $2
        """, evento["id"], user_id)
        
        if not participante:
            p = await conn.fetchrow("SELECT nome FROM personagens WHERE user_id = $1", user_id)
            if p:
                await conn.execute("""
                    INSERT INTO evento_participantes (evento_id, user_id, nome, pontos)
                    VALUES ($1, $2, $3, $4)
                """, evento["id"], user_id, p["nome"], valor)
                return True, evento["id"]
        
        await conn.execute("""
            UPDATE evento_participantes SET pontos = pontos + $1
            WHERE evento_id = $2 AND user_id = $3
        """, valor, evento["id"], user_id)
        
        return True, evento["id"]


async def registrar_batalha_evento(user_id: int) -> tuple:
    """Registra vitória em batalha para eventos"""
    return await registrar_pontos_evento(user_id, "batalha", 1)


async def registrar_dungeon_evento(user_id: int) -> tuple:
    """Registra dungeon completa para eventos"""
    return await registrar_pontos_evento(user_id, "dungeon", 1)


async def registrar_level_up_evento(user_id: int, niveis_subidos: int) -> tuple:
    """Registra level up para eventos"""
    return await registrar_pontos_evento(user_id, "nivel", niveis_subidos)


async def registrar_coleta_evento(user_id: int, quantidade: int = 1) -> tuple:
    """Registra coleta para eventos"""
    return await registrar_pontos_evento(user_id, "coleta", quantidade)


# ==================================================
# CRIAÇÃO DE EVENTO
# ==================================================

class CriarEventoModal(discord.ui.Modal, title="Criar Novo Evento"):
    titulo = discord.ui.TextInput(
        label="Título do Evento",
        placeholder="Ex: Torneio de Natal 2026",
        max_length=80
    )
    descricao = discord.ui.TextInput(
        label="Descrição",
        style=discord.TextStyle.paragraph,
        placeholder="Descreva o evento, regras, como participar...",
        max_length=500
    )
    duracao_horas = discord.ui.TextInput(
        label="Duração em horas",
        placeholder="Ex: 24 (para 1 dia), 168 (para 1 semana)",
        max_length=5,
        default="24"
    )
    imagem_url = discord.ui.TextInput(
        label="URL da Imagem (opcional)",
        placeholder="https://i.imgur.com/...",
        required=False,
        max_length=200
    )
    premio_desc = discord.ui.TextInput(
        label="Descrição do Prêmio",
        placeholder="Ex: 5000 moedas + Classe Dracomante exclusiva",
        max_length=200
    )

    def __init__(self, tipo, premio_tipo, premio_valor, canal_id):
        super().__init__()
        self.tipo = tipo
        self.premio_tipo = premio_tipo
        self.premio_valor = premio_valor
        self.canal_id = canal_id

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await init_db_eventos()
        
        try:
            horas = max(1, int(self.duracao_horas.value))
        except:
            horas = 24
        
        fim = datetime.now() + timedelta(hours=horas)

        pool = await get_pool()
        async with pool.acquire() as conn:
            evento = await conn.fetchrow("""
                INSERT INTO eventos
                (titulo, descricao, tipo, imagem_url, premio_tipo, premio_valor, premio_desc,
                 criado_por, canal_id, inicio, fim, ativo)
                VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,NOW(),$10,TRUE)
                RETURNING *
            """, str(self.titulo), str(self.descricao), self.tipo,
                str(self.imagem_url or ""), self.premio_tipo, str(self.premio_valor),
                str(self.premio_desc), interaction.user.id, self.canal_id, fim)

        canal = interaction.guild.get_channel(self.canal_id)
        tipo_info = TIPOS_EVENTO.get(self.tipo, TIPOS_EVENTO["livre"])
        premio_info = TIPOS_PREMIO.get(self.premio_tipo, TIPOS_PREMIO["moedas"])
        duracao_txt = f"{horas}h" if horas < 24 else f"{horas//24}d{horas%24}h" if horas%24 else f"{horas//24} dia(s)"

        embed = discord.Embed(
            title=f"{tipo_info['emoji']} {str(self.titulo)}",
            description=str(self.descricao),
            color=0xE4AF3C
        )
        embed.add_field(name="Tipo", value=f"{tipo_info['emoji']} {tipo_info['nome']}", inline=True)
        embed.add_field(name="Duração", value=f"⏱️ {duracao_txt}", inline=True)
        embed.add_field(name="Termina", value=f"<t:{int(fim.timestamp())}:R>", inline=True)
        embed.add_field(
            name=f"{premio_info['emoji']} Prêmio",
            value=str(self.premio_desc) or f"{premio_info['nome']}: {self.premio_valor}",
            inline=False
        )
        embed.set_footer(text=f"Evento #{evento['id']} | Use /evento-info para detalhes")
        if str(self.imagem_url):
            embed.set_image(url=str(self.imagem_url))

        class ParticiparView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=None)
            @discord.ui.button(label="✅ Participar!", style=discord.ButtonStyle.success, emoji="✅", custom_id=f"participar_{evento['id']}")
            async def btn(self, inter: discord.Interaction, b):
                await _participar_evento(inter, evento["id"])

        msg = None
        if canal:
            msg = await canal.send(embed=embed, view=ParticiparView())
            async with pool.acquire() as conn:
                await conn.execute("UPDATE eventos SET msg_id=$1, canal_id=$2 WHERE id=$3", msg.id, canal.id, evento["id"])

        await interaction.followup.send(
            f"✅ Evento **{str(self.titulo)}** criado! ID: `{evento['id']}`\nTermina em {duracao_txt}.",
            ephemeral=True
        )

        asyncio.create_task(_agendar_encerramento(evento["id"], horas * 3600, interaction.guild))


async def _agendar_encerramento(evento_id, segundos, guild):
    await asyncio.sleep(segundos)
    await encerrar_evento(evento_id, guild)


async def encerrar_evento(evento_id, guild):
    pool = await get_pool()
    async with pool.acquire() as conn:
        evento = await conn.fetchrow("SELECT * FROM eventos WHERE id=$1", evento_id)
        if not evento or evento["encerrado"]:
            return
        await conn.execute("UPDATE eventos SET ativo=FALSE, encerrado=TRUE WHERE id=$1", evento_id)
        participantes = await conn.fetch("SELECT * FROM evento_participantes WHERE evento_id=$1 ORDER BY pontos DESC LIMIT 3", evento_id)

    if not participantes:
        return

    vencedor = participantes[0]
    tipo_info = TIPOS_EVENTO.get(evento["tipo"], TIPOS_EVENTO["livre"])
    premio_info = TIPOS_PREMIO.get(evento["premio_tipo"], TIPOS_PREMIO["moedas"])
    canal = guild.get_channel(evento["canal_id"])

    member_v = guild.get_member(vencedor["user_id"])
    premio_entregue = await _entregar_premio(guild, vencedor["user_id"], evento["premio_tipo"], evento["premio_valor"])

    embed = discord.Embed(
        title=f"🏆 Evento Encerrado — {evento['titulo']}",
        description=f"O evento terminou! Confira o resultado:",
        color=0xE4AF3C
    )
    top = ""
    medalhas = ["🥇", "🥈", "🥉"]
    for i, p in enumerate(participantes[:3]):
        top += f"{medalhas[i]} **{p['nome']}** — {p['pontos']} pontos\n"
    embed.add_field(name="Ranking Final", value=top or "Nenhum participante", inline=False)
    embed.add_field(name=f"{premio_info['emoji']} Prêmio entregue", value=f"{member_v.mention if member_v else vencedor['nome']}: {premio_entregue}", inline=False)
    embed.set_footer(text="Obrigado a todos que participaram!")
    if canal:
        await canal.send(embed=embed)


async def _entregar_premio(guild, user_id, tipo, valor):
    pool = await get_pool()
    try:
        async with pool.acquire() as conn:
            p = await conn.fetchrow("SELECT * FROM personagens WHERE user_id=$1", user_id)
            if not p:
                return "Jogador sem personagem"

            if tipo == "moedas":
                qtd = int(valor)
                await conn.execute("UPDATE personagens SET moedas = moedas + $1 WHERE user_id = $2", qtd, user_id)
                return f"+{qtd} 🪙"

            elif tipo == "xp":
                qtd = int(valor)
                await conn.execute("UPDATE personagens SET xp = xp + $1 WHERE user_id = $2", qtd, user_id)
                return f"+{qtd} ⭐ XP"

            elif tipo == "ficha":
                qtd = int(valor)
                await conn.execute("""
                    INSERT INTO giros (user_id, roleta_id, raridade, quantidade)
                    VALUES ($1, 'skill', 'Lendario', $2)
                    ON CONFLICT (user_id, roleta_id, raridade)
                    DO UPDATE SET quantidade = giros.quantidade + $2
                """, user_id, qtd)
                return f"+{qtd} fichas 🎰"

            elif tipo == "item":
                partes = valor.split("|")
                if len(partes) >= 2:
                    item_id, nome = partes[0], partes[1]
                    tipo_item = partes[2] if len(partes) > 2 else "material"
                    raridade = partes[3] if len(partes) > 3 else "Lendario"
                    emoji = partes[4] if len(partes) > 4 else "🎁"
                    desc = partes[5] if len(partes) > 5 else "Prêmio de evento"
                    ex = await conn.fetchrow("SELECT id FROM inventario WHERE user_id=$1 AND item_id=$2", user_id, item_id)
                    if ex:
                        await conn.execute("UPDATE inventario SET quantidade = quantidade + 1 WHERE id = $1", ex["id"])
                    else:
                        await conn.execute("""
                            INSERT INTO inventario(user_id, item_id, nome, tipo, raridade, emoji, descricao)
                            VALUES($1,$2,$3,$4,$5,$6,$7)
                        """, user_id, item_id, nome, tipo_item, raridade, emoji, desc)
                    return f"{emoji} {nome}"

            elif tipo == "cargo":
                member = guild.get_member(user_id)
                if member:
                    cargo = discord.utils.get(guild.roles, name=valor)
                    if cargo:
                        await member.add_roles(cargo)
                        return f"Cargo: {valor} 🎖️"
                return f"Cargo '{valor}' não encontrado"

            elif tipo == "classe":
                await conn.execute("UPDATE personagens SET classe_id = $1 WHERE user_id = $2", valor.lower(), user_id)
                return f"Classe alterada para {valor} ✨"

    except Exception as e:
        print(f"Erro ao entregar prêmio: {e}")
        return f"Erro ao entregar: {e}"
    
    return "Prêmio entregue!"


async def _participar_evento(interaction: discord.Interaction, evento_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        evento = await conn.fetchrow("SELECT * FROM eventos WHERE id=$1 AND ativo=TRUE AND encerrado=FALSE", evento_id)
        if not evento:
            await interaction.response.send_message("Este evento já encerrou!", ephemeral=True)
            return
        p = await conn.fetchrow("SELECT nome FROM personagens WHERE user_id=$1", interaction.user.id)
        if not p:
            await interaction.response.send_message("Crie seu personagem primeiro!", ephemeral=True)
            return
        ex = await conn.fetchrow("SELECT id FROM evento_participantes WHERE evento_id=$1 AND user_id=$2", evento_id, interaction.user.id)
        if ex:
            await interaction.response.send_message("Você já está inscrito neste evento!", ephemeral=True)
            return
        await conn.execute("""
            INSERT INTO evento_participantes(evento_id, user_id, nome) VALUES($1,$2,$3)
        """, evento_id, interaction.user.id, p["nome"])
    await interaction.response.send_message(f"✅ Inscrito no evento **{evento['titulo']}**! Boa sorte!", ephemeral=True)


# ==================================================
# COMANDOS
# ==================================================

async def cmd_criar_evento(interaction: discord.Interaction, tipo: str, premio_tipo: str, premio_valor: str, canal: discord.TextChannel):
    modal = CriarEventoModal(tipo, premio_tipo, premio_valor, canal.id)
    await interaction.response.send_modal(modal)


async def cmd_eventos(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        eventos = await conn.fetch("SELECT * FROM eventos WHERE ativo=TRUE ORDER BY id DESC")
    
    if not eventos:
        await interaction.followup.send("Nenhum evento ativo no momento!", ephemeral=True)
        return
    
    embed = discord.Embed(title="🎉 Eventos Ativos", color=0xE4AF3C)
    for ev in eventos:
        tipo_info = TIPOS_EVENTO.get(ev["tipo"], TIPOS_EVENTO["livre"])
        fim_ts = int(ev["fim"].timestamp()) if ev["fim"] else 0
        embed.add_field(
            name=f"{tipo_info['emoji']} {ev['titulo']} (#{ev['id']})",
            value=f"{ev['descricao'][:80]}...\n**Termina:** <t:{fim_ts}:R>",
            inline=False
        )
    await interaction.followup.send(embed=embed, ephemeral=True)


async def cmd_evento_info(interaction: discord.Interaction, evento_id: int = 0):
    await interaction.response.defer(ephemeral=True)
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        if evento_id:
            evento = await conn.fetchrow("SELECT * FROM eventos WHERE id=$1", evento_id)
        else:
            evento = await conn.fetchrow("SELECT * FROM eventos WHERE ativo=TRUE ORDER BY id DESC LIMIT 1")
    
    if not evento:
        await interaction.followup.send("Evento não encontrado!", ephemeral=True)
        return
    
    participantes = await conn.fetch("SELECT * FROM evento_participantes WHERE evento_id=$1 ORDER BY pontos DESC", evento["id"])
    
    tipo_info = TIPOS_EVENTO.get(evento["tipo"], TIPOS_EVENTO["livre"])
    premio_info = TIPOS_PREMIO.get(evento["premio_tipo"], TIPOS_PREMIO["moedas"])
    fim_ts = int(evento["fim"].timestamp()) if evento["fim"] else 0
    
    embed = discord.Embed(
        title=f"{tipo_info['emoji']} {evento['titulo']}",
        description=evento["descricao"],
        color=0xE4AF3C if evento["ativo"] else 0x888780
    )
    embed.add_field(name="Tipo", value=f"{tipo_info['emoji']} {tipo_info['nome']}", inline=True)
    embed.add_field(name="Status", value="🟢 Ativo" if evento["ativo"] else "🔴 Encerrado", inline=True)
    if fim_ts:
        embed.add_field(name="Termina", value=f"<t:{fim_ts}:R>", inline=True)
    embed.add_field(name=f"{premio_info['emoji']} Prêmio", value=evento["premio_desc"] or evento["premio_valor"], inline=False)
    
    if participantes:
        top = "\n".join([f"**{i+1}.** {p['nome']} — {p['pontos']} pts" for i, p in enumerate(participantes[:5])])
        embed.add_field(name=f"Top Participantes ({len(participantes)} inscritos)", value=top, inline=False)
    
    if evento["imagem_url"]:
        embed.set_image(url=evento["imagem_url"])
    
    await interaction.followup.send(embed=embed, ephemeral=True)


async def cmd_encerrar_evento(interaction: discord.Interaction, evento_id: int):
    await interaction.response.defer(ephemeral=True)
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        ev = await conn.fetchrow("SELECT * FROM eventos WHERE id=$1", evento_id)
    
    if not ev:
        await interaction.followup.send("Evento não encontrado!", ephemeral=True)
        return
    
    await encerrar_evento(evento_id, interaction.guild)
    await interaction.followup.send(f"✅ Evento **{ev['titulo']}** encerrado e prêmio entregue!", ephemeral=True)


async def cmd_add_pontos(interaction: discord.Interaction, jogador: discord.Member, pontos: int, evento_id: int = 0):
    await interaction.response.defer(ephemeral=True)
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        if not evento_id:
            ev = await conn.fetchrow("SELECT id FROM eventos WHERE ativo=TRUE ORDER BY id DESC LIMIT 1")
            if not ev:
                await interaction.followup.send("Nenhum evento ativo!", ephemeral=True)
                return
            evento_id = ev["id"]
        
        ex = await conn.fetchrow("SELECT id FROM evento_participantes WHERE evento_id=$1 AND user_id=$2", evento_id, jogador.id)
        if ex:
            await conn.execute("UPDATE evento_participantes SET pontos = pontos + $1 WHERE id = $2", pontos, ex["id"])
        else:
            p = await conn.fetchrow("SELECT nome FROM personagens WHERE user_id=$1", jogador.id)
            nome = p["nome"] if p else jogador.display_name
            await conn.execute("""
                INSERT INTO evento_participantes(evento_id, user_id, nome, pontos) VALUES($1,$2,$3,$4)
            """, evento_id, jogador.id, nome, pontos)
    
    await interaction.followup.send(f"✅ +{pontos} pontos para **{jogador.display_name}** no evento #{evento_id}!", ephemeral=True)


async def get_evento_ativo():
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM eventos WHERE ativo=TRUE AND encerrado=FALSE ORDER BY id DESC LIMIT 1")
