# data_classes.py — Classes, Poderes e Destinos

# ==================================================
# CLASSES
# ==================================================

CLASSES = [
    {"id": "guerreiro", "nome": "Guerreiro", "emoji": "🗡️", "raridade": "Comum", "peso": 30, "desc": "Combate corpo a corpo. Alta defesa."},
    {"id": "arqueiro", "nome": "Arqueiro", "emoji": "🏹", "raridade": "Comum", "peso": 25, "desc": "Precisao e criticos frequentes."},
    {"id": "mago", "nome": "Mago", "emoji": "🔮", "raridade": "Comum", "peso": 20, "desc": "Dano magico crescente por turno."},
    {"id": "paladino", "nome": "Paladino", "emoji": "⚡", "raridade": "Incomum", "peso": 12, "desc": "Hibrido: cura e combate."},
    {"id": "necromante", "nome": "Necromante", "emoji": "🌑", "raridade": "Raro", "peso": 8, "desc": "Drena vida dos inimigos."},
    {"id": "dracomante", "nome": "Dracomante", "emoji": "🐉", "raridade": "Lendario", "peso": 2, "desc": "Sangue de dragao. Resistencia maxima."},
    {"id": "arcano", "nome": "Arcano", "emoji": "✨", "raridade": "Epico", "peso": 3, "desc": "Dano arcano que ignora defesa."},
]

# ==================================================
# PODERES BASE
# ==================================================

PODERES = [
    {"id": "fraquinho", "nome": "Fraquinho", "emoji": "💀", "valor": 10},
    {"id": "mediano", "nome": "Mediano", "emoji": "⚖️", "valor": 18},
    {"id": "acima", "nome": "Acima da media", "emoji": "📈", "valor": 26},
    {"id": "forte", "nome": "Forte", "emoji": "💪", "valor": 35},
    {"id": "epico", "nome": "Epico", "emoji": "⚡", "valor": 48},
    {"id": "absurdo", "nome": "Absurdo", "emoji": "🔥", "valor": 65},
]

PESOS_PODER = [20, 30, 25, 15, 7, 3]

# ==================================================
# DESTINOS
# ==================================================

DESTINOS = [
    {"id": "equilibrado", "nome": "Equilibrado", "emoji": "⚖️"},
    {"id": "prodigio", "nome": "Prodigio", "emoji": "🔥"},
    {"id": "maldito", "nome": "Maldito", "emoji": "💀"},
    {"id": "guardiao", "nome": "Guardiao", "emoji": "🛡️"},
    {"id": "abencado", "nome": "Abencado", "emoji": "🌟"},
    {"id": "amaldicoado", "nome": "Amaldicoado", "emoji": "☠️"},
    {"id": "filho_caos", "nome": "Filho do Caos", "emoji": "🌀"},
]

# ==================================================
# MANA POR CLASSE
# ==================================================

MANA_CLASSE = {
    "guerreiro": {"base": 105, "mult_nivel": 10, "mult_poder": 0.3},
    "arqueiro": {"base": 105, "mult_nivel": 11, "mult_poder": 0.3},
    "mago": {"base": 120, "mult_nivel": 15, "mult_poder": 0.6},
    "paladino": {"base": 110, "mult_nivel": 12, "mult_poder": 0.4},
    "necromante": {"base": 115, "mult_nivel": 13, "mult_poder": 0.5},
    "dracomante": {"base": 115, "mult_nivel": 11, "mult_poder": 0.4},
    "arcano": {"base": 125, "mult_nivel": 16, "mult_poder": 0.7},
}

MANA_DESTINO = {
    "equilibrado": 1.00,
    "prodigio": 0.85,
    "maldito": 0.70,
    "guardiao": 1.10,
    "abencado": 1.15,
    "amaldicoado": 1.00,
    "filho_caos": 1.20,
}