# data/skills.py — Todas as skills do jogo

# ==================================================
# SKILLS COMPLETAS (para compatibilidade com batalha.py)
# ==================================================

SKILLS_COMPLETAS = {
    "guerreiro": [
        {"id":"golpe_basico",  "nome":"Golpe Basico",  "nivel":1,  "emoji":"⚔️","dano":1.3,"mana":0, "desc":"Ataque fisico direto.", "efeito":None},
        {"id":"escudo",        "nome":"Postura de Escudo","nivel":3,"emoji":"🛡️","dano":0,  "mana":8, "desc":"Reduz 50% do dano recebido.", "efeito":"defesa"},
        {"id":"golpe_brutal",  "nome":"Golpe Brutal",   "nivel":8, "emoji":"💥","dano":2.2,"mana":18,"desc":"Golpe devastador.", "efeito":None},
        {"id":"investida",     "nome":"Investida",       "nivel":12,"emoji":"🏃","dano":1.4,"mana":15,"desc":"30% chance atordoar.", "efeito":"atordoar"},
        {"id":"grito_guerra",  "nome":"Grito de Guerra", "nivel":16,"emoji":"😤","dano":0,  "mana":22,"desc":"+35% de ataque por 3 turnos.", "efeito":"buff_ataque"},
        {"id":"lamina_girat",  "nome":"Lamina Giratoria","nivel":20,"emoji":"🌀","dano":1.8,"mana":28,"desc":"2 golpes consecutivos.", "efeito":"hits2"},
        {"id":"escudo_aco",    "nome":"Escudo de Aco",   "nivel":28,"emoji":"🪨","dano":0,  "mana":35,"desc":"Escudo impenetravel por 2 turnos.", "efeito":"escudo_total"},
        {"id":"furia",         "nome":"Furia Berserker", "nivel":35,"emoji":"🔥","dano":2.5,"mana":40,"desc":"+60% ATK, regenera vida.", "efeito":"berserker"},
        {"id":"golpe_final",   "nome":"Golpe Final",     "nivel":45,"emoji":"💢","dano":3.5,"mana":50,"desc":"Ignora 50% defesa.", "efeito":None},
        {"id":"lendario_atk",  "nome":"Golpe Lendario",  "nivel":70,"emoji":"⚡","dano":5.0,"mana":80,"desc":"Golpe lendario.", "efeito":None},
    ],
    "arqueiro": [
        {"id":"tiro_preciso",  "nome":"Tiro Preciso",   "nivel":1, "emoji":"🎯","dano":1.3,"mana":0, "desc":"+40% critico.", "efeito":"critico_bonus"},
        {"id":"tiro_rapido",   "nome":"Tiro Rapido",    "nivel":3, "emoji":"💨","dano":0.8,"mana":5, "desc":"2 tiros rapidos.", "efeito":"hits2"},
        {"id":"esquiva",       "nome":"Esquiva",        "nivel":5, "emoji":"💨","dano":0,  "mana":15,"desc":"Evita proximo ataque.", "efeito":"esquiva"},
        {"id":"flecha_veneno", "nome":"Flecha Venenosa","nivel":10,"emoji":"🟢","dano":1.1,"mana":18,"desc":"Veneno 3 turnos.", "efeito":"veneno"},
        {"id":"tiro_multiplo", "nome":"Tiro Multiplo",  "nivel":14,"emoji":"🏹","dano":0.7,"mana":22,"desc":"3 flechas.", "efeito":"hits3"},
        {"id":"flecha_perfurante","nome":"Flecha Perfurante","nivel":20,"emoji":"🔱","dano":2.0,"mana":30,"desc":"Ignora 60% defesa.", "efeito":"ignorar_defesa"},
        {"id":"chuva_flechas", "nome":"Chuva de Flechas","nivel":28,"emoji":"☄️","dano":0.5,"mana":40,"desc":"5 flechas.", "efeito":"hits5"},
        {"id":"tiro_fantasma", "nome":"Tiro Fantasma",  "nivel":35,"emoji":"👻","dano":2.5,"mana":50,"desc":"Ignora 100% defesa.", "efeito":"ignorar_defesa"},
    ],
    "mago": [
        {"id":"bola_fogo",     "nome":"Bola de Fogo",   "nivel":1, "emoji":"🔥","dano":1.3,"mana":12,"desc":"25% chance queimadura.", "efeito":"queimadura"},
        {"id":"missil_arcano", "nome":"Missil Arcano",  "nivel":3, "emoji":"✨","dano":1.1,"mana":6, "desc":"3 misseis.", "efeito":"hits3"},
        {"id":"escudo_arcano", "nome":"Escudo Arcano",  "nivel":6, "emoji":"💜","dano":0,  "mana":20,"desc":"Absorve proximo ataque.", "efeito":"escudo"},
        {"id":"raio_congelante","nome":"Raio Congelante","nivel":10,"emoji":"❄️","dano":1.5,"mana":22,"desc":"40% chance congelar.", "efeito":"congelar"},
        {"id":"tempestade",    "nome":"Tempestade",     "nivel":16,"emoji":"⚡","dano":1.7,"mana":35,"desc":"35% chance paralisar.", "efeito":"paralisia"},
        {"id":"meteor",        "nome":"Meteoro",         "nivel":24,"emoji":"☄️","dano":2.8,"mana":45,"desc":"Dano massivo.", "efeito":None},
        {"id":"campo_forca",   "nome":"Campo de Forca", "nivel":28,"emoji":"🔮","dano":0,  "mana":30,"desc":"Reflete 40% do dano.", "efeito":"reflexo"},
        {"id":"sobrecarga",    "nome":"Sobrecarga",      "nivel":35,"emoji":"🌟","dano":3.5,"mana":60,"desc":"Dano devastador.", "efeito":None},
        {"id":"chuva_meteoros","nome":"Chuva de Meteoros","nivel":50,"emoji":"💥","dano":4.0,"mana":70,"desc":"Multiplos meteoros.", "efeito":"hits3"},
        {"id":"singularidade_m","nome":"Singularidade",  "nivel":70,"emoji":"🌌","dano":7.0,"mana":100,"desc":"Dano absoluto.", "efeito":None},
    ],
    "paladino": [
        {"id":"golpe_sagrado", "nome":"Golpe Sagrado",  "nivel":1, "emoji":"⚡","dano":1.2,"mana":10,"desc":"Ataque sagrado.", "efeito":None},
        {"id":"cura",          "nome":"Cura",           "nivel":3, "emoji":"💚","dano":0,  "mana":25,"desc":"Cura 35% HP.", "efeito":"cura"},
        {"id":"martelo_sagrado","nome":"Martelo Sagrado","nivel":8, "emoji":"🔨","dano":1.6,"mana":20,"desc":"40% atordoar.", "efeito":"atordoar"},
        {"id":"aura_sagrada",  "nome":"Aura Sagrada",   "nivel":14,"emoji":"🌟","dano":0,  "mana":30,"desc":"+25% ATK/DEF, regen 5% HP.", "efeito":"buff_all"},
        {"id":"escudo_divino", "nome":"Escudo Divino",  "nivel":20,"emoji":"🛡️","dano":0,  "mana":35,"desc":"Bloqueia 2 ataques.", "efeito":"escudo_total"},
        {"id":"cura_area",     "nome":"Cura em Area",   "nivel":25,"emoji":"💗","dano":0,  "mana":45,"desc":"Cura 60% HP.", "efeito":"cura_grande"},
        {"id":"ressureicao",   "nome":"Ressurreição",   "nivel":32,"emoji":"✝️","dano":0,  "mana":40,"desc":"Revive com 60% HP.", "efeito":"ressurreicao"},
        {"id":"juizo_final",   "nome":"Juizo Final",    "nivel":35,"emoji":"☀️","dano":3.0,"mana":60,"desc":"Escala com HP perdido.", "efeito":"sagrado_bonus"},
    ],
    "necromante": [
        {"id":"drenar_vida",   "nome":"Drenar Vida",    "nivel":1, "emoji":"🌑","dano":1.1,"mana":10,"desc":"Drena 50% do dano.", "efeito":"dreno"},
        {"id":"maldicao",      "nome":"Maldicao",       "nivel":4, "emoji":"🩸","dano":0.8,"mana":8, "desc":"Veneno 4 turnos.", "efeito":"veneno"},
        {"id":"invocar_morto", "nome":"Invocar Morto",  "nivel":8, "emoji":"💀","dano":0.9,"mana":20,"desc":"Invoca esqueleto.", "efeito":None},
        {"id":"toque_necrotico","nome":"Toque Necrotico","nivel":12,"emoji":"☠️","dano":1.4,"mana":25,"desc":"-20% ATK inimigo.", "efeito":"enfraquecer"},
        {"id":"onda_sombria",  "nome":"Onda Sombria",   "nivel":18,"emoji":"🌊","dano":1.8,"mana":35,"desc":"Drena 30 mana.", "efeito":"drenar_mana"},
        {"id":"banshee",       "nome":"Grito da Banshee","nivel":24,"emoji":"👻","dano":1.5,"mana":40,"desc":"-30% ATK inimigo.", "efeito":"terror"},
        {"id":"exercito_mortos","nome":"Exercito Mortos","nivel":30,"emoji":"💀","dano":2.2,"mana":55,"desc":"3 ataques.", "efeito":"hits3"},
        {"id":"abraço_morte",  "nome":"Abraço da Morte","nivel":35,"emoji":"💀","dano":1.0,"mana":65,"desc":"20% instakill.", "efeito":"instakill_chance"},
    ],
    "dracomante": [
        {"id":"baforada",      "nome":"Baforada",       "nivel":1, "emoji":"🔥","dano":1.6,"mana":12,"desc":"Queimadura 2 turnos.", "efeito":"queimadura"},
        {"id":"garra_dragao",  "nome":"Garra do Dragão","nivel":4, "emoji":"🐾","dano":1.2,"mana":10,"desc":"Ataque fisico.", "efeito":None},
        {"id":"escamas_dragao","nome":"Escamas do Dragão","nivel":8,"emoji":"🐉","dano":0,  "mana":20,"desc":"-35% dano 3 turnos.", "efeito":"armadura"},
        {"id":"rugido_dragao", "nome":"Rugido do Dragão","nivel":14,"emoji":"😤","dano":0,  "mana":18,"desc":"-40% ATK inimigo.", "efeito":"terror"},
        {"id":"cauda_dragao",  "nome":"Chicote de Cauda","nivel":18,"emoji":"🌪️","dano":1.6,"mana":25,"desc":"45% atordoar.", "efeito":"atordoar"},
        {"id":"voo_dragao",    "nome":"Voo do Dragão",  "nivel":22,"emoji":"🦅","dano":0,  "mana":30,"desc":"Esquiva por 1 turno.", "efeito":"esquiva"},
        {"id":"forma_menor",   "nome":"Forma Menor do Dragão","nivel":28,"emoji":"🌋","dano":0,"mana":45,"desc":"+40% ATK/DEF, regen.", "efeito":"buff_all"},
        {"id":"dragao_eterno", "nome":"Dragão Eterno",  "nivel":35,"emoji":"💎","dano":4.0,"mana":70,"desc":"Forma completa.", "efeito":None},
        {"id":"chamas_ancestrais","nome":"Chamas Ancestrais","nivel":45,"emoji":"🌋","dano":3.0,"mana":45,"desc":"Queimadura garantida 3 turnos.","efeito":"queimadura"},
        {"id":"coracao_dragao","nome":"Coracao de Dragao","nivel":60,"emoji":"❤️‍🔥","dano":0,"mana":50,"desc":"+50% ATK/DEF, regen 8% HP 4 turnos.","efeito":"buff_all"},
    ],
    "arcano": [
        {"id":"faisca_arcana", "nome":"Faisca Arcana", "nivel":1, "emoji":"✨","dano":1.2,"mana":8, "desc":"Energia arcana.", "efeito":None},
        {"id":"distorcao",     "nome":"Distorcao",     "nivel":4, "emoji":"🌀","dano":1.1,"mana":12,"desc":"-50% precisao.", "efeito":"confusao"},
        {"id":"campo_forca_arcano","nome":"Campo de Forca","nivel":6,"emoji":"🔮","dano":0,"mana":22,"desc":"Reflete 30% dano.", "efeito":"reflexo"},
        {"id":"explosao_arcana","nome":"Explosao Arcana","nivel":10,"emoji":"💥","dano":2.0,"mana":28,"desc":"Dano massivo.", "efeito":None},
        {"id":"teletransporte","nome":"Teletransporte","nivel":15,"emoji":"🌟","dano":1.5,"mana":25,"desc":"Ignora defesa.", "efeito":"ignorar_defesa"},
        {"id":"drenar_magia",  "nome":"Drenar Magia",   "nivel":20,"emoji":"💜","dano":1.0,"mana":0, "desc":"Drena 40 mana.", "efeito":"drenar_mana"},
        {"id":"tempestade_arcana","nome":"Tempestade Arcana","nivel":26,"emoji":"⭐","dano":2.5,"mana":55,"desc":"4 ataques.", "efeito":"hits4"},
        {"id":"singularidade", "nome":"Singularidade",  "nivel":35,"emoji":"🕳️","dano":4.5,"mana":60,"desc":"Perde 30% da mana restante.", "efeito":"singularidade_v2"},
    ],
}


# ==================================================
# FUNÇÕES AUXILIARES
# ==================================================

def get_skill_by_id(skill_id):
    """Retorna uma skill pelo ID"""
    for classe, skills in SKILLS_COMPLETAS.items():
        for skill in skills:
            if skill["id"] == skill_id:
                return {**skill, "classe_origem": classe}
    return None

def get_skills_classe(classe_id):
    """Retorna todas as skills de uma classe"""
    return SKILLS_COMPLETAS.get(classe_id, [])