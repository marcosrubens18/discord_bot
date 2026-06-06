# data_armas.py — Todas as armas do jogo

ARMAS_POR_CLASSE = {
    "guerreiro": [
        {"id": "espada_ferro", "nome": "Espada de Ferro", "emoji": "⚔️", "raridade": "Comum", "atk_bonus": 5, "preco": 50, "venda": 25, "desc": "Arma inicial."},
        {"id": "machado_pesado", "nome": "Machado Pesado", "emoji": "🪓", "raridade": "Comum", "atk_bonus": 8, "preco": 120, "venda": 60, "desc": "Machado de ferro."},
        {"id": "espada_prata", "nome": "Espada de Prata", "emoji": "⚔️", "raridade": "Incomum", "atk_bonus": 12, "preco": 300, "venda": 150, "desc": "Forjada em prata."},
        {"id": "lanca_combate", "nome": "Lanca de Combate", "emoji": "🔱", "raridade": "Incomum", "atk_bonus": 10, "preco": 280, "venda": 140, "desc": "Alcance extra."},
        {"id": "espada_cavaleiro", "nome": "Espada do Cavaleiro", "emoji": "⚔️", "raridade": "Raro", "atk_bonus": 18, "preco": 700, "venda": 350, "desc": "Espada nobre."},
        {"id": "martelo_guerra", "nome": "Martelo de Guerra", "emoji": "🔨", "raridade": "Raro", "atk_bonus": 16, "preco": 650, "venda": 325, "desc": "15% chance atordoar."},
        {"id": "espada_orc", "nome": "Espada Orc", "emoji": "🗡️", "raridade": "Raro", "atk_bonus": 20, "preco": 1500, "venda": 750, "desc": "Forjada com metal orc."},
        {"id": "lanca_sagrada", "nome": "Lanca Sagrada", "emoji": "🔱", "raridade": "Epico", "atk_bonus": 25, "preco": 2500, "venda": 1250, "desc": "Abencada pelos deuses."},
        {"id": "espada_sombria", "nome": "Espada Sombria", "emoji": "🗡️", "raridade": "Epico", "atk_bonus": 28, "preco": 4000, "venda": 2000, "desc": "Drena HP ao acertar."},
        {"id": "espada_lendaria", "nome": "Espada do Heroi", "emoji": "⚔️", "raridade": "Lendario", "atk_bonus": 40, "preco": 10000, "venda": 5000, "desc": "Arma lendaria."},
    ],
    "arqueiro": [
        {"id": "arco_madeira", "nome": "Arco de Madeira", "emoji": "🏹", "raridade": "Comum", "atk_bonus": 4, "preco": 50, "venda": 25, "desc": "Arco inicial."},
        {"id": "besta_leve", "nome": "Besta Leve", "emoji": "🏹", "raridade": "Comum", "atk_bonus": 6, "preco": 100, "venda": 50, "desc": "Besta rapida."},
        {"id": "arco_composto", "nome": "Arco Composto", "emoji": "🏹", "raridade": "Incomum", "atk_bonus": 10, "preco": 260, "venda": 130, "desc": "Arco potente."},
        {"id": "besta_pesada", "nome": "Besta Pesada", "emoji": "🏹", "raridade": "Incomum", "atk_bonus": 12, "preco": 290, "venda": 145, "desc": "Dano perfurante."},
        {"id": "arco_elfico", "nome": "Arco Elfico", "emoji": "🏹", "raridade": "Raro", "atk_bonus": 15, "preco": 550, "venda": 275, "desc": "Critico +15%."},
        {"id": "arco_sombras", "nome": "Arco das Sombras", "emoji": "🏹", "raridade": "Raro", "atk_bonus": 18, "preco": 700, "venda": 350, "desc": "Flechas envenenadas."},
        {"id": "arco_encantado", "nome": "Arco Encantado", "emoji": "🏹", "raridade": "Raro", "atk_bonus": 20, "preco": 800, "venda": 400, "desc": "Critico +20%."},
        {"id": "besta_draconica", "nome": "Besta Draconica", "emoji": "🏹", "raridade": "Epico", "atk_bonus": 26, "preco": 1300, "venda": 650, "desc": "Flechas de fogo."},
        {"id": "arco_celestial", "nome": "Arco Celestial", "emoji": "🏹", "raridade": "Epico", "atk_bonus": 30, "preco": 1600, "venda": 800, "desc": "Critico +30%."},
        {"id": "arco_lendario", "nome": "Arco do Cacador", "emoji": "🏹", "raridade": "Lendario", "atk_bonus": 45, "preco": 10000, "venda": 5000, "desc": "Arco lendario."},
    ],
    "mago": [
        {"id": "cajado_pinho", "nome": "Cajado de Pinho", "emoji": "🪄", "raridade": "Comum", "atk_bonus": 4, "preco": 50, "venda": 25, "desc": "Cajado inicial."},
        {"id": "vara_magica", "nome": "Vara Magica", "emoji": "🪄", "raridade": "Comum", "atk_bonus": 6, "preco": 90, "venda": 45, "desc": "+5 mana."},
        {"id": "cajado_quartzo", "nome": "Cajado de Quartzo", "emoji": "🪄", "raridade": "Incomum", "atk_bonus": 10, "preco": 250, "venda": 125, "desc": "Amplifica magias."},
        {"id": "orbe_fogo", "nome": "Orbe de Fogo", "emoji": "🔮", "raridade": "Incomum", "atk_bonus": 11, "preco": 280, "venda": 140, "desc": "+10% dano fogo."},
        {"id": "cajado_magico", "nome": "Cajado Magico", "emoji": "🪄", "raridade": "Raro", "atk_bonus": 15, "preco": 600, "venda": 300, "desc": "Magia +10."},
        {"id": "tomo_arcano", "nome": "Tomo Arcano", "emoji": "📖", "raridade": "Raro", "atk_bonus": 16, "preco": 700, "venda": 350, "desc": "+15% dano magico."},
        {"id": "cajado_osso2", "nome": "Cajado Osseo+", "emoji": "💀", "raridade": "Raro", "atk_bonus": 17, "preco": 800, "venda": 400, "desc": "Amplifica magia negra."},
        {"id": "cajado_vazio", "nome": "Cajado do Vazio", "emoji": "🪄", "raridade": "Epico", "atk_bonus": 26, "preco": 1400, "venda": 700, "desc": "Ignora resistencias."},
        {"id": "orbe_arcano", "nome": "Orbe Arcano", "emoji": "🔮", "raridade": "Epico", "atk_bonus": 32, "preco": 1700, "venda": 850, "desc": "Magia +25."},
        {"id": "cajado_lendario", "nome": "Cajado do Arquimago", "emoji": "🪄", "raridade": "Lendario", "atk_bonus": 50, "preco": 10000, "venda": 5000, "desc": "Cajado lendario."},
    ],
    "paladino": [
        {"id": "maca_sagrada", "nome": "Maca Sagrada", "emoji": "⚡", "raridade": "Comum", "atk_bonus": 6, "preco": 50, "venda": 25, "desc": "Maca abencada."},
        {"id": "escudo_espada", "nome": "Espada e Escudo", "emoji": "⚔️", "raridade": "Comum", "atk_bonus": 5, "preco": 110, "venda": 55, "desc": "+5 DEF."},
        {"id": "lanca_prata", "nome": "Lanca de Prata", "emoji": "🔱", "raridade": "Incomum", "atk_bonus": 11, "preco": 270, "venda": 135, "desc": "Efetiva vs trevas."},
        {"id": "espada_prata_p", "nome": "Espada de Prata", "emoji": "⚔️", "raridade": "Incomum", "atk_bonus": 12, "preco": 300, "venda": 150, "desc": "Dano fisico e magico."},
        {"id": "maca_divina", "nome": "Maca Divina", "emoji": "⚡", "raridade": "Raro", "atk_bonus": 17, "preco": 680, "venda": 340, "desc": "20% atordoar."},
        {"id": "espada_luz", "nome": "Espada da Luz", "emoji": "⚔️", "raridade": "Raro", "atk_bonus": 19, "preco": 750, "venda": 375, "desc": "Sagrado +15."},
        {"id": "lanca_sagrada_p", "nome": "Lanca Sagrada", "emoji": "🔱", "raridade": "Raro", "atk_bonus": 20, "preco": 800, "venda": 400, "desc": "Lanca abencada."},
        {"id": "martelo_sagrado", "nome": "Martelo Sagrado", "emoji": "🔨", "raridade": "Epico", "atk_bonus": 27, "preco": 1350, "venda": 675, "desc": "+30 sagrado."},
        {"id": "espada_justica", "nome": "Espada da Justica", "emoji": "⚔️", "raridade": "Epico", "atk_bonus": 32, "preco": 1800, "venda": 900, "desc": "Espada divina."},
        {"id": "espada_cruzada", "nome": "Espada da Cruzada", "emoji": "⚔️", "raridade": "Lendario", "atk_bonus": 46, "preco": 10000, "venda": 5000, "desc": "Arma lendaria."},
    ],
    "necromante": [
        {"id": "cajado_osso", "nome": "Cajado de Osso", "emoji": "💀", "raridade": "Comum", "atk_bonus": 4, "preco": 50, "venda": 25, "desc": "Amplifica magia negra."},
        {"id": "foice_ferrugem", "nome": "Foice Enferrujada", "emoji": "⚰️", "raridade": "Comum", "atk_bonus": 6, "preco": 95, "venda": 47, "desc": "Sangramento."},
        {"id": "cajado_sombra", "nome": "Cajado das Sombras", "emoji": "💀", "raridade": "Incomum", "atk_bonus": 10, "preco": 240, "venda": 120, "desc": "+10% dreno."},
        {"id": "foice_arcana", "nome": "Foice Arcana", "emoji": "⚰️", "raridade": "Incomum", "atk_bonus": 12, "preco": 280, "venda": 140, "desc": "Drena vida."},
        {"id": "cajado_osso2_n", "nome": "Cajado Osseo+", "emoji": "💀", "raridade": "Raro", "atk_bonus": 16, "preco": 750, "venda": 375, "desc": "Magia negra +20."},
        {"id": "corvo_espirito", "nome": "Bastao do Corvo", "emoji": "🦅", "raridade": "Raro", "atk_bonus": 17, "preco": 720, "venda": 360, "desc": "Invoca corvos."},
        {"id": "cajado_lich", "nome": "Cajado do Lich", "emoji": "💀", "raridade": "Raro", "atk_bonus": 19, "preco": 800, "venda": 400, "desc": "Poder sombrio."},
        {"id": "foice_morte", "nome": "Foice da Morte", "emoji": "⚰️", "raridade": "Epico", "atk_bonus": 28, "preco": 1400, "venda": 700, "desc": "Dreno massivo."},
        {"id": "cetro_lich", "nome": "Cetro do Lich", "emoji": "💀", "raridade": "Epico", "atk_bonus": 32, "preco": 1600, "venda": 800, "desc": "+30% dano necrotico."},
        {"id": "cajado_sombra_l", "nome": "Cajado das Trevas", "emoji": "💀", "raridade": "Lendario", "atk_bonus": 47, "preco": 10000, "venda": 5000, "desc": "Artefato das trevas."},
    ],
    "dracomante": [
        {"id": "garra_dragao", "nome": "Garra de Dragao", "emoji": "🐉", "raridade": "Lendario", "atk_bonus": 52, "preco": 8000, "venda": 4000, "desc": "Arma lendaria de dragao."},
        {"id": "espada_dragao", "nome": "Espada do Dragao", "emoji": "⚔️", "raridade": "Lendario", "atk_bonus": 38, "preco": 9000, "venda": 4500, "desc": "Flamejante eternamente."},
        {"id": "cajado_dragao", "nome": "Cajado do Dragao", "emoji": "🪄", "raridade": "Lendario", "atk_bonus": 42, "preco": 9500, "venda": 4750, "desc": "Poder draconico."},
    ],
    "arcano": [
        {"id": "orbe_arcano", "nome": "Orbe Arcano", "emoji": "🔮", "raridade": "Epico", "atk_bonus": 32, "preco": 1700, "venda": 850, "desc": "Magia +25."},
        {"id": "cajado_vazio", "nome": "Cajado do Vazio", "emoji": "🪄", "raridade": "Epico", "atk_bonus": 26, "preco": 1400, "venda": 700, "desc": "Ignora resistencias."},
        {"id": "cajado_lendario", "nome": "Cajado do Arquimago", "emoji": "🪄", "raridade": "Lendario", "atk_bonus": 48, "preco": 10000, "venda": 5000, "desc": "Cajado lendario."},
    ],
}


def get_armas_classe(classe_id):
    return ARMAS_POR_CLASSE.get(classe_id, [])


def get_bonus_arma(item_id, classe_id):
    """Retorna o bônus de ATK da arma e se é compatível com a classe"""
    armas = ARMAS_POR_CLASSE.get(classe_id, [])
    item = next((a for a in armas if a["id"] == item_id), None)
    if item:
        return item["atk_bonus"], True
    # Verifica em outras classes para saber se é compatível ou não
    for cid, armas2 in ARMAS_POR_CLASSE.items():
        item2 = next((a for a in armas2 if a["id"] == item_id), None)
        if item2:
            return item2["atk_bonus"], False
    return 0, None
