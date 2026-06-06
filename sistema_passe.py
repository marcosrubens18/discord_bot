# sistema_passe.py — Sistema de Passe de Temporada (Battle Pass)

import discord
from discord import app_commands
import json
from datetime import datetime, timedelta, timezone

from db import get_pool
from data_itens import get_catalogo_completo
from constants import COR_PRIMARY, COR_SUCCESS, COR_DANGER, COR_WARNING, COR_INFO, COR_GOLD


# ==================================================
# CONFIGURAÇÃO DA TEMPORADA ATUAL
# ==================================================

TEMPORADA_ATUAL = {
    "id": 1,
    "nome": "Arena Glacial",
    "descricao": "A neve cobriu a arena! Novos desafios e recompensas!",
    "data_inicio": datetime(2026, 6, 1),
    "data_fim": datetime(2026, 7, 1),
    "imagem": "",
    "total_niveis": 25,
    "xp_por_nivel": 100,
}

RECOMPENSAS_PASSE = {
    1: {"tipo": "moedas", "valor": 500, "desc": "500 Moedas", "emoji": "🪙"},
    2: {"tipo": "xp", "valor": 200, "desc": "200 XP", "emoji": "⭐"},
    3: {"tipo": "ficha", "valor": "Comum", "desc": "Ficha Comum", "emoji": "🎰"},
    4: {"tipo": "moedas", "valor": 1000, "desc": "1000 Moedas", "emoji": "🪙"},
    5: {"tipo": "item", "valor": "pocao_hp_m", "desc": "Poção de Cura M", "emoji": "💊"},
    6: {"tipo": "xp", "valor": 300, "desc": "300 XP", "emoji": "⭐"},
    7: {"tipo": "moedas", "valor": 1500, "desc": "1500 Moedas", "emoji": "🪙"},
    8: {"tipo": "ficha", "valor": "Incomum", "desc": "Ficha Incomum", "emoji": "🎰"},
    9: {"tipo": "item", "valor": "pocao_mana_m", "desc": "Poção de Mana M", "emoji": "💙"},
    10: {"tipo": "moedas", "valor": 2000, "desc": "2000 Moedas", "emoji": "🪙"},
    11: {"tipo": "xp", "valor": 500, "desc": "500 XP", "emoji": "⭐"},
    12: {"tipo": "ficha", "valor": "Raro", "desc": "Ficha Rara", "emoji": "🎰"},
    13: {"tipo": "item", "valor": "elixir", "desc": "Elixir Supremo", "emoji": "✨"},
    14: {"tipo": "moedas", "valor": 3000, "desc": "3000 Moedas", "emoji": "🪙"},
    15: {"tipo": "titulo", "valor": "Gladiador", "desc": "Título: Gladiador", "emoji": "🏷️"},
    16: {"tipo": "xp", "valor": 800, "desc": "800 XP", "emoji": "⭐"},
    17: {"tipo": "moedas", "valor": 5000, "desc": "5000 Moedas", "emoji": "🪙"},
    18: {"tipo": "ficha", "valor": "Epico", "desc": "Ficha Épica", "emoji": "🎰"},
    19: {"tipo": "item", "valor": "espada_prata", "desc": "Espada de Prata", "emoji": "⚔️"},
    20: {"tipo": "moedas", "valor": 8000, "desc": "8000 Moedas", "emoji": "🪙"},
    21: {"tipo": "xp", "valor": 1200, "desc": "1200 XP", "emoji": "⭐"},
    22: {"tipo": "ficha", "valor": "Lendario", "desc": "Ficha Lendária", "emoji": "🎰"},
    23: {"tipo": "item", "valor": "armadura_plena", "desc": "Armadura Plena", "emoji": "🛡️"},
    24: {"tipo": "moedas", "valor": 10000, "desc": "10000 Moedas", "emoji": "🪙"},
    25: {"tipo": "titulo", "valor": "Campeão Absoluto", "desc": "Título: Campeão Absoluto", "emoji": "👑"},
}


# ==================================================
# BANCO DE DADOS
# ==================================================

async def init_db_passe():
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS passe_progresso (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                temporada_id INTEGER DEFAULT 1,
                pontos INTEGER DEFAULT 0,
                nivel INTEGER DEFAULT 1,
                recompensas_recebidas JSONB DEFAULT '[]',
                UNIQUE(user_id, temporada_id)
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS passe_historico (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                temporada_id INTEGER,
                nivel INTEGER,
                recompensa TEXT,
                recebida_em TIMESTAMP DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS passe_config (
                id SERIAL PRIMARY KEY,
                temporada_id INTEGER UNIQUE,
                nome TEXT,
                descricao TEXT,
                data_inicio TIMESTAMP,
                data_fim TIMESTAMP,
                imagem TEXT,
                total_niveis INTEGER DEFAULT 25,
                xp_por_nivel INTEGER DEFAULT 100,
                recompensas JSONB DEFAULT '{}',
                ativa BOOLEAN DEFAULT TRUE
            )
        """)
        
        existe = await conn.fetchval("SELECT id FROM passe_config WHERE temporada_id = $1", TEMPORADA_ATUAL["id"])
        if not existe:
            await conn.execute("""
                INSERT INTO passe_config (temporada_id, nome, descricao, data_inicio, data_fim, imagem, total_niveis, xp_por_nivel, recompensas, ativa)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, TRUE)
            """, 
                TEMPORADA_ATUAL["id"], 
                TEMPORADA_ATUAL["nome"], 
                TEMPORADA_ATUAL["descricao"],
                TEMPORADA_ATUAL["data_inicio"],
                TEMPORADA_ATUAL["data_fim"],
                TEMPORADA_ATUAL["imagem"],
                TEMPORADA_ATUAL["total_niveis"],
                TEMPORADA_ATUAL["xp_por_nivel"],
                json.dumps(RECOMPENSAS_PASSE)
            )
    
    print("DB Passe OK!")


# ==================================================
# FUNÇÕES AUXILIARES
# ==================================================

async def get_progresso(user_id: int, temporada_id: int = None):
    if temporada_id is None:
        temporada_id = TEMPORADA_ATUAL["id"]
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        progresso = await conn.fetchrow("""
            SELECT * FROM passe_progresso 
            WHERE user_id = $1 AND temporada_id = $2
        """, user_id, temporada_id)
        
        if not progresso:
            progresso = await conn.fetchrow("""
                INSERT INTO passe_progresso (user_id, temporada_id, pontos, nivel, recompensas_recebidas)
                VALUES ($1, $2, 0, 1, '[]')
                RETURNING *
            """, user_id, temporada_id)
        
        return dict(progresso)


async def adicionar_pontos_passe(user_id: int, pontos: int, fonte: str = "batalha"):
    progresso = await get_progresso(user_id)
    novos_pontos = progresso["pontos"] + pontos
    
    nivel_atual = progresso["nivel"]
    nivel_novo = nivel_atual
    recompensas_recebidas = json.loads(progresso["recompensas_recebidas"])
    
    xp_por_nivel = TEMPORADA_ATUAL["xp_por_nivel"]
    total_niveis = TEMPORADA_ATUAL["total_niveis"]
    
    novos_niveis = []
    while nivel_novo < total_niveis and novos_pontos >= nivel_novo * xp_por_nivel:
        nivel_novo += 1
        novos_niveis.append(nivel_novo)
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE passe_progresso 
            SET pontos = $1, nivel = $2
            WHERE user_id = $3 AND temporada_id = $4
        """, novos_pontos, nivel_novo, user_id, TEMPORADA_ATUAL["id"])
        
        for nv in novos_niveis:
            await conn.execute("""
                INSERT INTO passe_historico (user_id, temporada_id, nivel, recompensa)
                VALUES ($1, $2, $3, 'level_up')
            """, user_id, TEMPORADA_ATUAL["id"], nv)
    
    return {
        "pontos_ganhos": pontos,
        "pontos_total": novos_pontos,
        "nivel_antigo": nivel_atual,
        "nivel_novo": nivel_novo,
        "novos_niveis": novos_niveis,
        "level_up": nivel_novo > nivel_atual
    }


async def adicionar_pontos_batalha(user_id: int, vitoria: bool, tipo: str = "treino"):
    if not vitoria:
        return None
    
    pontos_por_tipo = {
        "treino": 10,
        "arena": 15,
        "dungeon": 20,
        "torneio": 25,
    }
    
    pontos = pontos_por_tipo.get(tipo, 10)
    
    try:
        from sistema_party import get_party_do_jogador
        party = await get_party_do_jogador(user_id)
        if party:
            pontos = int(pontos * 1.2)
    except:
        pass
    
    resultado = await adicionar_pontos_passe(user_id, pontos, tipo)
    return resultado


async def resgatar_recompensa(user_id: int, nivel: int):
    progresso = await get_progresso(user_id)
    
    if progresso["nivel"] < nivel:
        return False, f"❌ Nível insuficiente! Você está no nível {progresso['nivel']}, precisa do nível {nivel}."
    
    recompensas_recebidas = json.loads(progresso["recompensas_recebidas"])
    
    if str(nivel) in recompensas_recebidas:
        return False, "❌ Você já resgatou esta recompensa!"
    
    recompensa = RECOMPENSAS_PASSE.get(nivel)
    if not recompensa:
        return False, "❌ Recompensa não encontrada!"
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        recompensas_recebidas.append(str(nivel))
        await conn.execute("""
            UPDATE passe_progresso 
            SET recompensas_recebidas = $1
            WHERE user_id = $2 AND temporada_id = $3
        """, json.dumps(recompensas_recebidas), user_id, TEMPORADA_ATUAL["id"])
        
        await conn.execute("""
            INSERT INTO passe_historico (user_id, temporada_id, nivel, recompensa)
            VALUES ($1, $2, $3, $4)
        """, user_id, TEMPORADA_ATUAL["id"], nivel, f"{recompensa['tipo']}:{recompensa['valor']}")
        
        await entregar_recompensa(conn, user_id, recompensa)
    
    return True, f"✅ **Recompensa do Nível {nivel} resgatada!**\n{recompensa['emoji']} {recompensa['desc']}"


async def entregar_recompensa(conn, user_id: int, recompensa: dict):
    tipo = recompensa["tipo"]
    valor = recompensa["valor"]
    quantidade = recompensa.get("quantidade", 1)
    
    if tipo == "moedas":
        await conn.execute("UPDATE personagens SET moedas = moedas + $1 WHERE user_id = $2", valor, user_id)
    
    elif tipo == "xp":
        await conn.execute("UPDATE personagens SET xp = xp + $1 WHERE user_id = $2", valor, user_id)
    
    elif tipo.startswith("ficha"):
        raridade = valor
        await conn.execute("""
            INSERT INTO giros (user_id, roleta_id, raridade, quantidade)
            VALUES ($1, 'skill', $2, $3)
            ON CONFLICT (user_id, roleta_id, raridade)
            DO UPDATE SET quantidade = giros.quantidade + $3
        """, user_id, raridade, quantidade)
    
    elif tipo == "item":
        itens = get_catalogo_completo()
        item = next((i for i in itens if i["id"] == valor), None)
        if item:
            ex = await conn.fetchrow("SELECT id, quantidade FROM inventario WHERE user_id = $1 AND item_id = $2", user_id, item["id"])
            if ex:
                await conn.execute("UPDATE inventario SET quantidade = quantidade + $1 WHERE id = $2", quantidade, ex["id"])
            else:
                await conn.execute("""
                    INSERT INTO inventario (user_id, item_id, nome, tipo, raridade, emoji, descricao, quantidade)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """, user_id, item["id"], item["nome"], item["tipo"], item["raridade"], item["emoji"], item.get("desc", ""), quantidade)
    
    elif tipo == "titulo":
        await conn.execute("""
            INSERT INTO conquistas (user_id, conquista_id, progresso, concluida)
            VALUES ($1, $2, 1, 1)
            ON CONFLICT (user_id, conquista_id) DO UPDATE SET concluida = 1
        """, user_id, f"titulo_{valor.replace(' ', '_')}")


# ==================================================
# COMANDOS JOGADOR
# ==================================================

async def cmd_passe_ver(interaction: discord.Interaction):
    await interaction.response.defer()
    
    progresso = await get_progresso(interaction.user.id)
    nivel_atual = progresso["nivel"]
    pontos = progresso["pontos"]
    recompensas_recebidas = json.loads(progresso["recompensas_recebidas"])
    
    xp_por_nivel = TEMPORADA_ATUAL["xp_por_nivel"]
    total_niveis = TEMPORADA_ATUAL["total_niveis"]
    
    pontos_para_proximo = (nivel_atual * xp_por_nivel) - pontos
    pontos_para_proximo = max(0, pontos_para_proximo)
    
    pct = min(1.0, pontos / (nivel_atual * xp_por_nivel)) if nivel_atual * xp_por_nivel > 0 else 0
    f = int(pct * 10)
    barra = "█" * f + "░" * (10 - f)
    
    recompensas_disponiveis = []
    for nivel in range(1, nivel_atual + 1):
        if str(nivel) not in recompensas_recebidas and nivel in RECOMPENSAS_PASSE:
            recompensas_disponiveis.append(nivel)
    
    embed = discord.Embed(
        title=f"🎫 {TEMPORADA_ATUAL['nome']}",
        description=TEMPORADA_ATUAL['descricao'],
        color=COR_GOLD
    )
    
    if TEMPORADA_ATUAL["imagem"]:
        embed.set_thumbnail(url=TEMPORADA_ATUAL["imagem"])
    
    embed.add_field(
        name="📊 SEU PROGRESSO",
        value=f"**Nível:** {nivel_atual}/{total_niveis}\n"
              f"**Pontos:** {pontos} / {nivel_atual * xp_por_nivel}\n"
              f"`{barra}` {pontos_para_proximo} pontos para o próximo nível\n\n"
              f"**🎯 Ganhe pontos em batalhas!**\n"
              f"• Vitória no treino: +10 pts\n"
              f"• Vitória na arena: +15 pts\n"
              f"• Completar dungeon: +20 pts\n"
              f"• Vencer torneio: +25 pts",
        inline=False
    )
    
    if recompensas_disponiveis:
        recomp_txt = ""
        for nivel in recompensas_disponiveis[:5]:
            r = RECOMPENSAS_PASSE[nivel]
            recomp_txt += f"**Nível {nivel}:** {r['emoji']} {r['desc']}\n"
        embed.add_field(
            name="🎁 RECOMPENSAS DISPONÍVEIS",
            value=recomp_txt + f"\n*Use `/passe_resgatar` para resgatar!*",
            inline=False
        )
    
    data_fim = TEMPORADA_ATUAL["data_fim"]
    if isinstance(data_fim, datetime):
        embed.set_footer(text=f"Temporada termina em: <t:{int(data_fim.timestamp())}:R>")
    else:
        embed.set_footer(text="Temporada em andamento!")
    
    await interaction.followup.send(embed=embed)


async def cmd_passe_resgatar(interaction: discord.Interaction, nivel: int):
    await interaction.response.defer(ephemeral=True)
    
    if nivel < 1 or nivel > TEMPORADA_ATUAL["total_niveis"]:
        await interaction.followup.send(f"❌ Nível inválido! Escolha entre 1 e {TEMPORADA_ATUAL['total_niveis']}.", ephemeral=True)
        return
    
    if nivel not in RECOMPENSAS_PASSE:
        await interaction.followup.send("❌ Este nível não tem recompensa!", ephemeral=True)
        return
    
    sucesso, mensagem = await resgatar_recompensa(interaction.user.id, nivel)
    
    if sucesso:
        embed = discord.Embed(
            title="🎉 RECOMPENSA RESGATADA!",
            description=mensagem,
            color=COR_SUCCESS
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
    else:
        await interaction.followup.send(mensagem, ephemeral=True)


async def cmd_passe_ranking(interaction: discord.Interaction):
    await interaction.response.defer()
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        ranking = await conn.fetch("""
            SELECT p.user_id, p.nivel, p.pontos, pe.nome
            FROM passe_progresso p
            JOIN personagens pe ON p.user_id = pe.user_id
            WHERE p.temporada_id = $1
            ORDER BY p.nivel DESC, p.pontos DESC
            LIMIT 10
        """, TEMPORADA_ATUAL["id"])
    
    embed = discord.Embed(
        title=f"🏆 RANKING - {TEMPORADA_ATUAL['nome']}",
        color=COR_GOLD
    )
    
    for i, r in enumerate(ranking):
        medalha = "🥇 " if i == 0 else "🥈 " if i == 1 else "🥉 " if i == 2 else f"{i+1}° "
        embed.add_field(
            name=f"{medalha}{r['nome']}",
            value=f"📊 Nível {r['nivel']} | ⭐ {r['pontos']} pontos",
            inline=False
        )
    
    await interaction.followup.send(embed=embed)


async def cmd_passe_recompensas(interaction: discord.Interaction):
    await interaction.response.defer()
    
    progresso = await get_progresso(interaction.user.id)
    nivel_atual = progresso["nivel"]
    recompensas_recebidas = json.loads(progresso["recompensas_recebidas"])
    
    embed = discord.Embed(
        title=f"📋 RECOMPENSAS - {TEMPORADA_ATUAL['nome']}",
        description=f"**Seu nível atual: {nivel_atual}**\nComplete batalhas para subir de nível!",
        color=COR_PRIMARY
    )
    
    for nivel in range(1, TEMPORADA_ATUAL["total_niveis"] + 1, 5):
        grupo = range(nivel, min(nivel + 5, TEMPORADA_ATUAL["total_niveis"] + 1))
        txt = ""
        for n in grupo:
            if n in RECOMPENSAS_PASSE:
                r = RECOMPENSAS_PASSE[n]
                if str(n) in recompensas_recebidas:
                    status = "✅"
                elif n <= nivel_atual:
                    status = "🎁"
                else:
                    status = "🔒"
                txt += f"{status} **Nível {n}:** {r['emoji']} {r['desc']}\n"
            else:
                txt += f"⬜ **Nível {n}:** Sem recompensa\n"
        embed.add_field(name=f"📌 NÍVEIS {nivel}-{nivel+4}", value=txt or "Nenhuma", inline=True)
    
    embed.set_footer(text="Use /passe_resgatar [nível] para resgatar!")
    await interaction.followup.send(embed=embed)


# ==================================================
# AUTOCOMPLETE
# ==================================================

async def autocomplete_nivel(interaction: discord.Interaction, current: str):
    progresso = await get_progresso(interaction.user.id)
    nivel_atual = progresso["nivel"]
    recompensas_recebidas = json.loads(progresso["recompensas_recebidas"])
    
    opcoes = []
    for nivel in range(1, nivel_atual + 1):
        if str(nivel) not in recompensas_recebidas and nivel in RECOMPENSAS_PASSE:
            r = RECOMPENSAS_PASSE[nivel]
            if current.lower() in str(nivel) or current.lower() in r["desc"].lower():
                opcoes.append(app_commands.Choice(
                    name=f"Nível {nivel} - {r['emoji']} {r['desc']}",
                    value=str(nivel)
                ))
    return opcoes[:25]


# ==================================================
# COMANDOS ADMIN
# ==================================================

async def cmd_passe_admin_definir_recompensa(interaction: discord.Interaction, nivel: int, tipo: str, valor: str, descricao: str, emoji: str = "🎁"):
    await interaction.response.defer(ephemeral=True)
    
    if nivel < 1 or nivel > TEMPORADA_ATUAL["total_niveis"]:
        await interaction.followup.send(f"❌ Nível inválido! Use entre 1 e {TEMPORADA_ATUAL['total_niveis']}.", ephemeral=True)
        return
    
    valor_processado = valor
    if tipo == "moedas" or tipo == "xp":
        try:
            valor_processado = int(valor)
        except:
            await interaction.followup.send("❌ Valor deve ser um número para moedas/XP!", ephemeral=True)
            return
    
    RECOMPENSAS_PASSE[nivel] = {
        "tipo": tipo,
        "valor": valor_processado,
        "desc": descricao,
        "emoji": emoji
    }
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE passe_config SET recompensas = $1 WHERE temporada_id = $2
        """, json.dumps(RECOMPENSAS_PASSE), TEMPORADA_ATUAL["id"])
    
    embed = discord.Embed(
        title="✅ RECOMPENSA DEFINIDA!",
        description=f"**Nível {nivel}:** {emoji} {descricao}",
        color=COR_SUCCESS
    )
    await interaction.followup.send(embed=embed, ephemeral=True)


async def cmd_passe_admin_remover_recompensa(interaction: discord.Interaction, nivel: int):
    await interaction.response.defer(ephemeral=True)
    
    if nivel not in RECOMPENSAS_PASSE:
        await interaction.followup.send("❌ Este nível não tem recompensa!", ephemeral=True)
        return
    
    del RECOMPENSAS_PASSE[nivel]
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE passe_config SET recompensas = $1 WHERE temporada_id = $2
        """, json.dumps(RECOMPENSAS_PASSE), TEMPORADA_ATUAL["id"])
    
    await interaction.followup.send(f"✅ Recompensa do nível {nivel} removida!", ephemeral=True)


async def cmd_passe_admin_adicionar_pontos(interaction: discord.Interaction, jogador: discord.Member, pontos: int):
    await interaction.response.defer(ephemeral=True)
    
    resultado = await adicionar_pontos_passe(jogador.id, pontos, "admin")
    
    embed = discord.Embed(
        title="✅ PONTOS ADICIONADOS!",
        description=f"{jogador.mention} recebeu **+{pontos} pontos** no passe!\n"
                   f"Novo nível: **{resultado['nivel_novo']}**",
        color=COR_SUCCESS
    )
    await interaction.followup.send(embed=embed, ephemeral=True)


async def cmd_passe_admin_configurar(interaction: discord.Interaction):
    class ConfigurarPasseModal(discord.ui.Modal, title="Configurar Temporada"):
        nome = discord.ui.TextInput(label="Nome da Temporada", default=TEMPORADA_ATUAL["nome"])
        descricao = discord.ui.TextInput(label="Descrição", style=discord.TextStyle.paragraph, default=TEMPORADA_ATUAL["descricao"])
        total_niveis = discord.ui.TextInput(label="Total de Níveis", default=str(TEMPORADA_ATUAL["total_niveis"]))
        xp_por_nivel = discord.ui.TextInput(label="Pontos por Nível", default=str(TEMPORADA_ATUAL["xp_por_nivel"]))
        imagem = discord.ui.TextInput(label="URL da Imagem", default=TEMPORADA_ATUAL["imagem"], required=False)
        
        async def on_submit(self, inter: discord.Interaction):
            global TEMPORADA_ATUAL
            TEMPORADA_ATUAL["nome"] = self.nome.value
            TEMPORADA_ATUAL["descricao"] = self.descricao.value
            TEMPORADA_ATUAL["total_niveis"] = int(self.total_niveis.value)
            TEMPORADA_ATUAL["xp_por_nivel"] = int(self.xp_por_nivel.value)
            TEMPORADA_ATUAL["imagem"] = self.imagem.value
            
            pool = await get_pool()
            async with pool.acquire() as conn:
                await conn.execute("""
                    UPDATE passe_config 
                    SET nome = $1, descricao = $2, total_niveis = $3, xp_por_nivel = $4, imagem = $5
                    WHERE temporada_id = $6
                """, self.nome.value, self.descricao.value, int(self.total_niveis.value), int(self.xp_por_nivel.value), self.imagem.value, TEMPORADA_ATUAL["id"])
            
            await inter.response.send_message("✅ Configuração da temporada atualizada!", ephemeral=True)
    
    await interaction.response.send_modal(ConfigurarPasseModal())


# ==================================================
# REGISTRO DOS COMANDOS
# ==================================================

def register_passe_commands(bot):
    @bot.tree.command(name="passe_ver", description="Mostra seu progresso no passe")
    async def passe_ver(interaction: discord.Interaction):
        await cmd_passe_ver(interaction)
    
    @bot.tree.command(name="passe_resgatar", description="Resgata uma recompensa do passe")
    @app_commands.describe(nivel="Nível da recompensa")
    @app_commands.autocomplete(nivel=autocomplete_nivel)
    async def passe_resgatar(interaction: discord.Interaction, nivel: int):
        await cmd_passe_resgatar(interaction, nivel)
    
    @bot.tree.command(name="passe_ranking", description="Ranking do passe")
    async def passe_ranking(interaction: discord.Interaction):
        await cmd_passe_ranking(interaction)
    
    @bot.tree.command(name="passe_recompensas", description="Lista todas as recompensas")
    async def passe_recompensas(interaction: discord.Interaction):
        await cmd_passe_recompensas(interaction)
    
    @bot.tree.command(name="passe_admin_definir", description="[ADMIN] Define recompensa de um nível")
    @app_commands.describe(nivel="Nível (1-25)", tipo="Tipo da recompensa", valor="Valor", descricao="Descrição", emoji="Emoji")
    @app_commands.checks.has_permissions(administrator=True)
    async def passe_admin_definir(interaction: discord.Interaction, nivel: int, tipo: str, valor: str, descricao: str, emoji: str = "🎁"):
        await cmd_passe_admin_definir_recompensa(interaction, nivel, tipo, valor, descricao, emoji)
    
    @bot.tree.command(name="passe_admin_remover", description="[ADMIN] Remove recompensa de um nível")
    @app_commands.describe(nivel="Nível a remover")
    @app_commands.checks.has_permissions(administrator=True)
    async def passe_admin_remover(interaction: discord.Interaction, nivel: int):
        await cmd_passe_admin_remover_recompensa(interaction, nivel)
    
    @bot.tree.command(name="passe_admin_pontos", description="[ADMIN] Adiciona pontos a um jogador")
    @app_commands.describe(jogador="Jogador", pontos="Quantidade de pontos")
    @app_commands.checks.has_permissions(administrator=True)
    async def passe_admin_pontos(interaction: discord.Interaction, jogador: discord.Member, pontos: int):
        await cmd_passe_admin_adicionar_pontos(interaction, jogador, pontos)
    
    @bot.tree.command(name="passe_admin_config", description="[ADMIN] Configura a temporada")
    @app_commands.checks.has_permissions(administrator=True)
    async def passe_admin_config(interaction: discord.Interaction):
        await cmd_passe_admin_configurar(interaction)