# utils/decorators.py — Decoradores para comandos

import discord
from functools import wraps
from utils.cooldown import cooldown_manager

# ==================================================
# PERMISSÕES
# ==================================================

def admin_only():
    """Decorator para comandos que só admin pode usar"""
    def decorator(func):
        @wraps(func)
        async def wrapper(interaction: discord.Interaction, *args, **kwargs):
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message(
                    "❌ Apenas administradores podem usar este comando!",
                    ephemeral=True
                )
                return
            return await func(interaction, *args, **kwargs)
        return wrapper
    return decorator


def owner_only(owner_id: int):
    """Decorator para comandos que só o dono do bot pode usar"""
    def decorator(func):
        @wraps(func)
        async def wrapper(interaction: discord.Interaction, *args, **kwargs):
            if interaction.user.id != owner_id:
                await interaction.response.send_message(
                    "❌ Apenas o dono do bot pode usar este comando!",
                    ephemeral=True
                )
                return
            return await func(interaction, *args, **kwargs)
        return wrapper
    return decorator


# ==================================================
# COOLDOWN
# ==================================================

def cooldown(segundos: int = 5):
    """Decorator para aplicar cooldown em comandos"""
    def decorator(func):
        @wraps(func)
        async def wrapper(interaction: discord.Interaction, *args, **kwargs):
            pode, tempo = await cooldown_manager.acquire(interaction.user.id, func.__name__, segundos)
            if not pode:
                try:
                    await interaction.response.send_message(
                        f"⏰ Aguarde **{tempo} segundos** antes de usar este comando novamente!",
                        ephemeral=True
                    )
                except:
                    try:
                        await interaction.followup.send(
                            f"⏰ Aguarde **{tempo} segundos** antes de usar este comando novamente!",
                            ephemeral=True
                        )
                    except:
                        pass
                return
            return await func(interaction, *args, **kwargs)
        return wrapper
    return decorator


# ==================================================
# BATTLE CHECK
# ==================================================

def em_batalha_guard():
    """Decorator para verificar se o jogador não está em batalha"""
    def decorator(func):
        @wraps(func)
        async def wrapper(interaction: discord.Interaction, *args, **kwargs):
            from systems.combate import BATALHAS_ATIVAS
            if interaction.user.id in BATALHAS_ATIVAS:
                await interaction.response.send_message(
                    "❌ Você já está em batalha! Termine primeiro.",
                    ephemeral=True
                )
                return
            return await func(interaction, *args, **kwargs)
        return wrapper
    return decorator


# ==================================================
# EXISTE PERSONAGEM
# ==================================================

def personagem_existe():
    """Decorator para verificar se o jogador tem personagem"""
    def decorator(func):
        @wraps(func)
        async def wrapper(interaction: discord.Interaction, *args, **kwargs):
            from database.queries import get_personagem
            p = await get_personagem(interaction.user.id)
            if not p:
                await interaction.response.send_message(
                    "❌ Crie seu personagem primeiro usando `/criar_personagem`!",
                    ephemeral=True
                )
                return
            return await func(interaction, p, *args, **kwargs)
        return wrapper
    return decorator