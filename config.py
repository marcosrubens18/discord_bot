# config.py — Configurações centralizadas do bot

import os

# ==================================================
# DISCORD
# ==================================================

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
GUILD_ID = int(os.getenv("GUILD_ID", "0"))
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

# ==================================================
# DATABASE
# ==================================================

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/railway")

# ==================================================
# IMAGENS (URLs)
# ==================================================

IMG_PERFIL = ""
IMG_SETUP = ""
IMG_INVENTARIO = ""
IMG_SKILLS = ""
IMG_AJUDA = ""
IMG_LOJA = ""
IMG_FERREIRO = ""
IMG_HOSPITAL = ""
IMG_MERCADO = ""
IMG_MERCADOR = ""
IMG_MISSOES = ""
IMG_RANKING = ""
IMG_CONQUISTAS = ""
IMG_ROLETA = ""
IMG_BANNER_GERAL = ""
IMG_VITORIA = ""
IMG_DERROTA = ""
IMG_LEVEL_UP = ""

IMG_DUNGEON = {
    "F": "", "E": "", "D": "", "C": "", "B": "", "A": "", "S": "", "SS": ""
}

IMG_DUNGEON_MONSTRO = {
    "Goblin": "",
    "Lobo Selvagem": "",
    "Esqueleto": "",
    "Orc Guerreiro": "",
    "Vampiro": "",
    "Lich": "",
    "Titan": "",
    "Dragao Anciao": "",
    "default": "",
}

IMG_ARENA = {
    "floresta": "https://i.imgur.com/NptFGtk.png",
    "vulcao": "https://i.imgur.com/XO8L8R1.png",
    "gelo": "https://i.imgur.com/fWdV7mI.png",
    "ruinas": "https://i.imgur.com/HYnPxMN.png",
    "coloseu": "https://i.imgur.com/vcVWqyk.png",
}

MAX_PARTY_MEMBROS = 5
MAX_PARTY_NIVEL = 10
MAX_GUILDA_MEMBROS = 20
COOLDOWN_BATALHA = 5
COOLDOWN_TREINO = 5
COOLDOWN_DUNGEON = 10
TEMPO_CONVITE_PARTY = 300
TEMPO_LUTA_TORNEIO = 300
DESAFIOS_POR_DIA = 10

COR_PRIMARY = 0x7F77DD
COR_SUCCESS = 0x1D9E75
COR_DANGER = 0xE24B4A
COR_WARNING = 0xE4AF3C
COR_INFO = 0x378ADD
COR_DARK = 0x888780
COR_GOLD = 0xD85A30
