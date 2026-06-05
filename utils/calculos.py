# utils/calculos.py — Fórmulas matemáticas do jogo

import random
from data.classes import MANA_CLASSE, MANA_DESTINO

# ==================================================
# CÁLCULO DE DANO
# ==================================================

def calc_dano(atk, dfs, mult=1.0, crit=False, bonus_atk=1.0, ignorar_defesa=False, nivel=1, hp_max_monstro=None, passiva_mult=1.0):
    """Calcula o dano de um ataque"""
    if nivel <= 9:
        div_forca = 1.1
        mult_cap = 1.15
    elif nivel <= 19:
        div_forca = 0.95
        mult_cap = 1.35
    elif nivel <= 29:
        div_forca = 0.85
        mult_cap = 1.55
    elif nivel <= 39:
        div_forca = 0.78
        mult_cap = 1.70
    elif nivel <= 49:
        div_forca = 0.72
        mult_cap = 1.80
    elif nivel <= 59:
        div_forca = 0.67
        mult_cap = 1.80
    elif nivel <= 74:
        div_forca = 0.62
        mult_cap = 1.80
    else:
        div_forca = 0.58
        mult_cap = 1.80

    mult_real = min(mult_cap, mult)
    dano_minimo = max(12, int(atk * 0.20))

    if ignorar_defesa:
        base = int((atk / div_forca) * mult_real)
    else:
        atk_efetivo = max(1, atk - int(dfs * 0.35))
        base = int((atk_efetivo / div_forca) * mult_real)

    base = max(dano_minimo, base)

    variacao = random.randint(-max(1, base // 10), max(1, base // 10))
    dano = max(dano_minimo, base + variacao)

    dano = int(dano * min(bonus_atk, 1.15))

    if crit:
        dano = int(dano * 1.30)

    if hp_max_monstro:
        cap = max(dano_minimo, int(hp_max_monstro * 0.35))
        dano = min(cap, dano)

    return max(dano_minimo, dano)


# ==================================================
# CÁLCULO DE MANA
# ==================================================

def calcular_mana_max(classe_id, nivel, poder_valor, destino_id):
    """Calcula a mana máxima do personagem"""
    cfg = MANA_CLASSE.get(classe_id, {"base": 100, "mult_nivel": 10, "mult_poder": 0.4})
    base = cfg["base"] + (nivel - 1) * cfg["mult_nivel"] + poder_valor * cfg["mult_poder"]
    mult = MANA_DESTINO.get(destino_id, 1.0)
    return max(100, int(base * mult))


# ==================================================
# BARRA DE HP
# ==================================================

def barra_hp(cur, mx):
    """Retorna uma barra de HP visual"""
    if mx <= 0:
        return "░░░░░░░░░░"
    p = max(0.0, cur / mx)
    f = int(p * 10)
    char = "█" if p > 0.6 else ("▓" if p > 0.3 else "▒")
    return char * f + "░" * (10 - f)


# ==================================================
# CÁLCULO DE STATS
# ==================================================

def calcular_stats(poder_valor, destino_id, nivel=1):
    """Calcula HP, ATK e DEF base do personagem"""
    hp = 90 + poder_valor * 2 + nivel * 6
    atk = 9 + poder_valor // 5 + nivel * 2
    dfs = 6 + poder_valor // 7 + nivel * 1
    
    if destino_id == "prodigio":
        atk = int(atk * 1.12)
        dfs = int(dfs * 0.95)
    elif destino_id == "guardiao":
        dfs = int(dfs * 1.12)
        atk = int(atk * 0.95)
    elif destino_id == "abencado":
        hp = int(hp * 1.08)
        atk = int(atk * 1.05)
        dfs = int(dfs * 1.05)
    elif destino_id == "maldito":
        atk = int(atk * 0.85)
        dfs = int(dfs * 0.85)
    elif destino_id == "amaldicoado":
        atk = random.randint(5, atk + 5)
        dfs = random.randint(3, dfs + 3)
    
    return hp, atk, dfs