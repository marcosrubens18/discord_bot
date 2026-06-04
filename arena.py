# arena.py — Sistema de Arenas Ranqueadas PvP (1v1, 2v2, 3v3, 4v4, 5v5)
import discord
from discord import app_commands
import asyncio
import json
import random
from datetime import datetime, timedelta
from db import get_pool
from batalha import rodar_pvp, rodar_treino_dupla, ARENAS, BATALHAS_ATIVAS
from constants import COR_PRIMARY, COR_SUCCESS, COR_DANGER, COR_WARNING, COR_INFO, COR_GOLD

# ==================================================
# CONSTANTES
# ==================================================

ELOS = {
    "Ferro": {"rating_min": 0, "rating_max": 499, "emoji": "🟫", "cor": 0x888780, "perde": 15, "ganha": 25, "bonus_mensal": 100},
    "Bronze": {"rating_min": 500, "rating_max": 999, "emoji": "🥉", "cor": 0xCD7F32, "perde": 18, "ganha": 22, "bonus_mensal": 200},
    "Prata": {"rating_min": 1000, "rating_max": 1499, "emoji": "🥈", "cor": 0xC0C0C0, "perde": 20, "ganha": 20, "bonus_mensal": 300},
    "Ouro": {"rating_min": 1500, "rating_max": 1999, "emoji": "🥇", "cor": 0xFFD700, "perde": 22, "ganha": 18, "bonus_mensal": 500},
    "Platina": {"rating_min": 2000, "rating_max": 2499, "emoji": "💎", "cor": 0xE5E4E2, "perde": 25, "ganha": 15, "bonus_mensal": 800},
    "Diamante": {"rating_min": 2500, "rating_max": 2999, "emoji": "💎", "cor": 0x4A90E2, "perde": 28, "ganha": 12, "bonus_mensal": 1200},
    "Mestre": {"rating_min": 3000, "rating_max": 999999, "emoji": "⭐", "cor": 0x7F77DD, "perde": 30, "ganha": 10, "bonus_mensal": 2000},
}

DESAFIOS_POR_DIA = 10

MODOS = {
    "1v1": {"nome": "1v1 Individual", "emoji": "⚔️", "min_jogadores": 1, "max_jogadores": 1, "mult_rating": 1.0},
    "2v2": {"nome": "2v2 Dupla", "emoji": "👥", "min_jogadores": 2, "max_jogadores": 2, "mult_rating": 0.8},
    "3v3": {"nome": "3v3 Party", "emoji": "👥", "min_jogadores": 3, "max_jogadores": 3, "mult_rating": 0.7},
    "4v4": {"nome": "4v4 Party", "emoji": "👥", "min_jogadores": 4, "max_jogadores": 4, "mult_rating": 0.6},
    "5v5": {"nome": "5v5 Party", "emoji": "👥", "min_jogadores": 5, "max_jogadores": 5, "mult_rating": 0.5},
}

# ==================================================
# FUNÇÕES AUXILIARES
# ==================================================

def get_temporada_atual():
    agora = datetime.utcnow()
    return f"{agora.year}_{agora.month}"

def get_proxima_temporada():
    agora = datetime.utcnow()
    if agora.month == 12:
        return f"{agora.year + 1}_1"
    return f"{agora.year}_{agora.month + 1}"

async def get_party_do_jogador(user_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        membro = await conn.fetchrow("""
            SELECT pm.*, p.* 
            FROM party_membros pm
            JOIN parties p ON pm.party_id = p.id
            WHERE pm.user_id = $1 AND p.status = 'ativa'
        """, user_id)
        return dict(membro) if membro else None

async def get_jogador_arena(user_id: int, temporada: str = None):
    if temporada is None:
        temporada = get_temporada_atual()
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        jogador = await conn.fetchrow("""
            SELECT * FROM arena_rankings 
            WHERE user_id = $1 AND temporada = $2
        """, user_id, temporada)
        
        if not jogador:
            p = await conn.fetchrow("SELECT nome FROM personagens WHERE user_id = $1", user_id)
            nome = p["nome"] if p else str(user_id)
            
            jogador = await conn.fetchrow("""
                INSERT INTO arena_rankings (user_id, nome, rating, elo, temporada)
                VALUES ($1, $2, 1000, 'Ferro', $3)
                RETURNING *
            """, user_id, nome, temporada)
        
        return dict(jogador)

async def get_party_arena(party_id: int, temporada: str = None):
    if temporada is None:
        temporada = get_temporada_atual()
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        party = await conn.fetchrow("""
            SELECT * FROM arena_rankings_party 
            WHERE party_id = $1 AND temporada = $2
        """, party_id, temporada)
        
        if not party:
            membros = await conn.fetch("SELECT user_id, nome FROM party_membros WHERE party_id = $1", party_id)
            membros_lista = [{"user_id": m["user_id"], "nome": m["nome"]} for m in membros]
            
            party = await conn.fetchrow("""
                INSERT INTO arena_rankings_party (party_id, party_nome, rating, elo, membros, temporada)
                VALUES ($1, $2, 1000, 'Ferro', $3, $4)
                RETURNING *
            """, party_id, f"Party #{party_id}", json.dumps(membros_lista), temporada)
        
        return dict(party)

async def get_elo_por_rating(rating: int):
    for elo_nome, elo_info in sorted(ELOS.items(), key=lambda x: x[1]["rating_min"], reverse=True):
        if rating >= elo_info["rating_min"]:
            return elo_nome, elo_info
    return "Ferro", ELOS["Ferro"]

async def atualizar_elo_jogador(user_id: int, rating: int, temporada: str = None):
    if temporada is None:
        temporada = get_temporada_atual()
    
    novo_elo, elo_info = await get_elo_por_rating(rating)
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE arena_rankings 
            SET rating = $1, elo = $2, ultima_batalha = NOW()
            WHERE user_id = $3 AND temporada = $4
        """, rating, novo_elo, user_id, temporada)
    
    return novo_elo, elo_info

async def atualizar_elo_party(party_id: int, rating: int, temporada: str = None):
    if temporada is None:
        temporada = get_temporada_atual()
    
    novo_elo, elo_info = await get_elo_por_rating(rating)
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE arena_rankings_party 
            SET rating = $1, elo = $2, ultima_batalha = NOW()
            WHERE party_id = $3 AND temporada = $4
        """, rating, novo_elo, party_id, temporada)
    
    return novo_elo, elo_info

async def registrar_desafio(user_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        hoje = datetime.utcnow().date()
        
        existe = await conn.fetchrow("""
            SELECT desafios_feitos FROM arena_desafios 
            WHERE user_id = $1 AND data = $2
        """, user_id, hoje)
        
        if existe:
            if existe["desafios_feitos"] >= DESAFIOS_POR_DIA:
                return False, existe["desafios_feitos"]
            
            await conn.execute("""
                UPDATE arena_desafios SET desafios_feitos = desafios_feitos + 1
                WHERE user_id = $1 AND data = $2
            """, user_id, hoje)
            return True, existe["desafios_feitos"] + 1
        else:
            await conn.execute("""
                INSERT INTO arena_desafios (user_id, data, desafios_feitos)
                VALUES ($1, $2, 1)
            """, user_id, hoje)
            return True, 1

async def registrar_batalha_arena(user_id: int, oponente_id: int, oponente_nome: str, modo: str, vitoria: bool, rating_antes: int, rating_depois: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO arena_historico (user_id, oponente_id, oponente_nome, modo, resultado, rating_antes, rating_depois)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, user_id, oponente_id, oponente_nome, modo, "vitoria" if vitoria else "derrota", rating_antes, rating_depois)
        
        if vitoria:
            await conn.execute("""
                UPDATE arena_rankings SET vitorias = vitorias + 1
                WHERE user_id = $1 AND temporada = $2
            """, user_id, get_temporada_atual())
        else:
            await conn.execute("""
                UPDATE arena_rankings SET derrotas = derrotas + 1
                WHERE user_id = $1 AND temporada = $2
            """, user_id, get_temporada_atual())

async def get_ranking_arena(limite: int = 10, elo_filtro: str = None, modo: str = "1v1"):
    pool = await get_pool()
    async with pool.acquire() as conn:
        temporada = get_temporada_atual()
        
        if modo == "party":
            if elo_filtro:
                ranking = await conn.fetch("""
                    SELECT party_id, party_nome as nome, rating, elo, vitorias, derrotas
                    FROM arena_rankings_party
                    WHERE temporada = $1 AND elo = $2
                    ORDER BY rating DESC
                    LIMIT $3
                """, temporada, elo_filtro, limite)
            else:
                ranking = await conn.fetch("""
                    SELECT party_id, party_nome as nome, rating, elo, vitorias, derrotas
                    FROM arena_rankings_party
                    WHERE temporada = $1
                    ORDER BY rating DESC
                    LIMIT $2
                """, temporada, limite)
        else:
            if elo_filtro:
                ranking = await conn.fetch("""
                    SELECT user_id, nome, rating, elo, vitorias, derrotas
                    FROM arena_rankings
                    WHERE temporada = $1 AND elo = $2
                    ORDER BY rating DESC
                    LIMIT $3
                """, temporada, elo_filtro, limite)
            else:
                ranking = await conn.fetch("""
                    SELECT user_id, nome, rating, elo, vitorias, derrotas
                    FROM arena_rankings
                    WHERE temporada = $1
                    ORDER BY rating DESC
                    LIMIT $2
                """, temporada, limite)
        
        return ranking

# ==================================================
# COMANDO: DESAFIAR 1v1
# ==================================================

async def cmd_arena_desafiar(interaction: discord.Interaction, jogador: discord.Member):
    await interaction.response.defer()
    
    if jogador.id == interaction.user.id:
        await interaction.followup.send("❌ Você não pode desafiar a si mesmo!", ephemeral=True)
        return
    
    p1 = await get_personagem(interaction.user.id)
    p2 = await get_personagem(jogador.id)
    
    if not p1 or not p2:
        await interaction.followup.send("❌ Um dos jogadores não tem personagem!", ephemeral=True)
        return
    
    if interaction.user.id in BATALHAS_ATIVAS or jogador.id in BATALHAS_ATIVAS:
        await interaction.followup.send("❌ Um dos jogadores já está em batalha!", ephemeral=True)
        return
    
    pode, desafios = await registrar_desafio(interaction.user.id)
    if not pode:
        await interaction.followup.send(f"❌ Você atingiu o limite de {DESAFIOS_POR_DIA} desafios por dia!", ephemeral=True)
        return
    
    j1 = await get_jogador_arena(interaction.user.id)
    j2 = await get_jogador_arena(jogador.id)
    
    rating_diff = j2["rating"] - j1["rating"]
    expected = 1 / (1 + 10 ** (rating_diff / 400))
    
    class AceitarDesafioView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)
            self.aceito = False
        
        @discord.ui.button(label="✅ Aceitar", style=discord.ButtonStyle.success)
        async def aceitar(self, inter: discord.Interaction, button):
            if inter.user.id != jogador.id:
                await inter.response.send_message("❌ Este desafio não é para você!", ephemeral=True)
                return
            self.aceito = True
            self.stop()
        
        @discord.ui.button(label="❌ Recusar", style=discord.ButtonStyle.danger)
        async def recusar(self, inter: discord.Interaction, button):
            if inter.user.id != jogador.id:
                await inter.response.send_message("❌ Este desafio não é para você!", ephemeral=True)
                return
            self.aceito = False
            self.stop()
    
    embed_convite = discord.Embed(
        title="⚔️ DESAFIO DE ARENA 1v1!",
        description=f"**{interaction.user.display_name}** ({j1['elo']} - {j1['rating']} pts) desafiou **{jogador.display_name}** ({j2['elo']} - {j2['rating']} pts)!\n\n"
                   f"🎯 Chance de vitória: {expected*100:.1f}%\n"
                   f"⭐ Rating em jogo: ~{abs(j1['rating'] - j2['rating']) // 10 + 15} pontos\n\n"
                   f"⏱️ Você tem 60 segundos para aceitar!",
        color=COR_WARNING
    )
    
    view = AceitarDesafioView()
    await interaction.followup.send(content=jogador.mention, embed=embed_convite, view=view)
    await view.wait()
    
    if not view.aceito:
        await interaction.edit_original_response(content="❌ Desafio recusado ou expirado!", embed=None, view=None)
        return
    
    arena = random.choice(ARENAS)
    
    embed_luta = discord.Embed(
        title=f"⚔️ BATALHA RANQUEADA 1v1! ⚔️",
        description=f"**{interaction.user.display_name}** vs **{jogador.display_name}**\n"
                   f"🏟️ Arena: {arena['emoji']} {arena['nome']}\n\n"
                   f"⭐ Rating em jogo!",
        color=COR_PRIMARY
    )
    await interaction.edit_original_response(embed=embed_luta, view=None)
    
    rating_antes1 = j1["rating"]
    rating_antes2 = j2["rating"]
    
    async def callback_resultado(vencedor_id, perdedor_id):
        if vencedor_id == interaction.user.id:
            ganho = ELOS[j2["elo"]]["ganha"]
            rating_novo1 = rating_antes1 + ganho
            rating_novo2 = rating_antes2 - ELOS[j1["elo"]]["perde"]
            
            await atualizar_elo_jogador(interaction.user.id, rating_novo1)
            await atualizar_elo_jogador(jogador.id, rating_novo2)
            
            await registrar_batalha_arena(interaction.user.id, jogador.id, j2["nome"], "1v1", True, rating_antes1, rating_novo1)
            await registrar_batalha_arena(jogador.id, interaction.user.id, j1["nome"], "1v1", False, rating_antes2, rating_novo2)
            
            novo_elo1, _ = await get_elo_por_rating(rating_novo1)
            novo_elo2, _ = await get_elo_por_rating(rating_novo2)
            
            embed_resultado = discord.Embed(
                title="🏆 VITÓRIA NA ARENA!",
                description=f"**{interaction.user.display_name}** venceu a batalha!\n\n"
                           f"📈 Rating: {rating_antes1} → **{rating_novo1}** (+{ganho})\n"
                           f"🏅 Elo: {j1['elo']} → **{novo_elo1}**\n\n"
                           f"📉 {jogador.display_name}: {rating_antes2} → {rating_novo2} (-{ELOS[j1['elo']]['perde']})",
                color=COR_SUCCESS
            )
            await interaction.channel.send(embed=embed_resultado)
        else:
            ganho = ELOS[j1["elo"]]["ganha"]
            rating_novo1 = rating_antes1 - ELOS[j2["elo"]]["perde"]
            rating_novo2 = rating_antes2 + ganho
            
            await atualizar_elo_jogador(interaction.user.id, rating_novo1)
            await atualizar_elo_jogador(jogador.id, rating_novo2)
            
            await registrar_batalha_arena(interaction.user.id, jogador.id, j2["nome"], "1v1", False, rating_antes1, rating_novo1)
            await registrar_batalha_arena(jogador.id, interaction.user.id, j1["nome"], "1v1", True, rating_antes2, rating_novo2)
            
            novo_elo1, _ = await get_elo_por_rating(rating_novo1)
            novo_elo2, _ = await get_elo_por_rating(rating_novo2)
            
            embed_resultado = discord.Embed(
                title="🏆 VITÓRIA NA ARENA!",
                description=f"**{jogador.display_name}** venceu a batalha!\n\n"
                           f"📈 Rating: {rating_antes2} → **{rating_novo2}** (+{ganho})\n"
                           f"🏅 Elo: {j2['elo']} → **{novo_elo2}**\n\n"
                           f"📉 {interaction.user.display_name}: {rating_antes1} → {rating_novo1} (-{ELOS[j2['elo']]['perde']})",
                color=COR_SUCCESS
            )
            await interaction.channel.send(embed=embed_resultado)
    
    await rodar_pvp(interaction.channel, p1, p2, interaction.user, jogador, arena, callback=callback_resultado)

# ==================================================
# COMANDO: RANKING
# ==================================================

async def cmd_arena_ranking(interaction: discord.Interaction, modo: str = "1v1", elo: str = None):
    await interaction.response.defer()
    
    ranking = await get_ranking_arena(15, elo, modo)
    
    if not ranking:
        await interaction.followup.send("❌ Nenhum jogador encontrado no ranking!", ephemeral=True)
        return
    
    modo_info = MODOS.get(modo, MODOS["1v1"])
    titulo = f"RANKING - {modo_info['nome']}"
    
    embed = discord.Embed(
        title=f"🏆 {titulo}",
        description=f"Temporada: **{get_temporada_atual()}**\n" + ("Filtro: **" + elo + "**" if elo else "Geral"),
        color=COR_GOLD
    )
    
    for i, r in enumerate(ranking):
        medalha = "🥇 " if i == 0 else "🥈 " if i == 1 else "🥉 " if i == 2 else f"{i+1}° "
        embed.add_field(
            name=f"{medalha}{r['nome']}",
            value=f"🏅 {r['elo']} | ⭐ {r['rating']} pts | {r['vitorias']}W/{r['derrotas']}L",
            inline=False
        )
    
    embed.set_footer(text=f"Use /arena_meuperfil para ver seus dados | {DESAFIOS_POR_DIA} desafios/dia")
    await interaction.followup.send(embed=embed)

# ==================================================
# COMANDO: MEU PERFIL
# ==================================================

async def cmd_arena_meuperfil(interaction: discord.Interaction):
    await interaction.response.defer()
    
    j = await get_jogador_arena(interaction.user.id)
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        historico = await conn.fetch("""
            SELECT * FROM arena_historico 
            WHERE user_id = $1 
            ORDER BY data DESC LIMIT 10
        """, interaction.user.id)
        
        hoje = datetime.utcnow().date()
        desafios = await conn.fetchrow("""
            SELECT desafios_feitos FROM arena_desafios 
            WHERE user_id = $1 AND data = $2
        """, interaction.user.id, hoje)
    
    desafios_feitos = desafios["desafios_feitos"] if desafios else 0
    
    elo_info = ELOS.get(j["elo"], ELOS["Ferro"])
    
    proximo_elo = None
    proximo_rating = 999999
    for elo_nome, elo_info_prox in ELOS.items():
        if elo_info_prox["rating_min"] > j["rating"]:
            proximo_elo = elo_nome
            proximo_rating = elo_info_prox["rating_min"]
            break
    
    if proximo_elo:
        progresso = j["rating"] - elo_info["rating_min"]
        necessario = proximo_rating - elo_info["rating_min"]
        pct = min(1.0, progresso / necessario) if necessario > 0 else 0
        f = int(pct * 10)
        barra = "█" * f + "░" * (10 - f)
        progresso_txt = f"`{barra}` {progresso}/{necessario} pts para {proximo_elo}"
    else:
        progresso_txt = "🏆 **MESTRE** - Topo do ranking!"
    
    hist_txt = ""
    for h in historico[:5]:
        emoji = "✅" if h["resultado"] == "vitoria" else "❌"
        modo_emoji = "⚔️" if h["modo"] == "1v1" else "👥"
        hist_txt += f"{emoji} {modo_emoji} vs {h['oponente_nome']} — {h['rating_antes']} → {h['rating_depois']}\n"
    
    if not hist_txt:
        hist_txt = "Nenhuma batalha registrada nesta temporada"
    
    embed = discord.Embed(
        title=f"🏅 PERFIL DA ARENA - {j['nome']}",
        color=elo_info["cor"]
    )
    embed.add_field(name="🏅 Elo", value=f"{elo_info['emoji']} {j['elo']}", inline=True)
    embed.add_field(name="⭐ Rating", value=f"{j['rating']} pts", inline=True)
    embed.add_field(name="📊 Recorde", value=f"{j['vitorias']}W/{j['derrotas']}L", inline=True)
    embed.add_field(name="📈 Progresso", value=progresso_txt, inline=False)
    embed.add_field(name="🎯 Desafios Hoje", value=f"{desafios_feitos}/{DESAFIOS_POR_DIA}", inline=True)
    embed.add_field(name="🏆 Bônus Temporada", value=f"+{elo_info['bonus_mensal']} moedas", inline=True)
    embed.add_field(name="📜 Últimas Batalhas", value=hist_txt, inline=False)
    embed.set_footer(text=f"Temporada: {get_temporada_atual()}")
    
    await interaction.followup.send(embed=embed)

# ==================================================
# COMANDO: RECOMPENSAS
# ==================================================

async def cmd_arena_recompensas(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        recompensas = await conn.fetch("""
            SELECT * FROM arena_recompensas 
            WHERE user_id = $1 AND recebida = FALSE
            ORDER BY temporada DESC
        """, interaction.user.id)
    
    if not recompensas:
        await interaction.followup.send("❌ Nenhuma recompensa pendente!", ephemeral=True)
        return
    
    total_moedas = 0
    total_fichas = 0
    
    for r in recompensas:
        elo_info = ELOS.get(r["elo_final"], ELOS["Ferro"])
        total_moedas += elo_info["bonus_mensal"]
        
        if r["elo_final"] in ["Platina", "Diamante", "Mestre"]:
            total_fichas += 1
        
        await conn.execute("""
            UPDATE arena_recompensas SET recebida = TRUE
            WHERE user_id = $1 AND temporada = $2
        """, interaction.user.id, r["temporada"])
    
    pool_db = await get_pool()
    async with pool_db.acquire() as conn:
        await conn.execute("""
            UPDATE personagens SET moedas = moedas + $1
            WHERE user_id = $2
        """, total_moedas, interaction.user.id)
        
        if total_fichas > 0:
            await conn.execute("""
                INSERT INTO giros (user_id, roleta_id, raridade, quantidade)
                VALUES ($1, 'skill', 'Epico', $2)
                ON CONFLICT (user_id, roleta_id, raridade)
                DO UPDATE SET quantidade = giros.quantidade + $2
            """, interaction.user.id, total_fichas)
    
    embed = discord.Embed(
        title="💰 RECOMPENSAS RESGATADAS!",
        description=f"Você resgatou recompensas de {len(recompensas)} temporada(s)!\n\n"
                   f"🪙 +{total_moedas} moedas\n"
                   f"🎰 +{total_fichas} fichas épicas",
        color=COR_SUCCESS
    )
    await interaction.followup.send(embed=embed, ephemeral=True)

# ==================================================
# COMANDO: TEMPORADA
# ==================================================

async def cmd_arena_temporada(interaction: discord.Interaction):
    await interaction.response.defer()
    
    temporada_atual = get_temporada_atual()
    ano, mes = map(int, temporada_atual.split("_"))
    data_inicio = datetime(ano, mes, 1)
    if mes == 12:
        data_fim = datetime(ano + 1, 1, 1)
    else:
        data_fim = datetime(ano, mes + 1, 1)
    
    embed = discord.Embed(
        title="📅 TEMPORADA DA ARENA",
        description=f"**Temporada:** {temporada_atual}\n"
                   f"**Início:** {data_inicio.strftime('%d/%m/%Y')}\n"
                   f"**Término:** {data_fim.strftime('%d/%m/%Y')}\n\n"
                   f"**Recompensas por Elo:**",
        color=COR_PRIMARY
    )
    
    for elo_nome, elo_info in ELOS.items():
        embed.add_field(
            name=f"{elo_info['emoji']} {elo_nome}",
            value=f"💰 +{elo_info['bonus_mensal']} moedas\n" + ("🎰 +1 ficha épica" if elo_nome in ["Platina", "Diamante", "Mestre"] else ""),
            inline=True
        )
    
    embed.set_footer(text="As recompensas são resgatadas no início da próxima temporada!")
    await interaction.followup.send(embed=embed)

# ==================================================
# REGISTRO DOS COMANDOS
# ==================================================

def register_arena_commands(bot):
    @bot.tree.command(name="arena_desafiar", description="Desafia um jogador para batalha ranqueada 1v1")
    @app_commands.describe(jogador="Jogador a ser desafiado")
    async def arena_desafiar(interaction: discord.Interaction, jogador: discord.Member):
        await cmd_arena_desafiar(interaction, jogador)
    
    @bot.tree.command(name="arena_ranking", description="Mostra o ranking da arena")
    @app_commands.describe(modo="Modo de jogo", elo="Filtrar por elo")
    @app_commands.choices(modo=[
        app_commands.Choice(name="1v1 Individual", value="1v1"),
        app_commands.Choice(name="Party/Ranking de Party", value="party"),
    ])
    @app_commands.choices(elo=[
        app_commands.Choice(name="Ferro", value="Ferro"),
        app_commands.Choice(name="Bronze", value="Bronze"),
        app_commands.Choice(name="Prata", value="Prata"),
        app_commands.Choice(name="Ouro", value="Ouro"),
        app_commands.Choice(name="Platina", value="Platina"),
        app_commands.Choice(name="Diamante", value="Diamante"),
        app_commands.Choice(name="Mestre", value="Mestre"),
    ])
    async def arena_ranking(interaction: discord.Interaction, modo: str = "1v1", elo: str = None):
        await cmd_arena_ranking(interaction, modo, elo)
    
    @bot.tree.command(name="arena_meuperfil", description="Mostra seu perfil na arena")
    async def arena_meuperfil(interaction: discord.Interaction):
        await cmd_arena_meuperfil(interaction)
    
    @bot.tree.command(name="arena_recompensas", description="Resgata recompensas de temporadas anteriores")
    async def arena_recompensas(interaction: discord.Interaction):
        await cmd_arena_recompensas(interaction)
    
    @bot.tree.command(name="arena_temporada", description="Mostra informações da temporada atual")
    async def arena_temporada(interaction: discord.Interaction):
        await cmd_arena_temporada(interaction)