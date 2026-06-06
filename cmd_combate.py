# cmd_combate.py — Comandos de combate

import discord
from discord import app_commands
import random
import asyncio

from sistema_personagem import get_personagem
from data_monstros import MONSTROS
from constants import ARENAS, COOLDOWN_BATALHA
from sistema_combate import rodar_treino, rodar_pvp, BATALHAS_ATIVAS
from sistema_combate import EscolherArenaView, AceitarDueloView, cooldown_manager
from sistema_dupla import rodar_treino_dupla


# ==================================================
# FUNÇÕES AUXILIARES
# ==================================================

async def get_treino_uso(user_id):
    from db import get_pool
    from datetime import datetime, timezone
    
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow('SELECT * FROM treino_uso WHERE user_id=$1', user_id)
            if not row:
                return 0, None
            now = datetime.now(timezone.utc)
            if row['reset_em'] and now >= row['reset_em']:
                await conn.execute('UPDATE treino_uso SET count=0, reset_em=NULL WHERE user_id=$1', user_id)
                return 0, None
            return row['count'], row['reset_em']
    except Exception as e:
        print(f'Erro get_treino_uso: {e}')
        return 0, None


async def incrementar_treino_uso(user_id):
    from db import get_pool
    from datetime import datetime, timedelta, timezone
    
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow('SELECT count FROM treino_uso WHERE user_id=$1', user_id)
            novo = (row['count'] if row else 0) + 1
            reset_em = datetime.now(timezone.utc) + timedelta(hours=2) if novo >= 20 else None
            await conn.execute(
                'INSERT INTO treino_uso(user_id, count, reset_em) VALUES($1,$2,$3) ON CONFLICT(user_id) DO UPDATE SET count=$2, reset_em=COALESCE($3, treino_uso.reset_em)',
                user_id, novo, reset_em)
    except Exception as e:
        print(f'Erro incrementar_treino_uso: {e}')


def em_batalha(uid):
    return uid in BATALHAS_ATIVAS


# ==================================================
# COMANDO TREINAR
# ==================================================

async def cmd_treinar(interaction: discord.Interaction, dificuldade: str = "facil"):
    await interaction.response.defer()
    
    if em_batalha(interaction.user.id):
        await interaction.followup.send("Você já está em batalha!", ephemeral=True)
        return
    
    p = await get_personagem(interaction.user.id)
    if not p:
        await interaction.followup.send("Use `/criar_personagem` primeiro!", ephemeral=True)
        return
    
    count, reset_em = await get_treino_uso(interaction.user.id)
    if count >= 20 and reset_em:
        from datetime import datetime, timezone
        secs = int((reset_em - datetime.now(timezone.utc)).total_seconds())
        mins = secs // 60
        segs = secs % 60
        await interaction.followup.send(
            f"⏰ Você já treinou 20 vezes! Descanse. Próximo treino em {mins}min {segs}s.", ephemeral=True)
        return
    
    monstros_d = [m for m in MONSTROS if m["dificuldade"] == dificuldade]
    if not monstros_d:
        await interaction.followup.send("Dificuldade inválida!", ephemeral=True)
        return
    monstro = random.choice(monstros_d)

    view_arena = EscolherArenaView(interaction.user.id)
    embed_arena = discord.Embed(
        title="🏟️ Escolha a Arena!",
        description=f"Você vai enfrentar **{monstro['emoji']} {monstro['nome']}**!\n\nEscolha onde a batalha vai acontecer:",
        color=0x7F77DD
    )
    embed_arena.set_footer(text="30s para selecionar automaticamente")
    msg_arena = await interaction.followup.send(embed=embed_arena, view=view_arena, wait=True)
    await view_arena.wait()
    
    arena = view_arena.arena or random.choice(ARENAS)
    embed_escolhida = discord.Embed(
        title=f"{arena['emoji']} {arena['nome']}",
        description=f"Bônus: {arena['bonus']}\n\nPreparando batalha...",
        color=arena["cor"]
    )
    if arena.get("img"):
        embed_escolhida.set_image(url=arena["img"])
    try:
        await msg_arena.edit(embed=embed_escolhida, view=None)
    except:
        pass
    await asyncio.sleep(1)
    
    try:
        await rodar_treino(interaction, p, monstro, arena)
    except Exception as e:
        import traceback
        print(f"ERRO rodar_treino: {e}")
        traceback.print_exc()
        BATALHAS_ATIVAS.discard(interaction.user.id)
        try:
            await interaction.followup.send("❌ Ocorreu um erro na batalha. Tente novamente!", ephemeral=True)
        except:
            pass
    finally:
        await incrementar_treino_uso(interaction.user.id)


# ==================================================
# COMANDO DESAFIAR
# ==================================================

async def cmd_desafiar(interaction: discord.Interaction, jogador: discord.Member):
    await interaction.response.defer()
    
    if em_batalha(interaction.user.id):
        await interaction.followup.send("Você já está em batalha!", ephemeral=True)
        return
    
    if jogador.bot or jogador.id == interaction.user.id:
        await interaction.followup.send("Jogador inválido!", ephemeral=True)
        return
    
    p1 = await get_personagem(interaction.user.id)
    p2 = await get_personagem(jogador.id)
    
    if not p1:
        await interaction.followup.send("Você não tem personagem!", ephemeral=True)
        return
    if not p2:
        await interaction.followup.send(f"{jogador.display_name} não tem personagem!", ephemeral=True)
        return
    
    view = AceitarDueloView(interaction.user.id, jogador.id)
    embed = discord.Embed(
        title="⚔️ Desafio de Duelo!",
        description=f"{interaction.user.mention} desafia {jogador.mention}!\nVocê aceita?",
        color=0xE4AF3C
    )
    msg_d = await interaction.followup.send(embed=embed, view=view, wait=True)
    await view.wait()
    
    if not view.resposta:
        await msg_d.edit(embed=discord.Embed(title="❌ Desafio recusado!", color=0x888780), view=None)
        return
    
    arena = random.choice(ARENAS)
    await msg_d.edit(embed=discord.Embed(title=f"⚔️ Duelo! {arena['emoji']} {arena['nome']}", color=0x1D9E75), view=None)
    await rodar_pvp(interaction.channel, p1, p2, interaction.user, jogador, arena)


# ==================================================
# COMANDO TREINAR DUPLA
# ==================================================

async def cmd_treinar_dupla(interaction: discord.Interaction, parceiro: discord.Member):
    await interaction.response.defer()
    
    if em_batalha(interaction.user.id) or em_batalha(parceiro.id):
        await interaction.followup.send("Um dos jogadores já está em batalha!", ephemeral=True)
        return
    
    if parceiro.bot or parceiro.id == interaction.user.id:
        await interaction.followup.send("Jogador inválido!", ephemeral=True)
        return
    
    p1 = await get_personagem(interaction.user.id)
    p2 = await get_personagem(parceiro.id)
    
    if not p1 or not p2:
        await interaction.followup.send("Um dos jogadores não tem personagem!", ephemeral=True)
        return
    
    class AceitarDuplaView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)
            self.aceito = False
        
        @discord.ui.button(label="✅ Aceitar", style=discord.ButtonStyle.success)
        async def aceitar(self, inter: discord.Interaction, button):
            if inter.user.id != parceiro.id:
                await inter.response.send_message("Não é você!", ephemeral=True)
                return
            self.aceito = True
            await inter.response.defer()
            self.stop()
        
        @discord.ui.button(label="❌ Recusar", style=discord.ButtonStyle.danger)
        async def recusar(self, inter: discord.Interaction, button):
            if inter.user.id != parceiro.id:
                await inter.response.send_message("Não é você!", ephemeral=True)
                return
            self.aceito = False
            await inter.response.defer()
            self.stop()
    
    embed_convite = discord.Embed(
        title="⚔️ Convite para Batalha em Dupla!",
        description=f"**{interaction.user.display_name}** convidou **{parceiro.display_name}** para batalharem juntos!\n\n"
                   f"**Bônus:** +20% XP e Moedas!\n"
                   f"**Monstro:** HP dobrado!\n\n"
                   f"⏱️ Você tem 60 segundos para aceitar!",
        color=0x7F77DD
    )
    
    view = AceitarDuplaView()
    await interaction.followup.send(content=parceiro.mention, embed=embed_convite, view=view)
    await view.wait()
    
    if not view.aceito:
        await interaction.edit_original_response(content="❌ Convite recusado ou expirado!", embed=None, view=None)
        return
    
    dificuldade = "facil" if p1["nivel"] < 10 else "medio" if p1["nivel"] < 20 else "dificil" if p1["nivel"] < 35 else "lendario"
    monstros_d = [m for m in MONSTROS if m["dificuldade"] == dificuldade]
    monstro = random.choice(monstros_d)
    arena = random.choice(ARENAS)
    
    await interaction.edit_original_response(
        embed=discord.Embed(
            title=f"⚔️ Batalha em Dupla!",
            description=f"{interaction.user.mention} + {parceiro.mention} vs **{monstro['emoji']} {monstro['nome']}**\n"
                       f"🏟️ Arena: {arena['emoji']} {arena['nome']}\n\n"
                       f"**Monstro com HP dobrado!**\n"
                       f"**+20% de recompensa!**",
            color=arena["cor"]
        ),
        view=None
    )
    
    await rodar_treino_dupla(interaction, p1, p2, monstro, arena, interaction.user, parceiro)


# ==================================================
# REGISTRO DOS COMANDOS
# ==================================================

def setup_combate_commands(bot):
    @bot.tree.command(name="treinar", description="Batalhe contra monstros para ganhar XP")
    @app_commands.describe(dificuldade="Escolha a dificuldade")
    @app_commands.choices(dificuldade=[
        app_commands.Choice(name="Fácil", value="facil"),
        app_commands.Choice(name="Médio", value="medio"),
        app_commands.Choice(name="Difícil", value="dificil"),
        app_commands.Choice(name="Lendário", value="lendario"),
    ])
    async def treinar(interaction: discord.Interaction, dificuldade: str = "facil"):
        await cmd_treinar(interaction, dificuldade)
    
    @bot.tree.command(name="desafiar", description="Desafia outro jogador para um duelo PvP")
    @app_commands.describe(jogador="Jogador a desafiar")
    async def desafiar(interaction: discord.Interaction, jogador: discord.Member):
        await cmd_desafiar(interaction, jogador)
    
    @bot.tree.command(name="treinar-dupla", description="Batalhe em dupla contra um monstro (+20% recompensa)")
    @app_commands.describe(parceiro="Jogador para lutar ao seu lado")
    async def treinar_dupla(interaction: discord.Interaction, parceiro: discord.Member):
        await cmd_treinar_dupla(interaction, parceiro)