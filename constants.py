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

# ==================================================
# FUNÇÕES AUXILIARES DE PARTY
# ==================================================

def get_party_bonus(nivel: int) -> dict:
    """Retorna o bônus da party baseado no nível"""
    return PARTY_NIVEIS.get(nivel, PARTY_NIVEIS[1])

def get_bonus_por_membros(qtd: int) -> dict:
    """Retorna o bônus baseado no número de membros"""
    return BONUS_POR_MEMBROS.get(min(qtd, 5), BONUS_POR_MEMBROS[2])

# ==================================================
# PLANOS DO HOSPITAL
# ==================================================

PLANOS_HOSPITAL = [
    {"id": "basico",   "nome": "Atendimento Basico",  "emoji": "🩹", "preco": 10, "hp_pct": 0.5, "mana_pct": 0.5, "desc": "Restaura 50% do HP e Mana", "cor": 0x1D9E75},
    {"id": "completo", "nome": "Tratamento Completo", "emoji": "🏥", "preco": 30, "hp_pct": 1.0, "mana_pct": 1.0, "desc": "Restaura 100% do HP e Mana", "cor": 0x378ADD},
    {"id": "premium",  "nome": "Suite Premium",       "emoji": "✨", "preco": 50, "hp_pct": 1.0, "mana_pct": 1.0, "desc": "HP + Mana full + remove todos os efeitos negativos", "cor": 0x7F77DD},
]

# ==================================================
# ARENAS
# ==================================================

ARENAS = [
    {"id": "floresta", "nome": "Floresta Sombria", "emoji": "🌲", "bonus": "magia +15%", "cor": 0x1D9E75,
     "img": "https://i.imgur.com/5Q2xXkN.png"},
    {"id": "vulcao", "nome": "Cratera Vulcanica", "emoji": "🌋", "bonus": "fogo +20%", "cor": 0xD85A30,
     "img": "https://i.imgur.com/6kqJv1R.png"},
    {"id": "gelo", "nome": "Pico de Gelo", "emoji": "❄️", "bonus": "def +10%", "cor": 0x378ADD,
     "img": "https://i.imgur.com/3nQpLmZ.png"},
    {"id": "ruinas", "nome": "Ruinas Arcanas", "emoji": "🏚️", "bonus": "crit +10%", "cor": 0x7F77DD,
     "img": "https://i.imgur.com/8PqWrTz.png"},
    {"id": "coloseu", "nome": "Coloseu Real", "emoji": "🏟️", "bonus": "neutro", "cor": 0xE4AF3C,
     "img": "https://i.imgur.com/2LmNxKp.png"},
]

# ==================================================
# ELOS DA ARENA
# ==================================================

ELOS = {
    "Ferro": {"rating_min": 0, "rating_max": 499, "emoji": "🟫", "cor": 0x888780, "perde": 15, "ganha": 25, "bonus_mensal": 100},
    "Bronze": {"rating_min": 500, "rating_max": 999, "emoji": "🥉", "cor": 0xCD7F32, "perde": 18, "ganha": 22, "bonus_mensal": 200},
    "Prata": {"rating_min": 1000, "rating_max": 1499, "emoji": "🥈", "cor": 0xC0C0C0, "perde": 20, "ganha": 20, "bonus_mensal": 300},
    "Ouro": {"rating_min": 1500, "rating_max": 1999, "emoji": "🥇", "cor": 0xFFD700, "perde": 22, "ganha": 18, "bonus_mensal": 500},
    "Platina": {"rating_min": 2000, "rating_max": 2499, "emoji": "💎", "cor": 0xE5E4E2, "perde": 25, "ganha": 15, "bonus_mensal": 800},
    "Diamante": {"rating_min": 2500, "rating_max": 2999, "emoji": "💎", "cor": 0x4A90E2, "perde": 28, "ganha": 12, "bonus_mensal": 1200},
    "Mestre": {"rating_min": 3000, "rating_max": 999999, "emoji": "⭐", "cor": 0x7F77DD, "perde": 30, "ganha": 10, "bonus_mensal": 2000},
}

# ==================================================
# TIPOS DE EVENTO E PRÊMIO
# ==================================================

TIPOS_EVENTO = {
    "batalha":    {"nome": "Torneio de Batalha",   "emoji": "⚔️",  "desc": "Quem tiver mais vitorias ganha"},
    "dungeon":    {"nome": "Corrida de Dungeon",   "emoji": "🏰",  "desc": "Quem completar dungeon mais alto ganha"},
    "coleta":     {"nome": "Coleta de Materiais",  "emoji": "📦",  "desc": "Quem coletar mais materiais ganha"},
    "nivel":      {"nome": "Corrida de Nivel",     "emoji": "📈",  "desc": "Quem subir mais niveis ganha"},
    "livre":      {"nome": "Evento Livre",         "emoji": "🎉",  "desc": "Criterio definido pelo admin"},
}

TIPOS_PREMIO = {
    "moedas":   {"nome": "Moedas",          "emoji": "🪙", "desc": "Moedas para o inventario"},
    "xp":       {"nome": "XP",              "emoji": "⭐", "desc": "Experiencia de batalha"},
    "item":     {"nome": "Item especifico", "emoji": "📦", "desc": "Um item do catalogo"},
    "ficha":    {"nome": "Fichas de roleta", "emoji": "🎰", "desc": "Fichas para girar"},
    "cargo":    {"nome": "Cargo exclusivo", "emoji": "🎖️", "desc": "Cargo especial no servidor"},
    "classe":   {"nome": "Classe especial", "emoji": "⚡", "desc": "Muda classe do vencedor"},
}

# ==================================================
# RARIDADES
# ==================================================

RARIDADES = ["Comum", "Incomum", "Raro", "Epico", "Lendario"]

EMOJI_FICHA = {"Comum": "🟫", "Incomum": "🟩", "Raro": "🟦", "Epico": "🟪", "Lendario": "🟧"}

COR_RAR = {
    "Comum": 0x888780,
    "Incomum": 0x1D9E75,
    "Raro": 0x378ADD,
    "Epico": 0x7F77DD,
    "Lendario": 0xD85A30,
}