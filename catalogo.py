cat > /mnt/user-data/outputs/catalogo.py << 'PYEOF'
# catalogo.py — Catalogo completo: armas, armaduras, skills, ranks e mana por classe

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
# mana_max = base_classe + nivel * mult_nivel + poder_valor * mult_poder

MANA_CLASSE = {
    "guerreiro":  {"base": 60,  "mult_nivel": 1.5, "mult_poder": 0.3},
    "arqueiro":   {"base": 70,  "mult_nivel": 1.8, "mult_poder": 0.4},
    "mago":       {"base": 120, "mult_nivel": 3.5, "mult_poder": 0.8},
    "paladino":   {"base": 90,  "mult_nivel": 2.5, "mult_poder": 0.5},
    "necromante": {"base": 100, "mult_nivel": 2.8, "mult_poder": 0.6},
    "dracomante": {"base": 80,  "mult_nivel": 2.0, "mult_poder": 0.5},
    "arcano":     {"base": 130, "mult_nivel": 4.0, "mult_poder": 1.0},
}

MANA_DESTINO = {
    "equilibrado":  1.00,
    "prodigio":     0.85,  # troca mana por ataque
    "maldito":      0.70,  # fraco, menos mana
    "guardiao":     1.10,  # mais resistente, mais mana
    "abencado":     1.15,  # tudo +10%
    "amaldicoado":  1.00,  # aleatorio — usa base
    "filho_caos":   1.20,  # caos mas mais mana
}

def calcular_mana_max(classe_id, nivel, poder_valor, destino_id):
    cfg = MANA_CLASSE.get(classe_id, {"base": 80, "mult_nivel": 2.0, "mult_poder": 0.5})
    base = cfg["base"] + nivel * cfg["mult_nivel"] + poder_valor * cfg["mult_poder"]
    mult = MANA_DESTINO.get(destino_id, 1.0)
    return max(30, int(base * mult))

# ─── ARMAS POR CLASSE (10 cada) ──────────────────────────────────

ARMAS_POR_CLASSE = {
    "guerreiro": [
        {"id":"espada_ferro",    "nome":"Espada de Ferro",    "emoji":"⚔️","raridade":"Comum",    "atk_bonus":5,  "preco":0,    "desc":"Arma inicial. Confiavel e resistente."},
        {"id":"machado_pesado",  "nome":"Machado Pesado",     "emoji":"🪓","raridade":"Comum",    "atk_bonus":8,  "preco":120,  "desc":"Machado de ferro. Dano bruto alto."},
        {"id":"espada_prata",    "nome":"Espada de Prata",    "emoji":"⚔️","raridade":"Incomum",  "atk_bonus":12, "preco":300,  "desc":"Forjada em prata pura. ATK +12."},
        {"id":"lanca_combate",   "nome":"Lanca de Combate",   "emoji":"🔱","raridade":"Incomum",  "atk_bonus":10, "preco":280,  "desc":"Alcance extra. Bom para contra-ataques."},
        {"id":"espada_cavaleiro","nome":"Espada do Cavaleiro", "emoji":"⚔️","raridade":"Raro",    "atk_bonus":18, "preco":700,  "desc":"Espada nobre de cavaleiro veterano."},
        {"id":"martelo_guerra",  "nome":"Martelo de Guerra",  "emoji":"🔨","raridade":"Raro",    "atk_bonus":16, "preco":650,  "desc":"15% de chance de atordoar o inimigo."},
        {"id":"espada_orc",      "nome":"Espada Orc",         "emoji":"🗡️","raridade":"Raro",    "atk_bonus":20, "preco":0,    "desc":"Forjada com metal orc. Brutalidade pura."},
        {"id":"lanca_sagrada",   "nome":"Lanca Sagrada",      "emoji":"🔱","raridade":"Epico",   "atk_bonus":25, "preco":1200, "desc":"Abencada pelos deuses. Sagrado +20."},
        {"id":"espada_sombria",  "nome":"Espada Sombria",     "emoji":"🗡️","raridade":"Epico",   "atk_bonus":28, "preco":1500, "desc":"Forjada nas trevas. Drena HP ao acertar."},
        {"id":"espada_lendaria", "nome":"Espada do Heroi",    "emoji":"⚔️","raridade":"Lendario","atk_bonus":40, "preco":0,    "desc":"Arma dos grandes herois. Apenas em dungeons."},
    ],
    "arqueiro": [
        {"id":"arco_madeira",    "nome":"Arco de Madeira",    "emoji":"🏹","raridade":"Comum",    "atk_bonus":4,  "preco":0,    "desc":"Arco inicial. Leve e preciso."},
        {"id":"besta_leve",      "nome":"Besta Leve",         "emoji":"🏹","raridade":"Comum",    "atk_bonus":6,  "preco":100,  "desc":"Besta de disparo rapido."},
        {"id":"arco_composto",   "nome":"Arco Composto",      "emoji":"🏹","raridade":"Incomum",  "atk_bonus":10, "preco":260,  "desc":"Mais potente que o arco basico."},
        {"id":"besta_pesada",    "nome":"Besta Pesada",       "emoji":"🏹","raridade":"Incomum",  "atk_bonus":12, "preco":290,  "desc":"Dano perfurante. Ignora 10% da defesa."},
        {"id":"arco_elfico",     "nome":"Arco Elfico",        "emoji":"🏹","raridade":"Raro",    "atk_bonus":15, "preco":550,  "desc":"Critico +15%. Obra dos elfos da floresta."},
        {"id":"arco_sombras",    "nome":"Arco das Sombras",   "emoji":"🏹","raridade":"Raro",    "atk_bonus":18, "preco":700,  "desc":"Flechas envenenadas automaticamente."},
        {"id":"arco_encantado",  "nome":"Arco Encantado",     "emoji":"🏹","raridade":"Raro",    "atk_bonus":20, "preco":800,  "desc":"Encantado com magia arcana. Critico +20%."},
        {"id":"besta_draconica", "nome":"Besta Draconica",    "emoji":"🏹","raridade":"Epico",   "atk_bonus":26, "preco":1300, "desc":"Feita com garras de dragao. Flechas de fogo."},
        {"id":"arco_celestial",  "nome":"Arco Celestial",     "emoji":"🏹","raridade":"Epico",   "atk_bonus":30, "preco":1600, "desc":"Arco sagrado dos anjos. Critico +30%."},
        {"id":"arco_lendario",   "nome":"Arco do Cacador",    "emoji":"🏹","raridade":"Lendario","atk_bonus":45, "preco":0,    "desc":"Arco do maior cacador de todos os tempos."},
    ],
    "mago": [
        {"id":"cajado_pinho",    "nome":"Cajado de Pinho",    "emoji":"🪄","raridade":"Comum",    "atk_bonus":4,  "preco":0,    "desc":"Cajado inicial. Canaliza energia basica."},
        {"id":"vara_magica",     "nome":"Vara Magica",        "emoji":"🪄","raridade":"Comum",    "atk_bonus":6,  "preco":90,   "desc":"Vara de carvalho encantada. +5 mana."},
        {"id":"cajado_quartzo",  "nome":"Cajado de Quartzo",  "emoji":"🪄","raridade":"Incomum",  "atk_bonus":10, "preco":250,  "desc":"Cristal de quartzo amplifica magias."},
        {"id":"orbe_fogo",       "nome":"Orbe de Fogo",       "emoji":"🔮","raridade":"Incomum",  "atk_bonus":11, "preco":280,  "desc":"Orbe de fogo elementar. +10% dano de fogo."},
        {"id":"cajado_magico",   "nome":"Cajado Magico",      "emoji":"🪄","raridade":"Raro",    "atk_bonus":15, "preco":600,  "desc":"Amplifica todos os feiticos. Magia +10."},
        {"id":"tomo_arcano",     "nome":"Tomo Arcano",        "emoji":"📖","raridade":"Raro",    "atk_bonus":16, "preco":700,  "desc":"Tomo de feiticos antigos. +15% dano magico."},
        {"id":"cajado_osso2",    "nome":"Cajado Osseo+",      "emoji":"💀","raridade":"Raro",    "atk_bonus":17, "preco":0,    "desc":"Amplifica magia negra. Bom para necromante."},
        {"id":"cajado_vazio",    "nome":"Cajado do Vazio",    "emoji":"🪄","raridade":"Epico",   "atk_bonus":26, "preco":1400, "desc":"Canaliza energia do vazio. Ignora resistencias."},
        {"id":"orbe_arcano",     "nome":"Grande Orbe Arcano", "emoji":"🔮","raridade":"Epico",   "atk_bonus":30, "preco":1700, "desc":"Orbe de poder supremo. Magia +25."},
        {"id":"cajado_lendario", "nome":"Cajado do Arquimago","emoji":"🪄","raridade":"Lendario","atk_bonus":48, "preco":0,    "desc":"Cajado do maior mago de todos os tempos."},
    ],
    "paladino": [
        {"id":"maca_sagrada",    "nome":"Maca Sagrada",       "emoji":"⚡","raridade":"Comum",    "atk_bonus":6,  "preco":0,    "desc":"Maca abencada pelos deuses."},
        {"id":"escudo_espada",   "nome":"Espada e Escudo",    "emoji":"⚔️","raridade":"Comum",    "atk_bonus":5,  "preco":110,  "desc":"Combo de defesa e ataque. +5 DEF."},
        {"id":"lanca_prata",     "nome":"Lanca de Prata",     "emoji":"🔱","raridade":"Incomum",  "atk_bonus":11, "preco":270,  "desc":"Lanca de prata sagrada. Efetiva vs trevas."},
        {"id":"espada_prata",    "nome":"Espada de Prata",    "emoji":"⚔️","raridade":"Incomum",  "atk_bonus":12, "preco":300,  "desc":"Dano fisico e magico combinados."},
        {"id":"maca_divina",     "nome":"Maca Divina",        "emoji":"⚡","raridade":"Raro",    "atk_bonus":17, "preco":680,  "desc":"Canaliza poder divino. 20% chance de atordoar."},
        {"id":"espada_luz",      "nome":"Espada da Luz",      "emoji":"⚔️","raridade":"Raro",    "atk_bonus":19, "preco":750,  "desc":"Forjada com luz pura. Sagrado +15."},
        {"id":"lanca_sagrada",   "nome":"Lanca Sagrada",      "emoji":"🔱","raridade":"Raro",    "atk_bonus":20, "preco":0,    "desc":"Lanca abencada pelos deuses da guerra."},
        {"id":"martelo_sagrado", "nome":"Martelo Sagrado",    "emoji":"🔨","raridade":"Epico",   "atk_bonus":27, "preco":1350, "desc":"Martelo dos paladinos lendarios. +30 sagrado."},
        {"id":"espada_justica",  "nome":"Espada da Justica",  "emoji":"⚔️","raridade":"Epico",   "atk_bonus":32, "preco":1800, "desc":"Espada que julga os inocentes e culpados."},
        {"id":"espada_cruzada",  "nome":"Espada da Cruzada",  "emoji":"⚔️","raridade":"Lendario","atk_bonus":46, "preco":0,    "desc":"Arma dos grandes paladinos da historia."},
    ],
    "necromante": [
        {"id":"cajado_osso",     "nome":"Cajado de Osso",     "emoji":"💀","raridade":"Comum",    "atk_bonus":4,  "preco":0,    "desc":"Feito de ossos. Amplifica magia negra."},
        {"id":"foice_ferrugem",  "nome":"Foice Enferrujada",  "emoji":"⚰️","raridade":"Comum",    "atk_bonus":6,  "preco":95,   "desc":"Foice velha. Causa sangramento (veneno fraco)."},
        {"id":"cajado_sombra",   "nome":"Cajado das Sombras", "emoji":"💀","raridade":"Incomum",  "atk_bonus":10, "preco":240,  "desc":"Amplifica necromancia. +10% dreno de vida."},
        {"id":"foice_arcana",    "nome":"Foice Arcana",       "emoji":"⚰️","raridade":"Incomum",  "atk_bonus":12, "preco":280,  "desc":"Foice encantada. Drenan vida ao acertar."},
        {"id":"cajado_osso2",    "nome":"Cajado Osseo+",      "emoji":"💀","raridade":"Raro",    "atk_bonus":16, "preco":0,    "desc":"Forjado com ossos de gigante. Magia negra +20."},
        {"id":"corvo_espirito",  "nome":"Bastao do Corvo",    "emoji":"🦅","raridade":"Raro",    "atk_bonus":17, "preco":720,  "desc":"Invoca corvos espectrais que atacam."},
        {"id":"cajado_lich",     "nome":"Cajado do Lich",     "emoji":"💀","raridade":"Raro",    "atk_bonus":19, "preco":800,  "desc":"Cajado de um lich antigo. Poder sombrio."},
        {"id":"foice_morte",     "nome":"Foice da Morte",     "emoji":"⚰️","raridade":"Epico",   "atk_bonus":28, "preco":1400, "desc":"A foice da propria Morte. Drenan massivo."},
        {"id":"cetro_lich",      "nome":"Cetro do Lich",      "emoji":"💀","raridade":"Epico",   "atk_bonus":32, "preco":1600, "desc":"Cetro do Rei Lich. +30% dano necrotico."},
        {"id":"cajado_sombra_l", "nome":"Cajado das Trevas",  "emoji":"💀","raridade":"Lendario","atk_bonus":47, "preco":0,    "desc":"O mais poderoso artefato das trevas."},
    ],
    "dracomante": [
        {"id":"garra_dragao",    "nome":"Garra de Dragao",    "emoji":"🐉","raridade":"Comum",    "atk_bonus":5,  "preco":0,    "desc":"Garra de dragao jovem. Dano de fogo."},
        {"id":"dente_dragao_arm","nome":"Dente de Dragao",    "emoji":"🐉","raridade":"Comum",    "atk_bonus":7,  "preco":130,  "desc":"Dente afiado como faca. Sangramento."},
        {"id":"cajado_dragao",   "nome":"Cajado do Dragao",   "emoji":"🐉","raridade":"Incomum",  "atk_bonus":11, "preco":260,  "desc":"Cajado com essencia de dragao. +15% fogo."},
        {"id":"lanca_escama",    "nome":"Lanca de Escama",    "emoji":"🐉","raridade":"Incomum",  "atk_bonus":13, "preco":300,  "desc":"Feita com escamas duras. Perfura armaduras."},
        {"id":"garra_flamejante","nome":"Garra Flamejante",   "emoji":"🐉","raridade":"Raro",    "atk_bonus":18, "preco":650,  "desc":"Garra encharcada de fogo. Queimadura."},
        {"id":"espada_dragao",   "nome":"Espada do Dragao",   "emoji":"🐉","raridade":"Raro",    "atk_bonus":20, "preco":800,  "desc":"Forjada no fogo de um dragao anciao."},
        {"id":"lanca_draconica", "nome":"Lanca Draconica",    "emoji":"🐉","raridade":"Raro",    "atk_bonus":22, "preco":900,  "desc":"Lanca infundida com sangue de dragao."},
        {"id":"garra_anciao",    "nome":"Garra do Anciao",    "emoji":"🐉","raridade":"Epico",   "atk_bonus":30, "preco":1500, "desc":"Garra de dragao anciao. Fogo + veneno."},
        {"id":"espada_fogo",     "nome":"Espada de Fogo",     "emoji":"🐉","raridade":"Epico",   "atk_bonus":33, "preco":1800, "desc":"Lamina eternamente em chamas."},
        {"id":"garra_dragao_l",  "nome":"Garra do Dragao Eterno","emoji":"🐉","raridade":"Lendario","atk_bonus":50,"preco":0,"desc":"A arma de um dragao imortal. Poder absoluto."},
    ],
    "arcano": [
        {"id":"orbe_arcano_p",   "nome":"Orbe Arcano",        "emoji":"✨","raridade":"Comum",    "atk_bonus":4,  "preco":0,    "desc":"Orbe de energia arcana pura."},
        {"id":"anel_arcano",     "nome":"Anel Arcano",         "emoji":"💍","raridade":"Comum",    "atk_bonus":6,  "preco":100,  "desc":"Anel que amplifica feiticos. +5 mana."},
        {"id":"cristal_arcano",  "nome":"Cristal Arcano",     "emoji":"✨","raridade":"Incomum",  "atk_bonus":10, "preco":240,  "desc":"Cristal de poder arcano puro."},
        {"id":"tomo_segredos",   "nome":"Tomo dos Segredos",  "emoji":"📖","raridade":"Incomum",  "atk_bonus":12, "preco":270,  "desc":"Tomo de segredos arcanos. +15 mana."},
        {"id":"orbe_vazio",      "nome":"Orbe do Vazio",      "emoji":"🌀","raridade":"Raro",    "atk_bonus":16, "preco":600,  "desc":"Orbe do vazio absoluto. Ignora 15% defesa."},
        {"id":"cetro_arcano",    "nome":"Cetro Arcano",       "emoji":"✨","raridade":"Raro",    "atk_bonus":18, "preco":700,  "desc":"Cetro de poder arcano concentrado."},
        {"id":"cajado_magico",   "nome":"Cajado Magico",      "emoji":"🪄","raridade":"Raro",    "atk_bonus":20, "preco":750,  "desc":"Amplifica magias arcanas. Magia +15."},
        {"id":"orbe_singularidade","nome":"Orbe da Singularidade","emoji":"🕳️","raridade":"Epico","atk_bonus":28,"preco":1400,"desc":"Orbe que colapsa a realidade. Dano +25%."},
        {"id":"cetro_eterno",    "nome":"Cetro Eterno",       "emoji":"✨","raridade":"Epico",   "atk_bonus":34, "preco":1900, "desc":"Cetro de poder eterno e infinito."},
        {"id":"orbe_arcano_l",   "nome":"Orbe do Arcano Supremo","emoji":"✨","raridade":"Lendario","atk_bonus":52,"preco":0,"desc":"O orbe mais poderoso da historia do mundo."},
    ],
}

# ─── ARMADURAS POR CLASSE (10 cada) ──────────────────────────────

ARMADURAS_POR_CLASSE = {
    "guerreiro": [
        {"id":"armadura_couro",  "nome":"Armadura de Couro",  "emoji":"🥋","raridade":"Comum",    "def_bonus":5,  "preco":0,    "desc":"Armadura inicial. Leve e flexivel."},
        {"id":"cota_malha_g",    "nome":"Cota de Malha",      "emoji":"🛡️","raridade":"Comum",    "def_bonus":8,  "preco":150,  "desc":"Malha de ferro. Protecao equilibrada."},
        {"id":"armadura_ferro",  "nome":"Armadura de Ferro",  "emoji":"⚙️","raridade":"Incomum",  "def_bonus":13, "preco":350,  "desc":"Armadura de ferro completa."},
        {"id":"escudo_torre",    "nome":"Escudo Torre",        "emoji":"🛡️","raridade":"Incomum",  "def_bonus":15, "preco":380,  "desc":"Escudo gigante. DEF +15, bloqueia ataques."},
        {"id":"armadura_plena",  "nome":"Armadura Plena",     "emoji":"⚙️","raridade":"Raro",    "def_bonus":20, "preco":900,  "desc":"Cobertura total. Para guerreiros experientes."},
        {"id":"cota_aco",        "nome":"Cota de Aco",        "emoji":"🛡️","raridade":"Raro",    "def_bonus":22, "preco":950,  "desc":"Malha de aco temperado. Muito resistente."},
        {"id":"armadura_runa",   "nome":"Armadura Runada",    "emoji":"⚙️","raridade":"Raro",    "def_bonus":25, "preco":1100, "desc":"Gravada com runas de protecao."},
        {"id":"armadura_cavaleiro","nome":"Armadura do Cavaleiro","emoji":"⚙️","raridade":"Epico","def_bonus":32,"preco":1500,"desc":"Armadura completa de cavaleiro lendario."},
        {"id":"armadura_titan",  "nome":"Armadura do Titan",  "emoji":"🗿","raridade":"Epico",   "def_bonus":38, "preco":0,    "desc":"Armadura de um titan. +20% HP max."},
        {"id":"armadura_heroi",  "nome":"Armadura do Heroi",  "emoji":"⚙️","raridade":"Lendario","def_bonus":55, "preco":0,    "desc":"A armadura definitiva dos grandes herois."},
    ],
    "arqueiro": [
        {"id":"armadura_couro",  "nome":"Armadura de Couro",  "emoji":"🥋","raridade":"Comum",    "def_bonus":4,  "preco":0,    "desc":"Couro leve. Ideal para mobilidade."},
        {"id":"gibao_arqueiro",  "nome":"Gibao de Couro",     "emoji":"🥋","raridade":"Comum",    "def_bonus":6,  "preco":100,  "desc":"Gibao reforçado. Equilibra defesa e agilidade."},
        {"id":"cota_malha_leve", "nome":"Cota Leve",          "emoji":"🛡️","raridade":"Incomum",  "def_bonus":10, "preco":270,  "desc":"Cota de malha leve. Para arqueiros ageis."},
        {"id":"gibao_escama",    "nome":"Gibao de Escama",    "emoji":"🥋","raridade":"Incomum",  "def_bonus":12, "preco":300,  "desc":"Escamas leves costuradas no couro."},
        {"id":"armadura_ranger", "nome":"Armadura do Ranger", "emoji":"🥋","raridade":"Raro",    "def_bonus":16, "preco":700,  "desc":"Armadura de ranger veterano. +10% esquiva."},
        {"id":"gibao_elfico",    "nome":"Gibao Elfico",       "emoji":"🥋","raridade":"Raro",    "def_bonus":18, "preco":750,  "desc":"Armadura dos elfos. Levissima e resistente."},
        {"id":"manto_sombra",    "nome":"Manto das Sombras",  "emoji":"🥋","raridade":"Raro",    "def_bonus":20, "preco":800,  "desc":"Manto que funde com as sombras. +15% esquiva."},
        {"id":"armadura_caçador","nome":"Armadura do Cacador","emoji":"🥋","raridade":"Epico",   "def_bonus":27, "preco":1300, "desc":"Para o melhor dos cacadores. Perfil reduzido."},
        {"id":"gibao_dragao",    "nome":"Gibao de Dragao",    "emoji":"🐉","raridade":"Epico",   "def_bonus":32, "preco":1600, "desc":"Escamas de dragao processadas. Leve e forte."},
        {"id":"armadura_cacador_l","nome":"Armadura do Cacador Lendario","emoji":"🥋","raridade":"Lendario","def_bonus":48,"preco":0,"desc":"A armadura do maior cacador da historia."},
    ],
    "mago": [
        {"id":"robe_algodao",    "nome":"Robe de Algodao",    "emoji":"👘","raridade":"Comum",    "def_bonus":2,  "preco":0,    "desc":"Robe magico basico. +5 mana."},
        {"id":"manto_aprendiz",  "nome":"Manto do Aprendiz",  "emoji":"👘","raridade":"Comum",    "def_bonus":3,  "preco":80,   "desc":"Manto de estudante de magia. +10 mana."},
        {"id":"robe_arcano",     "nome":"Robe Arcano",        "emoji":"👘","raridade":"Incomum",  "def_bonus":6,  "preco":220,  "desc":"Robe encantado. +15 mana e +5% dano magico."},
        {"id":"manto_chamas",    "nome":"Manto das Chamas",   "emoji":"👘","raridade":"Incomum",  "def_bonus":7,  "preco":250,  "desc":"Manto de fogo. Resistencia elemental."},
        {"id":"robe_sabio",      "nome":"Robe do Sabio",      "emoji":"👘","raridade":"Raro",    "def_bonus":10, "preco":600,  "desc":"Robe de sabio anciao. +25 mana e escudo magico."},
        {"id":"manto_arcano",    "nome":"Manto Arcano",       "emoji":"👘","raridade":"Raro",    "def_bonus":12, "preco":700,  "desc":"Manto de arcano experiente. +20% dano magico."},
        {"id":"robe_espectral",  "nome":"Robe Espectral",     "emoji":"👘","raridade":"Raro",    "def_bonus":13, "preco":750,  "desc":"Robe espectral semi-corpóreo. +30 mana."},
        {"id":"manto_arquimago", "nome":"Manto do Arquimago", "emoji":"👘","raridade":"Epico",   "def_bonus":18, "preco":1400, "desc":"Manto de um arquimago. +50 mana e escudo forte."},
        {"id":"robe_vazio",      "nome":"Robe do Vazio",      "emoji":"👘","raridade":"Epico",   "def_bonus":20, "preco":1700, "desc":"Feito de energia do vazio. +40% dano magico."},
        {"id":"robe_lendario",   "nome":"Robe do Mago Supremo","emoji":"👘","raridade":"Lendario","def_bonus":30,"preco":0,"desc":"O robe do maior mago que ja existiu."},
    ],
    "paladino": [
        {"id":"armadura_couro",  "nome":"Armadura de Couro",  "emoji":"🥋","raridade":"Comum",    "def_bonus":5,  "preco":0,    "desc":"Armadura inicial do paladino."},
        {"id":"cota_malha",      "nome":"Cota de Malha",      "emoji":"🛡️","raridade":"Comum",    "def_bonus":9,  "preco":160,  "desc":"Cota de malha abencada."},
        {"id":"armadura_ferro",  "nome":"Armadura de Ferro",  "emoji":"⚙️","raridade":"Incomum",  "def_bonus":14, "preco":360,  "desc":"Armadura de ferro com simbolos sagrados."},
        {"id":"escudo_sagrado",  "nome":"Escudo Sagrado",     "emoji":"🛡️","raridade":"Incomum",  "def_bonus":16, "preco":400,  "desc":"Escudo abencado. Bloqueia magia negra."},
        {"id":"armadura_plena",  "nome":"Armadura Plena",     "emoji":"⚙️","raridade":"Raro",    "def_bonus":21, "preco":900,  "desc":"Armadura de paladino completa."},
        {"id":"armadura_sagrada","nome":"Armadura Sagrada",   "emoji":"⚙️","raridade":"Raro",    "def_bonus":24, "preco":1000, "desc":"Armadura abencada pelos deuses."},
        {"id":"armadura_escama", "nome":"Armadura de Escama", "emoji":"🐉","raridade":"Raro",    "def_bonus":26, "preco":0,    "desc":"Escamas de dragao sagrado. Forte e santa."},
        {"id":"armadura_divina", "nome":"Armadura Divina",    "emoji":"⚙️","raridade":"Epico",   "def_bonus":34, "preco":1600, "desc":"Armadura forjada pelos proprios deuses."},
        {"id":"aegis_sagrada",   "nome":"Aegis Sagrada",      "emoji":"🛡️","raridade":"Epico",   "def_bonus":36, "preco":1800, "desc":"Escudo definitivo. Imune a efeitos negativos."},
        {"id":"armadura_cruzado","nome":"Armadura do Cruzado","emoji":"⚙️","raridade":"Lendario","def_bonus":52,"preco":0,"desc":"A armadura dos grandes cruzados da historia."},
    ],
    "necromante": [
        {"id":"manto_sombrio",   "nome":"Manto Sombrio",      "emoji":"🧥","raridade":"Comum",    "def_bonus":3,  "preco":0,    "desc":"Manto das trevas. +5% magia negra."},
        {"id":"robe_osseo",      "nome":"Robe de Ossos",      "emoji":"💀","raridade":"Comum",    "def_bonus":5,  "preco":90,   "desc":"Tecido com ossos pequenos. +10% necromancia."},
        {"id":"manto_sombra",    "nome":"Manto das Sombras",  "emoji":"🧥","raridade":"Incomum",  "def_bonus":8,  "preco":230,  "desc":"Manto que absorve sombras. +15 mana."},
        {"id":"robe_lich",       "nome":"Robe do Lich",       "emoji":"💀","raridade":"Incomum",  "def_bonus":10, "preco":260,  "desc":"Robe de um lich. +20% dreno de vida."},
        {"id":"capa_vampiro",    "nome":"Capa de Vampiro",    "emoji":"🧛","raridade":"Raro",    "def_bonus":14, "preco":0,    "desc":"Capa de vampiro. DEF +14, drena HP passivo."},
        {"id":"armadura_morte",  "nome":"Armadura da Morte",  "emoji":"💀","raridade":"Raro",    "def_bonus":16, "preco":700,  "desc":"Armadura da propria Morte. Imune a veneno."},
        {"id":"manto_rey_lich",  "nome":"Manto do Rei Lich",  "emoji":"💀","raridade":"Raro",    "def_bonus":18, "preco":800,  "desc":"Manto do poderoso Rei Lich. +30 mana."},
        {"id":"armadura_espectro","nome":"Armadura Espectral","emoji":"👻","raridade":"Epico",   "def_bonus":24, "preco":1400, "desc":"Armadura espectral semi-fisica. +25% esquiva."},
        {"id":"robe_morte_etern","nome":"Robe da Morte Eterna","emoji":"💀","raridade":"Epico",  "def_bonus":28, "preco":1700, "desc":"Robe da morte eterna. Poder sombrio supremo."},
        {"id":"manto_sombrio_l", "nome":"Manto do Necromante Lendario","emoji":"🧥","raridade":"Lendario","def_bonus":45,"preco":0,"desc":"O maior artefato das trevas ja criado."},
    ],
    "dracomante": [
        {"id":"gibao_escama",    "nome":"Gibao de Escama",    "emoji":"🐉","raridade":"Comum",    "def_bonus":6,  "preco":0,    "desc":"Gibao de escamas de dragao jovem."},
        {"id":"peitoral_escama", "nome":"Peitoral de Escama", "emoji":"🐉","raridade":"Comum",    "def_bonus":8,  "preco":140,  "desc":"Peitoral pesado de escamas."},
        {"id":"armadura_escama", "nome":"Armadura de Escama", "emoji":"🐉","raridade":"Incomum",  "def_bonus":14, "preco":350,  "desc":"Armadura completa de escamas. Resistente ao fogo."},
        {"id":"escudo_dragao",   "nome":"Escudo do Dragao",   "emoji":"🐉","raridade":"Incomum",  "def_bonus":15, "preco":380,  "desc":"Escudo feito de escudos de dragao."},
        {"id":"armadura_fogo",   "nome":"Armadura de Fogo",   "emoji":"🌋","raridade":"Raro",    "def_bonus":20, "preco":800,  "desc":"Imune a queimadura. Resistencia ao fogo."},
        {"id":"escama_anciao",   "nome":"Armadura de Escama Anciao","emoji":"🐉","raridade":"Raro","def_bonus":23,"preco":900,"desc":"Escamas de dragao anciao. Extremamente dura."},
        {"id":"elmo_dragao",     "nome":"Elmo do Dragao",     "emoji":"🪖","raridade":"Raro",    "def_bonus":25, "preco":0,    "desc":"Elmo forjado com cranio de dragao. Max protecao."},
        {"id":"armadura_draconica","nome":"Armadura Draconica","emoji":"🐉","raridade":"Epico",  "def_bonus":33, "preco":1600, "desc":"A armadura de um dracomante lendario."},
        {"id":"forma_dragao",    "nome":"Escamas do Dragao Eterno","emoji":"🐉","raridade":"Epico","def_bonus":38,"preco":1900,"desc":"Escamas de um dragao imortal."},
        {"id":"armadura_dragao_l","nome":"Armadura do Dragao Lendario","emoji":"🐉","raridade":"Lendario","def_bonus":56,"preco":0,"desc":"A armadura definitiva de um dracomante."},
    ],
    "arcano": [
        {"id":"robe_arcano_p",   "nome":"Robe Arcano",        "emoji":"✨","raridade":"Comum",    "def_bonus":2,  "preco":0,    "desc":"Robe de energia arcana. +5 mana."},
        {"id":"manto_arcano",    "nome":"Manto Arcano",       "emoji":"✨","raridade":"Comum",    "def_bonus":4,  "preco":85,   "desc":"Manto de poder arcano. +10 mana."},
        {"id":"robe_singularidade","nome":"Robe da Singularidade","emoji":"🌀","raridade":"Incomum","def_bonus":7,"preco":230,"desc":"Robe que dobra a realidade. +20 mana."},
        {"id":"manto_vazio",     "nome":"Manto do Vazio",     "emoji":"🌀","raridade":"Incomum",  "def_bonus":9,  "preco":260,  "desc":"Manto do vazio absoluto. +25 mana."},
        {"id":"cota_malha",      "nome":"Cota de Malha",      "emoji":"🛡️","raridade":"Raro",    "def_bonus":13, "preco":600,  "desc":"Cota de malha magicamente reforçada."},
        {"id":"robe_arcano_r",   "nome":"Robe do Arcano",     "emoji":"✨","raridade":"Raro",    "def_bonus":15, "preco":700,  "desc":"Robe de poder arcano real. +30 mana."},
        {"id":"escudo_forca",    "nome":"Escudo de Forca",    "emoji":"🌀","raridade":"Raro",    "def_bonus":16, "preco":750,  "desc":"Escudo de campo de forca permanente."},
        {"id":"armadura_arcana", "nome":"Armadura Arcana",    "emoji":"✨","raridade":"Epico",   "def_bonus":22, "preco":1400, "desc":"Armadura de energia arcana pura. +50 mana."},
        {"id":"manto_transcend", "nome":"Manto da Transcendencia","emoji":"✨","raridade":"Epico","def_bonus":26,"preco":1800,"desc":"Manto de um ser que transcendeu a realidade."},
        {"id":"armadura_arcana_l","nome":"Armadura do Arcano Supremo","emoji":"✨","raridade":"Lendario","def_bonus":42,"preco":0,"desc":"A armadura definitiva de um arcano."},
    ],
}

# ─── SKILLS COMPLETAS POR CLASSE (10 cada) ───────────────────────

SKILLS_COMPLETAS = {
    "guerreiro": [
        {"id":"golpe_basico",  "nome":"Golpe Basico",  "nivel":1,  "emoji":"⚔️","dano":1.0,"mana":0, "desc":"Ataque fisico direto. Sem custo de mana.",         "efeito":None},
        {"id":"escudo",        "nome":"Postura de Escudo","nivel":3,"emoji":"🛡️","dano":0,  "mana":8, "desc":"Reduz 50% do dano recebido no proximo turno.",    "efeito":"defesa"},
        {"id":"golpe_brutal",  "nome":"Golpe Brutal",   "nivel":8, "emoji":"💥","dano":2.2,"mana":18,"desc":"Golpe devastador. Dano x2.2, ignora parte da defesa.","efeito":None},
        {"id":"investida",     "nome":"Investida",       "nivel":12,"emoji":"🏃","dano":1.4,"mana":15,"desc":"Corre em direcao ao inimigo. 30% chance atordoar.",  "efeito":"atordoar"},
        {"id":"grito_guerra",  "nome":"Grito de Guerra", "nivel":16,"emoji":"😤","dano":0,  "mana":22,"desc":"+35% de ataque por 3 turnos.",                      "efeito":"buff_ataque"},
        {"id":"lamina_girat",  "nome":"Lamina Giratoria","nivel":20,"emoji":"🌀","dano":1.8,"mana":28,"desc":"Gira a lamina causando 2 golpes consecutivos.",      "efeito":"hits2"},
        {"id":"escudo_aco",    "nome":"Escudo de Aco",   "nivel":28,"emoji":"🪨","dano":0,  "mana":35,"desc":"Escudo impenetravel por 2 turnos. Absorve tudo.",    "efeito":"escudo_total"},
        {"id":"furia",         "nome":"Furia Berserker", "nivel":35,"emoji":"🔥","dano":1.5,"mana":40,"desc":"EPICO: +60% ATK, regenera vida a cada golpe.",       "efeito":"berserker"},
        {"id":"golpe_final",   "nome":"Golpe Final",     "nivel":45,"emoji":"💢","dano":3.5,"mana":50,"desc":"Golpe definitivo. Dano massivo ignorando 50% defesa.","efeito":None},
        {"id":"lendario_atk",  "nome":"Golpe Lendario",  "nivel":70,"emoji":"⚡","dano":5.0,"mana":80,"desc":"LENDARIO: O ataque mais poderoso do guerreiro.",     "efeito":None},
    ],
    "arqueiro": [
        {"id":"tiro_preciso",  "nome":"Tiro Preciso",   "nivel":1, "emoji":"🎯","dano":1.0,"mana":0, "desc":"+40% chance de critico neste turno.",              "efeito":"critico_bonus"},
        {"id":"tiro_rapido",   "nome":"Tiro Rapido",    "nivel":3, "emoji":"💨","dano":0.8,"mana":5, "desc":"Dois disparos rapidos. Menor dano individual.",     "efeito":"hits2"},
        {"id":"esquiva",       "nome":"Esquiva",          "nivel":5, "emoji":"💨","dano":0,  "mana":15,"desc":"Evita completamente o proximo ataque recebido.",   "efeito":"esquiva"},
        {"id":"flecha_veneno", "nome":"Flecha Venenosa", "nivel":10,"emoji":"🟢","dano":1.1,"mana":18,"desc":"Envenena o alvo. 10% HP de dano por 3 turnos.",    "efeito":"veneno"},
        {"id":"tiro_multiplo", "nome":"Tiro Multiplo",   "nivel":14,"emoji":"🏹","dano":0.7,"mana":22,"desc":"Dispara 3 flechas simultaneamente.",                "efeito":"hits3"},
        {"id":"flecha_perf",   "nome":"Flecha Perfurante","nivel":20,"emoji":"🔱","dano":2.0,"mana":30,"desc":"Ignora 60% da defesa do alvo.",                   "efeito":"ignorar_defesa"},
        {"id":"chuva_flechas", "nome":"Chuva de Flechas","nivel":28,"emoji":"☄️","dano":0.5,"mana":40,"desc":"5 flechas em rapida sucessao. Dano total alto.",   "efeito":"hits5"},
        {"id":"tiro_fantasma", "nome":"Tiro Fantasma",   "nivel":35,"emoji":"👻","dano":2.5,"mana":50,"desc":"EPICO: Atravessa defesa. 100% ignorar defesa.",    "efeito":"ignorar_defesa"},
        {"id":"flecha_morte",  "nome":"Flecha da Morte", "nivel":45,"emoji":"💀","dano":3.0,"mana":60,"desc":"Flecha imbuida de morte. Alta chance de critico.",  "efeito":"critico_bonus"},
        {"id":"tiro_lendario", "nome":"Tiro Lendario",   "nivel":70,"emoji":"⭐","dano":6.0,"mana":90,"desc":"LENDARIO: O tiro definitivo do arqueiro lendario.", "efeito":None},
    ],
    "mago": [
        {"id":"bola_fogo",     "nome":"Bola de Fogo",   "nivel":1, "emoji":"🔥","dano":1.3,"mana":12,"desc":"Esfera de fogo. 25% chance de queimadura.",         "efeito":"queimadura"},
        {"id":"missil_arcano", "nome":"Missil Arcano",  "nivel":3, "emoji":"✨","dano":1.1,"mana":8, "desc":"3 misseis de energia arcana. Confiavel.",           "efeito":"hits3"},
        {"id":"escudo_arcano", "nome":"Escudo Arcano",  "nivel":6, "emoji":"💜","dano":0,  "mana":20,"desc":"Barreira magica que absorve o proximo ataque.",     "efeito":"escudo"},
        {"id":"raio_congelante","nome":"Raio Congelante","nivel":10,"emoji":"❄️","dano":1.5,"mana":22,"desc":"40% chance de congelar o inimigo (perde 1 turno).",  "efeito":"congelar"},
        {"id":"tempestade",    "nome":"Tempestade",     "nivel":16,"emoji":"⚡","dano":1.7,"mana":35,"desc":"Tempestade eletrica. 35% chance de paralisar.",      "efeito":"paralisia"},
        {"id":"meteor",        "nome":"Meteoro",         "nivel":24,"emoji":"☄️","dano":2.8,"mana":45,"desc":"Chama um meteoro do ceu. Dano massivo.",            "efeito":None},
        {"id":"campo_forca",   "nome":"Campo de Forca", "nivel":28,"emoji":"🔮","dano":0,  "mana":30,"desc":"EPICO: Reflete 40% do dano recebido por 2 turnos.", "efeito":"reflexo"},
        {"id":"sobrecarga",    "nome":"Sobrecarga",      "nivel":35,"emoji":"🌟","dano":3.5,"mana":60,"desc":"EPICO: Dano devastador mas fica sem mana.",         "efeito":"sobrecarga"},
        {"id":"chuva_meteoros","nome":"Chuva de Meteoros","nivel":50,"emoji":"💥","dano":4.0,"mana":70,"desc":"Multiplos meteoros. Dano massivo em area.",        "efeito":"hits3"},
        {"id":"singularidade_m","nome":"Singularidade",  "nivel":70,"emoji":"🌌","dano":7.0,"mana":100,"desc":"LENDARIO: Colapso dimensional. Dano absoluto.",   "efeito":None},
    ],
    "paladino": [
        {"id":"golpe_sagrado", "nome":"Golpe Sagrado",  "nivel":1, "emoji":"⚡","dano":1.2,"mana":10,"desc":"Combina dano fisico e sagrado.",                    "efeito":None},
        {"id":"cura",          "nome":"Cura",            "nivel":3, "emoji":"💚","dano":0,  "mana":25,"desc":"Cura sagrada. Restaura 35% do HP maximo.",         "efeito":"cura"},
        {"id":"martelo_sagrado","nome":"Martelo Sagrado","nivel":8, "emoji":"🔨","dano":1.6,"mana":20,"desc":"Golpe pesado. 40% chance de atordoar.",            "efeito":"atordoar"},
        {"id":"aura_sagrada",  "nome":"Aura Sagrada",   "nivel":14,"emoji":"🌟","dano":0,  "mana":30,"desc":"+25% ATK e DEF. Regenera 5% HP por turno.",        "efeito":"buff_all"},
        {"id":"escudo_divino", "nome":"Escudo Divino",  "nivel":20,"emoji":"🛡️","dano":0,  "mana":35,"desc":"Bloqueia completamente os proximos 2 ataques.",    "efeito":"escudo_total"},
        {"id":"cura_grande",   "nome":"Cura em Area",   "nivel":25,"emoji":"💗","dano":0,  "mana":45,"desc":"Cura poderosa. Restaura 60% do HP maximo.",        "efeito":"cura_grande"},
        {"id":"benção_divina", "nome":"Bencao Divina",  "nivel":30,"emoji":"🙏","dano":0,  "mana":40,"desc":"+30% em todos os stats por 3 turnos.",             "efeito":"buff_all"},
        {"id":"juizo_final",   "nome":"Juizo Final",    "nivel":35,"emoji":"☀️","dano":3.0,"mana":60,"desc":"EPICO: Dano sagrado que escala com HP perdido.",   "efeito":"sagrado_bonus"},
        {"id":"ressurreicao",  "nome":"Ressurreicao",   "nivel":50,"emoji":"✝️","dano":0,  "mana":80,"desc":"Volta com 50% HP se morrer. Uso unico.",           "efeito":"ressurreicao"},
        {"id":"poder_divino",  "nome":"Poder Divino",   "nivel":70,"emoji":"✨","dano":5.0,"mana":90,"desc":"LENDARIO: Dano sagrado absoluto. Imune por 2 turnos.","efeito":"buff_all"},
    ],
    "necromante": [
        {"id":"drenar_vida",   "nome":"Drenar Vida",    "nivel":1, "emoji":"🌑","dano":1.1,"mana":10,"desc":"Absorve a vida. Metade do dano vira HP.",           "efeito":"dreno"},
        {"id":"maldicao",      "nome":"Maldicao",        "nivel":4, "emoji":"🩸","dano":0.6,"mana":12,"desc":"Envenena o alvo por 4 turnos.",                   "efeito":"veneno"},
        {"id":"invocar_morto", "nome":"Invocar Esqueleto","nivel":8,"emoji":"💀","dano":0.9,"mana":20,"desc":"Esqueleto que ataca por voce.",                    "efeito":None},
        {"id":"toque_necro",   "nome":"Toque Necrotico","nivel":12,"emoji":"☠️","dano":1.4,"mana":25,"desc":"Dano + -20% ATK do inimigo por 2 turnos.",         "efeito":"enfraquecer"},
        {"id":"onda_sombria",  "nome":"Onda Sombria",   "nivel":18,"emoji":"🌊","dano":1.8,"mana":35,"desc":"Dano alto e drena 30 de mana do oponente.",        "efeito":"drenar_mana"},
        {"id":"banshee",       "nome":"Grito da Banshee","nivel":24,"emoji":"👻","dano":1.5,"mana":40,"desc":"Aterroriza o alvo. -30% ATK por 2 turnos.",       "efeito":"terror"},
        {"id":"exercito",      "nome":"Exercito dos Mortos","nivel":30,"emoji":"💀","dano":2.2,"mana":55,"desc":"EPICO: 3 mortos-vivos atacam juntos.",          "efeito":"hits3"},
        {"id":"abraco_morte",  "nome":"Abraco da Morte","nivel":35,"emoji":"💀","dano":1.0,"mana":65,"desc":"EPICO: 20% chance de morte instantanea.",           "efeito":"instakill_chance"},
        {"id":"exercito_grande","nome":"Grande Exercito","nivel":50,"emoji":"☠️","dano":2.8,"mana":80,"desc":"5 mortos-vivos atacam simultaneamente.",           "efeito":"hits5"},
        {"id":"morte_absoluta","nome":"Morte Absoluta",  "nivel":70,"emoji":"💀","dano":6.0,"mana":100,"desc":"LENDARIO: Instakill com 35% de chance.",          "efeito":"instakill_chance"},
    ],
    "dracomante": [
        {"id":"baforada",      "nome":"Baforada",        "nivel":1, "emoji":"🔥","dano":1.4,"mana":15,"desc":"Chamas draconicas. Queimadura por 2 turnos.",      "efeito":"queimadura"},
        {"id":"garra_dragao_s","nome":"Garra do Dragao", "nivel":4, "emoji":"🐾","dano":1.2,"mana":10,"desc":"Ataque fisico com garras draconicas.",             "efeito":None},
        {"id":"escamas",       "nome":"Escamas",          "nivel":8, "emoji":"🐉","dano":0,  "mana":20,"desc":"-35% dano recebido por 3 turnos.",                "efeito":"armadura"},
        {"id":"rugido",        "nome":"Rugido do Dragao","nivel":14,"emoji":"😤","dano":0,  "mana":18,"desc":"Aterroriza o inimigo. -40% ATK por 2 turnos.",     "efeito":"terror"},
        {"id":"cauda",         "nome":"Chicote de Cauda","nivel":18,"emoji":"🌪️","dano":1.6,"mana":25,"desc":"45% chance de atordoar o inimigo por 1 turno.",   "efeito":"atordoar"},
        {"id":"voo_dragao",    "nome":"Voo do Dragao",   "nivel":22,"emoji":"🦅","dano":0,  "mana":30,"desc":"Levanta voo. Intocavel por 1 turno.",              "efeito":"esquiva"},
        {"id":"forma_menor",   "nome":"Forma Menor",     "nivel":28,"emoji":"🌋","dano":0,  "mana":45,"desc":"EPICO: +40% ATK e DEF por 3 turnos.",              "efeito":"buff_all"},
        {"id":"dragao_eterno", "nome":"Dragao Eterno",   "nivel":35,"emoji":"💎","dano":4.0,"mana":70,"desc":"EPICO: Forma completa. ATK x4.0 por 1 turno.",    "efeito":None},
        {"id":"tempestade_fogo","nome":"Tempestade de Fogo","nivel":50,"emoji":"🌋","dano":3.5,"mana":80,"desc":"Devastacao de fogo em area. Queimadura massiva.", "efeito":"queimadura"},
        {"id":"dragao_lend",   "nome":"Dragao Lendario", "nivel":70,"emoji":"🐉","dano":7.5,"mana":110,"desc":"LENDARIO: Poder absoluto do dragao eterno.",     "efeito":None},
    ],
    "arcano": [
        {"id":"faisca",        "nome":"Faisca Arcana",  "nivel":1, "emoji":"✨","dano":1.2,"mana":8, "desc":"Energia arcana pura. Ignora resistencias.",        "efeito":None},
        {"id":"distorcao",     "nome":"Distorcao",       "nivel":4, "emoji":"🌀","dano":0.8,"mana":15,"desc":"-50% precisao do inimigo por 2 turnos.",          "efeito":"confusao"},
        {"id":"campo_forca_a", "nome":"Campo de Forca", "nivel":6, "emoji":"🔮","dano":0,  "mana":22,"desc":"Reflete 30% do dano recebido por 2 turnos.",       "efeito":"reflexo"},
        {"id":"explosao_arcana","nome":"Explosao Arcana","nivel":10,"emoji":"💥","dano":2.0,"mana":28,"desc":"Explosao de energia arcana. Dano massivo.",        "efeito":None},
        {"id":"teleporte",     "nome":"Teletransporte",  "nivel":15,"emoji":"🌟","dano":1.5,"mana":25,"desc":"Ataca pela retaguarda. Ignora defesa + esquiva.",  "efeito":"esquiva"},
        {"id":"drenar_magia",  "nome":"Drenar Magia",   "nivel":20,"emoji":"💜","dano":1.0,"mana":0, "desc":"Drena 40 mana do oponente e adiciona a voce.",     "efeito":"drenar_mana"},
        {"id":"tempestade_arc","nome":"Tempestade Arcana","nivel":26,"emoji":"⭐","dano":2.5,"mana":55,"desc":"EPICO: Atinge 4 vezes em rapida sucessao.",       "efeito":"hits4"},
        {"id":"singularidade", "nome":"Singularidade",  "nivel":35,"emoji":"🕳️","dano":5.0,"mana":75,"desc":"EPICO: Maior dano do jogo. Fica sem mana 3 turnos.","efeito":None},
        {"id":"distorcao_real","nome":"Distorcao da Realidade","nivel":50,"emoji":"🌀","dano":3.5,"mana":80,"desc":"Distorce a realidade. -70% precisao inimigo.","efeito":"confusao"},
        {"id":"arcano_supremo","nome":"Poder Arcano Supremo","nivel":70,"emoji":"✨","dano":8.0,"mana":120,"desc":"LENDARIO: O poder arcano em sua forma mais pura.","efeito":None},
    ],
}

# ─── AFINIDADE ────────────────────────────────────────────────────

def get_armas_classe(classe_id):
    return ARMAS_POR_CLASSE.get(classe_id, [])

def get_armaduras_classe(classe_id):
    return ARMADURAS_POR_CLASSE.get(classe_id, [])

def get_ids_armas_classe(classe_id):
    return {a["id"] for a in ARMAS_POR_CLASSE.get(classe_id, [])}

def get_ids_armaduras_classe(classe_id):
    return {a["id"] for a in ARMADURAS_POR_CLASSE.get(classe_id, [])}

def get_skills_classe(classe_id):
    return SKILLS_COMPLETAS.get(classe_id, [])

def get_skill_by_id(skill_id):
    for classe, skills in SKILLS_COMPLETAS.items():
        for sk in skills:
            if sk["id"] == skill_id:
                return dict(sk, classe_origem=classe)
    return None

def get_bonus_arma(item_id, classe_id):
    armas = ARMAS_POR_CLASSE.get(classe_id, [])
    item = next((a for a in armas if a["id"] == item_id), None)
    if item:
        return item["atk_bonus"], True  # bonus, compativel
    # Busca em outras classes
    for cid, armas2 in ARMAS_POR_CLASSE.items():
        item2 = next((a for a in armas2 if a["id"] == item_id), None)
        if item2:
            return item2["atk_bonus"], False  # bonus, incompativel
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
PYEOF
echo "OK - $(wc -l < /mnt/user-data/outputs/catalogo.py) linhas"
