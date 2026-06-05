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