# utils/cooldown.py — Sistema de rate limiting e cooldown

from datetime import datetime, timedelta, timezone
from collections import defaultdict
from asyncio import Lock

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
    
    def cleanup_old(self, max_age_seconds: int = 3600):
        """Remove entradas antigas para evitar memory leak"""
        now = datetime.now(timezone.utc)
        keys_to_remove = [
            k for k, v in self.cooldowns.items()
            if (now - v).total_seconds() > max_age_seconds
        ]
        for k in keys_to_remove:
            self.cooldowns.pop(k, None)


# Instância global
cooldown_manager = CooldownManager()