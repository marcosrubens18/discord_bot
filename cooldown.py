# cooldown.py — Sistema de rate limiting e cooldown
from datetime import datetime, timedelta
from collections import defaultdict

class CooldownManager:
    """Gerencia cooldowns de comandos por usuário"""
    
    def __init__(self):
        self.cooldowns = defaultdict(dict)
    
    def check(self, user_id: int, comando: str, segundos: int = 5) -> tuple:
        """
        Verifica se o comando está em cooldown.
        Retorna (pode_usar, segundos_restantes)
        """
        key = f"{user_id}_{comando}"
        now = datetime.utcnow()
        
        if key in self.cooldowns:
            if now < self.cooldowns[key]:
                restante = int((self.cooldowns[key] - now).total_seconds())
                return False, restante
        return True, 0
    
    def set(self, user_id: int, comando: str, segundos: int = 5) -> None:
        """Aplica cooldown para o comando"""
        key = f"{user_id}_{comando}"
        self.cooldowns[key] = datetime.utcnow() + timedelta(seconds=segundos)
    
    def clear(self, user_id: int, comando: str = None) -> None:
        """Limpa cooldown (útil para admin)"""
        if comando:
            key = f"{user_id}_{comando}"
            self.cooldowns.pop(key, None)
        else:
            self.cooldowns.pop(user_id, None)
    
    def get_remaining(self, user_id: int, comando: str) -> int:
        """Retorna segundos restantes de cooldown (0 se não houver)"""
        key = f"{user_id}_{comando}"
        now = datetime.utcnow()
        
        if key in self.cooldowns and now < self.cooldowns[key]:
            return int((self.cooldowns[key] - now).total_seconds())
        return 0


# Instância global
cooldown_manager = CooldownManager()


# ==================================================
# DECORATOR PARA COOLDOWN EM COMANDOS
# ==================================================

def cooldown(segundos: int = 5):
    """Decorator para aplicar cooldown em comandos"""
    def decorator(func):
        async def wrapper(interaction, *args, **kwargs):
            pode, tempo = cooldown_manager.check(interaction.user.id, func.__name__, segundos)
            if not pode:
                await interaction.response.send_message(
                    f"⏰ Aguarde **{tempo} segundos** antes de usar este comando novamente!",
                    ephemeral=True
                )
                return
            result = await func(interaction, *args, **kwargs)
            cooldown_manager.set(interaction.user.id, func.__name__, segundos)
            return result
        return wrapper
    return decorator