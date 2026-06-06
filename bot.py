# bot.py — Entry point principal do Villa Eldoria RPG

import discord
from discord import app_commands
from discord.ext import commands
import os
import asyncio

from config import DISCORD_TOKEN, GUILD_ID
from database.db import init_db
from database.queries import get_personagem

# Importar inicializadores de sistemas
from systems.arena import init_db_arena
from systems.social.party import init_db_party
from systems.social.guildas import init_db_guildas
from systems.sorteio import init_db_sorteios, reagendar_sorteios_pendentes, finalizar_e_anunciar_sorteio
from systems.dungeon_evento import init_db_dungeon_evento
from systems.passe import init_db_passe
from systems.eventos import init_db_eventos

# Importar comandos
from commands.admin import setup_admin_commands
from commands.jogador import setup_jogador_commands
from commands.combate import setup_combate_commands
from commands.dungeon import setup_dungeon_commands
from commands.economia import setup_economia_commands
from commands.social import setup_social_commands
from commands.competitivo import setup_competitivo_commands
from commands.progresso import setup_progresso_commands
from commands.roleta import setup_roleta_commands
from commands.sorteio import setup_sorteio_commands
from commands.hospital import setup_hospital_commands
from commands.tutorial import setup_tutorial_commands
from commands.setup_cmd import setup_setup_command  # ou a função que registra o comando

# Importar eventos
from core.events import setup_events

# ==================================================
# CONFIGURAÇÃO DO BOT
# ==================================================

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


# ==================================================
# INICIALIZAÇÃO
# ==================================================

@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")
    print(f"📊 Comandos registrados: {len(bot.tree.get_commands()):,}")
    
    # Inicializar bancos de dados
    await init_db()
    await init_db_arena()
    await init_db_party()
    await init_db_guildas()
    await init_db_sorteios()
    await init_db_dungeon_evento()
    await init_db_passe()
    await init_db_eventos()
    print("✅ Bancos de dados inicializados")
    
    # Reagendar sorteios pendentes
    expirados = await reagendar_sorteios_pendentes()
    for sid in expirados:
        asyncio.create_task(finalizar_e_anunciar_sorteio(sid, bot.get_guild(GUILD_ID)))
    print(f"✅ {len(expirados)} sorteios reagendados")
    
    # Iniciar agendador de reset de missões
    try:
        from systems.missoes import iniciar_agendador_reset
        await iniciar_agendador_reset(bot)
        print("✅ Agendador de reset de missões iniciado")
    except Exception as e:
        print(f"⚠️ Erro ao iniciar agendador de missões: {e}")
    
    # Sincronizar comandos
    try:
        if GUILD_ID:
            guild = discord.Object(id=GUILD_ID)
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
            print(f"✅ {len(synced)} comandos sincronizados no servidor")
        else:
            synced = await bot.tree.sync()
            print(f"✅ {len(synced)} comandos sincronizados globalmente")
    except Exception as e:
        print(f"❌ Erro ao sincronizar comandos: {e}")


# ==================================================
# SETUP DOS COMANDOS
# ==================================================

setup_admin_commands(bot)
setup_jogador_commands(bot)
setup_combate_commands(bot)
setup_dungeon_commands(bot)
setup_economia_commands(bot)
setup_social_commands(bot)
setup_competitivo_commands(bot)
setup_progresso_commands(bot)
setup_roleta_commands(bot)
setup_sorteio_commands(bot)
setup_hospital_commands(bot)
setup_tutorial_commands(bot)
setup_setup_command(bot)
setup_events(bot)


# ==================================================
# COMANDO SYNC MANUAL
# ==================================================

@bot.command(name="sync")
@commands.is_owner()
async def sync_cmd(ctx):
    """Sincroniza comandos manualmente (apenas dono)"""
    try:
        if GUILD_ID:
            guild = discord.Object(id=GUILD_ID)
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
            await ctx.send(f"✅ {len(synced)} comandos sincronizados no servidor")
        else:
            synced = await bot.tree.sync()
            await ctx.send(f"✅ {len(synced)} comandos sincronizados globalmente")
    except Exception as e:
        await ctx.send(f"❌ Erro: {e}")


# ==================================================
# MAIN
# ==================================================

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("❌ Token do Discord não encontrado!")
        exit(1)
    
    bot.run(DISCORD_TOKEN)
