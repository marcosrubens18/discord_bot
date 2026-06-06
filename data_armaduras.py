# data_armaduras.py — Todas as armaduras do jogo

ARMADURAS_POR_CLASSE = {
    "guerreiro": [
        {"id": "armadura_couro", "nome": "Armadura de Couro", "emoji": "🥋", "raridade": "Comum", "def_bonus": 5, "preco": 50, "venda": 25, "desc": "Armadura inicial."},
        {"id": "cota_malha_g", "nome": "Cota de Malha", "emoji": "🛡️", "raridade": "Comum", "def_bonus": 8, "preco": 150, "venda": 75, "desc": "Malha de ferro."},
        {"id": "armadura_ferro", "nome": "Armadura de Ferro", "emoji": "⚙️", "raridade": "Incomum", "def_bonus": 13, "preco": 350, "venda": 175, "desc": "Armadura completa."},
        {"id": "escudo_torre", "nome": "Escudo Torre", "emoji": "🛡️", "raridade": "Incomum", "def_bonus": 15, "preco": 380, "venda": 190, "desc": "Escudo gigante."},
        {"id": "armadura_plena", "nome": "Armadura Plena", "emoji": "⚙️", "raridade": "Raro", "def_bonus": 20, "preco": 900, "venda": 450, "desc": "Cobertura total."},
        {"id": "cota_aco", "nome": "Cota de Aco", "emoji": "🛡️", "raridade": "Raro", "def_bonus": 22, "preco": 950, "venda": 475, "desc": "Malha de aco."},
        {"id": "armadura_runa", "nome": "Armadura Runada", "emoji": "⚙️", "raridade": "Raro", "def_bonus": 25, "preco": 1100, "venda": 550, "desc": "Runas de protecao."},
        {"id": "armadura_cavaleiro", "nome": "Armadura do Cavaleiro", "emoji": "⚙️", "raridade": "Epico", "def_bonus": 32, "preco": 1500, "venda": 750, "desc": "Armadura lendaria."},
        {"id": "armadura_titan", "nome": "Armadura do Titan", "emoji": "🗿", "raridade": "Epico", "def_bonus": 38, "preco": 2500, "venda": 1250, "desc": "+20% HP max."},
        {"id": "armadura_heroi", "nome": "Armadura do Heroi", "emoji": "⚙️", "raridade": "Lendario", "def_bonus": 55, "preco": 10000, "venda": 5000, "desc": "Armadura definitiva."},
    ],
    "arqueiro": [
        {"id": "armadura_couro", "nome": "Armadura de Couro", "emoji": "🥋", "raridade": "Comum", "def_bonus": 5, "preco": 50, "venda": 25, "desc": "Armadura inicial."},
        {"id": "cota_malha_g", "nome": "Cota de Malha", "emoji": "🛡️", "raridade": "Comum", "def_bonus": 8, "preco": 150, "venda": 75, "desc": "Malha de ferro."},
        {"id": "armadura_escamas", "nome": "Armadura de Escamas", "emoji": "🐉", "raridade": "Raro", "def_bonus": 18, "preco": 800, "venda": 400, "desc": "Escamas leves."},
    ],
    "mago": [
        {"id": "robe_algodao", "nome": "Robe de Algodao", "emoji": "👘", "raridade": "Comum", "def_bonus": 4, "preco": 50, "venda": 25, "desc": "Robe simples."},
        {"id": "manto_aprendiz", "nome": "Manto do Aprendiz", "emoji": "🧥", "raridade": "Incomum", "def_bonus": 5, "preco": 200, "venda": 100, "desc": "+10 mana."},
        {"id": "manto_arquimago", "nome": "Manto do Arquimago", "emoji": "🧥", "raridade": "Raro", "def_bonus": 22, "preco": 600, "venda": 300, "desc": "+20 mana."},
        {"id": "robe_vazio", "nome": "Robe do Vazio", "emoji": "👘", "raridade": "Epico", "def_bonus": 28, "preco": 1400, "venda": 700, "desc": "Magia +25."},
    ],
    "paladino": [
        {"id": "armadura_plena", "nome": "Armadura Plena", "emoji": "⚙️", "raridade": "Raro", "def_bonus": 20, "preco": 900, "venda": 450, "desc": "Cobertura total."},
        {"id": "armadura_escama", "nome": "Armadura de Escama", "emoji": "🐉", "raridade": "Epico", "def_bonus": 28, "preco": 1800, "venda": 900, "desc": "Escamas de dragao."},
        {"id": "armadura_titan", "nome": "Armadura do Titan", "emoji": "🗿", "raridade": "Lendario", "def_bonus": 45, "preco": 10000, "venda": 5000, "desc": "Protecao maxima."},
    ],
    "necromante": [
        {"id": "armadura_couro", "nome": "Armadura de Couro", "emoji": "🥋", "raridade": "Comum", "def_bonus": 5, "preco": 50, "venda": 25, "desc": "Armadura inicial."},
        {"id": "capa_vampiro", "nome": "Capa do Vampiro", "emoji": "🧛", "raridade": "Raro", "def_bonus": 12, "preco": 700, "venda": 350, "desc": "Drena 5% HP ao atacar."},
        {"id": "armadura_ossos", "nome": "Armadura de Ossos", "emoji": "💀", "raridade": "Epico", "def_bonus": 20, "preco": 1500, "venda": 750, "desc": "Defesa osssea."},
    ],
    "dracomante": [
        {"id": "armadura_escama", "nome": "Armadura de Escama", "emoji": "🐉", "raridade": "Epico", "def_bonus": 28, "preco": 1800, "venda": 900, "desc": "Escamas de dragao."},
        {"id": "elmo_dragao", "nome": "Elmo do Dragao", "emoji": "🪖", "raridade": "Lendario", "def_bonus": 35, "preco": 5000, "venda": 2500, "desc": "Protecao draconica."},
        {"id": "armadura_dragao", "nome": "Armadura do Dragao", "emoji": "🐉", "raridade": "Lendario", "def_bonus": 50, "preco": 12000, "venda": 6000, "desc": "Armadura definitiva."},
    ],
    "arcano": [
        {"id": "armadura_couro", "nome": "Armadura de Couro", "emoji": "🥋", "raridade": "Comum", "def_bonus": 5, "preco": 50, "venda": 25, "desc": "Armadura inicial."},
        {"id": "cota_malha_g", "nome": "Cota de Malha", "emoji": "🛡️", "raridade": "Comum", "def_bonus": 8, "preco": 150, "venda": 75, "desc": "Malha de ferro."},
        {"id": "tunica_arcana", "nome": "Tunica Arcana", "emoji": "👘", "raridade": "Raro", "def_bonus": 10, "preco": 600, "venda": 300, "desc": "+20 mana."},
    ],
}


def get_armaduras_classe(classe_id):
    """Retorna as armaduras disponíveis para a classe"""
    return ARMADURAS_POR_CLASSE.get(classe_id, [])


def get_bonus_armadura(item_id, classe_id):
    """Retorna o bônus de DEF da armadura e se é compatível com a classe"""
    armaduras = ARMADURAS_POR_CLASSE.get(classe_id, [])
    item = next((a for a in armaduras if a["id"] == item_id), None)
    if item:
        return item["def_bonus"], True
    # Verifica em outras classes para saber se o item existe
    for cid, armaduras2 in ARMADURAS_POR_CLASSE.items():
        item2 = next((a for a in armaduras2 if a["id"] == item_id), None)
        if item2:
            return item2["def_bonus"], False
    return 0, None