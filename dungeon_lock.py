# dungeon_lock.py — Sistema de lock para dungeons e batalhas
from asyncio import Lock
from typing import Dict

class DungeonLockManager:
    """Gerencia locks para evitar conflitos em dungeons e batalhas"""
    
    def __init__(self):
        self.user_locks: Dict[int, Lock] = {}
        self.dungeon_locks: Dict[int, Lock] = {}
    
    def get_user_lock(self, user_id: int) -> Lock:
        """Retorna o lock de um usuário específico"""
        if user_id not in self.user_locks:
            self.user_locks[user_id] = Lock()
        return self.user_locks[user_id]
    
    def get_dungeon_lock(self, dungeon_id: int) -> Lock:
        """Retorna o lock de uma dungeon específica"""
        if dungeon_id not in self.dungeon_locks:
            self.dungeon_locks[dungeon_id] = Lock()
        return self.dungeon_locks[dungeon_id]
    
    def release_user(self, user_id: int) -> None:
        """Libera o lock de um usuário"""
        if user_id in self.user_locks:
            del self.user_locks[user_id]
    
    def release_dungeon(self, dungeon_id: int) -> None:
        """Libera o lock de uma dungeon"""
        if dungeon_id in self.dungeon_locks:
            del self.dungeon_locks[dungeon_id]
    
    def is_user_locked(self, user_id: int) -> bool:
        """Verifica se um usuário está em dungeon/batalha"""
        lock = self.user_locks.get(user_id)
        return lock is not None and lock.locked()
    
    def is_dungeon_locked(self, dungeon_id: int) -> bool:
        """Verifica se uma dungeon está em uso"""
        lock = self.dungeon_locks.get(dungeon_id)
        return lock is not None and lock.locked()


# Instância global
dungeon_lock = DungeonLockManager()