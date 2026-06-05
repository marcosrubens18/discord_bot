# utils/locks.py — Gerenciamento de locks para evitar race conditions

from asyncio import Lock
from typing import Dict

_user_locks: Dict[int, Lock] = {}


def get_user_lock(user_id: int) -> Lock:
    """Retorna um lock para o usuário (para operações atômicas)"""
    if user_id not in _user_locks:
        _user_locks[user_id] = Lock()
    return _user_locks[user_id]


def release_user_lock(user_id: int) -> None:
    """Libera o lock do usuário (opcional, para limpeza)"""
    if user_id in _user_locks:
        del _user_locks[user_id]


# ==================================================
# DUNGEON LOCK (para evitar corridas em dungeons)
# ==================================================

class DungeonLock:
    """Lock específico para dungeons, evitando que um jogador entre em duas dungeons simultâneas"""
    
    def __init__(self):
        self._locks: Dict[int, Lock] = {}
    
    def get_user_lock(self, user_id: int) -> Lock:
        if user_id not in self._locks:
            self._locks[user_id] = Lock()
        return self._locks[user_id]
    
    def is_user_locked(self, user_id: int) -> bool:
        """Verifica se o usuário está em uma dungeon (lock ocupado)"""
        lock = self._locks.get(user_id)
        if lock and lock.locked():
            return True
        return False
    
    def release_user_lock(self, user_id: int) -> None:
        if user_id in self._locks:
            del self._locks[user_id]


# Instância global
dungeon_lock = DungeonLock()
