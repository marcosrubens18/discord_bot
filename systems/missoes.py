# systems/missoes.py — Sistema de Missões Diárias

import discord
import random
from datetime import date, datetime, timezone
from typing import Optional, List

from database.db import get_pool
from database.queries import get_personagem
from data.ranks import get_rank
from data.constantes import EMOJI_FICHA, COR_PRIMARY, COR_SUCCESS, COR_DANGER, COR_WARNING, COR_INFO
from utils.calculos import calcular_mana_max


# ==================================================
# POOL DE MISSÕES
# ==================================================

POOL_MISSOES = [
    # Rank F
    ("vencer_batalhas_1",  "Vença 1 batalha de treino",           "vitorias_treino", 1,  35,  20,  None,      "F"),
    ("vencer_batalhas_3",  "Vença 3 batalhas de treino",          "vitorias_treino", 3,  90,  55,  None,      "F"),
    ("usar_skills_5",      "Use skills 5 vezes em batalha",       "skills_usadas",   5,  45,  30,  None,      "F"),
    ("usar_pocao",         "Use uma poção em batalha",            "pocoes_usadas",   1,  25,  15,  None,      "F"),
    ("usar_hospital",      "Use o hospital",                      "hospital_usado",  1,  25,  0,   None,      "F"),
    ("gastos_loja",        "Gaste 100 moedas na loja",            "moedas_gastas",   100,45,  0,   None,      "F"),
    ("coleta_loot",        "Colete loot em 3 batalhas",           "loots_coletados", 3,  65,  40,  None,      "F"),
    
    # Rank E
    ("vencer_batalhas_5",  "Vença 5 batalhas de treino",          "vitorias_treino", 5,  160, 100, "Incomum", "E"),
    ("dungeon_qualquer",   "Complete qualquer dungeon",            "dungeons",        1,  110, 85,  "Incomum", "E"),
    ("nivel_up",           "Suba de nível",                       "level_ups",       1,  70,  50,  "Incomum", "E"),
    ("usar_skills_10",     "Use skills 10 vezes em batalha",      "skills_usadas",   10, 90,  65,  None,      "E"),
    ("usar_pocao_3",       "Use 3 poções em batalha",             "pocoes_usadas",   3,  70,  45,  None,      "E"),
    
    # Rank D
    ("pvp_participar",     "Participe de um duelo PvP",           "pvp_jogados",     1,  60,  45,  None,      "D"),
    ("pvp_vencer",         "Vença um duelo PvP",                  "pvp_vitorias",    1,  140, 100, "Raro",    "D"),
    ("treino_medio",       "Vença 5 treinos Médios",              "vitorias_treino", 5,  120, 80,  None,      "D"),
    
    # Rank C
    ("dungeon_c_plus",     "Complete dungeon Rank C ou acima",    "dungeons_c_plus", 1,  220, 160, "Raro",    "C"),
    ("treino_dificil",     "Vença um treino Difícil",             "treino_hard",     1,  120, 80,  "Raro",    "C"),
    ("pvp_vencer_3",       "Vença 3 duelos PvP",                  "pvp_vitorias",    3,  350, 220, "Epico",   "C"),
    
    # Rank B
    ("treino_lendario",    "Vença um treino Lendário",            "treino_hard",     1,  200, 150, "Epico",   "B"),
    ("dungeon_b_plus",     "Complete dungeon Rank B ou acima",    "dungeons_c_plus", 1,  400, 300, "Epico",   "B"),
    
    # Rank S
    ("dungeon_s",          "Complete dungeon Rank S",             "dungeons_c_plus", 1,  800, 600, "Lendario","S"),
    ("pvp_5_vitorias",     "Vença 5 duelos PvP seguidos",         "pvp_vitorias",    5,  700, 500, "Lendario","S"),
]

RANK_ORDEM = ["F", "E", "D", "C", "B", "A", "S", "SS"]


def sortear_missoes_dia(rank_atual: str = "F") -> list:
    """Sorteia 3 missões diárias baseadas no rank do jogador"""
    rank_idx = RANK_ORDEM.index(rank_atual) if rank_atual in RANK_ORDEM else 0
    disponiveis = [m for m in POOL_MISSOES if RANK_ORDEM.index(m[7]) <= rank_idx]
    if len(disponiveis) < 3:
        disponiveis = POOL_MISSOES[:7]
    return random.sample(disponiveis, min(3, len(disponiveis)))


# ==================================================
# FUNÇÕES AUXILIARES
# ==================================================

async def get_missoes_hoje(user_id: int) -> list:
    """Retorna as missões do jogador para hoje"""
    hoje = date.today().isoformat()
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch(
            "SELECT * FROM missoes_diarias WHERE user_id = $1 AND data = $2",
            user_id, hoje
        )


async def criar_missoes_hoje(user_id: int, rank_atual: str = "F") -> bool:
    """Cria novas missões diárias para o jogador"""
    hoje = date.today().isoformat()
    missoes = sortear_missoes_dia(rank_atual)
    pool = await get_pool()
    async with pool.acquire() as conn:
        for m in missoes:
            mid, desc, tipo, meta, xp, moedas, ficha, rank_min = m
            await conn.execute("""
                INSERT INTO missoes_diarias
                (user_id, data, missao_id, descricao, tipo, meta, progresso, concluida, xp, moedas, ficha)
                VALUES ($1, $2, $3, $4, $5, $6, 0, 0, $7, $8, $9)
                ON CONFLICT DO NOTHING
            """, user_id, hoje, mid, desc, tipo, meta, xp, moedas, ficha or "")
    return True


async def resetar_missoes_diarias():
    """Reseta as missões diárias de todos os jogadores (chamado à meia-noite)"""
    hoje = date.today().isoformat()
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM missoes_diarias WHERE data < $1", hoje)
    print(f"[MISSOES] Reset diário executado para {hoje}")


async def atualizar_progresso(user_id: int, tipo: str, quantidade: int = 1) -> list:
    """
    Atualiza o progresso de uma missão do tipo especificado.
    Retorna lista de recompensas concedidas.
    """
    hoje = date.today().isoformat()
    pool = await get_pool()
    recompensas = []
    
    async with pool.acquire() as conn:
        missoes = await conn.fetch("""
            SELECT * FROM missoes_diarias 
            WHERE user_id = $1 AND data = $2 AND tipo = $3 AND concluida = 0
        """, user_id, hoje, tipo)
        
        for m in missoes:
            novo_prog = m["progresso"] + quantidade
            if novo_prog >= m["meta"]:
                # Conclui a missão
                await conn.execute("""
                    UPDATE missoes_diarias 
                    SET progresso = $1, concluida = 1 
                    WHERE user_id = $2 AND data = $3 AND missao_id = $4
                """, m["meta"], user_id, hoje, m["missao_id"])
                
                # Busca personagem para aplicar XP e level up
                p_atual = await conn.fetchrow("""
                    SELECT xp, nivel, hp_max, ataque, defesa, mana_max, mana_atual, 
                           poder_valor, destino_id, classe_id 
                    FROM personagens WHERE user_id = $1
                """, user_id)
                
                if p_atual:
                    novo_xp = p_atual["xp"] + m["xp"]
                    nv = p_atual["nivel"]
                    levelups = 0
                    needed = 100 + (nv - 1) * 50
                    
                    while novo_xp >= needed:
                        novo_xp -= needed
                        nv += 1
                        needed = 100 + (nv - 1) * 50
                        levelups += 1
                    
                    hp_max = p_atual["hp_max"] + levelups * 6
                    atk = p_atual["ataque"] + levelups * 2
                    dfs = p_atual["defesa"] + levelups * 1
                    
                    mana_max = calcular_mana_max(
                        p_atual["classe_id"], nv, 
                        p_atual["poder_valor"], p_atual["destino_id"]
                    )
                    
                    await conn.execute("""
                        UPDATE personagens 
                        SET xp = $1, nivel = $2, hp_max = $3, ataque = $4, defesa = $5, 
                            mana_max = $6, moedas = moedas + $7 
                        WHERE user_id = $8
                    """, novo_xp, nv, hp_max, atk, dfs, mana_max, m["moedas"], user_id)
                    
                    # Registrar level up no evento
                    if levelups > 0:
                        try:
                            from systems.eventos import registrar_level_up_evento
                            await registrar_level_up_evento(user_id, levelups)
                        except:
                            pass
                else:
                    await conn.execute("""
                        UPDATE personagens SET xp = xp + $1, moedas = moedas + $2 
                        WHERE user_id = $3
                    """, m["xp"], m["moedas"], user_id)
                
                # Adiciona ficha se houver
                if m["ficha"]:
                    await conn.execute("""
                        INSERT INTO giros (user_id, roleta_id, raridade, quantidade)
                        VALUES ($1, 'skill', $2, 1)
                        ON CONFLICT (user_id, roleta_id, raridade)
                        DO UPDATE SET quantidade = giros.quantidade + 1
                    """, user_id, m["ficha"])
                
                recompensas.append({
                    "descricao": m["descricao"],
                    "xp": m["xp"],
                    "moedas": m["moedas"],
                    "ficha": m["ficha"]
                })
            else:
                # Atualiza progresso
                await conn.execute("""
                    UPDATE missoes_diarias 
                    SET progresso = $1 
                    WHERE user_id = $2 AND data = $3 AND missao_id = $4
                """, novo_prog, user_id, hoje, m["missao_id"])
    
    return recompensas


# ==================================================
# COMANDOS
# ==================================================

async def cmd_missoes(interaction: discord.Interaction):
    """Comando /missoes - Mostra as missões diárias"""
    await interaction.response.defer(ephemeral=True)
    
    p = await get_personagem(interaction.user.id)
    if not p:
        await interaction.followup.send("Crie seu personagem primeiro!", ephemeral=True)
        return

    missoes = await get_missoes_hoje(interaction.user.id)
    if not missoes:
        rank_atual = get_rank(p["nivel"])["rank"]
        await criar_missoes_hoje(interaction.user.id, rank_atual)
        missoes = await get_missoes_hoje(interaction.user.id)

    hoje = date.today().strftime("%d/%m/%Y")
    embed = discord.Embed(
        title=f"📋 Missões Diárias — {hoje}",
        description="Complete missões para ganhar XP, moedas e fichas!\nRenovam todo dia à meia-noite.",
        color=COR_PRIMARY
    )

    total_concluidas = 0
    for m in missoes:
        if m["concluida"]:
            status = "✅ Concluída"
            barra = "██████████"
            total_concluidas += 1
        else:
            pct = m["progresso"] / max(1, m["meta"])
            f = int(pct * 10)
            barra = "█" * f + "░" * (10 - f)
            status = "🔄 Em progresso"
        
        recomp = f"+{m['xp']} XP | +{m['moedas']} 🪙"
        if m["ficha"]:
            fe = EMOJI_FICHA.get(m["ficha"], "⬜")
            recomp += f" | {fe} Ficha {m['ficha']}"
        
        embed.add_field(
            name=f"{'✅' if m['concluida'] else '🔄'} {m['descricao']}",
            value=f"`{barra}` {m['progresso']}/{m['meta']}\n{recomp}",
            inline=False
        )
    
    embed.set_footer(text=f"Concluídas: {total_concluidas}/3 hoje")
    await interaction.followup.send(embed=embed, ephemeral=True)


async def cmd_ranking(interaction: discord.Interaction):
    """Comando /ranking - Mostra os rankings do servidor"""
    await interaction.response.defer()
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        top_nivel = await conn.fetch("""
            SELECT nome, classe_id, nivel, xp 
            FROM personagens ORDER BY nivel DESC, xp DESC LIMIT 10
        """)
        top_vitorias = await conn.fetch("""
            SELECT nome, classe_id, vitorias 
            FROM personagens ORDER BY vitorias DESC LIMIT 10
        """)
        top_moedas = await conn.fetch("""
            SELECT nome, classe_id, moedas 
            FROM personagens ORDER BY moedas DESC LIMIT 10
        """)
        
        try:
            top_dungeons = await conn.fetch("""
                SELECT p.nome, p.classe_id, COUNT(*) as total
                FROM dungeon_evento_runs r 
                JOIN personagens p ON r.user_id = p.user_id
                WHERE r.concluida = TRUE 
                GROUP BY p.user_id, p.nome, p.classe_id
                ORDER BY total DESC LIMIT 10
            """)
        except:
            top_dungeons = []
        
        try:
            top_torneios = await conn.fetch("""
                SELECT p.nome, p.classe_id, COUNT(*) as total
                FROM torneio_lutas l 
                JOIN personagens p ON l.vencedor_id = p.user_id
                WHERE l.fase = 'FINAL' 
                GROUP BY p.user_id, p.nome, p.classe_id
                ORDER BY total DESC LIMIT 10
            """)
        except:
            top_torneios = []

    EMOJI_CLS = {
        "guerreiro": "🗡️", "mago": "🔮", "arqueiro": "🏹",
        "paladino": "⚡", "necromante": "🌑", "dracomante": "🐉", "arcano": "✨"
    }

    def fmt(rows, col, sufixo=""):
        if not rows:
            return "—"
        return "\n".join([
            f"**{i+1}.** {EMOJI_CLS.get(r['classe_id'], '⚔️')} {r['nome']} — {r[col]}{sufixo}" 
            for i, r in enumerate(rows)
        ])

    embed = discord.Embed(title="🏆 Ranking de Villa Eldoria", color=COR_GOLD)
    embed.add_field(name="📈 Maior Nível", value=fmt(top_nivel, "nivel", " Nv"), inline=True)
    embed.add_field(name="⚔️ Mais Vitórias", value=fmt(top_vitorias, "vitorias", " wins"), inline=True)
    embed.add_field(name="🪙 Mais Rico", value=fmt(top_moedas, "moedas", " 🪙"), inline=True)
    
    if top_dungeons:
        embed.add_field(name="🏰 Dungeons Concluídas", value=fmt(top_dungeons, "total", "x"), inline=True)
    if top_torneios:
        embed.add_field(name="🏆 Torneios Vencidos", value=fmt(top_torneios, "total", "x"), inline=True)
    
    await interaction.followup.send(embed=embed)


# ==================================================
# AGENDADOR DE RESET DIÁRIO
# ==================================================

async def iniciar_agendador_reset(bot):
    """Inicia o agendador de reset diário das missões"""
    import asyncio
    from datetime import datetime
    
    async def reset_loop():
        while True:
            agora = datetime.now()
            # Calcula próximo reset (meia-noite)
            meia_noite = datetime(agora.year, agora.month, agora.day + 1, 0, 0, 0)
            segundos_ate_reset = (meia_noite - agora).total_seconds()
            
            await asyncio.sleep(segundos_ate_reset)
            await resetar_missoes_diarias()
            print("[MISSOES] Reset diário executado!")
    
    asyncio.create_task(reset_loop())

# Adicione no final do arquivo systems/missoes.py

async def iniciar_agendador_reset(bot):
    """Inicia o agendador de reset diário das missões"""
    import asyncio
    from datetime import datetime
    
    async def reset_loop():
        while True:
            agora = datetime.now()
            # Calcula próximo reset (meia-noite)
            meia_noite = datetime(agora.year, agora.month, agora.day + 1, 0, 0, 0)
            segundos_ate_reset = (meia_noite - agora).total_seconds()
            
            await asyncio.sleep(segundos_ate_reset)
            await resetar_missoes_diarias()
            print("[MISSOES] Reset diário executado!")
    
    # Inicia o loop em background
    asyncio.create_task(reset_loop())
