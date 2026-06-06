# catalogo.py — Sistema de ranks, níveis e cálculos de mana

from constants import RANKS, RANK_EMOJIS, RANK_CORES, RANK_BONUS
from data_classes import MANA_CLASSE, MANA_DESTINO


# ==================================================
# RANKS E NÍVEIS
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


def get_rank(nivel: int) -> dict:
    """Retorna o objeto rank baseado no nível do jogador"""
    for r in reversed(RANKS_NIVEL):
        if nivel >= r["nivel_min"]:
            return r
    return RANKS_NIVEL[0]


def get_rank_by_name(rank_name: str) -> dict:
    """Retorna o objeto rank pelo nome do rank (F, E, D, etc.)"""
    for r in RANKS_NIVEL:
        if r["rank"] == rank_name.upper():
            return r
    return RANKS_NIVEL[0]


def get_rank_emoji(nivel: int) -> str:
    """Retorna o emoji do rank baseado no nível"""
    return get_rank(nivel)["emoji"]


def get_rank_cor(nivel: int) -> int:
    """Retorna a cor do rank baseado no nível"""
    return get_rank(nivel)["cor"]


# ==================================================
# CÁLCULO DE MANA MÁXIMA
# ==================================================

def calcular_mana_max(classe_id: str, nivel: int, poder_valor: int, destino_id: str) -> int:
    """
    Calcula a mana máxima do personagem baseado em:
    - Classe (base e multiplicador por nível)
    - Poder (bônus percentual)
    - Destino (multiplicador final)
    """
    # Dados da classe
    dados_classe = MANA_CLASSE.get(classe_id, MANA_CLASSE["mago"])
    mana_base = dados_classe["base"]
    mult_nivel = dados_classe["mult_nivel"]
    mult_poder = dados_classe["mult_poder"]
    
    # Cálculo base: mana_base + (nível * mult_nivel) + (poder_valor * mult_poder)
    mana_calculada = mana_base + (nivel * mult_nivel) + int(poder_valor * mult_poder)
    
    # Multiplicador do destino
    mult_destino = MANA_DESTINO.get(destino_id, 1.0)
    mana_final = int(mana_calculada * mult_destino)
    
    return max(mana_final, 50)  # Mínimo 50 de mana


# ==================================================
# FUNÇÕES DE UTILIDADE
# ==================================================

def calcular_xp_para_proximo_nivel(nivel_atual: int) -> int:
    """Calcula o XP necessário para o próximo nível"""
    return 100 + (nivel_atual - 1) * 50


def calcular_nivel_por_xp(xp_total: int) -> int:
    """Calcula o nível baseado no XP total acumulado"""
    nivel = 1
    xp_restante = xp_total
    
    while True:
        xp_necessario = 100 + (nivel - 1) * 50
        if xp_restante < xp_necessario:
            break
        xp_restante -= xp_necessario
        nivel += 1
    
    return nivel


def get_bonus_por_rank(rank: str) -> dict:
    """Retorna os bônus de um rank específico"""
    return RANK_BONUS.get(rank, {"hp": 0, "mana": 0, "atk": 0, "dfs": 0})