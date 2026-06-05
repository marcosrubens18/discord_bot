# data/itens.py — Poções, materiais e itens do jogo

# ==================================================
# POÇÕES
# ==================================================

POCOES_CAT = [
    {"id":"pocao_hp_p", "nome":"Pocao de Cura P", "emoji":"🧪", "tipo":"pocao", "raridade":"Comum", "desc":"Recupera 30 HP", "preco":30, "venda":15, "valor":30},
    {"id":"pocao_hp_m", "nome":"Pocao de Cura M", "emoji":"💊", "tipo":"pocao", "raridade":"Comum", "desc":"Recupera 60 HP", "preco":60, "venda":30, "valor":60},
    {"id":"pocao_hp_g", "nome":"Pocao de Cura G", "emoji":"❤️", "tipo":"pocao", "raridade":"Raro", "desc":"Recupera 120 HP", "preco":120, "venda":60, "valor":120},
    {"id":"pocao_mana_p", "nome":"Pocao de Mana P", "emoji":"🔵", "tipo":"pocao", "raridade":"Comum", "desc":"Recupera 20 Mana", "preco":25, "venda":12, "valor":20},
    {"id":"pocao_mana_m", "nome":"Pocao de Mana M", "emoji":"💙", "tipo":"pocao", "raridade":"Incomum", "desc":"Recupera 50 Mana", "preco":55, "venda":27, "valor":50},
    {"id":"elixir", "nome":"Elixir Supremo", "emoji":"✨", "tipo":"pocao", "raridade":"Epico", "desc":"HP e Mana full", "preco":300, "venda":150, "valor":999},
]

POCOES_BATALHA = {
    "pocao_hp_p": {"nome": "Pocao de Cura P", "emoji": "🧪", "tipo": "hp", "valor": 30, "preco": 50},
    "pocao_hp_m": {"nome": "Pocao de Cura M", "emoji": "💊", "tipo": "hp", "valor": 60, "preco": 100},
    "pocao_hp_g": {"nome": "Pocao de Cura G", "emoji": "❤️", "tipo": "hp", "valor": 120, "preco": 200},
    "pocao_mana_p": {"nome": "Pocao de Mana P", "emoji": "🔵", "tipo": "mana", "valor": 20, "preco": 60},
    "pocao_mana_m": {"nome": "Pocao de Mana M", "emoji": "💙", "tipo": "mana", "valor": 50, "preco": 120},
    "elixir": {"nome": "Elixir Supremo", "emoji": "✨", "tipo": "full", "valor": 999, "preco": 500},
}

# ==================================================
# MATERIAIS
# ==================================================

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

# ==================================================
# CATÁLOGO COMPLETO (todos os itens)
# ==================================================

def get_catalogo_completo():
    """Retorna todos os itens do catálogo (armas, armaduras, poções, materiais)"""
    from data.armas import ARMAS_POR_CLASSE
    from data.armaduras import ARMADURAS_POR_CLASSE
    
    todos = []
    
    # Armas
    for cls, armas in ARMAS_POR_CLASSE.items():
        for a in armas:
            todos.append({
                "chave": f"arma:{cls}:{a['id']}",
                "id": a["id"], "nome": a["nome"],
                "emoji": a.get("emoji", "⚔️"), "tipo": "arma",
                "raridade": a["raridade"], "classe": cls,
                "desc": a.get("desc", ""), "preco": a.get("preco", 0), "venda": a.get("venda", 0)
            })
    
    # Armaduras
    for cls, arms in ARMADURAS_POR_CLASSE.items():
        for a in arms:
            todos.append({
                "chave": f"armadura:{cls}:{a['id']}",
                "id": a["id"], "nome": a["nome"],
                "emoji": a.get("emoji", "🛡️"), "tipo": "armadura",
                "raridade": a["raridade"], "classe": cls,
                "desc": a.get("desc", ""), "preco": a.get("preco", 0), "venda": a.get("venda", 0)
            })
    
    # Poções
    for p in POCOES_CAT:
        todos.append({**p, "chave": f"pocao::{p['id']}", "classe": "", "preco": p["preco"], "venda": p["venda"]})
    
    # Materiais
    for m in MATERIAIS_CAT:
        todos.append({**m, "chave": f"material::{m['id']}", "classe": "", "preco": m.get("preco", 0), "venda": m.get("venda", 0)})
    
    return todos


def get_item_por_chave(chave: str):
    for it in get_catalogo_completo():
        if it["chave"] == chave:
            return it
    return None


def get_itens_por_categoria(categoria: str):
    todos = get_catalogo_completo()
    cat_map = {
        "pocoes": [i for i in todos if i["tipo"] == "pocao"],
        "arma_guerreiro": [i for i in todos if i["tipo"] == "arma" and i["classe"] == "guerreiro"],
        "arma_arqueiro": [i for i in todos if i["tipo"] == "arma" and i["classe"] == "arqueiro"],
        "arma_mago": [i for i in todos if i["tipo"] == "arma" and i["classe"] == "mago"],
        "arma_paladino": [i for i in todos if i["tipo"] == "arma" and i["classe"] == "paladino"],
        "arma_necromante": [i for i in todos if i["tipo"] == "arma" and i["classe"] == "necromante"],
        "arma_dracomante": [i for i in todos if i["tipo"] == "arma" and i["classe"] == "dracomante"],
        "arma_arcano": [i for i in todos if i["tipo"] == "arma" and i["classe"] == "arcano"],
        "arm_guerreiro": [i for i in todos if i["tipo"] == "armadura" and i["classe"] == "guerreiro"],
        "arm_arqueiro": [i for i in todos if i["tipo"] == "armadura" and i["classe"] == "arqueiro"],
        "arm_mago": [i for i in todos if i["tipo"] == "armadura" and i["classe"] == "mago"],
        "arm_paladino": [i for i in todos if i["tipo"] == "armadura" and i["classe"] == "paladino"],
        "arm_necromante": [i for i in todos if i["tipo"] == "armadura" and i["classe"] == "necromante"],
        "arm_dracomante": [i for i in todos if i["tipo"] == "armadura" and i["classe"] == "dracomante"],
        "arm_arcano": [i for i in todos if i["tipo"] == "armadura" and i["classe"] == "arcano"],
        "materiais": [i for i in todos if i["tipo"] == "material"],
    }
    return cat_map.get(categoria, todos)