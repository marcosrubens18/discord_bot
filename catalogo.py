# catalogo.py — Catalogo completo com preços balanceados

# ─── RANKS F → SS ────────────────────────────────────────────────

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

def get_rank(nivel):
    for r in reversed(RANKS_NIVEL):
        if nivel >= r["nivel_min"]:
            return r
    return RANKS_NIVEL[0]

# ─── MANA BASE POR CLASSE ────────────────────────────────────────

MANA_CLASSE = {
    "guerreiro":  {"base": 100, "mult_nivel": 10, "mult_poder": 0.3},
    "arqueiro":   {"base": 105, "mult_nivel": 11, "mult_poder": 0.3},
    "mago":       {"base": 120, "mult_nivel": 15, "mult_poder": 0.6},
    "paladino":   {"base": 110, "mult_nivel": 12, "mult_poder": 0.4},
    "necromante": {"base": 115, "mult_nivel": 13, "mult_poder": 0.5},
    "dracomante": {"base": 105, "mult_nivel": 11, "mult_poder": 0.4},
    "arcano":     {"base": 125, "mult_nivel": 16, "mult_poder": 0.7},
}

MANA_DESTINO = {
    "equilibrado":  1.00,
    "prodigio":     0.85,
    "maldito":      0.70,
    "guardiao":     1.10,
    "abencado":     1.15,
    "amaldicoado":  1.00,
    "filho_caos":   1.20,
}

def calcular_mana_max(classe_id, nivel, poder_valor, destino_id):
    cfg = MANA_CLASSE.get(classe_id, {"base": 100, "mult_nivel": 10, "mult_poder": 0.4})
    base = cfg["base"] + (nivel - 1) * cfg["mult_nivel"] + poder_valor * cfg["mult_poder"]
    mult = MANA_DESTINO.get(destino_id, 1.0)
    return max(100, int(base * mult))

# ─── ARMAS POR CLASSE (PREÇOS BALANCEADOS) ───────────────────────

ARMAS_POR_CLASSE = {
    "guerreiro": [
        {"id":"espada_ferro",    "nome":"Espada de Ferro",    "emoji":"⚔️","raridade":"Comum",    "atk_bonus":5,  "preco":50,   "venda":25,  "desc":"Arma inicial. Confiavel e resistente."},
        {"id":"machado_pesado",  "nome":"Machado Pesado",     "emoji":"🪓","raridade":"Comum",    "atk_bonus":8,  "preco":120,  "venda":60,  "desc":"Machado de ferro. Dano bruto alto."},
        {"id":"espada_prata",    "nome":"Espada de Prata",    "emoji":"⚔️","raridade":"Incomum",  "atk_bonus":12, "preco":300,  "venda":150, "desc":"Forjada em prata pura. ATK +12."},
        {"id":"lanca_combate",   "nome":"Lanca de Combate",   "emoji":"🔱","raridade":"Incomum",  "atk_bonus":10, "preco":280,  "venda":140, "desc":"Alcance extra. Bom para contra-ataques."},
        {"id":"espada_cavaleiro","nome":"Espada do Cavaleiro", "emoji":"⚔️","raridade":"Raro",    "atk_bonus":18, "preco":700,  "venda":350, "desc":"Espada nobre de cavaleiro veterano."},
        {"id":"martelo_guerra",  "nome":"Martelo de Guerra",  "emoji":"🔨","raridade":"Raro",    "atk_bonus":16, "preco":650,  "venda":325, "desc":"15% de chance de atordoar o inimigo."},
        {"id":"espada_orc",      "nome":"Espada Orc",         "emoji":"🗡️","raridade":"Raro",    "atk_bonus":20, "preco":1500, "venda":750, "desc":"Forjada com metal orc. Brutalidade pura."},
        {"id":"lanca_sagrada",   "nome":"Lanca Sagrada",      "emoji":"🔱","raridade":"Epico",   "atk_bonus":25, "preco":2500, "venda":1250,"desc":"Abencada pelos deuses. Sagrado +20."},
        {"id":"espada_sombria",  "nome":"Espada Sombria",     "emoji":"🗡️","raridade":"Epico",   "atk_bonus":28, "preco":4000, "venda":2000,"desc":"Forjada nas trevas. Drena HP ao acertar."},
        {"id":"espada_lendaria", "nome":"Espada do Heroi",    "emoji":"⚔️","raridade":"Lendario","atk_bonus":40, "preco":10000,"venda":5000,"desc":"Arma dos grandes herois. Apenas em dungeons."},
    ],
    "arqueiro": [
        {"id":"arco_madeira",    "nome":"Arco de Madeira",    "emoji":"🏹","raridade":"Comum",    "atk_bonus":4,  "preco":50,   "venda":25,  "desc":"Arco inicial. Leve e preciso."},
        {"id":"besta_leve",      "nome":"Besta Leve",         "emoji":"🏹","raridade":"Comum",    "atk_bonus":6,  "preco":100,  "venda":50,  "desc":"Besta de disparo rapido."},
        {"id":"arco_composto",   "nome":"Arco Composto",      "emoji":"🏹","raridade":"Incomum",  "atk_bonus":10, "preco":260,  "venda":130, "desc":"Mais potente que o arco basico."},
        {"id":"besta_pesada",    "nome":"Besta Pesada",       "emoji":"🏹","raridade":"Incomum",  "atk_bonus":12, "preco":290,  "venda":145, "desc":"Dano perfurante. Ignora 10% da defesa."},
        {"id":"arco_elfico",     "nome":"Arco Elfico",        "emoji":"🏹","raridade":"Raro",    "atk_bonus":15, "preco":550,  "venda":275, "desc":"Critico +15%. Obra dos elfos da floresta."},
        {"id":"arco_sombras",    "nome":"Arco das Sombras",   "emoji":"🏹","raridade":"Raro",    "atk_bonus":18, "preco":700,  "venda":350, "desc":"Flechas envenenadas automaticamente."},
        {"id":"arco_encantado",  "nome":"Arco Encantado",     "emoji":"🏹","raridade":"Raro",    "atk_bonus":20, "preco":800,  "venda":400, "desc":"Encantado com magia arcana. Critico +20%."},
        {"id":"besta_draconica", "nome":"Besta Draconica",    "emoji":"🏹","raridade":"Epico",   "atk_bonus":26, "preco":1300, "venda":650, "desc":"Feita com garras de dragao. Flechas de fogo."},
        {"id":"arco_celestial",  "nome":"Arco Celestial",     "emoji":"🏹","raridade":"Epico",   "atk_bonus":30, "preco":1600, "venda":800, "desc":"Arco sagrado dos anjos. Critico +30%."},
        {"id":"arco_lendario",   "nome":"Arco do Cacador",    "emoji":"🏹","raridade":"Lendario","atk_bonus":45, "preco":10000,"venda":5000,"desc":"Arco do maior cacador de todos os tempos."},
    ],
    "mago": [
        {"id":"cajado_pinho",    "nome":"Cajado de Pinho",    "emoji":"🪄","raridade":"Comum",    "atk_bonus":4,  "preco":50,   "venda":25,  "desc":"Cajado inicial. Canaliza energia basica."},
        {"id":"vara_magica",     "nome":"Vara Magica",        "emoji":"🪄","raridade":"Comum",    "atk_bonus":6,  "preco":90,   "venda":45,  "desc":"Vara de carvalho encantada. +5 mana."},
        {"id":"cajado_quartzo",  "nome":"Cajado de Quartzo",  "emoji":"🪄","raridade":"Incomum",  "atk_bonus":10, "preco":250,  "venda":125, "desc":"Cristal de quartzo amplifica magias."},
        {"id":"orbe_fogo",       "nome":"Orbe de Fogo",       "emoji":"🔮","raridade":"Incomum",  "atk_bonus":11, "preco":280,  "venda":140, "desc":"Orbe de fogo elementar. +10% dano de fogo."},
        {"id":"cajado_magico",   "nome":"Cajado Magico",      "emoji":"🪄","raridade":"Raro",    "atk_bonus":15, "preco":600,  "venda":300, "desc":"Amplifica todos os feiticos. Magia +10."},
        {"id":"tomo_arcano",     "nome":"Tomo Arcano",        "emoji":"📖","raridade":"Raro",    "atk_bonus":16, "preco":700,  "venda":350, "desc":"Tomo de feiticos antigos. +15% dano magico."},
        {"id":"cajado_osso2",    "nome":"Cajado Osseo+",      "emoji":"💀","raridade":"Raro",    "atk_bonus":17, "preco":800,  "venda":400, "desc":"Amplifica magia negra. Bom para necromante."},
        {"id":"cajado_vazio",    "nome":"Cajado do Vazio",    "emoji":"🪄","raridade":"Epico",   "atk_bonus":26, "preco":1400, "venda":700, "desc":"Canaliza energia do vazio. Ignora resistencias."},
        {"id":"orbe_arcano",     "nome":"Grande Orbe Arcano", "emoji":"🔮","raridade":"Epico",   "atk_bonus":30, "preco":1700, "venda":850, "desc":"Orbe de poder supremo. Magia +25."},
        {"id":"cajado_lendario", "nome":"Cajado do Arquimago","emoji":"🪄","raridade":"Lendario","atk_bonus":48, "preco":10000,"venda":5000,"desc":"Cajado do maior mago de todos os tempos."},
    ],
}

# Continuar com as outras classes com os mesmos padrões de preço...

# ─── POÇÕES (PREÇOS BALANCEADOS) ─────────────────────────────────

POCOES_CAT = [
    {"id":"pocao_hp_p", "nome":"Pocao de Cura P", "emoji":"🧪", "tipo":"pocao", "raridade":"Comum", "desc":"Recupera 30 HP", "preco":30, "venda":15, "valor":30},
    {"id":"pocao_hp_m", "nome":"Pocao de Cura M", "emoji":"💊", "tipo":"pocao", "raridade":"Comum", "desc":"Recupera 60 HP", "preco":60, "venda":30, "valor":60},
    {"id":"pocao_hp_g", "nome":"Pocao de Cura G", "emoji":"❤️", "tipo":"pocao", "raridade":"Raro", "desc":"Recupera 120 HP", "preco":120, "venda":60, "valor":120},
    {"id":"pocao_mana_p", "nome":"Pocao de Mana P", "emoji":"🔵", "tipo":"pocao", "raridade":"Comum", "desc":"Recupera 20 Mana", "preco":25, "venda":12, "valor":20},
    {"id":"pocao_mana_m", "nome":"Pocao de Mana M", "emoji":"💙", "tipo":"pocao", "raridade":"Incomum", "desc":"Recupera 50 Mana", "preco":55, "venda":27, "valor":50},
    {"id":"elixir", "nome":"Elixir Supremo", "emoji":"✨", "tipo":"pocao", "raridade":"Epico", "desc":"HP e Mana full", "preco":300, "venda":150, "valor":999},
]

MATERIAIS_CAT = [
    {"id":"pedra_suja","nome":"Pedra Suja","emoji":"🪨","tipo":"material","raridade":"Comum","desc":"Material basico","preco":0,"venda":5},
    {"id":"pele_lobo","nome":"Pele de Lobo","emoji":"🐾","tipo":"material","raridade":"Comum","desc":"Material comum","preco":0,"venda":10},
    {"id":"minerio_ferro","nome":"Minerio de Ferro","emoji":"⛏️","tipo":"material","raridade":"Comum","desc":"Metal bruto","preco":0,"venda":15},
    {"id":"osso_oco","nome":"Osso Oco","emoji":"💀","tipo":"material","raridade":"Incomum","desc":"Material necrotico","preco":0,"venda":25},
    {"id":"dente_orc","nome":"Dente de Orc","emoji":"🦷","tipo":"material","raridade":"Incomum","desc":"Ingrediente","preco":0,"venda":30},
    {"id":"fragmento_golem","nome":"Fragmento de Golem","emoji":"🪨","tipo":"material","raridade":"Raro","desc":"Material magico","preco":0,"venda":50},
    {"id":"sangue_anciao","nome":"Sangue Anciao","emoji":"🩸","tipo":"material","raridade":"Raro","desc":"Ingrediente raro","preco":0,"venda":75},
    {"id":"escama_dragao_p","nome":"Escama de Dragao","emoji":"🐉","tipo":"material","raridade":"Raro","desc":"Fragmento de escama","preco":0,"venda":100},
    {"id":"olho_dragao","nome":"Olho de Dragao","emoji":"👁️","tipo":"material","raridade":"Epico","desc":"Material epico","preco":0,"venda":200},
    {"id":"essencia_lich","nome":"Essencia do Lich","emoji":"💀","tipo":"material","raridade":"Lendario","desc":"Material sombrio","preco":0,"venda":500},
    {"id":"fragmento_titan","nome":"Fragmento do Titan","emoji":"🗿","tipo":"material","raridade":"Lendario","desc":"Lendario","preco":0,"venda":1000},
]

# Funções auxiliares
def get_armas_classe(classe_id):
    return ARMAS_POR_CLASSE.get(classe_id, [])

def get_armaduras_classe(classe_id):
    return ARMADURAS_POR_CLASSE.get(classe_id, [])

def get_catalogo_completo():
    todos = []
    for cls, armas in ARMAS_POR_CLASSE.items():
        for a in armas:
            todos.append({
                "chave": f"arma:{cls}:{a['id']}",
                "id": a["id"], "nome": a["nome"],
                "emoji": a.get("emoji","⚔️"), "tipo": "arma",
                "raridade": a["raridade"], "classe": cls,
                "desc": a.get("desc",""), "preco": a.get("preco",0), "venda": a.get("venda",0)
            })
    for cls, arms in ARMADURAS_POR_CLASSE.items():
        for a in arms:
            todos.append({
                "chave": f"armadura:{cls}:{a['id']}",
                "id": a["id"], "nome": a["nome"],
                "emoji": a.get("emoji","🛡️"), "tipo": "armadura",
                "raridade": a["raridade"], "classe": cls,
                "desc": a.get("desc",""), "preco": a.get("preco",0), "venda": a.get("venda",0)
            })
    for p in POCOES_CAT:
        todos.append({**p, "chave": f"pocao::{p['id']}", "classe": "", "preco": p["preco"], "venda": p["venda"]})
    for m in MATERIAIS_CAT:
        todos.append({**m, "chave": f"material::{m['id']}", "classe": "", "preco": m.get("preco",0), "venda": m.get("venda",0)})
    return todos

def get_item_por_chave(chave: str):
    for it in get_catalogo_completo():
        if it["chave"] == chave:
            return it
    return None
