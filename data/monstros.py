# data/monstros.py — Todos os monstros do jogo

MONSTROS = [
    # Nível 1-5 (Fácil)
    {"id": "goblin", "img": "https://i.imgur.com/3NpKzQm.png", "nome": "Goblin", "emoji": "👺", "nivel": 1, "hp": 60, "ataque": 20, "defesa": 2, "xp": 8, "moedas": 6, "dificuldade": "facil",
     "skills": [{"nome": "Mordida", "emoji": "🦷", "dano": 8}, {"nome": "Arranhao", "emoji": "💢", "dano": 6}],
     "loot": [("pedra_suja", "Pedra Suja", "material", "Comum", "🪨", "Ingrediente basico")]},
     
    {"id": "lobo", "img": "https://i.imgur.com/5Q2xXkN.png", "nome": "Lobo Selvagem", "emoji": "🐺", "nivel": 3, "hp": 75, "ataque": 22, "defesa": 3, "xp": 10, "moedas": 7, "dificuldade": "facil",
     "skills": [{"nome": "Mordida Feroz", "emoji": "🦷", "dano": 10}, {"nome": "Investida", "emoji": "💨", "dano": 8}],
     "loot": [("pele_lobo", "Pele de Lobo", "material", "Comum", "🐾", "Material de armadura")]},
     
    {"id": "orc", "img": "https://i.imgur.com/2LmNxKp.png", "nome": "Orc Guerreiro", "emoji": "👹", "nivel": 5, "hp": 120, "ataque": 28, "defesa": 8, "xp": 25, "moedas": 12, "dificuldade": "facil",
     "skills": [{"nome": "Machado", "emoji": "🪓", "dano": 15}, {"nome": "Grito de Guerra", "emoji": "😤", "dano": 10}],
     "loot": [("dente_orc", "Dente de Orc", "material", "Incomum", "🦷", "Ingrediente alquimico"), ("minerio_ferro", "Minerio de Ferro", "material", "Comum", "⛏️", "Metal bruto")]},
     
    {"id": "rato_gigante", "img": "https://i.imgur.com/6kqJv1R.png", "nome": "Rato Gigante", "emoji": "🐀", "nivel": 2, "hp": 50, "ataque": 16, "defesa": 2, "xp": 7, "moedas": 5, "dificuldade": "facil",
     "skills": [{"nome": "Arranhao Duplo", "emoji": "💢", "dano": 7}, {"nome": "Fuga", "emoji": "💨", "dano": 5}],
     "loot": [("pelo_rato", "Pelo de Rato", "material", "Comum", "🐾", "Material comum")]},
     
    {"id": "goblin_arqueiro", "img": "https://i.imgur.com/8PqWrTz.png", "nome": "Goblin Arqueiro", "emoji": "👺", "nivel": 4, "hp": 55, "ataque": 18, "defesa": 2, "xp": 8, "moedas": 6, "dificuldade": "facil",
     "skills": [{"nome": "Flechada", "emoji": "🏹", "dano": 12}, {"nome": "Tiro Rapido", "emoji": "🏹", "dano": 8}],
     "loot": [("flecha_goblin", "Flecha de Goblin", "material", "Comum", "🏹", "Material de projétil")]},

    # Nível 6-15 (Médio)
    {"id": "esqueleto", "img": "https://i.imgur.com/6MqWrZp.png", "nome": "Esqueleto Armado", "emoji": "💀", "nivel": 8, "hp": 160, "ataque": 22, "defesa": 8, "xp": 20, "moedas": 13, "dificuldade": "medio",
     "skills": [{"nome": "Espada Ossea", "emoji": "⚔️", "dano": 18}, {"nome": "Lanca de Osso", "emoji": "🔱", "dano": 14}],
     "loot": [("osso_oco", "Osso Oco", "material", "Incomum", "💀", "Material necrotico")]},
     
    {"id": "troll", "img": "https://i.imgur.com/4NqKpZm.png", "nome": "Troll", "emoji": "🧌", "nivel": 10, "hp": 200, "ataque": 28, "defesa": 6, "xp": 24, "moedas": 15, "dificuldade": "medio",
     "skills": [{"nome": "Porrada", "emoji": "👊", "dano": 22}, {"nome": "Lama Toxica", "emoji": "🟢", "dano": 14}],
     "loot": [("muco_troll", "Muco de Troll", "material", "Incomum", "🟢", "Ingrediente alquimico")]},
     
    {"id": "vampiro", "img": "https://i.imgur.com/5QrLpKz.png", "nome": "Vampiro Anciao", "emoji": "🧛", "nivel": 15, "hp": 300, "ataque": 55, "defesa": 15, "xp": 100, "moedas": 40, "dificuldade": "medio",
     "skills": [{"nome": "Drenar Sangue", "emoji": "🩸", "dano": 28}, {"nome": "Hipnose", "emoji": "👁️", "dano": 15}],
     "loot": [("sangue_fresco", "Sangue Fresco", "material", "Incomum", "🩸", "Ingrediente alquimico"), ("sangue_anciao", "Sangue Anciao", "material", "Raro", "🩸", "Ingrediente raro")]},
     
    {"id": "golem", "img": "https://i.imgur.com/3nQpLmZ.png", "nome": "Golem de Pedra", "emoji": "🗿", "nivel": 12, "hp": 220, "ataque": 38, "defesa": 10, "xp": 26, "moedas": 16, "dificuldade": "medio",
     "skills": [{"nome": "Soco de Pedra", "emoji": "👊", "dano": 25}, {"nome": "Terremoto", "emoji": "🌋", "dano": 18}],
     "loot": [("fragmento_golem", "Fragmento de Golem", "material", "Raro", "🪨", "Material magico")]},
     
    {"id": "troll_pedra", "img": "https://i.imgur.com/8WmKzNp.png", "nome": "Troll das Pedras", "emoji": "🗿", "nivel": 14, "hp": 280, "ataque": 52, "defesa": 16, "xp": 90, "moedas": 35, "dificuldade": "medio",
     "skills": [{"nome": "Avalanche", "emoji": "🪨", "dano": 30}, {"nome": "Esmagar", "emoji": "💥", "dano": 22}],
     "loot": [("nucleo_pedra", "Nucleo de Pedra", "material", "Raro", "💎", "Material magico raro")]},

    # Nível 16-30 (Difícil)
    {"id": "dragao_jovem", "img": "https://i.imgur.com/9WqLpNm.png", "nome": "Dragão Jovem", "emoji": "🐉", "nivel": 25, "hp": 550, "ataque": 85, "defesa": 25, "xp": 220, "moedas": 85, "dificuldade": "dificil",
     "skills": [{"nome": "Baforada de Fogo", "emoji": "🔥", "dano": 45}, {"nome": "Garra Draconica", "emoji": "🐾", "dano": 35}],
     "loot": [("escama_dragao_p", "Escama de Dragao Pequena", "material", "Raro", "🐉", "Fragmento de escama")]},
     
    {"id": "lich", "img": "https://i.imgur.com/6MqWrZp.png", "nome": "Lich", "emoji": "💀", "nivel": 30, "hp": 700, "ataque": 100, "defesa": 30, "xp": 300, "moedas": 120, "dificuldade": "dificil",
     "skills": [{"nome": "Toque da Morte", "emoji": "☠️", "dano": 50}, {"nome": "Exercito Espectral", "emoji": "👻", "dano": 35}],
     "loot": [("essencia_sombria_p", "Essencia Sombria", "material", "Raro", "💀", "Ingrediente sombrio"), ("osso_lich", "Osso do Lich", "material", "Raro", "💀", "Ingrediente raro")]},
     
    {"id": "bruxa", "img": "https://i.imgur.com/4QzXpKn.png", "nome": "Bruxa das Trevas", "emoji": "🧙", "nivel": 18, "hp": 350, "ataque": 60, "defesa": 18, "xp": 130, "moedas": 50, "dificuldade": "dificil",
     "skills": [{"nome": "Maldicao", "emoji": "🩸", "dano": 30}, {"nome": "Bola de Fogo Sombria", "emoji": "🔥", "dano": 38}],
     "loot": [("essencia_sombria", "Essencia Sombria", "material", "Raro", "🌑", "Ingrediente sombrio")]},
     
    {"id": "grifo", "img": "https://i.imgur.com/7RmKpXz.png", "nome": "Grifo Selvagem", "emoji": "🦅", "nivel": 22, "hp": 450, "ataque": 72, "defesa": 22, "xp": 180, "moedas": 70, "dificuldade": "dificil",
     "skills": [{"nome": "Bico de Aco", "emoji": "⚔️", "dano": 38}, {"nome": "Garra Dupla", "emoji": "🐾", "dano": 30}],
     "loot": [("pena_grifo", "Pena de Grifo", "material", "Raro", "🦅", "Material de voo")]},

    # Nível 31-50 (Lendário)
    {"id": "demonio", "img": "https://i.imgur.com/5QrLpKz.png", "nome": "Demônio", "emoji": "😈", "nivel": 40, "hp": 1000, "ataque": 130, "defesa": 40, "xp": 500, "moedas": 200, "dificuldade": "lendario",
     "skills": [{"nome": "Chamas do Inferno", "emoji": "🔥", "dano": 65}, {"nome": "Garras Demoníacas", "emoji": "🗡️", "dano": 50}],
     "loot": [("essencia_sombria", "Essencia Sombria", "material", "Raro", "🌑", "Ingrediente sombrio"), ("olho_dragao", "Olho de Dragao", "material", "Epico", "👁️", "Material epico")]},
     
    {"id": "titan", "img": "https://i.imgur.com/4NqKpZm.png", "nome": "Titã", "emoji": "🗿", "nivel": 50, "hp": 1500, "ataque": 160, "defesa": 50, "xp": 800, "moedas": 300, "dificuldade": "lendario",
     "skills": [{"nome": "Golpe Primordial", "emoji": "💥", "dano": 80}, {"nome": "Tremor da Terra", "emoji": "🌋", "dano": 60}],
     "loot": [("fragmento_titan", "Fragmento do Titan", "material", "Lendario", "🗿", "Lendario absoluto"), ("escama_dragao_p", "Escama de Dragao Pequena", "material", "Raro", "🐉", "Fragmento de escama")]},
     
    {"id": "quimera", "img": "https://i.imgur.com/3NpKzQm.png", "nome": "Quimera", "emoji": "🦁", "nivel": 35, "hp": 850, "ataque": 110, "defesa": 35, "xp": 400, "moedas": 160, "dificuldade": "lendario",
     "skills": [{"nome": "Rugido do Caos", "emoji": "😤", "dano": 55}, {"nome": "Chamas e Gelo", "emoji": "❄️", "dano": 45}],
     "loot": [("corno_quimera_p", "Fragmento de Corno", "material", "Raro", "🦄", "Material raro"), ("escama_dragao_p", "Escama de Dragao Pequena", "material", "Raro", "🐉", "Fragmento de escama")]},
]