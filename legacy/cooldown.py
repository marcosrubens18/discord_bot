# cooldown.py — Sistema de rate limiting e cooldown com locks para race conditions
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from asyncio import Lock
from typing import Callable, Any, Awaitable
import discord
from discord import app_commands

class CooldownManager:
    """Gerencia cooldowns de comandos por usuário com locks para evitar race conditions"""
    
    def __init__(self):
        self.cooldowns = {}
        self.locks = defaultdict(Lock)
    
    def check(self, user_id: int, comando: str, segundos: int = 5) -> tuple:
        """
        Verifica se o comando está em cooldown.
        Retorna (pode_usar, segundos_restantes)
        """
        key = f"{user_id}_{comando}"
        now = datetime.now(timezone.utc)
        
        if key in self.cooldowns:
            if now < self.cooldowns[key]:
                restante = int((self.cooldowns[key] - now).total_seconds())
                return False, restante
        return True, 0
    
    def set(self, user_id: int, comando: str, segundos: int = 5) -> None:
        """Aplica cooldown para o comando"""
        key = f"{user_id}_{comando}"
        self.cooldowns[key] = datetime.now(timezone.utc) + timedelta(seconds=segundos)
    
    def clear(self, user_id: int, comando: str = None) -> None:
        """Limpa cooldown (útil para admin)"""
        if comando:
            key = f"{user_id}_{comando}"
            self.cooldowns.pop(key, None)
        else:
            keys_to_remove = [k for k in self.cooldowns.keys() if k.startswith(f"{user_id}_")]
            for k in keys_to_remove:
                self.cooldowns.pop(k, None)
    
    def get_remaining(self, user_id: int, comando: str) -> int:
        """Retorna segundos restantes de cooldown (0 se não houver)"""
        key = f"{user_id}_{comando}"
        now = datetime.now(timezone.utc)
        
        if key in self.cooldowns and now < self.cooldowns[key]:
            return int((self.cooldowns[key] - now).total_seconds())
        return 0
    
    async def acquire(self, user_id: int, comando: str, segundos: int = 5) -> tuple:
        """
        Versão async que adquire lock e verifica cooldown atomicamente.
        Retorna (pode_usar, segundos_restantes)
        """
        lock_key = f"{user_id}_{comando}"
        async with self.locks[lock_key]:
            pode, tempo = self.check(user_id, comando, segundos)
            if pode:
                self.set(user_id, comando, segundos)
                return True, 0
            return False, tempo


# Instância global
cooldown_manager = CooldownManager()


# ==================================================
# DECORATOR PARA COOLDOWN EM COMANDOS (CORRIGIDO)
# ==================================================

def cooldown(segundos: int = 5):
    """
    Decorator para aplicar cooldown em comandos.
    Usa a versão async com lock para evitar race conditions.
    
    Exemplo:
        @bot.tree.command(name="treinar")
        @cooldown(5)
        async def treinar(interaction: discord.Interaction, dificuldade: str = "facil"):
            ...
    """
    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        async def wrapper(interaction: discord.Interaction, *args: Any, **kwargs: Any) -> Any:
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
        
        # Preserva os metadados da função original para o discord.py
        wrapper.__name__ = func.__name__
        wrapper.__annotations__ = func.__annotations__
        wrapper.__signature__ = getattr(func, '__signature__', None)
        
        return wrapper
    return decorator


# ==================================================
# DECORATOR PARA COOLDOWN POR JOGADOR (PvP)
# ==================================================

def player_cooldown(segundos: int = 5):
    """
    Decorator para cooldown que considera o jogador alvo também.
    Usado para comandos como /desafiar, para não floodar o mesmo jogador.
    """
    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        async def wrapper(interaction: discord.Interaction, *args: Any, **kwargs: Any) -> Any:
            user_id = interaction.user.id
            
            # Tenta extrair o jogador alvo dos argumentos
            target_id = None
            if args and hasattr(args[0], 'id'):
                target_id = args[0].id
            elif 'jogador' in kwargs and hasattr(kwargs['jogador'], 'id'):
                target_id = kwargs['jogador'].id
            
            # Chave única para o par (desafiante, desafiado)
            if target_id:
                key = f"pvp_{user_id}_{target_id}"
                lock_key = key
            else:
                key = f"{user_id}_{func.__name__}"
                lock_key = key
            
            async with cooldown_manager.locks[lock_key]:
                now = datetime.now(timezone.utc)
                if key in cooldown_manager.cooldowns:
                    if now < cooldown_manager.cooldowns[key]:
                        restante = int((cooldown_manager.cooldowns[key] - now).total_seconds())
                        try:
                            await interaction.response.send_message(
                                f"⏰ Aguarde **{restante} segundos** antes de desafiar este jogador novamente!",
                                ephemeral=True
                            )
                        except:
                            try:
                                await interaction.followup.send(
                                    f"⏰ Aguarde **{restante} segundos** antes de desafiar este jogador novamente!",
                                    ephemeral=True
                                )
                            except:
                                pass
                        return
                
                cooldown_manager.cooldowns[key] = now + timedelta(seconds=segundos)
                return await func(interaction, *args, **kwargs)
        
        # Preserva os metadados
        wrapper.__name__ = func.__name__
        wrapper.__annotations__ = func.__annotations__
        
        return wrapper
    return decorator


# ==================================================
# FUNÇÃO PARA LIMPAR COOLDOWN DE UM USUÁRIO (ADMIN)
# ==================================================

async def clear_user_cooldown(user_id: int, comando: str = None) -> None:
    """Limpa todos os cooldowns de um usuário (uso administrativo)"""
    cooldown_manager.clear(user_id, comando)
