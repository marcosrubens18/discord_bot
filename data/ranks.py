# data/ranks.py — Ranks, bônus e níveis

# ==================================================
# RANKS POR NÍVEL (F a SS)
# ==================================================

RANKS_NIVEL = [
    {"rank": "F",  "nivel_min": 1,  "nivel_max": 9,   "emoji": "🟫", "cor": 0x888780, "nome": "Rank F  — Recruta"},
    {"rank": "E",  "nivel_min": 10, "nivel_max": 19,  "emoji": "🟩", "cor": 0x1D9E75, "nome": "Rank E  — Aprendiz"},
    {"rank": "D",  "nivel_min": 20, "nivel_max": 29,  "emoji": "🟦", "cor": 0x378ADD, "nome": "Rank D  — Guerreiro"},
    {"rank": "C",  "nivel_min": 30, "nivel_max": 39,  "emoji": "🟨", "cor": 0xE4AF3C, "nome": "Rank C  — Veterano"},
    {"rank": "B",  "nivel_min": 40, "nivel_max": 49,  "emoji": "🟧", "cor": 0xD85A30, "nome": "Rank B  — Elite"},
    {"rank": "A",  "nivel_min": 50, "nivel_max": 59,  "emoji": "🟥", "cor": 0xE24B4A, "nome": "Rank A  — Mestre"},
    {"rank": "S",  "nivel_min": 60, "nivel_max": 74,  "emoji": "⭐", "cor": 0x7F77DD, "nome": "Rank S  — Lendario"},
    {"rank": "SS", "nivel_min": 75, "nivel_max": 100, "emoji": "💎", "cor": 0xD85A30, "nome": "Rank SS — Transcendente"},
]

CARGOS_RANK = {
    "F":  "🟫 Rank F",
    "E":  "🟩 Rank E",
    "D":  "🟦 Rank D",
    "C":  "🟨 Rank C",
    "B":  "🟧 Rank B",
    "A":  "🟥 Rank A",
    "S":  "⭐ Rank S",
    "SS": "💎 Rank SS",
}

# ==================================================
# BÔNUS POR RANK
# ==================================================

RANK_BONUS = {
    "E": {"hp": 35, "mana": 20, "atk": 8, "dfs": 5},
    "D": {"hp": 60, "mana": 35, "atk": 15, "dfs": 9},
    "C": {"hp": 100, "mana": 55, "atk": 25, "dfs": 15},
    "B": {"hp": 150, "mana": 80, "atk": 40, "dfs": 22},
    "A": {"hp": 220, "mana": 120, "atk": 60, "dfs": 35},
    "S": {"hp": 320, "mana": 180, "atk": 90, "dfs": 50},
    "SS": {"hp": 480, "mana": 260, "atk": 130, "dfs": 75},
}

# ==================================================
# FUNÇÕES AUXILIARES
# ==================================================

def get_rank(nivel):
    for r in reversed(RANKS_NIVEL):
        if nivel >= r["nivel_min"]:
            return r
    return RANKS_NIVEL[0]    
