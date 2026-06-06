# data_dungeons.py — Dados de todas as dungeons (Ranks F a SS)

RANKS_DUNGEON = {
    "F": {
        "nome": "Dungeon Rank F", "rank_min": "F", "emoji": "🟫", "nivel_min": 1, "cor": 0x888780,
        "desc": "Para iniciantes. Monstros fracos mas boa fonte de XP.",
        "recompensa_andar": {"xp": 30, "moedas": 15},
        "recompensa_chefe": {"xp": 150, "moedas": 80},
        "andares": [
            {"andar": 1, "nome": "Caverna Rasa", "emoji": "🕳️", "monstro": {"nome": "Goblin", "emoji": "👺", "hp": 90, "ataque": 19, "defesa": 2}},
            {"andar": 2, "nome": "Floresta Escura", "emoji": "🌲", "monstro": {"nome": "Lobo Selvagem", "emoji": "🐺", "hp": 126, "ataque": 30, "defesa": 4}},
            {"andar": 3, "nome": "Pântano Podre", "emoji": "🌿", "monstro": {"nome": "Sapo Gigante", "emoji": "🐸", "hp": 153, "ataque": 24, "defesa": 6}},
            {"andar": 4, "nome": "Ruínas Abandonadas", "emoji": "🏚️", "monstro": {"nome": "Esqueleto", "emoji": "💀", "hp": 171, "ataque": 35, "defesa": 5}},
            {"andar": 5, "nome": "Salão das Sombras", "emoji": "🌑", "monstro": {"nome": "Sombra Menor", "emoji": "👤", "hp": 198, "ataque": 41, "defesa": 7}},
        ],
        "chefe": {"nome": "Rei Goblin", "emoji": "👑", "hp": 250, "ataque": 44, "defesa": 10},
    },
    "E": {
        "nome": "Dungeon Rank E", "rank_min": "E", "emoji": "🟩", "nivel_min": 5, "cor": 0x1D9E75,
        "desc": "Monstros com habilidades especiais. Requer preparo.",
        "recompensa_andar": {"xp": 60, "moedas": 30},
        "recompensa_chefe": {"xp": 300, "moedas": 180},
        "andares": [
            {"andar": 1, "nome": "Mina Abandonada", "emoji": "⛏️", "monstro": {"nome": "Orc Minerador", "emoji": "👹", "hp": 221, "ataque": 48, "defesa": 10}},
            {"andar": 2, "nome": "Floresta Maldita", "emoji": "🌳", "monstro": {"nome": "Treant", "emoji": "🌳", "hp": 272, "ataque": 39, "defesa": 18}},
            {"andar": 3, "nome": "Lago Envenenado", "emoji": "💧", "monstro": {"nome": "Hidra", "emoji": "🐍", "hp": 306, "ataque": 59, "defesa": 12}},
            {"andar": 4, "nome": "Fortaleza em Ruinas", "emoji": "🏰", "monstro": {"nome": "Golem de Pedra", "emoji": "🗿", "hp": 374, "ataque": 55, "defesa": 25}},
            {"andar": 5, "nome": "Câmara Proibida", "emoji": "🚪", "monstro": {"nome": "Feiticeiro Renegado", "emoji": "🧙", "hp": 340, "ataque": 77, "defesa": 10}},
        ],
        "chefe": {"nome": "Senhor das Trevas", "emoji": "🧛", "hp": 500, "ataque": 77, "defesa": 20},
    },
    "D": {
        "nome": "Dungeon Rank D", "rank_min": "D", "emoji": "🟦", "nivel_min": 10, "cor": 0x378ADD,
        "desc": "Perigo real. Venha preparado com pocoes.",
        "recompensa_andar": {"xp": 100, "moedas": 55},
        "recompensa_chefe": {"xp": 500, "moedas": 350},
        "andares": [
            {"andar": 1, "nome": "Cripta Antiga", "emoji": "⚰️", "monstro": {"nome": "Lich Menor", "emoji": "💀", "hp": 400, "ataque": 79, "defesa": 15}},
            {"andar": 2, "nome": "Vulcão Ativo", "emoji": "🌋", "monstro": {"nome": "Elemental de Fogo", "emoji": "🔥", "hp": 448, "ataque": 92, "defesa": 12}},
            {"andar": 3, "nome": "Abismo Gelado", "emoji": "❄️", "monstro": {"nome": "Yeti", "emoji": "🦴", "hp": 512, "ataque": 72, "defesa": 28}},
            {"andar": 4, "nome": "Floresta Sangrenta", "emoji": "🌹", "monstro": {"nome": "Vampiro Anciao", "emoji": "🧛", "hp": 560, "ataque": 105, "defesa": 20}},
            {"andar": 5, "nome": "Torre do Caos", "emoji": "🗼", "monstro": {"nome": "Mago do Caos", "emoji": "🌀", "hp": 608, "ataque": 118, "defesa": 15}},
        ],
        "chefe": {"nome": "Hidra das Profundezas", "emoji": "🐲", "hp": 900, "ataque": 121, "defesa": 30},
    },
    "C": {
        "nome": "Dungeon Rank C", "rank_min": "C", "emoji": "🟨", "nivel_min": 20, "cor": 0xE4AF3C,
        "desc": "Apenas guerreiros experientes sobrevivem aqui.",
        "recompensa_andar": {"xp": 180, "moedas": 100},
        "recompensa_chefe": {"xp": 900, "moedas": 600},
        "andares": [
            {"andar": 1, "nome": "Cemitério Amaldicoado", "emoji": "🪦", "monstro": {"nome": "Banshee", "emoji": "👻", "hp": 600, "ataque": 132, "defesa": 20}},
            {"andar": 2, "nome": "Pântano Demoníaco", "emoji": "😈", "monstro": {"nome": "Demônio Menor", "emoji": "😈", "hp": 675, "ataque": 145, "defesa": 25}},
            {"andar": 3, "nome": "Caverna de Cristal", "emoji": "💎", "monstro": {"nome": "Golem de Cristal", "emoji": "💎", "hp": 750, "ataque": 125, "defesa": 45}},
            {"andar": 4, "nome": "Templo Profanado", "emoji": "⛩️", "monstro": {"nome": "Sacerdote Corrompido", "emoji": "🙏", "hp": 720, "ataque": 158, "defesa": 28}},
            {"andar": 5, "nome": "Salão do Rei Morto", "emoji": "👑", "monstro": {"nome": "Cavaleiro Negro", "emoji": "🏇", "hp": 900, "ataque": 171, "defesa": 40}},
        ],
        "chefe": {"nome": "Rei Lich", "emoji": "💀", "hp": 1500, "ataque": 176, "defesa": 45},
    },
    "B": {
        "nome": "Dungeon Rank B", "rank_min": "B", "emoji": "🟧", "nivel_min": 30, "cor": 0xD85A30,
        "desc": "Elite dos aventureiros. Recompensas extraordinarias.",
        "recompensa_andar": {"xp": 300, "moedas": 180},
        "recompensa_chefe": {"xp": 1500, "moedas": 1000},
        "andares": [
            {"andar": 1, "nome": "Dimensao Proibida", "emoji": "🌀", "monstro": {"nome": "Criatura Dimensional", "emoji": "👾", "hp": 979, "ataque": 189, "defesa": 40}},
            {"andar": 2, "nome": "Floresta Eterna", "emoji": "🌿", "monstro": {"nome": "Anciao da Floresta", "emoji": "🌲", "hp": 1120, "ataque": 176, "defesa": 60}},
            {"andar": 3, "nome": "Oceano de Lava", "emoji": "🌋", "monstro": {"nome": "Titan de Fogo", "emoji": "🔥", "hp": 1260, "ataque": 226, "defesa": 50}},
            {"andar": 4, "nome": "Tempestade Arcana", "emoji": "⚡", "monstro": {"nome": "Elemental Arcano", "emoji": "✨", "hp": 1190, "ataque": 213, "defesa": 45}},
            {"andar": 5, "nome": "Trono das Sombras", "emoji": "🖤", "monstro": {"nome": "Assassino das Sombras", "emoji": "🗡️", "hp": 1330, "ataque": 250, "defesa": 55}},
        ],
        "chefe": {"nome": "Titã Primordial", "emoji": "🗿", "hp": 3000, "ataque": 264, "defesa": 70},
    },
    "A": {
        "nome": "Dungeon Rank A", "rank_min": "A", "emoji": "🟥", "nivel_min": 40, "cor": 0xE24B4A,
        "desc": "Apenas lendas entram aqui. Recompensas unicas.",
        "recompensa_andar": {"xp": 500, "moedas": 300},
        "recompensa_chefe": {"xp": 2500, "moedas": 2000},
        "andares": [
            {"andar": 1, "nome": "Portal do Inferno", "emoji": "🔴", "monstro": {"nome": "Arquidemônio", "emoji": "😈", "hp": 1560, "ataque": 327, "defesa": 70}},
            {"andar": 2, "nome": "Reino dos Mortos", "emoji": "💀", "monstro": {"nome": "Senhor dos Mortos", "emoji": "💀", "hp": 1820, "ataque": 303, "defesa": 80}},
            {"andar": 3, "nome": "Abismo Eterno", "emoji": "🕳️", "monstro": {"nome": "Leviatã", "emoji": "🐉", "hp": 2080, "ataque": 378, "defesa": 75}},
            {"andar": 4, "nome": "Fortaleza Celeste", "emoji": "☁️", "monstro": {"nome": "Anjo Caido", "emoji": "👼", "hp": 1950, "ataque": 365, "defesa": 90}},
            {"andar": 5, "nome": "Sala do Julgamento", "emoji": "⚖️", "monstro": {"nome": "Juiz Eterno", "emoji": "⚖️", "hp": 2340, "ataque": 404, "defesa": 85}},
        ],
        "chefe": {"nome": "Deus da Destruição", "emoji": "💥", "hp": 6000, "ataque": 440, "defesa": 100},
    },
    "S": {
        "nome": "Dungeon Rank S", "rank_min": "S", "emoji": "⭐", "nivel_min": 50, "cor": 0x7F77DD,
        "desc": "A dungeon mais perigosa. Recompensas UNICAS no servidor.",
        "recompensa_andar": {"xp": 800, "moedas": 500},
        "recompensa_chefe": {"xp": 5000, "moedas": 5000},
        "andares": [
            {"andar": 1, "nome": "Vazio Absoluto", "emoji": "🌌", "monstro": {"nome": "Entidade do Vazio", "emoji": "🌌", "hp": 2500, "ataque": 484, "defesa": 120}},
            {"andar": 2, "nome": "Tempo Partido", "emoji": "⏳", "monstro": {"nome": "Guardiao do Tempo", "emoji": "⏳", "hp": 2750, "ataque": 459, "defesa": 140}},
            {"andar": 3, "nome": "Realidade Distorcida", "emoji": "🔮", "monstro": {"nome": "Espelho do Caos", "emoji": "🔮", "hp": 3125, "ataque": 532, "defesa": 130}},
            {"andar": 4, "nome": "Nucleo do Mundo", "emoji": "🌍", "monstro": {"nome": "Guardiao do Nucleo", "emoji": "🌍", "hp": 3500, "ataque": 580, "defesa": 150}},
            {"andar": 5, "nome": "Portal da Eternidade", "emoji": "🌟", "monstro": {"nome": "Ser Eterno", "emoji": "🌟", "hp": 3750, "ataque": 629, "defesa": 160}},
        ],
        "chefe": {"nome": "O Criador", "emoji": "🌟", "hp": 7000, "ataque": 550, "defesa": 150},
    },
    "SS": {
        "nome": "Dungeon Rank SS", "rank_min": "SS", "emoji": "💎", "nivel_min": 75, "cor": 0xD85A30,
        "desc": "O conteudo final. Apenas os Transcendentes ousam entrar.",
        "recompensa_andar": {"xp": 800, "moedas": 500},
        "recompensa_chefe": {"xp": 5000, "moedas": 5000},
        "andares": [
            {"andar": 1, "nome": "Portal do Vazio", "emoji": "🌀", "monstro": {"nome": "Guardiao do Vazio", "emoji": "🌀", "hp": 720, "ataque": 193, "defesa": 50}},
            {"andar": 2, "nome": "Abismo Eterno", "emoji": "🕳️", "monstro": {"nome": "Devorador de Almas", "emoji": "👁️", "hp": 840, "ataque": 217, "defesa": 55}},
            {"andar": 3, "nome": "Salao dos Herois", "emoji": "🏛️", "monstro": {"nome": "Heroi Corrompido", "emoji": "⚔️", "hp": 900, "ataque": 228, "defesa": 60}},
            {"andar": 4, "nome": "Trono das Sombras", "emoji": "🌑", "monstro": {"nome": "Senhor das Sombras", "emoji": "🌑", "hp": 960, "ataque": 242, "defesa": 65}},
            {"andar": 5, "nome": "Camara do Criador", "emoji": "✨", "monstro": {"nome": "Anjo Caido", "emoji": "👼", "hp": 1080, "ataque": 266, "defesa": 70}},
        ],
        "chefe": {"nome": "O Criador", "emoji": "🌌", "hp": 10000, "ataque": 680, "defesa": 180},
    },
}


def get_dungeon(rank):
    return RANKS_DUNGEON.get(rank.upper())