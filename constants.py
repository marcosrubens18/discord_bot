# constants.py — Constantes centralizadas do Villa Eldoria RPG

# ==================================================
# CORES
# ==================================================

COR_PRIMARY = 0x7F77DD      # Roxo - principal
COR_SUCCESS = 0x1D9E75      # Verde - sucesso
COR_DANGER = 0xE24B4A       # Vermelho - perigo
COR_WARNING = 0xE4AF3C      # Amarelo - aviso
COR_INFO = 0x378ADD         # Azul - informativo
COR_DARK = 0x888780         # Cinza - neutro
COR_GOLD = 0xD85A30         # Laranja - destaque

# ==================================================
# EMOJIS POR CLASSE
# ==================================================

EMOJI_CLASSE = {
    "guerreiro": "🗡️",
    "mago": "🔮",
    "arqueiro": "🏹",
    "paladino": "⚡",
    "necromante": "🌑",
    "dracomante": "🐉",
    "arcano": "✨",
}

# ==================================================
# RANKS
# ==================================================

RANKS = ["F", "E", "D", "C", "B", "A", "S", "SS"]

RANK_CORES = {
    "F": 0x888780,
    "E": 0x1D9E75,
    "D": 0x378ADD,
    "C": 0xE4AF3C,
    "B": 0xD85A30,
    "A": 0xE24B4A,
    "S": 0x7F77DD,
    "SS": 0xD85A30,
}

RANK_EMOJIS = {
    "F": "🟫",
    "E": "🟩",
    "D": "🟦",
    "C": "🟨",
    "B": "🟧",
    "A": "🟥",
    "S": "⭐",
    "SS": "💎",
}

# ==================================================
# LIMITES DO SISTEMA
# ==================================================

MAX_PARTY_MEMBROS = 5
MAX_PARTY_NIVEL = 10
MAX_GUILDA_MEMBROS = 20
COOLDOWN_BATALHA = 5          # segundos
COOLDOWN_TREINO = 5           # segundos
COOLDOWN_DUNGEON = 10         # segundos
TEMPO_CONVITE_PARTY = 300     # 5 minutos
TEMPO_LUTA_TORNEIO = 300      # 5 minutos

# ==================================================
# BÔNUS POR MEMBROS DA PARTY
# ==================================================

BONUS_POR_MEMBROS = {
    2: {"xp": 5, "moedas": 0, "loot": 0},
    3: {"xp": 10, "moedas": 5, "loot": 0},
    4: {"xp": 15, "moedas": 10, "loot": 5},
    5: {"xp": 20, "moedas": 15, "loot": 10},
}

# ==================================================
# NÍVEIS DA PARTY
# ==================================================

PARTY_NIVEIS = {
    1: {"xp_needed": 0, "bonus_xp": 0, "bonus_moedas": 0, "max_membros": 5, "titulo": "Recruta", "cor": COR_DARK},
    2: {"xp_needed": 500, "bonus_xp": 2, "bonus_moedas": 0, "max_membros": 5, "titulo": "Grupo", "cor": COR_INFO},
    3: {"xp_needed": 1500, "bonus_xp": 4, "bonus_moedas": 2, "max_membros": 6, "titulo": "Esquadrão", "cor": COR_INFO},
    4: {"xp_needed": 3500, "bonus_xp": 6, "bonus_moedas": 4, "max_membros": 6, "titulo": "Companhia", "cor": COR_WARNING},            
    5: {"xp_needed": 7000, "bonus_xp": 8, "bonus_moedas": 6, "max_membros": 7, "titulo": "Batalhão", "cor": COR_WARNING},
    6: {"xp_needed": 12000, "bonus_xp": 10, "bonus_moedas": 8, "max_membros": 7, "titulo": "Regimento", "cor": COR_GOLD},
    7: {"xp_needed": 18000, "bonus_xp": 12, "bonus_moedas": 10, "max_membros": 8, "titulo": "Legião", "cor": COR_GOLD},
    8: {"xp_needed": 25000, "bonus_xp": 15, "bonus_moedas": 12, "max_membros": 8, "titulo": "Exército", "cor": COR_SUCCESS},
    9: {"xp_needed": 35000, "bonus_xp": 18, "bonus_moedas": 15, "max_membros": 9, "titulo": "Irmandade", "cor": COR_SUCCESS},
    10: {"xp_needed": 50000, "bonus_xp": 20, "bonus_moedas": 20, "max_membros": 10, "titulo": "Lenda", "cor": COR_PRIMARY},
}

def get_party_bonus(nivel: int) -> dict:
    """Retorna o bônus da party baseado no nível"""
    return PARTY_NIVEIS.get(nivel, PARTY_NIVEIS[1])

def get_bonus_por_membros(qtd: int) -> dict:
    """Retorna o bônus baseado no número de membros"""
    return BONUS_POR_MEMBROS.get(min(qtd, 5), BONUS_POR_MEMBROS[2])
