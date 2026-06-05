# data/racas.py — Dados de todas as raças

RACAS = {
    "humano": {
        "id": "humano", "nome": "Humano", "emoji": "👤",
        "raridade": "Comum", "peso": 0,
        "desc": "Versáteis e determinados.",
        "passiva_desc": "+10% XP e +5% moedas",
        "bonus_xp": 0.10,
        "bonus_moedas": 0.05,
        "cor": 0x888780,
        "cargos": "👤 Humano",
    },
    "anao": {
        "id": "anao", "nome": "Anão", "emoji": "🧔",
        "raridade": "Comum", "peso": 0,
        "desc": "Resistentes como pedra.",
        "passiva_desc": "+5 DEF, 50% resist atordoar",
        "bonus_def": 5,
        "resist_atordoar": 0.50,
        "cor": 0xD85A30,
        "cargos": "🧔 Anão",
    },
    "elfo": {
        "id": "elfo", "nome": "Elfo", "emoji": "👂",
        "raridade": "Comum", "peso": 0,
        "desc": "Ágeis e mágicos.",
        "passiva_desc": "+20 mana, +15% crítico",
        "bonus_mana": 20,
        "bonus_crit": 0.15,
        "cor": 0x1D9E75,
        "cargos": "👂 Elfo",
    },
    "licantropo": {
        "id": "licantropo", "nome": "Licantropo", "emoji": "🐺",
        "raridade": "Incomum", "peso": 8,
        "desc": "Amaldiçoado entre homem e fera.",
        "passiva_desc": "HP<60%: transforma (+30% ATK, imune veneno)",
        "cor": 0x2ecc71,
        "cargos": "🐺 Licantropo",
    },
    "elfo_floresta": {
        "id": "elfo_floresta", "nome": "Elfo da Floresta", "emoji": "🌿",
        "raridade": "Incomum", "peso": 7,
        "desc": "Em harmonia com a natureza.",
        "passiva_desc": "Regenera 4% HP por turno",
        "cor": 0x27ae60,
        "cargos": "🌿 Elfo da Floresta",
    },
    "gigante_gelo": {
        "id": "gigante_gelo", "nome": "Gigante do Gelo", "emoji": "🧊",
        "raridade": "Raro", "peso": 5,
        "desc": "Civilização das montanhas do norte.",
        "passiva_desc": "35% chance de congelar",
        "cor": 0x3498db,
        "cargos": "🧊 Gigante do Gelo",
    },
    "djinn": {
        "id": "djinn", "nome": "Djinn", "emoji": "🧞",
        "raridade": "Raro", "peso": 4,
        "desc": "Espírito elemental do deserto.",
        "passiva_desc": "Skills ignoram 20% defesa",
        "cor": 0x9b59b6,
        "cargos": "🧞 Djinn",
    },
    "morto_vivo": {
        "id": "morto_vivo", "nome": "Morto-Vivo", "emoji": "🧟",
        "raridade": "Epico", "peso": 3,
        "desc": "Entre a vida e a morte.",
        "passiva_desc": "Imune veneno/congelar/queimadura. Ataques drenam 6% HP",
        "cor": 0x7F77DD,
        "cargos": "🧟 Morto-Vivo",
    },
    "elfo_sombrio": {
        "id": "elfo_sombrio", "nome": "Elfo Sombrio", "emoji": "🧝",
        "raridade": "Epico", "peso": 2,
        "desc": "Banidos para as cavernas.",
        "passiva_desc": "30% chance de contra-atacar",
        "cor": 0x6c3483,
        "cargos": "🧝 Elfo Sombrio",
    },
    "draconiano": {
        "id": "draconiano", "nome": "Draconiano", "emoji": "🐉",
        "raridade": "Epico", "peso": 1,
        "desc": "Descendentes de dragões.",
        "passiva_desc": "-12% dano, imune queimadura, +10% dano fogo",
        "cor": 0xE67E22,
        "cargos": "🐉 Draconiano",
    },
    "anjo": {
        "id": "anjo", "nome": "Anjo", "emoji": "😇",
        "raridade": "Lendario", "peso": 1,
        "desc": "Ser celestial descendido.",
        "passiva_desc": "Ressuscita 1x, escudo a cada 5 turnos",
        "cor": 0xF1C40F,
        "cargos": "😇 Anjo",
    },
    "demonio": {
        "id": "demonio", "nome": "Demônio", "emoji": "😈",
        "raridade": "Lendario", "peso": 1,
        "desc": "Ser das profundezas infernais.",
        "passiva_desc": "Primeiros 10 turnos: +5% dano/turno (max 50%)",
        "cor": 0xC0392B,
        "cargos": "😈 Demônio",
    },
}

RACAS_BASICAS = ["humano", "anao", "elfo"]
RACAS_ROLETA = [r for r in RACAS.values() if r["peso"] > 0]

def get_raca(raca_id):
    return RACAS.get(raca_id, RACAS["humano"])