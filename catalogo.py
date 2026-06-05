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

# ─── ARMAS POR CLASSE ─────────────────────────────────────────────

ARMAS_POR_CLASSE = {
    "guerreiro": [
        {"id":"espada_ferro",    "nome":"Espada de Ferro",    "emoji":"⚔️","raridade":"Comum",    "atk_bonus":5,  "preco":50,   "venda":25,  "desc":"Arma inicial."},
        {"id":"machado_pesado",  "nome":"Machado Pesado",     "emoji":"🪓","raridade":"Comum",    "atk_bonus":8,  "preco":120,  "venda":60,  "desc":"Machado de ferro."},
        {"id":"espada_prata",    "nome":"Espada de Prata",    "emoji":"⚔️","raridade":"Incomum",  "atk_bonus":12, "preco":300,  "venda":150, "desc":"Forjada em prata."},
        {"id":"lanca_combate",   "nome":"Lanca de Combate",   "emoji":"🔱","raridade":"Incomum",  "atk_bonus":10, "preco":280,  "venda":140, "desc":"Alcance extra."},
        {"id":"espada_cavaleiro","nome":"Espada do Cavaleiro","emoji":"⚔️","raridade":"Raro",    "atk_bonus":18, "preco":700,  "venda":350, "desc":"Espada nobre."},
        {"id":"martelo_guerra",  "nome":"Martelo de Guerra",  "emoji":"🔨","raridade":"Raro",    "atk_bonus":16, "preco":650,  "venda":325, "desc":"15% chance atordoar."},
        {"id":"espada_orc",      "nome":"Espada Orc",         "emoji":"🗡️","raridade":"Raro",    "atk_bonus":20, "preco":1500, "venda":750, "desc":"Forjada com metal orc."},
        {"id":"lanca_sagrada",   "nome":"Lanca Sagrada",      "emoji":"🔱","raridade":"Epico",   "atk_bonus":25, "preco":2500, "venda":1250,"desc":"Abencada pelos deuses."},
        {"id":"espada_sombria",  "nome":"Espada Sombria",     "emoji":"🗡️","raridade":"Epico",   "atk_bonus":28, "preco":4000, "venda":2000,"desc":"Drena HP ao acertar."},
        {"id":"espada_lendaria", "nome":"Espada do Heroi",    "emoji":"⚔️","raridade":"Lendario","atk_bonus":40, "preco":10000,"venda":5000,"desc":"Arma lendaria."},
    ],
    "arqueiro": [
        {"id":"arco_madeira",    "nome":"Arco de Madeira",    "emoji":"🏹","raridade":"Comum",    "atk_bonus":4,  "preco":50,   "venda":25,  "desc":"Arco inicial."},
        {"id":"besta_leve",      "nome":"Besta Leve",         "emoji":"🏹","raridade":"Comum",    "atk_bonus":6,  "preco":100,  "venda":50,  "desc":"Besta rapida."},
        {"id":"arco_composto",   "nome":"Arco Composto",      "emoji":"🏹","raridade":"Incomum",  "atk_bonus":10, "preco":260,  "venda":130, "desc":"Arco potente."},
        {"id":"besta_pesada",    "nome":"Besta Pesada",       "emoji":"🏹","raridade":"Incomum",  "atk_bonus":12, "preco":290,  "venda":145, "desc":"Dano perfurante."},
        {"id":"arco_elfico",     "nome":"Arco Elfico",        "emoji":"🏹","raridade":"Raro",    "atk_bonus":15, "preco":550,  "venda":275, "desc":"Critico +15%."},
        {"id":"arco_sombras",    "nome":"Arco das Sombras",   "emoji":"🏹","raridade":"Raro",    "atk_bonus":18, "preco":700,  "venda":350, "desc":"Flechas envenenadas."},
        {"id":"arco_encantado",  "nome":"Arco Encantado",     "emoji":"🏹","raridade":"Raro",    "atk_bonus":20, "preco":800,  "venda":400, "desc":"Critico +20%."},
        {"id":"besta_draconica", "nome":"Besta Draconica",    "emoji":"🏹","raridade":"Epico",   "atk_bonus":26, "preco":1300, "venda":650, "desc":"Flechas de fogo."},
        {"id":"arco_celestial",  "nome":"Arco Celestial",     "emoji":"🏹","raridade":"Epico",   "atk_bonus":30, "preco":1600, "venda":800, "desc":"Critico +30%."},
        {"id":"arco_lendario",   "nome":"Arco do Cacador",    "emoji":"🏹","raridade":"Lendario","atk_bonus":45, "preco":10000,"venda":5000,"desc":"Arco lendario."},
    ],
    "mago": [
        {"id":"cajado_pinho",    "nome":"Cajado de Pinho",    "emoji":"🪄","raridade":"Comum",    "atk_bonus":4,  "preco":50,   "venda":25,  "desc":"Cajado inicial."},
        {"id":"vara_magica",     "nome":"Vara Magica",        "emoji":"🪄","raridade":"Comum",    "atk_bonus":6,  "preco":90,   "venda":45,  "desc":"+5 mana."},
        {"id":"cajado_quartzo",  "nome":"Cajado de Quartzo",  "emoji":"🪄","raridade":"Incomum",  "atk_bonus":10, "preco":250,  "venda":125, "desc":"Amplifica magias."},
        {"id":"orbe_fogo",       "nome":"Orbe de Fogo",       "emoji":"🔮","raridade":"Incomum",  "atk_bonus":11, "preco":280,  "venda":140, "desc":"+10% dano fogo."},
        {"id":"cajado_magico",   "nome":"Cajado Magico",      "emoji":"🪄","raridade":"Raro",    "atk_bonus":15, "preco":600,  "venda":300, "desc":"Magia +10."},
        {"id":"tomo_arcano",     "nome":"Tomo Arcano",        "emoji":"📖","raridade":"Raro",    "atk_bonus":16, "preco":700,  "venda":350, "desc":"+15% dano magico."},
        {"id":"cajado_osso2",    "nome":"Cajado Osseo+",      "emoji":"💀","raridade":"Raro",    "atk_bonus":17, "preco":800,  "venda":400, "desc":"Amplifica magia negra."},
        {"id":"cajado_vazio",    "nome":"Cajado do Vazio",    "emoji":"🪄","raridade":"Epico",   "atk_bonus":26, "preco":1400, "venda":700, "desc":"Ignora resistencias."},
        {"id":"orbe_arcano",     "nome":"Orbe Arcano",        "emoji":"🔮","raridade":"Epico",   "atk_bonus":30, "preco":1700, "venda":850, "desc":"Magia +25."},
        {"id":"cajado_lendario", "nome":"Cajado do Arquimago","emoji":"🪄","raridade":"Lendario","atk_bonus":48, "preco":10000,"venda":5000,"desc":"Cajado lendario."},
    ],
    "paladino": [
        {"id":"maca_sagrada",    "nome":"Maca Sagrada",      "emoji":"⚡","raridade":"Comum","atk_bonus":6,  "preco":50,  "venda":25,  "desc":"Maca abencada."},
        {"id":"escudo_espada",   "nome":"Espada e Escudo",   "emoji":"⚔️","raridade":"Comum","atk_bonus":5,  "preco":110, "venda":55,  "desc":"+5 DEF."},
        {"id":"lanca_prata",     "nome":"Lanca de Prata",    "emoji":"🔱","raridade":"Incomum","atk_bonus":11, "preco":270, "venda":135, "desc":"Efetiva vs trevas."},
        {"id":"espada_prata_p",  "nome":"Espada de Prata",   "emoji":"⚔️","raridade":"Incomum","atk_bonus":12, "preco":300, "venda":150, "desc":"Dano fisico e magico."},
        {"id":"maca_divina",     "nome":"Maca Divina",       "emoji":"⚡","raridade":"Raro","atk_bonus":17, "preco":680, "venda":340, "desc":"20% atordoar."},
        {"id":"espada_luz",      "nome":"Espada da Luz",     "emoji":"⚔️","raridade":"Raro","atk_bonus":19, "preco":750, "venda":375, "desc":"Sagrado +15."},
        {"id":"lanca_sagrada_p", "nome":"Lanca Sagrada",     "emoji":"🔱","raridade":"Raro","atk_bonus":20, "preco":800, "venda":400, "desc":"Lanca abencada."},
        {"id":"martelo_sagrado", "nome":"Martelo Sagrado",   "emoji":"🔨","raridade":"Epico","atk_bonus":27, "preco":1350,"venda":675, "desc":"+30 sagrado."},
        {"id":"espada_justica",  "nome":"Espada da Justica", "emoji":"⚔️","raridade":"Epico","atk_bonus":32, "preco":1800,"venda":900, "desc":"Espada divina."},
        {"id":"espada_cruzada",  "nome":"Espada da Cruzada", "emoji":"⚔️","raridade":"Lendario","atk_bonus":46, "preco":10000,"venda":5000,"desc":"Arma lendaria."},
    ],
    "necromante": [
        {"id":"cajado_osso",     "nome":"Cajado de Osso",    "emoji":"💀","raridade":"Comum","atk_bonus":4,  "preco":50,  "venda":25,  "desc":"Amplifica magia negra."},
        {"id":"foice_ferrugem",  "nome":"Foice Enferrujada","emoji":"⚰️","raridade":"Comum","atk_bonus":6,  "preco":95,  "venda":47,  "desc":"Sangramento."},
        {"id":"cajado_sombra",   "nome":"Cajado das Sombras","emoji":"💀","raridade":"Incomum","atk_bonus":10, "preco":240, "venda":120, "desc":"+10% dreno."},
        {"id":"foice_arcana",    "nome":"Foice Arcana",     "emoji":"⚰️","raridade":"Incomum","atk_bonus":12, "preco":280, "venda":140, "desc":"Drena vida."},
        {"id":"cajado_osso2_n",  "nome":"Cajado Osseo+",    "emoji":"💀","raridade":"Raro","atk_bonus":16, "preco":750, "venda":375, "desc":"Magia negra +20."},
        {"id":"corvo_espirito",  "nome":"Bastao do Corvo",  "emoji":"🦅","raridade":"Raro","atk_bonus":17, "preco":720, "venda":360, "desc":"Invoca corvos."},
        {"id":"cajado_lich",     "nome":"Cajado do Lich",   "emoji":"💀","raridade":"Raro","atk_bonus":19, "preco":800, "venda":400, "desc":"Poder sombrio."},
        {"id":"foice_morte",     "nome":"Foice da Morte",   "emoji":"⚰️","raridade":"Epico","atk_bonus":28, "preco":1400,"venda":700, "desc":"Dreno massivo."},
        {"id":"cetro_lich",      "nome":"Cetro do Lich",    "emoji":"💀","raridade":"Epico","atk_bonus":32, "preco":1600,"venda":800, "desc":"+30% dano necrotico."},
        {"id":"cajado_sombra_l", "nome":"Cajado das Trevas","emoji":"💀","raridade":"Lendario","atk_bonus":47, "preco":10000,"venda":5000,"desc":"Artefato das trevas."},
    ],
    "dracomante": [
        {"id":"garra_dragao",    "nome":"Garra de Dragao",   "emoji":"🐉","raridade":"Lendario","atk_bonus":35, "preco":8000, "venda":4000, "desc":"Arma lendaria de dragao."},
        {"id":"espada_dragao",   "nome":"Espada do Dragao",  "emoji":"⚔️","raridade":"Lendario","atk_bonus":38, "preco":9000, "venda":4500, "desc":"Flamejante eternamente."},
        {"id":"cajado_dragao",   "nome":"Cajado do Dragao",  "emoji":"🪄","raridade":"Lendario","atk_bonus":42, "preco":9500, "venda":4750, "desc":"Poder draconico."},
    ],
    "arcano": [
        {"id":"orbe_arcano",     "nome":"Orbe Arcano",       "emoji":"🔮","raridade":"Epico","atk_bonus":30, "preco":1700, "venda":850, "desc":"Magia +25."},
        {"id":"cajado_vazio",    "nome":"Cajado do Vazio",   "emoji":"🪄","raridade":"Epico","atk_bonus":26, "preco":1400, "venda":700, "desc":"Ignora resistencias."},
        {"id":"cajado_lendario", "nome":"Cajado do Arquimago","emoji":"🪄","raridade":"Lendario","atk_bonus":48, "preco":10000,"venda":5000,"desc":"Cajado lendario."},
    ],
}

# ─── ARMADURAS POR CLASSE ─────────────────────────────────────────

ARMADURAS_POR_CLASSE = {
    "guerreiro": [
        {"id":"armadura_couro",  "nome":"Armadura de Couro","emoji":"🥋","raridade":"Comum","def_bonus":5,  "preco":50,  "venda":25,  "desc":"Armadura inicial."},
        {"id":"cota_malha_g",    "nome":"Cota de Malha",    "emoji":"🛡️","raridade":"Comum","def_bonus":8,  "preco":150, "venda":75,  "desc":"Malha de ferro."},
        {"id":"armadura_ferro",  "nome":"Armadura de Ferro","emoji":"⚙️","raridade":"Incomum","def_bonus":13, "preco":350, "venda":175, "desc":"Armadura completa."},
        {"id":"escudo_torre",    "nome":"Escudo Torre",     "emoji":"🛡️","raridade":"Incomum","def_bonus":15, "preco":380, "venda":190, "desc":"Escudo gigante."},
        {"id":"armadura_plena",  "nome":"Armadura Plena",   "emoji":"⚙️","raridade":"Raro","def_bonus":20, "preco":900, "venda":450, "desc":"Cobertura total."},
        {"id":"cota_aco",        "nome":"Cota de Aco",      "emoji":"🛡️","raridade":"Raro","def_bonus":22, "preco":950, "venda":475, "desc":"Malha de aco."},
        {"id":"armadura_runa",   "nome":"Armadura Runada",  "emoji":"⚙️","raridade":"Raro","def_bonus":25, "preco":1100,"venda":550, "desc":"Runas de protecao."},
        {"id":"armadura_cavaleiro","nome":"Armadura do Cavaleiro","emoji":"⚙️","raridade":"Epico","def_bonus":32,"preco":1500,"venda":750,"desc":"Armadura lendaria."},
        {"id":"armadura_titan",  "nome":"Armadura do Titan","emoji":"🗿","raridade":"Epico","def_bonus":38, "preco":2500,"venda":1250,"desc":"+20% HP max."},
        {"id":"armadura_heroi",  "nome":"Armadura do Heroi","emoji":"⚙️","raridade":"Lendario","def_bonus":55, "preco":10000,"venda":5000,"desc":"Armadura definitiva."},
    ],
    "arqueiro": [
        {"id":"armadura_couro",  "nome":"Armadura de Couro","emoji":"🥋","raridade":"Comum","def_bonus":5,  "preco":50,  "venda":25,  "desc":"Armadura inicial."},
        {"id":"cota_malha_g",    "nome":"Cota de Malha",    "emoji":"🛡️","raridade":"Comum","def_bonus":8,  "preco":150, "venda":75,  "desc":"Malha de ferro."},
        {"id":"armadura_escamas","nome":"Armadura de Escamas","emoji":"🐉","raridade":"Raro","def_bonus":18, "preco":800, "venda":400, "desc":"Escamas leves."},
    ],
    "mago": [
        {"id":"armadura_couro",  "nome":"Armadura de Couro","emoji":"🥋","raridade":"Comum","def_bonus":5,  "preco":50,  "venda":25,  "desc":"Armadura inicial."},
        {"id":"manto_mago",      "nome":"Manto do Mago",    "emoji":"🧥","raridade":"Incomum","def_bonus":6,  "preco":200, "venda":100, "desc":"+10 mana."},
        {"id":"tunica_arcana",   "nome":"Tunica Arcana",    "emoji":"👘","raridade":"Raro","def_bonus":10, "preco":600, "venda":300, "desc":"+20 mana."},
    ],
    "paladino": [
        {"id":"armadura_plena",  "nome":"Armadura Plena",   "emoji":"⚙️","raridade":"Raro","def_bonus":20, "preco":900, "venda":450, "desc":"Cobertura total."},
        {"id":"armadura_escama", "nome":"Armadura de Escama","emoji":"🐉","raridade":"Epico","def_bonus":28, "preco":1800,"venda":900, "desc":"Escamas de dragao."},
        {"id":"armadura_titan",  "nome":"Armadura do Titan","emoji":"🗿","raridade":"Lendario","def_bonus":45, "preco":10000,"venda":5000,"desc":"Protecao maxima."},
    ],
    "necromante": [
        {"id":"armadura_couro",  "nome":"Armadura de Couro","emoji":"🥋","raridade":"Comum","def_bonus":5,  "preco":50,  "venda":25,  "desc":"Armadura inicial."},
        {"id":"capa_vampiro",    "nome":"Capa do Vampiro",  "emoji":"🧛","raridade":"Raro","def_bonus":12, "preco":700, "venda":350, "desc":"Drena 5% HP ao atacar."},
        {"id":"armadura_ossos",  "nome":"Armadura de Ossos","emoji":"💀","raridade":"Epico","def_bonus":20, "preco":1500,"venda":750, "desc":"Defesa osssea."},
    ],
    "dracomante": [
        {"id":"armadura_escama", "nome":"Armadura de Escama","emoji":"🐉","raridade":"Epico","def_bonus":28, "preco":1800,"venda":900, "desc":"Escamas de dragao."},
        {"id":"elmo_dragao",     "nome":"Elmo do Dragao",   "emoji":"🪖","raridade":"Lendario","def_bonus":35, "preco":5000,"venda":2500, "desc":"Protecao draconica."},
        {"id":"armadura_dragao", "nome":"Armadura do Dragao","emoji":"🐉","raridade":"Lendario","def_bonus":50, "preco":12000,"venda":6000, "desc":"Armadura definitiva."},
    ],
    "arcano": [
        {"id":"armadura_couro",  "nome":"Armadura de Couro","emoji":"🥋","raridade":"Comum","def_bonus":5,  "preco":50,  "venda":25,  "desc":"Armadura inicial."},
        {"id":"cota_malha_g",    "nome":"Cota de Malha",    "emoji":"🛡️","raridade":"Comum","def_bonus":8,  "preco":150, "venda":75,  "desc":"Malha de ferro."},
        {"id":"tunica_arcana",   "nome":"Tunica Arcana",    "emoji":"👘","raridade":"Raro","def_bonus":10, "preco":600, "venda":300, "desc":"+20 mana."},
    ],
}

# ─── POÇÕES E MATERIAIS ──────────────────────────────────────────

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

# ─── FUNÇÕES AUXILIARES (ESSENCIAIS PARA O BOT) ───────────────────

def get_armas_classe(classe_id):
    return ARMAS_POR_CLASSE.get(classe_id, [])

def get_armaduras_classe(classe_id):
    return ARMADURAS_POR_CLASSE.get(classe_id, [])

def get_ids_armas_classe(classe_id):
    return {a["id"] for a in ARMAS_POR_CLASSE.get(classe_id, [])}

def get_ids_armaduras_classe(classe_id):
    return {a["id"] for a in ARMADURAS_POR_CLASSE.get(classe_id, [])}

def get_skills_classe(classe_id):
    """Retorna skills da classe - importação segura sem circular"""
    from skills_sistema import SKILLS
    skills_da_classe = []
    for sid, skill in SKILLS.items():
        if skill.get("classe") == classe_id:
            skills_da_classe.append({
                "id": sid,
                "nome": skill["nome"],
                "nivel": skill["nivel"],
                "emoji": skill["emoji"],
                "mana": skill.get("mana", 0),
                "dano": skill.get("dano_mult", 1.0),
                "desc": skill.get("desc", ""),
                "efeito": skill.get("efeito"),
            })
    return sorted(skills_da_classe, key=lambda x: x["nivel"])

def get_skill_by_id(skill_id):
    """Retorna uma skill pelo ID - importação segura sem circular"""
    from skills_sistema import SKILLS
    skill = SKILLS.get(skill_id)
    if skill:
        return {
            "id": skill_id,
            "nome": skill["nome"],
            "classe": skill.get("classe", "suporte"),
            "nivel": skill["nivel"],
            "raridade": skill.get("raridade", "Comum"),
            "emoji": skill["emoji"],
            "mana": skill.get("mana", 0),
            "dano": skill.get("dano_mult", 1.0),
            "desc": skill.get("desc", ""),
            "efeito": skill.get("efeito"),
            "hits": skill.get("hits", 1),
        }
    return None

def get_bonus_arma(item_id, classe_id):
    armas = ARMAS_POR_CLASSE.get(classe_id, [])
    item = next((a for a in armas if a["id"] == item_id), None)
    if item:
        return item["atk_bonus"], True
    for cid, armas2 in ARMAS_POR_CLASSE.items():
        item2 = next((a for a in armas2 if a["id"] == item_id), None)
        if item2:
            return item2["atk_bonus"], False
    return 0, None

def get_bonus_armadura(item_id, classe_id):
    armaduras = ARMADURAS_POR_CLASSE.get(classe_id, [])
    item = next((a for a in armaduras if a["id"] == item_id), None)
    if item:
        return item["def_bonus"], True
    for cid, armaduras2 in ARMADURAS_POR_CLASSE.items():
        item2 = next((a for a in armaduras2 if a["id"] == item_id), None)
        if item2:
            return item2["def_bonus"], False
    return 0, None

def get_catalogo_completo():
    """Retorna todos os itens do catalogo"""
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
    """Busca um item pela chave"""
    for it in get_catalogo_completo():
        if it["chave"] == chave:
            return it
    return None

def get_itens_por_categoria(categoria: str):
    """Retorna itens filtrados pela categoria (para autocomplete)"""
    todos = get_catalogo_completo()
    cat_map = {
        "pocoes":         [i for i in todos if i["tipo"] == "pocao"],
        "arma_guerreiro": [i for i in todos if i["tipo"] == "arma" and i["classe"] == "guerreiro"],
        "arma_arqueiro":  [i for i in todos if i["tipo"] == "arma" and i["classe"] == "arqueiro"],
        "arma_mago":      [i for i in todos if i["tipo"] == "arma" and i["classe"] == "mago"],
        "arma_paladino":  [i for i in todos if i["tipo"] == "arma" and i["classe"] == "paladino"],
        "arma_necromante":[i for i in todos if i["tipo"] == "arma" and i["classe"] == "necromante"],
        "arma_dracomante":[i for i in todos if i["tipo"] == "arma" and i["classe"] == "dracomante"],
        "arma_arcano":    [i for i in todos if i["tipo"] == "arma" and i["classe"] == "arcano"],
        "arm_guerreiro":  [i for i in todos if i["tipo"] == "armadura" and i["classe"] == "guerreiro"],
        "arm_arqueiro":   [i for i in todos if i["tipo"] == "armadura" and i["classe"] == "arqueiro"],
        "arm_mago":       [i for i in todos if i["tipo"] == "armadura" and i["classe"] == "mago"],
        "arm_paladino":   [i for i in todos if i["tipo"] == "armadura" and i["classe"] == "paladino"],
        "arm_necromante": [i for i in todos if i["tipo"] == "armadura" and i["classe"] == "necromante"],
        "arm_dracomante": [i for i in todos if i["tipo"] == "armadura" and i["classe"] == "dracomante"],
        "arm_arcano":     [i for i in todos if i["tipo"] == "armadura" and i["classe"] == "arcano"],
        "materiais":      [i for i in todos if i["tipo"] == "material"],
    }
    return cat_map.get(categoria, todos)

# ─── SKILLS_COMPLETAS (para compatibilidade com batalha.py) ───────
# Nota: O sistema real de skills está em skills_sistema.py
# Esta é uma versão simplificada para compatibilidade

SKILLS_COMPLETAS = {
    "guerreiro": [],
    "mago": [],
    "arqueiro": [],
    "paladino": [],
    "necromante": [],
    "dracomante": [],
    "arcano": [],
}

# Preenche SKILLS_COMPLETAS a partir do skills_sistema.py
def _carregar_skills_completas():
    from skills_sistema import SKILLS
    for sid, skill in SKILLS.items():
        classe = skill.get("classe")
        if classe and classe != "suporte":
            if classe not in SKILLS_COMPLETAS:
                SKILLS_COMPLETAS[classe] = []
            SKILLS_COMPLETAS[classe].append({
                "id": sid,
                "nome": skill["nome"],
                "nivel": skill["nivel"],
                "emoji": skill["emoji"],
                "mana": skill.get("mana", 0),
                "dano": skill.get("dano_mult", 1.0),
                "desc": skill.get("desc", ""),
                "efeito": skill.get("efeito"),
            })
    # Ordena por nível
    for classe in SKILLS_COMPLETAS:
        SKILLS_COMPLETAS[classe] = sorted(SKILLS_COMPLETAS[classe], key=lambda x: x["nivel"])

_carregar_skills_completas()
