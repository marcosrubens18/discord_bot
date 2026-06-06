# -*- coding: utf-8 -*-
# bot.py — Entry point principal do Villa Eldoria RPG

import sys
import io
import os
import asyncio

# Força encoding UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

import discord
from discord import app_commands
from discord.ext import commands

from db import init_db

# Importar inicializadores de sistemas
from sistema_arena import init_db_arena
from sistema_party import init_db_party
from sistema_guildas import init_db_guildas
from sistema_sorteio import init_db_sorteios, reagendar_sorteios_pendentes, finalizar_e_anunciar_sorteio
from sistema_dungeon_evento import init_db_dungeon_evento
from sistema_passe import init_db_passe, register_passe_commands
from sistema_eventos import init_db_eventos
from sistema_roleta import init_db_hospital
from sistema_missoes import iniciar_agendador_reset
from sistema_conquistas import init_conquistas
from sistema_torneio import init_db_torneio

# Importar registros de comandos
from cmd_personagem import setup_personagem_commands
from cmd_inventario import setup_inventario_commands
from cmd_combate import setup_combate_commands
from cmd_dungeon import setup_dungeon_commands
from cmd_economia import setup_economia_commands
from cmd_social import setup_social_commands
from cmd_progresso import setup_progresso_commands
from cmd_roleta import setup_roleta_commands
from cmd_hospital import setup_hospital_commands
from cmd_arena import setup_arena_commands
from cmd_torneio import setup_torneio_commands
from cmd_sorteio import setup_sorteio_commands
from cmd_evento import setup_evento_commands
from cmd_admin import setup_admin_commands
from cmd_tutorial import setup_tutorial_commands

# Importar eventos
from core_events import setup_events

# Importar constantes para config
from constants import COR_PRIMARY
from config import DISCORD_TOKEN, GUILD_ID


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
    try:
        await init_db()
        await init_db_arena()
        await init_db_party()
        await init_db_guildas()
        await init_db_sorteios()
        await init_db_dungeon_evento()
        await init_db_passe()
        await init_db_eventos()
        await init_db_hospital()
        await init_conquistas()
        await init_db_torneio()
        print("✅ Bancos de dados inicializados")
    except Exception as e:
        print(f"❌ ERRO ao inicializar bancos de dados: {e}")
    
    # Reagendar sorteios pendentes
    try:
        expirados = await reagendar_sorteios_pendentes()
        for sid in expirados:
            asyncio.create_task(finalizar_e_anunciar_sorteio(sid, bot.get_guild(GUILD_ID)))
        print(f"✅ {len(expirados)} sorteios reagendados")
    except Exception as e:
        print(f"⚠️ Erro ao reagendar sorteios: {e}")
    
    # Iniciar agendador de reset de missões
    try:
        await iniciar_agendador_reset(bot)
        print("✅ Agendador de reset de missões iniciado")
    except Exception as e:
        print(f"⚠️ Erro ao iniciar agendador de missões: {e}")
    
    # Sincronizar comandos
    try:
        if GUILD_ID and GUILD_ID != 0:
            guild = discord.Object(id=GUILD_ID)
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
            print(f"✅ {len(synced)} comandos sincronizados no servidor")
        else:
            synced = await bot.tree.sync()
            print(f"✅ {len(synced)} comandos sincronizados globalmente")
    except Exception as e:
        print(f"❌ Erro ao sincronizar comandos: {e}")
    
    print("🎉 Bot pronto para uso!")


# ==================================================
# SETUP DOS COMANDOS
# ==================================================

setup_personagem_commands(bot)
setup_inventario_commands(bot)
setup_combate_commands(bot)
setup_dungeon_commands(bot)
setup_economia_commands(bot)
setup_social_commands(bot)
setup_progresso_commands(bot)
setup_roleta_commands(bot)
setup_hospital_commands(bot)
setup_arena_commands(bot)
setup_torneio_commands(bot)
setup_sorteio_commands(bot)
setup_evento_commands(bot)
setup_admin_commands(bot)
setup_tutorial_commands(bot)

# Registrar eventos
setup_events(bot)


# ==================================================
# COMANDO SYNC MANUAL
# ==================================================

@bot.command(name="sync")
@commands.is_owner()
async def sync_cmd(ctx):
    """Sincroniza comandos manualmente (apenas dono)"""
    try:
        if GUILD_ID and GUILD_ID != 0:
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
        print("Configure a variável de ambiente DISCORD_TOKEN")
        exit(1)
    
    bot.run(DISCORD_TOKEN)